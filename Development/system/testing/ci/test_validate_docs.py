"""Verification IDs need a real test/procedure reference or an explicit gap."""

import tempfile
import unittest
from pathlib import Path

from validate_docs import verification_coverage


class CoverageTests(unittest.TestCase):
    def check(self, catalogue, sources):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = {
                "Development/system/testing/specification-verification.md": catalogue,
                **sources,
            }
            for name, text in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
            return verification_coverage(root)

    def test_missing_case_is_reported_by_id(self):
        errors = self.check("| VT-01 | Startup |\n| VT-14 | Setup |", {})
        self.assertEqual(len(errors), 2)
        self.assertIn("VT-01 has no test/procedure reference", errors[0])
        self.assertIn("VT-14 has no test/procedure reference", errors[1])

    def test_source_reference_filename_and_explicit_gap_are_accepted(self):
        self.assertEqual(
            self.check(
                "VT-01 VT-02 VT-14\n- VT-02: Not yet covered — target case pending",
                {
                    "Development/system/coding/app/tests/host/test_flow.py": "# VT-14",
                    "Development/system/testing/system/VT-01.md": "Startup procedure",
                },
            ),
            [],
        )

    def test_ci_tests_evidence_and_production_comments_do_not_count(self):
        errors = self.check(
            "VT-14",
            {
                "Development/system/testing/ci/test_example.py": "# VT-14",
                "Development/system/testing/evidence/run.md": "VT-14",
                "Development/system/coding/app/main.c": "// VT-14",
            },
        )
        self.assertEqual(len(errors), 1)

    def test_gap_needs_a_reason_and_does_not_match_another_id(self):
        for whitespace in (" ", "  ", " \t "):
            with self.subTest(whitespace=whitespace):
                errors = self.check(
                    f"VT-01 VT-02\n- VT-01: Not yet covered{whitespace}\n", {}
                )
                self.assertEqual(len(errors), 2)

    def test_retired_cases_need_a_reason_and_are_separate_from_gaps(self):
        self.assertEqual(self.check("VT-05\n- VT-05: Retired — replay removed", {}), [])
        for whitespace in (" ", "  ", " \t "):
            with self.subTest(whitespace=whitespace):
                self.assertEqual(
                    len(self.check(f"VT-05\n- VT-05: Retired —{whitespace}\n", {})), 1
                )

    def test_covered_case_with_stale_gap_is_reported(self):
        for source in (
            "Development/system/coding/app/tests/host/test_flow.py",
            "Development/system/testing/WIFI/setup.md",
        ):
            with self.subTest(source=source):
                errors = self.check(
                    "VT-14\n- VT-14: Not yet covered — setup pending",
                    {source: "VT-14"},
                )
                self.assertEqual(len(errors), 1)
                self.assertIn("VT-14 has a test/procedure reference", errors[0])
                self.assertIn("stale", errors[0])
