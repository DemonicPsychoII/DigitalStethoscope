# /// script
# requires-python = ">=3.11"
# dependencies = ["pyserial>=3.5"]
# ///
"""Record the application's UART log with PC timestamps for a number of minutes.

Usage: log_device.py <minutes> [--port COM4] [--output-directory .]
Turns on the debug log of the audio and I2S modules first, so the block timing report appears every second while
audio runs. Press the Start/Stop button to start audio; Ctrl+C ends early.
"""
import argparse
import datetime
import time
from pathlib import Path

import serial

ENABLE_DEBUG_LOG = b"\rlog enable dbg audio i2s\r"
FAULT_WORDS = ("<err>", "<wrn>", "fail", "fault", "no free", "still in use")

parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
parser.add_argument("minutes", type=float)
parser.add_argument("--port", default="COM4")
parser.add_argument("--baud", type=int, default=115200)
parser.add_argument("--output-directory", type=Path, default=Path("."))
arguments = parser.parse_args()

started = datetime.datetime.now()
log_path = arguments.output_directory / f"device-log-{started:%Y-%m-%d-%H%M%S}.txt"
end = time.monotonic() + arguments.minutes * 60
faults = []
with serial.Serial(arguments.port, arguments.baud, timeout=0.2) as connection, log_path.open("w", encoding="utf-8") as log:
    connection.write(ENABLE_DEBUG_LOG)
    print(f"Logging {arguments.port} for {arguments.minutes:g} min into {log_path} (Ctrl+C ends early)")
    pending = b""
    try:
        while time.monotonic() < end:
            pending += connection.read(4096)
            *lines, pending = pending.split(b"\n")
            for raw_line in lines:
                text = raw_line.decode("utf-8", "replace").rstrip("\r")
                line = f"{datetime.datetime.now():%H:%M:%S.%f}"[:-3] + "  " + text
                log.write(line + "\n")
                print(line)
                if any(word in text.lower() for word in FAULT_WORDS):
                    faults.append(line)
            log.flush()
    except KeyboardInterrupt:
        pass
print(f"\nDone after {(datetime.datetime.now() - started).total_seconds() / 60:.1f} min: {log_path}")
print(f"{len(faults)} error or warning lines" + (":" if faults else "."))
for line in faults:
    print("  " + line)
