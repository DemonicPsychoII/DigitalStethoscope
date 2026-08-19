$workspace = Join-Path $PSScriptRoot 'zephyrproject'

$env:PATH = "$(Join-Path $workspace '.venv\Scripts');$env:PATH"
$env:ZEPHYR_BASE = Join-Path $workspace 'zephyr'
$env:ZEPHYR_SDK_INSTALL_DIR = Join-Path $workspace 'zephyr-sdk-1.0.1'

Write-Host "Zephyr environment enabled from $workspace"
Write-Host 'west build -b esp32s3_devkitc/esp32s3/procpu <application>'
