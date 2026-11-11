"""Shared pinned tools and firmware profiles for setup and CI."""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import subprocess
import sys
import time
from collections.abc import Iterator
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
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]


def shared_workspace() -> Path:
    """One workspace per toolchain pin, shared by every checkout and worktree.

    It stays inside the user's own profile, so other local accounts cannot plant tools
    in it. On Windows it sits directly in the profile: the SDK's deepest file is 179
    characters below its directory, which under %LOCALAPPDATA% reaches the
    260-character path limit.
    """
    if os.name == "nt":
        return Path.home() / ".stethoscope-toolchain" / pin_key()
    return user_cache_directory() / "stethoscope-toolchain" / pin_key()


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
        if isinstance(recorded, dict) and recorded.get("pins") == PINS:
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


def sdk_directory(workspace: Path) -> Path:
    """The SDK this workspace builds with.

    `west sdk install` reuses an SDK of the pinned version that the CMake package
    registry already knows, even outside the workspace; setup records where it is.
    """
    local = workspace / f"zephyr-sdk-{PINS['sdk_version']}"
    if (local / "sdk_version").is_file():
        return local
    try:
        recorded = json.loads((workspace / PIN_STAMP).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return local
    sdk = recorded.get("sdk") if isinstance(recorded, dict) else None
    if isinstance(sdk, str) and (Path(sdk) / "sdk_version").is_file():
        return Path(sdk)
    return local


def toolchain_problems(workspace: Path) -> list[str]:
    """What keeps a workspace from building with the current pins; empty when ready."""
    tool_directory = bin_dir(workspace)
    suffix = ".exe" if os.name == "nt" else ""
    compiler = (
        sdk_directory(workspace)
        / "gnu"
        / PINS["toolchain"]
        / "bin"
        / f"{PINS['toolchain']}-gcc{suffix}"
    )
    required = {
        "west": tool_directory / f"west{suffix}",
        "cmake": tool_directory / f"cmake{suffix}",
        "ninja": tool_directory / f"ninja{suffix}",
        "Zephyr": workspace / "zephyr" / "CMakeLists.txt",
        "SDK compiler": compiler,
    }
    problems = [
        f"{name} missing" for name, path in required.items() if not path.is_file()
    ]
    if not workspace_matches_pins(workspace):
        problems.append("no record of the current toolchain.json pins")
    return problems


@contextlib.contextmanager
def exclusive_lock(path: Path) -> Iterator[None]:
    """Serialize setup of a shared environment across processes and checkouts."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        announced = False
        while True:
            try:
                if os.name == "nt":
                    import msvcrt

                    stream.seek(0)
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if not announced:
                    print(f"Waiting for {path}, held by another setup", flush=True)
                    announced = True
                time.sleep(1)
        try:
            yield
        finally:
            if os.name == "nt":
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


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
    env["ZEPHYR_SDK_INSTALL_DIR"] = str(sdk_directory(workspace))
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
