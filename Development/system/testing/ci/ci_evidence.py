"""Record the actual tested tree separately from the PR's advertised head."""

import json
import os
import subprocess
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[4]
    target = root / "artifacts/ci"
    target.mkdir(parents=True, exist_ok=True)
    event = (
        json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
        if os.environ.get("GITHUB_EVENT_PATH")
        else {}
    )
    pr = event.get("pull_request", {})
    data = {
        "tested_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
        "tested_tree": subprocess.check_output(
            ["git", "rev-parse", "HEAD^{tree}"], cwd=root, text=True
        ).strip(),
        "pr_head": pr.get("head", {}).get("sha"),
        "base": pr.get("base", {}).get("sha"),
        "event": os.environ.get("GITHUB_EVENT_NAME", "local"),
        "run": os.environ.get("GITHUB_RUN_ID"),
        "attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "toolchain": json.loads(
            (root / "Development/system/testing/ci/toolchain.json").read_text()
        ),
        "selection": {
            key: os.environ.get(key)
            for key in (
                "FIRMWARE",
                "NATIVE",
                "HOST",
                "TOOLING",
                "GATE",
                "QC",
                "DOCS",
                "DAILY",
                "PUBLISH",
                "REUSE",
            )
        },
    }
    (target / "identity.json").write_text(json.dumps(data, indent=2) + "\n")


if __name__ == "__main__":
    main()
