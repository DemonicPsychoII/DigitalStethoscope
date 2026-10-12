# Evaluation: Firmware, Funktion und Ressourcen

[Zum Einstieg](../README.md) · [Offene Punkte](../offene-punkte.md)

Prüfverfahren → Build/Host-Nachweise → historische Hardwarebefunde → offene Integration.

**29 aktive Einheiten.** Schreibreihenfolge: Definition → Mechanismus → Werte → Folgerung. Die Aussagen sind Material, kein fertiger Fließtext.

## Funktionstest und physische Annahmekriterien

### Mechanismen und Zusammenhänge

<a id="a075"></a>
**A075 · PROJEKTDOKUMENTATION · ANNAHME**

R04 nennt ESP-DSP-Grundoperationsbenchmarks, aber keinen direkt vergleichbaren vollständigen ESP32-S3-WSOLA-/Phase-Vocoder-Benchmark bei 8 kHz.

**Ursprung:** [preThesis/03-recherche/R04-time-stretch.md:167-190,247-260](../../preThesis/03-recherche/R04-time-stretch.md#L167)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

### Werte und dokumentierte Befunde

<a id="a074"></a>
**A074 · EIGENER ZIELWERT / VORLÄUFIGER VORSCHLAG · ANNAHME · ersetzt U052**

R04 schätzt 20–50 Mio. Zyklen/s für WSOLA und 10–30 Mio. Zyklen/s für Phase-Vocoder auf ESP32-S3; dies sind Schätzungen, keine gemessenen Gesamtanwendungsbenchmarks.

**Ursprung:** [preThesis/03-recherche/R04-time-stretch.md:192-250](../../preThesis/03-recherche/R04-time-stretch.md#L192)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

### Folgerungen, Entwurfsentscheidungen und Grenzen

<a id="u108"></a>
**U108 · METHODE / PRÜFVERFAHREN**

Firmware README says software diagnostics count 8 ms deadline misses and RX/TX/allocation failures, but slab use is not exact hardware FIFO depth; end-to-end acoustic/electrical latency must be measured separately.

**Ursprung:** [Development/system/coding/bringup-zephyr/README.md:217-222](../../Development/system/coding/bringup-zephyr/README.md#L217)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="c015"></a>
**C015 · METHODE / PRÜFVERFAHREN**

Für die untersuchte Anwendung verlangt R10 vor Implementierungsfestlegung einen Hands-on-Test von PDM-RX, PDM-zu-PCM-Konvertierung und DMA-Pufferung auf dem tatsächlich verwendeten Board.

**Ursprung:** [preThesis/03-recherche/R10-esp32-plattform.md:70-93](../../preThesis/03-recherche/R10-esp32-plattform.md#L70)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u090"></a>
**U090 · METHODE / PRÜFVERFAHREN**

TEST-PROTOCOL definiert manuelle Hardwareprüfungen, Verdrahtungs-/Electrical-Safety-, Audio-, Display-, Touch-, GPIO-, SD-, Netzwerk-/FHIR-Prüfungen und PASS/FAIL/BLOCKED-Evidenz.

**Ursprung:** [Development/system/coding/bringup-zephyr/TEST-PROTOCOL.md:1-1517](../../Development/system/coding/bringup-zephyr/TEST-PROTOCOL.md#L1)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

## Build-, Host- und QC-Nachweise

### Folgerungen, Entwurfsentscheidungen und Grenzen

<a id="u096"></a>
**U096 · METHODENVORSCHLAG**

BUILD-TIMES beschreibt einen vergleichbaren Buildzeit-Benchmark über Geräte, mit Warm-up-Ausschluss, Median/Min/Max und Trennung nach Source-Hash, Toolpins, Board und Cachepolitik; Ergebnisdateien sollen für Thesis-Messungen erhalten bleiben.

**Ursprung:** [Development/system/testing/BUILD-TIMES.md:1-89](../../Development/system/testing/BUILD-TIMES.md#L1)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u094"></a>
**U094 · METHODE / PRÜFVERFAHREN**

CI-Hardwaregrenze: ESP32-S3-Build belegt Kompilierung/Linken und Ressourcen-Fit, aber nicht Mikrofon-, DAC-, Display-, Touch-, GPIO-, ADC-, PWM- oder Verdrahtungsfunktion.

**Ursprung:** [Development/system/testing/CI-QUALITY-GATES.md:87-107](../../Development/system/testing/CI-QUALITY-GATES.md#L87)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u093"></a>
**U093 · METHODE / PRÜFVERFAHREN**

CI-QUALITY-GATES dokumentiert gepinnte Zephyr- und Werkzeugversionen, wiederholbare lokale/CI-Prüfungen sowie getrennte Builds und statische Prüfungen; Quelle beschreibt Entwicklungs-/Verifikationsmethode, keine medizinische Evidenz.

**Ursprung:** [Development/system/testing/CI-QUALITY-GATES.md:1-57](../../Development/system/testing/CI-QUALITY-GATES.md#L1)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u132"></a>
**U132 · METHODE / PRÜFVERFAHREN**

hardware-results.schema.json requires schema_version and records_by_firmware_commit, organizing hardware verdicts by firmware commit.

**Ursprung:** [Development/system/coding/bringup-zephyr/evidence/hardware-results.schema.json:1-100](../../Development/system/coding/bringup-zephyr/evidence/hardware-results.schema.json#L1)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u092"></a>
**U092 · RISIKO / EINORDNUNG**

QC-EVALUATION nennt als offene Aktionen: I²S/LEDC-Pinmux und XPT2046-Kalibrierung validieren, Touch-Callback-Zustand absichern, Eingabepolling ≤20 ms dokumentieren, Laufzeitfehlerbehandlung prüfen sowie Ergebnisse an Firmware-Commit binden.

**Ursprung:** [Development/system/testing/QC-EVALUATION.md:26-40](https://github.com/DemonicPsychoII/DigitalStethoscope/blob/23c1ea492270b897532896179e35f873eee823be/Development/system/testing/QC-EVALUATION.md?plain=1#L26) (**Herkunft verschoben:** seit 89ca8b1 nicht mehr eingecheckt; wird von `qc_eval.py` nach `artifacts/qc/` erzeugt. Link zeigt die zitierte historische Fassung. Aktuell: [Testing-README: Source-level QC](../../Development/system/testing/README.md#source-level-qc))
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u095"></a>
**U095 · METHODE / PRÜFVERFAHREN**

Testing-README unterscheidet QC-Score von funktionaler Evaluation; CI-Hosttests und Offline/QC/Netzwerk-QC-Builds schließen die physische Hardware-Abnahmematrix nicht ab.

**Ursprung:** [Development/system/testing/README.md:27-40](../../Development/system/testing/README.md#L27)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u098"></a>
**U098 · METHODE / PRÜFVERFAHREN**

THA-baseline-traceability.json bindet den institutionalisierten Vergleich an Revision 4698995f203f73f4b264e4355ca30e2712163729 und drei SHA-256-Einträge.

**Ursprung:** [Development/system/testing/tha-baseline-traceability.json:1-10](../../Development/system/testing/tha-baseline-traceability.json#L1)
**Korrektur Stage 2 (2026-10-12):** Ursprungsliste in inventory-merged.json/inventory.json war eine Kopie der U100-Ursprünge; inventory.md nennt die Traceability-JSON, die die Aussage tatsächlich belegt. Ursprüngliche Liste: preThesis/02-entscheidungen/widersprueche.md:1-4; preThesis/02-entscheidungen/open-questions.md:7-11; preThesis/05-hardware/hardware.md:32-34; Development/system/coding/bringup-zephyr/README.md:1-160. Quelle: [_build/stage2-corrections.json](../_build/stage2-corrections.json).
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u126"></a>
**U126 · EIGENE ANFORDERUNG**

The evaluation protocol requires server readback to match Patient, LOINC, quantity, unit, timestamp and resource ID; TLS negative cases must not transfer successfully, audio must continue, and retry is explicit.

> **Überholt (Stand integration, 2026-10-12):** „Retry is explicit“ gilt für das MVP nicht mehr. Aktuell: Fehlgeschlagene Sendungen werden angezeigt und abgebrochen; keine automatische oder manuelle Wiederholungswarteschlange; Zeitüberschreitung nach Server-Commit gilt als „Unverified“. Readback-Abgleich bleibt. – siehe [MVP-Entscheidungen 11.10.](../../Development/system/planning/mvp-decisions-2026-10-11.md#confirmed-scope-and-behavior).

**Ursprung:** [Development/system/coding/bringup-zephyr/EVAL-GUIDE.md:84-85](../../Development/system/coding/bringup-zephyr/EVAL-GUIDE.md#L84)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

## Laufzeit, Speicher und Netzwerkprüfung

### Folgerungen, Entwurfsentscheidungen und Grenzen

<a id="a076"></a>
**A076 · METHODENVORSCHLAG · ANNAHME**

R04 empfiehlt CPU-Last, RAM, Latenz, Dropouts, Frequenzlage, S1/S2-Dauer und subjektive Artefakte zu messen.

**Ursprung:** [preThesis/03-recherche/R04-time-stretch.md:262-279](../../preThesis/03-recherche/R04-time-stretch.md#L262)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="c024"></a>
**C024 · METHODENVORSCHLAG · ANNAHME**

R10 empfiehlt, optionale Time-Stretch-Verfahren getrennt zu implementieren und zu vermessen; für höhere Audioqualität sind mehrere FFTs pro Hop, Overlap-Add, Zwischenpuffer und kleine Blocklängen als Aufwandstreiber benannt.

**Ursprung:** [preThesis/03-recherche/R10-esp32-plattform.md:297-307](../../preThesis/03-recherche/R10-esp32-plattform.md#L297)
**Belege:** [Roelands, M., & Verhelst, W 1993 · wsola_roelands](https://doi.org/10.21437/Eurospeech.1993-59) — Fundstelle: Abstract and bibliographic record (web text lines 4–18). (aus Stage 1; am Original prüfen); [Verhelst, W., & Roelands, M 1993 · wsola_verhelst](https://ieeexplore.ieee.org/document/319366) — Seite prüfen · 🔒 Volltext kostenpflichtig; [Espressif Systems · esp_dsp_benchmarks](https://docs.espressif.com/projects/esp-dsp/en/latest/esp32/esp-dsp-benchmarks.html) — Fundstelle: FFTs Radix-2 rows (aus Stage 1; am Original prüfen)

<a id="c042"></a>
**C042 · METHODENVORSCHLAG**

R11 empfiehlt, den größten verfügbaren internen Heap zu beobachten und ihn während des Handshakes bei weiterhin belegten Audiopuffern zu messen, da die gesamte freie Heapmenge nach dem Boot nicht belegt, dass die Spitzenallokation des Handshakes gelingt.

**Ursprung:** [preThesis/03-recherche/R11-fhir-tls.md:209-218](../../preThesis/03-recherche/R11-fhir-tls.md#L209)
**Belege:** [Espressif Systems · esp_tls_faq](https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/protocols/esp-tls.html) — Fundstelle: Question on handshake memory (aus Stage 1; am Original prüfen); [Espressif Systems · esp_mbedtls_s3](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/protocols/mbedtls.html) — Seite prüfen; [Espressif Systems · esp_tls_s3](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/protocols/esp_tls.html) — Fundstelle: Overview (aus Stage 1; am Original prüfen)

## Dokumentierte Befunde mit Datum und Versionsbezug

### Werte und dokumentierte Befunde

<a id="u129"></a>
**U129 · EIGENER DOKUMENTIERTER BEFUND**

Hardware-results evidence for commit 2cd6d4c (2026-08-14) records 4 PASS, 4 PARTIAL, 3 BLOCKED cases; record is retrospective and lacks flashed-binary hash.

**Ursprung:** [Development/system/coding/bringup-zephyr/evidence/hardware-results.json:1-200](../../Development/system/coding/bringup-zephyr/evidence/hardware-results.json#L1)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u130"></a>
**U130 · EIGENER DOKUMENTIERTER BEFUND**

Hardware-results evidence for commit 418f9ba (2026-08-19) records all 11 physical cases BLOCKED because no board was attached/flashed; compile/simulation is not physical acceptance.

**Ursprung:** [Development/system/coding/bringup-zephyr/evidence/hardware-results.json:1-200](../../Development/system/coding/bringup-zephyr/evidence/hardware-results.json#L1)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u127"></a>
**U127 · EIGENER DOKUMENTIERTER BEFUND**

Integrated build evidence dated 2026-09-24 records PASS for offline, QC and network-QC/second-switch ESP32-S3 builds with zero application compiler warnings; network-QC used 334,320 bytes internal DRAM segment and 2,089,472 bytes external DRAM window.

**Ursprung:** [Development/system/coding/bringup-zephyr/evidence/integrated-build-results.json:1-200](../../Development/system/coding/bringup-zephyr/evidence/integrated-build-results.json#L1)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u128"></a>
**U128 · EIGENER DOKUMENTIERTER BEFUND**

Integrated host evidence records 73 passing tests for portable C DSP/FHIR functions, evaluation CLI and Python HTTPS readback (explicitly not the on-device TLS stack); Zephyr native_sim logic has 10 passing tests.

**Ursprung:** [Development/system/coding/bringup-zephyr/evidence/integrated-build-results.json:1-200](../../Development/system/coding/bringup-zephyr/evidence/integrated-build-results.json#L1)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u133"></a>
**U133 · EIGENER DOKUMENTIERTER BEFUND**

logic-tests.txt records 10 passing app_logic cases covering audio recovery, brightness, degraded-mode decisions, error handling, probe/retry transitions, status formatting, switch decoding and touch color transitions.

**Ursprung:** [Development/system/coding/bringup-zephyr/evidence/logic-tests.txt:1-40](../../Development/system/coding/bringup-zephyr/evidence/logic-tests.txt#L1)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u097"></a>
**U097 · EIGENER DOKUMENTIERTER BEFUND**

QC-Ergebnis JSON dokumentiert 10 Kontrollen mit Score je 10 und Gate PASS; Verifikation basiert teils auf Heuristiken, und erforderliche Maßnahmen bleiben trotz PASS ausgewiesen.

**Ursprung:** [Development/system/testing/qc-eval-results.json:1-92](https://github.com/DemonicPsychoII/DigitalStethoscope/blob/23c1ea492270b897532896179e35f873eee823be/Development/system/testing/qc-eval-results.json#L1) (**Herkunft verschoben:** seit 89ca8b1 nicht mehr eingecheckt; wird von `qc_eval.py` nach `artifacts/qc/` erzeugt. Link zeigt die zitierte historische Fassung. Aktuell: [Testing-README: Source-level QC](../../Development/system/testing/README.md#source-level-qc))
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u091"></a>
**U091 · EIGENER DOKUMENTIERTER BEFUND**

QC-EVALUATION meldet 100/100 PASS für statischen THA-baseline-Vergleich, datiert 2026-09-24; der Bericht sagt ausdrücklich, dass dies keine Compilation, Instrumentierung, Elektroprüfung, Audiomessung oder manuelle Hardwareprüfung ersetzt.

**Ursprung:** [Development/system/testing/QC-EVALUATION.md:1-9](https://github.com/DemonicPsychoII/DigitalStethoscope/blob/23c1ea492270b897532896179e35f873eee823be/Development/system/testing/QC-EVALUATION.md?plain=1#L1) (**Herkunft verschoben:** seit 89ca8b1 nicht mehr eingecheckt; wird von `qc_eval.py` nach `artifacts/qc/` erzeugt. Link zeigt die zitierte historische Fassung. Aktuell: [Testing-README: Source-level QC](../../Development/system/testing/README.md#source-level-qc))
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u118"></a>
**U118 · EIGENER DOKUMENTIERTER BEFUND**

TEST-PROTOCOL diagnosis: 240×320×2-byte screen fill at 10 MHz takes about 120 ms, exceeding audio RX ring budget and causing I²S error state; recovery work was identified.

**Ursprung:** [Development/system/coding/bringup-zephyr/TEST-PROTOCOL.md:1468-1471](../../Development/system/coding/bringup-zephyr/TEST-PROTOCOL.md#L1468)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u113"></a>
**U113 · EIGENER DOKUMENTIERTER BEFUND**

TEST-PROTOCOL historical result: button/LED passed; fitted switch was only two-position (3PDT) and could not exercise the intended third position.

**Ursprung:** [Development/system/coding/bringup-zephyr/TEST-PROTOCOL.md:1432-1434](../../Development/system/coding/bringup-zephyr/TEST-PROTOCOL.md#L1432)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u115"></a>
**U115 · EIGENER DOKUMENTIERTER BEFUND**

TEST-PROTOCOL historical result: INMP441 microphone peak tracked real sound (81–32643) with zero errors over 30 s on documented pins.

**Ursprung:** [Development/system/coding/bringup-zephyr/TEST-PROTOCOL.md:1439](../../Development/system/coding/bringup-zephyr/TEST-PROTOCOL.md#L1439)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u116"></a>
**U116 · EIGENER DOKUMENTIERTER BEFUND**

TEST-PROTOCOL historical result: PCM5102A passed I²S probe only; write-only I²S accepts a block even when module is unplugged, so this did not prove audible jack output.

**Ursprung:** [Development/system/coding/bringup-zephyr/TEST-PROTOCOL.md:1440](../../Development/system/coding/bringup-zephyr/TEST-PROTOCOL.md#L1440)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u114"></a>
**U114 · EIGENER DOKUMENTIERTER BEFUND**

TEST-PROTOCOL historical result: potentiometer measured 0–3083 mV monotonic; display/backlight was partial because touch generated several events per tap and audio stopped at first display redraw.

**Ursprung:** [Development/system/coding/bringup-zephyr/TEST-PROTOCOL.md:1436-1437](../../Development/system/coding/bringup-zephyr/TEST-PROTOCOL.md#L1436)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u117"></a>
**U117 · EIGENER DOKUMENTIERTER BEFUND**

TEST-PROTOCOL marked full assembly skipped because of the then-existing display/audio defect; later protocol sections record corrective findings and a subsequent no-board run where T00–T10 were blocked for lack of flash/physical measurements.

**Ursprung:** [Development/system/coding/bringup-zephyr/TEST-PROTOCOL.md:1442,1499-1513](../../Development/system/coding/bringup-zephyr/TEST-PROTOCOL.md#L1442)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.
