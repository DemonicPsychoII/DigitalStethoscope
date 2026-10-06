"""Validate disposable image environments against the checked-out inputs.

Preparation records versions and file hashes only after setup succeeds. A changed
pin or an incomplete environment falls back to ordinary provisioning.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from build_support import PINS, ROOT, python_path

STATIC_PYTHON = "3.12.10"
STATIC_REQUIREMENTS = (
    "Development/system/testing/ci/requirements-ci.txt",
    "Development/system/coding/bringup-zephyr/tools/requirements.txt",
)
MARKER = ".stethoscope-prepared.json"


def python_state(python: Path) -> dict:
    script = (
        "import importlib.metadata as m,json,platform;"
        "print(json.dumps({'python':platform.python_version(),"
        "'packages':{d.metadata['Name'].lower().replace('_','-'):d.version "
        "for d in m.distributions()}}))"
    )
    return json.loads(subprocess.check_output([str(python), "-c", script], text=True))


def git_head(path: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD"], text=True
    ).strip()


def state(kind: str, workspace: Path) -> dict:
    result = {"schema": 1, "kind": kind, **python_state(python_path(workspace))}
    if kind == "static":
        if result["python"] != STATIC_PYTHON:
            raise ValueError("prepared Python does not match the static pin")
        result["requirements"] = {
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in STATIC_REQUIREMENTS
        }
    elif kind == "zephyr":
        result["pins"] = PINS
        if git_head(workspace / "zephyr") != PINS["zephyr_revision"]:
            raise ValueError("Zephyr revision does not match")
        listing = subprocess.check_output(
            [str(python_path(workspace)), "-m", "west", "list", "-f", "{name}|{path}"],
            cwd=workspace,
            text=True,
        )
        projects = dict(line.split("|", 1) for line in listing.splitlines())
        result["modules"] = {
            name: git_head(workspace / projects[name]) for name in PINS["modules"]
        }
        sdk = workspace / f"zephyr-sdk-{PINS['sdk_version']}"
        suffix = ".exe" if sys.platform == "win32" else ""
        compiler = sdk / PINS["toolchain"] / "bin" / f"{PINS['toolchain']}-gcc{suffix}"
        if not compiler.is_file():
            raise ValueError("SDK compiler is missing")
        result["compiler"] = hashlib.sha256(compiler.read_bytes()).hexdigest()
        blobs = workspace / projects["hal_espressif"] / "zephyr/blobs"
        result["blobs"] = {
            str(path.relative_to(blobs)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(blobs.rglob("*"))
            if path.is_file()
        }
        if not result["blobs"]:
            raise ValueError("Espressif blobs are missing")
        for package, pin in (
            ("west", "west_version"),
            ("cmake", "cmake_version"),
            ("ninja", "ninja_version"),
            ("esptool", "esptool_version"),
        ):
            if result["packages"].get(package) != PINS[pin]:
                raise ValueError(f"{package} pin does not match")
    else:
        raise ValueError("unknown environment kind")
    return result


def record(kind: str, workspace: Path) -> None:
    data = state(kind, workspace)
    (workspace / MARKER).write_text(json.dumps(data, sort_keys=True) + "\n")


def ready(kind: str, workspace: Path) -> bool:
    try:
        return json.loads((workspace / MARKER).read_text()) == state(kind, workspace)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        return False


if __name__ == "__main__":
    command, kind, location = sys.argv[1:]
    workspace = Path(location)
    if command == "record":
        record(kind, workspace)
    elif command == "check":
        raise SystemExit(0 if ready(kind, workspace) else 1)
    else:
        raise SystemExit("expected record or check")
