param([string]$WorkspacePath)

& {
	param([string]$WorkspacePath, [bool]$ExplicitWorkspacePath)
	$ErrorActionPreference = 'Stop'

	function Resolve-WorkspacePath {
		param([string]$WorkspacePath, [string]$RepositoryRoot, [bool]$Explicit)

		$selected = if ($Explicit) { $WorkspacePath }
			elseif ($null -ne $env:STETHO_ZEPHYR_WORKSPACE) { $env:STETHO_ZEPHYR_WORKSPACE }
			else { 'Development/system/coding/tools/zephyrproject' }
		if ([string]::IsNullOrWhiteSpace($selected)) {
			throw 'Choose an existing workspace with -WorkspacePath or STETHO_ZEPHYR_WORKSPACE.'
		}
		if (-not [System.IO.Path]::IsPathRooted($selected)) {
			$selected = Join-Path $RepositoryRoot $selected
		}
		$selected = [System.IO.Path]::GetFullPath($selected)
		if (-not (Test-Path -LiteralPath $selected -PathType Container)) {
			throw "Workspace does not exist: $selected. Choose an existing directory with -WorkspacePath or STETHO_ZEPHYR_WORKSPACE; provisioning requires separate authorization."
		}
		return $selected
	}

	$RepositoryRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
	$workspace = Resolve-WorkspacePath -WorkspacePath $WorkspacePath -RepositoryRoot $RepositoryRoot -Explicit $ExplicitWorkspacePath
	$required = @('.west/config', '.venv/Scripts/python.exe', '.venv/Scripts/west.exe', 'zephyr/CMakeLists.txt', 'zephyr-sdk-1.0.1/sdk_version')
	foreach ($relative in $required) {
		if (-not (Test-Path -LiteralPath (Join-Path $workspace $relative) -PathType Leaf)) {
			throw "Incomplete workspace: missing $relative in $workspace. Environment unchanged."
		}
	}
	if ((Get-Content -LiteralPath (Join-Path $workspace 'zephyr-sdk-1.0.1/sdk_version') -Raw).Trim() -ne '1.0.1') {
		throw 'Expected Zephyr SDK 1.0.1. Environment unchanged.'
	}

	$env:PATH = "$(Join-Path $workspace '.venv\Scripts');$env:PATH"
	$env:ZEPHYR_BASE = Join-Path $workspace 'zephyr'
	$env:ZEPHYR_SDK_INSTALL_DIR = Join-Path $workspace 'zephyr-sdk-1.0.1'

	Write-Host "Zephyr environment enabled from $workspace"
	Write-Host 'west build -b esp32s3_devkitc/esp32s3/procpu <application>'
} $WorkspacePath $PSBoundParameters.ContainsKey('WorkspacePath')
