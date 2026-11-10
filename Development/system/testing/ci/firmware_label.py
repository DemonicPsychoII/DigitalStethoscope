"""Re-run a PR head's verification so that the `firmware` label publishes its firmware.

Labels do not trigger quality-gates.yml: a label-only run would become the newest run of that
workflow for the head and hide its required checks (#139). A re-run keeps the run, its event and
its required check names; its plan reads the live label and selects the application build.
"""

import json
import os
import subprocess
import urllib.parse
from pathlib import Path

WORKFLOW = "quality-gates.yml"
LABEL = "firmware"
RERUN = "rerun"
AUTOMATION = "github-actions[bot]"


def verification_run(runs: list[dict], head_sha: str) -> dict | None:
    """The head's newest verification run. Label-only runs of the former workflow concluded
    skipped and verified nothing, so they are never re-run."""
    candidates = [
        run
        for run in runs
        if run["event"] == "pull_request"
        and run["head_sha"] == head_sha
        and run.get("conclusion") != "skipped"
    ]
    return max(candidates, key=lambda run: run["id"], default=None)


def decision(
    pull: dict, repository: str, run: dict | None, artifacts: list[dict]
) -> str:
    """RERUN, or the reason why the head needs no re-run."""
    if (
        pull["state"] != "open"
        or (pull["head"].get("repo") or {}).get("full_name") != repository
    ):
        return "closed or fork pull request; nothing publishes"
    if LABEL not in {label["name"] for label in pull["labels"]}:
        return f"no `{LABEL}` label"
    if run is None:
        return "no verification run yet; its plan reads the label"
    if run["status"] != "completed":
        return "verification is running; its completion is checked again"
    if run["conclusion"] != "success":
        return f"verification concluded {run['conclusion']}; only a green run publishes"
    published = f"firmware-build-{run['run_attempt']}"
    if any(
        artifact["name"] == published and not artifact["expired"]
        for artifact in artifacts
    ):
        return f"attempt {run['run_attempt']} already uploaded {published}"
    # Stops a re-run loop if a requested attempt still selected no publication.
    if (run.get("triggering_actor") or {}).get("login") == AUTOMATION:
        return (
            f"automatic attempt {run['run_attempt']} did not publish; inspect its plan"
        )
    return RERUN


def api(path: str, method: str = "GET") -> dict | list | None:
    output = subprocess.check_output(["gh", "api", "--method", method, path])
    return json.loads(output) if output.strip() else None


def pull_request_numbers(event_name: str, event: dict, repository: str) -> list[int]:
    if event_name == "pull_request_target":
        return [event["pull_request"]["number"]]
    run = event["workflow_run"]
    numbers = [pull["number"] for pull in run.get("pull_requests") or []]
    if numbers:
        return numbers
    # GitHub sometimes leaves a run's pull_requests empty; fall back to the branch's open PRs.
    owner = repository.split("/")[0]
    head = urllib.parse.quote(f"{owner}:{run['head_branch']}", safe="")
    return [
        pull["number"]
        for pull in api(f"repos/{repository}/pulls?state=open&head={head}")
    ]


def main() -> None:
    repository = os.environ["GITHUB_REPOSITORY"]
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    for number in pull_request_numbers(
        os.environ["GITHUB_EVENT_NAME"], event, repository
    ):
        pull = api(f"repos/{repository}/pulls/{number}")
        head_sha = pull["head"]["sha"]
        runs = api(
            f"repos/{repository}/actions/workflows/{WORKFLOW}/runs"
            f"?event=pull_request&head_sha={head_sha}&per_page=100"
        )["workflow_runs"]
        run = verification_run(runs, head_sha)
        artifacts = (
            api(f"repos/{repository}/actions/runs/{run['id']}/artifacts?per_page=100")[
                "artifacts"
            ]
            if run
            else []
        )
        result = decision(pull, repository, run, artifacts)
        if result == RERUN:
            api(f"repos/{repository}/actions/runs/{run['id']}/rerun", method="POST")
            print(
                f"PR #{number}: re-running verification run {run['id']} to publish {head_sha[:12]}"
            )
        else:
            print(f"PR #{number}: {result}")


if __name__ == "__main__":
    main()
