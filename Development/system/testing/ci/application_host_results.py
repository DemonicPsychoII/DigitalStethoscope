"""Publish per-scenario JUnit evidence and reject absent or incomplete results."""

import argparse
import os
import xml.etree.ElementTree as ET
from pathlib import Path


def report(source: Path) -> tuple[str, bool]:
    header = "### Application host scenarios\n\n| Scenario | Level | VT ID | Result | Design basis |\n| --- | --- | --- | --- | --- |\n"
    try:
        cases = ET.parse(source).getroot().findall(".//testcase")
    except (OSError, ET.ParseError) as error:
        return header + f"\nMissing or invalid JUnit evidence: {error}\n", False
    if not cases:
        return header + "\nNo application scenarios were reported.\n", False
    rows = []
    passed = True
    for case in cases:
        properties = {
            item.get("name"): item.get("value", "")
            for item in case.findall("./properties/property")
        }
        scenario = properties.get("scenario") or case.get("name", "unknown")
        vt = properties.get("vt_id", "").strip() or "unmapped"
        result = "PASS"
        for tag, label in (
            ("failure", "FAIL"),
            ("error", "ERROR"),
            ("skipped", "SKIPPED"),
        ):
            if case.find(tag) is not None:
                result = label
                skipped = case.find(tag)
                if (
                    tag == "skipped"
                    and skipped.get("type") == "pytest.xfail"
                    and skipped.get("message", "").strip()
                ):
                    result = "XFAIL"
                break
        if vt == "unmapped":
            result += " (missing VT reference)"
        passed = passed and result in {"PASS", "XFAIL"}
        scenario = scenario.replace("|", "\\|").replace("\n", " ")
        vt = vt.replace("|", "\\|").replace("\n", " ")
        basis = (
            properties.get("basis", "unmapped").replace("|", "\\|").replace("\n", " ")
        )
        level = properties.get("level", "host").replace("|", "\\|").replace("\n", " ")
        rows.append(f"| {scenario} | {level} | {vt} | {result} | {basis} |")
    note = "\nXFAIL records a known defect, not verified behavior. Strict unexpected passes fail pytest.\n"
    return header + "\n".join(rows) + "\n" + note, passed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("junit", type=Path)
    args = parser.parse_args()
    markdown, passed = report(args.junit)
    print(markdown)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open(
            "a", encoding="utf-8"
        ) as stream:
            stream.write(markdown)
    if not passed:
        raise SystemExit(
            "application host results are missing, incomplete or unsuccessful"
        )


if __name__ == "__main__":
    main()
