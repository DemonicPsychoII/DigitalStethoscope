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
    if errors:
        raise SystemExit("\n".join(errors))
    print("Maintained local documentation links and diagram envelopes: PASS")


if __name__ == "__main__":
    main()
