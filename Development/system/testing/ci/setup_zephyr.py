#!/usr/bin/env python3
"""Provision the same local Zephyr workspace on Windows, Linux and macOS."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path

from build_support import PINS, ROOT, build_env, checked, python_path, west_command
from prepared_env import MARKER, record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=ROOT / ".ci-workspace")
    args = parser.parse_args()
    ws = args.workspace.resolve()
    if sys.version_info < (3, 12):
        parser.error("Use Python 3.12 or newer.")
    if not shutil.which("git"):
        parser.error("Install Git and put it on PATH first.")
    seven_zip = shutil.which("7z")
    if os.name == "nt" and not seven_zip:
        for folder in (
            os.environ.get("ProgramFiles"),
            os.environ.get("ProgramFiles(x86)"),
        ):
            if folder and (Path(folder) / "7-Zip/7z.exe").is_file():
                seven_zip = str(Path(folder) / "7-Zip/7z.exe")
                break
        if not seven_zip:
            parser.error(
                "Install 7-Zip first: winget install --id 7zip.7zip -e --silent"
            )
    ws.mkdir(parents=True, exist_ok=True)
    (ws / MARKER).unlink(missing_ok=True)
    if not python_path(ws).is_file():
        venv.create(ws / ".venv", with_pip=True)
    env = build_env(ws)
    if seven_zip:
        env["PATH"] += os.pathsep + str(Path(seven_zip).parent)
    py = str(python_path(ws))

    def run(argv: list[str], cwd: Path = ws) -> None:
        checked(argv, cwd=cwd, env=env)

    run(
        [
            py,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            f"west=={PINS['west_version']}",
            f"cmake=={PINS['cmake_version']}",
            f"ninja=={PINS['ninja_version']}",
        ]
    )
    west = west_command(ws)
    if not (ws / ".west/config").is_file():
        # Clone only the required commit; west init --mr cannot clone a raw SHA.
        if not (ws / "zephyr/.git").exists():
            run(["git", "init", str(ws / "zephyr")])
            run(
                [
                    "git",
                    "remote",
                    "add",
                    "origin",
                    "https://github.com/zephyrproject-rtos/zephyr",
                ],
                ws / "zephyr",
            )
        run(
            ["git", "fetch", "--depth=1", "origin", PINS["zephyr_revision"]],
            ws / "zephyr",
        )
        run(["git", "checkout", "--detach", PINS["zephyr_revision"]], ws / "zephyr")
        run([*west, "init", "-l", str(ws / "zephyr")])
    else:
        run(
            ["git", "fetch", "--depth=1", "origin", PINS["zephyr_revision"]],
            ws / "zephyr",
        )
        run(["git", "checkout", "--detach", PINS["zephyr_revision"]], ws / "zephyr")
    run([*west, "update", "--narrow", "-o=--depth=1", *PINS["modules"]])
    # Explicit module list also keeps fresh installs small and reproducible.
    # Firmware needs base build/SDK packages and esptool, rather than Zephyr's
    # optional simulation, documentation and full Twister dependency sets.
    run(
        [
            py,
            "-m",
            "pip",
            "install",
            "-r",
            str(ws / "zephyr/scripts/requirements-base.txt"),
        ]
    )
    run([py, "-m", "pip", "install", f"esptool=={PINS['esptool_version']}"])
    run([*west, "blobs", "fetch", "hal_espressif"])
    # west sdk install also completes interrupted installs in an existing SDK.
    run(
        [
            *west,
            "sdk",
            "install",
            "--version",
            PINS["sdk_version"],
            "-b",
            str(ws),
            "-t",
            PINS["toolchain"],
        ]
    )
    run([*west, "zephyr-export"])
    run([*west, "--version"])
    record("zephyr", ws)
    print(
        f"\nReady. No activation required:\n{py} {Path(__file__).with_name('benchmark_build.py')} run --runs 3",
        flush=True,
    )


if __name__ == "__main__":
    try:
        main()
    except (subprocess.CalledProcessError, RuntimeError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
