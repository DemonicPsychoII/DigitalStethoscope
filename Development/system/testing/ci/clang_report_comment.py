#!/usr/bin/env python3
"""Keep one comment per PR with the clang report of its latest verification run.

Runs from the default branch after "Mandatory quality gates" completes. It reads
clang/report.md from the run's static evidence and posts it to every open PR whose head is
still the run's head; a PR without the report gets a note that the reports did not run.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

MARKER = "<!-- clang-report -->"
AUTHOR = "github-actions[bot]"
MAXIMUM_BODY = 60_000
NOT_RUN = (
    "### Clang reports (information only)\n\n"
    "Not run: this verification run selected no application host tests, "
    "so clang-tidy, complexity, MC/DC and fuzzing did not run.\n"
)


def gh(*arguments: str, input_text: str | None = None) -> str:
    return subprocess.run(
        ["gh", *arguments],
        input=input_text,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def read_report(run: str, attempt: str, repository: str) -> str | None:
    with tempfile.TemporaryDirectory() as directory:
        downloaded = subprocess.run(
            [
                *("gh", "run", "download", run, "--repo", repository),
                *("--name", f"static-evidence-{attempt}", "--dir", directory),
            ],
            capture_output=True,
            text=True,
        )
        report = Path(directory, "clang/report.md")
        if downloaded.returncode or not report.is_file():
            return None
        return report.read_text(encoding="utf-8", errors="replace")


def body(report: str | None, head: str) -> str:
    text = report or NOT_RUN
    if len(text) > MAXIMUM_BODY:
        text = (
            text[:MAXIMUM_BODY]
            + "\n\n</details>\n\nThe report was shortened; the static evidence holds all of it.\n"
        )
    return f"{MARKER}\n{text}\n\nFor head `{head[:12]}`.\n"


def existing_comment(comments: list[dict]) -> int | None:
    for comment in comments:
        if comment["user"]["login"] == AUTHOR and comment["body"].startswith(MARKER):
            return comment["id"]
    return None


def main() -> None:
    repository = os.environ["GITHUB_REPOSITORY"]
    head = os.environ["HEAD_SHA"]
    pulls = json.loads(gh("api", f"repos/{repository}/commits/{head}/pulls"))
    targets = [
        pull["number"]
        for pull in pulls
        if pull["state"] == "open" and pull["head"]["sha"] == head
    ]
    if not targets:
        print(f"No open PR has head {head}; nothing to report.")
        return
    report = read_report(os.environ["RUN_ID"], os.environ["RUN_ATTEMPT"], repository)
    payload = json.dumps({"body": body(report, head)})
    for number in targets:
        comments = json.loads(
            gh(
                "api",
                "--paginate",
                "--slurp",
                f"repos/{repository}/issues/{number}/comments",
            )
        )
        found = existing_comment([comment for page in comments for comment in page])
        if found:
            gh(
                *("api", "--method", "PATCH"),
                f"repos/{repository}/issues/comments/{found}",
                *("--input", "-"),
                input_text=payload,
            )
        else:
            gh(
                *("api", "--method", "POST"),
                f"repos/{repository}/issues/{number}/comments",
                *("--input", "-"),
                input_text=payload,
            )
        print(f"Clang report {'updated' if found else 'posted'} on #{number}.")


if __name__ == "__main__":
    main()
