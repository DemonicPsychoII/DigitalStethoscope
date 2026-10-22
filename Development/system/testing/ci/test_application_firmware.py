"""Build orchestration stages both targets and keeps their evidence distinct."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import run_ci
from build_support import RELEASE_COMPONENTS
from test_cloud_publish import IDENTITY


class ApplicationFirmwareTests(unittest.TestCase):
    def build(self, root: Path, omit_application: bool = False):
        commands = []

        def fake_run(command, **kwargs):
            commands.append(command)
            if "-b" not in command:
                return
            output = Path(command[command.index("-d") + 1])
            for relative in (
                ".config",
                "include/generated/zephyr/devicetree_generated.h",
                "zephyr.elf",
                "zephyr.bin",
                "zephyr.map",
            ):
                if (
                    omit_application
                    and output.name == "build-ci-app"
                    and relative == "zephyr.bin"
                ):
                    continue
                path = output / "zephyr" / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((output.name + relative).encode())

        with (
            patch.object(run_ci, "ROOT", root),
            patch.object(run_ci, "ARTIFACTS", root / "artifacts"),
            patch.object(run_ci, "west", return_value="west"),
            patch.object(run_ci, "run", side_effect=fake_run),
            patch.object(run_ci.firmware_release, "identity", return_value=IDENTITY),
            patch.object(run_ci, "publish_local_firmware") as publish,
            patch.object(run_ci, "summary"),
        ):
            if omit_application:
                with self.assertRaisesRegex(
                    SystemExit, "required firmware evidence missing"
                ):
                    run_ci.build()
                publish.assert_not_called()
            else:
                run_ci.build()
                publish.assert_called_once()
        return commands

    def test_complete_bundle_contains_identified_application_and_bringup_profiles(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            commands = self.build(root)
            release = root / "artifacts/firmware-release"
            manifest = json.loads((release / "manifest.json").read_text())
            self.assertEqual(
                {entry["profile"] for entry in manifest["files"]},
                set(RELEASE_COMPONENTS),
            )
            for entry in manifest["files"]:
                self.assertEqual(
                    entry["component"], RELEASE_COMPONENTS[entry["profile"]]
                )
                self.assertEqual(entry["version"], IDENTITY.version(entry["profile"]))
                self.assertTrue((release / entry["name"]).is_file())
            self.assertTrue((root / "artifacts/firmware/application/.config").is_file())
            self.assertTrue(
                (root / "artifacts/firmware/application/zephyr.elf").is_file()
            )
            for profile in RELEASE_COMPONENTS:
                self.assertTrue(
                    any(IDENTITY.cmake_arg(profile) in argv for argv in commands)
                )

    def test_missing_application_binary_blocks_the_whole_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.build(root, omit_application=True)
            self.assertFalse(
                (root / "artifacts/firmware-release/manifest.json").exists()
            )
