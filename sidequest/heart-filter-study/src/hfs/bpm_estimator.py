"""Causal, streaming BPM estimator for the analysis path, written to port line by line to C.

Per 64-frame block: rectify -> envelope low-pass -> decimate -> ring buffer (the window held in PSRAM).
Every second: compress -> remove mean -> normalised autocorrelation -> peak choice -> interpolation -> validity.
All arrays have a fixed size chosen at construction; arithmetic is float32.
"""
from dataclasses import asdict, dataclass

import numba
import numpy

RECTIFICATION_CODES = {"absolute": 0, "square": 1, "shannon": 2}
ENVELOPE_LOWPASS_CODES = {"one_pole": 0, "two_pole": 1, "boxcar": 2}
PEAK_CHOICES = ("highest", "half_check", "first_above", "comb", "submultiple", "harmonic_sum")
EXTENDED_PEAK_CHOICE_CODES = {"highest": 0, "half_check": 1, "first_above": 2, "submultiple": 3, "harmonic_sum": 4}
LAG_WEIGHTINGS = ("none", "overlap")
MARGIN_CHECK_DISABLED = -2.0
COMPRESSIONS = ("none", "log", "clip_mean3")
SHANNON_SCALE = numpy.float32(0.5)
SHANNON_FLOOR = numpy.float32(1e-12)
MICROPHONE_SAMPLE_RATE_HZ = 16000.0


@dataclass(frozen=True)
class EstimatorConfiguration:
    rectification: str = "absolute"
    envelope_lowpass: str = "one_pole"
    envelope_lowpass_hz: float = 12.0
    envelope_rate_hz: int = 100
    window_seconds: float = 8.0
    update_seconds: float = 1.0
    minimum_bpm: float = 30.0
    maximum_bpm: float = 200.0
    compression: str = "none"
    peak_choice: str = "highest"
    first_above_fraction: float = 0.8
    half_check_fraction: float = 0.8
    quality_threshold: float = 0.3
    clipping_invalid_share: float = 0.01
    lag_weighting: str = "none"
    submultiple_fraction: float = 0.85
    submultiple_largest_divisor: int = 4
    minimum_rival_margin: float = MARGIN_CHECK_DISABLED
    agreement_fraction: float = 0.0

    def uses_extended_choice(self) -> bool:
        return (self.peak_choice in ("submultiple", "harmonic_sum") or self.lag_weighting != "none"
                or self.minimum_rival_margin > MARGIN_CHECK_DISABLED or self.agreement_fraction > 0.0)

    def key(self) -> str:
        default = EstimatorConfiguration()
        parts = [f"{name}={value}" for name, value in asdict(self).items() if getattr(default, name) != value]
        return "default" if not parts else ",".join(parts)


@dataclass
class EstimateResult:
    bpm: float
    valid: bool
    quality: float
    margin: float
    reason: str
    lag_seconds: float


@numba.njit(cache=True)
def _envelope_block(block, rectification_code, lowpass_code, coefficient, lowpass_state, counter_state,
                    decimation_factor, boxcar_scale, output):
    """Returns the number of envelope samples written to output."""
    written = 0
    for index in range(block.shape[0]):
        value = block[index]
        if rectification_code == 0:
            rectified = abs(value)
        elif rectification_code == 1:
            rectified = value * value
        else:
            scaled = value * SHANNON_SCALE
            if scaled > numpy.float32(1.0):
                scaled = numpy.float32(1.0)
            elif scaled < numpy.float32(-1.0):
                scaled = numpy.float32(-1.0)
            energy = scaled * scaled
            rectified = -energy * numpy.float32(numpy.log(energy + SHANNON_FLOOR))
        if lowpass_code == 0:
            lowpass_state[0] += coefficient * (rectified - lowpass_state[0])
            filtered = lowpass_state[0]
        elif lowpass_code == 1:
            lowpass_state[0] += coefficient * (rectified - lowpass_state[0])
            lowpass_state[1] += coefficient * (lowpass_state[0] - lowpass_state[1])
            filtered = lowpass_state[1]
        else:
            lowpass_state[0] += rectified
            filtered = numpy.float32(0.0)
        counter_state[0] += 1
        if counter_state[0] == decimation_factor:
            counter_state[0] = 0
            if lowpass_code == 2:
                mean = lowpass_state[0] * boxcar_scale
                lowpass_state[0] = numpy.float32(0.0)
                # Integrate-and-dump removes aliasing; the one-pole at the envelope rate sets the bandwidth.
                lowpass_state[1] += coefficient * (mean - lowpass_state[1])
                filtered = lowpass_state[1]
            output[written] = filtered
            written += 1
    return written


@numba.njit(cache=True)
def _normalised_autocorrelation(window, maximum_lag, correlation):
    length = window.shape[0]
    total_energy = numpy.float32(0.0)
    for index in range(length):
        total_energy += window[index] * window[index]
    head_energy = total_energy
    tail_energy = total_energy
    correlation[0] = numpy.float32(1.0)
    for lag in range(1, maximum_lag + 1):
        head_energy -= window[length - lag] * window[length - lag]
        tail_energy -= window[lag - 1] * window[lag - 1]
        accumulator = numpy.float32(0.0)
        for index in range(length - lag):
            accumulator += window[index] * window[index + lag]
        denominator = numpy.float32(numpy.sqrt(max(head_energy, numpy.float32(1e-30)) * max(tail_energy, numpy.float32(1e-30))))
        correlation[lag] = accumulator / denominator


@numba.njit(cache=True)
def _choose_lag(weighted, correlation, minimum_lag, maximum_lag, lag_count, choice_code, first_above_fraction,
                half_check_fraction, submultiple_fraction, largest_divisor, peaks):
    """Peak choice on the (optionally lag-weighted) correlation. Returns (chosen lag, highest unrelated peak of the
    unweighted correlation); chosen lag -1 when there is no peak in the search range. Codes: 0 highest, 1 half_check,
    2 first_above, 3 submultiple, 4 harmonic_sum."""
    count = 0
    for lag in range(minimum_lag, maximum_lag + 1):
        if weighted[lag] > weighted[lag - 1] and weighted[lag] >= weighted[lag + 1]:
            peaks[count] = lag
            count += 1
    if count == 0:
        return -1, 0.0
    highest = peaks[0]
    for index in range(1, count):
        if weighted[peaks[index]] > weighted[highest]:
            highest = peaks[index]
    chosen = highest
    if choice_code == 1:
        for _ in range(2):
            half = chosen / 2.0
            best_near = -1
            for index in range(count):
                lag = peaks[index]
                if abs(lag - half) <= 0.1 * half and (best_near < 0 or weighted[lag] > weighted[best_near]):
                    best_near = lag
            if best_near < 0 or weighted[best_near] < half_check_fraction * weighted[chosen]:
                break
            chosen = best_near
    elif choice_code == 2:
        threshold = first_above_fraction * weighted[highest]
        for index in range(count):
            if weighted[peaks[index]] >= threshold:
                chosen = peaks[index]
                break
    elif choice_code == 3:
        # Largest divisor first, so that the shortest lag that is nearly as similar as the highest peak wins.
        for divisor in range(largest_divisor, 1, -1):
            target = highest / divisor
            best_near = -1
            for index in range(count):
                lag = peaks[index]
                if abs(lag - target) <= 0.1 * target and (best_near < 0 or weighted[lag] > weighted[best_near]):
                    best_near = lag
            if best_near >= 0 and weighted[best_near] >= submultiple_fraction * weighted[highest]:
                chosen = best_near
                break
    elif choice_code == 4:
        best_score = -1e30
        for index in range(count):
            lag = peaks[index]
            total = weighted[lag]
            terms = 1
            for multiple in range(2, 4):
                centre = multiple * lag
                if centre + 1 <= lag_count:
                    total += max(weighted[centre - 1], weighted[centre], weighted[centre + 1])
                    terms += 1
            score = total / terms
            if score > best_score:
                best_score = score
                chosen = lag
    rival = 0.0
    for index in range(count):
        lag = peaks[index]
        multiple = round(lag / chosen)
        if multiple >= 1 and abs(lag - multiple * chosen) <= 0.1 * multiple * chosen:
            continue
        divisor = round(chosen / lag)
        if 2 <= divisor <= 4 and abs(lag - chosen / divisor) <= 0.1 * chosen / divisor:
            continue
        if correlation[lag] > rival:
            rival = correlation[lag]
    return chosen, rival


def _extended_validity(configuration, bpm, peak_value, margin, clipped_share, previous_estimates):
    if bpm < configuration.minimum_bpm or bpm > configuration.maximum_bpm:
        return "out_of_range"
    if clipped_share > configuration.clipping_invalid_share:
        return "clipping"
    if peak_value < configuration.quality_threshold:
        return "low_periodicity"
    if margin < configuration.minimum_rival_margin:
        return "small_margin"
    if configuration.agreement_fraction > 0.0:
        tolerance = configuration.agreement_fraction * bpm
        if not any(abs(bpm - previous) <= tolerance for previous in previous_estimates if numpy.isfinite(previous)):
            return "no_agreement"
    return ""


def _parabolic_lag(correlation, chosen):
    previous_value = float(correlation[chosen - 1])
    peak_value = float(correlation[chosen])
    next_value = float(correlation[chosen + 1])
    curvature = previous_value - 2.0 * peak_value + next_value
    offset = 0.5 * (previous_value - next_value) / curvature if curvature < 0 else 0.0
    return chosen + offset


class BPMEstimator:
    def __init__(self, configuration: EstimatorConfiguration = EstimatorConfiguration(), input_rate_hz: float = 16000.0):
        self.configuration = configuration
        configuration_values = configuration
        self.input_rate_hz = float(input_rate_hz)
        self.decimation_factor = int(round(input_rate_hz / configuration_values.envelope_rate_hz))
        if abs(self.decimation_factor * configuration_values.envelope_rate_hz - input_rate_hz) > 1e-6:
            raise ValueError("envelope rate must divide the input rate")
        self.envelope_rate_hz = configuration_values.envelope_rate_hz
        self.rectification_code = RECTIFICATION_CODES[configuration_values.rectification]
        self.lowpass_code = ENVELOPE_LOWPASS_CODES[configuration_values.envelope_lowpass]
        lowpass_rate = self.envelope_rate_hz if self.lowpass_code == 2 else input_rate_hz
        self.lowpass_coefficient = numpy.float32(1.0 - numpy.exp(-2.0 * numpy.pi * configuration_values.envelope_lowpass_hz / lowpass_rate))
        self.boxcar_scale = numpy.float32(1.0 / self.decimation_factor)
        self.lowpass_state = numpy.zeros(2, dtype=numpy.float32)
        self.counter_state = numpy.zeros(1, dtype=numpy.int64)
        self.window_length = int(round(configuration_values.window_seconds * self.envelope_rate_hz))
        self.ring_buffer = numpy.zeros(self.window_length, dtype=numpy.float32)
        self.ring_position = 0
        self.ring_filled = 0
        self.block_output = numpy.zeros(4096 // max(1, self.decimation_factor) + 2, dtype=numpy.float32)
        self.minimum_lag = int(numpy.floor(60.0 / configuration_values.maximum_bpm * self.envelope_rate_hz))
        self.maximum_lag = int(numpy.ceil(60.0 / configuration_values.minimum_bpm * self.envelope_rate_hz))
        self.correlation_lag_count = min(2 * self.maximum_lag + 1, self.window_length - 1)
        self.correlation = numpy.zeros(self.correlation_lag_count + 1, dtype=numpy.float32)
        self.chronological_window = numpy.zeros(self.window_length, dtype=numpy.float32)
        self.update_count_per_window = int(round(configuration_values.window_seconds / configuration_values.update_seconds))
        self.clipped_counts = numpy.zeros(self.update_count_per_window, dtype=numpy.int64)
        self.clipped_position = 0
        self.clipped_since_update = 0
        # Clipped counts are microphone samples at 16 kHz, also when the filter output is rate-reduced.
        self.microphone_samples_per_window = int(round(configuration_values.window_seconds * MICROPHONE_SAMPLE_RATE_HZ))
        self.extended_choice = configuration_values.uses_extended_choice()
        if self.extended_choice:
            lags = numpy.arange(self.correlation_lag_count + 1, dtype=numpy.float32)
            if configuration_values.lag_weighting == "overlap":
                self.lag_weights = ((self.window_length - lags) / numpy.float32(self.window_length)).astype(numpy.float32)
            else:
                self.lag_weights = numpy.ones(self.correlation_lag_count + 1, dtype=numpy.float32)
            self.weighted_correlation = numpy.zeros(self.correlation_lag_count + 1, dtype=numpy.float32)
            self.peak_lags = numpy.zeros(self.correlation_lag_count + 1, dtype=numpy.int64)
            self.previous_estimates = numpy.full(2, numpy.nan, dtype=numpy.float32)

    def memory_bytes(self) -> dict:
        return {"window_bytes": int(self.ring_buffer.nbytes), "correlation_bytes": int(self.correlation.nbytes),
                "scratch_bytes": int(self.chronological_window.nbytes),
                "other_state_bytes": int(self.lowpass_state.nbytes + 8 * self.update_count_per_window + 16)}

    def operations_per_second(self) -> dict:
        rectification_multiplies = {0: 0, 1: 1, 2: 3}[self.rectification_code]
        lowpass_multiplies = {0: 1, 1: 2, 2: 0}[self.lowpass_code]
        per_input = (rectification_multiplies + lowpass_multiplies) * self.input_rate_hz
        lags = self.correlation_lag_count
        autocorrelation = self.window_length * lags - lags * (lags + 1) // 2
        updates_per_second = 1.0 / self.configuration.update_seconds
        return {"envelope_multiplies_per_second": per_input + (self.envelope_rate_hz if self.lowpass_code == 2 else 0),
                "logarithms_per_second": self.input_rate_hz if self.rectification_code == 2 else 0,
                "autocorrelation_multiplies_per_update": autocorrelation,
                "autocorrelation_multiplies_per_second": autocorrelation * updates_per_second}

    def process_block(self, filtered_block: numpy.ndarray, clipped_sample_count: int = 0) -> None:
        filtered_block = numpy.ascontiguousarray(filtered_block, dtype=numpy.float32)
        written = _envelope_block(filtered_block, self.rectification_code, self.lowpass_code, self.lowpass_coefficient,
                                  self.lowpass_state, self.counter_state, self.decimation_factor, self.boxcar_scale,
                                  self.block_output)
        for index in range(written):
            self.ring_buffer[self.ring_position] = self.block_output[index]
            self.ring_position = (self.ring_position + 1) % self.window_length
        self.ring_filled = min(self.window_length, self.ring_filled + written)
        self.clipped_since_update += int(clipped_sample_count)

    def update(self) -> EstimateResult:
        self.clipped_counts[self.clipped_position] = self.clipped_since_update
        self.clipped_position = (self.clipped_position + 1) % self.update_count_per_window
        self.clipped_since_update = 0
        if self.ring_filled < self.window_length:
            return EstimateResult(float("nan"), False, 0.0, 0.0, "window_not_full", float("nan"))
        configuration = self.configuration
        window = self.chronological_window
        window[: self.window_length - self.ring_position] = self.ring_buffer[self.ring_position:]
        window[self.window_length - self.ring_position:] = self.ring_buffer[: self.ring_position]
        mean = numpy.float32(window.mean(dtype=numpy.float32))
        if configuration.compression == "log":
            window[:] = numpy.log1p(window / max(mean, numpy.float32(1e-20))).astype(numpy.float32)
        elif configuration.compression == "clip_mean3":
            numpy.minimum(window, numpy.float32(3.0) * mean, out=window)
        window -= numpy.float32(window.mean(dtype=numpy.float32))
        _normalised_autocorrelation(window, self.correlation_lag_count, self.correlation)
        return self._choose_peak()

    def _choose_peak_extended(self) -> EstimateResult:
        """Peak choice for the options added after run 2: lag weighting, sub-multiple check, harmonic sum, rival margin
        and agreement with the previous two estimates."""
        configuration = self.configuration
        correlation = self.correlation
        numpy.multiply(correlation, self.lag_weights, out=self.weighted_correlation)
        maximum_lag = min(self.maximum_lag, self.correlation_lag_count - 1)
        chosen, rival = _choose_lag(self.weighted_correlation, correlation, self.minimum_lag, maximum_lag,
                                    self.correlation_lag_count, EXTENDED_PEAK_CHOICE_CODES[configuration.peak_choice],
                                    configuration.first_above_fraction, configuration.half_check_fraction,
                                    configuration.submultiple_fraction, configuration.submultiple_largest_divisor, self.peak_lags)
        if chosen < 0:
            edge_lag = max(range(self.minimum_lag, maximum_lag + 1), key=lambda lag: correlation[lag])
            bpm = 60.0 * self.envelope_rate_hz / edge_lag
            self.previous_estimates[1] = self.previous_estimates[0]
            self.previous_estimates[0] = bpm
            return EstimateResult(bpm, False, float(correlation[edge_lag]), 0.0, "out_of_range", edge_lag / self.envelope_rate_hz)
        lag_seconds = _parabolic_lag(correlation, chosen) / self.envelope_rate_hz
        bpm = 60.0 / lag_seconds
        peak_value = float(correlation[chosen])
        margin = peak_value - float(rival)
        clipped_share = self.clipped_counts.sum() / self.microphone_samples_per_window
        reason = _extended_validity(configuration, bpm, peak_value, margin, clipped_share, self.previous_estimates)
        self.previous_estimates[1] = self.previous_estimates[0]
        self.previous_estimates[0] = bpm
        return EstimateResult(bpm, reason == "", peak_value, margin, reason or "valid", lag_seconds)

    def _choose_peak(self) -> EstimateResult:
        if self.extended_choice:
            return self._choose_peak_extended()
        configuration = self.configuration
        correlation = self.correlation
        minimum_lag = self.minimum_lag
        maximum_lag = min(self.maximum_lag, self.correlation_lag_count - 1)
        peaks = [lag for lag in range(minimum_lag, maximum_lag + 1)
                 if correlation[lag] > correlation[lag - 1] and correlation[lag] >= correlation[lag + 1]]
        if not peaks:
            edge_lag = max(range(minimum_lag, maximum_lag + 1), key=lambda lag: correlation[lag])
            return EstimateResult(60.0 * self.envelope_rate_hz / edge_lag, False, float(correlation[edge_lag]), 0.0,
                                  "out_of_range", edge_lag / self.envelope_rate_hz)
        highest = max(peaks, key=lambda lag: correlation[lag])
        chosen = highest
        if configuration.peak_choice == "first_above":
            threshold = configuration.first_above_fraction * correlation[highest]
            chosen = next(lag for lag in peaks if correlation[lag] >= threshold)
        elif configuration.peak_choice == "half_check":
            for _ in range(2):
                half = chosen / 2.0
                near = [lag for lag in peaks if abs(lag - half) <= 0.1 * half]
                if not near:
                    break
                best_near = max(near, key=lambda lag: correlation[lag])
                if correlation[best_near] >= configuration.half_check_fraction * correlation[chosen]:
                    chosen = best_near
                else:
                    break
        elif configuration.peak_choice == "comb":
            # Sum of the peak and its second harmonic: the true cycle scores r(T)+r(2T), a sub-harmonic
            # only r(2T)+r(4T), so long lags are not favoured.
            def comb_score(lag):
                start = max(1, 2 * lag - 2)
                stop = min(self.correlation_lag_count, 2 * lag + 2)
                return correlation[lag] + correlation[start:stop + 1].max()
            chosen = max(peaks, key=comb_score)
        previous_value = float(correlation[chosen - 1])
        peak_value = float(correlation[chosen])
        next_value = float(correlation[chosen + 1])
        curvature = previous_value - 2.0 * peak_value + next_value
        offset = 0.5 * (previous_value - next_value) / curvature if curvature < 0 else 0.0
        lag_samples = chosen + offset
        lag_seconds = lag_samples / self.envelope_rate_hz
        bpm = 60.0 / lag_seconds
        competitors = [correlation[lag] for lag in peaks if abs(lag - chosen) > 0.15 * chosen]
        margin = peak_value - (float(max(competitors)) if competitors else 0.0)
        reason = ""
        clipped_share = self.clipped_counts.sum() / self.microphone_samples_per_window
        if bpm < configuration.minimum_bpm or bpm > configuration.maximum_bpm:
            reason = "out_of_range"
        elif clipped_share > configuration.clipping_invalid_share:
            reason = "clipping"
        elif peak_value < configuration.quality_threshold:
            reason = "low_periodicity"
        return EstimateResult(bpm, reason == "", peak_value, margin, reason or "valid", lag_seconds)


def run_estimator(filtered: numpy.ndarray, input_rate_hz: float, configuration: EstimatorConfiguration,
                  clipped_flags: numpy.ndarray | None = None, start_time_seconds: float = 2.0,
                  first_end_time_seconds: int = 10, last_end_time_seconds: int = 60, block_frames: int = 64):
    """Stream a whole recording through the estimator; returns {end_time_s: EstimateResult}.
    clipped_flags marks clipped microphone samples at 16 kHz (one per input sample at 16 kHz)."""
    estimator = BPMEstimator(configuration, input_rate_hz)
    block_input = int(round(block_frames * input_rate_hz / 16000.0))
    samples_per_update = int(round(configuration.update_seconds * input_rate_hz))
    clip_ratio = int(round(16000.0 / input_rate_hz))
    results = {}
    position = 0
    update_time = start_time_seconds
    total = filtered.shape[0]
    while position + samples_per_update <= total:
        stop = position + samples_per_update
        for block_start in range(position, stop, block_input):
            block_stop = min(block_start + block_input, stop)
            clipped = 0
            if clipped_flags is not None:
                clipped = int(clipped_flags[block_start * clip_ratio:block_stop * clip_ratio].sum())
            estimator.process_block(filtered[block_start:block_stop], clipped)
        position = stop
        update_time += configuration.update_seconds
        result = estimator.update()
        end_time = int(round(update_time))
        if first_end_time_seconds <= end_time <= last_end_time_seconds:
            results[end_time] = result
    return results, estimator


def median_of_last_three(estimates: list[float]) -> list[float]:
    smoothed = []
    for index in range(len(estimates)):
        recent = [value for value in estimates[max(0, index - 2):index + 1] if numpy.isfinite(value)]
        smoothed.append(float(numpy.median(recent)) if recent else float("nan"))
    return smoothed
