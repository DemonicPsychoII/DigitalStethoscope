#Requires -Version 5.1
<#
.SYNOPSIS
Erase selected flash partitions on a numbered Windows COM port.
.DESCRIPTION
Reads the partition offsets and sizes from the final devicetree of the firmware build,
then erases only the selected partitions with the pinned esptool. Unselected partitions
stay unchanged. Erasing the application leaves the device without a bootable image until
the firmware is flashed again.
.PARAMETER App
Erase the application partition, including the boot image header.
.PARAMETER Settings
Erase the settings partition, including the saved Wi-Fi network.
.PARAMETER Provisioning
Erase the provisioning partition with the deployment endpoint and certificate.
.PARAMETER BuildDir
Firmware build whose devicetree defines the partitions; build-app by default.
.EXAMPLE
    .\erase-flash.ps1 5 -Settings
.EXAMPLE
    .\erase-flash.ps1 5 -Settings -Provisioning
#>
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'Medium')]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateRange(1, 65535)]
    [int]$Port,
    [switch]$App,
    [switch]$Settings,
    [Alias('Partition')]
    [switch]$Provisioning,
    [string]$BuildDir
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'firmware-common.ps1')

$selectedLabels = @(
    if ($App) { 'slot0_partition' }
    if ($Settings) { 'storage_partition' }
    if ($Provisioning) { 'provisioning_partition' }
)
if ($selectedLabels.Count -eq 0) {
    throw 'Select at least one partition: -App, -Settings or -Provisioning.'
}

Assert-FwToolchain
$BuildDir = Resolve-FwBuildDir -Target 'app' -BuildProfile 'release' -BuildDir $BuildDir
Assert-FwBuild -BuildDir $BuildDir -Target 'app' -BuildProfile 'release'
$devicetree = Get-Content -LiteralPath (Join-Path $BuildDir 'zephyr\zephyr.dts') -Raw

$device = "COM$Port"
$python = Join-Path $FwWorkspace '.venv\Scripts\python.exe'
foreach ($label in $selectedLabels) {
    $pattern = "\b${label}:\s*(?:\w+:\s*)*partition@[0-9a-fA-F]+\s*\{[^}]*?\breg\s*=\s*<\s*(0x[0-9a-fA-F]+)\s+(0x[0-9a-fA-F]+)\s*>"
    $match = [regex]::Match($devicetree, $pattern)
    if (-not $match.Success) { throw "No $label node in the devicetree of $BuildDir." }
    $offset = $match.Groups[1].Value
    $size = $match.Groups[2].Value
    if ($PSCmdlet.ShouldProcess($device, "Erase $label at $offset, size $size")) {
        # esptool logs progress on stderr; success is judged by the exit code only.
        $ErrorActionPreference = 'Continue'
        & $python -m esptool --chip esp32s3 --port $device erase-region $offset $size
        $exitCode = $LASTEXITCODE
        $ErrorActionPreference = 'Stop'
        if ($exitCode -ne 0) { throw "Erasing $label failed on $device (exit $exitCode)." }
        Write-Host "Erased ${label}: $device"
    }
}
