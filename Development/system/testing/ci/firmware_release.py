"""Firmware build identity, boot-banner string and release staging.

The same identity string is compiled into the firmware (printed at boot and by
`stetho version`) and recorded as the Personal Cloud version, so a flashed board
can be matched to its download.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

PROJECT = "Digital Stethoscope"
COMMIT = re.compile(r"[0-9a-f]{40}")
# Matches the CMake check on STETHO_BUILD_ID; anything else becomes "-".
UNSAFE = re.compile(r"[^A-Za-z0-9._:+/-]")
# Branch names Personal Cloud accepts as provenance.
BRANCH = re.compile(r"(?!.*\.\.)[A-Za-z0-9._-][A-Za-z0-9._/-]{0,99}")


@dataclass(frozen=True)
class Identity:
    channel: str
    commit: str
    merge_commit: str | None
    dirty: bool
    built_at: str
    branch: str | None

    def version(self, profile: str) -> str:
        """e.g. 'pr-12 1a2b3c4d5e6f+merge qc 20261002T031705Z'."""
        commit = self.commit[:12]
        commit += "+merge" if self.merge_commit else ""
        commit += "-dirty" if self.dirty else ""
        stamp = self.built_at.replace("-", "").replace(":", "")
        return f"{UNSAFE.sub('-', self.channel)[:48]} {commit} {profile} {stamp}"

    def cmake_arg(self, profile: str) -> str:
        return f"-DSTETHO_BUILD_ID={self.version(profile)}"


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def identity(
    root: Path,
    environ: Mapping[str, str] = os.environ,
    now: datetime | None = None,
) -> Identity:
    """Local builds default to channel 'local' and the checked-out commit.

    CI sets STETHO_BUILD_CHANNEL and STETHO_BUILD_COMMIT. For pull requests the
    checkout is GitHub's merge of the PR head into its base, so the named head
    commit differs from HEAD and the compiled tree is recorded separately.
    """
    head = git(root, "rev-parse", "HEAD")
    commit = environ.get("STETHO_BUILD_COMMIT") or head
    if not COMMIT.fullmatch(commit):
        raise SystemExit("STETHO_BUILD_COMMIT must be a full 40-character commit")
    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD")
    return Identity(
        channel=environ.get("STETHO_BUILD_CHANNEL") or "local",
        commit=commit,
        merge_commit=head if head != commit else None,
        # Like `git describe --dirty`: tracked changes only; build output is ignored.
        dirty=bool(git(root, "status", "--porcelain", "--untracked-files=no")),
        built_at=(now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        branch=branch if branch != "HEAD" and BRANCH.fullmatch(branch) else None,
    )


def stage(
    build: Identity, outputs: list[tuple[str, Path]], target: Path, board: str
) -> dict:
    """Copy each profile image under a descriptive name and write manifest.json."""
    shutil.rmtree(target, ignore_errors=True)
    target.mkdir(parents=True)
    slug = UNSAFE.sub("-", build.channel).replace("/", "-")[:48]
    files = []
    for profile, source in outputs:
        name = f"stethoscope-{slug}-{build.commit[:12]}-{profile}.bin"
        shutil.copy2(source, target / name)
        files.append(
            {
                "name": name,
                "profile": profile,
                "version": build.version(profile),
                "sha256": hashlib.sha256((target / name).read_bytes()).hexdigest(),
            }
        )
    manifest = {
        "schema": 1,
        "project": PROJECT,
        "channel": build.channel,
        "commit": build.commit,
        "merge_commit": build.merge_commit,
        "dirty": build.dirty,
        "built_at": build.built_at,
        "board": board,
        "files": files,
    }
    (target / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest
