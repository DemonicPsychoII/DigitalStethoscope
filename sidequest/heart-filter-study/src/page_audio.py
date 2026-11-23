"""Listening sample index: tolerant loading, copying of web audio files (FLAC or WAV), waveform peaks, download ZIP."""

from __future__ import annotations

import base64
import json
import os
import re
import shutil
import zipfile
from math import gcd
from pathlib import Path

import numpy as np
import soundfile

WEB_SAMPLE_RATE = 16000
WAVEFORM_BUCKET_COUNT = 600
WEB_AUDIO_SUFFIXES = (".flac", ".wav")

KEY_ALIASES = {
    "excerpt": ["excerpt", "excerpt_name", "excerpt_identifier", "recording", "recording_identifier", "position"],
    "variant": ["variant", "variant_name", "gain_variant", "mode"],
    "identifier": ["identifier", "candidate_identifier", "filter_identifier", "candidate", "filter"],
    "label": ["label", "candidate_label", "filter_label", "display_name", "name"],
    "applied_gain_db": ["applied_gain_db", "gain_db", "applied_gain"],
    "output_peak_dbfs": ["output_peak_dbfs", "peak_dbfs", "output_peak_db", "peak_db"],
    "clipped_samples": ["clipped_samples", "clipped_sample_count", "clipping_samples", "clipped"],
    "a_weighted_level_db": ["a_weighted_level_db", "a_weighted_db", "a_weighted_level"],
    "k_weighted_level_lufs": ["k_weighted_level_lufs", "k_loudness_gated_lufs", "k_weighted_lufs", "loudness_lufs", "integrated_loudness_lufs", "lufs"],
    "file": ["file", "file_24_bit", "file_path", "path", "wav", "wav_file"],
    "web_file": ["web_file", "file_16_bit_web", "web_path", "web_wav", "web"],
}
ENTRY_MARKER_KEYS = set(KEY_ALIASES["file"] + KEY_ALIASES["web_file"] + ["identifier", "candidate_identifier", "filter_identifier"])
TRANSPARENT_GROUP_KEYS = {"files", "samples", "entries", "items", "excerpts", "variants", "candidates", "data"}
NUMERIC_KEYS = ["applied_gain_db", "output_peak_dbfs", "clipped_samples", "a_weighted_level_db", "k_weighted_level_lufs"]


def safe_path_component(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", str(text)).strip("-.") or "unnamed"


def collect_raw_entries(node, context: dict, found: list):
    if isinstance(node, list):
        for item in node:
            collect_raw_entries(item, context, found)
    elif isinstance(node, dict):
        if ENTRY_MARKER_KEYS & set(node):
            found.append((node, dict(context)))
            return
        for key, value in node.items():
            if not isinstance(value, (dict, list)):
                continue
            if key in TRANSPARENT_GROUP_KEYS:
                collect_raw_entries(value, context, found)
                continue
            nested_context = dict(context)
            if "excerpt" not in nested_context:
                nested_context["excerpt"] = key
            elif "variant" not in nested_context:
                nested_context["variant"] = key
            collect_raw_entries(value, nested_context, found)


def to_number(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if np.isfinite(number) else None


class SampleLibrary:
    def __init__(self, index_path: Path | None, study_root: Path, output_folder: Path, warnings: list[str], log):
        self.index_path = index_path
        self.study_root = study_root
        self.output_folder = output_folder
        self.warnings = warnings
        self.log = log
        self.entries: list[dict] = []
        self.copied: dict[Path, dict] = {}
        self.load_error: str | None = None
        self.load()

    def load(self):
        if self.index_path is None or not self.index_path.is_file():
            self.load_error = f"sample index not found: {self.index_path}"
            return
        try:
            data = json.loads(self.index_path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as error:
            self.load_error = f"sample index {self.index_path} could not be read: {error}"
            self.warnings.append(self.load_error)
            return
        found: list = []
        collect_raw_entries(data, {}, found)
        mapped_aliases: dict[str, str] = {}
        for raw_entry, context in found:
            entry = {}
            for canonical, aliases in KEY_ALIASES.items():
                for alias in aliases:
                    if alias in raw_entry and raw_entry[alias] not in (None, ""):
                        entry[canonical] = raw_entry[alias]
                        if alias != canonical:
                            mapped_aliases[alias] = canonical
                        break
            for contextual_key in ("excerpt", "variant"):
                if contextual_key not in entry and contextual_key in context:
                    entry[contextual_key] = context[contextual_key]
                    mapped_aliases[f"(grouping key) {contextual_key}"] = contextual_key
            if "identifier" not in entry:
                path_text = entry.get("web_file") or entry.get("file")
                if path_text:
                    entry["identifier"] = Path(str(path_text)).stem
            if "excerpt" not in entry or "variant" not in entry or "identifier" not in entry:
                self.warnings.append(f"sample index: entry without excerpt, variant or identifier skipped: {raw_entry}")
                continue
            for key in ("excerpt", "variant", "identifier"):
                entry[key] = str(entry[key])
            entry["label"] = str(entry.get("label") or entry["identifier"])
            for key in NUMERIC_KEYS:
                entry[key] = to_number(entry.get(key))
            self.entries.append(entry)
        self.log(f"Sample index {self.index_path}: {len(self.entries)} entries")
        for alias, canonical in sorted(mapped_aliases.items()):
            self.log(f"  mapped key '{alias}' -> '{canonical}'")

    def resolve(self, path_text) -> Path | None:
        if not path_text:
            return None
        relative = Path(str(path_text))
        if relative.is_absolute():
            return relative if relative.is_file() else None
        index_folder = self.index_path.parent if self.index_path else self.study_root
        for base in (self.study_root, self.study_root / "listening", index_folder, index_folder.parent):
            candidate = base / relative
            if candidate.is_file():
                return candidate.resolve()
        return None

    def variants_for(self, excerpt: str) -> list[str]:
        variants = []
        for entry in self.entries:
            if entry["excerpt"] == excerpt and entry["variant"] not in variants:
                variants.append(entry["variant"])
        return variants

    def excerpts(self) -> list[str]:
        return list(dict.fromkeys(entry["excerpt"] for entry in self.entries))

    def entries_for(self, excerpt: str, variant: str) -> list[dict]:
        return [entry for entry in self.entries if entry["excerpt"] == excerpt and entry["variant"] == variant]

    def publish(self, entry: dict) -> dict:
        """Copy the web file (FLAC or WAV) into the site, or derive a 16-bit WAV from the original, and return the
        player's sample description."""
        web_source = self.resolve(entry.get("web_file"))
        suffix = web_source.suffix.lower() if web_source and web_source.suffix.lower() in WEB_AUDIO_SUFFIXES else ".wav"
        relative_target = Path("assets", "audio", safe_path_component(entry["excerpt"]), safe_path_component(entry["variant"]),
                               safe_path_component(entry["identifier"]) + suffix)
        target = self.output_folder / relative_target
        sample = {
            "identifier": entry["identifier"],
            "label": entry["label"],
            "url": relative_target.as_posix(),
            **{key: entry[key] for key in NUMERIC_KEYS},
        }
        if target in self.copied:
            return {**sample, **self.copied[target]}
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            if web_source:
                shutil.copyfile(web_source, target)
            else:
                original = self.resolve(entry.get("file"))
                if not original:
                    self.warnings.append(
                        f"audio file missing for {entry['excerpt']}/{entry['variant']}/{entry['identifier']}: "
                        f"web_file={entry.get('web_file')!r}, file={entry.get('file')!r}"
                    )
                    self.copied[target] = {"missing": True}
                    return {**sample, "missing": True}
                self.log(f"  no web_file for {entry['identifier']} ({entry['excerpt']}/{entry['variant']}): "
                         f"converted {original.name} to 16-bit {WEB_SAMPLE_RATE} Hz mono")
                write_web_wav(original, target)
            details = waveform_details(target)
        except (OSError, RuntimeError, ValueError) as error:
            self.warnings.append(f"audio file for {entry['identifier']} could not be processed: {error}")
            self.copied[target] = {"missing": True}
            return {**sample, "missing": True}
        self.copied[target] = details
        return {**sample, **details}

    def write_download_zip(self, zip_path: Path) -> int:
        """Pack the full-resolution originals of every entry plus the index; returns the file count."""
        originals = []
        for entry in self.entries:
            original = self.resolve(entry.get("file"))
            if original:
                originals.append(original)
            else:
                self.warnings.append(f"download ZIP: original file missing for {entry['excerpt']}/{entry['variant']}/{entry['identifier']}")
        originals = list(dict.fromkeys(originals))
        if not originals:
            return 0
        try:
            common_base = Path(os.path.commonpath([str(original.parent) for original in originals]))
        except ValueError:
            common_base = None
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for original in originals:
                archive_name = original.relative_to(common_base).as_posix() if common_base else original.name
                archive.write(original, "samples/" + archive_name)
            if self.index_path:
                archive.write(self.index_path, "samples/index.json")
        return len(originals)


def write_web_wav(source: Path, target: Path):
    from scipy.signal import resample_poly

    data, sample_rate = soundfile.read(source, dtype="float64", always_2d=True)
    mono = data.mean(axis=1)
    if sample_rate != WEB_SAMPLE_RATE:
        divisor = gcd(int(sample_rate), WEB_SAMPLE_RATE)
        mono = resample_poly(mono, WEB_SAMPLE_RATE // divisor, int(sample_rate) // divisor)
    soundfile.write(target, np.clip(mono, -1.0, 1.0), WEB_SAMPLE_RATE, subtype="PCM_16")


def waveform_details(path: Path) -> dict:
    data, sample_rate = soundfile.read(path, dtype="float32", always_2d=True)
    signal = data[:, 0] if data.shape[1] == 1 else data[np.arange(len(data)), np.abs(data).argmax(axis=1)]
    duration = len(signal) / float(sample_rate) if sample_rate else 0.0
    bucket_count = min(WAVEFORM_BUCKET_COUNT, len(signal))
    if bucket_count == 0:
        return {"duration": duration, "peaks": ""}
    edges = np.linspace(0, len(signal), bucket_count + 1).astype(int)[:-1]
    minima = np.minimum.reduceat(signal, edges)
    maxima = np.maximum.reduceat(signal, edges)
    interleaved = np.empty(bucket_count * 2, dtype=np.float32)
    interleaved[0::2] = minima
    interleaved[1::2] = maxima
    quantized = np.clip(np.round(interleaved * 127.0), -127, 127).astype(np.int8)
    return {"duration": round(duration, 4), "peaks": base64.b64encode(quantized.tobytes()).decode("ascii")}
