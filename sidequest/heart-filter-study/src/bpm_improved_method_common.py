"""Shared pieces of the improved-method study: method variants, the subject split, a batch version of the
estimator's peak choice over cached correlations, pooled metrics and the subject bootstrap."""
import sys
from dataclasses import replace
from pathlib import Path

import numba
import numpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpm_evaluate_public
import bpm_improved_method_compute as compute
import public_evaluation_common as common
from hfs import bpm_estimator, ephnogram
from hfs.bpm_estimator import EstimatorConfiguration

SPLIT_SEED = 20261123
BOOTSTRAP_SEED = 20261123
BOOTSTRAP_COUNT = 2000
CONDITIONS = ("rest", "overload")
FILTER_LABELS = {"raw": "no filter", "butterworth_hp2_25_lp2_150": "25-150 Hz", "butterworth_hp2_30_lp2_150": "30-150 Hz",
                 "butterworth_hp2_40_lp2_150": "40-150 Hz", "butterworth_hp2_50_lp2_150": "50-150 Hz",
                 "butterworth_hp2_60_lp2_150": "60-150 Hz", "butterworth_hp2_80_lp2_150": "80-150 Hz",
                 "butterworth_hp2_40_lp2_400": "40-400 Hz", "butterworth_hp4_60_lp4_150": "4+4 60-150 Hz"}
ENVELOPE_OF = {("two_pole", 5.0): "two_pole_5hz", ("one_pole", 12.0): "one_pole_12hz"}
ACTIVITY_GROUPS = ("seated rest", "lying", "walking", "stress tests", "pedalling")
MAXIMUM_LAG_COUNT = 402


def activity_group(scenario):
    text = scenario.lower()
    if "sitting on armchair" in text:
        return "seated rest"
    if "laying on bed" in text:
        return "lying"
    if "stress test" in text:
        return "stress tests"
    if "walk" in text:
        return "walking"
    return "pedalling"


def envelope_name(configuration):
    return ENVELOPE_OF[(configuration.envelope_lowpass, float(configuration.envelope_lowpass_hz))]


def subject_split():
    """{subject: 'development' | 'test'}; subjects with a stress-test record and the others are shuffled
    separately with a fixed seed and dealt alternately, so both halves contain stress tests."""
    records = bpm_evaluate_public.usable_records()
    subjects = sorted({info.subject_id for info in records})
    stress = sorted({info.subject_id for info in records if "stress test" in info.scenario.lower()})
    others = [subject for subject in subjects if subject not in stress]
    generator = numpy.random.default_rng(SPLIT_SEED)
    split = {}
    offset = 0
    for stratum in (stress, others):
        order = list(generator.permutation(stratum))
        for index, subject in enumerate(order):
            split[str(subject)] = "development" if (index + offset) % 2 == 0 else "test"
        offset += len(order)
    return split


@numba.njit(cache=True)
def choose_batch(correlations, lag_weights, minimum_lag, maximum_lag, lag_count, choice_code, first_above_fraction,
                 half_check_fraction, submultiple_fraction, largest_divisor, envelope_rate_hz, clipped_share,
                 minimum_bpm, maximum_bpm, clipping_invalid_share, quality_threshold, minimum_rival_margin,
                 agreement_fraction, output):
    """Row-by-row equivalent of BPMEstimator._choose_peak_extended (rows with NaN = window not full).
    output columns: bpm, valid, quality, margin."""
    weighted = numpy.zeros(lag_count + 1, dtype=numpy.float32)
    peaks = numpy.zeros(lag_count + 1, dtype=numpy.int64)
    correlation = numpy.zeros(lag_count + 1, dtype=numpy.float32)
    previous_first = numpy.nan
    previous_second = numpy.nan
    for row in range(correlations.shape[0]):
        if numpy.isnan(correlations[row, 0]):
            output[row, 0] = numpy.nan
            output[row, 1] = 0.0
            output[row, 2] = 0.0
            output[row, 3] = 0.0
            continue
        for lag in range(lag_count + 1):
            correlation[lag] = correlations[row, lag]
            weighted[lag] = correlation[lag] * lag_weights[lag]
        chosen, rival = bpm_estimator._choose_lag(weighted, correlation, minimum_lag, maximum_lag, lag_count, choice_code,
                                                  first_above_fraction, half_check_fraction, submultiple_fraction,
                                                  largest_divisor, peaks)
        valid = True
        if chosen < 0:
            edge_lag = minimum_lag
            for lag in range(minimum_lag, maximum_lag + 1):
                if correlation[lag] > correlation[edge_lag]:
                    edge_lag = lag
            bpm = 60.0 * envelope_rate_hz / edge_lag
            quality = correlation[edge_lag]
            margin = 0.0
            valid = False
        else:
            previous_value = numpy.float64(correlation[chosen - 1])
            peak_value = numpy.float64(correlation[chosen])
            next_value = numpy.float64(correlation[chosen + 1])
            curvature = previous_value - 2.0 * peak_value + next_value
            offset = 0.5 * (previous_value - next_value) / curvature if curvature < 0 else 0.0
            bpm = 60.0 / ((chosen + offset) / envelope_rate_hz)
            quality = peak_value
            margin = peak_value - rival
            if bpm < minimum_bpm or bpm > maximum_bpm:
                valid = False
            elif clipped_share[row] > clipping_invalid_share:
                valid = False
            elif peak_value < quality_threshold:
                valid = False
            elif margin < minimum_rival_margin:
                valid = False
            elif agreement_fraction > 0.0:
                tolerance = agreement_fraction * bpm
                agrees = False
                if not numpy.isnan(previous_first) and abs(bpm - previous_first) <= tolerance:
                    agrees = True
                if not numpy.isnan(previous_second) and abs(bpm - previous_second) <= tolerance:
                    agrees = True
                valid = agrees
        previous_second = previous_first
        previous_first = bpm
        output[row, 0] = bpm
        output[row, 1] = 1.0 if valid else 0.0
        output[row, 2] = quality
        output[row, 3] = margin


def estimates_from_correlations(correlations, clipped_per_second, configuration):
    """Estimates per update row for any configuration that the extended path supports (highest, half_check,
    first_above, submultiple, harmonic_sum)."""
    estimator = bpm_estimator.BPMEstimator(replace(configuration, peak_choice="highest"), 16000.0)
    lag_count = estimator.correlation_lag_count
    if configuration.lag_weighting == "overlap":
        lags = numpy.arange(lag_count + 1, dtype=numpy.float32)
        weights = ((estimator.window_length - lags) / numpy.float32(estimator.window_length)).astype(numpy.float32)
    else:
        weights = numpy.ones(lag_count + 1, dtype=numpy.float32)
    clipped = numpy.asarray(clipped_per_second, dtype=numpy.float64)
    rows = correlations.shape[0]
    window_sum = numpy.convolve(clipped, numpy.ones(estimator.update_count_per_window), mode="full")[:clipped.shape[0]]
    clipped_share = numpy.zeros(rows)
    clipped_share[:min(rows, window_sum.shape[0])] = window_sum[:rows] / estimator.microphone_samples_per_window
    output = numpy.zeros((rows, 4))
    choose_batch(numpy.ascontiguousarray(correlations, dtype=numpy.float32), weights, estimator.minimum_lag,
                 min(estimator.maximum_lag, lag_count - 1), lag_count,
                 bpm_estimator.EXTENDED_PEAK_CHOICE_CODES[configuration.peak_choice], configuration.first_above_fraction,
                 configuration.half_check_fraction, configuration.submultiple_fraction,
                 configuration.submultiple_largest_divisor, float(estimator.envelope_rate_hz), clipped_share,
                 configuration.minimum_bpm, configuration.maximum_bpm, configuration.clipping_invalid_share,
                 configuration.quality_threshold, configuration.minimum_rival_margin, configuration.agreement_fraction,
                 output)
    return output


class RecordData:
    """Reference and cached correlations of one record and condition, aligned to ECG-reliable windows."""

    def __init__(self, info, condition):
        self.info = info
        self.condition = condition
        self.group = activity_group(info.scenario)
        reference = common.load_reference(info.record_name)
        self.reference = reference
        self.correlations = {}

    def load(self, identifier, envelope):
        key = (identifier, envelope)
        if key not in self.correlations:
            with numpy.load(compute.output_path(self.condition, self.info.record_name, identifier, envelope)) as archive:
                self.correlations[key] = (archive["correlation"].astype(numpy.float32), archive["end_time_seconds"],
                                          archive["clipped_per_second"])
        return self.correlations[key]

    def scored(self, identifier, configuration):
        """Arrays over ECG-reliable scored windows: reference, estimate, valid."""
        correlations, end_times, clipped = self.load(identifier, envelope_name(configuration))
        output = estimates_from_correlations(correlations, clipped, configuration)
        selected_rows, reference_values = [], []
        for row, end_time in enumerate(end_times):
            end = int(round(end_time))
            window = self.reference.get(end)
            if end < common.FIRST_SCORED_END_TIME_SECONDS or window is None or not window["reliable"]:
                continue
            selected_rows.append(row)
            reference_values.append(window["reference_bpm"])
        selected_rows = numpy.array(selected_rows, dtype=int)
        return (numpy.array(reference_values, dtype=float), output[selected_rows, 0], output[selected_rows, 1] > 0.5)


def records_for(subjects=None):
    excluded = common.duplicate_records_excluded()
    records = [info for info in bpm_evaluate_public.usable_records() if info.record_name not in excluded]
    if subjects is not None:
        records = [info for info in records if info.subject_id in subjects]
    return records


def window_measures(reference, estimate, valid):
    """Per-window columns used by every pooled metric."""
    finite = numpy.isfinite(estimate)
    absolute = numpy.where(finite, numpy.abs(estimate - reference), reference)
    tolerance = numpy.maximum(5.0, 0.1 * reference)
    ratio = numpy.where(finite, estimate / reference, 0.0)
    gross = absolute > 0.2 * reference
    half = gross & (numpy.abs(ratio / 0.5 - 1) <= 0.1)
    double = gross & (numpy.abs(ratio / 2.0 - 1) <= 0.1)
    third = gross & (numpy.abs(ratio * 3.0 - 1) <= 0.1)
    other = gross & ~half & ~double & ~third
    return {"absolute": absolute, "within": absolute <= tolerance, "gross": gross, "half": half, "double": double,
            "third": third, "other": other, "valid": valid.astype(bool)}


def pooled(measures, mask=None):
    if mask is not None:
        measures = {name: values[mask] for name, values in measures.items()}
    count = measures["absolute"].shape[0]
    if count == 0:
        return {"window_count": 0}
    valid = measures["valid"]
    result = {"window_count": count, "mae_bpm": float(measures["absolute"].mean()),
              "median_absolute_error_bpm": float(numpy.median(measures["absolute"])),
              "within_tolerance_share": float(measures["within"].mean()), "gross_share": float(measures["gross"].mean()),
              "gross_count": int(measures["gross"].sum()), "half_count": int(measures["half"].sum()),
              "third_count": int(measures["third"].sum()), "double_count": int(measures["double"].sum()),
              "other_count": int(measures["other"].sum()), "valid_share": float(valid.mean())}
    if valid.any():
        result["valid_mae_bpm"] = float(measures["absolute"][valid].mean())
        result["valid_gross_share"] = float(measures["gross"][valid].mean())
        result["valid_within_tolerance_share"] = float(measures["within"][valid].mean())
    else:
        result.update(valid_mae_bpm=float("nan"), valid_gross_share=float("nan"), valid_within_tolerance_share=float("nan"))
    result["target_met"] = bool(result["valid_share"] >= 0.9 and result["valid_mae_bpm"] <= 5.0)
    return result


def bootstrap_indices(subjects, count=BOOTSTRAP_COUNT, seed=BOOTSTRAP_SEED):
    generator = numpy.random.default_rng(seed)
    return generator.integers(0, len(subjects), size=(count, len(subjects)))


def subject_sums(measures, subject_index, subject_count):
    """Per subject: (window count, error sum, within count, gross count, valid count, valid error sum, valid gross)."""
    valid = measures["valid"]
    columns = [numpy.ones_like(measures["absolute"]), measures["absolute"], measures["within"].astype(float),
               measures["gross"].astype(float), valid.astype(float), measures["absolute"] * valid,
               (measures["gross"] & valid).astype(float)]
    return numpy.stack([numpy.bincount(subject_index, weights=column, minlength=subject_count) for column in columns], axis=1)


def bootstrap_interval(sums, resamples, statistic):
    totals = sums[resamples].sum(axis=1)
    values = statistic(totals)
    values = values[numpy.isfinite(values)]
    if values.size == 0:
        return (float("nan"), float("nan"))
    return (float(numpy.percentile(values, 2.5)), float(numpy.percentile(values, 97.5)))


STATISTICS = {"mae_bpm": lambda totals: totals[:, 1] / totals[:, 0],
              "within_tolerance_share": lambda totals: totals[:, 2] / totals[:, 0],
              "gross_share": lambda totals: totals[:, 3] / totals[:, 0],
              "valid_share": lambda totals: totals[:, 4] / totals[:, 0],
              "valid_mae_bpm": lambda totals: numpy.where(totals[:, 4] > 0, totals[:, 5] / numpy.maximum(totals[:, 4], 1), numpy.nan),
              "valid_gross_share": lambda totals: numpy.where(totals[:, 4] > 0, totals[:, 6] / numpy.maximum(totals[:, 4], 1), numpy.nan)}
