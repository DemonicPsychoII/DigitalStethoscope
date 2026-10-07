"""Skip firmware provisioning only when no firmware or CI input changed."""

import os
import subprocess
from pathlib import Path


def needs_firmware(paths: list[str]) -> bool:
    app = "Development/system/coding/bringup-zephyr/"
    ci = "Development/system/testing/ci/"
    thesis_app = "Development/system/coding/app/"
    for path in paths:
        if path == ".github/workflows/quality-gates.yml":
            return True
        if path.startswith(thesis_app):
            relative = path[len(thesis_app) :]
            if relative.startswith("tests/host/") or relative.endswith(
                (".md", ".png", ".svg", ".puml", ".gitkeep")
            ):
                continue
            return True
        if path.startswith(app):
            relative = path[len(app) :]
            if relative.startswith(("tools/", "tests/host/", "evidence/")):
                continue
            if relative.endswith((".md", ".png", ".svg", ".puml")):
                continue
            return True
        if path.startswith(ci):
            relative = path[len(ci) :]
            if (
                relative.startswith("test_")
                or relative
                in {"daily_build.py", "firmware_changes.py", "benchmark_build.py"}
                or relative.endswith(".md")
            ):
                continue
            return True
    return False


def suites(paths: list[str]) -> dict[str, bool]:
    workflow = ".github/workflows/quality-gates.yml" in paths
    firmware = needs_firmware(paths)
    return {
        "firmware": firmware,
        "host": workflow
        or firmware
        or any(
            p.startswith("Development/system/coding/bringup-zephyr/")
            and ("/tools/" in p or "/tests/host/" in p)
            for p in paths
        ),
        "tooling": workflow
        or any(p.startswith("Development/system/testing/ci/") for p in paths)
        or "Development/system/testing/qc_eval.py" in paths,
        "gate": workflow or any(p.startswith(".github/agent-gate/") for p in paths),
    }


def main() -> None:
    changed = subprocess.check_output(
        [
            "git",
            "diff",
            "--name-only",
            "--no-renames",
            "-z",
            os.environ["BASE_SHA"],
            os.environ["HEAD_SHA"],
            "--",
        ]
    )
    paths = changed.decode("utf-8", errors="surrogateescape").split("\0")
    with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as output:
        for name, needed in suites(paths).items():
            output.write(f"{name}={str(needed).lower()}\n")
    print(f"Selected suites: {suites(paths)}")


if __name__ == "__main__":
    main()
