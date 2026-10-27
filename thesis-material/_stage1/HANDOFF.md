# Stage 1 hand-off

Inventory contains **133 units** (35 require citations; 29 have fewer than three verified sources). The JSON is canonical; the Markdown is its readable projection.

## Counts by chapter

- Anforderungen: 10
- Diskussion/Ausblick: 5
- Einleitung/Motivation: 2
- Ethik/Datenschutz/Regulatorik: 3
- Evaluation/Methodik: 57
- Grundlagen (medizinisch: Herztöne, Murmurs, Auskultation): 3
- Grundlagen (technisch: Akustik, MEMS, I2S, DSP/Filter, BPM, Time-Stretch, Embedded/RTOS, FHIR/TLS): 4
- Implementierung: 8
- Projektmanagement/Formales: 9
- Stand der Technik: 2
- Systemarchitektur: 30

## Counts by type

- contradiction: 2
- decision: 17
- definition: 4
- fact: 15
- formal-rule: 3
- measurement: 17
- method: 25
- open-question: 7
- parameter: 18
- requirement: 14
- risk: 11

## Source gaps

- **Incomplete source sets (<3 sources):** 29 units: U011, U030, U041, U042, U043, U045, U046, U047, U049, U050, U051, U052, U053, U054, U055, U056, U057, U059, U061, U062, U064, U065, U066, U067, U069, U071, U072, U073, U074.
- **At least one page/section unverified:** 15 units: U011, U043, U044, U045, U046, U047, U048, U051, U057, U058, U059, U060, U063, U064, U068.
- Shared bibliography contains 16 sources checked through browser search/open. Some cited evidence was verified only from a search excerpt; target pages could not always be opened.
- Directly opened sources include PhysioNet CirCor dataset metadata, the Springer murmur paper, HL7 FHIR R4 vital-sign profile, Regenstrief LOINC, and the ISCA WSOLA record.
- CirCor cohort counts/annotation specifics, microphone frequency-response table, platform/TLS resource estimates, latency thresholds, acoustic coupling numeric estimates, ethics rules and THA rules need tighter page-level validation. Do not treat an existing research-report statement as independently source-verified merely because the report states it.

## Contradictions and open points

- **U037 — contradicted:** W1: Aufgabenbeschreibungen führen Q1, Kettencharakterisierung und AP 2.2 auf, die interne Entscheidung verwirft gleichzeitig die formale Messung; die vorgesehenen Playback-Signale durchlaufen die reale Bruststückkopplung nicht.
- **U039 — contradicted:** W2: Nummerierung der beiden SP3T-Schalter weicht ab: intern/open-questions ordnen Schalter 1 Geschwindigkeit und Schalter 2 Filter zu, Hardwareliste ordnet Schalter 1 Filter und Schalter 2 Geschwindigkeit zu.
- **W1 remains unresolved:** decide whether to redefine Q1/AP 2.2 qualitatively, remove it, or run the proposed acoustic-chain measurement. Playback does not exercise the physical coupling.
- **W2 remains unresolved:** consistently assign the two identical SP3T switches to filter and speed controls.
- **Implementation/wiring caveat:** the newer README maps a speed switch and SD card on carrier Rev A but says those pins were not covered by the 2026-09-16 wiring confirmation. Distinguish this from the historical W2 assignment discrepancy.
- **Status/date caveat:** `open-questions.md` is labeled research status 2026-08-11 and `widersprueche.md` 2026-08-15; later implementation documents include 2026-09-16 and 2026-10-02 updates. These later records do not demonstrate new-firmware hardware acceptance.

## Files not readable or limits

- `preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Abgabe.pdf` could not be text-extracted: `pdftotext`, `mutool`, and Python PDF libraries are not installed. Its Markdown counterpart was read.
- Zero-byte files: `Development/system/architecture/architecture`, `Development/system/spec/spec`, `Development/system/design/design`, and `Development/system/requirements/requirements`.
- The 12 R*.json bundles were inspected for structure, response/citation/search-result metadata and compared with paired Markdown reports; answer text shares the Markdown reports’ vocabulary/content. Source and page details still need independent checking.
- Source code was skimmed with targeted searches for documented parameters/concurrency/measurements; no implementation-level code walk was performed.
- Statements are concise groupings when a source paragraph/table contains related parameters. Stage 2 should split grouped measurement tables/long protocol verdicts further if the thesis needs atomic traceability.

## Stage 2 notes

- Keep project decisions, internal targets and recorded device observations separate from literature-backed facts. Several values remain provisional engineering targets (e.g. 40–800 Hz / 25–150 Hz filter candidates, <30 ms latency, BPM acceptance limits).
- Hardware evidence is commit-specific: 2026-08-14 reports 4 PASS / 4 PARTIAL / 3 BLOCKED; 2026-08-19 reports all 11 physical cases BLOCKED. Later integrated builds/host tests do not replace physical tests.
- Do not infer the thesis hand-in date from repository records; the user supplied 11.01.2027, while repo plans contain a differing “Ende Januar” target.
- Citation completeness is not topic completeness: source gaps are marked `sources_incomplete: true`; unverified page positions are `page: unverified`.

<!-- created by GPT-6-Luna on behalf of Nico running in T3 Code through Codex. -->
