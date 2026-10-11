$configPath = Join-Path $PSScriptRoot '../../.ci-workspace/eval-environment.json'
if (Test-Path $configPath) {
    $config = Get-Content $configPath -Raw | ConvertFrom-Json
    $env:PATH = "$(Split-Path $config.python -Parent);$env:PATH"
    $env:ZEPHYR_BASE = $config.zephyr
    $env:ZEPHYR_SDK_INSTALL_DIR = $config.sdk
    Write-Host "Evaluation environment enabled from $($config.workspace)"
    return
}
$workspace = Join-Path $PSScriptRoot 'zephyrproject'
if (-not (Test-Path (Join-Path $workspace '.venv/Scripts/python.exe'))) {
    throw 'Run Development/Toolchain/setup-eval.ps1 first.'
}

$env:PATH = "$(Join-Path $workspace '.venv\Scripts');$env:PATH"
$env:ZEPHYR_BASE = Join-Path $workspace 'zephyr'
$env:ZEPHYR_SDK_INSTALL_DIR = Join-Path $workspace 'zephyr-sdk-1.0.1'

Write-Host "Zephyr environment enabled from $workspace"
Write-Host 'west build -b esp32s3_devkitc/esp32s3/procpu <application>'
