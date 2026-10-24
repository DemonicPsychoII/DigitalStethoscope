"""Skip firmware provisioning only when no firmware or CI input changed."""

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
# Register each implemented host suite with the component paths that affect it.
COMPONENT_HOST_SUITES = {
    "integration": {
        "tests": "Development/system/coding/app/tests/host/integration",
        "components": ("WIFI", "PORTAL", "L1_STORAGE", "L2_COMMUNICATION"),
    },
    "wifi": {
        "tests": "Development/system/coding/app/tests/host/l1_wifi",
        "components": ("WIFI", "L1_STORAGE"),
    },
    "portal": {
        "tests": "Development/system/coding/app/tests/host/l1_portal",
        "components": ("WIFI", "PORTAL"),
    },
    "communication": {
        "tests": "Development/system/coding/app/tests/host",
        "components": ("WIFI", "PORTAL", "L2_COMMUNICATION"),
    },
}


def available_component_suites() -> tuple[str, ...]:
    return tuple(
        name
        for name, suite in COMPONENT_HOST_SUITES.items()
        if (ROOT / suite["tests"]).is_dir()
    )


def component_host_affected(paths: list[str], suite: str) -> bool:
    components = COMPONENT_HOST_SUITES[suite]["components"]
    for path in paths:
        parts = path.split("/")
        if any(
            part in components or part.removeprefix("L1_") in components
            for part in parts
        ):
            return True
        if path.startswith(
            (
                "Development/system/requirements/",
                "Development/system/design/system/",
                "Development/system/architecture/system/",
            )
        ):
            return True
        if (
            path.startswith(
                ("Development/system/design/", "Development/system/architecture/")
            )
            and len(parts) == 4
        ):
            return True
    return False


def needs_build(paths: list[str], component: str) -> bool:
    ci = "Development/system/testing/ci/"
    thesis_app = "Development/system/coding/app/"
    for path in paths:
        if path == ".github/workflows/quality-gates.yml":
            return True
        if path.startswith(thesis_app) and component == thesis_app:
            relative = path[len(thesis_app) :]
            if relative.startswith("tests/") or relative.endswith(
                (".md", ".png", ".svg", ".puml", ".gitkeep")
            ):
                continue
            return True
        if path.startswith(ci):
            relative = path[len(ci) :]
            if (
                relative.startswith("test_")
                or relative
                in {
                    "daily_build.py",
                    "firmware_changes.py",
                    "ci_results.py",
                    "ci_evidence.py",
                    "validation_tools.py",
                    "validation_tools.json",
                    "validate_docs.py",
                    "release_reuse.py",
                    "post_merge.py",
                    "native_review.py",
                    "host_coverage.py",
                    "manual_test_records.py",
                    "application_host_results.py",
                }
                or relative.endswith(".md")
            ):
                continue
            return True
    return False


def needs_firmware(paths: list[str]) -> bool:
    return needs_build(paths, "Development/system/coding/app/")


def suites(paths: list[str]) -> dict[str, bool]:
    paths = [p for p in paths if not p.startswith("preThesis/06-bringup-zephyr/")]
    workflow = ".github/workflows/quality-gates.yml" in paths
    application = needs_firmware(paths)
    return {
        "application": application,
        # Documentation checks compare docs with renders, pins, scripts and the thesis kit.
        "docs": workflow
        or any(
            p.endswith((".md", ".puml", ".svg"))
            or "/tests/" in p
            or p.startswith(("thesis-material/", "Development/system/testing/ci/"))
            for p in paths
        ),
        "tooling": workflow
        or any(p.startswith("Development/system/testing/ci/") for p in paths),
        "gate": workflow or any(p.startswith(".github/agent-gate/") for p in paths),
        "application_host": bool(available_component_suites())
        and (
            workflow
            or application
            or any(
                component_host_affected(paths, suite)
                for suite in available_component_suites()
            )
            or any(
                p.startswith("Development/system/coding/app/tests/host/") for p in paths
            )
        ),
    }


def select(
    paths: list[str],
    *,
    full: bool,
    daily: bool,
    reuse: bool,
    publish: bool = False,
    retain: bool = False,
) -> dict[str, bool]:
    if full:
        selected = dict.fromkeys(suites([]), True)
        selected["application_host"] = bool(available_component_suites())
        return selected
    selected = suites(paths)
    if daily:
        # A reused application artifact already passed its selected verification.
        selected = dict.fromkeys(selected, False)
    if retain or ((daily or publish) and not reuse):
        selected.update(
            application=True,
            application_host=bool(available_component_suites()),
        )
    return selected


def changed_paths(base: str, head: str) -> list[str] | None:
    # New-branch pushes have a zero base; force pushes can reference missing commits.
    # Without a usable comparison, run every suite rather than omit verification.
    if (
        not base
        or subprocess.run(
            [
                "git",
                "rev-parse",
                "--verify",
                "--quiet",
                "--end-of-options",
                f"{base}^{{commit}}",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode
    ):
        print("Base revision unavailable; selecting every verification suite.")
        return None
    changed = subprocess.check_output(
        [
            "git",
            "diff",
            "--name-only",
            "--no-renames",
            "-z",
            base,
            head,
            "--",
        ]
    )
    return changed.decode("utf-8", errors="surrogateescape").split("\0")


def main() -> None:
    paths = changed_paths(os.environ.get("BASE_SHA", ""), os.environ["HEAD_SHA"])
    selected = select(
        paths or [],
        full=paths is None or os.environ.get("CI_FULL") == "true",
        daily=os.environ.get("CI_DAILY") == "true",
        reuse=bool(os.environ.get("REUSE")),
        publish=os.environ.get("CI_PUBLISH") == "true",
        retain=os.environ.get("CI_RETAIN") == "true",
    )
    if not (ROOT / "Development/system/coding/app/CMakeLists.txt").is_file():
        selected["application"] = False
    with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as output:
        for name, needed in selected.items():
            output.write(f"{name}={str(needed).lower()}\n")
    print(f"Selected suites: {selected}")


if __name__ == "__main__":
    main()
