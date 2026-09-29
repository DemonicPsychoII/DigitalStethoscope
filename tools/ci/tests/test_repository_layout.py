"""Executable contracts for the maintained repository layout, without provisioning."""

import ast
import base64
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.parse import unquote, urlsplit

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "software/evaluation/firmware"
LEGACY_WORKSPACE = "Development/system/coding/tools/zephyrproject"
POWERSHELL = shutil.which("powershell")


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("different_cwd", [False, True])
def test_ci_paths_and_stage_contract(tmp_path, monkeypatch, different_cwd):
    monkeypatch.chdir(tmp_path if different_cwd else ROOT)
    runner = load_module(ROOT / "tools/ci/run_ci.py", "layout_ci")
    assert runner.ROOT == ROOT
    assert runner.APP == APP
    for relative in ["CMakeLists.txt", "prj.conf", "qc.conf", "network.conf"]:
        assert (runner.APP / relative).is_file()
    logic = APP / "tests/logic"
    assert (logic / "../../include").resolve().is_dir()
    assert (logic / "../../src/app_logic.c").resolve().is_file()
    calls = []
    monkeypatch.setattr(runner, "run", lambda argv, **kwargs: calls.append(argv))
    monkeypatch.setattr(runner.subprocess, "check_output", lambda *args, **kwargs: b"")
    monkeypatch.setattr(runner.shutil, "which", lambda *args: None)
    monkeypatch.delenv("CI", raising=False)
    runner.static()
    assert calls == [
        ["git", "diff", "--check", "HEAD"],
        [sys.executable, "-m", "ruff", "check", "tools/ci"],
        [sys.executable, "-m", "ruff", "format", "--check", "tools/ci"],
    ]
    stages = []
    for stage in ["static", "build", "qc"]:
        monkeypatch.setattr(runner, stage, lambda stage=stage: stages.append(stage))
    monkeypatch.setattr(sys, "argv", ["run_ci.py", "all"])
    runner.main()
    assert stages == ["static", "build", "qc"]


@pytest.mark.parametrize(
    ("paths", "expected"),
    [
        ([], False),
        (["thesis/brief/draft.md"], False),
        (["software/evaluation/firmware-other/main.c", "tools/circuit/a.py"], False),
        (["software/evaluation/firmware/src/main.c"], True),
        (["tools/ci/requirements-ci.txt"], True),
        (["tools/toolchain/setup-toolchain.ps1"], True),
        (["tools/toolchain/setup_zephyr.sh"], True),
        ([".github/workflows/quality-gates.yml"], True),
        (["Development/system/coding/bringup-zephyr/src/main.c"], True),
        (["Development/system/testing/ci/requirements-ci.txt"], True),
        (["Development/system/coding/tools/setup-toolchain.ps1"], True),
        (["Development/Toolchain/zephyr-env.ps1"], True),
    ],
)
def test_firmware_watch_paths(paths, expected):
    detector = load_module(ROOT / "tools/ci/firmware_changes.py", "layout_detector")
    assert detector.needs_firmware(paths) is expected


@pytest.mark.parametrize(
    ("changed", "expected"),
    [
        (b"", False),
        (b"thesis/brief/only prose.md\0", False),
        (b"Development/system/coding/bringup-zephyr/deleted.c\0", True),
        (b"software/evaluation/firmware/deleted.c\0", True),
        (b"thesis/old name.md\0software/evaluation/firmware/new name.c\0", True),
        (b"software/evaluation/firmware/old name.c\0thesis/new name.md\0", True),
    ],
)
def test_detector_git_adapter_handles_deletions_and_rename_sides(
    tmp_path, monkeypatch, changed, expected
):
    detector = load_module(ROOT / "tools/ci/firmware_changes.py", "layout_adapter")
    output = tmp_path / "output.txt"
    monkeypatch.setenv("BASE_SHA", "base")
    monkeypatch.setenv("HEAD_SHA", "head")
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    calls = []

    def git_output(argv):
        calls.append(argv)
        return changed

    monkeypatch.setattr(detector.subprocess, "check_output", git_output)
    detector.main()
    assert calls == [
        ["git", "diff", "--name-only", "--no-renames", "-z", "base", "head", "--"]
    ]
    assert output.read_text() == f"firmware={str(expected).lower()}\n"


def test_workflow_inputs_and_pins():
    workflow = yaml.safe_load(
        (ROOT / ".github/workflows/quality-gates.yml").read_text()
    )
    assert workflow[True]["pull_request"]["branches"] == ["integration"]
    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["env"] == {
        "ZEPHYR_REVISION": "357467a011cd2557a1a3f0b4be83d817c4addc9b",
        "ZEPHYR_SDK_VERSION": "1.0.1",
        "WEST_VERSION": "1.5.0",
        "APP_DIR": "software/evaluation/firmware",
        "BOARD": "esp32s3_devkitc/esp32s3/procpu",
    }
    jobs = workflow["jobs"]
    assert jobs["static"]["name"] == "Quality / Static Checks"
    assert jobs["firmware"]["name"] == "Zephyr / Firmware Build"
    assert jobs["firmware"]["needs"] == "static"
    assert jobs["firmware"]["if"] == "needs.static.outputs.firmware == 'true'"
    allowed_actions = {
        "actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683",
        "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
    }
    commands = []
    for job in jobs.values():
        for step in job["steps"]:
            if "uses" in step:
                assert step["uses"] in allowed_actions
            for dependency in (
                step.get("with", {}).get("cache-dependency-path", "").splitlines()
            ):
                assert (ROOT / dependency).is_file()
            command = step.get("run", "")
            assert "Development/" not in command
            commands.append(command)
    joined = "\n".join(commands)
    for relative in [
        "tools/ci/firmware_changes.py",
        "tools/ci/run_ci.py",
        "tools/ci/requirements-ci.txt",
        "tools/toolchain/setup_zephyr.sh",
        "software/evaluation/firmware/tools/requirements.txt",
        "software/evaluation/firmware/tests/host",
        "tools/ci/tests/test_repository_layout.py",
    ]:
        assert relative in joined
        assert (ROOT / relative).exists()


def test_qc_live_output_and_cli_overrides(tmp_path, monkeypatch):
    evaluator = ROOT / "tools/qc/qc_eval.py"
    archive = ROOT / "verification-validation/reports/qc/2026-09-24"
    historic = {path: path.read_bytes() for path in archive.iterdir()}
    command = [sys.executable, str(evaluator), "--tha", str(tmp_path / "no-tha")]
    subprocess.run(command, cwd=tmp_path, check=True, capture_output=True)
    live = ROOT / "artifacts/qc/qc-eval-results.json"
    result = json.loads(live.read_text(encoding="utf-8"))
    assert result["target"] == "software/evaluation/firmware"
    assert result["gate"] == "PASS"
    assert all(path.read_bytes() == data for path, data in historic.items())
    custom = tmp_path / "custom output"
    subprocess.run(
        command + ["--repo", str(ROOT), "--output-dir", str(custom)],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    assert json.loads((custom / live.name).read_text(encoding="utf-8")) == result
    runner = load_module(ROOT / "tools/ci/run_ci.py", "layout_qc_reader")
    calls = []

    def run_qc(argv, **kwargs):
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(runner.subprocess, "run", run_qc)
    runner.qc()
    assert calls == [([sys.executable, str(evaluator)], {"cwd": ROOT})]


def test_qc_parity_with_preserved_maintained_baseline(tmp_path):
    baseline = ROOT / "artifacts/repository-migration/baseline"
    old_script = baseline / "Development/system/testing/qc_eval.py"
    if not old_script.is_file():
        pytest.skip(
            "Local pre-migration snapshot unavailable; parity requires W1 evidence"
        )
    old = load_module(old_script, "layout_qc_before")
    current = load_module(ROOT / "tools/qc/qc_eval.py", "layout_qc_after")
    before = old.evaluate(baseline, tmp_path / "no-tha")
    after = current.evaluate(ROOT, tmp_path / "no-tha")
    before.pop("target")
    after.pop("target")
    assert before == after


def test_research_registry_and_here_relative_inputs():
    investigation = ROOT / "research/investigations"
    runs = json.loads((investigation / "runs.json").read_text(encoding="utf-8"))
    assert len(runs) == 12
    assert len({run["id"] for run in runs}) == len(runs)
    for run in runs:
        assert (investigation / f"{run['id']}.md").is_file()
        json.loads((investigation / f"{run['id']}.json").read_text(encoding="utf-8"))
    runner = (investigation / "run_research.py").read_text(encoding="utf-8")
    here = next(
        node
        for node in ast.parse(runner).body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "HERE"
            for target in node.targets
        )
    )
    assert ast.unparse(here.value) == "os.path.dirname(os.path.abspath(__file__))"
    resolved = eval(
        compile(ast.Expression(here.value), "<HERE only>", "eval"),
        {"os": os, "__file__": str(investigation / "run_research.py")},
    )
    assert Path(resolved) == investigation
    assert 'os.path.join(HERE, "runs.json")' in runner
    assert (investigation / "research-log.txt").is_file()


@pytest.mark.parametrize(
    "relative",
    [
        "README.md",
        "AGENTS.md",
        "CONTRIBUTING.md",
        "software/product/README.md",
        "software/evaluation/host/README.md",
        "verification-validation/README.md",
        "REPO-MAP.md",
        "tools/ci/CI-QUALITY-GATES.md",
        "tools/qc/README.md",
        "software/evaluation/firmware/README.md",
        "software/evaluation/firmware/EVAL-GUIDE.md",
        "hardware/assembly/hardware.md",
        "engineering/decisions/open-questions.md",
        "engineering/decisions/widersprueche.md",
    ],
)
def test_navigation_links(relative):
    markdown = pytest.importorskip(
        "markdown_it", reason="Markdown parser unavailable; navigation links unverified"
    )
    parser = markdown.MarkdownIt()
    document = ROOT / relative
    tokens = parser.parse(document.read_text(encoding="utf-8"))
    for token in tokens:
        for child in token.children or []:
            if (
                relative.startswith("engineering/decisions/")
                and child.type == "code_inline"
            ):
                assert not child.content.startswith(
                    (
                        "../03-recherche/",
                        "01-aufgabenbeschreibung/",
                        "02-entscheidungen/",
                        "03-recherche/",
                        "05-hardware/",
                    )
                ), (relative, child.content)
            if child.type not in {"link_open", "image"}:
                continue
            link = urlsplit(child.attrGet("href") or child.attrGet("src"))
            if link.scheme or link.netloc:
                continue
            if (
                relative == "REPO-MAP.md"
                and link.path
                == "artifacts/repository-inventory/2026-09-29/REPO-FOLDER-INVENTORY.csv"
            ):
                continue
            target = (
                (document.parent / unquote(link.path)).resolve()
                if link.path
                else document
            )
            assert target.exists(), (relative, link.geturl())
            if link.fragment:
                target_tokens = parser.parse(target.read_text(encoding="utf-8"))
                headings = [
                    target_tokens[index + 1].content.lower().replace(" ", "-")
                    for index, item in enumerate(target_tokens)
                    if item.type == "heading_open"
                ]
                assert unquote(link.fragment) in headings, (relative, link.geturl())


def test_single_canonical_agent_policy():
    assert (ROOT / "AGENTS.md").is_file()
    assert not (ROOT / ".github/copilot-instructions.md").exists()


def test_actual_maintained_files_including_untracked_destinations():
    listed = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
    )
    files = {ROOT / raw.decode("utf-8") for raw in listed.split(b"\0") if raw}
    existing = {path for path in files if path.is_file()}
    assert APP / "src/main.c" in existing
    assert ROOT / "tools/ci/run_ci.py" in existing
    for path in existing:
        assert path.stat().st_size <= 5 * 1024 * 1024, path
        if path.suffix == ".py":
            compile(path.read_bytes(), str(path), "exec")
        elif path.suffix == ".json":
            json.loads(path.read_text(encoding="utf-8"))
        elif path.suffix in {".yaml", ".yml"}:
            yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("selection", ["legacy", "environment", "invalid-environment"])
def test_activation_entry_point_resolves_from_script_not_cwd(tmp_path, selection):
    repository = tmp_path / "repository with spaces"
    script = repository / "tools/toolchain/zephyr-env.ps1"
    script.parent.mkdir(parents=True)
    shutil.copy2(ROOT / "tools/toolchain/zephyr-env.ps1", script)
    workspace = repository / LEGACY_WORKSPACE
    for relative in [
        ".west/config",
        ".venv/Scripts/python.exe",
        ".venv/Scripts/west.exe",
        "zephyr/CMakeLists.txt",
        "zephyr-sdk-1.0.1/sdk_version",
    ]:
        target = workspace / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("1.0.1")
    environment = (
        None
        if selection == "legacy"
        else (LEGACY_WORKSPACE if selection == "environment" else "absent workspace")
    )
    code = f"""
$before = @{{path=$env:PATH; base=$env:ZEPHYR_BASE; sdk=$env:ZEPHYR_SDK_INSTALL_DIR}}
$failed = $false
try {{ & {ps_quote(script)} 6>$null }} catch {{ $failed = $true }}
$after = @{{path=$env:PATH; base=$env:ZEPHYR_BASE; sdk=$env:ZEPHYR_SDK_INSTALL_DIR}}
@{{before=$before; after=$after; failed=$failed}} | ConvertTo-Json -Compress
"""
    result = json.loads(powershell(code, tmp_path, environment).stdout)
    if selection == "invalid-environment":
        assert result["failed"]
        assert result["before"] == result["after"]
    else:
        assert not result["failed"]
        assert Path(result["after"]["base"]) == workspace / "zephyr"


def ps_quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def powershell(code, cwd, workspace_env=None):
    if not POWERSHELL:
        pytest.skip("Windows PowerShell unavailable; Windows contract unverified")
    env = os.environ.copy()
    env.pop("STETHO_ZEPHYR_WORKSPACE", None)
    if workspace_env is not None:
        env["STETHO_ZEPHYR_WORKSPACE"] = str(workspace_env)
    encoded = base64.b64encode(code.encode("utf-16-le")).decode("ascii")
    return subprocess.run(
        [POWERSHELL, "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )


@pytest.mark.parametrize("script", ["setup-toolchain.ps1", "zephyr-env.ps1"])
@pytest.mark.parametrize(
    "selection",
    [
        "explicit",
        "environment",
        "legacy",
        "relative",
        "missing",
        "invalid",
        "blank",
        "file",
    ],
)
def test_windows_workspace_resolver(tmp_path, script, selection):
    repository = tmp_path / "repo with spaces"
    legacy = repository / LEGACY_WORKSPACE
    legacy.mkdir(parents=True)
    chosen = repository / "chosen workspace"
    chosen.mkdir()
    unrelated = tmp_path / "other cwd"
    unrelated.mkdir()
    explicit = selection in {"explicit", "relative", "invalid", "blank", "file"}
    argument = str(chosen)
    env = None
    expected = legacy
    if selection in {"explicit", "relative"}:
        env = repository / "ignored invalid environment"
        argument = "chosen workspace" if selection == "relative" else str(chosen)
        expected = chosen
    elif selection == "environment":
        env = chosen
        expected = chosen
    elif selection == "invalid":
        argument = str(repository / "absent")
    elif selection == "blank":
        argument = " "
    elif selection == "file":
        argument = str(repository / "not a directory")
        Path(argument).write_text("fixture")
    elif selection == "missing":
        legacy.rmdir()
    source = ROOT / "tools/toolchain" / script
    code = f"""
$ErrorActionPreference = 'Stop'
$tokens = $null; $errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile({ps_quote(source)}, [ref]$tokens, [ref]$errors)
if ($errors.Count) {{ throw ($errors | Out-String) }}
$resolver = @($ast.FindAll({{param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Resolve-WorkspacePath'}}, $true))
if ($resolver.Count -ne 1) {{ throw 'Expected one pure workspace resolver' }}
$commands = @($resolver[0].FindAll({{param($node) $node -is [System.Management.Automation.Language.CommandAst]}}, $true) | ForEach-Object {{ $_.GetCommandName() }})
if (@($commands | Where-Object {{ $_ -notin @('Join-Path', 'Test-Path') }}).Count) {{ throw 'Resolver has side effects' }}
. ([ScriptBlock]::Create($resolver[0].Extent.Text))
$before = @(Get-ChildItem -LiteralPath {ps_quote(repository)} -Recurse -Force | ForEach-Object FullName)
try {{
    $resolved = Resolve-WorkspacePath -WorkspacePath {ps_quote(argument)} -RepositoryRoot {ps_quote(repository)} -Explicit ${str(explicit).lower()}
    $result = @{{path=$resolved; error=$null}}
}} catch {{ $result = @{{path=$null; error=$_.Exception.Message}} }}
$after = @(Get-ChildItem -LiteralPath {ps_quote(repository)} -Recurse -Force | ForEach-Object FullName)
if (Compare-Object $before $after) {{ throw 'Resolver changed filesystem' }}
$result | ConvertTo-Json -Compress
"""
    result = json.loads(powershell(code, unrelated, env).stdout)
    if selection in {"missing", "invalid", "blank", "file"}:
        assert result["error"]
        assert result["path"] is None
    else:
        assert result["error"] is None
        assert Path(result["path"]) == expected


@pytest.mark.parametrize("condition", ["valid", "incomplete", "wrong-sdk", "invalid"])
def test_activation_validates_before_environment_mutation(tmp_path, condition):
    workspace = tmp_path / "installed workspace"
    required = [
        ".west/config",
        ".venv/Scripts/python.exe",
        ".venv/Scripts/west.exe",
        "zephyr/CMakeLists.txt",
        "zephyr-sdk-1.0.1/sdk_version",
    ]
    for relative in required:
        target = workspace / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("1.0.1" if relative.endswith("sdk_version") else "fixture")
    if condition == "incomplete":
        (workspace / required[1]).unlink()
    if condition == "wrong-sdk":
        (workspace / required[-1]).write_text("0.0.0")
    selected = workspace / "absent" if condition == "invalid" else workspace
    script = ROOT / "tools/toolchain/zephyr-env.ps1"
    code = f"""
$ErrorActionPreference = 'Stop'
$before = @{{path=$env:PATH; base=$env:ZEPHYR_BASE; sdk=$env:ZEPHYR_SDK_INSTALL_DIR; cwd=(Get-Location).Path}}
$failed = $false
try {{ & {ps_quote(script)} -WorkspacePath {ps_quote(selected)} 6>$null }} catch {{ $failed = $true }}
$after = @{{path=$env:PATH; base=$env:ZEPHYR_BASE; sdk=$env:ZEPHYR_SDK_INSTALL_DIR; cwd=(Get-Location).Path}}
@{{before=$before; after=$after; failed=$failed}} | ConvertTo-Json -Compress
"""
    result = json.loads(powershell(code, tmp_path).stdout)
    if condition == "valid":
        assert not result["failed"]
        assert result["after"]["path"].endswith(result["before"]["path"])
        assert Path(result["after"]["base"]) == workspace / "zephyr"
        assert Path(result["after"]["sdk"]) == workspace / "zephyr-sdk-1.0.1"
        assert result["after"]["cwd"] == result["before"]["cwd"]
    else:
        assert result["failed"]
        assert result["after"] == result["before"]


@pytest.mark.parametrize("preference", ["Stop", "SilentlyContinue", "Ignore"])
@pytest.mark.parametrize("invocation", ["&", "."])
@pytest.mark.parametrize(
    "condition",
    ["unreadable-sdk", "empty-sdk", "invalid-explicit", "invalid-environment"],
)
def test_activation_invalid_inputs_preserve_caller(
    tmp_path, preference, invocation, condition
):
    workspace = tmp_path / "installed workspace"
    for relative in [
        ".west/config",
        ".venv/Scripts/python.exe",
        ".venv/Scripts/west.exe",
        "zephyr/CMakeLists.txt",
        "zephyr-sdk-1.0.1/sdk_version",
    ]:
        target = workspace / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("1.0.1")
    script = ROOT / "tools/toolchain/zephyr-env.ps1"
    version = workspace / "zephyr-sdk-1.0.1/sdk_version"
    if condition == "empty-sdk":
        version.write_text("")
    handle = (
        f"[IO.File]::Open({ps_quote(version)}, 'Open', 'ReadWrite', 'None')"
        if condition == "unreadable-sdk"
        else "$null"
    )
    setup = f"""
$ErrorActionPreference = '{preference}'
$env:PATH = 'PATH_SENTINEL'
$env:ZEPHYR_BASE = 'BASE_SENTINEL'
$env:ZEPHYR_SDK_INSTALL_DIR = 'SDK_SENTINEL'
$before = @{{path=$env:PATH; base=$env:ZEPHYR_BASE; sdk=$env:ZEPHYR_SDK_INSTALL_DIR; preference=[string]$ErrorActionPreference}}
$handle = {handle}
"""
    selected = workspace / "absent" if condition.startswith("invalid-") else workspace
    if condition == "invalid-environment":
        setup += f"$env:STETHO_ZEPHYR_WORKSPACE = {ps_quote(selected)}\n"
        argument = ""
    else:
        argument = f"-WorkspacePath {ps_quote(selected)}"
    activation = f"{invocation} {ps_quote(script)} {argument} 6>$null"
    report = """
if ($null -ne $handle) { $handle.Dispose() }
$after = @{path=$env:PATH; base=$env:ZEPHYR_BASE; sdk=$env:ZEPHYR_SDK_INSTALL_DIR; preference=[string]$ErrorActionPreference}
@{before=$before; after=$after; failed=$failed} | ConvertTo-Json -Compress
"""
    code = (
        setup
        + f"""
$failed = $true
try {{
    {activation}
    $failed = -not $?
}} finally {{
    {report}
}}
"""
    )
    try:
        output = powershell(code, tmp_path).stdout
    except subprocess.CalledProcessError as error:
        assert error.returncode == 1
        output = error.stdout
    result = json.loads(output)
    assert result["after"] == result["before"]
    assert result["failed"]
    try:
        output = powershell(
            setup + activation + "\n$failed = -not $?\n" + report,
            tmp_path,
        ).stdout
    except subprocess.CalledProcessError as error:
        assert error.returncode == 1
    else:
        result = json.loads(output)
        assert result["after"] == result["before"]
        assert result["failed"]
