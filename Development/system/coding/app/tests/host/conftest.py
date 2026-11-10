"""Compile real L1 units with deterministic kernel, driver, HTTP and settings adapters."""

import os
from pathlib import Path
import subprocess
import sys

import pytest

import host_build

HERE = Path(__file__).resolve().parent
APPLICATION = HERE.parents[1]
SIMULATION_INCLUDE_DIRECTORIES = [
    APPLICATION / "common",
    APPLICATION / "L2_application/L2_COMMUNICATION",
    APPLICATION / "L1_services/L1_WIFI",
    APPLICATION / "L1_services/L1_PORTAL",
    APPLICATION / "L1_services/L1_STORAGE",
    APPLICATION / "L1_services/L1_FHIR",
]


@pytest.fixture(scope="session")
def host_build_directory(tmp_path_factory):
    def directory(level, name):
        coverage = os.environ.get("STETHO_COVERAGE_DIRECTORY")
        if coverage:
            target = Path(coverage).resolve() / level / name
        else:
            target = tmp_path_factory.mktemp(name)
        target.mkdir(parents=True, exist_ok=True)
        return target

    return directory


@pytest.fixture(autouse=True)
def host_test_level(request, record_property):
    path = Path(str(request.node.fspath))
    if "integration" in path.parts:
        level = "integration"
    elif (
        path.parent.name.startswith("l1_") or path.parent.name == "server_profile_tool"
    ):
        level = "unit"
    else:
        level = "l2"
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
    return host_build.build(
        host_build_directory("unit", "services"),
        "services",
        [HERE / "l1_harness.c"],
        [
            APPLICATION / "L1_services/L1_WIFI",
            APPLICATION / "L1_services/L1_PORTAL",
            APPLICATION / "L1_services/L1_STORAGE",
        ],
        embed_portal_page=True,
    )


@pytest.fixture(scope="session")
def simulation_executable(host_build_directory):
    return host_build.build(
        host_build_directory("l2", "communication"),
        "simulation",
        [
            HERE / "simulation.c",
            APPLICATION / "L2_application/L2_COMMUNICATION/communication.c",
            APPLICATION / "L1_services/L1_FHIR/fhir.c",
        ],
        SIMULATION_INCLUDE_DIRECTORIES,
    )


@pytest.fixture(scope="session")
def memory_executable(host_build_directory):
    return host_build.build(
        host_build_directory("l2", "communication-memory"),
        "memory",
        [
            HERE / "communication_memory_harness.c",
            APPLICATION / "L1_services/L1_FHIR/fhir.c",
        ],
        SIMULATION_INCLUDE_DIRECTORIES,
    )


@pytest.fixture
def service(service_executable, record_property):
    service_executable.record_identity(record_property)

    def run(component, scenario, argument=""):
        result = subprocess.run(
            [str(service_executable.path), component, scenario, argument],
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
