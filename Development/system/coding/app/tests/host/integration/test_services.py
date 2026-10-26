"""VT-14 real COMMUNICATION, WIFI, PORTAL and STORAGE at the Zephyr boundary."""

import os
from pathlib import Path
import shlex
import subprocess
import sys

import pytest

HERE = Path(__file__).resolve().parent
APPLICATION = HERE.parents[2]


@pytest.fixture(scope="session")
def integration_executable(host_build_directory):
    if sys.platform == "win32":
        executable_name = "integration.exe"
    else:
        executable_name = "integration"
    target = host_build_directory("integration", "services") / executable_name
    (target.parent / "portal.html.inc").write_text(
        ",".join(
            str(value)
            for value in (
                APPLICATION / "L1_services/L1_PORTAL/portal.html"
            ).read_bytes()
        )
        + ",\n"
    )
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
        HERE.parent / "include",
        target.parent,
        APPLICATION / "L2_application/L2_COMMUNICATION",
        *(
            APPLICATION / "L1_services" / name
            for name in ("L1_WIFI", "L1_PORTAL", "L1_STORAGE")
        ),
    ):
        command += ["-I", str(directory)]
    command += [str(HERE / "harness.c"), "-o", str(target)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    return (
        target,
        command,
        subprocess.check_output(
            compiler + ["--version"], text=True, timeout=30
        ).splitlines()[0],
    )


@pytest.mark.parametrize(
    "scenario",
    (
        "boot-record",
        "protected-join",
        "open-join",
        "save-failure",
        "join-failure",
        "invalid-form",
        "start-selection",
        "cancel-selection",
        "rescan-exhaustion",
        "boot-disconnect-before-ipv4",
        "page-disconnect-before-ipv4",
    ),
)
def test_real_services(scenario, integration_executable, record_property):
    target, command, compiler = integration_executable
    for name, value in (
        ("scenario", "integration-" + scenario),
        ("vt_id", "VT-14"),
        (
            "basis",
            "Development/system/design/WIFI/interfaces-and-behavior.md#wi-fi-setup-and-recovery",
        ),
        ("compiler_version", compiler),
        ("compiler_command", subprocess.list2cmdline(command)),
        (
            "source_revision",
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=HERE, text=True, timeout=30
            ).strip(),
        ),
    ):
        record_property(name, value)
    result = subprocess.run(
        [str(target), scenario], capture_output=True, text=True, timeout=10
    )
    record_property("service_trace", result.stdout)
    record_property("service_error", result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr
    observed = {
        key: int(value)
        for key, value in (line.split() for line in result.stdout.splitlines())
    }
    assert observed["cleanup_fault"] == 0
    if scenario == "boot-disconnect-before-ipv4":
        assert observed["connect_calls"] == 4 and observed["boot_attempts"] == 4
        assert observed["first_join_milliseconds"] == 0
        assert observed["last_join_milliseconds"] == 15600
        assert observed["scan_calls"] == 0 and observed["writes"] == 0
        assert observed["connected"] == 0 and observed["page"] == 0
        assert (
            observed["record_old"] == 1
            and observed["join_failure"] == observed["not_connected_error"]
        )
    elif scenario == "page-disconnect-before-ipv4":
        assert observed["connect_calls"] == 1 and observed["scan_calls"] == 2
        assert observed["first_join_milliseconds"] == 1500
        assert observed["writes"] == 0 and observed["page"] == 1
        assert (
            observed["connected"] == 0
            and observed["join_failure"] == observed["not_connected_error"]
        )
    elif scenario == "boot-record":
        assert observed["connect_calls"] == 1 and observed["scan_calls"] == 0
        assert (
            observed["connected"] == 1
            and observed["page"] == 0
            and observed["writes"] == 0
        )
    elif scenario in {"protected-join", "open-join", "save-failure"}:
        assert (
            observed["response"] == 202
            and observed["connected"] == 1
            and observed["page"] == 0
        )
        if scenario == "save-failure":
            assert observed["writes"] == 2
            assert observed["record_new"] == 0
            assert observed["record_old"] == 1
        else:
            assert observed["writes"] == 1
            assert observed["record_new"] == 1
            assert observed["record_old"] == 0
    elif scenario in {"join-failure", "invalid-form"}:
        if scenario == "invalid-form":
            assert observed["response"] == 400
        else:
            assert observed["response"] == 202
        assert observed["writes"] == 0 and observed["page"] == 1
        if scenario == "invalid-form":
            assert observed["scan_calls"] == 1
        else:
            assert observed["scan_calls"] == 2
        assert observed["network_count"] == 1 and observed["clients"] == 1
    elif scenario == "rescan-exhaustion":
        assert (
            observed["scan_calls"] == 5
            and observed["page"] == 0
            and observed["connected"] == 1
        )
        assert observed["status_at_stop"] == 6 and observed["writes"] == 0
    else:
        assert (
            observed["page"] == 0
            and observed["writes"] == 0
            and observed["connected"] == 0
        )
        if scenario == "start-selection":
            assert observed["ack"] == 0
        else:
            assert observed["status_at_stop"] == 6
