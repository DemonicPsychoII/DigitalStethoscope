"""Check maintained documentation offline against the sources it repeats."""

import base64
import json
import re
import subprocess
import sys
import zlib
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[4]
AREAS = (
    "README.md",
    "AGENTS.md",
    "Development/system/",
    "preThesis/",
    "docs/",
    "thesis-material/",
)
SYSTEM = "Development/system/"
WORKFLOW = ".github/workflows/quality-gates.yml"
CI_DOCS = (
    SYSTEM + "testing/CI-QUALITY-GATES.md",
    SYSTEM + "testing/ci/OPERATIONS.md",
)
# Dated decision records keep the wording of their day.
HISTORICAL = re.compile(r"planning/mvp-decisions-\d{4}-\d{2}-\d{2}\.md$")
# PlantUML stores the diagram text in a deflated base64 variant with this alphabet.
PLANTUML_ALPHABET = str.maketrans(
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_",
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",
)


def anchors(text: str) -> set[str]:
    found = set(re.findall(r'(?:id|name)=["\']([^"\']+)', text))
    counts = {}
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", text, re.MULTILINE):
        slug = re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")
        count = counts.get(slug, 0)
        found.add(slug if not count else f"{slug}-{count}")
        counts[slug] = count + 1
    return found


def line_anchor(fragment: str, target: Path) -> bool:
    """GitHub line anchors (#L12 or #L12-L20) are valid when the lines exist."""
    match = re.fullmatch(r"L(\d+)(?:-L(\d+))?", fragment)
    if not match:
        return False
    last = int(match.group(2) or match.group(1))
    return last <= len(target.read_text(encoding="utf-8").splitlines())


def links(source: Path, root: Path = ROOT) -> list[str]:
    text = re.sub(r"```.*?```", "", source.read_text(encoding="utf-8"), flags=re.DOTALL)
    errors = []
    targets = re.findall(r"!?\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)", text)
    for raw in targets:
        url = urlsplit(raw.strip("<>"))
        if url.scheme or url.netloc:
            continue
        path = unquote(url.path)
        target = (
            (root / path.lstrip("/") if path.startswith("/") else source.parent / path)
            if path
            else source
        )
        if not target.exists():
            errors.append(f"{source.relative_to(root)}: missing local target {raw}")
        elif (
            url.fragment
            and target.suffix == ".md"
            and not line_anchor(unquote(url.fragment), target)
            and unquote(url.fragment) not in anchors(target.read_text(encoding="utf-8"))
        ):
            errors.append(f"{source.relative_to(root)}: missing anchor {raw}")
    return errors


def diagram_body(text: str) -> str:
    lines = text.replace("\r\n", "\n").strip().splitlines()
    return "\n".join(
        line for line in lines if not line.startswith(("@startuml", "@enduml"))
    ).strip()


def svg_source(svg: Path) -> str | None:
    match = re.search(r"plantuml-src ([0-9A-Za-z_-]+)", svg.read_text(encoding="utf-8"))
    if not match:
        return None
    encoded = match.group(1).translate(PLANTUML_ALPHABET)
    data = base64.b64decode(encoded + "=" * (-len(encoded) % 4))
    return zlib.decompress(data, -15).decode("utf-8")


def renders(paths: list[str], root: Path = ROOT) -> list[str]:
    """Each committed SVG must embed the current text of its PlantUML source."""
    errors = []
    pumls = {p for p in paths if p.endswith(".puml")}
    svgs = [p for p in paths if "/rendered/" in p and p.endswith(".svg")]
    rendered_dirs = {str(Path(p).parent.parent.as_posix()) for p in svgs}
    for svg in svgs:
        stem = Path(svg).stem.replace("_", "-")
        puml = f"{Path(svg).parent.parent.as_posix()}/{stem}.puml"
        if puml not in pumls:
            errors.append(f"{svg}: no PlantUML source {puml}")
            continue
        source = svg_source(root / svg)
        if source is None:
            errors.append(f"{svg}: no embedded PlantUML source")
        elif diagram_body(source) != diagram_body(
            (root / puml).read_text(encoding="utf-8")
        ):
            errors.append(f"{svg}: stale render of {puml}; rerender it")
    for puml in pumls:
        directory = Path(puml).parent.as_posix()
        svg = f"{directory}/rendered/{Path(puml).stem.replace('-', '_')}.svg"
        if directory in rendered_dirs and svg not in svgs:
            errors.append(f"{puml}: missing render {svg}")
    return errors


def listed(paths: list[str], root: Path = ROOT) -> list[str]:
    """Hand-written indexes must name every file they index."""
    errors = []
    indexes = (
        (SYSTEM + "testing/ci/", ".py", (SYSTEM + "testing/ci/README.md",)),
        (
            SYSTEM + "architecture/",
            ".puml",
            (SYSTEM + "architecture/README.md", SYSTEM + "architecture/VIEW-NOTES.md"),
        ),
    )
    for directory, suffix, docs in indexes:
        text = "".join((root / doc).read_text(encoding="utf-8") for doc in docs)
        for path in paths:
            name = Path(path).name
            if (
                Path(path).parent.as_posix() + "/" == directory
                and name.endswith(suffix)
                and not name.startswith("test_")
                and name not in text
            ):
                errors.append(f"{docs[0]}: {name} is not listed")
    return errors


def facts(paths: list[str], root: Path = ROOT) -> list[str]:
    """Values repeated in prose must match the files that define them."""
    errors = []
    workflow = (root / WORKFLOW).read_text(encoding="utf-8")
    tools = json.loads(
        (root / SYSTEM / "testing/ci/validation_tools.json").read_text(encoding="utf-8")
    )
    python = re.search(r"python-version: '([\d.]+)'", workflow).group(1)
    retention = set(re.findall(r"retention-days: (\d+)", workflow))
    requirements = (root / SYSTEM / "requirements/system-requirements.md").read_text(
        encoding="utf-8"
    )
    last_requirement = max(re.findall(r"^\| REQ-(\d+)", requirements, re.MULTILINE))
    docs = [
        p
        for p in paths
        if p.endswith(".md") and p.startswith(AREAS) and not HISTORICAL.search(p)
    ]
    for path in docs:
        text = (root / path).read_text(encoding="utf-8")
        for version in re.findall(r"\bPython (3\.\d+\.\d+)", text):
            if version != python:
                errors.append(f"{path}: Python {version}, workflow pins {python}")
        for tool, version in re.findall(
            r"\b(actionlint|ShellCheck) (\d+\.\d+\.\d+)", text
        ):
            pinned = tools[tool.lower()]["version"]
            if version != pinned:
                errors.append(
                    f"{path}: {tool} {version}, validation_tools.json pins {pinned}"
                )
        for last in re.findall(r"REQ-01\s*(?:…|–|-|to)\s*REQ-(\d+)", text):
            if last != last_requirement:
                errors.append(
                    f"{path}: REQ-01…REQ-{last}, last requirement is REQ-{last_requirement}"
                )
    for path in CI_DOCS:
        text = (root / path).read_text(encoding="utf-8")
        for days in re.findall(r"\b(\d+)[- ]days?\b", text):
            if days not in retention:
                errors.append(f"{path}: {days} days is not a workflow retention period")
        # Every test suite CI runs must appear in the local check commands.
        for suite in re.findall(
            r"(?:pytest|unittest discover -s)\s+(?:-\S+\s+)*([\w./-]+/[\w./-]+)",
            workflow,
        ):
            if suite not in text:
                errors.append(f"{path}: local checks omit CI suite {suite}")
    gates = (root / SYSTEM / "testing/CI-QUALITY-GATES.md").read_text(encoding="utf-8")
    required = re.search(r"Required contexts remain:\n\n((?:- .*\n)+)", gates)
    github = "".join(
        p.read_text(encoding="utf-8")
        for p in (root / ".github").rglob("*")
        if p.suffix in (".yml", ".py")
    )
    for name in re.findall(
        r"^- `([^`]+)`", required.group(1) if required else "", re.MULTILINE
    ):
        if name not in github:
            errors.append(
                f"CI-QUALITY-GATES.md: required context {name} not found in .github/"
            )
    return errors


def thesis(root: Path = ROOT) -> list[str]:
    """The thesis kit is generated; committed output must equal a fresh run."""
    area = "thesis-material"
    before = subprocess.check_output(["git", "diff", "--", area], cwd=root)
    run = subprocess.run(
        [sys.executable, "thesis-material/_build/build.py"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if run.returncode:
        tail = (run.stderr or run.stdout).strip().splitlines()[-1:]
        return [f"thesis-material/_build/build.py failed: {' '.join(tail)}"]
    after = subprocess.check_output(["git", "diff", "--", area], cwd=root)
    if after != before:
        return [
            "thesis-material: generated files were stale; commit the regenerated output"
        ]
    return []


def main() -> None:
    paths = (
        subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
        .decode()
        .split("\0")
    )
    errors = []
    for path in paths:
        if not path.startswith(AREAS):
            continue
        source = ROOT / path
        if source.suffix == ".md":
            errors.extend(links(source))
        elif source.suffix == ".puml":
            text = source.read_text(encoding="utf-8").strip()
            if not text.startswith("@startuml") or not text.endswith("@enduml"):
                errors.append(f"{path}: incomplete PlantUML source")
    errors.extend(renders(paths))
    errors.extend(listed(paths))
    errors.extend(facts(paths))
    errors.extend(thesis())
    if errors:
        raise SystemExit("\n".join(errors))
    print("Documentation links, renders, indexes, repeated facts and thesis kit: PASS")


if __name__ == "__main__":
    main()
