#Requires -Version 5.1
<#
.SYNOPSIS
Build the release app firmware and generate its SPDX software bill of materials.
.DESCRIPTION
Enables the CMake file-based API in the build directory, builds the release app with
build-firmware.ps1 and runs west spdx with the pinned toolchain. The SBOM covers the
application, Zephyr, the linked modules and the Zephyr SDK, and is written as SPDX 2.3
to <BuildDir>\spdx. It only builds; it never flashes or publishes firmware.
.PARAMETER Pristine
Delete the previous build state first.
.PARAMETER BuildDir
Build directory; defaults to build-app in the repository root, the CI release build.
.EXAMPLE
    .\build-sbom.ps1
.EXAMPLE
    .\build-sbom.ps1 -Pristine
#>
[CmdletBinding()]
param(
    [switch]$Pristine,
    [string]$BuildDir
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'firmware-common.ps1')

$BuildDir = Resolve-FwBuildDir -Target 'app' -BuildProfile 'release' -BuildDir $BuildDir

$buildScript = Join-Path $PSScriptRoot 'build-firmware.ps1'

# A pristine build deletes the build directory, including the query created below.
if ($Pristine) {
    & $buildScript -Target 'app' -BuildDir $BuildDir -Pristine
}
# west spdx reads the CMake file-based API reply, which CMake writes only when the
# query exists at configure time; build-firmware.ps1 always passes CMake arguments,
# so west re-runs CMake even for an existing build directory.
Invoke-FwWest @('spdx', '--init', '-d', $BuildDir)
& $buildScript -Target 'app' -BuildDir $BuildDir
Invoke-FwWest @('spdx', '-d', $BuildDir, '--include-sdk')

Write-Host "SBOM written to $(Join-Path $BuildDir 'spdx')"
