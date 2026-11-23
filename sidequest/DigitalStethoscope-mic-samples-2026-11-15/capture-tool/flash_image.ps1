param([Parameter(Mandatory = $true)][string]$BuildDirectory)
$ErrorActionPreference = 'Stop'
. 'C:\SVN\DigitalStethoscope\Development\system\coding\tools\firmware-common.ps1'
Assert-FwToolchain
Invoke-FwWest @('flash', '-d', $BuildDirectory, '--no-rebuild', '--esp-device', 'COM4')
Write-Host "Flash succeeded: $BuildDirectory"
