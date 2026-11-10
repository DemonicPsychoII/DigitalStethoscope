"""Labels never create quality-gate runs; the firmware label re-runs a head's verification."""

import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

import firmware_label
from firmware_label import RERUN, decision, pull_request_numbers, verification_run

ROOT = Path(__file__).resolve().parents[4]
REPOSITORY = "owner/thesis"
HEAD = "a" * 40


def workflow(name: str) -> dict:
    return yaml.safe_load(
        (ROOT / ".github/workflows" / name).read_text(encoding="utf-8")
    )


def pull(labels=("firmware",), state="open", repository=REPOSITORY):
    return {
        "state": state,
        "head": {
            "sha": HEAD,
            "repo": {"full_name": repository} if repository else None,
        },
        "labels": [{"name": name} for name in labels],
    }


def run(run_id=7, status="completed", conclusion="success", attempt=1, sha=HEAD):
    return {
        "id": run_id,
        "event": "pull_request",
        "head_sha": sha,
        "status": status,
        "conclusion": conclusion,
        "run_attempt": attempt,
    }


class WorkflowTests(unittest.TestCase):
    def test_labels_never_trigger_the_quality_gates(self):
        quality = workflow("quality-gates.yml")
        # PyYAML reads the `on:` key as boolean true.
        types = quality[True]["pull_request"]["types"]
        self.assertNotIn("labeled", types)
        self.assertNotIn("unlabeled", types)

    def test_required_check_names_do_not_depend_on_the_event(self):
        jobs = workflow("quality-gates.yml")["jobs"]
        self.assertEqual(jobs["static"]["name"], "Quality / Static Checks")
        self.assertEqual(jobs["firmware"]["name"], "Zephyr / Firmware Build")

    def test_publication_reads_the_live_label(self):
        plan = workflow("quality-gates.yml")["jobs"]["plan"]
        self.assertIn(
            "steps.label.outputs.firmware == 'true'", plan["outputs"]["publish"]
        )
        self.assertNotIn("github.event.pull_request.labels", str(plan))

    def test_label_workflow_runs_trusted_code_only(self):
        label = workflow("firmware-label.yml")
        self.assertEqual(label[True]["pull_request_target"]["types"], ["labeled"])
        checkout = label["jobs"]["rerun"]["steps"][0]
        self.assertEqual(
            checkout["with"]["ref"], "${{ github.event.repository.default_branch }}"
        )


class DecisionTests(unittest.TestCase):
    def test_green_unpublished_head_is_re_run(self):
        self.assertEqual(decision(pull(), REPOSITORY, run(), []), RERUN)

    def test_published_attempt_is_not_re_run(self):
        artifacts = [{"name": "firmware-build-2", "expired": False}]
        self.assertNotEqual(
            decision(pull(), REPOSITORY, run(attempt=2), artifacts), RERUN
        )

    def test_expired_or_earlier_attempt_artifact_does_not_count(self):
        artifacts = [
            {"name": "firmware-build-1", "expired": False},
            {"name": "firmware-build-2", "expired": True},
        ]
        self.assertEqual(decision(pull(), REPOSITORY, run(attempt=2), artifacts), RERUN)

    def test_an_automatic_attempt_that_did_not_publish_is_not_re_run_again(self):
        current = dict(
            run(attempt=2), triggering_actor={"login": "github-actions[bot]"}
        )
        self.assertNotEqual(decision(pull(), REPOSITORY, current, []), RERUN)
        current["triggering_actor"] = {"login": "DemonicPsychoII"}
        self.assertEqual(decision(pull(), REPOSITORY, current, []), RERUN)

    def test_running_failed_or_missing_verification_is_not_re_run(self):
        for current in (
            run(status="in_progress", conclusion=None),
            run(conclusion="failure"),
            run(conclusion="cancelled"),
            None,
        ):
            with self.subTest(current=current):
                self.assertNotEqual(decision(pull(), REPOSITORY, current, []), RERUN)

    def test_unlabelled_closed_and_fork_pull_requests_are_not_re_run(self):
        for current in (
            pull(labels=("Process",)),
            pull(state="closed"),
            pull(repository="fork/thesis"),
            pull(repository=None),
        ):
            with self.subTest(pull=current):
                self.assertNotEqual(decision(current, REPOSITORY, run(), []), RERUN)


class RunSelectionTests(unittest.TestCase):
    def test_newest_verification_run_of_the_head_is_selected(self):
        runs = [run(5), run(9, conclusion="failure"), run(11, sha="b" * 40)]
        self.assertEqual(verification_run(runs, HEAD)["id"], 9)

    def test_label_only_runs_of_the_former_workflow_are_never_selected(self):
        runs = [run(5), run(6, conclusion="skipped")]
        self.assertEqual(verification_run(runs, HEAD)["id"], 5)
        self.assertIsNone(verification_run([run(6, conclusion="skipped")], HEAD))


class PullRequestTests(unittest.TestCase):
    def test_label_event_names_its_pull_request(self):
        event = {"pull_request": {"number": 3}}
        self.assertEqual(
            pull_request_numbers("pull_request_target", event, REPOSITORY), [3]
        )

    def test_completion_falls_back_to_the_branch_pull_requests(self):
        event = {"workflow_run": {"pull_requests": [], "head_branch": "fix/139-label"}}
        with patch.object(firmware_label, "api", return_value=[{"number": 4}]) as api:
            self.assertEqual(
                pull_request_numbers("workflow_run", event, REPOSITORY), [4]
            )
        api.assert_called_once_with(
            "repos/owner/thesis/pulls?state=open&head=owner%3Afix%2F139-label"
        )


if __name__ == "__main__":
    unittest.main()
