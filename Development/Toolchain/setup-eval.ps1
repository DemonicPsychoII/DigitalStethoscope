#Requires -Version 5.1
<#
.SYNOPSIS
Prepare this checkout for local evaluation builds, reusing a pinned SDK if available.
.PARAMETER Workspace
Existing west workspace containing zephyr and zephyr-sdk-1.0.1. If omitted,
look in this checkout and the primary Git worktree, then provision locally.
#>
[CmdletBinding()]
param([string]$Workspace)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$local = Join-Path $root '.ci-workspace'
$python = Join-Path $local '.venv/Scripts/python.exe'
function Invoke-Checked {
    param([string]$Exe, [string[]]$Argv)
    & $Exe @Argv
    if ($LASTEXITCODE -ne 0) { throw "$Exe failed with exit code $LASTEXITCODE" }
}
if (-not $Workspace) {
    $common = & git -C $root rev-parse --path-format=absolute --git-common-dir
    if ($LASTEXITCODE -ne 0) { throw 'Cannot locate primary Git worktree' }
    $primary = Split-Path $common -Parent
    $candidates = @(
        (Join-Path $root '.ci-workspace/toolchain'),
        (Join-Path $root 'Development/Toolchain/zephyrproject'),
        (Join-Path $root 'Development/system/coding/tools/zephyrproject'),
        (Join-Path $primary 'Development/Toolchain/zephyrproject'),
        (Join-Path $primary 'Development/system/coding/tools/zephyrproject')
    )
    $Workspace = $candidates | Where-Object {
        Test-Path (Join-Path $_ 'zephyr-sdk-1.0.1/sdk_version')
    } | Select-Object -First 1
    if (-not $Workspace) {
        $Workspace = Join-Path $local 'toolchain'
        & (Join-Path $root 'Development/system/coding/tools/setup-toolchain.ps1') -WorkspaceDir $Workspace
    }
}
$Workspace = (Resolve-Path $Workspace).Path
$zephyr = Join-Path $Workspace 'zephyr'
$sdk = Join-Path $Workspace 'zephyr-sdk-1.0.1'
foreach ($item in @(
    @($zephyr, '357467a011cd2557a1a3f0b4be83d817c4addc9b'),
    @((Join-Path $Workspace 'modules/hal/espressif'), '3d4d922a4d2994f844790ec031a584ec71240485')
)) {
    $revision = & git -C $item[0] rev-parse HEAD
    if ($LASTEXITCODE -ne 0 -or $revision -ne $item[1]) { throw "Pinned revision mismatch: $($item[0])" }
}
if ((Get-Content (Join-Path $sdk 'sdk_version')).Trim() -ne '1.0.1') { throw 'SDK version mismatch' }
if (-not (Test-Path (Join-Path $sdk 'gnu/xtensa-espressif_esp32s3_zephyr-elf/bin/xtensa-espressif_esp32s3_zephyr-elf-gcc.exe'))) {
    throw "ESP32-S3 compiler missing from $sdk"
}
foreach ($tool in 'git', 'cmake', 'ninja') { Get-Command $tool -ErrorAction Stop | Out-Null }
$venv = [System.IO.Path]::GetFullPath((Join-Path $local '.venv'))
if (Test-Path $python) {
    & $python -c 'import sys; assert sys.version_info >= (3, 12)' 2>$null
    if ($LASTEXITCODE -ne 0) {
        # Only clear this checkout's disposable environment, never the shared SDK.
        if ((Split-Path $venv -Parent) -ne $local -or (Split-Path $venv -Leaf) -ne '.venv') {
            throw 'Refusing to clear a virtual environment outside the local workspace'
        }
        Invoke-Checked 'python' @('-m', 'venv', '--clear', $venv)
    }
} else {
    Invoke-Checked 'python' @('-m', 'venv', $venv)
}
Invoke-Checked $python @('-c', 'import sys; assert sys.version_info >= (3, 12), "Python 3.12+ required"')
# Scope package index selection to this disposable environment. Some host pip
# configurations contain obsolete extra indexes that make every download stall.
Set-Content (Join-Path $local '.venv/pip.ini') "[global]`nindex-url = https://pypi.org/simple`nextra-index-url =`ntrusted-host ="
Invoke-Checked $python @('-m', 'pip', 'install', 'west==1.5.0',
    '-r', (Join-Path $zephyr 'scripts/requirements-base.txt'),
    '-r', (Join-Path $Workspace 'modules/hal/espressif/zephyr/requirements.txt'))
$env:ZEPHYR_BASE = $zephyr
$env:ZEPHYR_SDK_INSTALL_DIR = $sdk
$env:PATH = "$(Split-Path $python -Parent);$env:PATH"
# Fetch verifies installed blob hashes and repairs missing blobs.
Invoke-Checked $python @('-m', 'west', 'blobs', 'fetch', 'hal_espressif')
@{ workspace = $Workspace; zephyr = $zephyr; sdk = $sdk; python = $python } |
    ConvertTo-Json | Set-Content (Join-Path $local 'eval-environment.json')
Write-Host 'Evaluation build environment ready. From the repository root run:'
Write-Host '. .\Development\Toolchain\zephyr-env.ps1'
Write-Host 'python Development/system/testing/ci/build_eval.py --profile qc'
