#Requires -Version 5.1
<#
.SYNOPSIS
Install Espressif's OpenOCD for JTAG debugging into .ci-workspace\openocd-esp32.
.DESCRIPTION
The Zephyr SDK OpenOCD cannot drive the ESP32-S3 built-in USB JTAG, and the board
runner accepts only openocd-esp32. The release is pinned here and not in
toolchain.json, because toolchain.json keys the CI compiler cache and CI does not debug.
Safe to rerun; an existing installation of the pinned version is kept.
.EXAMPLE
    .\setup-openocd.ps1
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'firmware-common.ps1')

$version = 'v0.12.0-esp32-20260831'
$sha256 = 'd508bbe1d166e38415d57b495dd0409f46883251087433cfb3eabf513be93ff7'
$archive = "openocd-esp32-win64-$($version.TrimStart('v')).zip"
$url = "https://github.com/espressif/openocd-esp32/releases/download/$version/$archive"
$marker = Join-Path $FwOpenOcdDir 'VERSION.txt'

$executable = Join-Path $FwOpenOcdDir 'bin\openocd.exe'

if ((Test-Path -LiteralPath $marker) -and ((Get-Content -LiteralPath $marker -Raw).Trim() -eq $version) -and
    (Test-Path -LiteralPath $executable -PathType Leaf)) {
    Write-Host "openocd-esp32 $version is already installed in $FwOpenOcdDir"
    return
}
if (-not (Test-Path -LiteralPath $FwWorkspace)) {
    throw "Pinned toolchain missing in $FwWorkspace. Run setup-toolchain.ps1 first."
}

# Stage on the workspace volume: Move-Item cannot move a directory across volumes.
$temp = Join-Path $FwWorkspace "openocd-esp32-download-$([guid]::NewGuid())"
New-Item -ItemType Directory -Path $temp | Out-Null
try {
    $zip = Join-Path $temp $archive
    Write-Host "Downloading $url"
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
    $actual = (Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $sha256) { throw "SHA-256 mismatch for ${archive}: $actual" }

    Expand-Archive -LiteralPath $zip -DestinationPath $temp
    # The archive holds one top-level openocd-esp32 directory.
    $extracted = Join-Path $temp 'openocd-esp32'
    if (-not (Test-Path -LiteralPath (Join-Path $extracted 'bin\openocd.exe'))) {
        throw "Unexpected archive layout in $archive."
    }
    if (Test-Path -LiteralPath $FwOpenOcdDir) { Remove-Item -LiteralPath $FwOpenOcdDir -Recurse -Force }
    Move-Item -LiteralPath $extracted -Destination $FwOpenOcdDir
    Set-Content -LiteralPath $marker -Value $version
    Write-Host "Installed openocd-esp32 $version in $FwOpenOcdDir"
}
finally {
    Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue
}
