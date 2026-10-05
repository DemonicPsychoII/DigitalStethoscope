$repo = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$workspace = Join-Path $repo '.ci-workspace'
$pins = Get-Content (Join-Path $repo 'Development\system\testing\ci\toolchain.json') -Raw | ConvertFrom-Json

$env:PATH = "$(Join-Path $workspace '.venv\Scripts');$env:PATH"
$env:ZEPHYR_BASE = Join-Path $workspace 'zephyr'
$env:ZEPHYR_SDK_INSTALL_DIR = Join-Path $workspace "zephyr-sdk-$($pins.sdk_version)"

Write-Host "Zephyr environment enabled from $workspace"
Write-Host 'west build -b esp32s3_devkitc/esp32s3/procpu <application>'
