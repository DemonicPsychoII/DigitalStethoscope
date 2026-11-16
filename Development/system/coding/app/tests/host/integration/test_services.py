"""VT-14 real COMMUNICATION, WIFI, PORTAL and STORAGE at the Zephyr boundary."""

from pathlib import Path
import subprocess

import pytest

import host_build

HERE = Path(__file__).resolve().parent
APPLICATION = HERE.parents[2]


@pytest.fixture(scope="session")
def integration_executable(host_build_directory):
    return host_build.build(
        host_build_directory("integration", "services"),
        "integration",
        [HERE / "harness.c"],
        [
            APPLICATION / "common",
            APPLICATION / "L2_application/L2_COMMUNICATION",
            *(
                APPLICATION / "L1_services" / name
                for name in ("L1_WIFI", "L1_PORTAL", "L1_STORAGE", "L1_FHIR")
            ),
        ],
        embed_portal_page=True,
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
        "start-selection-stops-block",
        "cancel-selection",
        "rescan-exhaustion",
        "boot-disconnect-before-ipv4",
        "page-disconnect-before-ipv4",
    ),
)
def test_real_services(scenario, integration_executable, record_property):
    integration_executable.record_identity(record_property)
    for name, value in (
        ("scenario", "integration-" + scenario),
        ("vt_id", "VT-14"),
        (
            "basis",
            "Development/system/design/COMMUNICATION/interfaces-and-behavior.md#wi-fi-setup-and-recovery",
        ),
    ):
        record_property(name, value)
    result = subprocess.run(
        [str(integration_executable.path), scenario],
        capture_output=True,
        text=True,
        timeout=10,
    )
    record_property("service_trace", result.stdout)
    record_property("service_error", result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr
    observed = {
        key: int(value)
        for key, value in (line.split() for line in result.stdout.splitlines())
    }
    if scenario == "start-selection-stops-block":
        # Start at 1 s; the DHCP server stop and AP disable each end at the 1 s P23 bound.
        assert observed["cleanup_fault"] == 1
        assert observed["cleanup_feedback_count"] == 1
        assert observed["cleanup_feedback_milliseconds"] == 1000 + 2 * 1000
        assert observed["dhcp_driver_calls"] == 0 and observed["hotspot_driver_calls"] == 0
        assert observed["ack"] == 0 and observed["page"] == 0
        return
    assert observed["cleanup_fault"] == 0
    assert observed["cleanup_feedback_count"] == 0
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
