"""Select application verification while archived firmware has no active suite."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import firmware_changes
from firmware_changes import available_component_suites, needs_firmware, select, suites

APP = "Development/system/coding/app/"
CI = "Development/system/testing/ci/"
ARCHIVE = "preThesis/06-bringup-zephyr/"


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
            self.assertTrue(
                suites([f"{APP}{component}/service.md"])["application_host"]
            )

    def test_l1_suites_select_the_shared_host_step(self):
        for component, suite in (("WIFI", "wifi"), ("PORTAL", "portal")):
            with patch(
                "firmware_changes.available_component_suites", return_value=(suite,)
            ):
                self.assertTrue(
                    suites(
                        [
                            f"Development/system/design/{component}/interfaces-and-behavior.md"
                        ]
                    )["application_host"]
                )
                self.assertTrue(
                    suites([f"{APP}tests/host/l1_{component.lower()}/test_service.py"])[
                        "application_host"
                    ]
                )
                self.assertTrue(
                    select([], full=True, daily=False, reuse=False)["application_host"]
                )
                self.assertFalse(
                    suites(["Development/system/design/AUDIO/README.md"])[
                        "application_host"
                    ]
                )

    def test_missing_suite_skips_host_step_for_all_entry_points(self):
        with patch("firmware_changes.available_component_suites", return_value=()):
            self.assertFalse(
                suites(["Development/system/design/WIFI/README.md"])["application_host"]
            )
            for options in (
                {"full": True},
                {"retain": True},
                {"daily": True},
                {"publish": True},
            ):
                args = dict(full=False, daily=False, reuse=False, **{})
                args.update(options)
                selected = select([], **args)
                self.assertFalse(selected["application_host"])
                self.assertTrue(selected["application"])

    def test_suite_availability_follows_the_checked_out_tree(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(firmware_changes, "ROOT", Path(directory)),
        ):
            # Use the real availability function, independent of the fixture above.
            self.assertEqual(available_component_suites(), ())
            (Path(directory) / APP / "tests/host").mkdir(parents=True)
            self.assertEqual(available_component_suites(), ("communication",))
            for component in ("l1_wifi", "l1_portal"):
                (Path(directory) / APP / "tests/host" / component).mkdir()
            self.assertEqual(
                available_component_suites(), ("wifi", "portal", "communication")
            )
            (Path(directory) / APP / "tests/host/integration").mkdir()
            self.assertEqual(
                available_component_suites(),
                ("integration", "wifi", "portal", "communication"),
            )

    def test_real_service_integration_is_selected_at_the_same_boundaries(self):
        with patch(
            "firmware_changes.available_component_suites", return_value=("integration",)
        ):
            for path in (
                APP + "L1_services/L1_STORAGE/storage.c",
                APP + "L2_application/L2_COMMUNICATION/communication.c",
                "Development/system/design/PORTAL/interfaces-and-behavior.md",
                APP + "tests/host/integration/test_services.py",
            ):
                self.assertTrue(suites([path])["application_host"], path)
            self.assertFalse(
                suites(["Development/system/design/AUDIO/README.md"])[
                    "application_host"
                ]
            )

    def test_archive_changes_select_no_application_suite(self):
        for path in (
            "src/main.c",
            "qc/qc_eval.py",
            "tools/requirements.txt",
            "tests/host/test_dsp.py",
            "README.md",
        ):
            self.assertFalse(any(suites([ARCHIVE + path]).values()), path)
            self.assertFalse(needs_firmware([ARCHIVE + path]))

    def test_application_source_and_build_inputs_select_the_application(self):
        for path in (
            APP + "L1_services/L1_WIFI/wifi.c",
            APP + "prj.conf",
            APP + "boards/board.overlay",
            CI + "toolchain.json",
            CI + "build_support.py",
            ".github/workflows/quality-gates.yml",
        ):
            self.assertTrue(suites([path])["application"], path)
            self.assertTrue(suites([path])["application_host"], path)

    def test_host_tests_run_without_target_build(self):
        selected = suites([APP + "tests/host/test_communication.py"])
        self.assertTrue(selected["application_host"])
        self.assertTrue(selected["docs"])
        self.assertFalse(selected["application"])

    def test_daily_reuse_does_not_repeat_verified_suites(self):
        self.assertFalse(any(select([], full=False, daily=True, reuse=True).values()))
        rebuilt = select([], full=False, daily=True, reuse=False)
        self.assertTrue(rebuilt["application"] and rebuilt["application_host"])
        self.assertFalse(rebuilt["tooling"] or rebuilt["gate"])

    def test_publication_and_retention_verify_the_application(self):
        for options in (
            {"daily": True},
            {"publish": True},
            {"retain": True},
            {"full": True},
        ):
            args = dict(full=False, daily=False, reuse=False)
            args.update(options)
            selected = select(["README.md"], **args)
            self.assertTrue(selected["application"] and selected["application_host"])
            self.assertEqual(
                set(selected),
                {"application", "application_host", "docs", "tooling", "gate"},
            )

    def test_design_basis_runs_available_host_scenarios_without_build(self):
        for area in ("design", "architecture", "requirements"):
            selected = suites([f"Development/system/{area}/basis.md"])
            self.assertTrue(selected["application_host"] and selected["docs"])
            self.assertFalse(selected["application"])

    def test_documents_and_tooling_only_changes_do_not_compile(self):
        for path in (
            APP + "README.md",
            APP + "common/.gitkeep",
            CI + "test_daily_build.py",
            CI + "daily_build.py",
            CI + "firmware_changes.py",
        ):
            self.assertFalse(needs_firmware([path]), path)
        self.assertTrue(suites([CI + "test_daily_build.py"])["tooling"])
        self.assertEqual(
            {k for k, v in suites([".github/agent-gate/agent_gate.py"]).items() if v},
            {"gate"},
        )


class RevisionSelectionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        application = self.root / APP
        application.mkdir(parents=True)
        (application / "CMakeLists.txt").touch()
        self.git("init", "--quiet")
        self.git(
            "-c",
            "user.name=CI test",
            "-c",
            "user.email=ci@example.invalid",
            "commit",
            "--quiet",
            "--allow-empty",
            "-m",
            "Base",
        )
        self.base = self.git("rev-parse", "HEAD").strip()
        (self.root / "README.md").write_text("Documentation change\n", encoding="utf-8")
        self.git("add", "README.md")
        self.git(
            "-c",
            "user.name=CI test",
            "-c",
            "user.email=ci@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "Documentation",
        )

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, text=True)

    def run_selection(self, base):
        output = self.root / "outputs"
        output.write_text("", encoding="utf-8")
        with (
            patch.dict(
                os.environ,
                {
                    "BASE_SHA": base,
                    "HEAD_SHA": "HEAD",
                    "GITHUB_OUTPUT": str(output),
                    "CI_FULL": "false",
                    "CI_DAILY": "true",
                    "CI_PUBLISH": "false",
                    "CI_RETAIN": "false",
                    "REUSE": "123",
                },
            ),
            patch("firmware_changes.ROOT", self.root),
            patch("firmware_changes.available_component_suites", return_value=()),
        ):
            # Exercise the entry point with real Git objects, including its output file.
            previous = Path.cwd()
            try:
                os.chdir(self.root)
                firmware_changes.main()
            finally:
                os.chdir(previous)
        return dict(line.split("=", 1) for line in output.read_text().splitlines())

    def test_invalid_base_selects_full_suite_even_with_daily_reuse(self):
        blob = self.git("rev-parse", "HEAD:README.md").strip()
        for base in ("0" * 40, "f" * 40, blob, ""):
            with self.subTest(base=base):
                selected = self.run_selection(base)
                self.assertEqual(
                    selected,
                    {
                        "application": "true",
                        "docs": "true",
                        "tooling": "true",
                        "gate": "true",
                        "application_host": "false",
                    },
                )

    def test_valid_base_preserves_path_selection(self):
        previous = Path.cwd()
        try:
            os.chdir(self.root)
            self.assertEqual(
                firmware_changes.changed_paths(self.base, "HEAD"), ["README.md", ""]
            )
        finally:
            os.chdir(previous)


if __name__ == "__main__":
    unittest.main()
