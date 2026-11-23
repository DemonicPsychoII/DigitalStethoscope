# /// script
# requires-python = ">=3.11"
# dependencies = ["pyserial>=3.5", "numpy>=2", "sounddevice>=0.5", "matplotlib>=3.9"]
# ///
"""Receive microphone audio from the mic-capture firmware over the UART bridge.

record: 15 s clips from PSRAM -> raw 24-bit WAV, listening WAV, waveform/spectrum PNG each.
stream: live audio to the PC speakers/headphones, also saved as raw 24-bit WAV.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime
import queue
import struct
import sys
import time
import wave
import zlib
from pathlib import Path

import numpy
import serial

BAUD_RATE = 921600
SAMPLE_RATE_HZ = 16000
BYTES_PER_SAMPLE = 3
FULL_SCALE = 2**23
MAGIC = b"STHA"
HEADER = struct.Struct("<4sBBHII")
CHECKSUM_BYTES = 4
MAXIMUM_SAMPLES_PER_FRAME = 128
FRAME_KIND_STREAM = 1
FRAME_KIND_RECORDING = 2
FRAME_KIND_RECORDING_END = 3
FRAME_FLAG_RECEIVE_ERROR = 0x01
# Same one-pole DC blocker as the carrier-bringup passthrough, about 20 Hz at 16 kHz.
DC_BLOCKER_POLE = 0.992
START_SKIP_SAMPLES = SAMPLE_RATE_HZ // 2


class FrameParser:
    def __init__(self) -> None:
        self.buffer = bytearray()
        self.text = bytearray()
        self.checksum_errors = 0

    def feed(self, data: bytes):
        self.buffer += data
        while True:
            start = self.buffer.find(MAGIC)
            if start < 0:
                keep = len(MAGIC) - 1
                self._text(self.buffer[:-keep] if len(self.buffer) > keep else b"")
                del self.buffer[: max(0, len(self.buffer) - keep)]
                return
            self._text(self.buffer[:start])
            del self.buffer[:start]
            if len(self.buffer) < HEADER.size:
                return
            _, kind, flags, count, sequence, first = HEADER.unpack_from(self.buffer)
            if kind not in (FRAME_KIND_STREAM, FRAME_KIND_RECORDING, FRAME_KIND_RECORDING_END) or (
                count > MAXIMUM_SAMPLES_PER_FRAME
            ):
                del self.buffer[:1]
                continue
            end = HEADER.size + count * BYTES_PER_SAMPLE
            if len(self.buffer) < end + CHECKSUM_BYTES:
                return
            (checksum,) = struct.unpack_from("<I", self.buffer, end)
            if zlib.crc32(self.buffer[:end]) != checksum:
                self.checksum_errors += 1
                del self.buffer[:1]
                continue
            payload = bytes(self.buffer[HEADER.size : end])
            del self.buffer[: end + CHECKSUM_BYTES]
            yield kind, flags, sequence, first, payload

    def _text(self, data: bytes) -> None:
        self.text += data
        while b"\n" in self.text:
            line, _, rest = self.text.partition(b"\n")
            self.text = bytearray(rest)
            line = line.strip()
            # Bytes skipped while resynchronising are not device text.
            if len(line) >= 3 and all(0x20 <= byte < 0x7F for byte in line):
                print(f"[device] {line.decode('ascii')}", file=sys.stderr)
        if len(self.text) > 4096:
            self.text.clear()


def open_device(port: str) -> serial.Serial:
    connection = serial.Serial()
    connection.port = port
    connection.baudrate = BAUD_RATE
    connection.timeout = 0.05
    # The DevKitC auto-reset circuit holds the chip in reset or download mode otherwise.
    connection.dtr = False
    connection.rts = False
    connection.open()
    if hasattr(connection, "set_buffer_size"):
        connection.set_buffer_size(rx_size=1 << 20)
    deadline = time.monotonic() + 8
    reply = bytearray()
    while time.monotonic() < deadline:
        connection.write(b"x?")
        until = time.monotonic() + 0.5
        while time.monotonic() < until:
            reply += connection.read(4096)
        line = next((entry for entry in reply.split(b"\n") if b"mic-capture ready=1" in entry), None)
        if line is not None:
            print(f"[device] {line.decode('ascii', 'ignore').strip()}", file=sys.stderr)
            connection.reset_input_buffer()
            return connection
        reply = reply[-512:]
    connection.close()
    raise SystemExit(f"No ready mic-capture firmware on {port} at {BAUD_RATE} baud.")


def decode_samples(payload: bytes) -> numpy.ndarray:
    raw = numpy.frombuffer(payload, dtype=numpy.uint8).reshape(-1, BYTES_PER_SAMPLE).astype(numpy.int32)
    values = raw[:, 0] | (raw[:, 1] << 8) | (raw[:, 2] << 16)
    return (values ^ 0x800000) - 0x800000


def remove_dc(samples: numpy.ndarray, state: tuple[float, float] = (0.0, 0.0)):
    previous_input, previous_output = state
    output = numpy.empty(len(samples), dtype=numpy.float64)
    for index, value in enumerate(samples.astype(numpy.float64)):
        previous_output = value - previous_input + DC_BLOCKER_POLE * previous_output
        previous_input = value
        output[index] = previous_output
    return output, (previous_input, previous_output)


def decibels_full_scale(value: float) -> float:
    return 20 * numpy.log10(max(value, 1e-12) / FULL_SCALE)


def write_wav(path: Path, payload: bytes, sample_width: int) -> None:
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(sample_width)
        output.setframerate(SAMPLE_RATE_HZ)
        output.writeframes(payload)


def write_plot(path: Path, samples: numpy.ndarray, title: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot

    time_axis = numpy.arange(len(samples)) / SAMPLE_RATE_HZ
    figure, (waveform_axis, spectrogram_axis, spectrum_axis) = pyplot.subplots(
        3, 1, figsize=(11, 10), constrained_layout=True
    )
    figure.suptitle(title)
    waveform_axis.plot(time_axis, samples / FULL_SCALE, linewidth=0.4)
    waveform_axis.set(xlabel="Time (s)", ylabel="Amplitude (FS)", title="Waveform, DC removed")
    waveform_axis.grid(alpha=0.3)
    spectrogram_axis.specgram(samples / FULL_SCALE, NFFT=1024, Fs=SAMPLE_RATE_HZ, noverlap=768, cmap="magma")
    spectrogram_axis.set(xlabel="Time (s)", ylabel="Frequency (Hz)", title="Spectrogram")
    segment = 4096
    window = numpy.hanning(segment)
    segments = [
        samples[start : start + segment] * window
        for start in range(0, len(samples) - segment + 1, segment // 2)
    ]
    power = numpy.mean([numpy.abs(numpy.fft.rfft(part)) ** 2 for part in segments], axis=0)
    frequencies = numpy.fft.rfftfreq(segment, 1 / SAMPLE_RATE_HZ)
    amplitude = numpy.sqrt(power) * 2 / numpy.sum(window)
    spectrum_axis.semilogx(frequencies[1:], 20 * numpy.log10(amplitude[1:] / FULL_SCALE + 1e-12), linewidth=0.7)
    spectrum_axis.set(xlabel="Frequency (Hz)", ylabel="Level (dBFS)", title="Average spectrum (Welch, Hann 4096)")
    spectrum_axis.set_xlim(10, SAMPLE_RATE_HZ / 2)
    spectrum_axis.grid(alpha=0.3, which="both")
    figure.savefig(path, dpi=120)
    pyplot.close(figure)


def record(arguments: argparse.Namespace) -> None:
    names = arguments.name or [datetime.datetime.now().strftime("%Y%m%d-%H%M%S")]
    connection = open_device(arguments.port)
    parser = FrameParser()
    if arguments.button:
        print(
            "The first press of the carrier button turns the headphones on, "
            f"each of the next {len(names)} records one clip (LED lights until the clip has reached the PC)."
        )
    else:
        connection.write(b"lr" if arguments.listen else b"r")
        print("Recording (LED lights while recording) ...")
    # The firmware sends the clips one after the other, so frames of two clips never mix.
    pending = parser.feed(b"")
    for stem in names:
        chunks: dict[int, bytes] = {}
        receive_error = False
        total_samples = None
        deadline = None if arguments.button else time.monotonic() + 40
        while total_samples is None:
            if deadline is not None and time.monotonic() > deadline:
                raise SystemExit(f"Timed out; received {len(chunks)} frames of {stem}.")
            frame = next(pending, None)
            if frame is None:
                pending = parser.feed(connection.read(65536))
                continue
            kind, flags, _, first, payload = frame
            receive_error |= bool(flags & FRAME_FLAG_RECEIVE_ERROR)
            if kind == FRAME_KIND_RECORDING:
                if not chunks:
                    print(f"Receiving {stem} ...")
                    if deadline is None:
                        deadline = time.monotonic() + 30
                chunks[first] = payload
            elif kind == FRAME_KIND_RECORDING_END:
                total_samples = first
        save_recording(arguments, parser, stem, chunks, total_samples, receive_error)
    connection.close()


def save_recording(
    arguments: argparse.Namespace,
    parser: FrameParser,
    stem: str,
    chunks: dict[int, bytes],
    total_samples: int,
    receive_error: bool,
) -> None:

    # Lost frames stay silent gaps so the timing of the clip is preserved.
    clip = bytearray(total_samples * BYTES_PER_SAMPLE)
    for first, chunk in chunks.items():
        clip[first * BYTES_PER_SAMPLE : first * BYTES_PER_SAMPLE + len(chunk)] = chunk
    payload = bytes(clip)
    received_samples = sum(len(chunk) for chunk in chunks.values()) // BYTES_PER_SAMPLE
    if received_samples != total_samples:
        print(f"WARNING: received {received_samples} of {total_samples} samples; gaps are zero.")
    received_samples = total_samples
    if receive_error:
        print("WARNING: the firmware saw an I2S receive error during this recording.")
    if parser.checksum_errors:
        print(f"WARNING: {parser.checksum_errors} frames failed the CRC and were dropped so far.")

    samples = decode_samples(payload)
    filtered, _ = remove_dc(samples)
    # The DC blocker settles within about 0.1 s and the button press clicks; keep both out.
    settled = filtered[START_SKIP_SAMPLES :]
    peak = numpy.max(numpy.abs(settled))
    root_mean_square = numpy.sqrt(numpy.mean(settled**2))
    print(
        f"{received_samples} samples, {received_samples / SAMPLE_RATE_HZ:.2f} s at {SAMPLE_RATE_HZ} Hz, 24 bit\n"
        f"DC offset {numpy.mean(samples):.0f} LSB ({decibels_full_scale(abs(numpy.mean(samples))):.1f} dBFS), "
        f"AC peak {decibels_full_scale(peak):.1f} dBFS, AC RMS {decibels_full_scale(root_mean_square):.1f} dBFS"
    )

    output_directory = Path(arguments.output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    raw_path = output_directory / f"{stem}-raw.wav"
    listening_path = output_directory / f"{stem}-listen.wav"
    plot_path = output_directory / f"{stem}.png"
    write_wav(raw_path, payload, BYTES_PER_SAMPLE)
    # Peak normalisation to -1 dBFS also raises the noise floor; the raw file stays untouched.
    normalised = settled * (10 ** (-1 / 20) / (peak / FULL_SCALE)) / FULL_SCALE if peak > 0 else settled
    listening = numpy.clip(numpy.concatenate([numpy.zeros(START_SKIP_SAMPLES), normalised]), -1, 1)
    write_wav(listening_path, (listening * 32767).astype("<i2").tobytes(), 2)
    write_plot(plot_path, settled, f"INMP441 on Eval carrier, {stem}")
    print(f"Raw:       {raw_path.resolve()}\nListening: {listening_path.resolve()}\nPlot:      {plot_path.resolve()}")

    if arguments.play:
        import winsound

        print("Playing the listening file ...")
        winsound.PlaySound(str(listening_path), winsound.SND_FILENAME)


def stream(arguments: argparse.Namespace) -> None:
    import sounddevice

    connection = open_device(arguments.port)
    parser = FrameParser()
    output_directory = Path(arguments.output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    raw_path = output_directory / f"{datetime.datetime.now():%Y%m%d-%H%M%S}-stream-raw.wav"
    playback: queue.Queue[numpy.ndarray] = queue.Queue()
    pending = numpy.zeros(0, dtype=numpy.float32)

    def fill(output, frame_count, _time, _status):
        nonlocal pending
        while len(pending) < frame_count and not playback.empty():
            pending = numpy.concatenate([pending, playback.get_nowait()])
        available = min(len(pending), frame_count)
        output[:available, 0] = pending[:available]
        output[available:, 0] = 0
        pending = pending[available:]

    filter_state = (0.0, 0.0)
    next_sample = None
    missing_samples = 0
    peak = 0.0
    next_report = time.monotonic() + 1
    deadline = time.monotonic() + arguments.seconds if arguments.seconds else None
    gain = arguments.gain
    playing = gain != 0
    audio_output = (
        sounddevice.OutputStream(
            samplerate=SAMPLE_RATE_HZ, channels=1, dtype="float32", latency="high", callback=fill
        )
        if playing
        else contextlib.nullcontext()
    )
    with audio_output, wave.open(str(raw_path), "wb") as raw_file:
        raw_file.setnchannels(1)
        raw_file.setsampwidth(BYTES_PER_SAMPLE)
        raw_file.setframerate(SAMPLE_RATE_HZ)
        # A short jitter buffer before the first block.
        playback.put(numpy.zeros(SAMPLE_RATE_HZ // 5, dtype=numpy.float32))
        connection.write(b"s")
        print(f"Streaming live at gain x{gain}; Ctrl+C stops. Saving {raw_path.resolve()}")
        try:
            while deadline is None or time.monotonic() < deadline:
                for kind, _, _, first, payload in parser.feed(connection.read(16384)):
                    if kind != FRAME_KIND_STREAM:
                        continue
                    if next_sample is not None and first > next_sample:
                        gap = first - next_sample
                        missing_samples += gap
                        raw_file.writeframes(bytes(gap * BYTES_PER_SAMPLE))
                        playback.put(numpy.zeros(gap, dtype=numpy.float32))
                    samples = decode_samples(payload)
                    next_sample = first + len(samples)
                    raw_file.writeframes(payload)
                    filtered, filter_state = remove_dc(samples, filter_state)
                    peak = max(peak, float(numpy.max(numpy.abs(filtered))))
                    playback.put(numpy.clip(filtered * gain / FULL_SCALE, -1, 1).astype(numpy.float32))
                if time.monotonic() >= next_report:
                    next_report += 1
                    bar = "#" * int(max(0, decibels_full_scale(peak) + 90) / 3)
                    print(
                        f"\rpeak {decibels_full_scale(peak):6.1f} dBFS {bar:<30} missing {missing_samples} "
                        f"crc {parser.checksum_errors} queued {playback.qsize()}",
                        end="",
                        flush=True,
                    )
                    peak = 0.0
        except KeyboardInterrupt:
            pass
        finally:
            connection.write(b"x")
            connection.close()
            print()
    print(f"Saved {raw_path.resolve()}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", default="COM4")
    parser.add_argument("--output-directory", default="recordings")
    commands = parser.add_subparsers(dest="command", required=True)
    record_parser = commands.add_parser("record", help="15 s clip from PSRAM")
    record_parser.add_argument("--button", action="store_true", help="wait for the carrier button instead")
    record_parser.add_argument("--play", action="store_true", help="play the listening file afterwards")
    record_parser.add_argument("--listen", action="store_true", help="turn the headphones on, without --button")
    record_parser.add_argument("--name", nargs="+", help="one file name stem per clip, default: one timestamp")
    stream_parser = commands.add_parser("stream", help="live audio to the PC")
    stream_parser.add_argument("--gain", type=float, default=16, help="linear gain, default 16 as passthrough")
    stream_parser.add_argument("--seconds", type=float, default=0, help="stop after this many seconds")
    arguments = parser.parse_args()
    {"record": record, "stream": stream}[arguments.command](arguments)


if __name__ == "__main__":
    main()
