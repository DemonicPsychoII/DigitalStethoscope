"""Skip firmware provisioning only when no firmware or CI input changed."""

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
# Register each implemented host suite with the component paths that affect it.
COMPONENT_HOST_SUITES = {
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
    app = "Development/system/coding/bringup-zephyr/"
    ci = "Development/system/testing/ci/"
    thesis_app = "Development/system/coding/app/"
    for path in paths:
        if path == ".github/workflows/quality-gates.yml":
            return True
        if path.startswith(thesis_app) and component == thesis_app:
            relative = path[len(thesis_app) :]
            if relative.startswith("tests/host/") or relative.endswith(
                (".md", ".png", ".svg", ".puml", ".gitkeep")
            ):
                continue
            return True
        if path.startswith(app) and component == app:
            relative = path[len(app) :]
            if relative.startswith(("tools/", "tests/", "evidence/")):
                continue
            if relative.endswith((".md", ".png", ".svg", ".puml")):
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
                    "benchmark_build.py",
                    "ci_results.py",
                    "ci_evidence.py",
                    "native_tests.py",
                    "validation_tools.py",
                    "validation_tools.json",
                    "validate_docs.py",
                    "release_reuse.py",
                    "post_merge.py",
                    "native_review.py",
                }
                or relative.endswith(".md")
            ):
                continue
            return True
    return False


def needs_firmware(paths: list[str]) -> bool:
    return any(
        needs_build(paths, component)
        for component in (
            "Development/system/coding/app/",
            "Development/system/coding/bringup-zephyr/",
        )
    )


def suites(paths: list[str]) -> dict[str, bool]:
    workflow = ".github/workflows/quality-gates.yml" in paths
    firmware = needs_build(paths, "Development/system/coding/bringup-zephyr/")
    application = needs_build(paths, "Development/system/coding/app/")
    return {
        "firmware": firmware,
        "application": application,
        "native": firmware
        or any(
            p.startswith("Development/system/coding/bringup-zephyr/tests/logic/")
            or p.endswith("/native_tests.py")
            for p in paths
        ),
        "docs": any(p.endswith((".md", ".puml")) or "/tests/" in p for p in paths),
        "host": workflow
        or firmware
        or application
        or any(
            p.startswith(
                (
                    "Development/system/coding/bringup-zephyr/",
                    "Development/system/coding/app/",
                )
            )
            and ("/tools/" in p or "/tests/host/" in p)
            for p in paths
        ),
        "tooling": workflow
        or any(p.startswith("Development/system/testing/ci/") for p in paths)
        or "Development/system/testing/qc_eval.py" in paths,
        "gate": workflow or any(p.startswith(".github/agent-gate/") for p in paths),
        "application_host": "communication" in available_component_suites()
        and (
            workflow
            or firmware
            or application
            or component_host_affected(paths, "communication")
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
        selected["application_host"] = "communication" in available_component_suites()
        return selected
    selected = suites(paths)
    if daily:
        # A reused bundle already passed its host, native and build checks.
        selected = dict.fromkeys(selected, False)
    if retain or ((daily or publish) and not reuse):
        selected.update(
            application=True,
            firmware=True,
            native=True,
            host=True,
            application_host="communication" in available_component_suites(),
        )
    return selected


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
    selected = select(
        paths,
        full=os.environ.get("CI_FULL") == "true",
        daily=os.environ.get("CI_DAILY") == "true",
        reuse=bool(os.environ.get("REUSE")),
        publish=os.environ.get("CI_PUBLISH") == "true",
        retain=os.environ.get("CI_RETAIN") == "true",
    )
    with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as output:
        for name, needed in selected.items():
            output.write(f"{name}={str(needed).lower()}\n")
    print(f"Selected suites: {selected}")


if __name__ == "__main__":
    main()
