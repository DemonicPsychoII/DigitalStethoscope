"""VT-04: L1_PHYSICALINTERFACE input decoding from the input design constraint.

The harness compiles the production physicalinterface_input.c unchanged. GPIO, ADC
and work-queue access in physicalinterface.c need Zephyr and remain target checks.
"""

from pathlib import Path
import subprocess

import pytest

import host_build

HERE = Path(__file__).resolve().parent
APPLICATION = HERE.parents[2]
INPUT = "Development/system/design/system/interfaces-and-behavior.md (Input design constraint)"
DEBOUNCE = (
    "Development/system/design/system/parameters.md (P10 candidate debounce 30 ms)"
)
SWITCH = "Development/system/testing/hardware/carrier-bringup/README.md (J8 as fitted)"
VOLUME = "Development/system/coding/app/Kconfig (PHYSICALINTERFACE_VOLUME_POTENTIOMETER_FITTED off: potentiometer absent)"
SAFE_VOLUME_PERCENT = 0


@pytest.fixture(scope="module")
def harness(host_build_directory):
    target = host_build.build(
        host_build_directory("unit", "physicalinterface"),
        "physicalinterface",
        [HERE / "physicalinterface_harness.c"],
        [
            APPLICATION / "common",
            APPLICATION / "L1_services/L1_PHYSICALINTERFACE",
        ],
    )

    def run(operation, *arguments):
        completed = subprocess.run(
            [str(target.path), operation, *[str(item) for item in arguments]],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        return completed.stdout.splitlines()

    run.executable = target
    return run


def evidence(record_property, harness, scenario, basis, expected):
    harness.executable.record_identity(record_property)
    record_property("scenario", scenario)
    record_property("vt_id", "VT-04")
    record_property("basis", basis)
    record_property("expected", expected)


DECODE_CASES = [
    pytest.param((1, -5, -5), "VALID RAW", id="switch-raw-ignores-other-contacts"),
    pytest.param((0, 1, 0), "VALID MURMUR", id="switch-murmur"),
    pytest.param((0, 0, 1), "VALID BPM", id="switch-bpm"),
    pytest.param((0, 0, 0), "FAILED RAW", id="switch-no-position"),
    pytest.param((0, 1, 1), "FAILED RAW", id="switch-two-positions"),
    pytest.param((-5, 0, 0), "FAILED RAW", id="switch-raw-contact-read-error"),
    pytest.param((0, -5, 0), "FAILED RAW", id="switch-murmur-contact-read-error"),
    pytest.param((0, 1, -5), "FAILED RAW", id="switch-bpm-contact-read-error"),
]


@pytest.mark.parametrize("levels, expected", DECODE_CASES)
def test_switch_decoding(harness, record_property, levels, expected):
    evidence(
        record_property,
        harness,
        f"decode contact levels {levels}",
        f"{SWITCH}; {INPUT}",
        expected,
    )
    assert harness("decode", *levels) == [expected]


DEBOUNCE_CASES = [
    pytest.param(
        ["0:murmur", "10:murmur", "20:murmur", "30:murmur", "40:murmur", "50:murmur"],
        ["30 VALID MURMUR"],
        id="first-stable-reading-reported-once",
    ),
    pytest.param(
        ["0:bpm", "29:bpm", "30:bpm"],
        ["30 VALID BPM"],
        id="stable-only-after-debounce-time",
    ),
    pytest.param(
        ["0:raw", "30:raw", "100:invalid", "110:invalid", "120:invalid", "130:bpm"]
        + [f"{time}:bpm" for time in range(140, 200, 10)],
        ["30 VALID RAW", "160 VALID BPM"],
        id="measured-gap-between-positions-is-not-a-failure",
    ),
    pytest.param(
        ["0:raw", "30:raw", "100:murmur", "110:raw", "120:murmur", "130:raw"]
        + [f"{time}:raw" for time in range(140, 200, 10)],
        ["30 VALID RAW"],
        id="bounce-back-to-same-position-is-not-reported",
    ),
    pytest.param(
        ["0:murmur", "30:murmur"]
        + [f"{time}:invalid" for time in range(100, 140, 10)]
        + [f"{time}:murmur" for time in range(140, 180, 10)],
        ["30 VALID MURMUR", "130 FAILED RAW", "170 VALID MURMUR"],
        id="persistent-invalid-position-reports-safe-filter-then-recovery",
    ),
    pytest.param(
        [f"{time}:invalid" for time in range(0, 50, 10)],
        ["30 FAILED RAW"],
        id="invalid-position-from-start",
    ),
]


@pytest.mark.parametrize("steps, expected", DEBOUNCE_CASES)
def test_switch_debounce(harness, record_property, steps, expected):
    evidence(
        record_property,
        harness,
        "debounce " + " ".join(steps),
        f"{DEBOUNCE}; {INPUT}",
        "; ".join(expected),
    )
    assert harness("debounce", *steps) == expected


VOLUME_CASES = [
    pytest.param(-2147483648, 0, id="volume-clamped-at-lowest-input"),
    pytest.param(-1, 0, id="volume-clamped-below-zero"),
    pytest.param(0, 0, id="volume-silent-at-zero"),
    pytest.param(1542, 50, id="volume-half-scale"),
    pytest.param(3083, 100, id="volume-full-at-measured-top"),
    pytest.param(3300, 100, id="volume-clamped-above-measured-top"),
    pytest.param(2147483647, 100, id="volume-clamped-at-highest-input"),
]


@pytest.mark.parametrize("millivolts, expected", VOLUME_CASES)
def test_volume_scaling_is_clamped(harness, record_property, millivolts, expected):
    evidence(
        record_property,
        harness,
        f"volume from {millivolts} mV",
        f"{INPUT}; {SWITCH.split(' (')[0]} (potentiometer sweep to 3083 mV)",
        f"{expected} %",
    )
    assert harness("volume", millivolts) == [str(expected)]


def test_volume_reports_steps_ends_and_failure(harness, record_property):
    steps = [
        "0:valid:1542",
        "50:valid:1573",
        "100:valid:1604",
        "150:valid:3053",
        "200:valid:3083",
        "250:valid:3053",
        "300:failed:0",
        "350:failed:0",
        "400:valid:31",
        "450:valid:0",
    ]
    expected = [
        "0 VALID 50",
        "100 VALID 52",
        "150 VALID 99",
        "200 VALID 100",
        f"300 FAILED {SAFE_VOLUME_PERCENT}",
        "400 VALID 1",
        "450 VALID 0",
    ]
    evidence(
        record_property,
        harness,
        "volume tracking " + " ".join(steps),
        INPUT,
        "; ".join(expected),
    )
    assert harness("track", *steps) == expected


def test_absent_potentiometer_is_reported_once(harness, record_property):
    expected = [f"0 ABSENT {SAFE_VOLUME_PERCENT}"]
    evidence(
        record_property,
        harness,
        "absent potentiometer polled twice",
        f"{VOLUME}; {INPUT}",
        "; ".join(expected),
    )
    assert harness("track", "0:absent:0", "50:absent:0") == expected
