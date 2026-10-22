"""Exercise the production workflow with deterministic time and L1 failures."""

import os
from pathlib import Path
import shlex
import subprocess

import pytest


@pytest.fixture(scope="session")
def communication_runner(tmp_path_factory):
    app = Path(__file__).resolve().parents[2]
    output = tmp_path_factory.mktemp("communication") / "communication-runner.exe"
    compiler = shlex.split(os.environ.get("CC", "gcc"), posix=os.name != "nt")
    compiler = [part.strip('"') for part in compiler]
    sanitizers = []
    if os.environ.get("STETHO_SANITIZERS") == "true":
        sanitizers = ["-fsanitize=address,undefined", "-fno-sanitize-recover=all"]
    subprocess.run(
        [
            *compiler,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-Werror",
            *sanitizers,
            "-I",
            str(app / "tests/host/include"),
            "-I",
            str(app / "L1_services/L1_WIFI"),
            "-I",
            str(app / "L1_services/L1_PORTAL"),
            str(app / "tests/host/communication_runner.c"),
            "-o",
            str(output),
        ],
        check=True,
        timeout=120,
    )
    return output


@pytest.mark.parametrize(
    "scenario",
    [
        "control_burst",
        "retry_deadline",
        "result_deadline",
        "result_interrupt",
        "init_failure_offline",
        "scan_interrupt",
        "cleanup_failure",
        "connect_cancel_failure",
        "scan_timeout",
        "save_failure",
        "initial_scan_order",
        "recovery_once",
        "inactivity",
        "stale_acknowledgement",
        "start_keeps_station",
        "setup_hold_ignored",
        "partial_start_failure",
    ],
)
def test_communication_workflow(communication_runner, scenario):
    subprocess.run([str(communication_runner), scenario], check=True, timeout=10)
