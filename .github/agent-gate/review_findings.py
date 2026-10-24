"""Recognise explicitly nonblocking findings from authenticated CodeRabbit reviews."""

import re


FINDING_HEADER = re.compile(
    r"^_[^_\n]+_\s*\|\s*_[^\w\n]*(Critical|Major|Minor|Trivial)_\s*$",
    re.MULTILINE,
)


def nonblocking_finding(body: str) -> bool:
    """Only the bot's leading classification counts, never quoted examples or replies."""
    first_line = body.strip().splitlines()[:1]
    header = FINDING_HEADER.fullmatch(first_line[0]) if first_line else None
    return bool(header and header[1] in {"Minor", "Trivial"}
                and all(severity in {"Minor", "Trivial"} for severity in FINDING_HEADER.findall(body)))


def nonblocking_review(body: str, findings: list[str]) -> bool:
    """Account for every inline finding and supported summary section, failing closed.

    Review details and AI prompts repeat metadata/findings; other summary sections
    must explicitly classify their findings. A changed bot format needs review.
    """
    text = re.sub(r"```.*?```|~~~.*?~~~|<!--.*?-->", "", body, flags=re.DOTALL).strip()
    count = re.match(r"\*\*Actionable comments posted: (\d+)\*\*", text)
    if count is None or int(count[1]) != len(findings) or not all(map(nonblocking_finding, findings)):
        return False
    remaining = text[count.end():].strip()
    additional_findings = 0
    while remaining:
        if not remaining.startswith("<details>"):
            return False
        depth = 0
        end = None
        for tag in re.finditer(r"</?details>", remaining):
            depth += -1 if tag[0].startswith("</") else 1
            if depth == 0:
                end = tag.end()
                break
        if end is None:
            return False
        block, remaining = remaining[:end], remaining[end:].strip()
        summary = re.match(r"<details>\s*<summary>([^<]+)</summary>", block)
        if summary is None:
            return False
        title = summary[1].strip()
        content = block[summary.end():-len("</details>")]
        headers = FINDING_HEADER.findall(content)
        if any(severity not in {"Minor", "Trivial"} for severity in headers):
            return False
        if title in {"📜 Review details", "🤖 Prompt for all review comments with AI agents"}:
            continue
        section = re.fullmatch(r"(?:🧹 Nitpick|⚠️ Outside diff range|♻️ Duplicate) comments \((\d+)\)", title)
        if section is None:
            return False
        section_count = int(section[1])
        summary_classifies_nitpicks = title.startswith("🧹 Nitpick comments") and not headers
        if section_count and not summary_classifies_nitpicks and len(headers) != section_count:
            return False
        additional_findings += section_count
    return bool(findings or additional_findings)
