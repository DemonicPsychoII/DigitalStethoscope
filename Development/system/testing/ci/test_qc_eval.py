"""QC must inspect production modules and never reuse stale passing reports."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import run_ci

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import qc_eval  # noqa: E402


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.app = self.root / "Development/system/coding/bringup-zephyr"
        original = run_ci.APP
        for relative in (
            "CMakeLists.txt",
            "prj.conf",
            "qc.conf",
            "README.md",
            "TEST-PROTOCOL.md",
            "boards/esp32s3_devkitc_procpu.overlay",
            "evidence/build-results.json",
        ):
            destination = self.app / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original / relative, destination)
        shutil.copytree(original / "src", self.app / "src")
        self.testing = self.root / "Development/system/testing"
        self.testing.mkdir(parents=True)
        shutil.copyfile(
            run_ci.ROOT / "Development/system/testing/tha-baseline-traceability.json",
            self.testing / "tha-baseline-traceability.json",
        )

    def evaluate(self):
        return qc_eval.evaluate(self.root, self.root / "absent-tha")

    def control(self, name):
        return next(c for c in self.evaluate()["controls"] if c["control"] == name)

    def test_unhandled_driver_result_outside_main_holds_gate(self):
        with (self.app / "src/audio_loopback.c").open("a") as stream:
            stream.write(
                "\nvoid bad(void) {\n (void)\n i2s_write(dev, data, size);\n}\n"
            )
        result = self.evaluate()
        self.assertEqual(result["gate"], "HOLD")
        self.assertEqual(
            self.control("API return-code discipline")["status"], "PARTIAL"
        )

    def test_comments_strings_and_test_fixtures_do_not_affect_api_control(self):
        with (self.app / "src/audio_loopback.c").open("a") as stream:
            stream.write(
                "\n/* i2s_write(dev, data, size); */\n"
                "// (void)i2s_trigger(dev, 0, 0);\n"
                'const char *example = "display_write(dev, x, y, d, b);";\n'
            )
        fixtures = self.app / "tests/host"
        fixtures.mkdir(parents=True)
        (fixtures / "fixture.c").write_text("void bad(void) { i2s_write(d, b, s); }")
        self.assertEqual(self.control("API return-code discipline")["status"], "PASS")

    def test_discarded_unbraced_conditional_calls_hold_gate(self):
        path = self.app / "src/audio_loopback.c"
        original = path.read_text()
        for body in (
            "if (ready) i2s_write(dev, data, size);",
            "if (ready && check(nested())) (void)i2s_write(dev, data, size);",
            "if (ready) rc = 0; else i2s_write(dev, data, size);",
            "while (ready()) i2s_write(dev, data, size);",
            "for (int i = 0; i < limit(); ++i) i2s_write(dev, data, size);",
        ):
            with self.subTest(body=body):
                path.write_text(original + "\nvoid bad(void) { " + body + " }\n")
                self.assertEqual(self.evaluate()["gate"], "HOLD")
                self.assertEqual(
                    self.control("API return-code discipline")["status"], "PARTIAL"
                )

    def test_consumed_conditional_call_results_do_not_hold_gate(self):
        path = self.app / "src/audio_loopback.c"
        path.write_text(
            path.read_text() + "\nint checked(void) {\n"
            " if (ready()) rc = (int)i2s_write(dev, data, size);\n"
            " if (i2s_write(dev, data, size) < 0) recover();\n"
            " if (ready) return i2s_write(dev, data, size);\n}\n"
        )
        self.assertEqual(self.control("API return-code discipline")["status"], "PASS")

    def test_gpio_module_interrupts_and_queue_replace_polling_claim(self):
        control = self.control("Real-time response and bounded work")
        self.assertEqual(control["status"], "PASS")
        self.assertNotIn("20 ms", control["evidence"])
        path = self.app / "src/gpio_inputs.c"
        path.write_text(
            path.read_text().replace(
                "gpio_pin_interrupt_configure_dt", "removed_interrupt_configuration"
            )
        )
        self.assertEqual(
            self.control("Real-time response and bounded work")["status"], "PARTIAL"
        )

    def test_missing_fault_policy_cannot_pass_unconditionally(self):
        self.assertEqual(
            self.control("Fault isolation and degraded operation")["status"], "PASS"
        )
        (self.app / "src/peripherals.c").write_text("/* app_probe_record(); */\n")
        self.assertEqual(
            self.control("Fault isolation and degraded operation")["status"], "FAIL"
        )
        self.assertEqual(self.evaluate()["gate"], "HOLD")

    def test_fixture_synchronization_cannot_replace_production_declarations(self):
        for path in (self.app / "src").glob("*.c"):
            path.write_text(
                qc_eval.source_code(path.read_text())
                .replace("atomic_t", "int")
                .replace("K_MUTEX_DEFINE", "REMOVED_MUTEX")
                .replace("K_MSGQ_DEFINE", "REMOVED_MSGQ")
                .replace("K_SEM_DEFINE", "REMOVED_SEM")
                .replace("K_FIFO_DEFINE", "REMOVED_FIFO")
            )
        fixtures = self.app / "tests"
        fixtures.mkdir()
        (fixtures / "example.c").write_text("K_MUTEX_DEFINE(example);")
        self.assertEqual(
            self.control("Concurrency and shared-state synchronization")["status"],
            "FAIL",
        )

    def test_commented_runtime_configuration_does_not_pass(self):
        path = self.app / "prj.conf"
        path.write_text(
            path.read_text().replace(
                "CONFIG_STACK_SENTINEL=y", "# CONFIG_STACK_SENTINEL=y"
            )
        )
        self.assertEqual(
            self.control("Logging and runtime diagnostics")["status"], "PARTIAL"
        )

    def test_cli_defaults_to_selected_repo_artifacts_and_preserves_source_tree(self):
        result = subprocess.run(
            [
                sys.executable,
                str(Path(qc_eval.__file__)),
                "--repo",
                str(self.root),
                "--tha",
                str(self.root / "absent-tha"),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        output = self.root / "artifacts/qc"
        self.assertEqual(
            json.loads((output / "qc-eval-results.json").read_text())["gate"], "PASS"
        )
        self.assertTrue((output / "QC-EVALUATION.md").is_file())
        self.assertFalse((self.testing / "QC-EVALUATION.md").exists())
        self.assertFalse((self.testing / "qc-eval-results.json").exists())

    def test_malformed_build_evidence_holds_instead_of_crashing(self):
        (self.app / "evidence/build-results.json").write_text("[]")
        self.assertEqual(
            self.control("Repeatable verification and recorded verdicts")["status"],
            "PARTIAL",
        )


class ReportIntegrationTests(unittest.TestCase):
    def test_crashed_evaluator_cannot_read_stale_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            artifacts = Path(directory)
            output = artifacts / "qc"
            output.mkdir()
            (output / "qc-eval-results.json").write_text('{"gate":"PASS"}')
            (output / "QC-EVALUATION.md").write_text("Old PASS")
            with (
                patch.object(run_ci, "ARTIFACTS", artifacts),
                patch.object(
                    run_ci.subprocess,
                    "run",
                    return_value=subprocess.CompletedProcess([], 2),
                ),
            ):
                with self.assertRaises(FileNotFoundError):
                    run_ci.qc()
            self.assertFalse((output / "qc-eval-results.json").exists())
            self.assertFalse((output / "QC-EVALUATION.md").exists())

    def test_wrapper_reads_new_artifact_report_and_preserves_hold_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            artifacts = Path(directory)

            def evaluator(argv, **kwargs):
                output = Path(argv[argv.index("--output-dir") + 1])
                self.assertEqual(output, artifacts / "qc")
                (output / "qc-eval-results.json").write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "score": 95,
                            "maximum_score": 100,
                            "gate": "HOLD",
                            "controls": [{"status": "PARTIAL"}],
                        }
                    )
                )
                return subprocess.CompletedProcess(argv, 1)

            with (
                patch.object(run_ci, "ARTIFACTS", artifacts),
                patch.object(run_ci.subprocess, "run", side_effect=evaluator),
                patch.object(run_ci, "summary"),
            ):
                with self.assertRaisesRegex(SystemExit, "95/100.*HOLD"):
                    run_ci.qc()


if __name__ == "__main__":
    unittest.main()
