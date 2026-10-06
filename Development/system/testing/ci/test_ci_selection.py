"""Changed inputs select their verification without rebuilding unrelated firmware."""

import unittest

from firmware_changes import needs_firmware, suites

APP = "Development/system/coding/bringup-zephyr/"
CI = "Development/system/testing/ci/"


class SelectionTests(unittest.TestCase):
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
            "tests/logic/src/main.c",
            "boards/board.overlay",
            "new-input",
        ):
            self.assertTrue(needs_firmware([APP + path]))
        self.assertTrue(needs_firmware([CI + "toolchain.json"]))
        self.assertTrue(needs_firmware([CI + "setup_zephyr.py"]))

    def test_docs_and_gate_changes_select_only_needed_suites(self):
        self.assertFalse(any(suites(["Development/architecture/design.md"]).values()))
        self.assertEqual(
            suites([".github/agent-gate/agent_gate.py"]),
            {"firmware": False, "host": False, "tooling": False, "gate": True},
        )

    def test_mixed_changes_and_workflow_changes_select_all_affected_suites(self):
        self.assertTrue(all(suites([".github/workflows/quality-gates.yml"]).values()))
        selected = suites([APP + "src/main.c", ".github/agent-gate/config.json"])
        self.assertTrue(selected["firmware"] and selected["host"] and selected["gate"])


if __name__ == "__main__":
    unittest.main()
