"""Device-like signal chain: block-wise single-precision filtering and the firmware output stage."""
import numba
import numpy

from .filters import FilterCandidate
from .recordings import SAMPLE_MAXIMUM, SAMPLE_MINIMUM

BLOCK_FRAMES = 64
FULL_SCALE = numpy.float32(8388608.0)
NORMALISATION_FACTOR = numpy.float32(1.0 / 8388608.0)
AUDIO_FULL_VOLUME_PERCENT = 100
AUDIO_GAIN_ONE = 65536
AUDIO_SAMPLE_STEP = 256


@numba.njit(cache=True)
def _sections_in_place(sections, state, block):
    # Transposed direct form II; every operand is float32, so numba keeps single precision.
    for index in range(block.shape[0]):
        value = block[index]
        for section_index in range(sections.shape[0]):
            b0 = sections[section_index, 0]
            b1 = sections[section_index, 1]
            b2 = sections[section_index, 2]
            a1 = sections[section_index, 4]
            a2 = sections[section_index, 5]
            output = b0 * value + state[section_index, 0]
            state[section_index, 0] = b1 * value - a1 * output + state[section_index, 1]
            state[section_index, 1] = b2 * value - a2 * output
            value = output
        block[index] = value


@numba.njit(cache=True)
def _fir_sample(taps, history, write_position):
    accumulator = numpy.float32(0.0)
    tap_count = taps.shape[0]
    position = write_position
    for tap_index in range(tap_count):
        accumulator += taps[tap_index] * history[position]
        position -= 1
        if position < 0:
            position = tap_count - 1
    return accumulator


@numba.njit(cache=True)
def _fir_in_place(taps, history, position_holder, block):
    tap_count = taps.shape[0]
    for index in range(block.shape[0]):
        position = position_holder[0] + 1
        if position >= tap_count:
            position = 0
        position_holder[0] = position
        history[position] = block[index]
        block[index] = _fir_sample(taps, history, position)


@numba.njit(cache=True)
def _stream_iir(sections, samples, block_frames, gain, apply_gain):
    state = numpy.zeros((sections.shape[0], 2), dtype=numpy.float32)
    output = samples.copy()
    for start in range(0, samples.shape[0], block_frames):
        block = output[start:start + block_frames]
        _sections_in_place(sections, state, block)
        if apply_gain:
            for index in range(block.shape[0]):
                block[index] = block[index] * gain
    return output


@numba.njit(cache=True)
def _stream_fir(taps, samples, block_frames, gain, apply_gain):
    history = numpy.zeros(taps.shape[0], dtype=numpy.float32)
    position_holder = numpy.zeros(1, dtype=numpy.int64)
    output = samples.copy()
    for start in range(0, samples.shape[0], block_frames):
        block = output[start:start + block_frames]
        _fir_in_place(taps, history, position_holder, block)
        if apply_gain:
            for index in range(block.shape[0]):
                block[index] = block[index] * gain
    return output


@numba.njit(cache=True)
def _stream_decimated(taps, sections, samples, block_frames, decimation_factor, gain, apply_gain):
    tap_count = taps.shape[0]
    history = numpy.zeros(tap_count, dtype=numpy.float32)
    state = numpy.zeros((sections.shape[0], 2), dtype=numpy.float32)
    output = numpy.zeros(samples.shape[0] // decimation_factor, dtype=numpy.float32)
    output_count = 0
    position = tap_count - 1
    phase = 0
    single = numpy.zeros(1, dtype=numpy.float32)
    for start in range(0, samples.shape[0], block_frames):
        stop = min(start + block_frames, samples.shape[0])
        for index in range(start, stop):
            position += 1
            if position >= tap_count:
                position = 0
            history[position] = samples[index]
            phase += 1
            if phase == decimation_factor:
                phase = 0
                single[0] = _fir_sample(taps, history, position)
                _sections_in_place(sections, state, single)
                value = single[0]
                if apply_gain:
                    value = value * gain
                output[output_count] = value
                output_count += 1
    return output


def normalise(samples_int24: numpy.ndarray) -> numpy.ndarray:
    return numpy.asarray(samples_int24).astype(numpy.float32) * NORMALISATION_FACTOR


def apply_filter_blockwise(candidate: FilterCandidate, samples_int24: numpy.ndarray, block_frames: int = BLOCK_FRAMES) -> numpy.ndarray:
    """Device-like streaming filter. Normalises once to float32 (value / 8388608.0), processes block by block
    with persistent state, single-precision arithmetic throughout (cascaded biquads in transposed direct form II;
    FIR as direct form), applies candidate.gain. Returns float32 in units of full scale (may exceed +-1.0).
    Decimated candidates return candidate.output_rate_hz samples per second."""
    samples = normalise(samples_int24)
    return apply_filter_to_normalised(candidate, samples, block_frames)


def apply_filter_to_normalised(candidate: FilterCandidate, samples: numpy.ndarray, block_frames: int = BLOCK_FRAMES) -> numpy.ndarray:
    samples = numpy.ascontiguousarray(samples, dtype=numpy.float32)
    gain = numpy.float32(candidate.gain)
    apply_gain = candidate.gain != 1.0
    if candidate.family == "raw":
        return samples * gain if apply_gain else samples.copy()
    if candidate.family == "decimated":
        return _stream_decimated(candidate.fir_coefficients, candidate.second_order_sections, samples, block_frames,
                                 candidate.decimation_factor, gain, apply_gain)
    if candidate.family == "fir":
        return _stream_fir(candidate.fir_coefficients, samples, block_frames, gain, apply_gain)
    return _stream_iir(candidate.second_order_sections, samples, block_frames, gain, apply_gain)


def float_to_int24(filtered_float32: numpy.ndarray) -> numpy.ndarray:
    """Output conversion: scale to 24-bit units in float32, saturate, round to nearest (lrintf)."""
    scaled = numpy.asarray(filtered_float32, dtype=numpy.float32) * FULL_SCALE
    scaled = numpy.clip(scaled, numpy.float32(SAMPLE_MINIMUM), numpy.float32(SAMPLE_MAXIMUM))
    return numpy.rint(scaled).astype(numpy.int32)


def _truncating_division(numerator: numpy.ndarray, denominator: int) -> numpy.ndarray:
    quotient = numpy.abs(numerator) // denominator
    return numpy.where(numerator < 0, -quotient, quotient)


def audio_apply_volume(left_aligned_samples: numpy.ndarray, volume_percent: int) -> numpy.ndarray:
    """Bit-exact port of audio_applyVolume (audio_processing.c) on left-aligned 32-bit words."""
    clamped_percent = min(int(volume_percent), AUDIO_FULL_VOLUME_PERCENT)
    gain = (clamped_percent * AUDIO_GAIN_ONE) // AUDIO_FULL_VOLUME_PERCENT
    value = _truncating_division(numpy.asarray(left_aligned_samples, dtype=numpy.int64), AUDIO_SAMPLE_STEP)
    scaled = _truncating_division(value * gain, AUDIO_GAIN_ONE)
    scaled = numpy.clip(scaled, SAMPLE_MINIMUM, SAMPLE_MAXIMUM)
    return (scaled * AUDIO_SAMPLE_STEP).astype(numpy.int32)


def volume_gain(volume_percent: int) -> numpy.float32:
    """The firmware's quantised volume gain (percent * 65536 / 100 in integers, as audio_applyVolume) as float32."""
    clamped_percent = min(max(int(volume_percent), 0), AUDIO_FULL_VOLUME_PERCENT)
    return numpy.float32(((clamped_percent * AUDIO_GAIN_ONE) // AUDIO_FULL_VOLUME_PERCENT) / AUDIO_GAIN_ONE)


def apply_volume_and_saturate(filtered_float32: numpy.ndarray, volume_percent: int = 100) -> numpy.ndarray:
    """Output stage in the order of the system design (shared-filter-signal-flow.puml: listening filter -> volume ->
    saturation at output conversion): float32 multiplication by the firmware's quantised volume gain, then one
    saturation to the 24-bit range with rounding (float_to_int24). At 100 % the gain is exactly 1.0, so the result
    equals the previous saturate-then-audio_applyVolume order bit for bit. Returns int32 24-bit values for the DAC."""
    gain = volume_gain(volume_percent)
    filtered = numpy.asarray(filtered_float32, dtype=numpy.float32)
    return float_to_int24(filtered if gain == 1.0 else filtered * gain)


def listening_path(candidate: FilterCandidate, samples_int24: numpy.ndarray, volume_percent: int = 100) -> numpy.ndarray:
    if candidate.decimation_factor != 1:
        raise ValueError("decimated candidates have no 16 kHz output for the DAC")
    return apply_volume_and_saturate(apply_filter_blockwise(candidate, samples_int24), volume_percent)


def count_clipped(samples_int24_or_output: numpy.ndarray) -> int:
    samples = numpy.asarray(samples_int24_or_output)
    if numpy.issubdtype(samples.dtype, numpy.floating):
        return int(numpy.count_nonzero((samples >= SAMPLE_MAXIMUM / 8388608.0) | (samples <= -1.0)))
    return int(numpy.count_nonzero((samples >= SAMPLE_MAXIMUM) | (samples <= SAMPLE_MINIMUM)))
