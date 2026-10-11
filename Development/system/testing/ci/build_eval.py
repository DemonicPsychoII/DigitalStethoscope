#!/usr/bin/env python3
"""Local evaluation firmware builds with timing, logs and memory evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
APP = ROOT / "Development/system/coding/bringup-zephyr"
BOARD = "esp32s3_devkitc/esp32s3/procpu"
PROFILES = {
    "offline": [],
    "qc": ["-DEXTRA_CONF_FILE=qc.conf"],
    "network-qc-switch": [
        "-DEXTRA_CONF_FILE=network.conf;qc.conf",
        "-DEXTRA_DTC_OVERLAY_FILE=boards/second-switch.overlay",
    ],
}


def capture(argv: list[str], env: dict[str, str]) -> str:
    return subprocess.check_output(argv, cwd=ROOT, env=env, text=True).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=[*PROFILES, "all"], default="qc")
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Reuse the profile build directory; includes no-op builds",
    )
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--jobs", type=int, default=os.cpu_count() or 1)
    args = parser.parse_args()
    if args.repeat < 1 or args.jobs < 1:
        parser.error("--repeat and --jobs must be positive")
    config_path = ROOT / ".ci-workspace/eval-environment.json"
    if not config_path.is_file():
        parser.error("Run Development/Toolchain/setup-eval.ps1 first")
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    env = os.environ.copy()
    env.update(
        ZEPHYR_BASE=config["zephyr"],
        ZEPHYR_SDK_INSTALL_DIR=config["sdk"],
        ZEPHYR_TOOLCHAIN_VARIANT="zephyr",
    )
    env["PATH"] = str(Path(config["python"]).parent) + os.pathsep + env.get("PATH", "")
    west = [config["python"], "-m", "west"]
    zephyr_revision = capture(["git", "-C", config["zephyr"], "rev-parse", "HEAD"], env)
    hal_revision = capture(
        [
            "git",
            "-C",
            str(Path(config["workspace"]) / "modules/hal/espressif"),
            "rev-parse",
            "HEAD",
        ],
        env,
    )
    if (
        zephyr_revision != "357467a011cd2557a1a3f0b4be83d817c4addc9b"
        or hal_revision != "3d4d922a4d2994f844790ec031a584ec71240485"
    ):
        parser.error("Toolchain source revisions differ from the project pins")
    if capture([*west, "--version"], env) != "West version: v1.5.0":
        parser.error("west 1.5.0 required")
    source_hashes = {
        str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(
            p.read_bytes()
        ).hexdigest()
        for p in sorted(APP.rglob("*"))
        if p.is_file()
        and (
            p.suffix in {".c", ".h", ".conf", ".overlay", ".txt"} or p.name == "Kconfig"
        )
        and not any(part.startswith("build") for part in p.relative_to(APP).parts)
    }
    profiles = list(PROFILES) if args.profile == "all" else [args.profile]
    if args.incremental:
        for profile in profiles:
            if not (ROOT / f"build-eval-{profile}/CMakeCache.txt").is_file():
                parser.error(f"Build {profile} without --incremental first")
    for profile in profiles:
        for iteration in range(1, args.repeat + 1):
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
            evidence = ROOT / "artifacts/evaluation" / profile / stamp
            evidence.mkdir(parents=True)
            out = ROOT / f"build-eval-{profile}"
            command = [
                *west,
                "build",
                "--pristine=never" if args.incremental else "--pristine=always",
                "-b",
                BOARD,
                str(APP),
                "-d",
                str(out),
                f"-o=-j{args.jobs}",
                "-o=-d",
                "-o=stats",
            ]
            if not args.incremental:
                command.extend(
                    ["--", "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON", *PROFILES[profile]]
                )
            result = {
                "schema_version": 1,
                "started_utc": stamp,
                "profile": profile,
                "mode": "incremental" if args.incremental else "pristine",
                "iteration": iteration,
                "jobs": args.jobs,
                "board": BOARD,
                "host": platform.platform(),
                "cpu_count": os.cpu_count(),
                "commit": capture(["git", "rev-parse", "HEAD"], env),
                "dirty": bool(capture(["git", "status", "--porcelain"], env)),
                "source_sha256": source_hashes,
                "zephyr_revision": zephyr_revision,
                "hal_espressif_revision": hal_revision,
                "sdk_version": (Path(config["sdk"]) / "sdk_version")
                .read_text()
                .strip(),
                "versions": {
                    name: capture(argv, env)
                    for name, argv in {
                        "python": [config["python"], "--version"],
                        "west": [*west, "--version"],
                        "cmake": ["cmake", "--version"],
                        "ninja": ["ninja", "--version"],
                    }.items()
                },
                "command": command,
                "build_directory": str(out),
                "stages": [],
                "status": "running",
            }

            def run_stage(name: str, argv: list[str]) -> int:
                print(f"{profile}: {name} ({evidence})", flush=True)
                started = time.perf_counter()
                with (evidence / f"{name}.log").open("w", encoding="utf-8") as log:
                    process = subprocess.run(
                        argv, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT
                    )
                duration = time.perf_counter() - started
                result["stages"].append(
                    {
                        "name": name,
                        "seconds": duration,
                        "returncode": process.returncode,
                    }
                )
                if process.returncode:
                    result["status"] = "failed"
                (evidence / "results.json").write_text(
                    json.dumps(result, indent=2) + "\n", encoding="utf-8"
                )
                print(f"{name}: {duration:.2f}s, exit {process.returncode}", flush=True)
                if process.returncode:
                    print(
                        (evidence / f"{name}.log").read_text(
                            encoding="utf-8", errors="replace"
                        )[-8000:]
                    )
                return process.returncode

            if code := run_stage("build", command):
                return code
            compiler = next(
                line.split("=", 1)[1]
                for line in (out / "CMakeCache.txt")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.startswith("CMAKE_C_COMPILER:")
            )
            result["versions"]["compiler"] = capture([compiler, "--version"], env)
            for target in ("ram_report", "rom_report"):
                if code := run_stage(
                    target, [*west, "build", "-d", str(out), "-t", target]
                ):
                    return code
            for relative in (
                "zephyr/.config",
                "zephyr/zephyr.bin",
                "zephyr/zephyr.elf",
                "zephyr/zephyr.map",
                "zephyr/zephyr.dts",
                "compile_commands.json",
                ".ninja_log",
            ):
                source = out / relative
                if not source.is_file():
                    raise SystemExit(f"Required build evidence missing: {source}")
                shutil.copy2(source, evidence / source.name)
            result["firmware_sha256"] = hashlib.sha256(
                (out / "zephyr/zephyr.bin").read_bytes()
            ).hexdigest()
            with (evidence / "python-packages.txt").open(
                "w", encoding="utf-8"
            ) as packages:
                subprocess.run(
                    [config["python"], "-m", "pip", "freeze"],
                    env=env,
                    check=True,
                    stdout=packages,
                )
            result["status"] = "complete"
            (evidence / "results.json").write_text(
                json.dumps(result, indent=2) + "\n", encoding="utf-8"
            )
            print(f"Firmware: {out / 'zephyr/zephyr.bin'}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
