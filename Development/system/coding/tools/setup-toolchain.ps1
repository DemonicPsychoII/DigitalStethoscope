#Requires -Version 5.1
<#
.SYNOPSIS
    Recreates the Zephyr toolchain workspace that is excluded from version control.

.DESCRIPTION
    Everything under tools/zephyrproject/ is third-party content (west modules,
    the Zephyr SDK, a Python virtual environment and Espressif binary blobs) and
    is therefore git-ignored. This script rebuilds that directory from scratch at
    the exact position and the exact revisions the firmware was tested against.

    It performs the following steps:
      1. verify host prerequisites (git, cmake, ninja, python, 7-Zip)
      2. create the Python virtual environment in tools/zephyrproject/.venv
      3. install west into that environment
      4. west init + checkout the pinned Zephyr revision + west update
      5. west packages pip --install and west zephyr-export
      6. install the Zephyr SDK with the Xtensa ESP32-S3 GNU toolchain
      7. fetch the Espressif binary blobs (required to build for ESP32-S3)

    The script is idempotent: steps that are already complete are skipped, so it
    can be re-run to repair a partial installation.

.PARAMETER ZephyrRevision
    Zephyr commit to check out. Defaults to the revision the bring-up firmware
    was verified against (reported as v4.4.0-11807-g357467a011c in the logs).

.PARAMETER SdkVersion
    Zephyr SDK version to install. Must match zephyr/SDK_VERSION.

.PARAMETER SdkToolchains
    GNU toolchains to install. Only the ESP32-S3 one is needed for this project;
    installing all of them costs several extra GB.

.PARAMETER SkipBlobs
    Skip 'west blobs fetch hal_espressif'. Builds for ESP32-S3 will fail without
    the blobs; only useful for offline or partial setups.

.PARAMETER Force
    Delete an existing tools/zephyrproject/ directory and start over.

.EXAMPLE
    .\setup-toolchain.ps1

.EXAMPLE
    .\setup-toolchain.ps1 -Force -Verbose
#>
[CmdletBinding(SupportsShouldProcess, ConfirmImpact = 'High')]
param(
    [string]   $ZephyrRevision = '357467a011cd2557a1a3f0b4be83d817c4addc9b',
    [string]   $SdkVersion     = '1.0.1',
    [string[]] $SdkToolchains  = @('xtensa-espressif_esp32s3_zephyr-elf'),
    [switch]   $SkipBlobs,
    [switch]   $Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# --------------------------------------------------------------------- paths
$ToolsDir     = $PSScriptRoot
$WorkspaceDir = Join-Path $ToolsDir 'zephyrproject'
$VenvDir      = Join-Path $WorkspaceDir '.venv'
$VenvPython   = Join-Path $VenvDir 'Scripts\python.exe'
$VenvWest     = Join-Path $VenvDir 'Scripts\west.exe'
$ZephyrDir    = Join-Path $WorkspaceDir 'zephyr'
$SdkDir       = Join-Path $WorkspaceDir "zephyr-sdk-$SdkVersion"
$ManifestUrl  = 'https://github.com/zephyrproject-rtos/zephyr'

# ------------------------------------------------------------------ helpers
function Write-Step {
    param([string]$Message)
    Write-Host ''
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Write-Skip {
    param([string]$Message)
    Write-Host "    (skipped) $Message" -ForegroundColor DarkGray
}

# Native tools signal failure via exit code, which PowerShell does not turn into
# a terminating error on its own.
function Invoke-Native {
    param(
        [Parameter(Mandatory)][string]   $FilePath,
        [Parameter(Mandatory)][string[]] $Arguments,
        [string] $WorkingDirectory
    )

    Write-Verbose "$FilePath $($Arguments -join ' ')"

    if ($WorkingDirectory) {
        Push-Location $WorkingDirectory
    }
    try {
        & $FilePath @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "'$([System.IO.Path]::GetFileName($FilePath)) $($Arguments -join ' ')' failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        if ($WorkingDirectory) {
            Pop-Location
        }
    }
}

function Resolve-HostPython {
    # Zephyr 4.4 requires Python >= 3.10.
    $candidates = @()
    foreach ($name in 'python', 'python3') {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) { $candidates += $cmd.Source }
    }
    if (Get-Command 'py' -ErrorAction SilentlyContinue) {
        # No quotes inside the snippet: PowerShell 5.1 strips them from native args.
        $candidates += (& py -3 -c 'import sys; print(sys.executable)' 2>$null)
    }

    foreach ($exe in ($candidates | Where-Object { $_ } | Select-Object -Unique)) {
        $banner = (& $exe -V 2>&1) -join ' '
        if ($LASTEXITCODE -eq 0 -and $banner -match 'Python\s+(\d+\.\d+(\.\d+)?)') {
            $version = [version]$Matches[1]
            if ($version -ge [version]'3.10') {
                Write-Verbose "Using host Python $version at $exe"
                return $exe
            }
            Write-Verbose "Ignoring Python $version at $exe (need >= 3.10)"
        }
    }
    throw 'No Python 3.10 or newer found on PATH. Install it from https://www.python.org/downloads/ and re-run.'
}

# ------------------------------------------------------- 1. prerequisites
Write-Step 'Checking host prerequisites'

$missing = @()
foreach ($tool in 'git', 'cmake', 'ninja') {
    if (Get-Command $tool -ErrorAction SilentlyContinue) {
        Write-Host "    $tool ok"
    } else {
        $missing += $tool
    }
}
if ($missing.Count -gt 0) {
    throw ("Missing required host tools: {0}. Install them, e.g.:`n" -f ($missing -join ', ')) +
          "    winget install Git.Git Kitware.CMake Ninja-build.Ninja"
}

$HostPython = Resolve-HostPython
Write-Host "    python ok ($HostPython)"

# The SDK archive is a .7z; patoolib cannot unpack it without 7-Zip on PATH.
if (Get-Command '7z' -ErrorAction SilentlyContinue) {
    Write-Host '    7z ok'
} else {
    $sevenZip = @(
        "$env:ProgramFiles\7-Zip\7z.exe"
        "${env:ProgramFiles(x86)}\7-Zip\7z.exe"
    ) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1

    if (-not $sevenZip) {
        throw "7-Zip is required to extract the Zephyr SDK archive but '7z' was not found.`n" +
              '    winget install 7zip.7zip'
    }
    # patoolib resolves 7z via PATH, so make it visible for this session.
    $env:PATH = "$(Split-Path $sevenZip -Parent);$env:PATH"
    Write-Host "    7z ok ($sevenZip, added to PATH for this session)"
}

# gperf and dtc are only needed by a few boards; ESP32-S3 builds fine without them.
foreach ($tool in 'gperf', 'dtc') {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        Write-Host "    $tool not found - optional, not required for ESP32-S3" -ForegroundColor DarkGray
    }
}

# --------------------------------------------------- 2. clean / create root
if ($Force -and (Test-Path $WorkspaceDir)) {
    if ($PSCmdlet.ShouldProcess($WorkspaceDir, 'Delete the existing toolchain workspace')) {
        Write-Step "Removing existing workspace $WorkspaceDir"
        Remove-Item -LiteralPath $WorkspaceDir -Recurse -Force
    } else {
        throw 'Aborted by user.'
    }
}

if (-not (Test-Path $WorkspaceDir)) {
    New-Item -ItemType Directory -Path $WorkspaceDir | Out-Null
}

# ---------------------------------------------------- 3. virtual environment
Write-Step 'Setting up the Python virtual environment'
if (Test-Path $VenvPython) {
    Write-Skip "$VenvDir already exists"
} else {
    Invoke-Native -FilePath $HostPython -Arguments @('-m', 'venv', $VenvDir)
}
Invoke-Native -FilePath $VenvPython -Arguments @('-m', 'pip', 'install', '--upgrade', 'pip')

# ------------------------------------------------------------- 4. west tool
Write-Step 'Installing west'
if (Test-Path $VenvWest) {
    Write-Skip 'west already installed'
} else {
    Invoke-Native -FilePath $VenvPython -Arguments @('-m', 'pip', 'install', 'west')
}

# ------------------------------------------------- 5. Zephyr sources (west)
Write-Step "Fetching Zephyr and its modules (revision $($ZephyrRevision.Substring(0,12)))"
if (Test-Path (Join-Path $WorkspaceDir '.west\config')) {
    Write-Skip 'west workspace already initialised'
} else {
    Invoke-Native -FilePath $VenvWest -Arguments @('init', '-m', $ManifestUrl, '--mr', 'main', $WorkspaceDir)
}

# Pin to the exact revision the firmware was tested against before pulling the
# modules, so the module revisions come from that manifest.
Invoke-Native -FilePath 'git' -Arguments @('fetch', 'origin') -WorkingDirectory $ZephyrDir
Invoke-Native -FilePath 'git' -Arguments @('checkout', '--detach', $ZephyrRevision) -WorkingDirectory $ZephyrDir

Invoke-Native -FilePath $VenvWest -Arguments @('update') -WorkingDirectory $WorkspaceDir

# Must run before zephyr-export, which fails on a missing jsonschema otherwise.
Write-Step 'Installing the Python packages required by Zephyr'
Invoke-Native -FilePath $VenvWest -Arguments @('packages', 'pip', '--install') -WorkingDirectory $WorkspaceDir

Invoke-Native -FilePath $VenvWest -Arguments @('zephyr-export') -WorkingDirectory $WorkspaceDir

# --------------------------------------------------------- 6. Zephyr SDK
Write-Step "Installing the Zephyr SDK $SdkVersion ($($SdkToolchains -join ', '))"
if (Test-Path (Join-Path $SdkDir 'sdk_version')) {
    Write-Skip "$SdkDir already present"
} else {
    # -b places the archive's zephyr-sdk-<version> folder inside the workspace.
    $sdkArgs = @('sdk', 'install', '--version', $SdkVersion, '-b', $WorkspaceDir, '-t') + $SdkToolchains
    Invoke-Native -FilePath $VenvWest -Arguments $sdkArgs -WorkingDirectory $WorkspaceDir
}

# ------------------------------------------------------ 7. Espressif blobs
if ($SkipBlobs) {
    Write-Step 'Skipping Espressif binary blobs (-SkipBlobs)'
} else {
    Write-Step 'Fetching the Espressif binary blobs'
    Invoke-Native -FilePath $VenvWest -Arguments @('blobs', 'fetch', 'hal_espressif') -WorkingDirectory $WorkspaceDir
}

# ------------------------------------------------------------- 8. summary
Write-Step 'Installed versions'
Invoke-Native -FilePath $VenvPython -Arguments @('--version')
Invoke-Native -FilePath $VenvWest   -Arguments @('--version')
Write-Host "    zephyr    $(git -C $ZephyrDir describe --tags)"
Write-Host "    sdk       $(Get-Content (Join-Path $SdkDir 'sdk_version'))"

$appDir = Join-Path (Split-Path $ToolsDir -Parent) 'bringup-zephyr'

Write-Host ''
Write-Host 'Toolchain ready.' -ForegroundColor Green
Write-Host 'Open a new shell and run:' -ForegroundColor Green
Write-Host @"

    & "$VenvDir\Scripts\Activate.ps1"
    `$env:ZEPHYR_BASE = "$ZephyrDir"
    Set-Location "$appDir"
    west build -b esp32s3_devkitc/esp32s3/procpu .
    west flash --esp-device COM6
"@
