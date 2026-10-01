"""Protect comparable inputs, failure evidence and benchmark summaries."""

import argparse
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import benchmark_build as benchmark


class BenchmarkTests(unittest.TestCase):
    def test_source_hash_matches_crlf_and_lf_but_detects_edits(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            app = root / "app"
            app.mkdir()
            source = app / "CMakeLists.txt"
            with (
                patch.object(benchmark, "ROOT", root),
                patch.object(benchmark, "APP", app),
                patch.object(
                    benchmark,
                    "capture",
                    side_effect=lambda argv, *_: "app/CMakeLists.txt"
                    if "ls-files" in argv
                    else "commit",
                ),
            ):
                source.write_bytes(b"project(eval)\r\n")
                windows = benchmark.source_info({})
                source.write_bytes(b"project(eval)\n")
                linux = benchmark.source_info({})
                self.assertEqual(windows["input_sha256"], linux["input_sha256"])
                source.write_bytes(b"project(changed)\n")
                self.assertNotEqual(
                    linux["input_sha256"], benchmark.source_info({})["input_sha256"]
                )

    def test_comparison_excludes_warmups_and_failed_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.json"
            report = {
                "schema_version": 1,
                "board": "test",
                "machine": {"label": "test"},
                "source": {"input_sha256": "abc"},
                "policy": "clean",
                "toolchain": {"pins": {}, "compiler": "gcc", "python": "3.14"},
                "measurements": [
                    {"warmup": True, "exit_code": 0, "total_seconds": 1000},
                    {"warmup": False, "exit_code": 1, "total_seconds": 1000},
                    *[
                        {
                            "warmup": False,
                            "exit_code": 0,
                            "profile": "offline",
                            "jobs": 4,
                            "mode": "clean",
                            "total_seconds": value,
                        }
                        for value in (2, 4, 9)
                    ],
                ],
            }
            path.write_text(json.dumps(report))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                benchmark.compare([path])
            self.assertIn("| 3 | 4.00 | 2.00 | 9.00 |", output.getvalue())

    def test_failed_configure_saves_evidence_and_never_compiles(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = argparse.Namespace(
                workspace=root,
                device="test",
                profiles=["offline"],
                jobs=[4],
                warmups=0,
                runs=3,
                include_noop=True,
            )
            with (
                patch.object(benchmark, "ROOT", root),
                patch.object(benchmark, "tool_info", return_value={"modules": {}}),
                patch.object(
                    benchmark, "source_info", return_value={"input_sha256": "abc"}
                ),
                patch.object(benchmark, "west_command", return_value=["west"]),
                patch.object(benchmark, "timed", return_value=(1.25, 7)) as timed,
            ):
                with self.assertRaisesRegex(RuntimeError, "Build failed"):
                    benchmark.run_benchmark(args)
            self.assertEqual(timed.call_count, 1)
            report = json.loads(next(root.rglob("results.json")).read_text())
            self.assertEqual(len(report["measurements"]), 1)
            self.assertEqual(report["measurements"][0]["exit_code"], 7)
            self.assertEqual(report["measurements"][0]["compile_seconds"], 0)


if __name__ == "__main__":
    unittest.main()
