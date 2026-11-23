"""Run 2: validate run 1's sound-derived reference method (src/reference_beats.py) against the ECG reference.

Usage: python -I src/sound_reference_validation.py [--workers 6] [--records-per-subject 1]
For each chosen EPHNOGRAM record the sound is modelled through the capture chain (rest level, microphone only,
same seed as the BPM evaluation), and 62 s excerpts (2 s that the method discards + 60 s) are fed unchanged to
`reference_beats.process_recording`. Excerpts: the 60 s with the lowest, a middle and the highest ECG heart
rate of the record. Per-excerpt results are cached in cache/sound-reference/.
Writes results-public/sound_reference_validation.md and sound_reference_validation.csv.
"""
import argparse
import csv
import json
import os
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy
import soundfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import public_evaluation_common as common
import reference_beats
from hfs import ephnogram

STUDY_DIRECTORY = common.STUDY_DIRECTORY
CACHE_DIRECTORY = STUDY_DIRECTORY / "cache" / "sound-reference"
RESULTS_DIRECTORY = common.RESULTS_DIRECTORY
EXCERPT_SECONDS = 60
DISCARDED_SECONDS = int(reference_beats.DISCARDED_SECONDS)
MINIMUM_RELIABLE_SHARE = 0.8
MINIMUM_RATE_SPREAD_FOR_MIDDLE_BPM = 15.0
VALIDATION_VERSION = "1"


def ecg_windows(record_name):
    reference = common.load_reference(record_name)
    return reference


def choose_excerpts(record_name, duration_seconds):
    """Start times (record seconds, the first sample of the 62 s file) for lowest, middle and highest rate."""
    reference = ecg_windows(record_name)
    if reference is None:
        return []
    candidates = []
    last_start = int(duration_seconds) - EXCERPT_SECONDS - DISCARDED_SECONDS
    for start in range(0, last_start + 1, 5):
        ends = range(start + DISCARDED_SECONDS + 10, start + DISCARDED_SECONDS + EXCERPT_SECONDS + 1)
        windows = [reference.get(end) for end in ends]
        reliable = [window for window in windows if window and window.get("reliable") and window.get("reference_bpm")]
        if len(reliable) < MINIMUM_RELIABLE_SHARE * len(windows):
            continue
        candidates.append((start, float(numpy.mean([window["reference_bpm"] for window in reliable]))))
    if not candidates:
        return []
    lowest = min(candidates, key=lambda item: item[1])
    highest = max(candidates, key=lambda item: item[1])
    chosen = [("lowest rate", lowest)]

    def apart(item, others):
        return all(abs(item[0] - other[0]) >= EXCERPT_SECONDS + DISCARDED_SECONDS for other in others)

    if highest[1] - lowest[1] >= MINIMUM_RATE_SPREAD_FOR_MIDDLE_BPM and apart(highest, [lowest]):
        middle_target = 0.5 * (lowest[1] + highest[1])
        middle_options = [item for item in candidates if apart(item, [lowest, highest])]
        if middle_options:
            chosen.append(("middle rate", min(middle_options, key=lambda item: abs(item[1] - middle_target))))
        chosen.append(("highest rate", highest))
    return [(label, start, mean_bpm) for label, (start, mean_bpm) in chosen]


def excerpt_cache_path(record_name, start):
    return CACHE_DIRECTORY / f"{record_name}_{start:05d}.json"


def process_record(item):
    record_name, excerpts = item
    todo = [excerpt for excerpt in excerpts if not excerpt_cache_path(record_name, excerpt[1]).exists()]
    if not todo:
        return record_name, 0
    import bpm_evaluate_public
    record = ephnogram.load_record(record_name)
    modelled = numpy.asarray(bpm_evaluate_public.modelled_capture(record, "rest"))
    for label, start, mean_bpm in todo:
        first = start * 16000
        excerpt = modelled[first:first + (EXCERPT_SECONDS + DISCARDED_SECONDS) * 16000]
        with tempfile.TemporaryDirectory(prefix="sound-reference-") as directory:
            name = f"{record_name}_{start}"
            folder = Path(directory) / "recordings" / name
            folder.mkdir(parents=True)
            soundfile.write(folder / "capture.wav", (excerpt.astype(numpy.int64) << 8).astype(numpy.int32), 16000, subtype="PCM_32")
            reference_beats.STUDY_DIRECTORY = Path(directory)
            result, _ = reference_beats.process_recording(name)
        document = {"version": VALIDATION_VERSION, "record": record_name, "excerpt": label, "start_s": start,
                    "mean_ecg_bpm": mean_bpm, "windows": result["windows"]}
        CACHE_DIRECTORY.mkdir(parents=True, exist_ok=True)
        excerpt_cache_path(record_name, start).write_text(json.dumps(document), encoding="utf-8")
    return record_name, len(todo)


def chosen_records(records_per_subject):
    by_subject = {}
    excluded = common.duplicate_records_excluded()
    for info in ephnogram.list_records():
        if info.record_name in excluded or not info.available or info.duration_seconds < EXCERPT_SECONDS + DISCARDED_SECONDS + 10:
            continue
        if "disconnected" in info.pcg_quality.lower() or common.load_reference(info.record_name) is None:
            continue
        by_subject.setdefault(info.subject_id, []).append(info)
    chosen = []
    for rank in range(records_per_subject):
        for subject in sorted(by_subject):
            records = sorted(by_subject[subject], key=lambda info: ("rest" in info.scenario.lower(), info.record_name))
            if rank < len(records):
                chosen.append(records[rank])
    return chosen


def compute(workers, records_per_subject):
    items = []
    for info in chosen_records(records_per_subject):
        excerpts = choose_excerpts(info.record_name, info.duration_seconds)
        if excerpts:
            items.append((info.record_name, excerpts))
    print(f"{len(items)} records, {sum(len(item[1]) for item in items)} excerpts", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(process_record, item) for item in items]
        for done, future in enumerate(as_completed(futures), 1):
            record_name, count = future.result()
            print(f"[{done}/{len(items)}] {record_name}: {count} excerpts", flush=True)


def comparison_rows():
    info_by_name = {info.record_name: info for info in ephnogram.list_records()}
    rows = []
    excluded = common.duplicate_records_excluded()
    for path in sorted(CACHE_DIRECTORY.glob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        if document["record"] in excluded:
            continue
        reference = ecg_windows(document["record"])
        for window in document["windows"]:
            record_end = document["start_s"] + int(window["end_time_s"])
            ecg = reference.get(record_end)
            if ecg is None or ecg.get("reference_bpm") is None:
                continue
            rows.append({"record": document["record"], "subject_id": info_by_name[document["record"]].subject_id,
                         "excerpt": document["excerpt"], "excerpt_start_s": document["start_s"], "record_end_time_s": record_end,
                         "ecg_bpm": ecg["reference_bpm"], "ecg_reliable": bool(ecg.get("reliable")),
                         "sound_reference_bpm": window["reference_bpm"], "sound_reference_reliable": bool(window["reliable"]),
                         "sound_unreliable_reason": window.get("unreliable_reason") or ""})
    return rows


def agreement_block(rows):
    with_value = [row for row in rows if row["sound_reference_bpm"] is not None]
    if not with_value:
        return {"windows": len(rows), "with_value": 0}
    difference = numpy.array([row["sound_reference_bpm"] - row["ecg_bpm"] for row in with_value])
    ecg = numpy.array([row["ecg_bpm"] for row in with_value])
    absolute = numpy.abs(difference)
    return {"windows": len(rows), "with_value": len(with_value), "subjects": len({row["subject_id"] for row in rows}),
            "excerpts": len({(row["record"], row["excerpt_start_s"]) for row in rows}),
            "mean_absolute_difference_bpm": float(absolute.mean()), "median_absolute_difference_bpm": float(numpy.median(absolute)),
            "bias_bpm": float(difference.mean()), "largest_difference_bpm": float(absolute.max()),
            "within_2_bpm_share": float(numpy.mean(absolute <= 2.0)),
            "within_tolerance_share": float(numpy.mean(absolute <= numpy.maximum(5.0, 0.1 * ecg))),
            "gross_share": float(numpy.mean(absolute > 0.2 * ecg))}


def write_outputs():
    rows = comparison_rows()
    RESULTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_DIRECTORY / "sound_reference_validation.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    ecg_clean = [row for row in rows if row["ecg_reliable"]]
    marked = [row for row in ecg_clean if row["sound_reference_reliable"]]
    unmarked = [row for row in ecg_clean if not row["sound_reference_reliable"]]
    blocks = {"all windows with a reliable ECG reference": agreement_block(ecg_clean),
              "sound method marks reliable": agreement_block(marked),
              "sound method marks unreliable": agreement_block(unmarked)}
    lines = ["# Run 2: run 1's sound-derived reference against ECG", "",
             "Generated by `src/sound_reference_validation.py`. Method: `src/reference_beats.py` from run 1, imported unchanged, "
             "fed 62 s excerpts of EPHNOGRAM sound modelled through the capture chain (`hfs.chain_model`, rest level, microphone "
             "only); it discards the first 2 s as for the own recordings, so its windows end 10-60 s into the 60 s that follow. "
             "Excerpts per record: the 60 s with the lowest, a middle and the highest ECG rate (middle and highest only when the "
             f"record spans at least {MINIMUM_RATE_SPREAD_FOR_MIDDLE_BPM:g} BPM), each with at least "
             f"{MINIMUM_RELIABLE_SHARE:.0%} ECG-reliable windows. Comparison only on windows the ECG reference marks reliable.", "",
             "| windows | excerpts / subjects | windows with a value | mean absolute difference | median | bias | largest | within 2 BPM "
             "| within max(5 BPM, 10 %) | more than 20 % off |", "|---|---|---|---|---|---|---|---|---|---|"]
    for label, block in blocks.items():
        if not block.get("with_value"):
            lines.append(f"| {label} | 0 | | | | | | | | |")
            continue
        lines.append(f"| {label} | {block['excerpts']} / {block['subjects']} | {block['with_value']} of {block['windows']} | "
                     f"{block['mean_absolute_difference_bpm']:.2f} BPM | {block['median_absolute_difference_bpm']:.2f} | "
                     f"{block['bias_bpm']:+.2f} | {block['largest_difference_bpm']:.1f} | {100 * block['within_2_bpm_share']:.1f} % | "
                     f"{100 * block['within_tolerance_share']:.1f} % | {100 * block['gross_share']:.1f} % |")
    lines += ["", "## By ECG heart-rate band (windows the sound method marks reliable)", "",
              "| band (BPM) | windows marked reliable / all | subjects | mean absolute difference | largest | within 2 BPM | within tolerance |",
              "|---|---|---|---|---|---|---|"]
    for low, high, label in common.HEART_RATE_BANDS:
        band = [row for row in ecg_clean if low <= row["ecg_bpm"] < high]
        if not band:
            continue
        block = agreement_block([row for row in band if row["sound_reference_reliable"]])
        if block.get("with_value"):
            lines.append(f"| {label} | {block['with_value']} / {len(band)} | {block['subjects']} | {block['mean_absolute_difference_bpm']:.2f} | "
                         f"{block['largest_difference_bpm']:.1f} | {100 * block['within_2_bpm_share']:.1f} % | "
                         f"{100 * block['within_tolerance_share']:.1f} % |")
        else:
            lines.append(f"| {label} | 0 / {len(band)} | {len({row['subject_id'] for row in band})} | n/a | n/a | n/a | n/a |")
    agreeing = [row for row in ecg_clean if row["sound_reference_bpm"] is not None
                and abs(row["sound_reference_bpm"] - row["ecg_bpm"]) <= max(5.0, 0.1 * row["ecg_bpm"])]
    disagreeing = [row for row in ecg_clean if row not in agreeing]
    flagged_and_agreeing = sum(row["sound_reference_reliable"] for row in agreeing)
    flagged_and_disagreeing = sum(row["sound_reference_reliable"] for row in disagreeing)
    lines += ["", "## Does the reliable flag predict agreement with ECG?", "",
              "Agreement = within max(5 BPM, 10 %) of ECG; windows without a sound value count as disagreeing.", "",
              f"- Windows marked reliable that agree (precision): {flagged_and_agreeing} of {flagged_and_agreeing + flagged_and_disagreeing}"
              f" ({100 * flagged_and_agreeing / max(flagged_and_agreeing + flagged_and_disagreeing, 1):.1f} %).",
              f"- Disagreeing windows caught by the flag (marked unreliable): {len(disagreeing) - flagged_and_disagreeing} of {len(disagreeing)}"
              f" ({100 * (len(disagreeing) - flagged_and_disagreeing) / max(len(disagreeing), 1):.1f} %).",
              f"- Agreeing windows wrongly marked unreliable: {len(agreeing) - flagged_and_agreeing} of {len(agreeing)}"
              f" ({100 * (len(agreeing) - flagged_and_agreeing) / max(len(agreeing), 1):.1f} %).", "",
              "## Per excerpt", "", "| record | subject | excerpt | start (s) | mean ECG BPM | reliable (sound) / windows | mean absolute difference, marked reliable | largest |",
              "|---|---|---|---|---|---|---|---|"]
    excerpts = sorted({(row["record"], row["excerpt_start_s"]) for row in ecg_clean})
    for record_name, start in excerpts:
        excerpt_rows = [row for row in ecg_clean if row["record"] == record_name and row["excerpt_start_s"] == start]
        block = agreement_block([row for row in excerpt_rows if row["sound_reference_reliable"]])
        mean_ecg = numpy.mean([row["ecg_bpm"] for row in excerpt_rows])
        lines.append(f"| {record_name} | {excerpt_rows[0]['subject_id']} | {excerpt_rows[0]['excerpt']} | {start} | {mean_ecg:.1f} | "
                     f"{sum(row['sound_reference_reliable'] for row in excerpt_rows)} / {len(excerpt_rows)} | "
                     f"{format_value(block.get('mean_absolute_difference_bpm'))} | {format_value(block.get('largest_difference_bpm'), 1)} |")
    lines += ["", "Limits: the sound is the public stethoscope's, shaped only by the microphone model and level calibration, "
              "not by our chest-piece; the method's artefact and disturbance thresholds were set on the own recordings. "
              "The ECG reference has its own limits (two detectors on one lead)."]
    (RESULTS_DIRECTORY / "sound_reference_validation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"validation: {len(ecg_clean)} ECG-reliable windows from {len(excerpts)} excerpts")


def format_value(value, digits=2):
    return "n/a" if value is None else f"{value:.{digits}f}"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workers", type=int, default=min(6, os.cpu_count() or 2))
    parser.add_argument("--records-per-subject", type=int, default=1)
    parser.add_argument("--report-only", action="store_true")
    arguments = parser.parse_args()
    if not arguments.report_only:
        compute(arguments.workers, arguments.records_per_subject)
    write_outputs()


if __name__ == "__main__":
    main()
