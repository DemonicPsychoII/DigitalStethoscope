"""Shared pinned tools and firmware profiles for setup, CI and timing runs."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
APP = ROOT / "Development/system/coding/bringup-zephyr"
PINS = json.loads(Path(__file__).with_name("toolchain.json").read_text())
BOARD = PINS["board"]
PROFILES = {
    "offline": [],
    "qc": ["-DEXTRA_CONF_FILE=qc.conf"],
    "network-qc-switch": [
        "-DEXTRA_CONF_FILE=network.conf;qc.conf",
        "-DEXTRA_DTC_OVERLAY_FILE=boards/second-switch.overlay",
    ],
}


def bin_dir(workspace: Path) -> Path:
    return workspace / ".venv" / ("Scripts" if os.name == "nt" else "bin")


def python_path(workspace: Path) -> Path:
    return bin_dir(workspace) / ("python.exe" if os.name == "nt" else "python")


def build_env(workspace: Path) -> dict[str, str]:
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
