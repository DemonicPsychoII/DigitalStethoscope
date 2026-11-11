#!/usr/bin/env python3
"""Provision the same local Zephyr workspace on Windows, Linux and macOS."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import venv
from pathlib import Path

from build_support import (
    BOARD,
    PIN_STAMP,
    PINS,
    PREPARED_MARKER,
    ROOT,
    bin_dir,
    build_env,
    checked,
    exclusive_lock,
    python_path,
    sdk_directory,
    toolchain_problems,
    toolchain_workspace,
    west_command,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace",
        type=Path,
        default=toolchain_workspace(),
        help="defaults to the workspace shared by all checkouts for these pins",
    )
    parser.add_argument(
        "--if-needed",
        action="store_true",
        help="return at once when the workspace already matches the pins",
    )
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
    # Checkouts share this workspace; one setup at a time, and readiness is judged
    # only after the lock, when no other setup can be halfway through.
    with exclusive_lock(ws / ".stethoscope-setup.lock"):
        if args.if_needed and not toolchain_problems(ws):
            print(f"Toolchain workspace already provisioned: {ws}", flush=True)
            return
        provision(ws, seven_zip)


def provision(ws: Path, seven_zip: str | None) -> None:
    (ws / PREPARED_MARKER).unlink(missing_ok=True)
    (ws / PIN_STAMP).unlink(missing_ok=True)
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
    # Only the pinned modules are cloned; marking the rest inactive keeps Zephyr's
    # build meta file, which west spdx needs, from reading projects that do not exist.
    project_filter = ",".join(["-.*", *(f"+{name}" for name in PINS["modules"])])
    run([*west, "config", "manifest.project-filter", "--", project_filter])
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
    sdk = sdk_directory(ws)
    if not (sdk / "sdk_version").is_file():
        # west reused an SDK of this version from elsewhere; record its location.
        listing = subprocess.run(
            [*west, "sdk", "list"],
            cwd=ws,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        version = re.escape(PINS["sdk_version"])
        found = re.search(rf"^{version}:\s*\n\s+path:\s*(.+?)\s*$", listing, re.M)
        if not found:
            raise RuntimeError(f"west sdk list shows no SDK {PINS['sdk_version']}")
        sdk = Path(found.group(1))
    print(f"Zephyr SDK: {sdk}", flush=True)
    (ws / PIN_STAMP).write_text(
        json.dumps({"pins": PINS, "sdk": str(sdk)}, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Toolchain workspace: {ws}", flush=True)
    if os.name == "nt":
        build_firmware = Path(__file__).resolve().parents[1] / "build-firmware.ps1"
        next_step = f"powershell -File {build_firmware}"
    else:
        # Same environment as build_env(): west finds its Zephyr build command only inside
        # the workspace with ZEPHYR_BASE set, and the build uses the pinned CMake, Ninja
        # and SDK.
        tool_env = build_env(ws)
        assignments = " ".join(
            f"{name}={shlex.quote(tool_env[name])}"
            for name in (
                "ZEPHYR_BASE",
                "ZEPHYR_SDK_INSTALL_DIR",
                "ZEPHYR_TOOLCHAIN_VARIANT",
            )
        )
        build_command = shlex.join(
            [
                *west,
                "build",
                "-b",
                BOARD,
                "-d",
                str(ROOT / "build-app"),
                str(ROOT / "Development/system/coding/app"),
            ]
        )
        next_step = (
            f"cd {shlex.quote(str(ws))} && "
            f'PATH={shlex.quote(str(bin_dir(ws)))}:"$PATH" '
            f"{assignments} {build_command}"
        )
    print(f"\nReady. No activation required:\n{next_step}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (subprocess.CalledProcessError, RuntimeError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
