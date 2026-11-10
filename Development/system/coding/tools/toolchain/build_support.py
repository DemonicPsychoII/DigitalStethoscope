"""Shared pinned tools and firmware profiles for setup and CI."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
APP = ROOT / "Development/system/coding/app"
PINS = json.loads(Path(__file__).with_name("toolchain.json").read_text())
BOARD = PINS["board"]
# Prepared-environment marker; setup removes it before changing a workspace, so a
# half-finished setup never keeps the fingerprint of the previous complete one.
PREPARED_MARKER = ".stethoscope-prepared.json"
# Written by setup_zephyr.py after a complete setup; holds the pins it installed.
PIN_STAMP = ".stethoscope-toolchain-pins.json"
WORKSPACE_VARIABLE = "STETHOSCOPE_TOOLCHAIN_WORKSPACE"
PROFILES = {"application": []}

RELEASE_COMPONENTS = dict.fromkeys(PROFILES, "application")


def user_cache_directory() -> Path:
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    return Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))


def pin_key() -> str:
    canonical = json.dumps(PINS, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def shared_workspace() -> Path:
    """One workspace per toolchain pin, shared by every checkout and worktree."""
    return user_cache_directory() / "stethoscope-toolchain" / f"zephyr-{pin_key()}"


def main_checkout() -> Path | None:
    try:
        common = subprocess.check_output(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    common_path = Path(common)
    return common_path.parent if common_path.name == ".git" else None


def workspace_matches_pins(workspace: Path) -> bool:
    for marker in (PIN_STAMP, PREPARED_MARKER):
        try:
            recorded = json.loads((workspace / marker).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if recorded.get("pins") == PINS:
            return True
    return False


def toolchain_workspace() -> Path:
    """Resolve the pinned workspace for this checkout without provisioning it.

    An explicit override wins. A checkout's own `.ci-workspace` (CI links the prepared
    image there) keeps its previous meaning. Otherwise any workspace already recorded
    with the current pins is reused; the shared per-pin location is the setup target.
    """
    override = os.environ.get(WORKSPACE_VARIABLE)
    if override:
        return Path(override)
    local = ROOT / ".ci-workspace"
    if local.exists():
        return local
    candidates = [shared_workspace()]
    main = main_checkout()
    if main and main != ROOT:
        candidates.append(main / ".ci-workspace")
    if sys.platform != "win32":
        candidates.append(Path("/opt/zephyr-workspace"))
    for candidate in candidates:
        if workspace_matches_pins(candidate):
            return candidate
    return shared_workspace()


def bin_dir(workspace: Path) -> Path:
    return workspace.resolve() / ".venv" / ("Scripts" if os.name == "nt" else "bin")


def python_path(workspace: Path) -> Path:
    return bin_dir(workspace) / ("python.exe" if os.name == "nt" else "python")


def build_env(workspace: Path) -> dict[str, str]:
    # Zephyr computes linker include paths lexically; a workspace symlink breaks them.
    workspace = workspace.resolve()
    env = os.environ.copy()
    env["PATH"] = os.pathsep.join((str(bin_dir(workspace)), env.get("PATH", "")))
    env["ZEPHYR_BASE"] = str(workspace / "zephyr")
    env["ZEPHYR_SDK_INSTALL_DIR"] = str(workspace / f"zephyr-sdk-{PINS['sdk_version']}")
    env["ZEPHYR_TOOLCHAIN_VARIANT"] = "zephyr"
    return env


def west_command(workspace: Path) -> list[str]:
    python = python_path(workspace)
    if not python.is_file():
        raise RuntimeError(
            f"Toolchain environment missing: {python}. Run setup_zephyr.py first."
        )
    return [str(python), "-m", "west"]


def checked(argv: list[str], *, cwd: Path, env: dict[str, str]) -> None:
    print("+", subprocess.list2cmdline(argv), flush=True)
    subprocess.run(argv, cwd=cwd, env=env, check=True)
