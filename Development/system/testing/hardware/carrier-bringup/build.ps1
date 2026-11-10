#Requires -Version 5.1
<#
.SYNOPSIS
Build the Eval carrier peripheral test firmware with the pinned toolchain.
.DESCRIPTION
Uses the toolchain provisioned by Development/system/coding/tools/setup-toolchain.ps1.
Only builds; flash the result with flash-firmware.ps1 -BuildDir.
.PARAMETER Pristine
Delete the previous build state first.
.PARAMETER BuildDir
Build directory; defaults to build-carrier in the repository root.
.EXAMPLE
    .\build.ps1 -Pristine
#>
[CmdletBinding()]
param(
    [switch]$Pristine,
    [string]$BuildDir
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\..\..\coding\tools\firmware-common.ps1')

if (-not $BuildDir) { $BuildDir = Join-Path $FwRepo 'build-carrier' }
# west runs from the toolchain workspace, so resolve from the caller's location now.
$BuildDir = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($BuildDir)

$arguments = @('build', '-b', $FwPins.board, $PSScriptRoot, '-d', $BuildDir)
if ($Pristine) { $arguments += '--pristine=always' }

Write-Host "Building the Eval carrier test for $($FwPins.board) into $BuildDir"
Invoke-FwWest $arguments
Write-Host "Build succeeded: $(Join-Path $BuildDir 'zephyr\zephyr.bin')"
