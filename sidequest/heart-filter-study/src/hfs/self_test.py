"""Self-test of the device-chain library. Run: python -m hfs.self_test (with src on the path)."""
import sys

import numpy
from scipy import signal

from . import device_chain, filters
from .recordings import RECORDING_NAMES, SAMPLE_MAXIMUM, SAMPLE_MINIMUM, load_recording


def c_division(numerator: int, denominator: int) -> int:
    quotient = abs(numerator) // abs(denominator)
    return -quotient if (numerator < 0) != (denominator < 0) else quotient


def audio_apply_volume_transcription(samples, volume_percent):
    """Line-by-line transcription of audio_applyVolume in plain Python integers."""
    clamped_percent = 100 if volume_percent > 100 else volume_percent
    gain = c_division(clamped_percent * 65536, 100)
    result = []
    for sample in samples:
        value = c_division(int(sample), 256)
        scaled = c_division(value * gain, 65536)
        if scaled > 8388607:
            scaled = 8388607
        elif scaled < -8388608:
            scaled = -8388608
        result.append(scaled * 256)
    return numpy.array(result, dtype=numpy.int64)


def previous_saturate_then_volume(filtered_float32, volume_percent):
    """Run-1 output stage kept for comparison: saturate at conversion, then audio_applyVolume."""
    left_aligned = device_chain.float_to_int24(filtered_float32).astype(numpy.int64) * 256
    return (device_chain.audio_apply_volume(left_aligned, volume_percent) // 256).astype(numpy.int32)


def deviation_candidates():
    candidates = []
    for family in ("butterworth", "bessel", "chebyshev1", "chebyshev2", "elliptic"):
        for highpass_order, lowpass_order in ((1, 1), (2, 2), (4, 4), (2, 4), (4, 2)):
            candidates.append(filters.design_filter(family, 25, 150, highpass_order, lowpass_order))
        candidates.append(filters.design_filter(family, 20, 150, 4, 2))
        candidates.append(filters.design_filter(family, 10, 150, 4, 2))
        candidates.append(filters.design_filter(family, 40, 800, 2, 2))
    candidates.append(filters.design_filter("fir", 25, 150, fir_tap_count=257))
    candidates.append(filters.design_filter("decimated", 25, 150, 2, 2))
    return candidates


def main() -> int:
    failures = []
    samples = load_recording("elevated-2")[:16000 * 20]
    normalised = device_chain.normalise(samples)

    print("1. Block-wise (64 frames) equals sample-wise streaming (block of 1), bit-exact")
    for candidate in (filters.design_filter("butterworth", 25, 150), filters.design_filter("fir", 40, 800, fir_tap_count=65),
                      filters.design_filter("decimated", 25, 150), filters.design_filter("elliptic", 20, 800, 4, 4)):
        block_output = device_chain.apply_filter_blockwise(candidate, samples, 64)
        sample_output = device_chain.apply_filter_blockwise(candidate, samples, 1)
        odd_output = device_chain.apply_filter_blockwise(candidate, samples, 37)
        equal = numpy.array_equal(block_output, sample_output) and numpy.array_equal(block_output, odd_output)
        print(f"   {candidate.identifier:40s} {'equal' if equal else 'DIFFERENT'}  dtype {block_output.dtype}")
        if not equal or block_output.dtype != numpy.float32:
            failures.append(f"block-wise {candidate.identifier}")

    print("2. float32 device filter versus float64 scipy.signal.sosfilt (same float32 coefficients), 20 s of elevated-2")
    print(f"   {'candidate':44s} {'worst abs dev (FS)':>18s} {'output RMS (FS)':>16s} {'relative dev (dB re RMS)':>25s}  flag")
    deviation_rows = []
    for candidate in deviation_candidates():
        device_output = device_chain.apply_filter_blockwise(candidate, samples)
        if candidate.family == "fir":
            exact = signal.lfilter(candidate.fir_coefficients.astype(numpy.float64), [1.0], normalised.astype(numpy.float64))
        elif candidate.family == "decimated":
            stage = signal.lfilter(candidate.fir_coefficients.astype(numpy.float64), [1.0], normalised.astype(numpy.float64))
            stage = stage[candidate.decimation_factor - 1::candidate.decimation_factor][:len(device_output)]
            exact = signal.sosfilt(candidate.second_order_sections.astype(numpy.float64), stage)
        else:
            exact = signal.sosfilt(candidate.second_order_sections.astype(numpy.float64), normalised.astype(numpy.float64))
        worst = float(numpy.max(numpy.abs(device_output - exact)))
        rms = float(numpy.sqrt(numpy.mean(exact ** 2)))
        relative_db = 20 * numpy.log10(max(worst, 1e-30) / rms)
        flag = "UNUSABLE" if relative_db > -40 else ("marginal" if relative_db > -60 else "")
        deviation_rows.append((candidate.identifier, worst, rms, relative_db, flag))
        print(f"   {candidate.identifier:44s} {worst:18.3e} {rms:16.3e} {relative_db:25.1f}  {flag}")

    print("3. scipy.signal.sosfilt on float32 input versus the numba float32 kernel")
    candidate = filters.design_filter("butterworth", 25, 150, 4, 4)
    scipy_float32 = signal.sosfilt(candidate.second_order_sections, normalised)
    device_output = device_chain.apply_filter_blockwise(candidate, samples)
    print(f"   scipy output dtype {scipy_float32.dtype}, bit-exact with numba kernel: {numpy.array_equal(scipy_float32, device_output)},"
          f" worst difference {float(numpy.max(numpy.abs(scipy_float32.astype(numpy.float64) - device_output))):.3e}")

    print("4. Volume stage port versus direct transcription of audio_applyVolume")
    generator = numpy.random.default_rng(1)
    random_samples = generator.integers(SAMPLE_MINIMUM, SAMPLE_MAXIMUM + 1, 20000, dtype=numpy.int64)
    random_samples = numpy.concatenate([random_samples, [SAMPLE_MINIMUM, SAMPLE_MAXIMUM, 0, 1, -1, 255, -255, 100, -100]])
    left_aligned = random_samples * 256
    for volume in (0, 1, 50, 99, 100, 150):
        port = device_chain.audio_apply_volume(left_aligned, volume).astype(numpy.int64)
        transcription = audio_apply_volume_transcription(left_aligned, volume)
        equal = numpy.array_equal(port, transcription)
        print(f"   volume {volume:3d} %: {'bit-exact' if equal else 'DIFFERENT'}")
        if not equal:
            failures.append(f"volume {volume}")

    print("5. Saturation at both 24-bit limits")
    test_values = numpy.array([2.0, 1.0, 0.9999999, -1.0, -1.5, 0.5, -0.5], dtype=numpy.float32)
    converted = device_chain.apply_volume_and_saturate(test_values, 100)
    expected = numpy.array([SAMPLE_MAXIMUM, SAMPLE_MAXIMUM, SAMPLE_MAXIMUM, SAMPLE_MINIMUM, SAMPLE_MINIMUM, 4194304, -4194304])
    print(f"   inputs {test_values.tolist()} -> {converted.tolist()}; clipped count {device_chain.count_clipped(converted)}")
    if not numpy.array_equal(converted, expected):
        failures.append("saturation")
    half_volume = device_chain.apply_volume_and_saturate(test_values, 50)
    print(f"   at 50 %: {half_volume.tolist()}")

    print("6. Recordings load as 24-bit int32 after discarding 2 s")
    for name in RECORDING_NAMES:
        recording = load_recording(name)
        print(f"   {name:11s} {recording.shape[0]} samples, range {recording.min()}..{recording.max()},"
              f" clipped {device_chain.count_clipped(recording)}")

    print("7. Output stage order: volume, then one saturation (design) versus saturation, then audio_applyVolume (run 1)")
    boosted = filters.design_filter("butterworth", 40, 800, 2, 2)
    boosted = type(boosted)(**{**boosted.__dict__, "gain": 2.0})
    for name in RECORDING_NAMES:
        filtered = device_chain.apply_filter_blockwise(boosted, load_recording(name))
        for volume in (100, 150, 50, 25):
            previous_order = previous_saturate_then_volume(filtered, volume)
            design_order = device_chain.apply_volume_and_saturate(filtered, volume)
            differing = int(numpy.count_nonzero(previous_order != design_order))
            beyond_rounding = int(numpy.count_nonzero(numpy.abs(previous_order.astype(numpy.int64) - design_order) > 1))
            line = (f"   {name:11s} volume {volume:3d} %: differing {differing:6d}, by more than 1 LSB {beyond_rounding:5d}, at a limit"
                    f" {device_chain.count_clipped(previous_order):6d} -> {device_chain.count_clipped(design_order):6d},"
                    f" largest |value| {int(numpy.abs(previous_order).max()):8d} -> {int(numpy.abs(design_order).max()):8d}")
            print(line)
            if volume >= 100 and differing:
                failures.append(f"output order at {volume} % {name}")
            expected = numpy.clip(numpy.rint(filtered * device_chain.FULL_SCALE * device_chain.volume_gain(volume)),
                                  SAMPLE_MINIMUM, SAMPLE_MAXIMUM)
            if numpy.max(numpy.abs(expected - design_order)) > 1:
                failures.append(f"design order reference {volume} % {name}")

    if failures:
        print("FAILED:", ", ".join(failures))
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
