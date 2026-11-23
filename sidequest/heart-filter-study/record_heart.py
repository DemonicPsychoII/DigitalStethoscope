"""Record one heart-sound dataset raw from the capture firmware.

Usage: record_heart.py <name> [--seconds 60] [--reference-bpm-start N] [--reference-bpm-end N] [--note TEXT]
Writes recordings/<name>/capture.wav (24-bit, 16 kHz) and recording.json.
"""

import argparse
import datetime
import json
import sys
from pathlib import Path

import numpy as np
import soundfile

sys.path.insert(
    0,
    str(
        Path.home()
        / ".t3/worktrees/DigitalStethoscope/feature-audio-chain-swe-2447cecce9041295"
        / "Development/system/testing/AUDIO/chain-measurement"
    ),
)
import device_capture  # noqa: E402

parser = argparse.ArgumentParser()
parser.add_argument("name")
parser.add_argument("--seconds", type=int, default=60)
parser.add_argument("--serial-port", default="COM4")
parser.add_argument("--reference-bpm-start", type=float)
parser.add_argument("--reference-bpm-end", type=float)
parser.add_argument("--note", default="")
arguments = parser.parse_args()

directory = Path(__file__).parent / "recordings" / arguments.name
directory.mkdir(parents=True, exist_ok=False)
started = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
shell = device_capture.DeviceShell(arguments.serial_port)
try:
    shell.record(arguments.seconds)
    shell.wait_for_state({"RECORDING"}, timeout_seconds=5)
    print("RECORDING", flush=True)
    shell.wait_for_state({"COMPLETE"}, timeout_seconds=arguments.seconds + 10)
    print(f"Reading {arguments.seconds} s out of the device.", flush=True)
    samples, rate = shell.read_capture()
finally:
    shell.close()
soundfile.write(directory / "capture.wav", samples, rate, "PCM_24")
settled = samples[2 * rate :]
(directory / "recording.json").write_text(
    json.dumps(
        {
            "name": arguments.name,
            "started_at": started,
            "seconds": arguments.seconds,
            "sample_rate_hz": rate,
            "firmware": "chain-measurement capture-firmware, raw INMP441 left slot, 921600 baud",
            "reference_bpm_start": arguments.reference_bpm_start,
            "reference_bpm_end": arguments.reference_bpm_end,
            "note": arguments.note,
            "peak_after_2_s_fs": float(np.max(np.abs(settled))),
            "rms_after_2_s_dbfs": float(20 * np.log10(np.sqrt(np.mean(settled**2)) + 1e-12)),
        },
        indent=2,
    ),
    "utf-8",
)
print(f"Saved {directory}")
