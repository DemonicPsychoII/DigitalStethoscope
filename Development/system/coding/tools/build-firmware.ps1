#Requires -Version 5.1
<#
.SYNOPSIS
Build the thesis application or the bring-up firmware manually with the pinned toolchain.
.DESCRIPTION
Uses the toolchain provisioned by setup-toolchain.ps1 in .ci-workspace and the board
pinned in toolchain.json. Only builds; it never flashes or publishes firmware.
.PARAMETER Target
app (default) builds Development/system/coding/app; bringup builds the evaluation firmware.
.PARAMETER Pristine
Delete the previous build state first.
.PARAMETER BuildDir
Build directory; defaults to build-app or build-eval in the repository root.
.EXAMPLE
    .\build-firmware.ps1
.EXAMPLE
    .\build-firmware.ps1 -Target bringup -Pristine
#>
[CmdletBinding()]
param(
    [ValidateSet('app', 'bringup')]
    [string]$Target = 'app',
    [switch]$Pristine,
    [string]$BuildDir
)

$ErrorActionPreference = 'Stop'
$repo = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..'))
$workspace = Join-Path $repo '.ci-workspace'
$pins = Get-Content (Join-Path $repo 'Development\system\testing\ci\toolchain.json') -Raw | ConvertFrom-Json

$west = Join-Path $workspace '.venv\Scripts\west.exe'
if (-not (Test-Path $west)) {
    throw "Pinned toolchain missing in $workspace. Run setup-toolchain.ps1 first."
}

$sources = @{
    app     = 'Development\system\coding\app'
    bringup = 'Development\system\coding\bringup-zephyr'
}
$defaultDirs = @{ app = 'build-app'; bringup = 'build-eval' }
$source = Join-Path $repo $sources[$Target]
if (-not $BuildDir) { $BuildDir = Join-Path $repo $defaultDirs[$Target] }

# Same environment as build_support.build_env. Scripts share the caller's session,
# so the previous values are restored to keep the caller's shell unchanged.
$toolEnv = @{
    PATH                     = "$(Join-Path $workspace '.venv\Scripts');$env:PATH"
    ZEPHYR_BASE              = Join-Path $workspace 'zephyr'
    ZEPHYR_SDK_INSTALL_DIR   = Join-Path $workspace "zephyr-sdk-$($pins.sdk_version)"
    ZEPHYR_TOOLCHAIN_VARIANT = 'zephyr'
}
$previous = @{}
foreach ($name in $toolEnv.Keys) {
    $previous[$name] = [Environment]::GetEnvironmentVariable($name)
    [Environment]::SetEnvironmentVariable($name, $toolEnv[$name])
}

$arguments = @('build', '-b', $pins.board, $source, '-d', $BuildDir)
if ($Pristine) { $arguments += '--pristine=always' }

try {
    Write-Host "Building $Target for $($pins.board) into $BuildDir"
    # west logs progress on stderr; Windows PowerShell 5.1 turns redirected stderr
    # into errors, so success is judged by the exit code only.
    $ErrorActionPreference = 'Continue'
    & $west @arguments
    $ErrorActionPreference = 'Stop'
    if ($LASTEXITCODE -ne 0) { throw "Build failed (exit $LASTEXITCODE)." }
    Write-Host "Build succeeded: $(Join-Path $BuildDir 'zephyr\zephyr.bin')"
}
finally {
    foreach ($name in $previous.Keys) {
        if ($null -eq $previous[$name]) { Remove-Item "Env:\$name" -ErrorAction SilentlyContinue }
        else { Set-Item "Env:\$name" $previous[$name] }
    }
}
