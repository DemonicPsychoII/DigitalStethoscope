#Requires -Version 5.1
<#
.SYNOPSIS
Flash an existing firmware build to a numbered Windows COM port.
.PARAMETER Profile
release (default) flashes build-app; debug flashes build-app-debug.
.PARAMETER Erase
Erase the whole flash first, including saved settings such as the Wi-Fi
network. Without it, flashing keeps the settings partition.
.EXAMPLE
    .\flash-firmware.ps1 5
.EXAMPLE
    .\flash-firmware.ps1 5 -Profile debug
.EXAMPLE
    .\flash-firmware.ps1 5 -Target bringup
.EXAMPLE
    .\flash-firmware.ps1 5 -Erase
#>
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'Medium')]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateRange(1, 65535)]
    [int]$Port,
    [ValidateSet('app', 'bringup')]
    [string]$Target = 'app',
    # $Profile is PowerShell's automatic profile path, so the variable has another name.
    [Alias('Profile')]
    [ValidateSet('release', 'debug')]
    [string]$BuildProfile = 'release',
    [string]$BuildDir,
    [switch]$Erase
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'firmware-common.ps1')
Assert-FwToolchain
$BuildDir = Resolve-FwBuildDir -Target $Target -BuildProfile $BuildProfile -BuildDir $BuildDir
Assert-FwBuild -BuildDir $BuildDir -Target $Target -BuildProfile $BuildProfile

$device = "COM$Port"
if ($PSCmdlet.ShouldProcess($device, "Flash firmware from $BuildDir")) {
    $arguments = @('flash', '-d', $BuildDir, '--no-rebuild', '--esp-device', $device)
    if ($Erase) {
        $arguments += '--erase'
        Write-Host "Erasing all flash on $device, including saved settings"
    }
    Write-Host "Flashing $BuildDir to $device"
    Invoke-FwWest $arguments
    Write-Host "Flash succeeded: $device"
}
