"""Collect GCC line and branch evidence for each production host-test level."""

import argparse
import gzip
import json
import os
from pathlib import Path
import shlex
import subprocess

ROOT = Path(__file__).resolve().parents[4]
APPLICATION = ROOT / "Development/system/coding/app"
SOURCES = (
    "L1_services/L1_WIFI/wifi.c",
    "L1_services/L1_PORTAL/portal.c",
    "L1_services/L1_STORAGE/storage.c",
    "L2_application/L2_COMMUNICATION/communication.c",
)


def collect(directory: Path) -> dict:
    results = {}
    for level in ("unit", "l2", "integration"):
        counters = sorted((directory / level).rglob("*.gcda"))
        if not counters:
            raise ValueError(f"missing {level} coverage counters")
        files = {}
        for counter in counters:
            command = shlex.split(os.environ.get("GCOV", "gcov")) + [
                "--json-format",
                "--branch-probabilities",
                str(counter.resolve()),
            ]
            result = subprocess.run(
                command, cwd=counter.parent, capture_output=True, text=True, timeout=60
            )
            counter.with_suffix(".gcov.log").write_text(
                result.stdout + result.stderr, encoding="utf-8"
            )
            if result.returncode:
                raise ValueError(f"gcov failed for {counter}: {result.stderr}")
            report = counter.with_suffix(".gcov.json.gz")
            with gzip.open(report, "rt", encoding="utf-8") as stream:
                data = json.load(stream)
            for source in data["files"]:
                path = Path(data["current_working_directory"], source["file"]).resolve()
                try:
                    relative = path.relative_to(APPLICATION.resolve()).as_posix()
                except ValueError:
                    continue
                if relative not in SOURCES:
                    continue
                counts = files.setdefault(relative, {"lines": {}, "branches": {}})
                for line in source["lines"]:
                    number = str(line["line_number"])
                    counts["lines"][number] = (
                        counts["lines"].get(number, 0) + line["count"]
                    )
                    for index, branch in enumerate(line.get("branches", [])):
                        key = f"{number}:{index}"
                        counts["branches"][key] = (
                            counts["branches"].get(key, 0) + branch["count"]
                        )
        expected = (
            SOURCES[:3]
            if level == "unit"
            else SOURCES[3:]
            if level == "l2"
            else SOURCES
        )
        if set(files) != set(expected):
            raise ValueError(f"{level} production coverage mismatch: {sorted(files)}")
        if not all(counts["lines"] and counts["branches"] for counts in files.values()):
            raise ValueError(f"missing line or branch evidence in {level}")
        results[level] = files
    return results


def markdown(results: dict) -> str:
    text = "### Production host coverage\n\n| Level / source | Lines | Branches |\n| --- | ---: | ---: |\n"
    for level, files in results.items():
        totals = {"lines": [0, 0], "branches": [0, 0]}
        for name, counts in files.items():
            values = []
            for kind in totals:
                hit = sum(value > 0 for value in counts[kind].values())
                total = len(counts[kind])
                totals[kind][0] += hit
                totals[kind][1] += total
                values.append(f"{hit}/{total} ({100 * hit / total:.1f}%)")
            text += f"| {level} / {name} | {' | '.join(values)} |\n"
        values = [
            f"{hit}/{total} ({100 * hit / total:.1f}%)"
            for hit, total in totals.values()
        ]
        text += f"| **{level} total** | {' | '.join(values)} |\n"
    return (
        text
        + "\nGCC executable lines and branch arcs; production C only. Levels are reported separately.\nKnown-defect XFAIL executions contribute coverage, not verified behavior. No numeric threshold is imposed.\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    arguments = parser.parse_args()
    try:
        results = collect(arguments.directory)
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
        raise SystemExit(str(error)) from error
    report = markdown(results)
    (arguments.directory / "coverage.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8"
    )
    (arguments.directory / "coverage.md").write_text(report, encoding="utf-8")
    print(report)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open(
            "a", encoding="utf-8"
        ) as stream:
            stream.write(report)


if __name__ == "__main__":
    main()
