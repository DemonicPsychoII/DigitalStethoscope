"""Build the static read site (index.html plus assets/) from a Markdown report with block directives.

Usage:
    python src/build_page.py [--input page/read.md] [--output page/site] [--samples-index listening/samples/index.json]
                             [--with-download-zip] [--zip page/site.zip]
"""

from __future__ import annotations

import argparse
import html
import shutil
import sys
import zipfile
from pathlib import Path

from page_audio import SampleLibrary
from page_document import parse_document
from page_render import DOWNLOAD_PLACEHOLDER, PageRenderer, escape

STUDY_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_FOLDER = STUDY_ROOT / "page" / "template"
OUTPUT_MARKER = ".generated-by-build-page"


def log(message: str):
    print(message, flush=True)


def prepare_output_folder(output_folder: Path, input_path: Path):
    resolved = output_folder.resolve()
    if resolved == STUDY_ROOT or resolved in STUDY_ROOT.parents or resolved in input_path.resolve().parents:
        raise SystemExit(f"refusing to clean {resolved}: it contains the study or the input file")
    if resolved.exists():
        is_generated = (resolved / OUTPUT_MARKER).exists()
        if not is_generated and any(resolved.iterdir()):
            raise SystemExit(f"refusing to clean {resolved}: it is not empty and was not created by build_page.py")
        shutil.rmtree(resolved)
    (resolved / "assets").mkdir(parents=True)
    (resolved / OUTPUT_MARKER).write_text("Created by src/build_page.py; this folder is deleted on every build.\n", encoding="utf-8")


def render_table_of_contents(entries, css_class: str) -> str:
    items = "".join(f'<li><a href="#{identifier}">{html.escape(title)}</a></li>' for identifier, title in entries)
    return f'<ol class="{css_class}">{items}</ol>'


def render_page(front_matter: dict, body_html: str, table_of_contents) -> str:
    title = front_matter.get("title", "Untitled read")
    subtitle = front_matter.get("subtitle", "")
    date = front_matter.get("date", "")
    status = front_matter.get("status", "")
    watermark = front_matter.get("watermark", "")
    authors = front_matter.get("authors", "")
    subtitle_html = f'<p class="page-subtitle">{escape(subtitle)}</p>' if subtitle else ""
    authors_html = f'\n<p class="page-authors">{escape(authors)}</p>' if authors else ""
    meta_parts = []
    if status:
        meta_parts.append(f'<span class="status-badge">{escape(status)}</span>')
    if date:
        meta_parts.append(f'<time class="page-date">{escape(date)}</time>')
    meta_html = f'<p class="page-meta">{"".join(meta_parts)}</p>' if meta_parts else ""
    watermark_html = f'<p class="watermark">{escape(watermark)}</p>' if watermark else ""
    if table_of_contents:
        sidebar_html = (f'<nav class="toc-sidebar" aria-label="Contents"><p class="toc-heading">Contents</p>'
                        f'{render_table_of_contents(table_of_contents, "toc-list")}</nav>')
        mobile_html = (f'<details class="toc-mobile"><summary>Contents</summary>'
                       f'<nav aria-label="Contents">{render_table_of_contents(table_of_contents, "toc-list")}</nav></details>')
    else:
        sidebar_html = mobile_html = ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark">
<title>{escape(title)}</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<div class="page-shell{' has-toc' if table_of_contents else ''}">
{sidebar_html}
<main class="page-main" id="top">
<header class="page-header">
{meta_html}
<h1 class="page-title">{escape(title)}</h1>
{subtitle_html}{authors_html}
</header>
{mobile_html}
<article class="article-body">
{body_html}
</article>
<footer class="page-footer">{watermark_html}</footer>
</main>
</div>
<div class="figure-overlay" hidden role="dialog" aria-modal="true" aria-label="Figure, full size">
<button type="button" class="figure-overlay-close" aria-label="Close figure">Close</button>
<img alt="">
<p class="figure-overlay-caption"></p>
</div>
<script src="assets/page.js"></script>
</body>
</html>
"""


def folder_size(folder: Path) -> tuple[int, int]:
    files = [path for path in folder.rglob("*") if path.is_file()]
    return len(files), sum(path.stat().st_size for path in files)


def write_site_zip(output_folder: Path, zip_path: Path):
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(output_folder.rglob("*")):
            if path.is_file() and path.name != OUTPUT_MARKER:
                archive.write(path, path.relative_to(output_folder).as_posix())


def format_bytes(size: int) -> str:
    return f"{size / 1_000_000:.2f} MB" if size >= 1_000_000 else f"{size / 1000:.1f} kB"


def main(arguments=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", default="page/read.md", help="Markdown report (relative to the study folder)")
    parser.add_argument("--output", default="page/site", help="output folder, rebuilt from scratch")
    parser.add_argument("--samples-index", default="listening/samples/index.json", help="listening sample index JSON")
    parser.add_argument("--with-download-zip", action="store_true", help="pack the full-resolution samples into assets/samples.zip")
    parser.add_argument("--zip", help="also write the finished site as a ZIP with index.html at its root")
    options = parser.parse_args(arguments)

    input_path = (STUDY_ROOT / options.input).resolve()
    output_folder = (STUDY_ROOT / options.output).resolve()
    samples_index = (STUDY_ROOT / options.samples_index).resolve()
    if not input_path.is_file():
        log(f"error: input file not found: {input_path}")
        log("hint: try  python src/build_page.py --input page/read.example.md --output page/example-site "
            "--samples-index page/example-data/index.json")
        return 2

    warnings: list[str] = []
    prepare_output_folder(output_folder, input_path)
    for asset_name in ("style.css", "page.js"):
        shutil.copyfile(TEMPLATE_FOLDER / asset_name, output_folder / "assets" / asset_name)

    document = parse_document(input_path.read_text(encoding="utf-8-sig"))
    warnings.extend(document.warnings)
    sample_library = SampleLibrary(samples_index, STUDY_ROOT, output_folder, warnings, log)
    renderer = PageRenderer(document, STUDY_ROOT, output_folder, sample_library, warnings, log)
    body_html = renderer.render_nodes(document.nodes)

    download_html = ""
    if options.with_download_zip:
        download_zip = output_folder / "assets" / "samples.zip"
        file_count = sample_library.write_download_zip(download_zip) if not sample_library.load_error else 0
        if file_count:
            download_html = (f'<p class="download-all"><a href="assets/samples.zip" download>Download all samples (ZIP)</a> '
                             f'<span class="download-size">{file_count} WAV files, full resolution, '
                             f'{format_bytes(download_zip.stat().st_size)}</span></p>')
        else:
            warnings.append("--with-download-zip given but no original sample files were found")
    if download_html and renderer.audio_block_count == 0:
        body_html += download_html
    body_html = body_html.replace(DOWNLOAD_PLACEHOLDER, download_html)

    page_html = render_page(document.front_matter, body_html, renderer.environment.get("table_of_contents", []))
    (output_folder / "index.html").write_text(page_html, encoding="utf-8")

    for warning in warnings:
        log(f"warning: {warning}")
    file_count, total_bytes = folder_size(output_folder)
    audio_folder = output_folder / "assets" / "audio"
    audio_count = sum(1 for path in audio_folder.rglob("*") if path.suffix.lower() in (".flac", ".wav")) if audio_folder.exists() else 0
    log(f"Built {output_folder / 'index.html'}")
    log(f"Summary: 1 page, {len(renderer.figure_targets)} figures, {audio_count} audio files, "
        f"{renderer.audio_block_count} comparison players, {file_count} files, {format_bytes(total_bytes)} ({total_bytes} bytes), "
        f"{len(warnings)} warnings")
    if options.zip:
        zip_path = (STUDY_ROOT / options.zip).resolve()
        write_site_zip(output_folder, zip_path)
        log(f"Site ZIP: {zip_path} ({format_bytes(zip_path.stat().st_size)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
