"""Changed inputs select their verification without rebuilding unrelated firmware."""

import unittest
from unittest.mock import patch

from firmware_changes import needs_firmware, select, suites

APP = "Development/system/coding/bringup-zephyr/"
CI = "Development/system/testing/ci/"


class SelectionTests(unittest.TestCase):
    def setUp(self):
        availability = patch(
            "firmware_changes.available_component_suites",
            return_value=("communication",),
        )
        availability.start()
        self.addCleanup(availability.stop)

    def test_component_pages_select_only_the_available_communication_suite(self):
        for area in ("architecture", "design"):
            for component in ("WIFI", "PORTAL", "L2_COMMUNICATION", "system"):
                self.assertTrue(
                    suites([f"Development/system/{area}/{component}/README.md"])[
                        "application_host"
                    ]
                )
            self.assertFalse(
                suites([f"Development/system/{area}/AUDIO/README.md"])[
                    "application_host"
                ]
            )
        for component in ("L1_WIFI", "L1_PORTAL", "L2_COMMUNICATION"):
            path = f"Development/system/coding/app/{component}/service.md"
            self.assertTrue(suites([path])["application_host"])
        with patch("firmware_changes.available_component_suites", return_value=()):
            self.assertFalse(
                suites(["Development/system/design/WIFI/README.md"])["application_host"]
            )
            self.assertFalse(
                select([], full=True, daily=False, reuse=False)["application_host"]
            )
            self.assertFalse(
                select([], full=False, daily=False, reuse=False, retain=True)[
                    "application_host"
                ]
            )

    def test_component_changes_do_not_build_the_other_application(self):
        application = suites(["Development/system/coding/app/main.c"])
        self.assertTrue(application["application"])
        self.assertFalse(application["firmware"] or application["native"])
        self.assertTrue(application["host"])
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

    def test_application_host_tests_select_host_without_firmware(self):
        selected = suites(
            ["Development/system/coding/app/tests/host/test_communication.py"]
        )
        self.assertTrue(selected["host"])
        self.assertFalse(
            selected["application"] or selected["firmware"] or selected["native"]
        )

    def test_daily_promotion_avoids_repeating_verified_suites(self):
        promoted = select([], full=False, daily=True, reuse=True)
        self.assertEqual([key for key, value in promoted.items() if value], [])
        rebuilt = select([], full=False, daily=True, reuse=False)
        self.assertTrue(rebuilt["firmware"] and rebuilt["native"] and rebuilt["host"])
        self.assertTrue(rebuilt["application"] and rebuilt["application_host"])
        self.assertFalse(rebuilt["tooling"] or rebuilt["gate"])
        self.assertTrue(all(select([], full=True, daily=False, reuse=False).values()))

    def test_publication_selects_both_firmware_targets_and_host_suites(self):
        for full, daily, publish in (
            (False, True, False),
            (True, False, True),
            (False, False, True),
        ):
            selected = select(
                ["README.md"], full=full, daily=daily, reuse=False, publish=publish
            )
            for suite in (
                "application",
                "firmware",
                "application_host",
                "host",
                "native",
            ):
                self.assertTrue(selected[suite], (full, daily, publish, suite))

    def test_integration_retention_verifies_complete_bundle_for_single_target_changes(
        self,
    ):
        for paths in (
            ["Development/system/coding/app/main.c"],
            [APP + "src/main.c"],
            ["README.md"],
        ):
            selected = select(paths, full=False, daily=False, reuse=False, retain=True)
            for suite in (
                "application",
                "firmware",
                "native",
                "host",
                "application_host",
            ):
                self.assertTrue(selected[suite], (paths, suite))

    def test_design_basis_changes_run_application_host_scenarios(self):
        for area in ("design", "architecture", "requirements"):
            selected = suites([f"Development/system/{area}/basis.md"])
            self.assertTrue(selected["application_host"] and selected["docs"])
            self.assertFalse(selected["firmware"] or selected["application"])
            self.assertFalse(selected["host"])

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
                "application": False,
                "native": False,
                "docs": False,
                "host": False,
                "tooling": False,
                "gate": True,
                "application_host": False,
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
                "application": False,
                "native": False,
                "docs": False,
                "application_host": False,
                "host": False,
                "tooling": True,
                "gate": False,
            },
        )


if __name__ == "__main__":
    unittest.main()
