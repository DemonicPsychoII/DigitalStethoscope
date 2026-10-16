#Requires -Version 5.1
<#
.SYNOPSIS
Debug the firmware with GDB over the ESP32-S3 built-in USB JTAG.
.DESCRIPTION
Connect the DevKitC "USB" connector (GPIO19/20); the console stays on the "UART"
connector. Requires openocd-esp32 from setup-openocd.ps1. Nothing is flashed: flash the
same build first with flash-firmware.ps1, or GDB shows wrong source lines.
Halting the CPU stops I2S DMA, so audio output breaks while the target is halted.
.PARAMETER Mode
debug (default) resets the target and stops at main (west debug).
attach connects GDB to the running firmware without a reset; the CPU halts where it is.
server starts only the OpenOCD GDB server on port 3333 for an IDE or another GDB.
.PARAMETER Profile
debug (default) uses build-app-debug; release uses build-app, which steps poorly.
.EXAMPLE
    .\debug-firmware.ps1
.EXAMPLE
    .\debug-firmware.ps1 -Mode attach
.EXAMPLE
    .\debug-firmware.ps1 -Mode server
#>
[CmdletBinding()]
param(
    [ValidateSet('debug', 'attach', 'server')]
    [string]$Mode = 'debug',
    # $Profile is PowerShell's automatic profile path, so the variable has another name.
    [Alias('Profile')]
    [ValidateSet('release', 'debug')]
    [string]$BuildProfile = 'debug',
    [string]$BuildDir
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'firmware-common.ps1')
Assert-FwToolchain
$BuildDir = Resolve-FwBuildDir -Target 'app' -BuildProfile $BuildProfile -BuildDir $BuildDir
Assert-FwBuild -BuildDir $BuildDir -Target 'app' -BuildProfile $BuildProfile
$elf = Join-Path $BuildDir 'zephyr\zephyr.elf'

$openocd = Join-Path $FwOpenOcdDir 'bin\openocd.exe'
$scripts = Join-Path $FwOpenOcdDir 'share\openocd\scripts'
if (-not (Test-Path -LiteralPath $openocd -PathType Leaf)) {
    throw "openocd-esp32 missing in $FwOpenOcdDir. Run setup-openocd.ps1 first."
}

if ($Mode -ne 'attach') {
    # The board runner rejects OpenOCD outside the Espressif toolchain path, so the
    # build records no executable; pass the pinned one and its script directory.
    $command = @{ debug = 'debug'; server = 'debugserver' }[$Mode]
    if ($Mode -eq 'server') { Write-Host "Connect GDB to :3333 with $elf" }
    Invoke-FwWest @($command, '-d', $BuildDir, '--runner', 'openocd',
        '--openocd', $openocd, '--openocd-search', $scripts)
    return
}

# west attach would run the board's GDB init, which contains "mon reset halt".
# Start OpenOCD and GDB directly so the running firmware keeps its state.
$boardCfg = Join-Path $FwWorkspace 'zephyr\boards\espressif\esp32s3_devkitc\support\openocd.cfg'
$gdb = Join-Path $FwToolBin "$($FwPins.toolchain)-gdb.exe"
foreach ($file in @($boardCfg, $gdb)) {
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Missing $file. Run setup-toolchain.ps1 first." }
}

$server = Start-Process -FilePath $openocd -PassThru -NoNewWindow -ArgumentList @(
    '-s', "`"$scripts`"", '-f', "`"$($boardCfg -replace '\\', '/')`"",
    '-c', '"gdb port 3333"', '-c', 'init')
# Without an open handle, Windows PowerShell 5.1 reports no exit code later.
$null = $server.Handle
try {
    Start-Sleep -Seconds 2
    if ($server.HasExited) { throw "OpenOCD stopped (exit $($server.ExitCode)). Check the USB JTAG connection and driver." }
    & $gdb -q $elf `
        -ex 'set remote hardware-watchpoint-limit 2' `
        -ex 'target extended-remote :3333' `
        -ex 'maintenance flush register-cache'
}
finally {
    if (-not $server.HasExited) { Stop-Process -Id $server.Id -Force }
}
