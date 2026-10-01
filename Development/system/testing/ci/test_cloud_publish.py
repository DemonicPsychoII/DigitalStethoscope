"""Local publishing is success-only and never runs in hosted Actions."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import run_ci


IDENTITY = run_ci.firmware_release.Identity(
    channel="local",
    commit="a" * 40,
    merge_commit=None,
    dirty=True,
    built_at="2026-10-02T03:17:05Z",
    branch="feat/x",
)
MANIFEST = {
    "files": [
        {
            "name": f"stethoscope-local-{profile}.bin",
            "profile": profile,
            "version": profile,
        }
        for profile, _ in run_ci.PROFILES
    ]
}


class CloudPublishTests(unittest.TestCase):
    def test_local_profiles_include_source_board_and_provenance(self):
        with (
            patch.dict(run_ci.os.environ, {"GITHUB_ACTIONS": "false"}),
            patch.object(
                run_ci.shutil, "which", return_value="/usr/local/bin/cloud-publish"
            ),
            patch.object(run_ci, "run") as run,
        ):
            run_ci.publish_local_firmware(IDENTITY, MANIFEST, Path("/release"))
        self.assertEqual(run.call_count, 4)
        build_id = "local-20261002T031705Z-" + "a" * 12
        self.assertEqual(
            run.call_args.args[0],
            ["/usr/local/bin/cloud-publish", "--retire", "local", "--keep", build_id],
        )
        for call, (profile, _) in zip(run.call_args_list, run_ci.PROFILES):
            args = call.args[0]
            option = dict(zip(args[1:-1:2], args[2:-1:2]))
            self.assertEqual(option["--project"], "Digital Stethoscope")
            self.assertEqual(option["--board"], run_ci.BOARD)
            self.assertEqual(option["--commit"], "a" * 40)
            self.assertEqual(option["--source"], "local")
            self.assertEqual(option["--profile"], profile)
            self.assertEqual(option["--parts"], "3")
            self.assertEqual(option["--build"], "local-20261002T031705Z-" + "a" * 12)
            self.assertIn("--dirty", args)
            self.assertEqual(args[-1], f"/release/stethoscope-local-{profile}.bin")

    def test_failed_upload_retires_only_the_partial_build(self):
        with (
            patch.dict(run_ci.os.environ, {"GITHUB_ACTIONS": "false"}),
            patch.object(run_ci.shutil, "which", return_value="cloud-publish"),
            patch.object(
                run_ci, "run", side_effect=[None, SystemExit("upload")]
            ) as run,
            patch.object(run_ci.subprocess, "run") as cleanup,
        ):
            with self.assertRaises(SystemExit):
                run_ci.publish_local_firmware(IDENTITY, MANIFEST, Path("/release"))
        self.assertEqual(run.call_count, 2)
        cleanup.assert_called_once_with(
            [
                "cloud-publish",
                "--retire",
                "local",
                "--build",
                "local-20261002T031705Z-" + "a" * 12,
            ]
        )

    def test_hosted_ci_does_not_publish(self):
        with (
            patch.dict(run_ci.os.environ, {"GITHUB_ACTIONS": "true"}),
            patch.object(run_ci.shutil, "which", return_value="cloud-publish"),
            patch.object(run_ci, "run") as run,
        ):
            run_ci.publish_local_firmware(IDENTITY, MANIFEST, Path("/release"))
        run.assert_not_called()

    def test_failed_profile_never_publishes(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(run_ci, "ROOT", Path(directory)),
            patch.object(run_ci, "ARTIFACTS", Path(directory) / "artifacts"),
            patch.object(run_ci, "west", return_value="west"),
            patch.object(run_ci.firmware_release, "identity", return_value=IDENTITY),
            patch.object(Path, "is_file", return_value=True),
            patch.object(run_ci.shutil, "copy2"),
            patch.object(
                run_ci,
                "run",
                side_effect=[None, None, None, None, SystemExit("build failed")],
            ),
            patch.object(run_ci, "publish_local_firmware") as publish,
        ):
            with self.assertRaises(SystemExit):
                run_ci.build()
        publish.assert_not_called()


if __name__ == "__main__":
    unittest.main()
