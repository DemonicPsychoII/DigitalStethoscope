"""Event-driven failure confirmation; infrastructure failures never trigger a revert."""

import json
import os
import subprocess
from pathlib import Path

CODE_STEPS = frozenset(
    {
        "Run static repository checks",
        "Validate maintained documentation",
        "Test build tooling",
        "Test DSP and FHIR readback",
        "Run required QC evaluation",
        "Test the agent merge gate",
        "Pristine firmware build",
        "Test audio recovery and application logic",
    }
)


def failures(jobs: list[dict]) -> set[str]:
    return {
        step["name"]
        for job in jobs
        for step in job.get("steps", [])
        if step.get("conclusion") == "failure" and step["name"] in CODE_STEPS
    }


def decision(
    first: dict, current: dict, first_jobs: list[dict], current_jobs: list[dict]
) -> str:
    if current["run_attempt"] == 1:
        return "rerun" if current["conclusion"] == "failure" else "ignore"
    if current["run_attempt"] != 2 or first.get("conclusion") != "failure":
        return "ignore"
    if current["conclusion"] == "success":
        return "recovered"
    if current["conclusion"] == "failure" and failures(first_jobs) & failures(
        current_jobs
    ):
        return "confirmed"
    return "infrastructure-or-unconfirmed"


def api(path: str) -> dict:
    return json.loads(subprocess.check_output(["gh", "api", path]))


def main() -> None:
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    run = event["workflow_run"]
    if run["event"] != "push" or run["head_branch"] != "integration":
        raise SystemExit("recovery accepts only integration push runs")
    repo = os.environ["GITHUB_REPOSITORY"]
    base = f"repos/{repo}/actions/runs/{run['id']}"
    first = api(base + "/attempts/1")
    # Explicit attempt endpoints avoid mixing jobs from a later manual rerun.
    first_jobs = api(base + "/attempts/1/jobs?per_page=100")["jobs"]
    current_jobs = api(base + f"/attempts/{run['run_attempt']}/jobs?per_page=100")[
        "jobs"
    ]
    result = decision(first, run, first_jobs, current_jobs)
    if result == "rerun":
        request = subprocess.run(
            ["gh", "run", "rerun", str(run["id"]), "--repo", repo, "--failed"],
            check=False,
        )
        if request.returncode:
            result = "rerun-request-failed"
    with Path(os.environ["GITHUB_OUTPUT"]).open("a") as stream:
        stream.write(f"result={result}\n")
    print(f"Recovery decision: {result}; no runner waits for the rerun.")


if __name__ == "__main__":
    main()
