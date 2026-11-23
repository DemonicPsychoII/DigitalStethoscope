"""Whole-window (non-causal) BPM estimators for the buffered 8 s analysis window.

Every method has the signature estimate(window_normalised_float, sample_rate_hz) -> WindowEstimate and sees
only the samples of the current window. Two groups:

- Zero-phase family: Butterworth sections run forward, reversed, forward again (as scipy.signal.sosfiltfilt),
  in float32 with the transposed direct form II of run 1, so the code ports line by line to C. Then run 1's
  envelope (absolute value, low-pass, 100 values per second) and run 1's autocorrelation with half-rate check.
- Springer family: a port of the heart-rate estimate and the envelope features of the PhysioNet reference code
  "Logistic Regression-HSMM-based Heart Sound Segmentation" 1.0 (files and lines in sources/springer-method-notes.md).
  This group uses float64 SciPy routines: it measures the method, not a device implementation.
"""
from dataclasses import dataclass, field, replace

import numba
import numpy
from scipy import optimize, signal

from .bpm_estimator import BPMEstimator, EstimatorConfiguration, _normalised_autocorrelation
from .device_chain import _sections_in_place

FINAL_ESTIMATOR = EstimatorConfiguration(envelope_lowpass="two_pole", envelope_lowpass_hz=5.0, peak_choice="half_check")
ENVELOPE_RATE_HZ = 100
WINDOW_SECONDS = 8.0
HALF_POWER = 0.5


@dataclass
class WindowEstimate:
    bpm: float
    quality: float
    valid: bool
    details: dict = field(default_factory=dict)


# Building blocks shared by the zero-phase family ---------------------------------------------------------------

def butterworth_sections(highpass_hz, lowpass_hz, order, sample_rate_hz) -> numpy.ndarray:
    sections = []
    if highpass_hz is not None:
        sections.append(signal.butter(order, highpass_hz, "highpass", fs=sample_rate_hz, output="sos"))
    if lowpass_hz is not None:
        sections.append(signal.butter(order, lowpass_hz, "lowpass", fs=sample_rate_hz, output="sos"))
    return numpy.vstack(sections)


def _squared_magnitude(sections, frequency_hz, sample_rate_hz):
    _, response = signal.sosfreqz(sections, worN=[frequency_hz], fs=sample_rate_hz)
    return float(abs(response[0]) ** 2)


def edges_for_half_power_after_two_passes(highpass_hz, lowpass_hz, order, sample_rate_hz):
    """Edges whose two-pass response (squared magnitude) is -3 dB at the requested frequencies, solved per edge."""
    matched_highpass = None
    matched_lowpass = None
    if highpass_hz is not None:
        def highpass_mismatch(edge):
            sections = signal.butter(order, edge, "highpass", fs=sample_rate_hz, output="sos")
            return _squared_magnitude(sections, highpass_hz, sample_rate_hz) - numpy.sqrt(HALF_POWER)
        matched_highpass = optimize.brentq(highpass_mismatch, 0.2 * highpass_hz, highpass_hz)
    if lowpass_hz is not None:
        def lowpass_mismatch(edge):
            sections = signal.butter(order, edge, "lowpass", fs=sample_rate_hz, output="sos")
            return _squared_magnitude(sections, lowpass_hz, sample_rate_hz) - numpy.sqrt(HALF_POWER)
        matched_lowpass = optimize.brentq(lowpass_mismatch, lowpass_hz, min(4.0 * lowpass_hz, 0.49 * sample_rate_hz))
    return matched_highpass, matched_lowpass


def default_padding_length(sections) -> int:
    # Same rule as scipy.signal.sosfiltfilt (padtype "odd", padlen default).
    trailing_zero_count = min(int((sections[:, 2] == 0).sum()), int((sections[:, 5] == 0).sum()))
    return 3 * (2 * len(sections) + 1 - trailing_zero_count)


def run_sections(sections_float32, values, initial_state):
    output = numpy.ascontiguousarray(values, dtype=numpy.float32).copy()
    state = numpy.ascontiguousarray(initial_state, dtype=numpy.float32).copy()
    _sections_in_place(sections_float32, state, output)
    return output


def two_pass_filter(sections, values, pass_mode, edge_mode):
    """pass_mode "forward_backward" (zero phase), "forward_twice" (same magnitude, doubled phase), "forward_once", or
    "backward_only" (input already filtered forward by the streaming causal filter; together zero phase);
    edge_mode "reflect" (odd reflection and steady-state start as filtfilt) or "none" (zero start, no padding)."""
    sections_float32 = numpy.ascontiguousarray(sections, dtype=numpy.float32)
    values = numpy.ascontiguousarray(values, dtype=numpy.float32)
    padding = 0
    steady_state = numpy.zeros((len(sections), 2), dtype=numpy.float32)
    extended = values
    if edge_mode == "reflect":
        padding = min(default_padding_length(sections), values.shape[0] - 1)
        first = values[0]
        last = values[-1]
        extended = numpy.concatenate((2 * first - values[padding:0:-1], values, 2 * last - values[-2:-padding - 2:-1]))
        steady_state = signal.sosfilt_zi(sections).astype(numpy.float32)
    forward = run_sections(sections_float32, extended, steady_state * extended[0])
    if pass_mode == "forward_backward":
        backward_input = forward[::-1]
        second = run_sections(sections_float32, backward_input, steady_state * backward_input[0])[::-1]
    elif pass_mode == "forward_twice":
        second = run_sections(sections_float32, forward, steady_state * forward[0])
    elif pass_mode == "forward_once":
        second = forward
    elif pass_mode == "backward_only":
        backward_input = numpy.ascontiguousarray(extended[::-1])
        second = run_sections(sections_float32, backward_input, steady_state * backward_input[0])[::-1]
    else:
        raise ValueError(pass_mode)
    if padding:
        second = second[padding:-padding]
    return numpy.ascontiguousarray(second, dtype=numpy.float32)


@numba.njit(cache=True)
def _one_pole(values, coefficient, initial, output):
    state = initial
    for index in range(values.shape[0]):
        state += coefficient * (values[index] - state)
        output[index] = state


def one_pole_coefficient(cutoff_hz, sample_rate_hz):
    return numpy.float32(1.0 - numpy.exp(-2.0 * numpy.pi * cutoff_hz / sample_rate_hz))


def envelope(filtered, sample_rate_hz, envelope_mode, edge_mode, lowpass_hz=5.0, envelope_rate_hz=ENVELOPE_RATE_HZ):
    """Absolute value, low-pass, keep every n-th value (as run 1: the value at the end of each 1/100 s).
    envelope_mode "causal_two_pole": run 1's two one-pole stages; "zero_phase_one_pole": one stage forward
    and backward (the same magnitude as two stages, no delay)."""
    rectified = numpy.abs(filtered).astype(numpy.float32)
    coefficient = one_pole_coefficient(lowpass_hz, sample_rate_hz)
    start = rectified[0] if edge_mode == "reflect" else numpy.float32(0.0)
    first_stage = numpy.empty_like(rectified)
    second_stage = numpy.empty_like(rectified)
    _one_pole(rectified, coefficient, numpy.float32(start), first_stage)
    if envelope_mode == "causal_two_pole":
        _one_pole(first_stage, coefficient, numpy.float32(start), second_stage)
        smoothed = second_stage
    elif envelope_mode == "zero_phase_one_pole":
        reversed_first = numpy.ascontiguousarray(first_stage[::-1])
        backward_start = reversed_first[0] if edge_mode == "reflect" else numpy.float32(0.0)
        _one_pole(reversed_first, coefficient, numpy.float32(backward_start), second_stage)
        smoothed = second_stage[::-1]
    else:
        raise ValueError(envelope_mode)
    decimation_factor = int(round(sample_rate_hz / envelope_rate_hz))
    return numpy.ascontiguousarray(smoothed[decimation_factor - 1::decimation_factor], dtype=numpy.float32)


_PEAK_CHOOSERS = {}


def _peak_chooser(window_length, envelope_rate_hz, peak_choice, minimum_bpm=30.0, maximum_bpm=200.0):
    key = (window_length, envelope_rate_hz, peak_choice, minimum_bpm, maximum_bpm)
    if key not in _PEAK_CHOOSERS:
        configuration = replace(FINAL_ESTIMATOR, envelope_rate_hz=int(envelope_rate_hz),
                                window_seconds=window_length / envelope_rate_hz, peak_choice=peak_choice,
                                minimum_bpm=minimum_bpm, maximum_bpm=maximum_bpm)
        _PEAK_CHOOSERS[key] = BPMEstimator(configuration, input_rate_hz=16000.0)
    return _PEAK_CHOOSERS[key]


def run_one_autocorrelation_and_peak(envelope_values, envelope_rate_hz=ENVELOPE_RATE_HZ, peak_choice="half_check",
                                     taper_fraction=0.0, minimum_bpm=30.0, maximum_bpm=200.0):
    """Mean removal, optional Tukey taper, run 1's normalised autocorrelation and peak choice."""
    window = numpy.ascontiguousarray(envelope_values, dtype=numpy.float32).copy()
    window -= numpy.float32(window.mean(dtype=numpy.float32))
    if taper_fraction > 0:
        window *= signal.windows.tukey(window.shape[0], taper_fraction).astype(numpy.float32)
    chooser = _peak_chooser(window.shape[0], envelope_rate_hz, peak_choice, minimum_bpm, maximum_bpm)
    _normalised_autocorrelation(window, chooser.correlation_lag_count, chooser.correlation)
    result = chooser._choose_peak()
    return WindowEstimate(result.bpm, result.quality, result.valid, {"reason": result.reason, "margin": result.margin})


# Zero-phase family -----------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class ZeroPhaseMethod:
    """Band-pass the whole window (two passes), envelope, autocorrelation with half-rate check."""
    key: str
    highpass_hz: float | None
    lowpass_hz: float | None
    order: int
    pass_mode: str = "forward_backward"
    edge_mode: str = "reflect"
    discard_seconds: float = 0.0
    envelope_mode: str = "zero_phase_one_pole"
    match_half_power_edges: bool = False
    spike_removal: bool = False
    description: str = ""

    def designed_sections(self, sample_rate_hz):
        highpass_hz, lowpass_hz = self.highpass_hz, self.lowpass_hz
        if self.match_half_power_edges and self.pass_mode != "forward_once":
            highpass_hz, lowpass_hz = edges_for_half_power_after_two_passes(highpass_hz, lowpass_hz, self.order, sample_rate_hz)
        return butterworth_sections(highpass_hz, lowpass_hz, self.order, sample_rate_hz), (highpass_hz, lowpass_hz)

    def estimate(self, window_normalised_float, sample_rate_hz):
        sections, used_edges = _cached_sections(self, sample_rate_hz)
        filter_edge_mode = "reflect" if self.edge_mode == "reflect" else "none"
        filtered = two_pass_filter(sections, window_normalised_float, self.pass_mode, filter_edge_mode)
        if self.spike_removal:
            filtered = schmidt_spike_removal(filtered, sample_rate_hz).astype(numpy.float32)
        if self.envelope_mode == "homomorphic":
            homomorphic = homomorphic_envelope(numpy.asarray(filtered, dtype=float), sample_rate_hz)
            decimation_factor = int(round(sample_rate_hz / ENVELOPE_RATE_HZ))
            envelope_values = numpy.ascontiguousarray(homomorphic[decimation_factor - 1::decimation_factor], dtype=numpy.float32)
        else:
            envelope_values = envelope(filtered, sample_rate_hz, self.envelope_mode, filter_edge_mode)
        discard = int(round(self.discard_seconds * ENVELOPE_RATE_HZ))
        if discard:
            envelope_values = envelope_values[discard:-discard]
        estimate = run_one_autocorrelation_and_peak(envelope_values)
        estimate.details.update({"used_edges_hz": [None if edge is None else round(float(edge), 2) for edge in used_edges],
                                 "usable_seconds": envelope_values.shape[0] / ENVELOPE_RATE_HZ})
        return estimate


_SECTION_CACHE = {}


def _cached_sections(method, sample_rate_hz):
    key = (method.highpass_hz, method.lowpass_hz, method.order, method.pass_mode, method.match_half_power_edges, sample_rate_hz)
    if key not in _SECTION_CACHE:
        _SECTION_CACHE[key] = method.designed_sections(sample_rate_hz)
    return _SECTION_CACHE[key]


# Non-causal counting on run 1's stored envelope buffer ----------------------------------------------------------

@dataclass(frozen=True)
class StoredEnvelopeMethod:
    """Input: the 800 stored envelope values of run 1's causal chain (100 per second), not raw samples."""
    key: str
    zero_phase_smoothing_hz: float | None
    taper_fraction: float
    description: str = ""

    def estimate(self, envelope_values, sample_rate_hz=ENVELOPE_RATE_HZ):
        values = numpy.ascontiguousarray(envelope_values, dtype=numpy.float32)
        if self.zero_phase_smoothing_hz:
            coefficient = one_pole_coefficient(self.zero_phase_smoothing_hz, sample_rate_hz)
            forward = numpy.empty_like(values)
            _one_pole(values, coefficient, values[0], forward)
            reversed_forward = numpy.ascontiguousarray(forward[::-1])
            backward = numpy.empty_like(values)
            _one_pole(reversed_forward, coefficient, reversed_forward[0], backward)
            values = numpy.ascontiguousarray(backward[::-1])
        return run_one_autocorrelation_and_peak(values, int(sample_rate_hz), taper_fraction=self.taper_fraction)


# Springer family ------------------------------------------------------------------------------------------------

SPRINGER_AUDIO_RATE_HZ = 1000
SPRINGER_FEATURE_RATE_HZ = 50


def matlab_filtfilt(numerator, denominator, values):
    # MATLAB filtfilt pads 3*(nfilt-1) samples by odd reflection and starts from the steady state, as SciPy with this padlen.
    return signal.filtfilt(numerator, denominator, values, padtype="odd",
                           padlen=3 * (max(len(numerator), len(denominator)) - 1))


def springer_band_pass(audio, sample_rate_hz):
    low_numerator, low_denominator = signal.butter(2, 2 * 400 / sample_rate_hz, "low")
    audio = matlab_filtfilt(low_numerator, low_denominator, audio)
    high_numerator, high_denominator = signal.butter(2, 2 * 25 / sample_rate_hz, "high")
    return matlab_filtfilt(high_numerator, high_denominator, audio)


def schmidt_spike_removal(original_signal, sample_rate_hz):
    window_size = int(numpy.round(sample_rate_hz / 2))
    trailing = len(original_signal) % window_size
    usable = len(original_signal) - trailing
    frames = numpy.array(original_signal[:usable], dtype=float).reshape(-1, window_size).T.copy()
    maximum_absolute_amplitudes = numpy.abs(frames).max(axis=0)
    while numpy.any(maximum_absolute_amplitudes > numpy.median(maximum_absolute_amplitudes) * 3):
        window_number = int(numpy.argmax(maximum_absolute_amplitudes))
        column = frames[:, window_number]
        spike_position = int(numpy.argmax(numpy.abs(column)))
        zero_crossings = numpy.concatenate((numpy.abs(numpy.diff(numpy.sign(column))) > 1, [False]))
        before = numpy.flatnonzero(zero_crossings[:spike_position + 1])
        spike_start = before[-1] if before.size else 0
        zero_crossings[:spike_position + 1] = False
        after = numpy.flatnonzero(zero_crossings)
        spike_end = min(after[0], window_size - 1) if after.size else window_size - 1
        frames[spike_start:spike_end + 1, window_number] = 0.0001
        maximum_absolute_amplitudes = numpy.abs(frames).max(axis=0)
    despiked = frames.T.reshape(-1)
    return numpy.concatenate((despiked, numpy.asarray(original_signal[usable:], dtype=float)))


def homomorphic_envelope(audio, sample_rate_hz, lowpass_hz=8.0):
    numerator, denominator = signal.butter(1, 2 * lowpass_hz / sample_rate_hz, "low")
    magnitude = numpy.maximum(numpy.abs(signal.hilbert(audio)), 1e-30)
    result = numpy.exp(matlab_filtfilt(numerator, denominator, numpy.log(magnitude)))
    result[0] = result[1]
    return result


def hilbert_envelope(audio):
    return numpy.abs(signal.hilbert(audio))


def power_spectral_density_feature(audio, sample_rate_hz, low_hz=40, high_hz=60):
    """Mean spectrogram power over 40-60 Hz: Hamming window of sample_rate/40 samples, overlap round(sample_rate/80),
    evaluated at whole-Hz frequencies as MATLAB spectrogram(data, Fs/40, round(Fs/80), 1:1:round(Fs/2), Fs)."""
    window_length = int(sample_rate_hz / 40)
    overlap = int(numpy.floor(sample_rate_hz / 80 + 0.5))
    hop = window_length - overlap
    segment_count = (len(audio) - overlap) // hop
    taper = numpy.hamming(window_length)
    frequencies = numpy.arange(low_hz, high_hz + 1)
    sample_index = numpy.arange(window_length)
    kernel = taper[None, :] * numpy.exp(-2j * numpy.pi * frequencies[:, None] * sample_index[None, :] / sample_rate_hz)
    starts = numpy.arange(segment_count) * hop
    segments = audio[starts[:, None] + sample_index[None, :]]
    power = numpy.abs(segments @ kernel.T) ** 2
    return power.mean(axis=1)


def z_normalise(values):
    return (values - values.mean()) / values.std(ddof=1)


def matlab_coefficient_autocorrelation(values):
    """xcorr(y, 'coeff') for lags 0..N-1: raw sums divided by the zero-lag value."""
    length = len(values)
    size = 1 << int(numpy.ceil(numpy.log2(2 * length)))
    spectrum = numpy.fft.rfft(values, size)
    raw = numpy.fft.irfft(spectrum * numpy.conj(spectrum), size)[:length]
    return raw / raw[0]


def springer_preprocess(window_normalised_float, sample_rate_hz):
    audio = numpy.asarray(window_normalised_float, dtype=float)
    if sample_rate_hz != SPRINGER_AUDIO_RATE_HZ:
        factor = int(round(sample_rate_hz / SPRINGER_AUDIO_RATE_HZ))
        audio = signal.resample_poly(audio, 1, factor)
    audio = springer_band_pass(audio, SPRINGER_AUDIO_RATE_HZ)
    return schmidt_spike_removal(audio, SPRINGER_AUDIO_RATE_HZ)


def _parabolic_lag(correlation, lag):
    previous_value, peak_value, next_value = correlation[lag - 1], correlation[lag], correlation[lag + 1]
    curvature = previous_value - 2 * peak_value + next_value
    return lag + (0.5 * (previous_value - next_value) / curvature if curvature < 0 else 0.0)


def _range_estimate(correlation, rate_hz, minimum_seconds, maximum_seconds, interpolate):
    minimum_index = int(round(minimum_seconds * rate_hz))
    maximum_index = int(round(maximum_seconds * rate_hz))
    lag = minimum_index + int(numpy.argmax(correlation[minimum_index:maximum_index + 1]))
    precise_lag = _parabolic_lag(correlation, lag) if interpolate and 0 < lag < len(correlation) - 1 else float(lag)
    quality = float(correlation[lag])
    return WindowEstimate(60.0 / (precise_lag / rate_hz), quality, quality >= FINAL_ESTIMATOR.quality_threshold,
                          {"lag_samples": precise_lag})


def _half_check_estimate(correlation, rate_hz):
    chooser = _peak_chooser(len(correlation) - 1, rate_hz, "half_check")
    count = min(chooser.correlation.shape[0], len(correlation))
    chooser.correlation[:] = 0
    chooser.correlation[:count] = correlation[:count].astype(numpy.float32)
    result = chooser._choose_peak()
    return WindowEstimate(result.bpm, result.quality, result.valid, {"reason": result.reason})


@dataclass(frozen=True)
class SpringerHeartRateMethod:
    """getHeartRateSchmidt.m: band-pass, spike removal, homomorphic envelope, autocorrelation, highest value in the lag range."""
    key: str
    minimum_seconds: float = 0.5
    maximum_seconds: float = 2.0
    peak_choice: str = "highest_in_range"
    description: str = ""

    def estimate(self, window_normalised_float, sample_rate_hz):
        audio = springer_preprocess(window_normalised_float, sample_rate_hz)
        homomorphic = homomorphic_envelope(audio, SPRINGER_AUDIO_RATE_HZ)
        correlation = matlab_coefficient_autocorrelation(homomorphic - homomorphic.mean())
        if self.peak_choice == "half_check":
            return _half_check_estimate(correlation, SPRINGER_AUDIO_RATE_HZ)
        return _range_estimate(correlation, SPRINGER_AUDIO_RATE_HZ, self.minimum_seconds, self.maximum_seconds, False)


@dataclass(frozen=True)
class SpringerEnvelopesCombinedMethod:
    """Homomorphic, Hilbert and power-spectral-density envelopes of getSpringerPCGFeatures.m (the wavelet feature is not
    implemented), each at the feature rate and normalised, autocorrelated, averaged, then one peak search."""
    key: str
    feature_rate_hz: int = SPRINGER_FEATURE_RATE_HZ
    minimum_seconds: float = 0.5
    maximum_seconds: float = 2.0
    peak_choice: str = "highest_in_range"
    description: str = ""

    def features(self, window_normalised_float, sample_rate_hz):
        audio = springer_preprocess(window_normalised_float, sample_rate_hz)
        down = SPRINGER_AUDIO_RATE_HZ // self.feature_rate_hz
        homomorphic = z_normalise(signal.resample_poly(homomorphic_envelope(audio, SPRINGER_AUDIO_RATE_HZ), 1, down))
        hilbert = z_normalise(signal.resample_poly(hilbert_envelope(audio), 1, down))
        power = power_spectral_density_feature(audio, SPRINGER_AUDIO_RATE_HZ)
        divisor = numpy.gcd(len(homomorphic), len(power))
        power = z_normalise(signal.resample_poly(power, len(homomorphic) // divisor, len(power) // divisor))[:len(homomorphic)]
        return [homomorphic, hilbert, power]

    def estimate(self, window_normalised_float, sample_rate_hz):
        features = self.features(window_normalised_float, sample_rate_hz)
        correlation = numpy.mean([matlab_coefficient_autocorrelation(feature - feature.mean()) for feature in features], axis=0)
        if self.peak_choice == "half_check":
            return _half_check_estimate(correlation, self.feature_rate_hz)
        return _range_estimate(correlation, self.feature_rate_hz, self.minimum_seconds, self.maximum_seconds, True)
