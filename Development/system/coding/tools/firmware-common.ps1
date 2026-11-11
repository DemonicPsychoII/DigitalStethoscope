#Requires -Version 5.1
# Shared paths and the west launcher for the firmware helper scripts.
# Dot-source it: . (Join-Path $PSScriptRoot 'firmware-common.ps1')

$FwRepo = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..'))
function Invoke-ToolchainResolver {
    param([string]$Resolver, [string[]]$Arguments)
    # Windows PowerShell 5.1 decodes native output with the console code page, but the
    # resolver writes UTF-8; non-ASCII profile paths would arrive corrupted.
    $previousEncoding = [Console]::OutputEncoding
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    try {
        # `python` can be the inactive Microsoft Store alias; the launcher is the fallback.
        foreach ($candidate in @(, @('python')) + @(, @('py', '-3'))) {
            if (-not (Get-Command $candidate[0] -ErrorAction SilentlyContinue)) { continue }
            $launcherArguments = @($candidate | Select-Object -Skip 1)
            $output = & $candidate[0] @launcherArguments $Resolver @Arguments
            if ($LASTEXITCODE -eq 0) { return $output }
        }
    }
    finally { [Console]::OutputEncoding = $previousEncoding }
    throw 'Pinned toolchain not resolved; needs Python 3.12+ as python or py -3, see the message above.'
}

# The pinned workspace is shared by all checkouts and worktrees; Python resolves it like CI.
$FwLocations = Invoke-ToolchainResolver -Resolver (Join-Path $PSScriptRoot 'toolchain\toolchain_environment.py') -Arguments '--format', 'locations' | ConvertFrom-Json
$FwWorkspace = $FwLocations.workspace
$FwPins = Get-Content (Join-Path $PSScriptRoot 'toolchain\toolchain.json') -Raw | ConvertFrom-Json
$FwWest = Join-Path $FwWorkspace '.venv\Scripts\west.exe'
# west may reuse an SDK of the pinned version outside the workspace; setup records it.
$FwSdk = $FwLocations.sdk
$FwToolBin = Join-Path $FwSdk "gnu\$($FwPins.toolchain)\bin"
$FwOpenOcdDir = Join-Path $FwWorkspace 'openocd-esp32'

function Assert-FwToolchain {
    if (-not (Test-Path -LiteralPath $FwWest -PathType Leaf)) {
        throw "Pinned toolchain missing in $FwWorkspace. Run setup-toolchain.ps1 first."
    }
}

# Release keeps the CI build directories, so CI parity and old commands stay valid.
function Resolve-FwBuildDir {
    param([string]$Target, [string]$BuildProfile, [string]$BuildDir)
    if ($BuildProfile -eq 'debug' -and $Target -ne 'app') {
        throw 'The debug profile exists only for the app target.'
    }
    if (-not $BuildDir) {
        $name = @{ app = 'build-app'; bringup = 'build-eval' }[$Target]
        if ($BuildProfile -eq 'debug') { $name += '-debug' }
        $BuildDir = Join-Path $FwRepo $name
    }
    # Callers change directory before west runs, so resolve from the caller's location now.
    $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($BuildDir)
}

function Assert-FwBuild {
    param([string]$BuildDir, [string]$Target, [string]$BuildProfile)
    if (-not (Test-Path -LiteralPath (Join-Path $BuildDir 'zephyr\zephyr.elf') -PathType Leaf)) {
        throw "Firmware missing in $BuildDir. Run build-firmware.ps1 -Target $Target -Profile $BuildProfile first."
    }
}

# Same environment as build_support.build_env. Scripts share the caller's session,
# so the previous values are restored to keep the caller's shell unchanged.
function Invoke-FwWest {
    param([string[]]$Arguments)
    Assert-FwToolchain
    $toolEnv = @{
        # The ESP32 runner starts esptool by name, so its pinned launcher must be on PATH.
        PATH                     = "$(Join-Path $FwWorkspace '.venv\Scripts');$env:PATH"
        ZEPHYR_BASE              = Join-Path $FwWorkspace 'zephyr'
        ZEPHYR_SDK_INSTALL_DIR   = $FwSdk
        ZEPHYR_TOOLCHAIN_VARIANT = 'zephyr'
    }
    $previous = @{}
    foreach ($name in $toolEnv.Keys) {
        $previous[$name] = [Environment]::GetEnvironmentVariable($name)
        [Environment]::SetEnvironmentVariable($name, $toolEnv[$name])
    }
    # west discovers its Zephyr and Espressif commands from the pinned workspace.
    Push-Location -LiteralPath $FwWorkspace
    try {
        # west logs progress on stderr; Windows PowerShell 5.1 turns redirected stderr
        # into errors, so success is judged by the exit code only.
        $ErrorActionPreference = 'Continue'
        & $FwWest @Arguments
        $exitCode = $LASTEXITCODE
        $ErrorActionPreference = 'Stop'
        if ($exitCode -ne 0) { throw "west $($Arguments[0]) failed (exit $exitCode)." }
    }
    finally {
        Pop-Location
        foreach ($name in $previous.Keys) {
            if ($null -eq $previous[$name]) { Remove-Item "Env:\$name" -ErrorAction SilentlyContinue }
            else { Set-Item "Env:\$name" $previous[$name] }
        }
    }
}
