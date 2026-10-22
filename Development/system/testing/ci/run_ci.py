#!/usr/bin/env python3
"""Shared fail-fast entry point for local and GitHub CI quality gates."""

from __future__ import annotations

import argparse
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
THESIS_APP = ROOT / "Development/system/coding/app"
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


def generated_output(relative: str) -> bool:
    path = "/" + relative.replace("\\", "/")
    # These maintained headers substitute the Zephyr API in host scenarios.
    host_headers = "/Development/system/coding/app/tests/host/include/zephyr/"
    return (
        any(token in path for token in ("/build/", "/.west/", "twister-out"))
        or ("/zephyr/" in path and not path.startswith(host_headers))
        or path.endswith((".elf", ".bin", ".map"))
    )


def static() -> None:
    ARTIFACTS.joinpath("ci").mkdir(parents=True, exist_ok=True)
    run(["git", "diff", "--check", "HEAD"])
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).split(b"\0")
    for raw in filter(None, tracked):
        rel = raw.decode("utf-8")
        if generated_output(rel):
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
    run([sys.executable, "-m", "ruff", "check", "Development/system/testing"])
    run(
        [
            sys.executable,
            "-m",
            "ruff",
            "format",
            "--check",
            "Development/system/testing",
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
        maintained_sources.extend(
            str(path)
            for path in sorted(THESIS_APP.rglob("*"))
            if path.is_file() and path.suffix in {".c", ".h"}
        )
        if not maintained_sources:
            raise SystemExit("no maintained C sources were discovered for formatting")
        run([clang_format, "--dry-run", "--Werror", *maintained_sources])
    elif os.environ.get("CI"):
        raise SystemExit("clang-format is required in CI")
    workflow_validators()
    summary("### Static checks: PASS")


def workflow_validators() -> None:
    commands = {
        "actionlint": ["actionlint", "-color"],
        "shellcheck": [
            "shellcheck",
            "Development/system/testing/ci/setup_zephyr.sh",
            ".github/agent-gate/revert-last-merge.sh",
        ],
    }
    for tool, command in commands.items():
        if shutil.which(tool):
            run(command)
        elif sys.platform == "win32" and not os.environ.get("CI"):
            print(f"SKIP {tool}: pinned installer supports Linux; CI runs this check.")
        else:
            raise SystemExit(f"{tool} is required; run validation_tools.py first")


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


def retain_firmware_evidence(build_dir: Path, evidence: Path) -> None:
    evidence.mkdir(parents=True, exist_ok=True)
    for source, name in [
        (build_dir / "zephyr/.config", ".config"),
        (
            build_dir / "zephyr/include/generated/zephyr/devicetree_generated.h",
            "devicetree_generated.h",
        ),
        (build_dir / "zephyr/zephyr.elf", "zephyr.elf"),
        (build_dir / "zephyr/zephyr.bin", "zephyr.bin"),
        (build_dir / "zephyr/zephyr.map", "zephyr.map"),
    ]:
        if not source.is_file():
            raise SystemExit(f"required firmware evidence missing: {source}")
        shutil.copy2(source, evidence / name)


def build_application(identity: firmware_release.Identity) -> None:
    run(
        [
            west(),
            "build",
            "--pristine=always",
            "-b",
            BOARD,
            str(THESIS_APP),
            "-d",
            str(ROOT / "build-ci-app"),
            "--",
            identity.cmake_arg("application"),
        ],
        log=ARTIFACTS / "firmware" / "app-build.log",
    )
    retain_firmware_evidence(
        ROOT / "build-ci-app", ARTIFACTS / "firmware" / "application"
    )


def build(*, application: bool = True, firmware: bool = True) -> None:
    identity = firmware_release.identity(ROOT)
    outputs = []
    release = ARTIFACTS / "firmware-release"
    if application:
        build_application(identity)
        outputs.append(("application", ROOT / "build-ci-app/zephyr/zephyr.bin"))
    if not firmware:
        firmware_release.stage(identity, outputs, release, BOARD)
        summary(
            f"### Application build: PASS\n\nBuild identity: `{identity.version('application')}`"
        )
        return
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
    retain_firmware_evidence(out, evidence)
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
    outputs.extend(
        (profile, ROOT / directory / "zephyr/zephyr.bin")
        for profile, directory in PROFILES
    )
    manifest = firmware_release.stage(identity, outputs, release, BOARD)
    # Publish the complete bundle only; component-only runs supply local evidence.
    if application:
        publish_local_firmware(identity, manifest, release)
    summary(
        "### Firmware build: PASS\n\n"
        f"Build identity: `{identity.version('<profile>')}`. See RAM/ROM reports in "
        "the firmware job log. Configured homelab builds also publish verified firmware to Personal Cloud."
    )


def qc() -> None:
    evaluator = ROOT / "Development/system/testing/qc_eval.py"
    output = ARTIFACTS / "qc"
    output.mkdir(parents=True, exist_ok=True)
    # A crashed evaluator must not reuse a previous run's passing report.
    for name in ("qc-eval-results.json", "QC-EVALUATION.md"):
        (output / name).unlink(missing_ok=True)
    result_process = subprocess.run(
        [sys.executable, str(evaluator), "--output-dir", str(output)], cwd=ROOT
    )
    result = json.loads((output / "qc-eval-results.json").read_text(encoding="utf-8"))
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
        "The scorecard is retained with the CI evidence; it is source-level evidence only."
    )
    if result_process.returncode != 0:
        raise SystemExit(
            f"QC evaluation failed: {result['score']}/{result['maximum_score']} "
            f"({result['gate']})"
        )


def main() -> None:
    stages = {"static": static, "build": build, "qc": qc}
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", nargs="?", choices=("all", *stages), default="all")
    parser.add_argument("--application", action="store_true")
    parser.add_argument("--firmware", action="store_true")
    args = parser.parse_args()
    if (args.application or args.firmware) and args.stage != "build":
        parser.error("component selection is supported only for build")
    requested = args.stage
    selected = list(stages) if requested == "all" else [requested]
    for name in selected:
        if name not in stages:
            raise SystemExit(
                f"usage: {Path(sys.argv[0]).name} [all|{'|'.join(stages)}]"
            )
        print(f"\n== {name} ==", flush=True)
        if name == "build" and (args.application or args.firmware):
            build(application=args.application, firmware=args.firmware)
        else:
            stages[name]()


if __name__ == "__main__":
    main()
