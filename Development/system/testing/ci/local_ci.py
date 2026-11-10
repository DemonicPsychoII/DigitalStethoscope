#!/usr/bin/env python3
"""Run the CI quality-gate stages from any checkout, natively or on homelab-annex.

The stages run the same commands as .github/workflows/quality-gates.yml:

  static  verification identity, documentation, manual records, run_ci.py static
  unit    build tooling and merge-gate regression tests
  host    application host scenarios with sanitizers, then production coverage
  build   run_ci.py build --application, then the ELF path and build ID

`--mode auto` runs a stage natively when this device has its toolchain and otherwise
on homelab-annex: it wakes the annex, ships the working tree including uncommitted
changes, runs the stage there, copies `artifacts/` back and removes the scratch copy.
`--detach` returns at once; `follow` streams the progress log of a detached run.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import shlex
import shutil
import socket
import struct
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

import toolchain_path  # noqa: F401
from build_support import (
    bin_dir,
    python_path,
    toolchain_workspace,
    user_cache_directory,
    workspace_matches_pins,
)
from prepared_env import STATIC_PYTHON

ROOT = Path(__file__).resolve().parents[4]
CI = ROOT / "Development/system/testing/ci"
ARTIFACTS = ROOT / "artifacts"
RUNS = ARTIFACTS / "local-ci"
STAGES = ("static", "unit", "host", "build")
REMOTE_HOST = "homelab-annex"
POWER_HOST = "homelab-server"
REMOTE_SCRATCH = "stethoscope-local-ci"
KEEP_REFRESH_SECONDS = 20 * 60
POLL_SECONDS = 10
STILL_RUNNING = 3
REQUIREMENTS = (CI / "requirements-ci.txt", CI / "requirements-host.txt")
STATIC_PYTHON_MINOR = tuple(int(part) for part in STATIC_PYTHON.split(".")[:2])
UTF8_ENVIRONMENT = {
    "PYTHONUTF8": "1",
    "PYTHONIOENCODING": "utf-8",
    "PYTHONUNBUFFERED": "1",
}


class StageFailure(Exception):
    pass


def configure_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def child_environment(extra: dict[str, str] | None = None) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(UTF8_ENVIRONMENT)
    environment.update(extra or {})
    return environment


def run_command(
    argv: list[str], environment: dict[str, str] | None = None, check: bool = True
) -> int:
    print("+", subprocess.list2cmdline(argv), flush=True)
    result = subprocess.run(argv, cwd=ROOT, env=environment or child_environment())
    if check and result.returncode:
        command = " ".join([Path(argv[0]).name, *argv[1:3]])
        raise StageFailure(f"{command} failed ({result.returncode})")
    return result.returncode


# Native environments


def ci_interpreter() -> str:
    """A Python of the CI minor version; the requirement hashes cover only its wheels."""
    if sys.version_info[:2] == STATIC_PYTHON_MINOR:
        return sys.executable
    uv = shutil.which("uv") or str(Path.home() / ".local/bin/uv")
    if Path(uv).is_file():
        found = subprocess.run(
            [uv, "python", "find", STATIC_PYTHON], capture_output=True, text=True
        )
        if found.returncode:
            run_command([uv, "python", "install", STATIC_PYTHON])
            found = subprocess.run(
                [uv, "python", "find", STATIC_PYTHON], capture_output=True, text=True
            )
        if not found.returncode:
            return found.stdout.strip()
    minor = ".".join(map(str, STATIC_PYTHON_MINOR))
    if shutil.which(f"python{minor}"):
        return shutil.which(f"python{minor}")
    raise StageFailure(
        f"Python {minor} is required for the hash-locked CI requirements; "
        f"install uv or Python {STATIC_PYTHON}"
    )


def python_environment() -> Path:
    """Shared virtual environment with the hash-locked CI and host requirements."""
    digest = hashlib.sha256()
    for requirement in REQUIREMENTS:
        digest.update(requirement.read_bytes())
    version = ".".join(map(str, STATIC_PYTHON_MINOR))
    workspace = (
        user_cache_directory()
        / "stethoscope-python"
        / f"python{version}-{digest.hexdigest()[:16]}"
    )
    stamp = workspace / ".stethoscope-requirements"
    python = python_path(workspace)
    if stamp.is_file() and python.is_file():
        return python
    print(f"Creating the CI Python environment in {workspace}", flush=True)
    shutil.rmtree(workspace, ignore_errors=True)
    run_command([ci_interpreter(), "-m", "venv", str(workspace / ".venv")])
    requirement_arguments = [
        argument for path in REQUIREMENTS for argument in ("-r", str(path))
    ]
    run_command(
        [
            str(python),
            *("-m", "pip", "install", "--disable-pip-version-check"),
            "--require-hashes",
            *requirement_arguments,
        ]
    )
    write_text(stamp, digest.hexdigest() + "\n")
    return python


def validation_tools(python: Path) -> Path:
    """Linux validators and Node, shared by all checkouts and reused once verified."""
    pins = (CI / "validation_tools.json").read_bytes()
    target = (
        user_cache_directory()
        / "stethoscope-validation-tools"
        / hashlib.sha256(pins).hexdigest()[:16]
    )
    run_command(
        [
            str(python),
            str(CI / "validation_tools.py"),
            *("--target", str(target), "--prepared", str(target)),
        ]
    )
    return target


def compiler_available() -> bool:
    command = shlex.split(os.environ.get("CC", "gcc"))
    return bool(command) and shutil.which(command[0]) is not None


def toolchain_ready() -> bool:
    workspace = toolchain_workspace()
    west = bin_dir(workspace) / ("west.exe" if os.name == "nt" else "west")
    return west.is_file() and (workspace / "zephyr").is_dir()


def native_blocker(stage: str, provision: bool) -> str | None:
    if stage == "host":
        if sys.platform == "win32":
            return "host scenarios need GCC with sanitizers on Linux"
        if not compiler_available():
            return "no C compiler: install gcc or set CC"
    if stage == "build" and not provision and not toolchain_ready():
        return f"pinned firmware toolchain missing in {toolchain_workspace()}"
    return None


# Native stages


def static_stage() -> None:
    python = str(python_environment())
    environment = child_environment()
    if sys.platform != "win32":
        tools = validation_tools(Path(python))
        environment["PATH"] = os.pathsep.join((str(tools), environment["PATH"]))
    for script in ("ci_evidence.py", "validate_docs.py", "manual_test_records.py"):
        run_command([python, str(CI / script)], environment)
    run_command([python, str(CI / "run_ci.py"), "static"], environment)


def unit_stage() -> None:
    python = str(python_environment())
    run_command(
        [python, "-m", "unittest", "discover", "-s", str(CI), "-p", "test_*.py"]
    )
    run_command(
        [python, "-m", "unittest", "discover", "-s", str(ROOT / ".github/agent-gate")]
    )


def host_stage() -> None:
    python = str(python_environment())
    tests = str(ROOT / "Development/system/coding/app/tests/host")
    results = ARTIFACTS / "ci"
    extra = {}
    if sys.platform != "win32":
        extra["STETHO_NODE"] = str(validation_tools(Path(python)) / "node")
    scenarios = run_command(
        [
            *(python, "-m", "pytest", "-q", "-o", "junit_family=xunit1"),
            f"--junitxml={results / 'application-host.xml'}",
            tests,
        ],
        child_environment({**extra, "STETHO_SANITIZERS": "true"}),
        check=False,
    )
    run_command(
        [
            python,
            str(CI / "application_host_results.py"),
            str(results / "application-host.xml"),
        ]
    )
    if scenarios:
        raise StageFailure("application host scenarios failed")
    coverage = results / "host-coverage"
    shutil.rmtree(coverage, ignore_errors=True)
    run_command(
        [
            *(python, "-m", "pytest", "-q", "-o", "junit_family=xunit1"),
            f"--junitxml={results / 'application-coverage.xml'}",
            tests,
        ],
        child_environment(
            {
                **extra,
                "STETHO_SANITIZERS": "false",
                "STETHO_COVERAGE_DIRECTORY": str(coverage),
            }
        ),
    )
    run_command([python, str(CI / "host_coverage.py"), str(coverage)])


def provision_toolchain() -> None:
    workspace = toolchain_workspace()
    if toolchain_ready() and workspace_matches_pins(workspace):
        return
    print(f"Provisioning the pinned firmware toolchain in {workspace}", flush=True)
    run_command(
        [
            sys.executable,
            str(ROOT / "Development/system/coding/tools/toolchain/setup_zephyr.py"),
            *("--workspace", str(workspace)),
        ]
    )


def build_stage(provision: bool) -> None:
    if provision:
        provision_toolchain()
    workspace = toolchain_workspace()
    print(f"Toolchain workspace: {workspace}", flush=True)
    run_command(
        [str(python_path(workspace)), str(CI / "run_ci.py"), "build", "--application"]
    )
    describe_firmware(include_build_directory=True)


# Firmware identity


def gnu_build_id(data: bytes) -> str | None:
    """Return the NT_GNU_BUILD_ID note of an ELF image, if it was linked with one."""
    if data[:4] != b"\x7fELF":
        return None
    is_64_bit = data[4] == 2
    order = "<" if data[5] == 1 else ">"
    if is_64_bit:
        section_offset = struct.unpack_from(order + "Q", data, 0x28)[0]
        entry_size, count = struct.unpack_from(order + "HH", data, 0x3A)
        layout = order + "IIQQQQ"
    else:
        section_offset = struct.unpack_from(order + "I", data, 0x20)[0]
        entry_size, count = struct.unpack_from(order + "HH", data, 0x2E)
        layout = order + "IIIIII"
    for index in range(count):
        fields = struct.unpack_from(layout, data, section_offset + index * entry_size)
        section_type, offset, size = fields[1], fields[4], fields[5]
        if section_type != 7:  # SHT_NOTE
            continue
        position = offset
        while position + 12 <= offset + size:
            name_size, description_size, note_type = struct.unpack_from(
                order + "III", data, position
            )
            name_start = position + 12
            description_start = name_start + (name_size + 3) // 4 * 4
            name = data[name_start : name_start + name_size].rstrip(b"\0")
            if note_type == 3 and name == b"GNU":
                return data[
                    description_start : description_start + description_size
                ].hex()
            position = description_start + (description_size + 3) // 4 * 4
    return None


def describe_firmware(include_build_directory: bool) -> None:
    """Name the exact ELF of this build, so crash decoding uses the matching binary.

    A remote build returns only the retained ELF; a local build directory then holds
    an older build and is not listed.
    """
    elves = [ARTIFACTS / "firmware/application/zephyr.elf"]
    if include_build_directory:
        elves.append(ROOT / "build-ci-app/zephyr/zephyr.elf")
    manifest = ARTIFACTS / "firmware-release/manifest.json"
    if manifest.is_file():
        for entry in json.loads(manifest.read_text(encoding="utf-8"))["files"]:
            print(f"Firmware version: {entry['version']} ({entry['name']})")
    for elf in elves:
        if not elf.is_file():
            continue
        data = elf.read_bytes()
        build_id = gnu_build_id(data)
        print(f"Firmware ELF: {elf}")
        print(f"  GNU build ID: {build_id or 'none (linked without a build-id note)'}")
        print(f"  SHA-256: {hashlib.sha256(data).hexdigest()}", flush=True)


# Stage execution


def execute_native(stages: list[str], provision: bool) -> dict[str, dict]:
    actions = {
        "static": static_stage,
        "unit": unit_stage,
        "host": host_stage,
        "build": lambda: build_stage(provision),
    }
    results = {}
    for stage in stages:
        print(f"\n== {stage} (native on {socket.gethostname()}) ==", flush=True)
        started = time.monotonic()
        try:
            blocker = native_blocker(stage, provision)
            if blocker:
                raise StageFailure(blocker)
            actions[stage]()
            outcome = "passed"
            detail = ""
        except (StageFailure, SystemExit, subprocess.SubprocessError, OSError) as error:
            outcome = "failed"
            detail = str(error)
            print(f"{stage} failed: {detail}", flush=True)
        results[stage] = {
            "outcome": outcome,
            "detail": detail,
            "seconds": round(time.monotonic() - started),
            "where": socket.gethostname(),
        }
    return results


def plan(stages: list[str], mode: str, provision: bool) -> dict[str, str]:
    placement = {}
    for stage in stages:
        if mode == "auto":
            blocker = native_blocker(stage, provision)
            local_host = socket.gethostname().lower() == REMOTE_HOST
            placement[stage] = "remote" if blocker and not local_host else "native"
            if blocker:
                print(f"{stage}: {blocker}; running it {placement[stage]}ly")
        else:
            placement[stage] = mode
    return placement


def print_summary(results: dict[str, dict]) -> int:
    print("\n== summary ==")
    for stage, result in results.items():
        line = f"{stage:7} {result['outcome']:7} {result['seconds']:5d} s  on {result['where']}"
        print(line + (f"  ({result['detail']})" if result["detail"] else ""))
    print(f"Artifacts: {ARTIFACTS}", flush=True)
    passed = all(result["outcome"] == "passed" for result in results.values())
    return 0 if passed else 1


# Remote execution on homelab-annex


def ssh_command(host: str, command: str) -> list[str]:
    options = ("-o", "BatchMode=yes", "-o", "ConnectTimeout=20")
    return ["ssh", *options, "-o", "ServerAliveInterval=30", host, command]


def ssh(
    host: str,
    command: str,
    input_bytes: bytes | None = None,
    timeout: float | None = 120,
    check: bool = True,
) -> subprocess.CompletedProcess:
    result = subprocess.run(
        ssh_command(host, command),
        input=input_bytes,
        capture_output=True,
        timeout=timeout,
    )
    if check and result.returncode:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise StageFailure(f"ssh {host} failed ({result.returncode}): {message}")
    return result


def annex_power(*arguments: str) -> None:
    command = shlex.join(["annex-power", *arguments])
    if socket.gethostname().lower() == POWER_HOST:
        argv = ["bash", "-c", command]
    else:
        argv = ssh_command(POWER_HOST, command)
    result = subprocess.run(argv, capture_output=True, timeout=300)
    output = (result.stdout + result.stderr).decode("utf-8", errors="replace").strip()
    print(f"annex-power {' '.join(arguments)}: {output}", flush=True)
    if result.returncode:
        raise StageFailure(f"annex-power {arguments[0]} failed ({result.returncode})")


def wait_until_reachable(deadline_seconds: int = 300) -> None:
    deadline = time.monotonic() + deadline_seconds
    while True:
        try:
            if not ssh(REMOTE_HOST, "true", timeout=40, check=False).returncode:
                return
        except subprocess.TimeoutExpired:
            pass
        if time.monotonic() > deadline:
            raise StageFailure(f"{REMOTE_HOST} did not become reachable")
        time.sleep(5)


def git_output(*arguments: str) -> str:
    return subprocess.check_output(["git", *arguments], cwd=ROOT, text=True).strip()


def payload() -> bytes:
    """The committed history of HEAD plus the working tree as it is now."""
    listed = subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
    )
    # Windows checkouts lose the executable bit; the index keeps the committed mode.
    staged = subprocess.check_output(["git", "ls-files", "-z", "--stage"], cwd=ROOT)
    executables = {
        entry.split(b"\t", 1)[1].decode("utf-8")
        for entry in filter(None, staged.split(b"\0"))
        if entry.startswith(b"100755 ")
    }

    def committed_mode(member: tarfile.TarInfo) -> tarfile.TarInfo:
        relative = member.name.removeprefix("tree/")
        member.mode = 0o755 if relative in executables else 0o644
        return member

    buffer = io.BytesIO()
    with tempfile.TemporaryDirectory() as directory:
        bundle = Path(directory) / "repository.bundle"
        subprocess.run(
            ["git", "bundle", "create", "--quiet", str(bundle), "HEAD"],
            cwd=ROOT,
            check=True,
        )
        with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
            archive.add(bundle, arcname="repository.bundle")
            for raw in filter(None, listed.split(b"\0")):
                relative = raw.decode("utf-8")
                path = ROOT / relative
                # Deleted files stay absent, so the copy shows the same changes.
                if path.is_file():
                    archive.add(
                        path,
                        arcname=f"tree/{relative}",
                        recursive=False,
                        filter=committed_mode if os.name == "nt" else None,
                    )
    return buffer.getvalue()


def remote_prepare(scratch: str) -> None:
    head = git_output("rev-parse", "HEAD")
    branch = git_output("rev-parse", "--abbrev-ref", "HEAD")
    point_head = (
        f"git update-ref refs/heads/{shlex.quote(branch)} {head}"
        f" && git symbolic-ref HEAD refs/heads/{shlex.quote(branch)}"
        if branch != "HEAD"
        else f"git update-ref --no-deref HEAD {head}"
    )
    script = f"""set -euo pipefail
mkdir -p "$HOME/{REMOTE_SCRATCH}"
# Remove copies that interrupted runs left behind.
find "$HOME/{REMOTE_SCRATCH}" -mindepth 1 -maxdepth 1 -mtime +1 -exec rm -rf {{}} +
scratch="$HOME/{scratch}"
mkdir -p "$scratch"
tar -xzf - -C "$scratch"
mkdir -p "$scratch/tree"
cd "$scratch/tree"
git init -q
git fetch -q ../repository.bundle HEAD
{point_head}
git reset -q
rm ../repository.bundle
git status --short | head -20
"""
    data = payload()
    print(f"Shipping {len(data) / 1e6:.1f} MB to {REMOTE_HOST}:~/{scratch}", flush=True)
    result = ssh(REMOTE_HOST, f"bash -c {shlex.quote(script)}", data, timeout=600)
    changes = result.stdout.decode("utf-8", errors="replace").rstrip()
    if changes:
        print("Uncommitted changes in the copy:\n" + changes, flush=True)


def remote_start(scratch: str, stages: list[str]) -> None:
    # setsid detaches the run from this SSH session; its shell is the group leader,
    # so cleanup can stop the whole process group through the recorded PID.
    starter = (
        f'cd "$HOME/{scratch}/tree" && setsid -f bash -c '
        + shlex.quote(
            "echo $$ > ../pid; "
            f"python3 Development/system/testing/ci/local_ci.py run {' '.join(stages)} "
            "--mode native --provision --results ../results.json "
            "> ../progress.log 2>&1; echo $? > ../exit-code"
        )
        + " < /dev/null > /dev/null 2>&1"
    )
    ssh(REMOTE_HOST, starter)
    print(f"Started on {REMOTE_HOST}: ~/{scratch}/progress.log", flush=True)


def remote_follow(scratch: str, keep_minutes: int) -> int:
    offset = 0
    failures = 0
    refreshed = time.monotonic()
    # New log bytes, a record separator, then the exit code, "running" or "lost".
    status_query = (
        "printf '\\036'; cat exit-code 2>/dev/null || "
        '{ kill -0 "$(cat pid 2>/dev/null)" 2>/dev/null && echo running || echo lost; }'
    )
    while True:
        try:
            query = (
                f'cd "$HOME/{scratch}" && tail -c +{offset + 1} progress.log '
                f"2>/dev/null; {status_query}"
            )
            result = ssh(REMOTE_HOST, query, timeout=60)
            failures = 0
        except (StageFailure, subprocess.TimeoutExpired) as error:
            failures += 1
            print(f"(progress query failed {failures}x: {error})", flush=True)
            if failures >= 30:
                raise StageFailure(f"lost contact with {REMOTE_HOST}") from error
            time.sleep(POLL_SECONDS)
            continue
        data, _, status = result.stdout.rpartition(b"\x1e")
        sys.stdout.buffer.write(data)
        sys.stdout.flush()
        offset += len(data)
        state = status.decode("ascii", errors="replace").strip()
        if state == "lost":
            raise StageFailure("the remote run ended without an exit code")
        if state != "running":
            return int(state)
        if time.monotonic() - refreshed > KEEP_REFRESH_SECONDS:
            annex_power("keep", str(keep_minutes))
            refreshed = time.monotonic()
        time.sleep(POLL_SECONDS)


def remote_collect(scratch: str) -> dict[str, dict]:
    archive = ssh(
        REMOTE_HOST,
        f'cd "$HOME/{scratch}/tree" && if [ -d artifacts ]; then tar -czf - artifacts; fi',
        timeout=600,
    ).stdout
    if archive:
        # Overwrite file by file, so evidence of native stages in this run stays.
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as stream:
            stream.extractall(ROOT, filter="data")
        print(f"Copied {REMOTE_HOST} artifacts into {ARTIFACTS}", flush=True)
    results = ssh(REMOTE_HOST, f'cat "$HOME/{scratch}/results.json"', check=False)
    if results.returncode:
        return {}
    return json.loads(results.stdout.decode("utf-8"))


def execute_remote(stages: list[str], run_id: str, keep_minutes: int) -> dict:
    scratch = f"{REMOTE_SCRATCH}/{run_id}"
    started = time.monotonic()
    results: dict[str, dict] = {}
    print(f"\n== {' '.join(stages)} (remote on {REMOTE_HOST}) ==", flush=True)
    try:
        annex_power("keep", str(keep_minutes))
        wait_until_reachable()
        remote_prepare(scratch)
        remote_start(scratch, stages)
        exit_code = remote_follow(scratch, keep_minutes)
        results = remote_collect(scratch)
        if exit_code and not results:
            raise StageFailure(f"remote run failed ({exit_code})")
        if "build" in stages:
            describe_firmware(include_build_directory=False)
    except (StageFailure, subprocess.SubprocessError, OSError) as error:
        print(f"remote run failed: {error}", flush=True)
        for stage in stages:
            results.setdefault(
                stage,
                {
                    "outcome": "failed",
                    "detail": str(error),
                    "seconds": round(time.monotonic() - started),
                    "where": REMOTE_HOST,
                },
            )
    finally:
        cleanup = (
            f'scratch="$HOME/{scratch}"; '
            'if [ -f "$scratch/pid" ] && [ ! -f "$scratch/exit-code" ]; then '
            'kill -TERM -- "-$(cat "$scratch/pid")" 2>/dev/null || true; fi; '
            'rm -rf "$scratch"'
        )
        try:
            ssh(REMOTE_HOST, cleanup, check=False, timeout=120)
        except subprocess.TimeoutExpired:
            print(f"Could not remove ~/{scratch} on {REMOTE_HOST}", flush=True)
        try:
            annex_power("release")
        except (StageFailure, subprocess.SubprocessError, OSError) as error:
            print(f"Release failed: {error}", flush=True)
    return results


# Detached runs


def new_run_id() -> str:
    return time.strftime("%Y%m%d-%H%M%S") + "-" + os.urandom(3).hex()


def detach(arguments: list[str], run_id: str) -> int:
    directory = RUNS / run_id
    directory.mkdir(parents=True, exist_ok=True)
    log = directory / "progress.log"
    command = [sys.executable, str(Path(__file__).resolve()), *arguments]
    command += ["--run-id", run_id]
    if os.name == "nt":
        # A windowless console of its own: children inherit it and the log handles.
        # DETACHED_PROCESS would give every console child a new, unseen console.
        windowless = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
        # Agent shells run in a job that is closed with the shell; leave that job.
        attempts = [
            {"creationflags": windowless | subprocess.CREATE_BREAKAWAY_FROM_JOB},
            {"creationflags": windowless},
        ]
    else:
        attempts = [{"start_new_session": True}]
    with log.open("wb") as stream:
        for index, options in enumerate(attempts):
            try:
                subprocess.Popen(
                    command,
                    cwd=ROOT,
                    env=child_environment(),
                    stdin=subprocess.DEVNULL,
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                    **options,
                )
                break
            except OSError:
                if index == len(attempts) - 1:
                    raise
    follower = Path(__file__).resolve().relative_to(ROOT).as_posix()
    print(f"Run {run_id} detached; progress log: {log}")
    print(f"Follow it with: python {follower} follow {run_id} --timeout 540")
    return 0


def follow(run_id: str | None, timeout: float | None, from_start: bool) -> int:
    if not run_id:
        runs = sorted(path.name for path in RUNS.glob("*") if path.is_dir())
        if not runs:
            raise SystemExit(f"no runs in {RUNS}")
        run_id = runs[-1]
    directory = RUNS / run_id
    log = directory / "progress.log"
    position_file = directory / "follow-position"
    position = 0
    if not from_start and position_file.is_file():
        position = int(position_file.read_text(encoding="utf-8") or 0)
    deadline = time.monotonic() + timeout if timeout else None
    while True:
        status = directory / "status.json"
        finished = status.is_file()
        with log.open("rb") as stream:
            stream.seek(position)
            chunk = stream.read()
        sys.stdout.buffer.write(chunk)
        sys.stdout.flush()
        position += len(chunk)
        write_text(position_file, str(position))
        if finished:
            exit_code = json.loads(status.read_text(encoding="utf-8"))["exit_code"]
            print(f"\nRun {run_id} finished with exit code {exit_code}")
            return exit_code
        if deadline and time.monotonic() > deadline:
            print(f"\nRun {run_id} is still running; follow it again to continue.")
            return STILL_RUNNING
        time.sleep(2)


def run(arguments: argparse.Namespace, raw_arguments: list[str]) -> int:
    if arguments.detach:
        forwarded = [argument for argument in raw_arguments if argument != "--detach"]
        return detach(forwarded, new_run_id())
    stages = [stage for stage in STAGES if stage in (arguments.stages or STAGES)]
    exit_code = 1
    try:
        placement = plan(stages, arguments.mode, arguments.provision)
        native = [stage for stage in stages if placement[stage] == "native"]
        remote = [stage for stage in stages if placement[stage] == "remote"]
        results = execute_native(native, arguments.provision)
        if remote:
            run_id = arguments.run_id or new_run_id()
            results.update(execute_remote(remote, run_id, arguments.keep_minutes))
        results = {stage: results[stage] for stage in stages if stage in results}
        if arguments.results:
            write_text(arguments.results, json.dumps(results, indent=2) + "\n")
        exit_code = print_summary(results)
    finally:
        if arguments.run_id:
            write_text(
                RUNS / arguments.run_id / "status.json",
                json.dumps({"exit_code": exit_code}) + "\n",
            )
    return exit_code


def main() -> int:
    configure_output()
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    commands = parser.add_subparsers(dest="command", required=True)
    run_parser = commands.add_parser("run", help="run stages (default: all)")
    run_parser.add_argument("stages", nargs="*", choices=STAGES, metavar="stage")
    run_parser.add_argument(
        "--mode",
        choices=("auto", "native", "remote"),
        default="auto",
        help="auto runs natively where the toolchain exists, else on the annex",
    )
    run_parser.add_argument(
        "--provision",
        action="store_true",
        help="install the pinned firmware toolchain here when it is missing",
    )
    run_parser.add_argument(
        "--detach",
        action="store_true",
        help="return at once; follow the progress log with the follow command",
    )
    run_parser.add_argument(
        "--keep-minutes",
        type=int,
        default=60,
        help="annex keep-awake hold, refreshed while a remote run is followed",
    )
    run_parser.add_argument("--run-id", help=argparse.SUPPRESS)
    run_parser.add_argument("--results", type=Path, help=argparse.SUPPRESS)
    follow_parser = commands.add_parser("follow", help="stream a detached run")
    follow_parser.add_argument("run_id", nargs="?", help="defaults to the newest run")
    follow_parser.add_argument(
        "--timeout",
        type=float,
        help=f"return with exit code {STILL_RUNNING} after this many seconds",
    )
    follow_parser.add_argument(
        "--from-start", action="store_true", help="replay the whole log"
    )
    raw_arguments = sys.argv[1:]
    arguments = parser.parse_args(raw_arguments)
    if arguments.command == "follow":
        return follow(arguments.run_id, arguments.timeout, arguments.from_start)
    return run(arguments, raw_arguments)


if __name__ == "__main__":
    sys.exit(main())
