"""Listening samples for the shortlisted listening filters, driven by listening/shortlist.json, for the own recordings
and for the public murmur excerpts listed in recordings-public/excerpts.json.

Writes listening/samples/<excerpt>/<variant>/<identifier>.wav (PCM 24-bit, the DAC word),
listening/samples_web/<excerpt>/<variant>/<identifier>.flac (lossless FLAC of PCM 16-bit with triangular dither),
listening/samples/index.json and listening/samples/README.md. Files not listed by the current shortlist are removed.
"""
import json
import zlib

import numpy
import soundfile

import listening_common as common
from listening_common import (RECORDING_NAMES, SAMPLE_RATE_HZ, DISCARDED_SECONDS, LISTENING_DIRECTORY, database,
                              load_recording, apply_filter_blockwise, apply_gain_and_output, count_clipped,
                              candidate_from_entry)

SAMPLES_DIRECTORY = LISTENING_DIRECTORY / "samples"
WEB_DIRECTORY = LISTENING_DIRECTORY / "samples_web"
SHORTLIST_PATH = LISTENING_DIRECTORY / "shortlist.json"
PUBLIC_EXCERPTS_PATH = common.STUDY_DIRECTORY / "recordings-public" / "excerpts.json"
FADE_SECONDS = 0.020
VARIANTS = ("device", "madeup", "matched")
PUBLIC_VARIANTS = ("madeup", "matched")
PUBLIC_SOURCE = "CirCor DigiScope 1.0.3 through the capture-chain model"


def fade_window(sample_count: int) -> numpy.ndarray:
    fade_samples = int(round(FADE_SECONDS * SAMPLE_RATE_HZ))
    window = numpy.ones(sample_count)
    ramp = 0.5 - 0.5 * numpy.cos(numpy.pi * (numpy.arange(fade_samples) + 0.5) / fade_samples)
    window[:fade_samples] = ramp
    window[-fade_samples:] = ramp[::-1]
    return window


def apply_fades(dac_values: numpy.ndarray) -> numpy.ndarray:
    return numpy.rint(dac_values.astype(numpy.float64) * fade_window(len(dac_values))).astype(numpy.int32)


def dithered_16_bit(dac_values: numpy.ndarray, seed_text: str) -> numpy.ndarray:
    generator = numpy.random.default_rng(zlib.crc32(seed_text.encode("utf-8")))
    triangular = generator.random(len(dac_values)) - generator.random(len(dac_values))
    values = numpy.rint(dac_values.astype(numpy.float64) / 256.0 + triangular)
    return numpy.clip(values, -32768, 32767).astype(numpy.int16)


def write_24_bit(path, dac_values: numpy.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    soundfile.write(path, (dac_values.astype(numpy.int32) << 8), SAMPLE_RATE_HZ, subtype="PCM_24")


def write_16_bit_flac(path, values: numpy.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    soundfile.write(path, values, SAMPLE_RATE_HZ, format="FLAC", subtype="PCM_16")


def load_public_capture(path) -> numpy.ndarray:
    """24-bit sample values of a capture-equivalent public excerpt. Unlike the own recordings nothing is discarded:
    the file holds no device start-up."""
    left_aligned, sample_rate = soundfile.read(path, dtype="int32")
    if sample_rate != SAMPLE_RATE_HZ or left_aligned.ndim != 1:
        raise ValueError(f"{path}: expected mono {SAMPLE_RATE_HZ} Hz, got {sample_rate} Hz, shape {left_aligned.shape}")
    return (left_aligned >> 8).astype(numpy.int32)


def public_excerpts() -> list:
    """Excerpts of recordings-public/excerpts.json whose capture file exists. An optional excerpt that has been written
    is named after its folder, because the optional entries share one label."""
    if not PUBLIC_EXCERPTS_PATH.exists():
        return []
    document = json.loads(PUBLIC_EXCERPTS_PATH.read_text(encoding="utf-8"))
    found, seen_paths = [], set()
    for list_name in ("excerpts", "diastolic_options"):
        for excerpt in document.get(list_name, []):
            if not excerpt.get("file"):
                continue
            capture = (common.STUDY_DIRECTORY / excerpt["file"]).resolve()
            if not capture.exists() or capture in seen_paths:
                continue
            seen_paths.add(capture)
            label = excerpt["label"] if list_name == "excerpts" else capture.parent.name
            found.append({**excerpt, "label": label, "path": capture})
    return found


def excerpt_levels(dac_values: numpy.ndarray) -> dict:
    full_scale = common.to_full_scale(dac_values)
    gated, ungated = common.bs1770_loudness(common.bs1770_block_powers(common.weighted(full_scale, common.K_WEIGHTING)))
    return {"output_peak_dbfs": round(20.0 * numpy.log10(max(float(numpy.max(numpy.abs(full_scale))), 1e-12)), 3),
            "a_weighted_level_db": round(float(database(numpy.mean(common.weighted(full_scale, common.A_WEIGHTING) ** 2))), 3),
            "k_loudness_gated_lufs": round(gated, 3), "k_loudness_ungated_lufs": round(ungated, 3)}


def remove_previous_output() -> None:
    for directory in (SAMPLES_DIRECTORY, WEB_DIRECTORY):
        if not directory.exists():
            continue
        for audio_file in [*directory.rglob("*.wav"), *directory.rglob("*.flac")]:
            audio_file.unlink()
        for child in sorted(directory.rglob("*"), key=lambda path: len(path.parts), reverse=True):
            if child.is_dir() and not any(child.iterdir()):
                child.rmdir()
    index = SAMPLES_DIRECTORY / "index.json"
    if index.exists():
        index.unlink()


def load_candidates(entries: list, recordings: dict) -> list:
    candidates = []
    for entry in entries:
        candidate = candidate_from_entry({key: value for key, value in entry.items() if key not in ("identifier", "label")})
        if entry.get("identifier") and entry["identifier"] != candidate.identifier:
            raise ValueError(f"shortlist identifier {entry['identifier']} does not match design {candidate.identifier}")
        filtered = {name: apply_filter_blockwise(candidate, samples) for name, samples in recordings.items()}
        safe_gain = min(common.zero_saturation_gain_db(values) for values in filtered.values())
        candidates.append({"candidate": candidate, "label": entry.get("label", candidate.description),
                           "filtered": filtered, "safe_gain_db": safe_gain})
    return candidates


def write_excerpt(label: str, input_samples: numpy.ndarray, filtered_by_identifier: dict, start: int, stop: int,
                  candidates: list, variants: tuple, details: dict, files: list, checks: list) -> None:
    """Writes every variant of every candidate for one excerpt. input_samples and the filtered signals cover the
    whole source, so the filter state at the cut is the one the device would have; start and stop select the excerpt."""
    input_excerpt = input_samples[start:stop]
    input_clipped = count_clipped(input_excerpt)
    loudness_at_unity, clip_free_gain = {}, {}
    for item in candidates:
        identifier = item["candidate"].identifier
        filtered_excerpt = filtered_by_identifier[identifier][start:stop].astype(numpy.float64)
        block_powers = common.bs1770_block_powers(common.weighted(filtered_excerpt, common.K_WEIGHTING))
        loudness_at_unity[identifier] = common.bs1770_loudness(block_powers)[0]
        clip_free_gain[identifier] = common.zero_saturation_gain_db(filtered_excerpt)
    target_loudness = min(loudness_at_unity[key] + clip_free_gain[key] for key in loudness_at_unity)
    for item in candidates:
        identifier = item["candidate"].identifier
        gains = {"device": 0.0, "madeup": item["safe_gain_db"],
                 "matched": target_loudness - loudness_at_unity[identifier]}
        for variant in variants:
            dac_values = apply_gain_and_output(filtered_by_identifier[identifier], gains[variant])[start:stop]
            clipped = count_clipped(dac_values)
            faded = apply_fades(dac_values)
            relative = f"{label}/{variant}/{identifier}.wav"
            web_relative = f"{label}/{variant}/{identifier}.flac"
            write_24_bit(SAMPLES_DIRECTORY / relative, faded)
            # The dither seed stays the .wav path so the 16-bit values equal those of the earlier 16-bit WAV files.
            write_16_bit_flac(WEB_DIRECTORY / web_relative, dithered_16_bit(faded, relative))
            files.append({"excerpt": label, **details, "variant": variant, "identifier": identifier,
                          "label": item["label"], "description": item["candidate"].description,
                          "file_24_bit": f"samples/{relative}", "file_16_bit_web": f"samples_web/{web_relative}",
                          "applied_gain_db": round(gains[variant], 3),
                          "clipped_samples": clipped, "input_clipped_samples": input_clipped,
                          **excerpt_levels(faded)})
            if variant != "device" and clipped > input_clipped:
                checks.append(f"{relative}: {clipped} clipped samples, input excerpt had {input_clipped}")


def main() -> None:
    shortlist = json.loads(SHORTLIST_PATH.read_text(encoding="utf-8"))
    excerpts, entries = shortlist["excerpts"], shortlist["candidates"]
    labels = [excerpt["label"] for excerpt in excerpts]
    if len(set(labels)) != len(labels):
        raise ValueError("excerpt labels must be unique")
    recordings = {name: load_recording(name) for name in RECORDING_NAMES}
    candidates = load_candidates(entries, recordings)

    remove_previous_output()
    SAMPLES_DIRECTORY.mkdir(parents=True, exist_ok=True)
    files, checks = [], []
    for excerpt in excerpts:
        name = excerpt["recording"]
        start = int(round((excerpt["start_s"] - DISCARDED_SECONDS) * SAMPLE_RATE_HZ))
        stop = start + int(round(excerpt["duration_s"] * SAMPLE_RATE_HZ))
        if start < 0 or stop > len(recordings[name]):
            raise ValueError(f"excerpt {excerpt['label']} lies outside {name}")
        filtered_by_identifier = {item["candidate"].identifier: item["filtered"][name] for item in candidates}
        write_excerpt(excerpt["label"], recordings[name], filtered_by_identifier, start, stop, candidates, VARIANTS,
                      {"recording": name, "start_s": excerpt["start_s"], "duration_s": excerpt["duration_s"]},
                      files, checks)
        raw_device = SAMPLES_DIRECTORY / f"{excerpt['label']}/device/raw.wav"
        if raw_device.exists():
            written, _ = soundfile.read(raw_device, dtype="int32")
            fade_samples = int(round(FADE_SECONDS * SAMPLE_RATE_HZ))
            identical = numpy.array_equal(written[fade_samples:-fade_samples] >> 8,
                                          recordings[name][start:stop][fade_samples:-fade_samples])
            checks.append(f"{excerpt['label']}: device/raw.wav equals the input excerpt sample for sample outside the "
                          f"fades: {'yes' if identical else 'NO'}")
    used_labels = set(labels)
    for excerpt in public_excerpts():
        if excerpt["label"] in used_labels:
            raise ValueError(f"public excerpt label {excerpt['label']} is already used")
        used_labels.add(excerpt["label"])
        capture = load_public_capture(excerpt["path"])
        filtered_by_identifier = {item["candidate"].identifier: apply_filter_blockwise(item["candidate"], capture)
                                  for item in candidates}
        write_excerpt(excerpt["label"], capture, filtered_by_identifier, 0, len(capture), candidates, PUBLIC_VARIANTS,
                      {"recording": excerpt.get("file_stem", excerpt["label"]), "source": PUBLIC_SOURCE, "start_s": excerpt["start_s"],
                       "duration_s": round(len(capture) / SAMPLE_RATE_HZ, 3)},
                      files, checks)
    index = {"sample_rate_hz": SAMPLE_RATE_HZ, "fade_ms": FADE_SECONDS * 1e3, "chain": "hfs.device_chain",
             "matched_target_k_loudness_note": "per excerpt, the loudest common gated BS.1770-4 loudness that no "
                                               "candidate reaches only by clipping inside the excerpt",
             "checks": checks, "files": files}
    (SAMPLES_DIRECTORY / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    (SAMPLES_DIRECTORY / "README.md").write_text(README_TEXT, encoding="utf-8")
    size = sum(path.stat().st_size for path in WEB_DIRECTORY.rglob("*.flac"))
    print(f"{len(files)} files per format, samples_web {size / 1e6:.1f} MB")
    for line in checks:
        print(line)


README_TEXT = """# Listening samples: listening-filter candidates

Generated by `src/listening_samples.py` from `../shortlist.json` and `../../recordings-public/excerpts.json`. Edit the
shortlist and rerun to change the set; files that are no longer listed are removed. `index.json` lists every file with
its gain, peak, clipped samples and levels.

## Folders

- `samples/<excerpt>/<variant>/<candidate>.wav`: mono, 16 kHz, **PCM 24-bit**, the exact 24-bit word the device sends to
  the DAC (PCM5102A).
- `../samples_web/<excerpt>/<variant>/<candidate>.flac`: the same content as **PCM 16-bit** with triangular (TPDF,
  ±1 LSB) dither, stored losslessly as FLAC for browsers. The dither is seeded by the `.wav` path, so the 16-bit values
  equal those of the earlier 16-bit WAV files.

Each own excerpt is 10 s cut from a 60 s recording. The filter runs over the whole recording from its start, so its state at
the cut is realistic. A 20 ms raised-cosine fade-in and fade-out is added at the cut so that it does not click; **the
fades are not part of the device.**

## Variants

- `device`: what the device does today. Filter, volume 100 %, saturation at the 24-bit limits, gain 1.0. No make-up gain
  exists in the firmware, so a filter can only make the sound quieter than Raw or equally loud.
- `madeup`: the same chain with one fixed make-up gain per candidate before the volume stage. The gain is the largest
  that leaves *all five* recordings without a single saturated output sample, so this is what the device could deliver
  with one fixed gain per switch position. Gains are in `index.json` (`applied_gain_db`).
- `matched`: all candidates of one excerpt brought to the same K-weighted loudness (ITU-R BS.1770-4, gated), at the
  loudest level that none of them reaches only by clipping. Use it to judge **timbre and cleanliness apart from
  loudness**. The gain differs per excerpt and is not a device setting.

## How to listen

- **Use headphones.** Heart sounds live mostly at 20–150 Hz; laptop and phone speakers reproduce almost nothing below
  about 100–200 Hz, so most of the sound would be missing.
- Playback level on a computer is **not the device level**. The device's line output gives 2.1 V RMS at digital full
  scale into the headphone amplifier; a computer's level depends on its volume setting. Set a comfortable level once on
  the loudest file (`elevated-overload`, `madeup`) and do not change it while comparing.
- Compare within one excerpt and one variant first (`device` for today's loudness, `madeup` for the achievable
  loudness, `matched` for the sound itself), then switch between Raw and a candidate several times.
- Listen for: loudness of S1/S2, whether beats sound distorted or crackling (`elevated-overload` contains input overload
  on every beat, which no filter can undo), how much rubbing, breathing or hum lies between beats, and in
  `movement-artefact` how loud the movement thump becomes.

## Public murmur excerpts

`murmur-loud`, `murmur-soft` and `no-murmur-child` (and any further excerpt written to
`recordings-public/excerpts.json`) are 8 s CirCor DigiScope 1.0.3 recordings of children, passed through the
capture-chain model (`recordings-public/README.md`), then through the same device chain and candidates. They have the
variants `madeup` (the same fixed gain per candidate as for the own recordings, derived only from the five own
recordings, so these excerpts can clip) and `matched`. There is no `device` variant. The filter runs over the whole 8 s,
so the first fraction of a second contains the filter settling; the fades are the same as for the own excerpts. The
source is sampled at 4 kHz, so there is nothing above 2 kHz.
"""


if __name__ == "__main__":
    main()
