#Requires -Version 5.1
<#
.SYNOPSIS
Flash an existing firmware build to a numbered Windows COM port.
.EXAMPLE
    .\flash-firmware.ps1 5
.EXAMPLE
    .\flash-firmware.ps1 5 -Target bringup
#>
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'Medium')]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateRange(1, 65535)]
    [int]$Port,
    [ValidateSet('app', 'bringup')]
    [string]$Target = 'app',
    [string]$BuildDir
)

$ErrorActionPreference = 'Stop'
$repo = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..'))
$workspace = Join-Path $repo '.ci-workspace'
$west = Join-Path $workspace '.venv\Scripts\west.exe'
if (-not (Test-Path -LiteralPath $west -PathType Leaf)) {
    throw "Pinned toolchain missing in $workspace. Run setup-toolchain.ps1 first."
}

$defaultDirs = @{ app = 'build-app'; bringup = 'build-eval' }
if (-not $BuildDir) { $BuildDir = Join-Path $repo $defaultDirs[$Target] }
$BuildDir = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($BuildDir)
if (-not (Test-Path -LiteralPath (Join-Path $BuildDir 'zephyr\zephyr.bin') -PathType Leaf)) {
    throw "Firmware missing in $BuildDir. Run build-firmware.ps1 -Target $Target first."
}

$device = "COM$Port"
if ($PSCmdlet.ShouldProcess($device, "Flash firmware from $BuildDir")) {
    # west discovers its Zephyr commands from the pinned workspace.
    Push-Location -LiteralPath $workspace
    $previousPath = $env:PATH
    try {
        # The ESP32 runner starts esptool by name, so its pinned launcher must be on PATH.
        $env:PATH = "$(Join-Path $workspace '.venv\Scripts');$previousPath"
        Write-Host "Flashing $BuildDir to $device"
        # Match the build helper: west writes progress to stderr on PowerShell 5.1.
        $ErrorActionPreference = 'Continue'
        & $west flash -d $BuildDir --no-rebuild --esp-device $device
        $ErrorActionPreference = 'Stop'
        if ($LASTEXITCODE -ne 0) { throw "Flash failed (exit $LASTEXITCODE)." }
        Write-Host "Flash succeeded: $device"
    }
    finally {
        $env:PATH = $previousPath
        Pop-Location
    }
}
