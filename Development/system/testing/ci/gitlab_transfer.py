#!/usr/bin/env python3
"""Check and export the files that the company GitLab repository receives.

The GitLab repository holds the product: specification, requirements, architecture, design,
code and the reference code. Both commands work on one committed snapshot, never on the
working tree. `check` fails when a file of that snapshot carries what a product document must
not carry, repeats a finding of the supervisor's reviews or links to a file that is not
transferred. The documentation check of the static stage runs the same rules on the working tree. `export` writes the checked snapshot
into a new, empty directory. It changes nothing else: copying that directory into a GitLab
checkout is a separate, reviewed step.
"""

from __future__ import annotations

import argparse
import io
import os
import posixpath
import re
import subprocess
import sys
import tarfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[4]
SYSTEM = "Development/system/"

# Every committed file below these folders is transferred, except the exclusions.
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
# The root page of the GitLab repository has its own text. Its links are written relative to
# its place in this repository and are rewritten for the root when it is exported.
GITLAB_README_SOURCE = SYSTEM + "process/gitlab-readme.md"
GITLAB_README_TARGET = "README.md"

# Files that are not UTF-8 text need an entry here before they can be transferred.
BINARY_SUFFIXES: frozenset[str] = frozenset()

MONTHS = (
    "Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|"
    "Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?"
)
DATE = re.compile(rf"\b\d{{1,2}}\.? (?:{MONTHS})\.? 20\d\d\b|\b20\d\d-[01]\d-[0-3]\d\b")
# Inside a source entry a date is the publication or access date unless the line narrates.
NARRATION = re.compile(
    r"\b(?:checked|reviewed|decided|confirmed|measured|agreed|accepted)\b", re.I
)
PRIVATE_ADDRESS = re.compile(
    r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b"
)
PRIVATE_NAME = re.compile(
    r"\bnglegion\b|\b[\w-]+\.(?:local|lan|internal|zz)\b|tail[0-9a-f]{6}\.ts\.net|[\w.+-]+@[\w-]+\.[\w.-]+",
    re.I,
)
# 192.168.4.0/24 is the network of the device's own setup hotspot.
PUBLIC_VALUES = re.compile(r"^192\.168\.4\.\d{1,3}$")

# Each rule: name and a function that returns the offending parts of a line.
RULES = (
    ("project member", lambda line: re.findall(r"\bNico\b|\bSummerer\b", line, re.I)),
    (
        "decision record",
        lambda line: re.findall(r"project decision|personal communication", line, re.I),
    ),
    ("ticket id", lambda line: re.findall(r"\bTICKET-\d+", line)),
    (
        "chat or agent trace",
        lambda line: re.findall(
            r"t3-thread|on behalf of|\bGPT-\d[\w.-]*|\bClaude[- ](?:Code|Opus|Sonnet|Fable|Haiku)[\w.-]*"
            r"|\bGemini[- ](?:\d|Neon|Pro)[\w.-]*|\bCodex\b",
            line,
        ),
    ),
    (
        "private network detail",
        lambda line: [
            value
            for value in PRIVATE_ADDRESS.findall(line) + PRIVATE_NAME.findall(line)
            if not PUBLIC_VALUES.match(value)
        ],
    ),
    (
        "link into a folder that is not transferred",
        lambda line: re.findall(
            r"\]\([^)]*(?:planning|thesis-material|preThesis)/[^)]*\)", line
        ),
    ),
)
DATE_RULE = "written date outside a source entry"

# Accepted values, each with its reason: (path, rule name) -> the exact values that may occur.
ACCEPTED = {
    # Working configuration of the lab deployment; tracked in the issue on the lab profile.
    (
        SYSTEM + "coding/server-profiles/lab-hapi.toml",
        "private network detail",
    ): frozenset({"nglegion", "192.168.2.0", "172.20.10.0", "172.20.10.7"}),
}


def git(root: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ["git", *arguments], cwd=root, capture_output=True, check=True
    ).stdout


def is_transferred(path: str) -> bool:
    in_folder = path.startswith(TRANSFERRED_FOLDERS) and not path.startswith(
        EXCLUDED_FOLDERS
    )
    return in_folder or path in TRANSFERRED_FILES


def transfer_set(paths: list[str]) -> list[str]:
    """Select the transferred files from a list of committed paths."""
    return sorted(path for path in paths if is_transferred(path))


def snapshot(root: Path = ROOT, revision: str = "HEAD") -> dict[str, bytes]:
    """Return the transferred files of one commit and the GitLab root page, path to content."""
    listed = git(root, "ls-tree", "-r", "-z", "--name-only", revision).decode("utf-8")
    committed = [path for path in listed.split("\0") if path]
    wanted = set(transfer_set(committed))
    if GITLAB_README_SOURCE in committed:
        wanted.add(GITLAB_README_SOURCE)
    archive = git(root, "archive", "--format=tar", revision, "--", "Development/system")
    files: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        for member in tar:
            if member.name not in wanted:
                continue
            if not member.isfile():
                raise ValueError(f"{member.name}: only regular files are transferred")
            extracted = tar.extractfile(member)
            assert extracted is not None
            files[member.name] = extracted.read()
    missing = wanted - set(files)
    if missing:
        raise ValueError(f"not in the snapshot: {sorted(missing)}")
    return files


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
        for name, offending in RULES:
            accepted = ACCEPTED.get((path, name), frozenset())
            values = [value for value in offending(line) if value not in accepted]
            if values:
                findings.append(
                    f"{path}:{number}: {name}: {', '.join(sorted(set(values)))}"
                )
        # A date inside a URL is part of the address, and "accessed <date>" is the access
        # date of a citation in running text.
        prose = re.sub(r"https?://\S+", " ", line)
        dates = [
            match.group(0)
            for match in DATE.finditer(prose)
            if not re.search(r"\baccessed(?: on)?\s+$", prose[: match.start()])
        ]
        if dates and (not in_source_entry or NARRATION.search(line)):
            findings.append(f"{path}:{number}: {DATE_RULE}: {', '.join(dates)}")
    return findings


# Findings of the supervisor's reviews that must not come back. Each rule names the files it reads.
OWN_TEXT_EXCLUDED = (SYSTEM + "references/", SYSTEM + "coding/third_party/")
LEVEL_FOLDERS = (SYSTEM + "architecture/", SYSTEM + "design/")
SELF_DESCRIPTION = re.compile(
    r"\b[Tt]his (?:page|design|document|section|note|specification)\b|\b[Tt]hese notes\b|\b[Tt]he steps below\b"
)
STATUS_WORD = re.compile(
    r"\bMVP\b|\b[Pp]rovisional\b|\b[Pp]roposed\b|\bfor now\b|\bTODO\b|\bFIXME\b"
)
STATUS_IN_NAME = re.compile(r"(?i)(?:^|[/_.-])mvp(?:[/_.-]|$)")
LAYER_AS_ACTOR = re.compile(
    r"\bL[0-4] (?:reads|owns|takes|decides|retains|compares|calls|keeps|reports|must|may)\b"
)
UNNAMED_PHONE = re.compile(r"(?<!operator's )\bthe phone\b")
REPORTED_BUILD = re.compile(r"\b(?:configuration|build|firmware) (?:enables|sets)\b")
LINK_INTO_CODE = re.compile(r"\]\([^)]*coding/[^)]*\)")
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\([^)]*\)")
REQUIREMENT_ID = re.compile(r"\bREQ-\d+\b")
CONDITION_START = re.compile(r"\s*(?:\}\s*)?(?:else\s+)?(?:if|while)\s*\(")
CALL = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
# Keywords and compile-time macros that may stand in a condition.
NOT_A_CALL = frozenset({"if", "while", "sizeof", "defined", "IS_ENABLED", "ARRAY_SIZE"})


def condition_findings(path: str, text: str) -> list[str]:
    """Return the conditions of a C file that call a function instead of testing a named value."""
    findings = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        if CONDITION_START.match(lines[index]):
            first = index
            statement = lines[index]
            while statement.count("(") > statement.count(")") and index + 1 < len(
                lines
            ):
                index += 1
                statement += lines[index]
            calls = [
                name
                for name in CALL.findall(statement[statement.index("(") :])
                if name not in NOT_A_CALL
            ]
            if calls:
                findings.append(
                    f"{path}:{first + 1}: condition calls a function: {', '.join(sorted(set(calls)))}"
                )
        index += 1
    return findings


def table_findings(path: str, text: str) -> list[str]:
    """Return the Markdown table rows whose number of cells differs from their header."""
    findings = []
    header = None
    in_code_block = False
    for number, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            in_code_block = not in_code_block
        if in_code_block or not line.lstrip().startswith("|"):
            header = None
            continue
        cells = len(re.findall(r"(?<!\\)\|", re.sub(r"`[^`]*`", "", line))) - 1
        if header is None:
            header = cells
        elif cells != header:
            findings.append(
                f"{path}:{number}: table row has {cells} cells, its header has {header}"
            )
    return findings


def review_findings(path: str, text: str) -> list[str]:
    """Return the review findings of one file of the project's own text and code."""
    if path.startswith(OWN_TEXT_EXCLUDED):
        return []
    findings = []
    if STATUS_IN_NAME.search(path):
        findings.append(f"{path}: status word in the file name")
    suffix = posixpath.splitext(path)[1].lower()
    is_page = suffix in (".md", ".puml") or (
        suffix == ".html" and "/coding/" not in path
    )
    is_level_page = is_page and path.startswith(LEVEL_FOLDERS)
    is_code = path.startswith(SYSTEM + "coding/") and suffix != ".md"
    rules = [("status word", STATUS_WORD.findall)]
    if is_page:
        rules.append(("page describes itself", SELF_DESCRIPTION.findall))
    if is_level_page:
        rules.append(("design reports the build", REPORTED_BUILD.findall))
        rules.append(
            ("link from architecture or design into the code", LINK_INTO_CODE.findall)
        )
    # The architecture states what a layer does; design and code name the module.
    if (is_page and path.startswith(SYSTEM + "design/")) or is_code:
        rules.append(("layer named instead of the module", LAYER_AS_ACTOR.findall))
    if is_level_page or is_code:
        rules.append(("phone without its owner", UNNAMED_PHONE.findall))
    if is_level_page and suffix == ".md":
        rules.append(
            (
                "requirement id without a link",
                lambda line: REQUIREMENT_ID.findall(MARKDOWN_LINK.sub(" ", line)),
            )
        )
    for number, line in enumerate(text.splitlines(), start=1):
        for name, offending in rules:
            values = offending(line)
            if values:
                findings.append(
                    f"{path}:{number}: {name}: {', '.join(sorted(set(values)))}"
                )
    if suffix == ".md":
        findings.extend(table_findings(path, text))
    if suffix == ".c":
        findings.extend(condition_findings(path, text))
    return findings


def working_tree(root: Path = ROOT) -> dict[str, bytes]:
    """Return the transferred files and the GitLab root page as they are on disk, path to content."""
    listed = git(root, "ls-files", "-z").decode("utf-8")
    tracked = [path for path in listed.split("\0") if path]
    wanted = set(transfer_set(tracked))
    if GITLAB_README_SOURCE in tracked:
        wanted.add(GITLAB_README_SOURCE)
    return {
        path: (root / path).read_bytes()
        for path in sorted(wanted)
        if (root / path).is_file()
    }


def link_targets(text: str, suffix: str) -> list[tuple[int, str]]:
    """Return the link destinations of a Markdown or HTML file with their line numbers."""
    targets = []
    for number, line in enumerate(text.splitlines(), start=1):
        found = []
        if suffix == ".md":
            # Inline links and images, with balanced parentheses and an optional title.
            found += re.findall(
                r"\]\(\s*<?((?:[^()\s<>]|\((?:[^()\s])*\))+)>?(?:\s+\"[^\"]*\")?\s*\)",
                line,
            )
            # Reference definitions.
            found += re.findall(r"^\s{0,3}\[[^\]]+\]:\s*<?(\S+?)>?(?:\s|$)", line)
        found += re.findall(r"""(?:href|src)\s*=\s*["']([^"']+)["']""", line)
        targets += [(number, target) for target in found]
    return targets


def resolve(folder: str, link_path: str) -> str | None:
    """Return the repository path a relative link points at, or None when it leaves the root."""
    parts: list[str] = []
    for part in posixpath.join(folder, unquote(link_path)).split("/"):
        if part == "..":
            if not parts:
                return None
            parts.pop()
        elif part not in ("", "."):
            parts.append(part)
    return "/".join(parts)


def link_findings(path: str, text: str, selected: set[str]) -> list[str]:
    """Return the relative links of a page whose target is not transferred."""
    suffix = posixpath.splitext(path)[1].lower()
    if suffix not in (".md", ".html"):
        return []
    findings = []
    folder = posixpath.dirname(path)
    for number, raw in link_targets(text, suffix):
        link = urlsplit(raw)
        if link.scheme or link.netloc or not link.path:
            continue
        target = resolve(folder, link.path)
        if target is None:
            findings.append(f"{path}:{number}: link leaves the repository: {raw}")
            continue
        is_folder = any(candidate.startswith(target + "/") for candidate in selected)
        if target not in selected and not is_folder:
            findings.append(
                f"{path}:{number}: link to a file that is not transferred: {raw}"
            )
    return findings


def gitlab_readme(text: str) -> str:
    """Rewrite the links of the GitLab root page from its place here to the repository root."""
    folder = posixpath.dirname(GITLAB_README_SOURCE)

    def rewrite(match: re.Match[str]) -> str:
        link = urlsplit(match.group(1))
        if link.scheme or link.netloc or not link.path:
            return match.group(0)
        target = resolve(folder, link.path)
        if target is None:
            return match.group(0)
        fragment = "#" + link.fragment if link.fragment else ""
        return f"]({target}{fragment})"

    return re.sub(r"\]\(([^)\s]+)\)", rewrite, text)


def check(files: dict[str, bytes]) -> list[str]:
    """Return every finding of a snapshot."""
    findings = []
    selected = {path for path in files if path != GITLAB_README_SOURCE}
    if GITLAB_README_SOURCE not in files:
        findings.append(
            f"{GITLAB_README_SOURCE}: the root page of the GitLab repository is missing"
        )
    for path in sorted(files):
        if posixpath.splitext(path)[1].lower() in BINARY_SUFFIXES:
            continue
        try:
            text = files[path].decode("utf-8")
        except UnicodeDecodeError:
            findings.append(f"{path}: not UTF-8 text and not listed as a binary file")
            continue
        if "\0" in text:
            findings.append(f"{path}: not UTF-8 text and not listed as a binary file")
            continue
        findings.extend(content_findings(path, text))
        findings.extend(review_findings(path, text))
        if path == GITLAB_README_SOURCE:
            # The root page is checked as it is exported: rewritten, at the repository root.
            findings.extend(
                link_findings(GITLAB_README_TARGET, gitlab_readme(text), selected)
            )
        else:
            findings.extend(link_findings(path, text, selected))
    return findings


def export(files: dict[str, bytes], destination: Path) -> int:
    """Write a checked snapshot into a new, empty directory and return the number of files."""
    destination.mkdir(parents=True, exist_ok=False)
    base = destination.resolve()
    written = 0
    for path, content in sorted(files.items()):
        if path == GITLAB_README_SOURCE:
            path = GITLAB_README_TARGET
            content = gitlab_readme(content.decode("utf-8")).encode("utf-8")
        target = (base / path).resolve()
        if base not in target.parents:
            raise ValueError(f"{path}: outside the export directory")
        target.parent.mkdir(parents=True, exist_ok=True)
        # "x" refuses to write over anything that already exists.
        with open(target, "xb") as handle:
            handle.write(content)
        written += 1
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--revision", default="HEAD", help="commit to read (default: HEAD)"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="report what must not reach GitLab")
    commands.add_parser("list", help="print the transferred files")
    export_parser = commands.add_parser(
        "export", help="write the transferred files into a new directory"
    )
    export_parser.add_argument(
        "destination", type=Path, help="directory that does not exist yet"
    )
    arguments = parser.parse_args()

    files = snapshot(ROOT, arguments.revision)
    if arguments.command == "list":
        print("\n".join(sorted(path for path in files if path != GITLAB_README_SOURCE)))
        return 0
    findings = check(files)
    if findings:
        print("\n".join(findings))
        print(
            f"{len(findings)} finding(s): the transfer set is not clean.",
            file=sys.stderr,
        )
        return 1
    if arguments.command == "check":
        print(f"Transfer set of {arguments.revision} is clean: {len(files)} file(s).")
        return 0
    # A dangling link at the destination does not exist any more once it is resolved.
    exists_as_given = os.path.lexists(arguments.destination)
    destination = arguments.destination.resolve()
    if exists_as_given or destination.exists():
        print(
            f"{destination} exists already; export needs a new directory.",
            file=sys.stderr,
        )
        return 2
    if ROOT.resolve() == destination or ROOT.resolve() in destination.parents:
        print(
            f"{destination} is inside this repository; choose a directory outside it.",
            file=sys.stderr,
        )
        return 2
    written = export(files, destination)
    print(f"Wrote {written} file(s) of {arguments.revision} to {destination}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
