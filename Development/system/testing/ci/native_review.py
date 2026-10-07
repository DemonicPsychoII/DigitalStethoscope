"""Stage native protection, then retire the legacy gate only after real approval probes."""

import argparse
import copy
import json
import subprocess
from pathlib import Path


def gh(*args: str) -> dict:
    return json.loads(subprocess.check_output(["gh", *args]))


def policy(source: dict, retire: bool = False) -> dict:
    result = {
        key: copy.deepcopy(source[key])
        for key in ("name", "target", "enforcement", "conditions", "rules")
    }
    if source.get("bypass_actors"):
        result["bypass_actors"] = copy.deepcopy(source["bypass_actors"])
    types = {rule["type"]: rule for rule in result["rules"]}
    review = types["pull_request"]["parameters"]
    review.update(
        required_approving_review_count=1,
        dismiss_stale_reviews_on_push=True,
        required_review_thread_resolution=True,
    )
    checks = types["required_status_checks"]["parameters"]["required_status_checks"]
    if not any(check["context"] == "agent-gate" for check in checks) and not retire:
        raise ValueError("prepare requires the existing agent-gate protection")
    if retire:
        checks[:] = [check for check in checks if check["context"] != "agent-gate"]
    return result


def probe(pr: dict, reviewer: str) -> None:
    if (
        pr["baseRefName"] != "integration"
        or pr["reviewDecision"] != "APPROVED"
        or pr["state"] != "OPEN"
        or pr["isDraft"]
    ):
        raise ValueError(
            "probe must demonstrate native APPROVED protection on integration"
        )
    if pr["author"]["login"] == reviewer:
        raise ValueError("fallback identity must be distinct from the PR author")
    # The probe must isolate this identity: another eligible approval could mask
    # an App review that GitHub does not count toward native protection.
    latest = {}
    for review in pr["reviews"]:
        if review["state"] in {"APPROVED", "CHANGES_REQUESTED", "DISMISSED"}:
            latest[review["author"]["login"]] = review
    if any(
        login != reviewer and review["state"] == "APPROVED"
        for login, review in latest.items()
    ):
        raise ValueError("probe must isolate the tested approving identity")
    reviews = [
        review
        for review in pr["reviews"]
        if review["author"]["login"] == reviewer
        and review["state"] in {"APPROVED", "CHANGES_REQUESTED", "DISMISSED"}
    ]
    if (
        not reviews
        or reviews[-1]["state"] != "APPROVED"
        or reviews[-1]["commit"]["oid"] != pr["headRefOid"]
    ):
        raise ValueError(
            "probe needs the reviewer's native approval on the current head"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "finish"))
    parser.add_argument("--repo", required=True)
    parser.add_argument("--ruleset", required=True, type=int)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--coderabbit-pr", type=int)
    parser.add_argument("--fallback-pr", type=int)
    parser.add_argument("--fallback-login")
    args = parser.parse_args()
    source = gh("api", f"repos/{args.repo}/rulesets/{args.ruleset}")
    if args.mode == "finish":
        params = next(r for r in source["rules"] if r["type"] == "pull_request")[
            "parameters"
        ]
        if params.get("required_approving_review_count", 0) < 1 or not params.get(
            "dismiss_stale_reviews_on_push"
        ):
            parser.error(
                "prepare must be applied before validating native approval probes"
            )
        if not all((args.coderabbit_pr, args.fallback_pr, args.fallback_login)):
            parser.error(
                "finish requires two real probe PRs and a separate fallback login"
            )
        if (
            args.fallback_login in {"coderabbitai", "coderabbitai[bot]"}
            or args.coderabbit_pr == args.fallback_pr
        ):
            parser.error("fallback must use a different identity and probe PR")
        fields = "author,baseRefName,headRefOid,reviewDecision,reviews,state,isDraft"
        for number, reviewer in (
            (args.coderabbit_pr, "coderabbitai"),
            (args.fallback_pr, args.fallback_login),
        ):
            pr = gh("pr", "view", str(number), "--repo", args.repo, "--json", fields)
            probe(pr, reviewer)
    proposed = policy(source, args.mode == "finish")
    print(json.dumps(proposed, indent=2))
    if not args.apply:
        print("Dry run. No settings changed.")
        return
    # Retain a local rollback snapshot; API tokens are never included.
    safe_repo = args.repo.replace("/", "_")
    snapshot = Path(
        f"artifacts/ci/native-review-before-{safe_repo}-{args.ruleset}.json"
    )
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    if not snapshot.exists():
        snapshot.write_text(json.dumps(source, indent=2) + "\n")
    subprocess.run(
        [
            "gh",
            "api",
            "--method",
            "PUT",
            f"repos/{args.repo}/rulesets/{args.ruleset}",
            "--input",
            "-",
        ],
        input=json.dumps(proposed),
        text=True,
        check=True,
    )
    if args.mode == "finish":
        subprocess.run(
            [
                "gh",
                "variable",
                "set",
                "CI_NATIVE_REVIEW",
                "--repo",
                args.repo,
                "--body",
                "true",
            ],
            check=True,
        )


if __name__ == "__main__":
    main()
