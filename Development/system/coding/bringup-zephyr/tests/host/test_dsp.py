"""Behavioral tests: response, reference BPM, replay duration/pitch, FHIR."""

import json
from pathlib import Path
import subprocess

import numpy as np
import pytest

APP = Path(__file__).resolve().parents[2]
RATE = 16000


@pytest.fixture(scope="session")
def runner(tmp_path_factory):
    binary = tmp_path_factory.mktemp("dsp") / "dsp-runner"
    subprocess.run(
        [
            "gcc",
            "-std=c11",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-I",
            str(APP / "include"),
            str(APP / "src/stetho_dsp.c"),
            str(APP / "src/stetho_fhir.c"),
            str(APP / "tests/host/dsp_runner.c"),
            "-lm",
            "-o",
            str(binary),
        ],
        check=True,
    )
    return binary


def process(runner, tmp_path, signal, filter_id=0, analysis=2):
    src, dst = tmp_path / "in.f32", tmp_path / "out.f32"
    np.asarray(signal, dtype=np.float32).tofile(src)
    result = subprocess.run(
        [str(runner), "process", str(filter_id), str(analysis), str(src), str(dst)],
        check=True,
        capture_output=True,
        text=True,
    )
    estimates = [
        list(map(float, line.split(","))) for line in result.stdout.splitlines()
    ]
    return np.fromfile(dst, dtype=np.float32), estimates


@pytest.mark.parametrize(
    "filter_id,frequency,max_ratio",
    [(1, 5, 0.025), (1, 3000, 0.08), (2, 5, 0.05), (2, 1000, 0.03)],
)
def test_filter_rejects_out_of_band(runner, tmp_path, filter_id, frequency, max_ratio):
    t = np.arange(RATE * 2) / RATE
    x = 0.2 * np.sin(2 * np.pi * frequency * t)
    y, _ = process(runner, tmp_path, x, filter_id)
    assert np.std(y[RATE:]) / np.std(x[RATE:]) < max_ratio


@pytest.mark.parametrize("filter_id,frequency", [(0, 400), (1, 200), (2, 70)])
def test_passband_and_raw_reference(runner, tmp_path, filter_id, frequency):
    t = np.arange(RATE * 2) / RATE
    x = 0.2 * np.sin(2 * np.pi * frequency * t)
    y, _ = process(runner, tmp_path, x, filter_id)
    assert 0.85 < np.std(y[RATE:]) / np.std(x[RATE:]) < 1.05


@pytest.mark.parametrize("bpm", [30, 40, 60, 72, 100, 140, 180, 200])
@pytest.mark.parametrize("analysis", [0, 1, 2])
def test_reference_bpm(runner, tmp_path, bpm, analysis):
    t = np.arange(RATE * 12) / RATE
    phase = t % (60 / bpm)
    envelope = np.exp(-(phase**2) / 0.0008) + 0.55 * np.exp(
        -((phase - 0.28) ** 2) / 0.00045
    )
    x = 0.2 * envelope * np.sin(2 * np.pi * 80 * t)
    _, estimates = process(runner, tmp_path, x, analysis=analysis)
    valid = [row[2] for row in estimates if row[1]]
    assert len(valid) >= 4
    assert max(abs(value - bpm) for value in valid) <= 3


@pytest.mark.parametrize("kind", ["silence", "dc", "noise", "tone"])
def test_no_bpm_for_unusable_signal(runner, tmp_path, kind):
    x = np.zeros(RATE * 12)
    if kind == "dc":
        x[:] = 0.1
    elif kind == "tone":
        x = 0.2 * np.sin(2 * np.pi * 440 * np.arange(len(x)) / RATE)
    elif kind == "noise":
        x = np.random.default_rng(17).normal(0, 0.01, len(x))
    _, estimates = process(runner, tmp_path, x)
    assert not any(row[1] for row in estimates)


@pytest.mark.parametrize("speed", [50, 75, 100])
def test_replay_pitch_and_duration(runner, tmp_path, speed):
    t = np.arange(RATE * 2) / RATE
    x = (0.3 * np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
    src, dst = tmp_path / "clip.s16", tmp_path / "replay.f32"
    x.tofile(src)
    subprocess.run([str(runner), "replay", str(speed), str(src), str(dst)], check=True)
    y = np.fromfile(dst, dtype=np.float32)
    assert len(y) == len(x) * 100 // speed
    middle = y[RATE // 4 : -RATE // 4]
    spectrum = abs(np.fft.rfft(middle * np.hanning(len(middle))))
    frequency = np.fft.rfftfreq(len(middle), 1 / RATE)[spectrum.argmax()]
    assert abs(frequency - 440) < 5
    assert np.max(abs(y)) <= 0.301


def test_fhir_payload(runner):
    result = subprocess.run(
        [str(runner), "fhir"], check=True, capture_output=True, text=True
    )
    resource = json.loads(result.stdout)
    assert resource["resourceType"] == "Observation"
    assert resource["subject"]["reference"] == "Patient/test-patient"
    assert resource["valueQuantity"]["value"] == 72.5
    assert resource["valueQuantity"]["code"] == "/min"
    assert resource["code"]["coding"][0]["code"] == "8867-4"


def test_clipping_nan_and_lung_boundaries(runner):
    subprocess.run([str(runner), "boundaries"], check=True)


@pytest.mark.parametrize("frames", [0, 1, 159, 160, 161, 499])
@pytest.mark.parametrize("speed", [50, 75, 100])
def test_replay_short_and_empty_clips(runner, tmp_path, frames, speed):
    src, dst = tmp_path / "short.s16", tmp_path / "short.f32"
    np.full(frames, 1000, dtype=np.int16).tofile(src)
    subprocess.run([str(runner), "replay", str(speed), str(src), str(dst)], check=True)
    y = np.fromfile(dst, dtype=np.float32)
    assert len(y) == frames * 100 // speed
    assert np.all(np.isfinite(y))
    assert np.all(abs(y) < 0.031)


def test_signal_loss_expires_bpm(runner, tmp_path):
    t = np.arange(RATE * 12) / RATE
    phase = t % (60 / 72)
    heart = (
        0.2
        * (
            np.exp(-(phase**2) / 0.0008)
            + 0.55 * np.exp(-((phase - 0.28) ** 2) / 0.00045)
        )
        * np.sin(2 * np.pi * 80 * t)
    )
    _, estimates = process(
        runner, tmp_path, np.concatenate([heart, np.zeros(3 * RATE)])
    )
    assert any(row[1] for row in estimates[:12])
    assert not estimates[-1][1]
