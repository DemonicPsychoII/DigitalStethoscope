"""Changed inputs select their verification without rebuilding unrelated firmware."""

import unittest

from firmware_changes import needs_firmware, select, suites

APP = "Development/system/coding/bringup-zephyr/"
CI = "Development/system/testing/ci/"


class SelectionTests(unittest.TestCase):
    def test_component_changes_do_not_build_the_other_application(self):
        application = suites(["Development/system/coding/app/main.c"])
        self.assertTrue(application["application"])
        self.assertFalse(
            application["firmware"] or application["native"] or application["host"]
        )
        bringup = suites([APP + "src/main.c"])
        self.assertTrue(bringup["firmware"] and bringup["native"] and bringup["host"])
        self.assertFalse(bringup["application"])
        mixed = suites(["Development/system/coding/app/main.c", APP + "src/main.c"])
        self.assertTrue(mixed["application"] and mixed["firmware"])
        for path in (
            CI + "toolchain.json",
            CI + "build_support.py",
            ".github/workflows/quality-gates.yml",
        ):
            selected = suites([path])
            self.assertTrue(selected["application"] and selected["firmware"])

    def test_daily_promotion_keeps_qc_without_repeating_verified_suites(self):
        promoted = select([], full=False, daily=True, reuse=True)
        self.assertEqual([key for key, value in promoted.items() if value], ["qc"])
        rebuilt = select([], full=False, daily=True, reuse=False)
        self.assertTrue(rebuilt["firmware"] and rebuilt["native"] and rebuilt["host"])
        self.assertFalse(
            rebuilt["application"] or rebuilt["tooling"] or rebuilt["gate"]
        )
        self.assertTrue(all(select([], full=True, daily=False, reuse=False).values()))

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
        for path in (
            "Development/system/architecture/rendered/view.svg",
            "thesis-material/_build/integration-notes.json",
            "Development/system/testing/ci/toolchain.json",
        ):
            self.assertTrue(suites([path])["docs"], path)
        self.assertEqual(
            suites([".github/agent-gate/agent_gate.py"]),
            {
                "firmware": False,
                "application": False,
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
            all(v for v in suites([".github/workflows/quality-gates.yml"]).values())
        )
        selected = suites([APP + "src/main.c", ".github/agent-gate/config.json"])
        self.assertTrue(selected["firmware"] and selected["host"] and selected["gate"])

    def test_qc_evaluator_changes_run_its_tooling_regressions_without_firmware(self):
        self.assertEqual(
            suites(["Development/system/testing/qc_eval.py"]),
            {
                "firmware": False,
                "application": False,
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
