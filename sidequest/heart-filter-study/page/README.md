# Writing `page/read.md`

`src/build_page.py` turns `page/read.md` into a self-contained dark site in `page/site/`
(`index.html` + `assets/`). Every path in a directive is **relative to the study folder**
(`heart-filter-study/`).

```sh
.venv/Scripts/python.exe src/build_page.py                          # page/read.md -> page/site/
.venv/Scripts/python.exe src/build_page.py --with-download-zip --zip page/site.zip
# demo with synthetic data (regenerate it with: python src/page_example_data.py)
.venv/Scripts/python.exe src/build_page.py --input page/read.example.md --output page/example-site --samples-index page/example-data/index.json
```

Options: `--input`, `--output` (deleted and rebuilt each time; only folders created by the
generator are deleted), `--samples-index` (default `listening/samples/index.json`),
`--with-download-zip` (packs the 24-bit originals into `assets/samples.zip` and adds one
"Download all samples (ZIP)" link under the first player), `--zip` (the finished site as a ZIP
with `index.html` at its root, for upload). Problems never stop the build: they are printed as
`warning:` lines and shown as a red dashed box on the page, so a clean build ends with `0 warnings`.

## Front matter

```
---
title: Which filter should the stethoscope use?
subtitle: One-line plain-language summary
authors: Nico Friedrich, with AI assistance   # optional; own line below the subtitle
date: 23 November 2026
status: Interim            # badge next to the date
watermark: Written by … on behalf of … running in …   # last line of the page
---
```

## Markdown

GitHub-style Markdown: headings, emphasis, lists, tables (they scroll sideways on phones),
links, inline code, code blocks, block quotes. **Every `##` heading becomes an entry in the table
of contents** (sticky sidebar on wide screens, a collapsed "Contents" box on phones); use `###`
for subsections that should not appear there. A literal `[1]` or `[1, 3]` in the text becomes a
link to source 1 (and 3), but only if that number exists in `::sources`.

## Directives

Each directive starts at the beginning of a line. Attribute values go in double quotes; write
`\"` for a quote inside a value. Block directives end with a line `::end` (or put body and
`::end` on the same line: `::term{name="x"} text ::end`).

| Directive | What it does |
| --- | --- |
| `::figure{src="results/figures/a.png" alt="…" caption="…" width="wide"}` | Image with caption; tap opens it full size. `width="text"` keeps it at text width. A missing file shows a placeholder naming the path. Always give `alt`. |
| `::summary` … `::end` | "Result in brief" card (Markdown inside). Optional `title="…"`. |
| `::callout{kind="finding"}` … `::end` | Coloured box. `kind`: `finding`, `limitation`, `decision` ("Project decision"), `open` ("Open point"). |
| `::term{name="band-pass filter"}` … `::end` | "In plain words" definition box; also listed in the glossary. |
| `::glossary` | All terms, alphabetically, linked to their boxes. |
| `::audio-compare{excerpt="resting" …}` | The listening comparison player (below). |
| `::sources` … `::end` | Numbered sources, one per line: `[1] Author, "Title," Venue, year. URL`. A line without `[n]` continues the previous source. |
| `::table-csv{src="results/x.csv" …}` | Table from a CSV (below). |
| `::raw-html` … `::end` | HTML passed through unchanged. Do not load anything from the internet in it. |

### `::audio-compare`

```
::audio-compare{excerpt="resting" variants="device,madeup,matched" title="Resting heart" note="Use headphones."}
```

- `excerpt` (required) must match `excerpt` in `listening/samples/index.json`; the build
  warning lists the known names if it does not.
- `variants`: which variants to offer and in what order (default: all in the index). Built-in
  labels: `device` "As the device plays it today", `madeup` "With a fixed boost per position",
  `matched` "Same loudness for all". Override per variant with `label-device="…"`, and the
  one-line explanation with `explain-device="…"` (likewise for `madeup`, `matched` and others).
- `title`, `note`: heading and one-line hint above the player.
- Every filter in the index for that excerpt and variant becomes one row, in index order. The
  row shows the applied gain, output peak, loudness and clipped samples (amber when > 0); a
  missing value shows "–". Readers can tap rows while playing (same position, seamless loop),
  use keys 1–9 and space, hide the names for a blind test, and see the waveform with the
  full-scale lines.

### `::table-csv`

```
::table-csv{src="results/bpm.csv" columns="identifier,mean_absolute_error_bpm" headers="Filter,Mean error (BPM)" rows="10" precision="2" caption="…" highlight="identifier=butterworth_hp2_25_lp2_150"}
```

`columns` selects and orders columns (default: all); `headers` renames them (same count);
`rows` keeps the first N rows, so sort the CSV first; numbers are right-aligned and shown exactly as
written in the CSV (signs, decimals and rounding included), unless `precision="2"` (or any count) is given; `highlight`
marks rows where `column=value` (several conditions separated by `;`). The highlight column does not
need to be shown.

## Things to know

- Keep the page self-contained: no external images, fonts or scripts. Links to sources are fine.
- An unknown directive (for example a typo like `::callut`) shows a warning box, not your text.
- The samples copied into the site are the 16-bit 16 kHz `web_file`s, lossless FLAC (about
  60–100 kB each; WAV is accepted too and keeps its extension); the site size is printed at the
  end of the build. The player decodes FLAC with the browser's own decoder (current Chrome,
  Edge, Firefox and Safari).
