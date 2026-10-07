"""Promote only successful integration artifacts for the exact current commit."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import zipfile
from pathlib import Path

from build_support import BOARD, PROFILES, ROOT
from firmware_release import PROJECT

ARTIFACT = re.compile(r"verified-firmware-[1-9][0-9]*$")


def api(path: str) -> dict:
    return json.loads(subprocess.check_output(["gh", "api", path]))


def eligible(run: dict, repo: str, sha: str) -> bool:
    return (
        run.get("status") == "completed"
        and run.get("conclusion") == "success"
        and run.get("event") == "push"
        and run.get("head_branch") == "integration"
        and run.get("head_sha") == sha
        and run.get("path", "").partition("@")[0]
        == ".github/workflows/quality-gates.yml"
        and run.get("head_repository", {}).get("full_name") == repo
    )


def find(repo: str, sha: str) -> int | None:
    runs = api(
        f"repos/{repo}/actions/workflows/quality-gates.yml/runs?branch=integration&event=push&status=success&per_page=30"
    )["workflow_runs"]
    for run in runs:
        if not eligible(run, repo, sha):
            continue
        artifacts = api(
            f"repos/{repo}/actions/runs/{run['id']}/artifacts?per_page=100"
        )["artifacts"]
        if any(ARTIFACT.fullmatch(a["name"]) and not a["expired"] for a in artifacts):
            return run["id"]
    return None


def extract(archive: Path, target: Path, sha: str) -> None:
    with zipfile.ZipFile(archive) as stream:
        entries = stream.infolist()
        if len(entries) > 8 or sum(e.file_size for e in entries) > 32 * 1024 * 1024:
            raise ValueError("firmware archive exceeds its bounded layout")
        if len({e.filename for e in entries}) != len(entries):
            raise ValueError("duplicate firmware archive members")
        manifest = json.loads(stream.read("manifest.json"))
        if (
            manifest.get("schema") != 1
            or manifest.get("project") != PROJECT
            or manifest.get("commit") != sha
            or manifest.get("board") != BOARD
            or manifest.get("dirty") is not False
            or manifest.get("channel") != "integration"
            or manifest.get("merge_commit") is not None
        ):
            raise ValueError(
                "firmware identity does not match the exact integration commit"
            )
        files = manifest["files"]
        if len(files) != len(PROFILES) or {f["profile"] for f in files} != set(
            PROFILES
        ):
            raise ValueError("incomplete firmware profiles")
        if len({f["name"] for f in files}) != len(files):
            raise ValueError("duplicate firmware names")
        expected = {"manifest.json", *(f["name"] for f in files)}
        if {e.filename for e in entries} != expected:
            raise ValueError("unexpected firmware archive members")
        validated = {}
        for file in files:
            name = file["name"]
            if Path(name).name != name or not name.endswith(".bin"):
                raise ValueError("unsafe firmware name")
            data = stream.read(name)
            if not data or hashlib.sha256(data).hexdigest() != file["sha256"]:
                raise ValueError("firmware checksum mismatch")
            validated[name] = data
        target.mkdir(parents=True, exist_ok=False)
        for name, data in validated.items():
            (target / name).write_bytes(data)
        (target / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def download(repo: str, sha: str, run_id: int) -> None:
    if not eligible(api(f"repos/{repo}/actions/runs/{run_id}"), repo, sha):
        raise ValueError("source run is no longer eligible")
    artifacts = api(f"repos/{repo}/actions/runs/{run_id}/artifacts?per_page=100")[
        "artifacts"
    ]
    candidates = [
        a for a in artifacts if ARTIFACT.fullmatch(a["name"]) and not a["expired"]
    ]
    if not candidates:
        raise ValueError(
            "source run no longer has an unexpired verified firmware artifact"
        )
    artifact = max(candidates, key=lambda a: a["id"])
    if artifact["size_in_bytes"] > 16 * 1024 * 1024:
        raise ValueError("firmware download too large")
    archive = ROOT / "artifacts/reuse.zip"
    archive.parent.mkdir(parents=True, exist_ok=True)
    with archive.open("wb") as stream:
        subprocess.run(
            ["gh", "api", f"repos/{repo}/actions/artifacts/{artifact['id']}/zip"],
            stdout=stream,
            check=True,
        )
    extract(archive, ROOT / "artifacts/firmware-release", sha)
    archive.unlink()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("find", "download"))
    parser.add_argument("--run", type=int)
    args = parser.parse_args()
    repo, sha = os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_SHA"]
    if args.mode == "find":
        run = find(repo, sha)
        with Path(os.environ["GITHUB_OUTPUT"]).open("a") as stream:
            stream.write(f"run={run or ''}\n")
    else:
        if not args.run:
            parser.error("download requires --run")
        download(repo, sha, args.run)


if __name__ == "__main__":
    main()
