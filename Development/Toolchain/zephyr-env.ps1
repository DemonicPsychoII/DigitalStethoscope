# Dot-source to put the pinned west, CMake and Ninja on PATH and set the Zephyr
# variables: . .\Development\Toolchain\zephyr-env.ps1
# The workspace is the one shared by all checkouts and worktrees for the current pins.
function Invoke-ToolchainResolver {
    param([string]$Resolver, [string[]]$Arguments)
    # Windows PowerShell 5.1 decodes native output with the console code page, but the
    # resolver writes UTF-8; non-ASCII profile paths would arrive corrupted.
    $previousEncoding = [Console]::OutputEncoding
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    try {
        # `python` can be the inactive Microsoft Store alias; the launcher is the fallback.
        foreach ($candidate in @(, @('python')) + @(, @('py', '-3'))) {
            if (-not (Get-Command $candidate[0] -ErrorAction SilentlyContinue)) { continue }
            $launcherArguments = @($candidate | Select-Object -Skip 1)
            $output = & $candidate[0] @launcherArguments $Resolver @Arguments
            if ($LASTEXITCODE -eq 0) { return $output }
        }
    }
    finally { [Console]::OutputEncoding = $previousEncoding }
    throw 'Pinned toolchain not resolved; needs Python 3.12+ as python or py -3, see the message above.'
}

$repo = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$resolver = Join-Path $repo 'Development\system\coding\tools\toolchain\toolchain_environment.py'
$description = Invoke-ToolchainResolver -Resolver $resolver -Arguments '--format', 'json'
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
