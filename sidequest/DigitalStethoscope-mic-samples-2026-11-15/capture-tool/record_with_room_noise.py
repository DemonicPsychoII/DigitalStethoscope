# /// script
# requires-python = ">=3.11"
# dependencies = ["pyserial>=3.5", "numpy>=2", "sounddevice>=0.5", "matplotlib>=3.9"]
# ///
"""Play the same pink noise on the PC's default audio output and record one clip while it plays.

Usage: record_with_room_noise.py test            plays 3 s of the noise, records nothing
       record_with_room_noise.py <clip name>     plays the noise and records one 15 s clip, started from the PC
"""
import subprocess
import sys
import time
import wave
import winsound
from pathlib import Path

import numpy

RATE_HZ = 48000
SECONDS = 22
LEAD_SECONDS = 2
LEVEL = 0.25
NOISE_FILE = Path(__file__).with_name("room-noise-pink-48kHz.wav")


def write_noise(seconds: float, path: Path) -> None:
    # A fixed seed gives the same noise for every clip.
    white = numpy.random.default_rng(20261116).standard_normal(int(seconds * RATE_HZ))
    spectrum = numpy.fft.rfft(white)
    frequencies = numpy.fft.rfftfreq(len(white), 1 / RATE_HZ)
    shaping = numpy.zeros_like(frequencies)
    audible = (frequencies >= 50) & (frequencies <= 8000)
    shaping[audible] = 1 / numpy.sqrt(frequencies[audible])
    pink = numpy.fft.irfft(spectrum * shaping, len(white))
    pink *= LEVEL / pink.std() / 4
    fade = int(0.05 * RATE_HZ)
    pink[:fade] *= numpy.linspace(0, 1, fade)
    pink[-fade:] *= numpy.linspace(1, 0, fade)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(RATE_HZ)
        output.writeframes((numpy.clip(pink, -1, 1) * 32767).astype("<i2").tobytes())


if sys.argv[1] == "test":
    test_file = NOISE_FILE.with_name("room-noise-test.wav")
    write_noise(3, test_file)
    winsound.PlaySound(str(test_file), winsound.SND_FILENAME)
else:
    if not NOISE_FILE.exists():
        write_noise(SECONDS, NOISE_FILE)
    winsound.PlaySound(str(NOISE_FILE), winsound.SND_FILENAME | winsound.SND_ASYNC)
    time.sleep(LEAD_SECONDS)
    result = subprocess.run(["uv", "run", str(Path(__file__).with_name("capture.py")), "record", "--name", sys.argv[1]],
                            cwd=Path(__file__).parent)
    winsound.PlaySound(None, winsound.SND_PURGE)
    sys.exit(result.returncode)
