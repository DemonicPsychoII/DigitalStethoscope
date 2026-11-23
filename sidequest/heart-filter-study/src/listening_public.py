"""Run 2: do the listening-filter candidates keep murmurs audible and distinguishable? CirCor DigiScope 1.0.3 through
the capture-chain model and the device chain.

Usage (from the study directory):
  .venv/Scripts/python.exe -I src/listening_public_gains.py              fixed gains from run 1 (once)
  .venv/Scripts/python.exe -I src/listening_public.py delays             chain-model delay check (once)
  .venv/Scripts/python.exe -I src/listening_public.py compute [condition ...] [--limit-patients N]
  .venv/Scripts/python.exe -I src/listening_public.py analyse
  .venv/Scripts/python.exe -I src/listening_public.py excerpts
Results are cached per recording in listening-public/cache/<condition>/, so a rerun only adds recordings.
"""
import argparse
import csv
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

SOURCE_DIRECTORY = Path(__file__).resolve().parent
if str(SOURCE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIRECTORY))

import numpy  # noqa: E402

import listening_public_compute as compute  # noqa: E402
from hfs import circor  # noqa: E402

MAXIMUM_WORKERS = 6
PATIENT_ORDER_SEED = 20261123


def analysed_patients(include_unknown: bool = False) -> list:
    patients = [patient for patient in circor.list_patients()
                if include_unknown or patient.murmur in ("Present", "Absent")]
    order = numpy.random.default_rng(PATIENT_ORDER_SEED).permutation(len(patients))
    return [patients[index] for index in order]


def analysed_recordings(patient) -> list:
    """Murmur-present: recordings at a location where the murmur is heard; murmur-absent: all recordings."""
    recordings = [recording for recording in circor.list_recordings(patient.patient_identifier) if recording.has_segmentation]
    if patient.murmur == "Present":
        return [recording for recording in recordings if recording.location in patient.murmur_locations]
    return recordings


def recordings_for_condition(condition: str, limit_patients: int | None) -> list[str]:
    patients = analysed_patients(include_unknown=condition == "rest_microphone_only")
    if limit_patients:
        patients = patients[:limit_patients]
    if condition != "rest_microphone_only":
        # The sensitivity conditions may be cut by the time box; the paired tests need the murmur patients first.
        patients = sorted(patients, key=lambda patient: patient.murmur != "Present")
    stems = []
    for patient in patients:
        if condition == "rest_microphone_only":
            stems += [recording.file_stem for recording in circor.list_recordings(patient.patient_identifier)
                      if recording.has_segmentation]
        else:
            stems += [recording.file_stem for recording in analysed_recordings(patient)]
    return stems


def command_delays(_arguments) -> None:
    patients = analysed_patients()[:12]
    stems = [circor.list_recordings(patient.patient_identifier)[0].file_stem for patient in patients]
    result = {}
    for condition in compute.CONDITIONS:
        delays = [compute.measure_delay_seconds(stem, condition) for stem in stems]
        result[condition] = {"recordings": stems, "delays_seconds": delays}
        print(condition, delays)
    delay_seconds = {condition: float(numpy.median(entry["delays_seconds"])) for condition, entry in result.items()}
    compute.DELAYS_PATH.write_text(json.dumps({
        "method": "cross-correlation peak of the 50-400 Hz band of the modelled capture against the plain resampled "
                  "dataset signal, search range +-200 ms, median over 12 recordings",
        "chain_model": compute.chain_model_available(), "delay_seconds": delay_seconds, "measurements": result},
        indent=2), encoding="utf-8")


def command_compute(arguments) -> None:
    conditions = arguments.conditions or list(compute.CONDITIONS)
    unknown = [condition for condition in conditions if condition not in compute.CONDITIONS]
    if unknown:
        raise SystemExit(f"unknown conditions {unknown}; choose from {list(compute.CONDITIONS)}")
    if not compute.chain_model_available():
        print("chain model not available: computing with the plain resampling stand-in (development only)")
    for condition in conditions:
        stems = recordings_for_condition(condition, arguments.limit_patients)
        missing = [stem for stem in stems if not compute.cache_path(condition, stem).exists()]
        print(f"{condition}: {len(stems)} recordings, {len(missing)} to compute", flush=True)
        started = time.time()
        failures = 0
        with ProcessPoolExecutor(max_workers=MAXIMUM_WORKERS) as executor:
            futures = [executor.submit(compute.measure_and_cache, (stem, condition)) for stem in missing]
            for count, future in enumerate(as_completed(futures), start=1):
                if not future.result()[2]:
                    failures += 1
                if count % 100 == 0 or count == len(futures):
                    print(f"  {condition}: {count}/{len(futures)} after {time.time() - started:.0f} s, "
                          f"{failures} failed", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("delays")
    compute_parser = commands.add_parser("compute")
    compute_parser.add_argument("conditions", nargs="*")
    compute_parser.add_argument("--limit-patients", type=int, default=None)
    commands.add_parser("analyse")
    commands.add_parser("excerpts")
    arguments = parser.parse_args()
    if arguments.command == "delays":
        command_delays(arguments)
    elif arguments.command == "compute":
        command_compute(arguments)
    elif arguments.command == "analyse":
        import listening_public_analysis
        listening_public_analysis.main()
    elif arguments.command == "excerpts":
        import listening_public_excerpts
        listening_public_excerpts.main()


if __name__ == "__main__":
    main()
