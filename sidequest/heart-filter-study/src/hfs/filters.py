"""Filter candidates for the listening and analysis paths, with float32 coefficients as the device holds them."""
from dataclasses import dataclass, field

import numpy
from scipy import signal

from .recordings import SAMPLE_RATE_HZ

FAMILIES = ("raw", "butterworth", "bessel", "chebyshev1", "chebyshev2", "elliptic", "fir", "decimated")
DECIMATED_RATE_HZ = 1000
DECIMATION_FACTOR = SAMPLE_RATE_HZ // DECIMATED_RATE_HZ
ANTI_ALIAS_TAP_COUNT = 64
FLOAT_BYTES = 4


@dataclass(frozen=True)
class FilterCandidate:
    identifier: str
    family: str
    description: str
    highpass_hz: float | None
    lowpass_hz: float | None
    highpass_order: int
    lowpass_order: int
    second_order_sections: numpy.ndarray | None = field(compare=False, repr=False)
    fir_coefficients: numpy.ndarray | None = field(compare=False, repr=False)
    gain: float = 1.0
    # Family "decimated": fir_coefficients is the anti-alias filter at 16 kHz, the sections run at
    # 16 kHz / decimation_factor and the output has that lower rate.
    decimation_factor: int = 1

    @property
    def output_rate_hz(self) -> float:
        return SAMPLE_RATE_HZ / self.decimation_factor


def _edge_text(value: float | None) -> str:
    return "none" if value is None else f"{value:g}".replace(".", "p")


def _prototype_sections(family, order, edge_hz, band_type, sample_rate_hz, passband_ripple_db, stopband_attenuation_db):
    if family == "butterworth":
        return signal.butter(order, edge_hz, band_type, fs=sample_rate_hz, output="sos")
    if family == "bessel":
        return signal.bessel(order, edge_hz, band_type, fs=sample_rate_hz, output="sos", norm="mag")
    if family == "chebyshev1":
        return signal.cheby1(order, passband_ripple_db, edge_hz, band_type, fs=sample_rate_hz, output="sos")
    if family == "elliptic":
        return signal.ellip(order, passband_ripple_db, stopband_attenuation_db, edge_hz, band_type,
                            fs=sample_rate_hz, output="sos")
    if family == "chebyshev2":
        return _chebyshev2_at_half_power(order, edge_hz, band_type, sample_rate_hz, stopband_attenuation_db)
    raise ValueError(f"unknown IIR family {family}")


def _chebyshev2_at_half_power(order, edge_hz, band_type, sample_rate_hz, stopband_attenuation_db):
    # SciPy places the Chebyshev II edge at the start of the stopband; move it so that the edge is the
    # -3 dB point like for the other families, otherwise "25 Hz" would mean a passband far above 25 Hz.
    target = 10 ** (-3.0103 / 20)
    nyquist = sample_rate_hz / 2
    low, high = (1e-3, edge_hz) if band_type == "highpass" else (edge_hz, nyquist * 0.999)
    sections = None
    for _ in range(60):
        middle = numpy.sqrt(low * high)
        sections = signal.cheby2(order, stopband_attenuation_db, middle, band_type, fs=sample_rate_hz, output="sos")
        _, response = signal.sosfreqz(sections, worN=[edge_hz], fs=sample_rate_hz)
        magnitude = abs(response[0])
        if band_type == "highpass":
            if magnitude > target:
                low = middle
            else:
                high = middle
        else:
            if magnitude > target:
                high = middle
            else:
                low = middle
    return sections


def raw_candidate() -> FilterCandidate:
    return FilterCandidate("raw", "raw", "no filter", None, None, 0, 0, None, None)


def design_filter(family, highpass_hz, lowpass_hz, highpass_order=2, lowpass_order=2, *, passband_ripple_db=0.5,
                  stopband_attenuation_db=40.0, fir_tap_count=None, gain=1.0) -> FilterCandidate:
    if family == "raw" or (highpass_hz is None and lowpass_hz is None):
        return raw_candidate()
    gain_text = "" if gain == 1.0 else f"_gain{_edge_text(gain)}"
    if family == "fir":
        return _design_fir(highpass_hz, lowpass_hz, fir_tap_count or 129, gain, gain_text)
    sample_rate_hz = SAMPLE_RATE_HZ
    decimation_factor = 1
    fir_coefficients = None
    family_for_sections = family
    if family == "decimated":
        if lowpass_hz is not None and lowpass_hz >= DECIMATED_RATE_HZ * 0.4:
            raise ValueError("decimated design needs a low-pass edge below 400 Hz")
        sample_rate_hz = DECIMATED_RATE_HZ
        decimation_factor = DECIMATION_FACTOR
        family_for_sections = "butterworth"
        fir_coefficients = signal.firwin(ANTI_ALIAS_TAP_COUNT, 0.4 * DECIMATED_RATE_HZ, fs=SAMPLE_RATE_HZ,
                                         window=("kaiser", 6.0)).astype(numpy.float32)
    sections = []
    if highpass_hz is not None:
        sections.append(_prototype_sections(family_for_sections, highpass_order, highpass_hz, "highpass",
                                            sample_rate_hz, passband_ripple_db, stopband_attenuation_db))
    if lowpass_hz is not None:
        sections.append(_prototype_sections(family_for_sections, lowpass_order, lowpass_hz, "lowpass",
                                            sample_rate_hz, passband_ripple_db, stopband_attenuation_db))
    second_order_sections = numpy.vstack(sections).astype(numpy.float32)
    highpass_order_used = highpass_order if highpass_hz is not None else 0
    lowpass_order_used = lowpass_order if lowpass_hz is not None else 0
    identifier = (f"{family}_hp{highpass_order_used}_{_edge_text(highpass_hz)}"
                  f"_lp{lowpass_order_used}_{_edge_text(lowpass_hz)}{gain_text}")
    parts = []
    if highpass_hz is not None:
        parts.append(f"order-{highpass_order} high-pass at {highpass_hz:g} Hz")
    if lowpass_hz is not None:
        parts.append(f"order-{lowpass_order} low-pass at {lowpass_hz:g} Hz")
    family_text = {"butterworth": "Butterworth", "bessel": "Bessel", "chebyshev1": f"Chebyshev I ({passband_ripple_db:g} dB ripple)",
                   "chebyshev2": f"Chebyshev II ({stopband_attenuation_db:g} dB stopband, edge at -3 dB)",
                   "elliptic": f"elliptic ({passband_ripple_db:g} dB / {stopband_attenuation_db:g} dB)",
                   "decimated": "Butterworth at 1 kHz after a 64-tap anti-alias FIR and decimation by 16"}[family]
    description = f"{family_text}: " + " then ".join(parts)
    if gain != 1.0:
        description += f", make-up gain {gain:g}"
    return FilterCandidate(identifier, family, description, highpass_hz, lowpass_hz, highpass_order_used,
                           lowpass_order_used, second_order_sections, fir_coefficients, float(gain), decimation_factor)


def _design_fir(highpass_hz, lowpass_hz, tap_count, gain, gain_text):
    if tap_count % 2 == 0:
        raise ValueError("linear-phase FIR with a high-pass part needs an odd tap count")
    if highpass_hz is not None and lowpass_hz is not None:
        taps = signal.firwin(tap_count, [highpass_hz, lowpass_hz], pass_zero=False, fs=SAMPLE_RATE_HZ, window="hamming")
    elif highpass_hz is not None:
        taps = signal.firwin(tap_count, highpass_hz, pass_zero=False, fs=SAMPLE_RATE_HZ, window="hamming")
    else:
        taps = signal.firwin(tap_count, lowpass_hz, fs=SAMPLE_RATE_HZ, window="hamming")
    identifier = f"fir{tap_count}_hp_{_edge_text(highpass_hz)}_lp_{_edge_text(lowpass_hz)}{gain_text}"
    description = (f"linear-phase Hamming-window FIR, {tap_count} taps, pass band "
                   f"{'0' if highpass_hz is None else f'{highpass_hz:g}'}-{'8000' if lowpass_hz is None else f'{lowpass_hz:g}'} Hz")
    return FilterCandidate(identifier, "fir", description, highpass_hz, lowpass_hz, 0, 0, None,
                           taps.astype(numpy.float32), float(gain))


def frequency_response(candidate: FilterCandidate, frequencies_hz) -> numpy.ndarray:
    """Complex response of the float32 coefficients; for decimated designs aliasing is ignored."""
    frequencies_hz = numpy.atleast_1d(numpy.asarray(frequencies_hz, dtype=float))
    response = numpy.ones(frequencies_hz.shape, dtype=complex) * candidate.gain
    if candidate.fir_coefficients is not None:
        _, fir_response = signal.freqz(candidate.fir_coefficients.astype(numpy.float64), worN=frequencies_hz, fs=SAMPLE_RATE_HZ)
        response *= fir_response
    if candidate.second_order_sections is not None:
        rate = candidate.output_rate_hz
        inside = frequencies_hz < rate / 2
        section_response = numpy.zeros(frequencies_hz.shape, dtype=complex)
        _, section_response[inside] = signal.sosfreqz(candidate.second_order_sections.astype(numpy.float64),
                                                       worN=frequencies_hz[inside], fs=rate)
        response *= section_response
    return response


def group_delay_seconds(candidate: FilterCandidate, frequencies_hz) -> numpy.ndarray:
    frequencies_hz = numpy.atleast_1d(numpy.asarray(frequencies_hz, dtype=float))
    delay = numpy.zeros(frequencies_hz.shape)
    if candidate.fir_coefficients is not None:
        delay += (len(candidate.fir_coefficients) - 1) / 2 / SAMPLE_RATE_HZ
    if candidate.second_order_sections is not None:
        rate = candidate.output_rate_hz
        inside = frequencies_hz < rate / 2
        for section in candidate.second_order_sections.astype(numpy.float64):
            _, samples_delay = signal.group_delay((section[:3], section[3:]), w=frequencies_hz[inside], fs=rate)
            delay[inside] += samples_delay / rate
        delay[~inside] = numpy.nan
    return delay


def _section_multiplies(section) -> int:
    nonzero = numpy.count_nonzero(section[[0, 1, 2, 4, 5]])
    return int(nonzero)


def cost(candidate: FilterCandidate) -> dict:
    """Per input sample at 16 kHz; FIR counted in direct form without exploiting symmetry."""
    multiplies = 0.0
    state_bytes = 0
    coefficient_bytes = 0
    if candidate.family == "decimated":
        multiplies += len(candidate.fir_coefficients) / candidate.decimation_factor
        state_bytes += len(candidate.fir_coefficients) * FLOAT_BYTES
        coefficient_bytes += len(candidate.fir_coefficients) * FLOAT_BYTES
        section_multiplies = sum(_section_multiplies(section) for section in candidate.second_order_sections)
        multiplies += section_multiplies / candidate.decimation_factor
        state_bytes += 2 * FLOAT_BYTES * len(candidate.second_order_sections)
        coefficient_bytes += 5 * FLOAT_BYTES * len(candidate.second_order_sections)
    else:
        if candidate.fir_coefficients is not None:
            multiplies += len(candidate.fir_coefficients)
            state_bytes += len(candidate.fir_coefficients) * FLOAT_BYTES
            coefficient_bytes += len(candidate.fir_coefficients) * FLOAT_BYTES
        if candidate.second_order_sections is not None:
            multiplies += sum(_section_multiplies(section) for section in candidate.second_order_sections)
            state_bytes += 2 * FLOAT_BYTES * len(candidate.second_order_sections)
            coefficient_bytes += 5 * FLOAT_BYTES * len(candidate.second_order_sections)
    if candidate.gain != 1.0:
        multiplies += 1
        coefficient_bytes += FLOAT_BYTES
    return {"multiplies_per_sample": int(numpy.ceil(multiplies)), "state_bytes": int(state_bytes),
            "coefficient_bytes": int(coefficient_bytes)}
