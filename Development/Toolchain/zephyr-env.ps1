# Dot-source to put the pinned west, CMake and Ninja on PATH and set the Zephyr
# variables: . .\Development\Toolchain\zephyr-env.ps1
# The workspace is the one shared by all checkouts and worktrees for the current pins.
. (Join-Path $PSScriptRoot '..\system\coding\tools\toolchain\toolchain-resolver.ps1')

$description = Invoke-ToolchainResolver -Arguments '--format', 'json'
$toolchain = $description -join "`n" | ConvertFrom-Json

foreach ($property in $toolchain.variables.PSObject.Properties) {
    Set-Item "Env:\$($property.Name)" $property.Value
}
$env:PATH = (@($toolchain.path) + $env:PATH) -join [System.IO.Path]::PathSeparator

Write-Host "Zephyr environment enabled from $($toolchain.workspace)"
foreach ($tool in 'west', 'cmake', 'ninja') {
    Write-Host "  $tool -> $((Get-Command $tool -ErrorAction Stop).Source)"
}
Write-Host 'west build -b esp32s3_devkitc/esp32s3/procpu <application>'
