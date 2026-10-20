#Requires -Version 5.1
<#
.SYNOPSIS
Build the thesis application or the bring-up firmware manually with the pinned toolchain.
.DESCRIPTION
Uses the toolchain provisioned by setup-toolchain.ps1 in .ci-workspace and the board
pinned in toolchain.json. Only builds; it never flashes or publishes firmware.
.PARAMETER Target
app (default) builds Development/system/coding/app; bringup builds the evaluation firmware.
.PARAMETER Profile
release (default) builds prj.conf alone, the same configuration as CI. debug merges
app/debug.conf for GDB, debug logs and fault checks; it exists only for the app target.
.PARAMETER Pristine
Delete the previous build state first.
.PARAMETER BuildDir
Build directory; defaults to build-app, build-app-debug or build-eval in the repository root.
.EXAMPLE
    .\build-firmware.ps1
.EXAMPLE
    .\build-firmware.ps1 -Profile debug
.EXAMPLE
    .\build-firmware.ps1 -Target bringup -Pristine
#>
[CmdletBinding()]
param(
    [ValidateSet('app', 'bringup')]
    [string]$Target = 'app',
    # $Profile is PowerShell's automatic profile path, so the variable has another name.
    [Alias('Profile')]
    [ValidateSet('release', 'debug')]
    [string]$BuildProfile = 'release',
    [switch]$Pristine,
    [string]$BuildDir
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'firmware-common.ps1')

$sources = @{
    app     = 'Development\system\coding\app'
    bringup = 'Development\system\coding\bringup-zephyr'
}
$source = Join-Path $FwRepo $sources[$Target]
$BuildDir = Resolve-FwBuildDir -Target $Target -BuildProfile $BuildProfile -BuildDir $BuildDir

$arguments = @('build', '-b', $FwPins.board, $source, '-d', $BuildDir)
if ($Pristine) { $arguments += '--pristine=always' }
# Always pass the fragment list, so a reused build directory cannot keep a stale one.
$extraConf = if ($BuildProfile -eq 'debug') { Join-Path $source 'debug.conf' } else { '' }
$arguments += @('--', "-DEXTRA_CONF_FILE=$($extraConf -replace '\\', '/')")

Write-Host "Building $Target ($BuildProfile) for $($FwPins.board) into $BuildDir"
Invoke-FwWest $arguments
Write-Host "Build succeeded: $(Join-Path $BuildDir 'zephyr\zephyr.bin')"
