#!/usr/bin/env python3
"""Time pristine evaluation firmware builds and compare reports from other hosts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import re
import shutil
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from build_support import APP, BOARD, PINS, PROFILES, ROOT, build_env, west_command


def capture(argv: list[str], cwd: Path, env: dict[str, str]) -> str:
    argv = [shutil.which(argv[0], path=env["PATH"]) or argv[0], *argv[1:]]
    return subprocess.check_output(
        argv, cwd=cwd, env=env, text=True, stderr=subprocess.STDOUT
    ).strip()


def source_info(env: dict[str, str]) -> dict:
    names = capture(
        [
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            str(APP),
        ],
        ROOT,
        env,
    ).splitlines()
    inputs = {}
    for name in sorted(set(names)):
        rel = Path(name).relative_to(APP.relative_to(ROOT))
        if rel.parts[0] in {"src", "include", "boards"} or str(rel) in {
            "CMakeLists.txt",
            "Kconfig",
            "prj.conf",
            "qc.conf",
            "network.conf",
        }:
            # Git checkouts can use CRLF on Windows; compare logical input bytes.
            inputs[rel.as_posix()] = hashlib.sha256(
                (ROOT / name).read_bytes().replace(b"\r\n", b"\n")
            ).hexdigest()
    digest = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
    return {
        "commit": capture(["git", "rev-parse", "HEAD"], ROOT, env),
        "dirty": bool(capture(["git", "status", "--porcelain"], ROOT, env)),
        "input_sha256": digest,
        "inputs": inputs,
    }


def machine_info(label: str) -> dict:
    cpu = platform.processor()
    if os.name == "nt":
        try:
            cpu = subprocess.check_output(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-Command",
                    "(Get-CimInstance Win32_Processor).Name",
                ],
                text=True,
                timeout=15,
            ).strip()
        except (OSError, subprocess.SubprocessError):
            pass
    if sys.platform.startswith("linux"):
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                cpu = line.split(":", 1)[1].strip()
                break
    return {
        "label": label,
        "hostname": platform.node(),
        "os": platform.platform(),
        "architecture": platform.machine(),
        "cpu": cpu,
        "logical_cpus": os.cpu_count(),
    }


def tool_info(ws: Path, env: dict[str, str]) -> dict:
    west = west_command(ws)
    info = {"pins": PINS, "modules": {}}
    info["zephyr_revision"] = capture(["git", "rev-parse", "HEAD"], ws / "zephyr", env)
    if info["zephyr_revision"] != PINS["zephyr_revision"]:
        raise RuntimeError(
            "Zephyr revision differs from toolchain.json; rerun setup_zephyr.py."
        )
    projects = {}
    for line in capture(
        [*west, "list", "-f", "{name}|{path}|{revision}"], ws, env
    ).splitlines():
        name, path, revision = line.split("|", 2)
        projects[name] = {"path": path, "revision": revision}
    for name in PINS["modules"]:
        project = projects[name]
        folder = ws / project["path"]
        revision = capture(["git", "rev-parse", "HEAD"], folder, env)
        if revision != project["revision"]:
            raise RuntimeError(
                f"{name} revision differs from the pinned manifest; rerun setup."
            )
        if capture(
            ["git", "status", "--porcelain", "--untracked-files=no"], folder, env
        ):
            raise RuntimeError(f"Tracked files in {name} have local changes.")
        info["modules"][name] = {"revision": revision, "path": folder.as_posix()}
    if capture(
        ["git", "status", "--porcelain", "--untracked-files=no"], ws / "zephyr", env
    ):
        raise RuntimeError("Tracked Zephyr files have local changes.")
    sdk = ws / f"zephyr-sdk-{PINS['sdk_version']}"
    if (sdk / "sdk_version").read_text().strip() != PINS["sdk_version"]:
        raise RuntimeError("SDK version differs from toolchain.json.")
    compiler = (
        sdk
        / "gnu"
        / PINS["toolchain"]
        / "bin"
        / (PINS["toolchain"] + "-gcc" + (".exe" if os.name == "nt" else ""))
    )
    for name, command in {
        "west": [*west, "--version"],
        "cmake": ["cmake", "--version"],
        "ninja": ["ninja", "--version"],
        "compiler": [str(compiler), "--version"],
        "python": [west[0], "--version"],
        "esptool": [west[0], "-m", "esptool", "version"],
    }.items():
        info[name] = capture(command, ws, env).splitlines()[0]
    for name in ("west", "cmake", "ninja", "esptool"):
        if PINS[f"{name}_version"] not in info[name]:
            raise RuntimeError(
                f"{name} version differs from toolchain.json; rerun setup."
            )
    return info


def timed(
    argv: list[str], ws: Path, env: dict[str, str], log: Path
) -> tuple[float, int]:
    argv = [shutil.which(argv[0], path=env["PATH"]) or argv[0], *argv[1:]]
    print("+", subprocess.list2cmdline(argv), flush=True)
    start = time.perf_counter()
    with log.open("w", encoding="utf-8") as stream:
        stream.write("+ " + subprocess.list2cmdline(argv) + "\n")
        stream.flush()
        process = subprocess.run(
            argv, cwd=ws, env=env, stdout=stream, stderr=subprocess.STDOUT
        )
    elapsed = time.perf_counter() - start
    print(f"  {elapsed:.2f}s; exit {process.returncode}; {log}", flush=True)
    return elapsed, process.returncode


def save(report: dict, out: Path) -> None:
    (out / "results.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    with (out / "results.csv").open("w", newline="", encoding="utf-8") as stream:
        fields = [
            "profile",
            "jobs",
            "run",
            "warmup",
            "mode",
            "configure_seconds",
            "compile_seconds",
            "total_seconds",
            "exit_code",
        ]
        writer = csv.DictWriter(stream, fieldnames=["device", *fields])
        writer.writeheader()
        for row in report["measurements"]:
            writer.writerow(
                {
                    "device": report["machine"]["label"],
                    **{key: row.get(key) for key in fields},
                }
            )


def run_benchmark(args: argparse.Namespace) -> None:
    ws = args.workspace.resolve()
    env = build_env(ws)
    # Never use another host's exported package, compiler launcher or module set.
    env["CCACHE_DISABLE"] = "1"
    for key in ("CC", "CXX", "CFLAGS", "CXXFLAGS", "LDFLAGS", "CMAKE_GENERATOR"):
        env.pop(key, None)
    toolchain = tool_info(ws, env)
    source = source_info(env)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    label = re.sub(r"[^A-Za-z0-9_.-]", "-", args.device)
    out = ROOT / "artifacts/build-times" / f"{label}-{stamp}"
    out.mkdir(parents=True)
    report = {
        "schema_version": 1,
        "started_utc": stamp,
        "board": BOARD,
        "machine": machine_info(args.device),
        "source": source,
        "toolchain": toolchain,
        "policy": "pristine configure + compile; compiler cache disabled; OS filesystem cache retained",
        "workspace": str(ws),
        "measurements": [],
        "status": "running",
    }
    save(report, out)
    west = west_command(ws)
    cmake_args = [
        "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
        "-DCMAKE_C_COMPILER_LAUNCHER=",
        "-DCMAKE_CXX_COMPILER_LAUNCHER=",
        "-DUSE_CCACHE=0",
        "-DZEPHYR_MODULES="
        + ";".join(item["path"] for item in toolchain["modules"].values()),
    ]
    for profile in args.profiles:
        for jobs in args.jobs:
            # Reuse only this invocation's isolated directory; west prunes it.
            build = ROOT / "build-benchmark" / out.name / f"{profile}-j{jobs}"
            for iteration in range(args.warmups + args.runs):
                warmup = iteration < args.warmups
                number = iteration + 1 if warmup else iteration + 1 - args.warmups
                prefix = f"{profile}-j{jobs}-{'warmup' if warmup else 'run'}{number}"
                row = {
                    "profile": profile,
                    "jobs": jobs,
                    "run": number,
                    "warmup": warmup,
                    "mode": "clean",
                }
                configure = [
                    *west,
                    "build",
                    "--pristine=always",
                    "--cmake-only",
                    "-b",
                    BOARD,
                    str(APP),
                    "-d",
                    str(build),
                    "--",
                    "-GNinja",
                    *cmake_args,
                    *PROFILES[profile],
                ]
                row["configure_seconds"], code = timed(
                    configure, ws, env, out / f"{prefix}-configure.log"
                )
                row["compile_seconds"] = 0.0
                if code == 0:
                    row["compile_seconds"], code = timed(
                        ["cmake", "--build", str(build), "--parallel", str(jobs)],
                        ws,
                        env,
                        out / f"{prefix}-compile.log",
                    )
                row["total_seconds"] = row["configure_seconds"] + row["compile_seconds"]
                row["exit_code"] = code
                row["build_directory"] = str(build)
                if code == 0:
                    binary = build / "zephyr/zephyr.bin"
                    if not binary.is_file():
                        row["exit_code"] = code = 1
                        row["error"] = (
                            "Build returned success but zephyr.bin is missing"
                        )
                    else:
                        row["firmware_sha256"] = hashlib.sha256(
                            binary.read_bytes()
                        ).hexdigest()
                        row["firmware_bytes"] = binary.stat().st_size
                        shutil.copy2(binary, out / f"{prefix}-zephyr.bin")
                report["measurements"].append(row)
                save(report, out)
                if code:
                    report["status"] = "failed"
                    save(report, out)
                    raise RuntimeError(
                        f"Build failed; results and logs retained at {out}"
                    )
                if args.include_noop:
                    seconds, code = timed(
                        ["cmake", "--build", str(build), "--parallel", str(jobs)],
                        ws,
                        env,
                        out / f"{prefix}-noop.log",
                    )
                    report["measurements"].append(
                        {
                            **row,
                            "mode": "noop",
                            "configure_seconds": 0.0,
                            "compile_seconds": seconds,
                            "total_seconds": seconds,
                            "exit_code": code,
                        }
                    )
                    save(report, out)
                    if code:
                        report["status"] = "failed"
                        save(report, out)
                        raise RuntimeError(f"No-op build failed; see {out}")
    if source_info(env)["input_sha256"] != source["input_sha256"]:
        report["error"] = (
            "Firmware source changed during measurement; discard this report"
        )
        save(report, out)
        raise RuntimeError(report["error"])
    report["status"] = "complete"
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    save(report, out)
    print(f"\nResults: {out / 'results.json'}", flush=True)
    compare([out / "results.json"])


def compare(paths: list[Path]) -> None:
    groups = {}
    signatures = set()
    python_versions = set()
    for path in paths:
        report = json.loads(path.read_text(encoding="utf-8"))
        if report.get("schema_version") != 1 or report.get("error"):
            raise RuntimeError(f"Invalid or incomplete report: {path}")
        if report.get("status", "complete") != "complete":
            print(
                f"Report {path} is {report['status']}; only finished successful samples are shown."
            )
        tc = report["toolchain"]
        python_versions.add(tc["python"])
        signature = json.dumps(
            {
                "source": report["source"]["input_sha256"],
                "pins": tc["pins"],
                "compiler": tc["compiler"].replace("gcc.exe ", "gcc "),
                "versions": {
                    name: tc.get(name) for name in ("west", "cmake", "ninja", "esptool")
                },
                "policy": report["policy"],
                "board": report["board"],
            },
            sort_keys=True,
        )
        signatures.add(signature)
        for row in report["measurements"]:
            if row["warmup"] or row["exit_code"]:
                continue
            key = (
                signature,
                report["machine"]["label"],
                row["profile"],
                row["jobs"],
                row["mode"],
            )
            groups.setdefault(key, []).append(row["total_seconds"])
    if len(signatures) > 1:
        print(
            "Different source/toolchain/policy inputs detected; compare only within each input group."
        )
    if len(python_versions) > 1:
        print("Python versions differ: " + ", ".join(sorted(python_versions)))
    print(
        "| Inputs | Device | Profile | Jobs | Mode | Runs | Median s | Min s | Max s |"
    )
    print("|---|---|---|---:|---|---:|---:|---:|---:|")
    for (signature, device, profile, jobs, mode), values in sorted(groups.items()):
        fingerprint = hashlib.sha256(signature.encode()).hexdigest()[:8]
        print(
            f"| {fingerprint} | {device} | {profile} | {jobs} | {mode} | {len(values)} | {statistics.median(values):.2f} | {min(values):.2f} | {max(values):.2f} |"
        )


def positive(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser(
        "run", help="Build locally and record timings; never publish or flash"
    )
    run.add_argument("--workspace", type=Path, default=ROOT / ".ci-workspace")
    run.add_argument("--device", default=platform.node())
    run.add_argument(
        "--profiles", nargs="+", choices=list(PROFILES), default=["offline"]
    )
    run.add_argument("--jobs", nargs="+", type=positive, default=[os.cpu_count() or 1])
    run.add_argument("--runs", type=positive, default=3)
    run.add_argument("--warmups", type=int, default=1)
    run.add_argument("--include-noop", action="store_true")
    comparison = commands.add_parser(
        "compare", help="Print median/min/max for reports copied from each device"
    )
    comparison.add_argument("reports", nargs="+", type=Path)
    args = parser.parse_args()
    if args.command == "run":
        if args.warmups < 0:
            parser.error("--warmups must be nonnegative")
        run_benchmark(args)
    else:
        compare(args.reports)


if __name__ == "__main__":
    try:
        main()
    except (OSError, subprocess.CalledProcessError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from exc
