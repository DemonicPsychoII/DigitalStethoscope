$ErrorActionPreference = 'Stop'
. 'C:\SVN\DigitalStethoscope\Development\system\coding\tools\firmware-common.ps1'
Assert-FwToolchain
$buildDirectory = Join-Path $PSScriptRoot 'build'
Invoke-FwWest @('build', '-b', $FwPins.board, $PSScriptRoot, '-d', $buildDirectory, '--pristine=always')
Write-Host "Build succeeded: $(Join-Path $buildDirectory 'zephyr\zephyr.bin')"
