"""Changed inputs select their verification without rebuilding unrelated firmware."""

import unittest

from firmware_changes import needs_firmware, suites

APP = "Development/system/coding/bringup-zephyr/"
CI = "Development/system/testing/ci/"


class SelectionTests(unittest.TestCase):
    def test_thesis_application_inputs_compile_firmware(self):
        app = "Development/system/coding/app/"
        for path in (
            "main.c",
            "L1_services/audio/audio.h",
            "CMakeLists.txt",
            "prj.conf",
            "boards/esp32s3_devkitc_procpu.overlay",
        ):
            self.assertTrue(needs_firmware([app + path]))
        for path in ("README.md", "tests/host/test_filter.py", "common/.gitkeep"):
            self.assertFalse(needs_firmware([app + path]))

    def test_host_tools_and_tests_do_not_compile_firmware(self):
        for path in ("tools/requirements.txt", "tests/host/test_dsp.py", "README.md"):
            self.assertFalse(needs_firmware([APP + path]))
        self.assertTrue(suites([APP + "tools/requirements.txt"])["host"])

    def test_ci_unit_tests_and_daily_selector_do_not_compile_firmware(self):
        for path in ("test_daily_build.py", "daily_build.py", "firmware_changes.py"):
            self.assertFalse(needs_firmware([CI + path]))
            self.assertTrue(suites([CI + path])["tooling"])

    def test_firmware_inputs_and_unknown_application_inputs_build(self):
        for path in (
            "src/main.c",
            "include/stetho_dsp.h",
            "prj.conf",
            "CMakeLists.txt",
            "boards/board.overlay",
            "new-input",
        ):
            self.assertTrue(needs_firmware([APP + path]))
        self.assertTrue(needs_firmware([CI + "toolchain.json"]))
        self.assertTrue(needs_firmware([CI + "setup_zephyr.py"]))

    def test_docs_and_gate_changes_select_only_needed_suites(self):
        self.assertTrue(suites(["Development/architecture/design.md"])["docs"])
        self.assertEqual(
            suites([".github/agent-gate/agent_gate.py"]),
            {
                "firmware": False,
                "native": False,
                "docs": False,
                "host": False,
                "tooling": False,
                "gate": True,
                "qc": False,
            },
        )

    def test_mixed_changes_and_workflow_changes_select_all_affected_suites(self):
        self.assertTrue(
            all(
                v
                for k, v in suites([".github/workflows/quality-gates.yml"]).items()
                if k != "docs"
            )
        )
        selected = suites([APP + "src/main.c", ".github/agent-gate/config.json"])
        self.assertTrue(selected["firmware"] and selected["host"] and selected["gate"])

    def test_qc_evaluator_changes_run_its_tooling_regressions_without_firmware(self):
        self.assertEqual(
            suites(["Development/system/testing/qc_eval.py"]),
            {
                "firmware": False,
                "native": False,
                "docs": False,
                "qc": True,
                "host": False,
                "tooling": True,
                "gate": False,
            },
        )


if __name__ == "__main__":
    unittest.main()
