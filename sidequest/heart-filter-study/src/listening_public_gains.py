"""Run-1 safe gains of the run-2 candidates, computed with run 1's own function on the five own recordings and
compared with the run-1 tables. Writes listening-public/fixed_gains.json."""
import csv
import json
import sys
from pathlib import Path

SOURCE_DIRECTORY = Path(__file__).resolve().parent
if str(SOURCE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIRECTORY))

import listening_common as common  # noqa: E402
import listening_public_compute as compute  # noqa: E402


def run1_safe_gain_db(entry: dict) -> float:
    candidate = common.candidate_from_entry(entry)
    return min(common.zero_saturation_gain_db(common.apply_filter_blockwise(candidate, common.load_recording(name)))
               for name in common.RECORDING_NAMES)


def run1_table_gains() -> dict[str, float]:
    with open(common.LISTENING_DIRECTORY / "metrics_summary.csv", newline="", encoding="utf-8") as stream:
        return {row["identifier"]: float(row["safe_gain_all_recordings_zero_saturation_db"]) for row in csv.DictReader(stream)}


def main() -> None:
    table = run1_table_gains()
    gains, checks = {}, []
    for identifier, entry, brief_gain, group in compute.CANDIDATES:
        recomputed = round(run1_safe_gain_db(entry), 3)
        designed = common.candidate_from_entry(entry).identifier
        if designed != identifier:
            raise ValueError(f"{identifier}: design gives identifier {designed}")
        in_table = table.get(identifier)
        gains[identifier] = brief_gain if brief_gain is not None else recomputed
        checks.append({"identifier": identifier, "group": group, "gain_given_in_brief_db": brief_gain,
                       "recomputed_db": recomputed, "run1_metrics_summary_db": in_table,
                       "used_db": gains[identifier],
                       "mismatch": any(value is not None and abs(value - recomputed) > 0.0015
                                       for value in (brief_gain, in_table))})
    compute.OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    compute.FIXED_GAINS_PATH.write_text(json.dumps({"gains_db": gains, "checks": checks}, indent=2), encoding="utf-8")
    for check in checks:
        print(check)


if __name__ == "__main__":
    main()
