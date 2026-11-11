#Requires -Version 5.1
# Runs toolchain_environment.py, which resolves the pinned workspace like CI.
# Dot-source it: . (Join-Path $PSScriptRoot 'toolchain-resolver.ps1')

function Invoke-ToolchainResolver {
    param([string[]]$Arguments)
    $resolver = Join-Path $PSScriptRoot 'toolchain_environment.py'
    # `python` can be the inactive Microsoft Store alias; the launcher is the fallback.
    # Only an interpreter that cannot run Python 3.12+ falls through to the next one.
    $interpreter = $null
    foreach ($candidate in @(, @('python')) + @(, @('py', '-3'))) {
        if (-not (Get-Command $candidate[0] -ErrorAction SilentlyContinue)) { continue }
        $launcherArguments = @($candidate | Select-Object -Skip 1)
        & $candidate[0] @launcherArguments -c 'import sys; sys.exit(sys.version_info < (3, 12))' 2>$null
        if ($LASTEXITCODE -eq 0) { $interpreter = $candidate; break }
    }
    if (-not $interpreter) { throw 'Python 3.12 or newer is required as python or py -3.' }
    # Windows PowerShell 5.1 decodes native output with the console code page, but the
    # resolver writes UTF-8; non-ASCII profile paths would arrive corrupted.
    $previousEncoding = [Console]::OutputEncoding
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    try {
        $launcherArguments = @($interpreter | Select-Object -Skip 1)
        $output = & $interpreter[0] @launcherArguments $resolver @Arguments
        if ($LASTEXITCODE -ne 0) { throw 'Pinned toolchain not resolved; see the message above.' }
        return $output
    }
    finally { [Console]::OutputEncoding = $previousEncoding }
}
