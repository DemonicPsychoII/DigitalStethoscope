#!/usr/bin/env python3
"""Check and copy the files that the company GitLab repository receives.

The GitLab repository holds the product: specification, requirements, architecture, design,
code and the reference code. `check` fails when one of those files carries what a product
document must not carry or links to a file that is not transferred. `export` copies the
checked set into a GitLab checkout and removes transferred files that no longer exist here.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[4]
SYSTEM = "Development/system/"

# Every tracked file below these folders is transferred, except the exclusions.
TRANSFERRED_FOLDERS = (
    SYSTEM + "spec/",
    SYSTEM + "requirements/",
    SYSTEM + "architecture/",
    SYSTEM + "design/",
    SYSTEM + "coding/",
    SYSTEM + "references/",
)
TRANSFERRED_FILES = (SYSTEM + "testing/verification-allocation.md",)
EXCLUDED_FOLDERS = (SYSTEM + "coding/app/tests/",)
# The root page of the GitLab repository has its own text.
GITLAB_README_SOURCE = SYSTEM + "process/gitlab-readme.md"
GITLAB_README_TARGET = "README.md"

TEXT_SUFFIXES = {
    ".c",
    ".cmake",
    ".conf",
    ".cpp",
    ".dtsi",
    ".h",
    ".html",
    ".json",
    ".ld",
    ".md",
    ".overlay",
    ".ps1",
    ".puml",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"

# Each rule: name, pattern, and a predicate that says whether a matching line is acceptable.
RULES = (
    ("project member", re.compile(r"\bNico\b|\bSummerer\b"), lambda line: False),
    (
        "written date outside a source entry",
        re.compile(rf"\b\d{{1,2}} (?:{MONTHS}) 20\d\d\b"),
        lambda line: bool(re.match(r"\s*\[S?\d+\]", line)) or "accessed" in line,
    ),
    (
        "decision record",
        re.compile(r"project decision|personal communication", re.I),
        lambda line: False,
    ),
    ("ticket id", re.compile(r"\bTICKET-\d+"), lambda line: False),
    (
        "chat or agent trace",
        re.compile(r"t3-thread|on behalf of|\bGPT-\d|\bClaude\b|\bGemini\b"),
        lambda line: False,
    ),
    (
        "private network detail",
        re.compile(
            r"\b192\.168\.\d+\.\d+|\bnglegion\b|tail[0-9a-f]{6}\.ts\.net|gitlab\.newtec",
            re.I,
        ),
        # 192.168.4.0/24 is the network of the device's own setup hotspot.
        lambda line: not re.search(r"nglegion|ts\.net|gitlab\.newtec", line, re.I)
        and all(
            address.startswith("192.168.4.")
            for address in re.findall(r"\b192\.168\.\d+\.\d+", line)
        ),
    ),
    (
        "link into a folder that is not transferred",
        re.compile(r"\]\([^)]*(?:planning|thesis-material|preThesis)/"),
        lambda line: False,
    ),
)

# Accepted findings, each with its reason: (path, rule name).
ACCEPTED = {
    # Working configuration of the lab deployment; tracked in the issue on the lab profile.
    (SYSTEM + "coding/server-profiles/lab-hapi.toml", "private network detail"),
}


def tracked_files(root: Path) -> list[str]:
    """Return the paths git tracks, relative to the repository root."""
    output = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True
    ).stdout.decode("utf-8")
    return [path for path in output.split("\0") if path]


def transfer_set(paths: list[str]) -> list[str]:
    """Select the transferred files from the tracked paths."""
    selected = []
    for path in paths:
        in_folder = path.startswith(TRANSFERRED_FOLDERS) and not path.startswith(
            EXCLUDED_FOLDERS
        )
        if in_folder or path in TRANSFERRED_FILES:
            selected.append(path)
    return sorted(selected)


def content_findings(path: str, text: str) -> list[str]:
    """Return the rule violations of one file."""
    findings = []
    in_source_entry = False
    for number, line in enumerate(text.splitlines(), start=1):
        # A source entry runs from its "[n]" marker to the next blank line.
        if not line.strip():
            in_source_entry = False
        elif re.match(r"\s*\[S?\d+\]\s", line):
            in_source_entry = True
        for name, pattern, acceptable in RULES:
            if (path, name) in ACCEPTED:
                continue
            if name == "written date outside a source entry" and in_source_entry:
                continue
            if pattern.search(line) and not acceptable(line):
                findings.append(f"{path}:{number}: {name}: {line.strip()[:120]}")
    return findings


def link_findings(path: str, text: str, selected: set[str]) -> list[str]:
    """Return the relative links of a Markdown file whose target is not transferred."""
    findings = []
    if not path.endswith(".md"):
        return findings
    folder = Path(path).parent
    for number, line in enumerate(text.splitlines(), start=1):
        for raw in re.findall(r"\]\(([^)\s]+)\)", line):
            link = urlsplit(raw)
            if link.scheme or link.netloc or not link.path:
                continue
            target = (folder / unquote(link.path)).as_posix()
            parts: list[str] = []
            for part in target.split("/"):
                if part == "..":
                    if parts:
                        parts.pop()
                elif part not in ("", "."):
                    parts.append(part)
            normalized = "/".join(parts)
            is_folder = any(
                candidate.startswith(normalized + "/") for candidate in selected
            )
            if normalized not in selected and not is_folder:
                findings.append(
                    f"{path}:{number}: link to a file that is not transferred: {raw}"
                )
    return findings


def check(root: Path = ROOT, paths: list[str] | None = None) -> list[str]:
    """Return every finding of the transferred set."""
    selected = transfer_set(tracked_files(root) if paths is None else paths)
    selected_set = set(selected)
    findings = []
    for path in selected + [GITLAB_README_SOURCE]:
        file = root / path
        if not file.is_file():
            if path == GITLAB_README_SOURCE:
                findings.append(
                    f"{path}: the root page of the GitLab repository is missing"
                )
            continue
        if file.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = file.read_text(encoding="utf-8", errors="replace")
        findings.extend(content_findings(path, text))
        if path != GITLAB_README_SOURCE:
            findings.extend(link_findings(path, text, selected_set))
    return findings


def export(destination: Path, root: Path = ROOT) -> tuple[int, int]:
    """Copy the transferred set into a GitLab checkout and remove files that left the set."""
    selected = transfer_set(tracked_files(root))
    selected_set = set(selected)
    removed = 0
    for folder in TRANSFERRED_FOLDERS:
        target_folder = destination / folder
        if not target_folder.is_dir():
            continue
        for file in sorted(target_folder.rglob("*")):
            relative = file.relative_to(destination).as_posix()
            if file.is_file() and relative not in selected_set:
                file.unlink()
                removed += 1
    for path in selected:
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / path, target)
    shutil.copyfile(root / GITLAB_README_SOURCE, destination / GITLAB_README_TARGET)
    return len(selected) + 1, removed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="report what must not reach GitLab")
    commands.add_parser("list", help="print the transferred files")
    export_parser = commands.add_parser(
        "export", help="copy the transferred files into a GitLab checkout"
    )
    export_parser.add_argument("destination", type=Path)
    arguments = parser.parse_args()

    if arguments.command == "list":
        print("\n".join(transfer_set(tracked_files(ROOT))))
        return 0
    findings = check()
    if findings:
        print("\n".join(findings))
        print(
            f"{len(findings)} finding(s): the transfer set is not clean.",
            file=sys.stderr,
        )
        return 1
    if arguments.command == "check":
        print("Transfer set is clean.")
        return 0
    if not (arguments.destination / ".git").exists():
        print(f"{arguments.destination} is not a git checkout.", file=sys.stderr)
        return 2
    copied, removed = export(arguments.destination)
    print(
        f"Copied {copied} file(s) and removed {removed} file(s) in {arguments.destination}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
