"""Check maintained Markdown local links and diagram source envelopes offline."""

import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[4]
AREAS = ("README.md", "AGENTS.md", "Development/system/", "preThesis/")


def anchors(text: str) -> set[str]:
    found = set(re.findall(r'(?:id|name)=["\']([^"\']+)', text))
    counts = {}
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", text, re.MULTILINE):
        slug = re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")
        count = counts.get(slug, 0)
        found.add(slug if not count else f"{slug}-{count}")
        counts[slug] = count + 1
    return found


def links(source: Path, root: Path = ROOT) -> list[str]:
    text = re.sub(r"```.*?```", "", source.read_text(), flags=re.DOTALL)
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
            and unquote(url.fragment) not in anchors(target.read_text())
        ):
            errors.append(f"{source.relative_to(root)}: missing anchor {raw}")
    return errors


def verification_coverage(root: Path = ROOT) -> list[str]:
    """Require a test/procedure reference or an explicit gap for each VT ID."""
    catalogue = root / "Development/system/testing/specification-verification.md"
    text = catalogue.read_text(encoding="utf-8")
    cases = set(re.findall(r"\bVT-\d{2}\b", text))
    gaps = set(re.findall(r"^- (VT-\d{2}): Not yet covered .*\S", text, re.MULTILINE))
    retired = set(re.findall(r"^- (VT-\d{2}): Retired — .*\S", text, re.MULTILINE))
    referenced = set()
    coding = root / "Development/system/coding"
    testing = root / "Development/system/testing"
    sources = list(coding.glob("**/tests/**/*")) + list(testing.rglob("*"))
    for source in sources:
        if not source.is_file() or source.suffix not in {
            ".py",
            ".c",
            ".h",
            ".md",
            ".sh",
        }:
            continue
        if source == catalogue or (
            source.is_relative_to(testing)
            and source.relative_to(testing).parts[0] in {"ci", "evidence"}
        ):
            continue
        referenced.update(
            re.findall(
                r"\bVT-\d{2}\b", source.name + "\n" + source.read_text(encoding="utf-8")
            )
        )
    errors = [
        f"{catalogue.relative_to(root)}: {case} has no test/procedure reference; "
        "add coverage or a '- VT-xx: Not yet covered ...' entry"
        for case in sorted(cases - referenced - gaps - retired)
    ]
    errors.extend(
        f"{catalogue.relative_to(root)}: {case} has a test/procedure reference; "
        "remove its stale 'Not yet covered' entry"
        for case in sorted(gaps & referenced)
    )
    return errors


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
            text = source.read_text().strip()
            if not text.startswith("@startuml") or not text.endswith("@enduml"):
                errors.append(f"{path}: incomplete PlantUML source")
    errors.extend(verification_coverage())
    if errors:
        raise SystemExit("\n".join(errors))
    print("Maintained documentation links, diagram envelopes and VT references: PASS")


if __name__ == "__main__":
    main()
