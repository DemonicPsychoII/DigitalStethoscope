"""Skip the daily integration firmware build when integration has not moved.

Compares this scheduled run's commit with the newest successful scheduled or
dispatched integration run of this workflow. Unreadable history builds anyway.
"""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

BUILDING_EVENTS = {"schedule", "workflow_dispatch"}


def last_built_commit(runs: list[dict], current_run_id: int) -> str | None:
    """Runs arrive newest first. A skipped daily run still names a commit built earlier."""
    for run in runs:
        if (
            run["id"] != current_run_id
            and run["event"] in BUILDING_EVENTS
            and run["conclusion"] == "success"
            and run.get("published") is True
        ):
            return run["head_sha"]
    return None


def integration_runs(environ: dict[str, str]) -> list[dict]:
    url = (
        f"{environ.get('GITHUB_API_URL', 'https://api.github.com')}/repos/"
        f"{environ['GITHUB_REPOSITORY']}/actions/workflows/quality-gates.yml/runs"
        "?branch=integration&status=success&per_page=30"
    )
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {environ['GH_TOKEN']}",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        runs = json.load(response)["workflow_runs"]
    for run in runs:
        run["published"] = False
        if run["event"] not in BUILDING_EVENTS:
            continue
        request.full_url = (
            f"{environ.get('GITHUB_API_URL', 'https://api.github.com')}/repos/"
            f"{environ['GITHUB_REPOSITORY']}/actions/runs/{run['id']}/artifacts?per_page=100"
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            artifacts = json.load(response)["artifacts"]
        run["published"] = any(
            a["name"].startswith("firmware-build-") and not a["expired"]
            for a in artifacts
        )
    return runs


def main(environ: dict[str, str] = os.environ) -> None:
    try:
        previous = last_built_commit(
            integration_runs(environ), int(environ["GITHUB_RUN_ID"])
        )
    except (OSError, ValueError, KeyError) as error:
        print(f"Earlier runs unavailable ({error}); building.")
        previous = None
    build = previous != environ["GITHUB_SHA"]
    message = (
        f"Daily firmware build: integration moved to {environ['GITHUB_SHA'][:12]}."
        if build
        else f"Daily firmware build skipped: {previous[:12]} was already built."
    )
    print(message)
    with Path(environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as output:
        output.write(f"build={str(build).lower()}\n")
    if environ.get("GITHUB_STEP_SUMMARY"):
        with Path(environ["GITHUB_STEP_SUMMARY"]).open(
            "a", encoding="utf-8"
        ) as summary:
            summary.write(f"### {message}\n")


if __name__ == "__main__":
    main()
