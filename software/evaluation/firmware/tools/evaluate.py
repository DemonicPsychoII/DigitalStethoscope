#!/usr/bin/env python3
"""Reproducible host DSP evaluation, serial capture/upload and FHIR readback."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import ssl
import subprocess
import time
from urllib.parse import urlparse
from urllib.request import Request, HTTPRedirectHandler, HTTPSHandler, build_opener
import wave

import numpy as np

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parents[2]
RATE = 16000
FILTERS = ("raw", "murmur", "bpm")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def provenance():
    return {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "working_tree_modified": bool(
            subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)
        ),
        "dsp_sha256": digest(APP / "src/stetho_dsp.c"),
    }


def read_wave(path):
    with wave.open(str(path), "rb") as wav:
        if (wav.getframerate(), wav.getnchannels(), wav.getsampwidth()) != (RATE, 1, 2):
            raise ValueError(
                "Expected mono 16-bit PCM WAV at 16000 Hz; resample explicitly first"
            )
        return np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2").copy()


def write_wave(path, signal):
    with wave.open(str(path), "wb") as wav:
        wav.setparams((1, 2, RATE, 0, "NONE", "not compressed"))
        wav.writeframes((np.clip(signal, -1, 0.999969) * 32768).astype("<i2").tobytes())


def build_runner(output):
    binary = output / "dsp-runner"
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


def evaluate(args):
    args.output.mkdir(parents=True, exist_ok=True)
    x = read_wave(args.wav)
    if len(x) < RATE * 10:
        raise ValueError(
            "At least 10 seconds required for the 8-second estimator window"
        )
    source = args.output / "input.f32"
    (x.astype(np.float32) / 32768).tofile(source)
    runner = build_runner(args.output)
    report = provenance() | {
        "kind": "host-dsp",
        "signal": str(args.wav),
        "signal_sha256": digest(args.wav),
        "reference_bpm": args.reference_bpm,
        "reference_description": args.reference,
        "analysis_mode": args.analysis_filter,
        "filters": [],
    }
    for index, name in enumerate(FILTERS):
        analysis = (
            index
            if args.analysis_filter == "matched"
            else FILTERS.index(args.analysis_filter)
        )
        target = args.output / f"{name}.f32"
        result = subprocess.run(
            [
                str(runner),
                "process",
                str(index),
                str(analysis),
                str(source),
                str(target),
            ],
            check=True,
            text=True,
            capture_output=True,
        )
        (args.output / f"{name}-estimates.csv").write_text(
            "sample,valid,bpm,quality\n" + result.stdout
        )
        rows = [
            list(map(float, line.split(","))) for line in result.stdout.splitlines()
        ]
        eligible = [r for r in rows if r[0] >= 8 * RATE]
        errors = [r[2] - args.reference_bpm for r in eligible if r[1]]
        report["filters"].append(
            {
                "name": name,
                "listening_filter": name,
                "analysis_filter": FILTERS[analysis],
                "valid_windows": len(errors),
                "eligible_windows": len(eligible),
                "coverage": len(errors) / len(eligible) if eligible else 0,
                "mae_bpm": float(np.mean(np.abs(errors))) if errors else None,
                "bias_bpm": float(np.mean(errors)) if errors else None,
                "rmse_bpm": float(np.sqrt(np.mean(np.square(errors))))
                if errors
                else None,
                "max_absolute_error_bpm": float(np.max(np.abs(errors)))
                if errors
                else None,
            }
        )
        write_wave(args.output / f"{name}.wav", np.fromfile(target, dtype=np.float32))
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


def generate(args):
    t = np.arange(int(args.seconds * RATE)) / RATE
    phase = t % (60 / args.bpm)
    if args.kind == "heart":
        envelope = np.exp(-(phase**2) / 0.0008) + 0.55 * np.exp(
            -((phase - 0.28) ** 2) / 0.00045
        )
        signal = 0.2 * envelope * np.sin(2 * np.pi * 80 * t)
    elif args.kind == "tone":
        signal = 0.03 * np.sin(2 * np.pi * 440 * t)
    else:
        signal = np.zeros(len(t))
        signal[::RATE] = 0.25
    write_wave(args.output, signal)


ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


class Console:
    def __init__(self, port):
        import serial

        self.raw_log = None
        self.serial = serial.Serial(port=None, baudrate=115200, timeout=0.2)
        self.serial.dtr = False
        self.serial.rts = False
        self.serial.port = port
        self.serial.open()
        self.serial.write(b"\r\n")
        # Drain boot/log/prompt fragments before issuing the first command.
        time.sleep(0.3)
        self.serial.reset_input_buffer()

    def close(self):
        self.serial.close()

    def command(self, command, status=False):
        self.serial.write((command + "\r\n").encode())
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            raw = self.serial.readline().decode(errors="replace")
            if self.raw_log:
                self.raw_log.write(raw)
                self.raw_log.flush()
            line = ANSI.sub("", raw)
            if status:
                start, end = line.find('{"ms":'), line.rfind("}")
                if start >= 0 and end > start:
                    return json.loads(line[start : end + 1])
            else:
                result = re.search(r"(?:^|\s)result=(-?\d+)", line)
                if result:
                    if int(result[1]):
                        raise RuntimeError(f"{command.split()[:3]} failed: {result[1]}")
                    return
        raise TimeoutError(f"No acknowledgement for {command.split()[:3]}")


def upload(args):
    samples = read_wave(args.wav)
    console = Console(args.port)
    try:
        console.command("stetho set source 0")
        console.command("stetho fixture reset")
        for offset in range(0, len(samples), 128):
            words = "".join(
                f"{int(s) & 0xFFFF:04x}" for s in samples[offset : offset + 128]
            )
            console.command("stetho fixture append " + words)
        console.command("stetho set source 3")
        print(json.dumps({"uploaded_frames": len(samples), "sha256": digest(args.wav)}))
    finally:
        console.close()


def record(args):
    args.output.mkdir(parents=True, exist_ok=True)
    metadata = provenance() | {
        "kind": "hardware-telemetry",
        "operator": args.operator,
        "wiring_revision": args.wiring_revision,
        "signal": args.signal,
        "firmware_sha256": digest(args.firmware),
        "firmware_path": str(args.firmware),
        "note": "Operator must confirm this supplied binary is the flashed image; telemetry is not acoustic proof.",
    }
    console = Console(args.port)
    raw_log = (args.output / "console.log").open("w")
    console.raw_log = raw_log
    try:
        (args.output / "manifest.json").write_text(
            json.dumps(metadata, indent=2) + "\n"
        )
        deadline = time.monotonic() + args.seconds
        with (args.output / "telemetry.jsonl").open("w") as stream:
            while time.monotonic() < deadline:
                sample = console.command("stetho status", status=True)
                stream.write(json.dumps(sample) + "\n")
                stream.flush()
                time.sleep(1)
    finally:
        console.close()
        raw_log.close()


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("FHIR readback redirects are refused")


def readback(args):
    if urlparse(args.url).scheme != "https":
        raise ValueError("HTTPS required")
    context = ssl.create_default_context(cafile=str(args.ca))
    headers = {"Accept": "application/fhir+json"}
    token = os.environ.get("STETHO_FHIR_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    request = Request(args.url, headers=headers)
    opener = build_opener(HTTPSHandler(context=context), NoRedirect())
    with opener.open(request, timeout=10) as response:
        resource = json.load(response)
    if resource.get("id") != urlparse(args.url).path.rstrip("/").split("/")[-1]:
        raise ValueError("Observation ID mismatch")
    if resource.get("status") != "final":
        raise ValueError("Observation is not final")
    if resource.get("resourceType") != "Observation":
        raise ValueError("Server did not return an Observation")
    if resource.get("subject", {}).get("reference") != "Patient/" + args.patient:
        raise ValueError("Patient reference mismatch")
    if not any(
        c.get("system") == "http://loinc.org" and c.get("code") == "8867-4"
        for c in resource.get("code", {}).get("coding", [])
    ):
        raise ValueError("Heart-rate LOINC missing")
    quantity = resource.get("valueQuantity", {})
    if (
        quantity.get("system") != "http://unitsofmeasure.org"
        or quantity.get("code") != "/min"
    ):
        raise ValueError("UCUM unit mismatch")
    if abs(float(quantity["value"]) - args.bpm) > 0.05:
        raise ValueError("BPM mismatch")
    if resource.get("effectiveDateTime") != args.timestamp:
        raise ValueError("Measurement timestamp mismatch")
    args.output.write_text(
        json.dumps(
            {"verdict": "PASS", "readback": resource, "url": args.url, **provenance()},
            indent=2,
        )
        + "\n"
    )
    print("FHIR server readback PASS")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(required=True)
    p = commands.add_parser("generate")
    p.add_argument("output", type=Path)
    p.add_argument("--kind", choices=["heart", "tone", "impulse"], default="heart")
    p.add_argument("--bpm", type=float, default=72)
    p.add_argument("--seconds", type=float, default=12)
    p.set_defaults(run=generate)
    p = commands.add_parser("evaluate")
    p.add_argument("wav", type=Path)
    p.add_argument("--reference-bpm", type=float, required=True)
    p.add_argument(
        "--reference", required=True, help="Reference source and synchronization method"
    )
    p.add_argument("--output", type=Path, required=True)
    p.add_argument(
        "--analysis-filter",
        choices=[*FILTERS, "matched"],
        default="bpm",
        help="Keep BPM analysis fixed while comparing listening filters (default: bpm); "
        "matched compares paired listening/analysis variants",
    )
    p.set_defaults(run=evaluate)
    p = commands.add_parser("upload")
    p.add_argument("wav", type=Path)
    p.add_argument("--port", required=True)
    p.set_defaults(run=upload)
    p = commands.add_parser("record")
    p.add_argument("--port", required=True)
    p.add_argument("--seconds", type=float, default=600)
    p.add_argument("--operator", required=True)
    p.add_argument("--wiring-revision", required=True)
    p.add_argument("--signal", required=True)
    p.add_argument("--firmware", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.set_defaults(run=record)
    p = commands.add_parser("readback")
    p.add_argument("url")
    p.add_argument("--ca", type=Path, required=True)
    p.add_argument("--patient", required=True)
    p.add_argument("--bpm", type=float, required=True)
    p.add_argument("--timestamp", required=True)
    p.add_argument("--output", type=Path, required=True)
    p.set_defaults(run=readback)
    args = parser.parse_args()
    if hasattr(args, "seconds") and args.seconds <= 0:
        parser.error("seconds must be positive")
    if hasattr(args, "bpm") and not 30 <= args.bpm <= 200:
        parser.error("bpm must be between 30 and 200")
    args.run(args)


if __name__ == "__main__":
    main()
