#Requires -Version 5.1
<#
.SYNOPSIS
Translate an Xtensa fatal-error dump from the serial console into functions and source lines.
.DESCRIPTION
Reads the register dump, takes PC (the faulting instruction) and A0 (the return
address into the caller), and resolves both with addr2line. The pinned Zephyr cannot
link CONFIG_XTENSA_ENABLE_BACKTRACE for the ESP32-S3, so deeper frames need GDB.
A wrong ELF gives wrong lines, so select the build that was flashed.
.PARAMETER Path
Text file with the copied crash output. Without Path and Text the clipboard is used.
.PARAMETER Text
Crash output as a string.
.PARAMETER Profile
debug (default) uses build-app-debug; release uses build-app.
.EXAMPLE
    .\decode-crash.ps1                        # crash output is in the clipboard
.EXAMPLE
    .\decode-crash.ps1 -Path crash.txt -Profile release
#>
[CmdletBinding()]
param(
    [string]$Path,
    [string]$Text,
    # $Profile is PowerShell's automatic profile path, so the variable has another name.
    [Alias('Profile')]
    [ValidateSet('release', 'debug')]
    [string]$BuildProfile = 'debug',
    [string]$BuildDir
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'firmware-common.ps1')
$BuildDir = Resolve-FwBuildDir -Target 'app' -BuildProfile $BuildProfile -BuildDir $BuildDir
Assert-FwBuild -BuildDir $BuildDir -Target 'app' -BuildProfile $BuildProfile
$elf = Join-Path $BuildDir 'zephyr\zephyr.elf'
$addr2line = Join-Path $FwToolBin "$($FwPins.toolchain)-addr2line.exe"
if (-not (Test-Path -LiteralPath $addr2line -PathType Leaf)) {
    throw "addr2line missing in $FwToolBin. Run setup-toolchain.ps1 first."
}

if ($Path) { $Text = Get-Content -LiteralPath $Path -Raw }
elseif (-not $Text) { $Text = Get-Clipboard -Raw }
if (-not $Text) { throw 'No crash output. Copy it to the clipboard or pass -Path or -Text.' }

$pc = [regex]::Match($Text, '\*\*\s+PC\s+(0x[0-9a-fA-F]+)')
$a0 = [regex]::Match($Text, '\*\*\s+A0\s+(0x[0-9a-fA-F]+)')
if (-not $pc.Success) { throw 'No " **  PC 0x..." line found in the crash output.' }

$addresses = @($pc.Groups[1].Value)
if ($a0.Success) {
    # Windowed calls store the call size in the top two bits of A0; code addresses
    # on the ESP32-S3 start with 0b01, so restore those bits.
    $value = ([Convert]::ToUInt32($a0.Groups[1].Value.Substring(2), 16) -band 0x3FFFFFFF) -bor 0x40000000
    $addresses += ('0x{0:x8}' -f $value)
}

Write-Host "Decoding PC and caller with $elf"
# -a address, -f function, -i inlined callers, -p one line each, -C demangle.
& $addr2line -e $elf -a -f -i -p -C @addresses
if ($LASTEXITCODE -ne 0) { throw "addr2line failed (exit $LASTEXITCODE)." }
