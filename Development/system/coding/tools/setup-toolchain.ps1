#Requires -Version 5.1
<#
.SYNOPSIS
Provision the pinned evaluation firmware toolchain in .ci-workspace.
.DESCRIPTION
Requires Git, Python 3.12+ and 7-Zip. CMake, Ninja and west are installed
in the workspace virtual environment. Safe to rerun after interrupted setup.
.EXAMPLE
    .\setup-toolchain.ps1
#>
[CmdletBinding()]
param([string]$Python = 'python')

$ErrorActionPreference = 'Stop'
$setup = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\testing\ci\setup_zephyr.py'))
& $Python $setup
if ($LASTEXITCODE -ne 0) { throw "Toolchain setup failed (exit $LASTEXITCODE)." }
