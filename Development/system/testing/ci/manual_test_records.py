"""Validate completed manual runs without treating procedure templates as execution."""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[4]
RESULTS = {"pass", "fail", "blocked", "not-run"}


def validate(record: dict) -> list[str]:
    errors = []
    if not isinstance(record, dict):
        return ["run must be an object"]
    for field in ("test_id", "procedure", "device", "firmware_build", "configuration"):
        if not isinstance(record.get(field), str) or not record[field].strip():
            errors.append(f"{field} is required")
    for field in ("firmware_sha", "procedure_sha"):
        if not re.fullmatch(r"[0-9a-f]{40}", str(record.get(field, ""))):
            errors.append(f"{field} must identify the full source commit")
    steps = record.get("steps")
    if not isinstance(steps, list) or not steps:
        errors.append("at least one step is required")
        steps = []
    identifiers = set()
    outcomes = []
    for step in steps:
        if not isinstance(step, dict):
            errors.append("step must be an object")
            continue
        identifier = step.get("id")
        if (
            not isinstance(identifier, str)
            or not identifier.strip()
            or identifier in identifiers
        ):
            errors.append("step IDs must be nonempty and unique")
        else:
            identifiers.add(identifier)
        outcome = step.get("result")
        outcomes.append(outcome)
        if not isinstance(outcome, str) or outcome not in RESULTS:
            errors.append(f"step {identifier}: invalid result")
        for field in ("action", "expected", "observations"):
            if not isinstance(step.get(field), str) or not step[field].strip():
                errors.append(f"step {identifier}: {field} is required")
    expected = (
        "fail"
        if "fail" in outcomes
        else "blocked"
        if any(value != "pass" for value in outcomes)
        else "pass"
    )
    if record.get("result") != expected:
        errors.append(f"overall result must be {expected}")
    sign_off = record.get("sign_off")
    if not isinstance(sign_off, dict):
        errors.append("Nico's execution sign-off is required")
    else:
        if sign_off.get("name") != "Nico":
            errors.append("execution sign-off must be by Nico")
        if (
            not isinstance(sign_off.get("signature_reference"), str)
            or not sign_off["signature_reference"].strip()
        ):
            errors.append("signature reference is required")
        try:
            date = datetime.fromisoformat(sign_off.get("date", ""))
            if date.tzinfo is None:
                errors.append("sign-off date must include a timezone")
        except (TypeError, ValueError):
            errors.append("valid sign-off date is required")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "directory",
        type=Path,
        nargs="?",
        default=ROOT / "Development/system/testing/manual/runs",
    )
    arguments = parser.parse_args()
    records = sorted(arguments.directory.glob("*.json"))
    errors = []
    for path in records:
        try:
            errors.extend(
                f"{path.name}: {error}"
                for error in validate(json.loads(path.read_text(encoding="utf-8")))
            )
        except (OSError, ValueError) as error:
            errors.append(f"{path.name}: {error}")
    report = f"### Manual execution records\n\n{len(records)} executed run record(s) checked.\n"
    if not records:
        report += "No executed runs recorded; device verification and Nico's sign-off remain pending.\n"
    if errors:
        report += "\n" + "\n".join(errors) + "\n"
    print(report)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open(
            "a", encoding="utf-8"
        ) as stream:
            stream.write(report)
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
