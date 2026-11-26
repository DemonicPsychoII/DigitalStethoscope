"""The clang reports keep production findings only and stay informational."""

import unittest
from unittest.mock import patch

import clang_report_comment
import clang_reports

FHIR = clang_reports.APPLICATION / "L1_services/L1_FHIR/fhir.c"
HARNESS = clang_reports.HOST_TESTS / "l1_fhir/fhir_harness.c"


class ClangReportTests(unittest.TestCase):
    def test_production_files_exclude_tests_and_vendor_code(self):
        self.assertEqual(
            clang_reports.production_file(FHIR), "L1_services/L1_FHIR/fhir.c"
        )
        self.assertIsNone(clang_reports.production_file(HARNESS))
        self.assertIsNone(
            clang_reports.production_file(
                clang_reports.VENDORED_PARSER / "http_parser.c"
            )
        )

    def test_database_has_one_compile_entry_per_unit_without_vendor_code(self):
        vendored = clang_reports.VENDORED_PARSER / "http_parser.c"
        command = ["clang", "-std=c11", "-I", "include"]
        entries = [
            {
                "directory": "/work",
                "arguments": [*command, str(HARNESS), str(vendored), "-o", "/out/fhir"],
                "output": "/out/fhir",
            },
            {
                "directory": "/work",
                "arguments": [*command, str(HARNESS), "-o", "/out/second"],
                "output": "/out/second",
            },
        ]
        database = clang_reports.compile_database(entries)
        self.assertEqual(len(database), 1)
        self.assertEqual(
            database[0]["arguments"], [*command, "-c", str(HARNESS.resolve())]
        )

    def test_tidy_splits_complexity_from_production_warnings(self):
        output = (
            f"{FHIR}:10:1: warning: function 'fhir_skipJsonValue' has cognitive complexity "
            "of 38 (threshold 0) [readability-function-cognitive-complexity]\n"
            f"{FHIR}:20:5: warning: narrowing conversion [bugprone-narrowing-conversions]\n"
            f"{HARNESS}:3:1: warning: harness finding [misc-no-recursion]\n"
        )
        completed = clang_reports.subprocess.CompletedProcess([], 0, output, "")
        with (
            patch.object(clang_reports, "run", return_value=completed),
            patch.object(clang_reports, "llvm_tool", return_value="clang-tidy"),
            patch.object(clang_reports.Path, "mkdir"),
            patch.object(clang_reports.Path, "write_text"),
            patch.object(clang_reports.shutil, "copy2"),
        ):
            results = clang_reports.tidy([{"file": str(FHIR)}])
        self.assertEqual(
            [warning["check"] for warning in results["warnings"]],
            ["bugprone-narrowing-conversions"],
        )
        self.assertEqual(results["complexity"][0]["score"], 38)

    def test_missing_toolchain_is_reported_not_run(self):
        with patch.object(clang_reports, "llvm_tool", return_value=None):
            results = clang_reports.collect(1)
        report = clang_reports.markdown(results)
        self.assertIn("Not run:", report)
        self.assertIn("No result here fails the check", report)

    def test_result_text_is_shown_only_as_code_spans(self):
        hostile = "@owner [click](https://example.org) <b>x</b> ` | **bold**\nline"
        results = {
            "toolchain": hostile,
            "errors": {"fuzz": hostile},
            "tidy": {
                "translation_units": 1,
                "failed_units": [],
                "warnings": [
                    {
                        "file": hostile,
                        "line": 1,
                        "column": 1,
                        "check": hostile,
                        "message": hostile,
                    }
                ],
                "complexity": [
                    {"function": hostile, "file": "f.c", "line": 2, "score": 3}
                ],
            },
        }
        report = clang_reports.markdown(results)
        for line in report.splitlines():
            outside = "".join(line.split("`")[0::2])
            for forbidden in ("@owner", "](", "<b>", "**bold**"):
                self.assertNotIn(forbidden, outside, line)
        self.assertNotIn("\nline", report)

    def test_a_failing_section_is_reported_and_the_others_still_run(self):
        version = clang_reports.subprocess.CompletedProcess([], 0, "clang 18\n", "")
        host = {"suite": {}, "compile_commands": []}
        with (
            patch.object(clang_reports, "llvm_tool", return_value="tool"),
            patch.object(clang_reports, "run", return_value=version),
            patch.object(clang_reports, "instrumented_host_run", return_value=host),
            patch.object(clang_reports, "mcdc_coverage", side_effect=IndexError),
            patch.object(clang_reports, "tidy", return_value={}),
            patch.object(clang_reports, "fuzz", return_value=[]),
        ):
            results = clang_reports.collect(1)
        self.assertEqual(results["errors"], {"mcdc": "IndexError"})
        self.assertEqual(results["fuzz"], [])

    def test_fuzzer_timeout_is_reported_and_the_next_target_runs(self):
        built = clang_reports.subprocess.CompletedProcess([], 0, "", "")
        calls = []

        def fake_run(argv, **options):
            calls.append(argv[0])
            if "timeout" in options:
                raise clang_reports.subprocess.TimeoutExpired(argv, options["timeout"])
            return built

        with (
            patch.object(clang_reports, "run", side_effect=fake_run),
            patch.object(clang_reports.Path, "mkdir"),
            patch.object(clang_reports.Path, "glob", return_value=[]),
            patch.object(clang_reports.shutil, "copytree"),
        ):
            results = clang_reports.fuzz("clang", 1)
        self.assertEqual([result["outcome"] for result in results], ["timed out"] * 2)
        self.assertEqual(len(calls), 4)

    def test_comment_is_found_only_when_written_by_the_workflow(self):
        comments = [
            {
                "id": 1,
                "user": {"login": "someone"},
                "body": clang_report_comment.MARKER,
            },
            {
                "id": 2,
                "user": {"login": clang_report_comment.AUTHOR},
                "body": clang_report_comment.MARKER + "\nreport",
            },
        ]
        self.assertEqual(clang_report_comment.existing_comment(comments), 2)
        self.assertIsNone(clang_report_comment.existing_comment(comments[:1]))

    def test_comment_without_report_says_not_run_and_long_reports_are_shortened(self):
        self.assertIn("Not run", clang_report_comment.body(None, "a" * 40))
        long = clang_report_comment.body("x" * 70_000, "a" * 40)
        self.assertLess(len(long), 61_000)
        self.assertIn("shortened", long)


if __name__ == "__main__":
    unittest.main()
