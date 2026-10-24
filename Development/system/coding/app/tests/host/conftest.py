"""Compile real L1 units with deterministic kernel, driver, HTTP and settings adapters."""

import os
from pathlib import Path
import shlex
import subprocess
import sys

import pytest

HERE = Path(__file__).resolve().parent
APPLICATION = HERE.parents[1]


@pytest.fixture(scope="session")
def host_build_directory(tmp_path_factory):
    def directory(level, name):
        coverage = os.environ.get("STETHO_COVERAGE_DIRECTORY")
        target = (
            Path(coverage).resolve() / level / name
            if coverage
            else tmp_path_factory.mktemp(name)
        )
        target.mkdir(parents=True, exist_ok=True)
        return target

    return directory


@pytest.fixture(autouse=True)
def host_test_level(request, record_property):
    path = Path(str(request.node.fspath))
    level = (
        "integration"
        if "integration" in path.parts
        else "unit"
        if path.parent.name.startswith("l1_")
        else "l2"
    )
    record_property("level", level)


@pytest.fixture
def page_javascript_runtime():
    root = HERE.parents[5]
    sys.path.insert(0, str(root / "Development/system/testing/ci"))
    from validation_tools import node_runtime

    try:
        runtime = node_runtime(root)
    except RuntimeError as error:
        pytest.fail(str(error), pytrace=False)
    if runtime is None:
        pytest.skip(
            "Pinned Node installer supports Linux; CI executes the portal page check. "
            "Set STETHO_NODE to an absolute Node executable path to run it on Windows."
        )
    return runtime


@pytest.fixture(scope="session")
def service_executable(host_build_directory):
    target = host_build_directory("unit", "services") / (
        "services.exe" if sys.platform == "win32" else "services"
    )
    page = APPLICATION / "L1_services/L1_PORTAL/portal.html"
    generated = target.parent / "portal.html.inc"
    generated.write_text(",".join(str(value) for value in page.read_bytes()) + ",\n")
    compiler = shlex.split(os.environ.get("CC", "gcc"))
    command = compiler + [
        "-std=c11",
        "-D_POSIX_C_SOURCE=200809L",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-g",
    ]
    if os.environ.get("STETHO_COVERAGE_DIRECTORY"):
        command += ["--coverage", "-O0"]
    if os.environ.get("STETHO_SANITIZERS", "").lower() == "true":
        command += ["-fsanitize=address,undefined", "-fno-sanitize-recover=all"]
    for directory in (
        HERE / "include",
        target.parent,
        APPLICATION / "L1_services/L1_WIFI",
        APPLICATION / "L1_services/L1_PORTAL",
        APPLICATION / "L1_services/L1_STORAGE",
    ):
        command += ["-I", str(directory)]
    command += [str(HERE / "l1_harness.c"), "-o", str(target)]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
    except OSError as error:
        pytest.fail(
            f"Host C compiler could not start ({compiler}): {error}", pytrace=False
        )
    assert result.returncode == 0, result.stdout + result.stderr
    try:
        version = subprocess.check_output(
            compiler + ["--version"], text=True, timeout=30
        ).splitlines()[0]
    except subprocess.TimeoutExpired as error:
        pytest.fail(f"Host compiler identity timed out: {error.cmd}", pytrace=False)
    return target, command, version


@pytest.fixture
def service(service_executable, record_property):
    target, command, version = service_executable
    record_property("compiler_version", version)
    record_property("compiler_command", subprocess.list2cmdline(command))
    try:
        revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=HERE, text=True, timeout=30
        ).strip()
    except subprocess.TimeoutExpired as error:
        pytest.fail(f"Host source identity timed out: {error.cmd}", pytrace=False)
    except OSError as error:
        pytest.fail(f"Git is required for host source identity: {error}", pytrace=False)
    record_property("source_revision", revision)

    def run(component, scenario, argument=""):
        result = subprocess.run(
            [str(target), component, scenario, argument],
            capture_output=True,
            text=True,
            timeout=10,
        )
        record_property("service_output", result.stdout)
        record_property("service_error", result.stderr)
        assert result.returncode == 0, (
            f"{scenario}: {result.returncode}\n{result.stdout}\n{result.stderr}"
        )
        return result.stdout

    return run
