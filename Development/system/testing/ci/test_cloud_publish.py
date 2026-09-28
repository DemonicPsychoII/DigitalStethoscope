"""Local publishing is success-only and never runs in hosted Actions."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import run_ci


class CloudPublishTests(unittest.TestCase):
    def test_local_profiles_include_source_and_board(self):
        with (
            patch.dict(run_ci.os.environ, {"GITHUB_ACTIONS": "false"}),
            patch.object(
                run_ci.shutil, "which", return_value="/usr/local/bin/cloud-publish"
            ),
            patch.object(
                run_ci.subprocess, "check_output", side_effect=["a" * 40, " M source.c"]
            ),
            patch.object(run_ci, "run") as run,
        ):
            run_ci.publish_local_firmware()
        self.assertEqual(run.call_count, 3)
        for call in run.call_args_list:
            args = call.args[0]
            self.assertIn("Digital Stethoscope", args)
            self.assertIn(run_ci.BOARD, args)
            self.assertIn("a" * 40, args)
            self.assertIn("-dirty-", args[args.index("--version") + 1])
            self.assertTrue(args[-1].endswith("/zephyr/zephyr.bin"))

    def test_hosted_ci_does_not_publish(self):
        with (
            patch.dict(run_ci.os.environ, {"GITHUB_ACTIONS": "true"}),
            patch.object(run_ci.shutil, "which", return_value="cloud-publish"),
            patch.object(run_ci, "run") as run,
        ):
            run_ci.publish_local_firmware()
        run.assert_not_called()

    def test_failed_profile_never_publishes(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(run_ci, "ROOT", Path(directory)),
            patch.object(run_ci, "ARTIFACTS", Path(directory) / "artifacts"),
            patch.object(run_ci, "west", return_value="west"),
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
