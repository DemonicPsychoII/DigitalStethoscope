"""The daily build is skipped only for a commit an earlier building run succeeded on."""

import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

import daily_build

HEAD = "a" * 40


def run(run_id, sha, event="schedule", conclusion="success"):
    return {"id": run_id, "head_sha": sha, "event": event, "conclusion": conclusion}


class DailyBuildTests(unittest.TestCase):
    def decide(self, runs):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            environ = {
                "GITHUB_SHA": HEAD,
                "GITHUB_RUN_ID": "9",
                "GITHUB_OUTPUT": str(output),
                "GITHUB_REPOSITORY": "owner/thesis",
                "GH_TOKEN": "token",
            }
            fetch = (
                {"side_effect": runs}
                if isinstance(runs, Exception)
                else {"return_value": runs}
            )
            with (
                patch.object(daily_build, "integration_runs", **fetch),
                patch("builtins.print"),
            ):
                daily_build.main(environ)
            return output.read_text()

    def test_unchanged_head_skips_the_build(self):
        self.assertEqual(self.decide([run(8, HEAD)]), "build=false\n")
        manual = [run(8, HEAD, event="workflow_dispatch"), run(7, "b" * 40)]
        self.assertEqual(self.decide(manual), "build=false\n")

    def test_new_commit_or_no_history_builds(self):
        self.assertEqual(self.decide([run(8, "b" * 40), run(7, HEAD)]), "build=true\n")
        self.assertEqual(self.decide([]), "build=true\n")

    def test_only_successful_building_runs_of_other_ids_count(self):
        for runs in (
            [run(9, HEAD)],
            [run(8, HEAD, event="pull_request")],
            [run(8, HEAD, conclusion="failure")],
        ):
            with self.subTest(runs=runs):
                self.assertEqual(self.decide(runs), "build=true\n")

    def test_unreadable_history_builds(self):
        error = urllib.error.URLError("offline")
        self.assertEqual(self.decide(error), "build=true\n")


if __name__ == "__main__":
    unittest.main()
