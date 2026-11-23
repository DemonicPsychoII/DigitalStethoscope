"""Shared analysis for the listening-filter study: weightings, loudness, segments, gains, figures style."""
import json
import sys
from pathlib import Path

import numpy
from scipy import signal

SOURCE_DIRECTORY = Path(__file__).resolve().parent
if str(SOURCE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIRECTORY))

STUDY_DIRECTORY = SOURCE_DIRECTORY.parent
LISTENING_DIRECTORY = STUDY_DIRECTORY / "listening"
FIGURES_DIRECTORY = LISTENING_DIRECTORY / "figures"
CACHE_DIRECTORY = LISTENING_DIRECTORY / "cache"
REFERENCE_DIRECTORY = STUDY_DIRECTORY / "reference"

FULL_SCALE = 8388608.0
SAMPLE_MAXIMUM = 8388607
SAMPLE_MINIMUM = -8388608
SAFETY_MARGIN_DB = 0.01
SATURATION_SHARE_LIMIT = 1e-4
FRAME_SECONDS = 0.020
ISO226_PHON_LEVEL = 60.0

from hfs.recordings import RECORDING_NAMES, SAMPLE_RATE_HZ, DISCARDED_SECONDS, load_recording  # noqa: E402,F401
from hfs.filters import design_filter, raw_candidate, frequency_response, group_delay_seconds, cost  # noqa: E402,F401
from hfs.device_chain import apply_filter_blockwise, apply_volume_and_saturate, count_clipped  # noqa: E402,F401


def database(power: numpy.ndarray | float) -> numpy.ndarray | float:
    return 10.0 * numpy.log10(numpy.maximum(power, 1e-30))


def to_full_scale(dac_values: numpy.ndarray) -> numpy.ndarray:
    return dac_values.astype(numpy.float64) / FULL_SCALE


def bilinear_second_order_sections(zeros, poles, gain, sample_rate_hz):
    digital_zeros, digital_poles, digital_gain = signal.bilinear_zpk(zeros, poles, gain, sample_rate_hz)
    return signal.zpk2sos(digital_zeros, digital_poles, digital_gain)


def a_weighting_sections(sample_rate_hz: float = 16000.0) -> numpy.ndarray:
    """IEC 61672-1 A-weighting, analog pole frequencies 20.6, 107.7, 737.9, 12194 Hz, bilinear transform,
    normalised to 0 dB at 1 kHz."""
    pole_frequencies = numpy.array([20.598997, 20.598997, 107.65265, 737.86223, 12194.217, 12194.217])
    poles = -2.0 * numpy.pi * pole_frequencies
    zeros = numpy.zeros(4)
    sections = bilinear_second_order_sections(zeros, poles, 1.0, sample_rate_hz)
    _, response = signal.sosfreqz(sections, worN=[1000.0], fs=sample_rate_hz)
    sections[0, :3] /= numpy.abs(response[0])
    return sections


def k_weighting_sections(sample_rate_hz: float = 16000.0) -> numpy.ndarray:
    """ITU-R BS.1770-4 K-weighting (pre-filter shelf and RLB high-pass) re-derived for the sample rate from the
    analog parameters behind the 48 kHz coefficients of the recommendation."""
    shelf_gain_db, shelf_q, shelf_frequency = 3.999843853973347, 0.7071752369554196, 1681.974450955533
    gain_linear = 10.0 ** (shelf_gain_db / 20.0)
    warped = numpy.tan(numpy.pi * shelf_frequency / sample_rate_hz)
    root = gain_linear ** 0.4996667741545416
    denominator = 1.0 + warped / shelf_q + warped ** 2
    shelf = [(gain_linear + root * warped / shelf_q + warped ** 2) / denominator,
             2.0 * (warped ** 2 - gain_linear) / denominator,
             (gain_linear - root * warped / shelf_q + warped ** 2) / denominator,
             1.0,
             2.0 * (warped ** 2 - 1.0) / denominator,
             (1.0 - warped / shelf_q + warped ** 2) / denominator]
    highpass_q, highpass_frequency = 0.5003270373238773, 38.13547087602444
    warped = numpy.tan(numpy.pi * highpass_frequency / sample_rate_hz)
    denominator = 1.0 + warped / highpass_q + warped ** 2
    highpass = [1.0, -2.0, 1.0, 1.0,
                2.0 * (warped ** 2 - 1.0) / denominator,
                (1.0 - warped / highpass_q + warped ** 2) / denominator]
    return numpy.array([shelf, highpass])


A_WEIGHTING = a_weighting_sections()
K_WEIGHTING = k_weighting_sections()

ISO226_FREQUENCIES_HZ = numpy.array([20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800,
                                     1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000, 12500])
ISO226_EXPONENT = numpy.array([0.532, 0.506, 0.480, 0.455, 0.432, 0.409, 0.387, 0.367, 0.349, 0.330, 0.315, 0.301,
                               0.288, 0.276, 0.267, 0.259, 0.253, 0.250, 0.246, 0.244, 0.243, 0.243, 0.243, 0.242,
                               0.242, 0.245, 0.254, 0.271, 0.301])
ISO226_MAGNITUDE_DB = numpy.array([-31.6, -27.2, -23.0, -19.1, -15.9, -13.0, -10.3, -8.1, -6.2, -4.5, -3.1, -2.0,
                                   -1.1, -0.4, 0.0, 0.3, 0.5, 0.0, -2.7, -4.1, -1.0, 1.7, 2.5, 1.2, -2.1, -7.1,
                                   -11.2, -10.7, -3.1])
ISO226_THRESHOLD_DB = numpy.array([78.5, 68.7, 59.5, 51.1, 44.0, 37.5, 31.5, 26.5, 22.1, 17.9, 14.4, 11.4, 8.6, 6.2,
                                   4.4, 3.0, 2.2, 2.4, 3.5, 1.7, -1.3, -4.2, -6.0, -5.4, -1.5, 6.0, 12.6, 13.9, 12.3])


def iso226_contour_db(phon: float) -> numpy.ndarray:
    """Sound pressure level (dB) of the ISO 226:2003 equal-loudness contour at the table frequencies."""
    term = (4.47e-3 * (10.0 ** (0.025 * phon) - 1.15)
            + (0.4 * 10.0 ** ((ISO226_THRESHOLD_DB + ISO226_MAGNITUDE_DB) / 10.0 - 9.0)) ** ISO226_EXPONENT)
    return 10.0 / ISO226_EXPONENT * numpy.log10(term) - ISO226_MAGNITUDE_DB + 94.0


def iso226_weighting_db(frequencies_hz: numpy.ndarray, phon: float = ISO226_PHON_LEVEL) -> numpy.ndarray:
    """Weighting = inverse equal-loudness contour relative to 1 kHz; below 20 Hz extrapolated at the 20-25 Hz slope,
    which makes infrasound strongly suppressed rather than ignored."""
    contour = iso226_contour_db(phon)
    relative = -(contour - contour[ISO226_FREQUENCIES_HZ == 1000][0])
    logarithmic_frequencies = numpy.log10(ISO226_FREQUENCIES_HZ)
    query = numpy.log10(numpy.maximum(frequencies_hz, 1.0))
    weighting = numpy.interp(query, logarithmic_frequencies, relative)
    slope = (relative[1] - relative[0]) / (logarithmic_frequencies[1] - logarithmic_frequencies[0])
    below = query < logarithmic_frequencies[0]
    weighting[below] = relative[0] + slope * (query[below] - logarithmic_frequencies[0])
    above = query > logarithmic_frequencies[-1]
    weighting[above] = relative[-1]
    return weighting


def weighted(samples_full_scale: numpy.ndarray, sections: numpy.ndarray) -> numpy.ndarray:
    return signal.sosfilt(sections, samples_full_scale)


def bs1770_block_powers(k_weighted: numpy.ndarray, sample_rate_hz: float = 16000.0) -> numpy.ndarray:
    block = int(round(0.400 * sample_rate_hz))
    hop = block // 4
    squared = numpy.concatenate([[0.0], numpy.cumsum(k_weighted.astype(numpy.float64) ** 2)])
    starts = numpy.arange(0, len(k_weighted) - block + 1, hop)
    return (squared[starts + block] - squared[starts]) / block


def bs1770_loudness(block_powers: numpy.ndarray, gain_db: float = 0.0) -> tuple[float, float]:
    """Gated integrated loudness and ungated loudness (LUFS, 1.0 = digital full scale) of a mono signal from its
    400 ms block powers, optionally scaled by a gain."""
    powers = block_powers * 10.0 ** (gain_db / 10.0)
    ungated = -0.691 + database(powers.mean()) if len(powers) else float("nan")
    loudness = -0.691 + database(powers)
    absolute = powers[loudness > -70.0]
    if len(absolute) == 0:
        return float("nan"), ungated
    relative_threshold = -0.691 + database(absolute.mean()) - 10.0
    gated = powers[loudness > max(-70.0, relative_threshold)]
    return float(-0.691 + database(gated.mean())), float(ungated)


def frame_powers(samples: numpy.ndarray, frame_samples: int) -> numpy.ndarray:
    count = len(samples) // frame_samples
    framed = samples[:count * frame_samples].astype(numpy.float64).reshape(count, frame_samples)
    return (framed ** 2).mean(axis=1)


def load_reference_beats(name: str) -> list[float] | None:
    path = REFERENCE_DIRECTORY / f"{name}.json"
    if not path.exists():
        return None
    try:
        beats = json.loads(path.read_text(encoding="utf-8")).get("beat_times_s")
    except (json.JSONDecodeError, OSError):
        return None
    return [float(value) for value in beats] if beats else None


def segment_frames(samples_int24: numpy.ndarray, name: str, sample_rate_hz: int) -> dict:
    """Boolean masks of 20 ms frames: heart sounds and between beats. Computed from the input once per recording so
    every candidate is measured on the same frames.

    Envelope: zero-phase 25-150 Hz Butterworth band-pass of the input, frame RMS. Heart sounds are the loudest 30 % of
    frames. Without reference beats the quietest 30 % are the between-beat background. With reference beats (S1 times)
    heart-sound frames are further restricted to [S1 - 60 ms, S1 + 0.70 RR) so movement noise in late diastole is not
    counted as heart sound, and between-beat frames are the late-diastole interval [S1 + 0.70 RR, next S1 - 60 ms)."""
    frame_samples = int(round(FRAME_SECONDS * sample_rate_hz))
    band = signal.butter(4, [25.0, 150.0], btype="bandpass", fs=sample_rate_hz, output="sos")
    envelope = numpy.sqrt(frame_powers(signal.sosfiltfilt(band, samples_int24 / FULL_SCALE), frame_samples))
    loud = envelope >= numpy.quantile(envelope, 0.70)
    quiet = envelope <= numpy.quantile(envelope, 0.30)
    beats = load_reference_beats(name)
    frame_centres = DISCARDED_SECONDS + (numpy.arange(len(envelope)) + 0.5) * FRAME_SECONDS
    if beats is None or len(beats) < 3:
        return {"heart": loud, "between": quiet, "source": "self-derived envelope (no reference beats)"}
    beats = numpy.asarray(sorted(beats))
    systole = numpy.zeros(len(envelope), dtype=bool)
    diastole = numpy.zeros(len(envelope), dtype=bool)
    for current, following in zip(beats[:-1], beats[1:]):
        period = following - current
        if not 0.25 <= period <= 2.0:
            continue
        systole |= (frame_centres >= current - 0.060) & (frame_centres < current + 0.70 * period)
        diastole |= (frame_centres >= current + 0.70 * period) & (frame_centres < following - 0.060)
    return {"heart": loud & systole, "between": diastole, "source": "reference beat times (reference/<name>.json)"}


def frame_samples_count(sample_rate_hz: int) -> int:
    return int(round(FRAME_SECONDS * sample_rate_hz))


def mask_samples(mask: numpy.ndarray, sample_count: int, frame_samples: int) -> numpy.ndarray:
    expanded = numpy.repeat(mask, frame_samples)
    full = numpy.zeros(sample_count, dtype=bool)
    full[:len(expanded)] = expanded[:sample_count]
    return full


def zero_saturation_gain_db(filtered_full_scale: numpy.ndarray) -> float:
    """Largest gain (dB, with a 0.01 dB margin) for which no output sample reaches the 24-bit limits."""
    peak = float(numpy.max(numpy.abs(filtered_full_scale)))
    return -20.0 * numpy.log10(max(peak, 1e-12)) - SAFETY_MARGIN_DB


def share_saturation_gain_db(filtered_full_scale: numpy.ndarray, share: float = SATURATION_SHARE_LIMIT) -> float:
    """Largest gain (dB, 0.01 dB margin) for which at most the given share of samples reaches the limits."""
    magnitudes = numpy.abs(filtered_full_scale)
    allowed = int(numpy.floor(share * len(magnitudes)))
    threshold = numpy.partition(magnitudes, len(magnitudes) - 1 - allowed)[len(magnitudes) - 1 - allowed]
    return -20.0 * numpy.log10(max(float(threshold), 1e-12)) - SAFETY_MARGIN_DB


def apply_gain_and_output(filtered_full_scale: numpy.ndarray, gain_db: float) -> numpy.ndarray:
    scaled = (filtered_full_scale * numpy.float32(10.0 ** (gain_db / 20.0))).astype(numpy.float32)
    return apply_volume_and_saturate(scaled, volume_percent=100)


def candidate_from_entry(entry: dict):
    if entry.get("family", "raw") == "raw":
        return raw_candidate()
    return design_filter(entry["family"], entry.get("highpass_hz"), entry.get("lowpass_hz"),
                         highpass_order=entry.get("highpass_order", 2), lowpass_order=entry.get("lowpass_order", 2),
                         **({"passband_ripple_db": entry["passband_ripple_db"]} if "passband_ripple_db" in entry else {}))


BACKGROUND_COLOUR = "#0f1419"
TEXT_COLOUR = "#e6e6e6"
GRID_COLOUR = "#2a3440"


def apply_dark_style() -> None:
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot
    pyplot.rcParams.update({
        "figure.facecolor": BACKGROUND_COLOUR, "axes.facecolor": BACKGROUND_COLOUR, "savefig.facecolor": BACKGROUND_COLOUR,
        "axes.edgecolor": "#6b7785", "axes.labelcolor": TEXT_COLOUR, "text.color": TEXT_COLOUR,
        "xtick.color": TEXT_COLOUR, "ytick.color": TEXT_COLOUR, "grid.color": GRID_COLOUR, "grid.linewidth": 0.6,
        "axes.grid": True, "legend.facecolor": "#161d26", "legend.edgecolor": "#3a4654", "font.size": 10,
        "axes.prop_cycle": matplotlib.cycler(color=["#5aa9e6", "#f2a541", "#7bd389", "#e86a92", "#b18cf2", "#f25f5c",
                                                     "#4fd1c5", "#ffd166", "#c0c0c0"]),
    })


def hertz_axis(axis, minimum_hz: float, maximum_hz: float) -> None:
    from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter
    axis.set_xscale("log")
    axis.set_xlim(minimum_hz, maximum_hz)
    candidates = [5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 8000, 10000]
    ticks = [value for value in candidates if minimum_hz <= value <= maximum_hz]
    axis.xaxis.set_major_locator(FixedLocator(ticks))
    axis.xaxis.set_major_formatter(FuncFormatter(
        lambda value, _: f"{value / 1000:g} kHz" if value >= 1000 else f"{value:g} Hz"))
    axis.xaxis.set_minor_formatter(NullFormatter())
    axis.set_xlabel("Frequency")


MOVEMENT_ARTEFACT_WINDOWS_S = {"rest-1": [(39.3, 40.5)]}


def outside_artefact_mask(name: str, sample_count: int) -> numpy.ndarray:
    """True for samples outside the known movement artefact (file-start times), including filter settling after it."""
    keep = numpy.ones(sample_count, dtype=bool)
    for start_s, stop_s in MOVEMENT_ARTEFACT_WINDOWS_S.get(name, []):
        first = max(0, int((start_s - DISCARDED_SECONDS) * SAMPLE_RATE_HZ))
        last = min(sample_count, int((stop_s - DISCARDED_SECONDS) * SAMPLE_RATE_HZ))
        keep[first:last] = False
    return keep
