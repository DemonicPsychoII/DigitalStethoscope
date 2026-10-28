#Requires -Version 5.1
# Shared paths and the west launcher for the firmware helper scripts.
# Dot-source it: . (Join-Path $PSScriptRoot 'firmware-common.ps1')

$FwRepo = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..'))
$FwWorkspace = Join-Path $FwRepo '.ci-workspace'
$FwPins = Get-Content (Join-Path $FwRepo 'Development\system\testing\ci\toolchain.json') -Raw | ConvertFrom-Json
$FwWest = Join-Path $FwWorkspace '.venv\Scripts\west.exe'
$FwSdk = Join-Path $FwWorkspace "zephyr-sdk-$($FwPins.sdk_version)"
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
    $resolvedWorkspace = & (Join-Path $FwWorkspace '.venv\Scripts\python.exe') -c 'import pathlib, sys; print(pathlib.Path(sys.argv[1]).resolve())' $FwWorkspace
    if ($LASTEXITCODE -ne 0) { throw 'Could not resolve the pinned toolchain workspace.' }
    $toolEnv = @{
        # The ESP32 runner starts esptool by name, so its pinned launcher must be on PATH.
        PATH                     = "$(Join-Path $FwWorkspace '.venv\Scripts');$env:PATH"
        ZEPHYR_BASE              = Join-Path $resolvedWorkspace 'zephyr'
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
