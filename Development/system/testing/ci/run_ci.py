#!/usr/bin/env python3
"""Shared fail-fast entry point for local and GitHub CI quality gates."""

from __future__ import annotations

import json
import os
import py_compile
import shutil
import subprocess
import sys
from pathlib import Path

import firmware_release
import yaml
from build_support import BOARD, build_env
from build_support import PROFILES as PROFILE_ARGS

ROOT = Path(__file__).resolve().parents[4]
APP = ROOT / "Development/system/coding/bringup-zephyr"
ARTIFACTS = ROOT / "artifacts"
# (profile, build directory); each profile's CMake options live in build_support.
PROFILES = tuple(
    (profile, "build-ci" if profile == "offline" else f"build-ci-{profile}")
    for profile in PROFILE_ARGS
)


def summary(line: str) -> None:
    target = os.environ.get("GITHUB_STEP_SUMMARY")
    if target:
        with Path(target).open("a", encoding="utf-8") as stream:
            stream.write(line + "\n")


def run(
    argv: list[str],
    *,
    cwd: Path = ROOT,
    log: Path | None = None,
    env_overrides: dict[str, str] | None = None,
) -> None:
    print("+", subprocess.list2cmdline(argv), flush=True)
    env = os.environ.copy()
    pinned_zephyr = ROOT / ".ci-workspace/zephyr"
    if pinned_zephyr.is_dir():
        # CI commands run from the application repository, outside the nested
        # West workspace. Point West at the pinned Zephyr checkout explicitly.
        env = build_env(ROOT / ".ci-workspace")
    if env_overrides:
        env.update(env_overrides)
    if log:
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("w", encoding="utf-8") as stream:
            result = subprocess.run(
                argv,
                cwd=cwd,
                env=env,
                text=True,
                stdout=stream,
                stderr=subprocess.STDOUT,
            )
        print(log.read_text(encoding="utf-8", errors="replace"))
    else:
        result = subprocess.run(argv, cwd=cwd, env=env)
    if result.returncode:
        raise SystemExit(
            f"stage command failed ({result.returncode}): {subprocess.list2cmdline(argv)}"
        )


def west() -> str:
    workspace_candidates = (
        ROOT / ".ci-workspace/.venv/bin/west",
        ROOT / ".ci-workspace/.venv/Scripts/west.exe",
    )
    for candidate in workspace_candidates:
        if candidate.is_file():
            return str(candidate)
    found = shutil.which("west")
    if found:
        return found
    raise SystemExit(
        "west was not found on PATH or in the pinned .ci-workspace virtual environment"
    )


def static() -> None:
    run(["git", "diff", "--check", "HEAD"])
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).split(b"\0")
    forbidden = ("/build/", "/zephyr/", "/.west/", "twister-out")
    for raw in filter(None, tracked):
        rel = raw.decode("utf-8")
        normalized = "/" + rel.replace("\\", "/")
        if any(token in normalized for token in forbidden) or normalized.endswith(
            (".elf", ".bin", ".map")
        ):
            raise SystemExit(f"generated/build output is tracked: {rel}")
        path = ROOT / rel
        if not path.is_file():
            continue
        if path.stat().st_size > 5 * 1024 * 1024:
            raise SystemExit(f"unexpected tracked file over 5 MiB: {rel}")
        if path.suffix == ".py":
            py_compile.compile(str(path), doraise=True)
        if path.suffix == ".json":
            json.loads(path.read_text(encoding="utf-8"))
        if path.suffix in {".yaml", ".yml"}:
            yaml.safe_load(path.read_text(encoding="utf-8"))
    # Format all maintained application sources.
    run([sys.executable, "-m", "ruff", "check", "Development/system/testing/ci"])
    run(
        [
            sys.executable,
            "-m",
            "ruff",
            "format",
            "--check",
            "Development/system/testing/ci",
        ]
    )
    clang_format = shutil.which("clang-format")
    if clang_format:
        maintained_sources = sorted(
            str(path)
            for area in (APP / "include", APP / "src")
            for path in area.rglob("*")
            if path.is_file() and path.suffix in {".c", ".h"}
        )
        if not maintained_sources:
            raise SystemExit("no maintained C sources were discovered for formatting")
        run([clang_format, "--dry-run", "--Werror", *maintained_sources])
    elif os.environ.get("CI"):
        raise SystemExit("clang-format is required in CI")
    summary("### Static checks: PASS")


def publish_local_firmware(
    build: firmware_release.Identity, manifest: dict, release: Path
) -> None:
    """Publish only after all local build profiles succeed; hosted CI stays credential-free.

    Like the homelab's GitHub builds, the new build is uploaded completely before the
    previous one is retired, so the `local` channel always holds one complete build.
    """
    publisher = shutil.which("cloud-publish")
    if os.environ.get("GITHUB_ACTIONS") == "true" or not publisher:
        return
    stamp = build.built_at.replace("-", "").replace(":", "")
    build_id = f"local-{stamp}-{build.commit[:12]}"
    try:
        for entry in manifest["files"]:
            argv = [
                publisher,
                *("--project", firmware_release.PROJECT, "--version", entry["version"]),
                *("--commit", build.commit, "--board", BOARD),
                *("--source", "local", "--trigger", "local"),
                *("--profile", entry["profile"], "--build", build_id),
                *("--parts", str(len(manifest["files"])), "--built-at", build.built_at),
            ]
            if build.dirty:
                argv.append("--dirty")
            if build.branch:
                argv += ["--branch", build.branch]
            run([*argv, str(release / entry["name"])])
    except SystemExit:
        # Remove this build's partial upload; the previous complete build stays.
        subprocess.run([publisher, "--retire", "local", "--build", build_id])
        raise
    run([publisher, "--retire", "local", "--keep", build_id])


def build() -> None:
    identity = firmware_release.identity(ROOT)
    print(f"Firmware build identity: {identity.version('<profile>')}", flush=True)
    out = ROOT / "build-ci"
    evidence = ARTIFACTS / "firmware"
    evidence.mkdir(parents=True, exist_ok=True)
    run(
        [
            west(),
            "build",
            "--pristine=always",
            "-b",
            BOARD,
            str(APP),
            "-d",
            str(out),
            "--",
            "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
            identity.cmake_arg("offline"),
        ],
        log=evidence / "build.log",
    )
    run(
        [west(), "build", "-d", str(out), "-t", "ram_report"],
        log=evidence / "ram-report.txt",
    )
    run(
        [west(), "build", "-d", str(out), "-t", "rom_report"],
        log=evidence / "rom-report.txt",
    )
    for source, name in [
        (out / "zephyr/.config", ".config"),
        (
            out / "zephyr/include/generated/zephyr/devicetree_generated.h",
            "devicetree_generated.h",
        ),
        (out / "zephyr/zephyr.elf", "zephyr.elf"),
        (out / "zephyr/zephyr.bin", "zephyr.bin"),
        (out / "zephyr/zephyr.map", "zephyr.map"),
    ]:
        if not source.is_file():
            raise SystemExit(f"required firmware evidence missing: {source}")
        shutil.copy2(source, evidence / name)
    # Compile feature combinations too: the default offline image cannot cover
    # TLS or the optional GPIO extension. These remain disconnected at boot.
    for profile, directory in PROFILES:
        if profile == "offline":
            continue
        run(
            [
                west(),
                "build",
                "--pristine=always",
                "-b",
                BOARD,
                str(APP),
                "-d",
                str(ROOT / directory),
                "--",
                *PROFILE_ARGS[profile],
                identity.cmake_arg(profile),
            ],
            log=evidence / f"{profile}-build.log",
        )
    # CI uploads this directory for the homelab's firmware sync; local runs publish it.
    release = ARTIFACTS / "firmware-release"
    manifest = firmware_release.stage(
        identity,
        [
            (profile, ROOT / directory / "zephyr/zephyr.bin")
            for profile, directory in PROFILES
        ],
        release,
        BOARD,
    )
    publish_local_firmware(identity, manifest, release)
    summary(
        "### Firmware build: PASS\n\n"
        f"Build identity: `{identity.version('<profile>')}`. See RAM/ROM reports in "
        "the firmware job log. Configured homelab builds also publish verified firmware to Personal Cloud."
    )


def qc() -> None:
    evaluator = ROOT / "Development/system/testing/qc_eval.py"
    result_process = subprocess.run([sys.executable, str(evaluator)], cwd=ROOT)
    result = json.loads(
        (evaluator.parent / "qc-eval-results.json").read_text(encoding="utf-8")
    )
    required = {"schema_version", "score", "maximum_score", "gate", "controls"}
    if not required.issubset(result):
        raise SystemExit(f"QC JSON missing fields: {sorted(required - result.keys())}")
    if not isinstance(result["controls"], list) or not result["controls"]:
        raise SystemExit("QC JSON schema violation: controls must be a non-empty array")
    if not all(
        isinstance(result[key], int)
        for key in ("schema_version", "score", "maximum_score")
    ):
        raise SystemExit(
            "QC JSON schema violation: schema version/scores must be integers"
        )
    disposition = "PASS" if result_process.returncode == 0 else "FAIL"
    summary(
        f"### QC evaluation: {disposition}\n\nScore: {result['score']}/"
        f"{result['maximum_score']}; gate: {result['gate']}. "
        "The scorecard is generated locally; no artifacts are uploaded."
    )
    if result_process.returncode != 0:
        raise SystemExit(
            f"QC evaluation failed: {result['score']}/{result['maximum_score']} "
            f"({result['gate']})"
        )


def main() -> None:
    stages = {"static": static, "build": build, "qc": qc}
    requested = sys.argv[1] if len(sys.argv) == 2 else "all"
    selected = list(stages) if requested == "all" else [requested]
    for name in selected:
        if name not in stages:
            raise SystemExit(
                f"usage: {Path(sys.argv[0]).name} [all|{'|'.join(stages)}]"
            )
        print(f"\n== {name} ==", flush=True)
        stages[name]()


if __name__ == "__main__":
    main()
