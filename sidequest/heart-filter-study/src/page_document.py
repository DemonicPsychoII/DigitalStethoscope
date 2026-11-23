"""Parse a read.md file: front matter and block directives around GitHub-flavoured Markdown."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

CONTAINER_DIRECTIVES = {"summary", "callout", "term", "sources", "raw-html"}
RAW_CONTAINER_DIRECTIVES = {"sources", "raw-html"}
LEAF_DIRECTIVES = {"figure", "audio-compare", "table-csv", "glossary"}

DIRECTIVE_LINE_PATTERN = re.compile(r"^(?P<indent>\s*)::(?P<name>[A-Za-z][\w-]*)(?P<rest>.*)$")
ATTRIBUTE_PATTERN = re.compile(r"""([A-Za-z_][\w-]*)\s*=\s*(?:"((?:[^"\\]|\\.)*)"|'((?:[^'\\]|\\.)*)'|([^\s"'}]+))""")
FENCE_PATTERN = re.compile(r"^\s{0,3}(`{3,}|~{3,})")


@dataclass
class MarkdownNode:
    text: str


@dataclass
class DirectiveNode:
    name: str
    attributes: dict[str, str]
    line_number: int
    indent: str = ""
    children: list = field(default_factory=list)
    raw_lines: list[str] = field(default_factory=list)
    attribute_error: str | None = None


@dataclass
class Document:
    front_matter: dict[str, str]
    nodes: list
    warnings: list[str]


def parse_front_matter(lines: list[str]) -> tuple[dict[str, str], int]:
    if not lines or lines[0].strip() != "---":
        return {}, 0
    front_matter: dict[str, str] = {}
    for index in range(1, len(lines)):
        line = lines[index]
        if line.strip() in ("---", "..."):
            return front_matter, index + 1
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition(":")
        if not separator:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        front_matter[key.strip().lower()] = value
    return {}, 0


def split_attribute_block(rest: str) -> tuple[str | None, str, str | None]:
    """Return (attribute text, remaining text, error) for the text after '::name'."""
    stripped = rest.lstrip()
    if not stripped.startswith("{"):
        return None, rest.strip(), None
    quote_character = None
    for position, character in enumerate(stripped):
        if quote_character:
            if character == "\\":
                continue
            if character == quote_character and stripped[position - 1] != "\\":
                quote_character = None
        elif character in "\"'":
            quote_character = character
        elif character == "}":
            return stripped[1:position], stripped[position + 1:].strip(), None
    return stripped[1:], "", "attribute block is not closed with '}'"


def parse_attributes(attribute_text: str | None) -> dict[str, str]:
    if not attribute_text:
        return {}
    attributes = {}
    for match in ATTRIBUTE_PATTERN.finditer(attribute_text):
        value = match.group(2) if match.group(2) is not None else match.group(3) if match.group(3) is not None else match.group(4)
        attributes[match.group(1).lower()] = re.sub(r"\\(.)", r"\1", value)
    return attributes


def parse_document(source: str) -> Document:
    lines = source.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    front_matter, body_start = parse_front_matter(lines)
    warnings: list[str] = []
    nodes, _ = parse_nodes(lines, body_start, closing_expected=None, warnings=warnings)
    return Document(front_matter, nodes, warnings)


def parse_nodes(lines: list[str], start: int, closing_expected: DirectiveNode | None, warnings: list[str]):
    nodes: list = []
    markdown_lines: list[str] = []
    fence_marker: str | None = None
    index = start

    def flush_markdown():
        if markdown_lines:
            nodes.append(MarkdownNode("\n".join(markdown_lines)))
            markdown_lines.clear()

    while index < len(lines):
        line = lines[index]
        fence_match = FENCE_PATTERN.match(line)
        if fence_marker:
            markdown_lines.append(line)
            if fence_match and fence_match.group(1)[0] == fence_marker[0] and len(fence_match.group(1)) >= len(fence_marker):
                fence_marker = None
            index += 1
            continue
        if fence_match:
            fence_marker = fence_match.group(1)
            markdown_lines.append(line)
            index += 1
            continue

        directive_match = DIRECTIVE_LINE_PATTERN.match(line)
        if not directive_match:
            markdown_lines.append(line)
            index += 1
            continue

        name = directive_match.group("name").lower()
        line_number = index + 1
        if name == "end":
            if closing_expected is not None:
                flush_markdown()
                return nodes, index + 1
            warnings.append(f"line {line_number}: '::end' without an opening directive; ignored")
            index += 1
            continue

        attribute_text, remaining_text, attribute_error = split_attribute_block(directive_match.group("rest"))
        directive = DirectiveNode(name, parse_attributes(attribute_text), line_number, directive_match.group("indent"))
        directive.attribute_error = attribute_error
        flush_markdown()
        index += 1

        if name in CONTAINER_DIRECTIVES:
            single_line_body = None
            if remaining_text:
                if remaining_text.endswith("::end"):
                    single_line_body = remaining_text[: -len("::end")].strip()
                else:
                    lines.insert(index, remaining_text)
            if single_line_body is not None:
                if name in RAW_CONTAINER_DIRECTIVES:
                    directive.raw_lines = [single_line_body]
                else:
                    directive.children = [MarkdownNode(single_line_body)]
            elif name in RAW_CONTAINER_DIRECTIVES:
                raw_lines = []
                while index < len(lines) and lines[index].strip() != "::end":
                    raw_lines.append(lines[index])
                    index += 1
                if index >= len(lines):
                    warnings.append(f"line {line_number}: '::{name}' is not closed with '::end'; it runs to the end of the file")
                index += 1
                directive.raw_lines = raw_lines
            else:
                children, index = parse_nodes(lines, index, directive, warnings)
                directive.children = children
        elif remaining_text:
            markdown_lines_after = remaining_text
            lines.insert(index, markdown_lines_after)
        nodes.append(directive)

    flush_markdown()
    if closing_expected is not None:
        warnings.append(
            f"line {closing_expected.line_number}: '::{closing_expected.name}' is not closed with '::end'; it runs to the end of the file"
        )
    return nodes, index


def walk_directives(nodes):
    for node in nodes:
        if isinstance(node, DirectiveNode):
            yield node
            yield from walk_directives(node.children)
