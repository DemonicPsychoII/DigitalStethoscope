"""Missing JUnit and unsuccessful scenarios must fail result reporting."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import run_ci
from application_host_results import report
from ci_results import problems


class HostResultTests(unittest.TestCase):
    def test_per_scenario_table_records_vt_and_outcome(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "results.xml"
            source.write_text(
                '<testsuites><testsuite><testcase name="test_flow[retry]">'
                '<properties><property name="scenario" value="retry"/>'
                '<property name="vt_id" value="VT-14"/></properties>'
                "</testcase></testsuite></testsuites>"
            )
            markdown, passed = report(source)
            self.assertTrue(passed)
            self.assertIn("| retry | VT-14 | PASS |", markdown)
            for tag in ("failure", "error", "skipped"):
                failed = source.read_text().replace(
                    "</testcase>", f"<{tag}/></testcase>"
                )
                source.write_text(failed)
                self.assertFalse(report(source)[1])
                source.write_text(failed.replace(f"<{tag}/>", ""))

    def test_absent_empty_malformed_and_unmapped_results_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "results.xml"
            self.assertFalse(report(source)[1])
            for text in (
                "<testsuites/>",
                "broken",
                '<testsuite><testcase name="flow"/></testsuite>',
            ):
                source.write_text(text)
                self.assertFalse(report(source)[1])

    def test_missing_static_suite_selector_cannot_pass_accounting(self):
        self.assertTrue(
            problems(
                "success",
                "success",
                "skipped",
                "false",
                "false",
                "false",
                "true",
                static_suites={"APPLICATION_HOST": ""},
            )
        )

    def test_maintained_zephyr_host_headers_are_not_generated_output(self):
        self.assertFalse(
            run_ci.generated_output(
                "Development/system/coding/app/tests/host/include/zephyr/kernel.h"
            )
        )
        for path in (
            ".ci-workspace/zephyr/kernel.h",
            "build/zephyr/file.h",
            "Development/system/coding/app/tests/host/include/zephyr/test.bin",
        ):
            self.assertTrue(run_ci.generated_output(path))

    def test_missing_validators_skip_only_on_local_windows(self):
        with patch.object(run_ci.shutil, "which", return_value=None):
            for platform, ci, should_fail in (
                ("win32", "", False),
                ("win32", "true", True),
                ("linux", "", True),
            ):
                with (
                    patch.object(run_ci.sys, "platform", platform),
                    patch.dict(os.environ, {"CI": ci}),
                ):
                    if should_fail:
                        with self.assertRaises(SystemExit):
                            run_ci.workflow_validators()
                    else:
                        run_ci.workflow_validators()
