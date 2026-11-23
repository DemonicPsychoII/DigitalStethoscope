"""Render a parsed read.md document into the article HTML."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import shutil
import unicodedata
from pathlib import Path

from markdown_it import MarkdownIt

from page_document import DirectiveNode, MarkdownNode, walk_directives

VARIANT_LABELS = {
    "device": "As the device plays it today",
    "madeup": "With a fixed boost per position",
    "matched": "Same loudness for all",
}
VARIANT_EXPLANATIONS = {
    "device": "Exact output of the simulated device at full volume: filter, then volume, then the limit of the output converter.",
    "madeup": "The same, with one fixed boost per filter that never overloads the output on any of the five recordings.",
    "matched": "All filters brought to the same measured loudness, to compare character rather than loudness.",
}
CALLOUT_LABELS = {
    "finding": "Finding",
    "limitation": "Limitation",
    "decision": "Project decision",
    "open": "Open point",
}
DOWNLOAD_PLACEHOLDER = "<!--download-all-samples-->"
SOURCE_REFERENCE_PATTERN = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")
PROTECTED_HTML_PATTERN = re.compile(r"(<pre[\s\S]*?</pre>|<code[\s\S]*?</code>|<a\s[\s\S]*?</a>|<[^>]+>)")


def escape(text) -> str:
    return html.escape(str(text), quote=True)


def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-") or "section"


def heading_identifier_rule(state):
    used = state.env.setdefault("used_identifiers", set())
    tokens = state.tokens
    for index, token in enumerate(tokens):
        if token.type != "heading_open" or index + 1 >= len(tokens):
            continue
        title = "".join(child.content for child in (tokens[index + 1].children or []) if child.type in ("text", "code_inline"))
        base = slugify(title or tokens[index + 1].content)
        identifier = base
        counter = 2
        while identifier in used:
            identifier = f"{base}-{counter}"
            counter += 1
        used.add(identifier)
        token.attrSet("id", identifier)
        if token.tag == "h2":
            state.env.setdefault("table_of_contents", []).append((identifier, title or tokens[index + 1].content))


def create_markdown_parser() -> MarkdownIt:
    parser = MarkdownIt("commonmark", {"html": True, "typographer": False}).enable(["table", "strikethrough"])
    parser.core.ruler.push("heading_identifiers", heading_identifier_rule)
    return parser


class PageRenderer:
    def __init__(self, document, study_root: Path, output_folder: Path, sample_library, warnings: list[str], log):
        self.document = document
        self.study_root = study_root
        self.output_folder = output_folder
        self.sample_library = sample_library
        self.warnings = warnings
        self.log = log
        self.parser = create_markdown_parser()
        self.environment: dict = {"used_identifiers": {"top", "contents", "glossary-list"}}
        self.figure_targets: dict[str, Path] = {}
        self.audio_block_count = 0
        self.source_numbers: set[int] = set()
        self.terms: list[dict] = []
        self.player_counter = 0
        self.collect_sources_and_terms()

    def warn(self, node: DirectiveNode | None, message: str) -> str:
        location = f"line {node.line_number}: " if node else ""
        self.warnings.append(location + message)
        return f'<div class="build-warning" role="note"><strong>Build warning</strong> {escape(location + message)}</div>'

    def collect_sources_and_terms(self):
        for directive in walk_directives(self.document.nodes):
            if directive.name == "sources":
                for number, _ in parse_source_lines(directive.raw_lines):
                    self.source_numbers.add(number)
            elif directive.name == "term":
                name = directive.attributes.get("name", "").strip()
                if name:
                    directive.term_identifier = self.unique_identifier("term-" + slugify(name))
                    self.terms.append({"name": name, "identifier": directive.term_identifier, "directive": directive})

    def unique_identifier(self, base: str) -> str:
        used = self.environment["used_identifiers"]
        identifier = base
        counter = 2
        while identifier in used:
            identifier = f"{base}-{counter}"
            counter += 1
        used.add(identifier)
        return identifier

    def link_source_references(self, rendered: str) -> str:
        def replace_reference(match):
            numbers = [int(part) for part in re.split(r"\s*,\s*", match.group(1))]
            if not all(number in self.source_numbers for number in numbers):
                return match.group(0)
            links = ", ".join(f'<a class="source-reference" href="#source-{number}">{number}</a>' for number in numbers)
            return f'<span class="source-references">[{links}]</span>'

        parts = PROTECTED_HTML_PATTERN.split(rendered)
        return "".join(part if index % 2 else SOURCE_REFERENCE_PATTERN.sub(replace_reference, part) for index, part in enumerate(parts))

    def render_markdown(self, text: str) -> str:
        rendered = self.parser.render(text, self.environment)
        rendered = rendered.replace("<table>", '<div class="table-scroll"><table>').replace("</table>", "</table></div>")
        return self.link_source_references(rendered)

    def render_nodes(self, nodes) -> str:
        placeholders: dict[str, str] = {}
        markdown_parts: list[str] = []
        for node in nodes:
            if isinstance(node, MarkdownNode):
                markdown_parts.append(node.text)
            else:
                token = f"DIRECTIVEPLACEHOLDER{len(placeholders):04d}X"
                placeholders[token] = self.render_directive(node)
                markdown_parts.append(f"\n\n{node.indent}{token}\n\n")
        rendered = self.render_markdown("\n".join(markdown_parts))
        for token, directive_html in placeholders.items():
            if f"<p>{token}</p>" in rendered:
                rendered = rendered.replace(f"<p>{token}</p>", directive_html)
            else:
                rendered = rendered.replace(token, directive_html)
        return rendered

    def render_directive(self, node: DirectiveNode) -> str:
        if node.attribute_error:
            self.warn(node, f"'::{node.name}': {node.attribute_error}")
        handler = {
            "figure": self.render_figure,
            "summary": self.render_summary,
            "callout": self.render_callout,
            "term": self.render_term,
            "glossary": self.render_glossary,
            "audio-compare": self.render_audio_compare,
            "sources": self.render_sources,
            "table-csv": self.render_table_csv,
            "raw-html": lambda directive: "\n".join(directive.raw_lines),
        }.get(node.name)
        if handler is None:
            return self.warn(node, f"unknown directive '::{node.name}' (see page/README.md for the supported directives)")
        return handler(node)

    def render_summary(self, node: DirectiveNode) -> str:
        title = node.attributes.get("title", "Result in brief")
        return (f'<section class="summary-card" aria-label="{escape(title)}"><p class="card-label">{escape(title)}</p>'
                f"{self.render_nodes(node.children)}</section>")

    def render_callout(self, node: DirectiveNode) -> str:
        kind = node.attributes.get("kind", "finding").strip().lower()
        if kind not in CALLOUT_LABELS:
            self.warn(node, f"callout kind '{kind}' is unknown; use one of {', '.join(CALLOUT_LABELS)}")
            kind = "open"
        label = node.attributes.get("label") or CALLOUT_LABELS[kind]
        return (f'<aside class="callout callout-{kind}"><p class="callout-label">{escape(label)}</p>'
                f"{self.render_nodes(node.children)}</aside>")

    def render_term(self, node: DirectiveNode) -> str:
        name = node.attributes.get("name", "").strip()
        if not name:
            return self.warn(node, "'::term' needs a name attribute, for example ::term{name=\"band-pass filter\"}")
        body = self.render_nodes(node.children)
        node.rendered_body = body
        return (f'<aside class="term-box" id="{node.term_identifier}"><p class="term-label">In plain words</p>'
                f'<p class="term-name"><dfn>{escape(name)}</dfn></p>{body}</aside>')

    def render_glossary(self, node: DirectiveNode) -> str:
        if not self.terms:
            return self.warn(node, "'::glossary' found but there is no '::term' in the document")
        entries = []
        for term in sorted(self.terms, key=lambda item: item["name"].casefold()):
            directive = term["directive"]
            body = getattr(directive, "rendered_body", None)
            if body is None:
                body = self.render_nodes(directive.children)
            entries.append(f'<div class="glossary-entry"><dt><a href="#{term["identifier"]}">{escape(term["name"])}</a></dt>'
                           f"<dd>{body}</dd></div>")
        return f'<dl class="glossary" id="glossary-list">{"".join(entries)}</dl>'

    def render_sources(self, node: DirectiveNode) -> str:
        items = []
        for number, text in parse_source_lines(node.raw_lines):
            items.append(f'<li id="source-{number}"><span class="source-number">[{number}]</span> '
                         f'<span class="source-text">{self.parser.renderInline(text)}</span></li>')
        if not items:
            return self.warn(node, "'::sources' contains no line of the form '[1] text'")
        return f'<ol class="source-list">{"".join(items)}</ol>'

    def render_figure(self, node: DirectiveNode) -> str:
        source_text = node.attributes.get("src", "").strip()
        alt_text = node.attributes.get("alt", "")
        caption = node.attributes.get("caption", "")
        width_class = "figure-wide" if node.attributes.get("width", "wide").strip().lower() == "wide" else "figure-text"
        caption_html = f"<figcaption>{self.parser.renderInline(caption)}</figcaption>" if caption else ""
        source_path = (self.study_root / source_text) if source_text else None
        if not source_path or not source_path.is_file():
            self.warn(node, f"figure not found: {source_text or '(no src attribute)'}")
            return (f'<figure class="{width_class} figure-missing"><div class="figure-placeholder" role="img" aria-label="Missing figure">'
                    f"<strong>Figure missing</strong><code>{escape(source_text or 'no src given')}</code></div>{caption_html}</figure>")
        relative_target = self.copy_figure(source_path)
        size_attributes = ""
        try:
            from PIL import Image

            with Image.open(source_path) as image:
                size_attributes = f' width="{image.width}" height="{image.height}"'
        except Exception:
            pass
        if not alt_text:
            self.warn(node, f"figure {source_text} has no alt text")
        return (f'<figure class="{width_class}"><button type="button" class="figure-open" data-full="{escape(relative_target)}" '
                f'aria-label="Show figure full size: {escape(alt_text)}">'
                f'<img src="{escape(relative_target)}" alt="{escape(alt_text)}"{size_attributes} loading="lazy" decoding="async"></button>'
                f"{caption_html}</figure>")

    def copy_figure(self, source_path: Path) -> str:
        resolved = source_path.resolve()
        name = re.sub(r"[^A-Za-z0-9._-]+", "-", resolved.name)
        existing = self.figure_targets.get(name)
        if existing is not None and existing != resolved:
            name = hashlib.sha1(str(resolved).encode()).hexdigest()[:8] + "-" + name
        self.figure_targets[name] = resolved
        target = self.output_folder / "assets" / "figures" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(resolved, target)
        return f"assets/figures/{name}"

    def render_table_csv(self, node: DirectiveNode) -> str:
        attributes = node.attributes
        source_text = attributes.get("src", "").strip()
        source_path = self.study_root / source_text if source_text else None
        caption = attributes.get("caption", "")
        if not source_path or not source_path.is_file():
            return self.warn(node, f"table CSV not found: {source_text or '(no src attribute)'}")
        with source_path.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        available_columns = list(rows[0].keys()) if rows else []
        columns = split_list(attributes.get("columns")) or available_columns
        missing_columns = [column for column in columns if column not in available_columns]
        if missing_columns:
            self.warn(node, f"table CSV {source_text}: column(s) not found: {', '.join(missing_columns)}")
        headers = split_list(attributes.get("headers"))
        if headers and len(headers) != len(columns):
            self.warn(node, f"table CSV {source_text}: {len(headers)} headers for {len(columns)} columns")
        headers = [headers[index] if index < len(headers) else column for index, column in enumerate(columns)]
        row_limit = attributes.get("rows", "").strip()
        if row_limit:
            try:
                rows = rows[: int(row_limit)]
            except ValueError:
                self.warn(node, f"table CSV {source_text}: rows=\"{row_limit}\" is not a number")
        precision = attributes.get("precision", "").strip()
        precision_value = int(precision) if precision.isdigit() else None
        highlights = []
        for condition in (attributes.get("highlight", "").split(";") if attributes.get("highlight") else []):
            column, separator, value = condition.partition("=")
            if separator:
                highlights.append((column.strip(), value.strip()))
        numeric_columns = {column for column in columns
                           if rows and all(parse_number(row.get(column)) is not None or not (row.get(column) or "").strip() for row in rows)
                           and any(parse_number(row.get(column)) is not None for row in rows)}
        header_html = "".join(f'<th scope="col"{" class=\"number\"" if column in numeric_columns else ""}>{escape(header)}</th>'
                              for column, header in zip(columns, headers))
        body_rows = []
        for row in rows:
            highlighted = any((row.get(column) or "").strip() == value for column, value in highlights)
            cells = []
            for column in columns:
                raw_value = row.get(column)
                if raw_value is None or not raw_value.strip():
                    cells.append('<td class="empty">–</td>')
                elif column in numeric_columns:
                    cells.append(f'<td class="number">{escape(format_number(raw_value, precision_value))}</td>')
                else:
                    cells.append(f"<td>{escape(raw_value)}</td>")
            row_class = ' class="highlighted"' if highlighted else ""
            body_rows.append(f"<tr{row_class}>{''.join(cells)}</tr>")
        caption_html = f"<figcaption>{self.parser.renderInline(caption)}</figcaption>" if caption else ""
        return (f'<figure class="table-block"><div class="table-scroll"><table><thead><tr>{header_html}</tr></thead>'
                f"<tbody>{''.join(body_rows)}</tbody></table></div>{caption_html}</figure>")

    def render_audio_compare(self, node: DirectiveNode) -> str:
        attributes = node.attributes
        excerpt = attributes.get("excerpt", "").strip()
        if not excerpt:
            return self.warn(node, "'::audio-compare' needs an excerpt attribute")
        library = self.sample_library
        if library.load_error:
            return self.warn(node, f"audio comparison for '{excerpt}' cannot be built: {library.load_error}")
        available_variants = library.variants_for(excerpt)
        if not available_variants:
            known = ", ".join(library.excerpts()) or "none"
            return self.warn(node, f"no listening samples for excerpt '{excerpt}' in the sample index (known excerpts: {known})")
        requested_variants = split_list(attributes.get("variants")) or available_variants
        variants = []
        for variant in requested_variants:
            if variant not in available_variants:
                self.warn(node, f"excerpt '{excerpt}' has no variant '{variant}' in the sample index")
                continue
            samples = [library.publish(entry) for entry in library.entries_for(excerpt, variant)]
            variants.append({
                "name": variant,
                "label": attributes.get(f"label-{variant}") or VARIANT_LABELS.get(variant, variant),
                "explanation": attributes.get(f"explain-{variant}") or VARIANT_EXPLANATIONS.get(variant, ""),
                "samples": samples,
            })
        if not variants:
            return self.warn(node, f"audio comparison for '{excerpt}' has no usable variant")
        self.player_counter += 1
        player_identifier = f"player-{self.player_counter}"
        title = attributes.get("title") or f"Listen: {excerpt}"
        configuration = {"excerpt": excerpt, "title": title, "variants": variants}
        configuration_json = json.dumps(configuration, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        note_html = f'<p class="player-note">{self.parser.renderInline(attributes["note"])}</p>' if attributes.get("note") else ""
        download_html = DOWNLOAD_PLACEHOLDER if self.audio_block_count == 0 else ""
        self.audio_block_count += 1
        fallback_links = " · ".join(
            f'<a href="{escape(sample["url"])}">{escape(sample["label"])}</a>' for sample in variants[0]["samples"] if not sample.get("missing")
        )
        return (
            f'<section class="audio-compare" id="{player_identifier}" data-player tabindex="0" aria-label="{escape(title)}">'
            f'<header class="player-header"><h3 class="player-title">{escape(title)}</h3>{note_html}</header>'
            f'<div class="player-mount"><p class="player-status">Loading the player…</p>'
            f"<noscript><p>The comparison player needs JavaScript. Samples: {fallback_links}</p></noscript></div>"
            f'<script type="application/json" class="player-configuration">{configuration_json}</script>'
            f"{download_html}</section>"
        )


def parse_source_lines(lines: list[str]) -> list[tuple[int, str]]:
    sources: list[list] = []
    for line in lines:
        match = re.match(r"^\s*\[(\d+)\]\s*(.*)$", line)
        if match:
            sources.append([int(match.group(1)), match.group(2).strip()])
        elif line.strip() and sources:
            sources[-1][1] += " " + line.strip()
    return [(number, text) for number, text in sources]


def split_list(text: str | None) -> list[str]:
    if not text:
        return []
    return [part.strip() for part in text.split(",") if part.strip()]


def parse_number(text):
    if text is None:
        return None
    try:
        value = float(str(text).strip())
    except ValueError:
        return None
    return value if value == value else None


def format_number(text: str, precision: int | None) -> str:
    value = parse_number(text)
    stripped = text.strip()
    if value is None:
        return stripped
    if precision is not None:
        return f"{value:.{precision}f}"
    return stripped
