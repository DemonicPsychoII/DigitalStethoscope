"""Coverage accounting must reject missing levels and merge production counters."""

import gzip
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import host_coverage


class HostCoverageTests(unittest.TestCase):
    def test_missing_selected_level_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "missing unit coverage"):
                host_coverage.collect(Path(directory))

    def test_merge_counts_ignore_harness_and_report_both_metrics(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for level in ("unit", "l2", "integration"):
                (root / level).mkdir()
                for name in ("first", "second"):
                    (root / level / f"{name}.gcda").touch()

            def gcov(command, **options):
                counter = Path(command[-1])
                sources = (
                    host_coverage.SOURCES[:3]
                    if counter.parent.name == "unit"
                    else host_coverage.SOURCES[3:]
                    if counter.parent.name == "l2"
                    else host_coverage.SOURCES
                )
                files = [
                    {
                        "file": str(host_coverage.APPLICATION / source),
                        "lines": [
                            {
                                "line_number": 10,
                                "count": 1,
                                "branches": [
                                    {"count": int(counter.stem == "first")},
                                    {"count": int(counter.stem == "second")},
                                ],
                            }
                        ],
                    }
                    for source in (*sources, "tests/host/harness.c")
                ]
                with gzip.open(
                    counter.with_suffix(".gcov.json.gz"), "wt", encoding="utf-8"
                ) as stream:
                    json.dump(
                        {
                            "current_working_directory": str(host_coverage.ROOT),
                            "files": files,
                        },
                        stream,
                    )
                return subprocess.CompletedProcess(command, 0, "", "")

            with patch.object(host_coverage.subprocess, "run", side_effect=gcov):
                results = host_coverage.collect(root)
            counts = results["integration"][host_coverage.SOURCES[0]]
            self.assertEqual(counts["lines"], {"10": 2})
            self.assertEqual(counts["branches"], {"10:0": 1, "10:1": 1})
            report = host_coverage.markdown(results)
            self.assertIn("Lines | Branches", report)
            self.assertIn("integration total", report)
            self.assertIn("100.0%", report)

    def test_gcov_failure_cannot_publish_successful_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "unit").mkdir()
            (root / "unit/source.gcda").touch()
            with patch.object(
                host_coverage.subprocess,
                "run",
                return_value=subprocess.CompletedProcess([], 1, "", "version mismatch"),
            ):
                with self.assertRaisesRegex(ValueError, "version mismatch"):
                    host_coverage.collect(root)
