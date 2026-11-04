#Requires -Version 5.1
<#
.SYNOPSIS
Write the provisioning image of one deployment file to a numbered Windows COM port.
.DESCRIPTION
Runs provisioning\provisioning.py build, then writes only that image at the start of the
provisioning partition of the firmware build; esptool verifies the written data. The firmware
image and the settings partition, including the saved Wi-Fi network, stay unchanged.
.PARAMETER BuildDir
Firmware build whose devicetree defines the provisioning partition; build-app by default.
.EXAMPLE
    .\flash-provisioning.ps1 5 ..\provisioning\lab-hapi.toml
#>
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'Medium')]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateRange(1, 65535)]
    [int]$Port,
    [Parameter(Mandatory = $true, Position = 1)]
    [string]$File,
    [string]$BuildDir
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'firmware-common.ps1')
Assert-FwToolchain
$BuildDir = Resolve-FwBuildDir -Target 'app' -BuildProfile 'release' -BuildDir $BuildDir
Assert-FwBuild -BuildDir $BuildDir -Target 'app' -BuildProfile 'release'
$File = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($File)

$device = "COM$Port"
$python = Join-Path $FwWorkspace '.venv\Scripts\python.exe'
$tool = Join-Path $PSScriptRoot 'provisioning\provisioning.py'
if ($PSCmdlet.ShouldProcess($device, "Write the provisioning image of $File")) {
    # esptool logs progress on stderr; success is judged by the exit code only.
    $ErrorActionPreference = 'Continue'
    & $python $tool flash $File --build-dir $BuildDir --port $device
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($exitCode -ne 0) { throw "Provisioning flash failed on $device (exit $exitCode)." }
    Write-Host "Provisioning flash succeeded: $device"
}
