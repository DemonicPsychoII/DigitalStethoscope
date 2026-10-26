# Evaluation: Fragen und Annahmekriterien

[Zum Einstieg](../README.md) · [Offene Punkte](../offene-punkte.md)

Forschungsfragen → eigene Akzeptanzziele → Grenzen des Nachweises.

**16 aktive Einheiten.** Schreibreihenfolge: Definition → Mechanismus → Werte → Folgerung. Die Aussagen sind Material, kein fertiger Fließtext.

## Schreibbausteine

### Werte und dokumentierte Befunde

<a id="u125"></a>
**U125 · EIGENER DOKUMENTIERTER BEFUND**

Hardware report historic 2026-08 test had no verified end-to-end loopback, audible DAC output, or simultaneous full assembly; the microphone itself passed the reported 30-second input test.

**Ursprung:** [Development/system/coding/bringup-zephyr/TEST-PROTOCOL.md:1439-1449](../../Development/system/coding/bringup-zephyr/TEST-PROTOCOL.md#L1439)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u131"></a>
**U131 · EIGENER DOKUMENTIERTER BEFUND**

Wiring-confirmation JSON records a user statement dated 2026-09-16 about the existing evaluation assembly; it has no board revision, captures or flashed-image hash and does not cover second-switch extension or new-firmware acceptance.

**Ursprung:** [Development/system/coding/bringup-zephyr/evidence/wiring-confirmation.json:1-10](../../Development/system/coding/bringup-zephyr/evidence/wiring-confirmation.json#L1)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

### Folgerungen, Entwurfsentscheidungen und Grenzen

<a id="u005"></a>
**U005 · EIGENE ANFORDERUNG**

Der Echtzeit-Audiopfad, Filterwahl, reduzierte Wiedergabegeschwindigkeit und sichere FHIR-Übertragung werden anhand definierter Funktionskriterien geprüft.

> **Überholt (Stand integration, 2026-10-22):** Reduzierte Wiedergabegeschwindigkeit ist kein Prüfgegenstand mehr. Seit 14.10. gilt eine Anforderung nur, wenn Nico sie am Gerät mit verfügbarer Ausrüstung eindeutig prüfen kann. Aktuell: Abnahme über REQ-01…REQ-15: Audiopfad (REQ-01, REQ-02, REQ-04, REQ-05), Filterwahl (REQ-03), BPM (REQ-06…REQ-08), FHIR-Übertragung (REQ-09, REQ-10, REQ-15), WLAN und Serverzertifikat (REQ-11, REQ-12), Fehleranzeige (REQ-13, REQ-14). – siehe [Systemanforderungen](../../Development/system/requirements/system-requirements.md#system-requirements-mvp), [MVP-Entscheidungen 14.10. (Anforderungen)](../../Development/system/planning/mvp-decisions-2026-10-14.md#requirements).

**Ursprung:** [preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Abgabe.md:9](../../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Abgabe.md#L9)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u004"></a>
**U004 · EIGENE ANFORDERUNG**

Die BPM-Bestimmung wird quantitativ gegen eine geeignete Referenz evaluiert; Testsignale, Referenzen, Metriken und Versuchsabläufe sollen vorab festgelegt werden.

**Ursprung:** [preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Abgabe.md:9](../../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Abgabe.md#L9)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u089"></a>
**U089 · METHODE / PRÜFVERFAHREN**

EVAL-GUIDE definiert physische Annahmekriterien und trennt Software-Build-Nachweis von Hardware-Funktion; ungeprüfte Positionen bleiben offen bzw. blockiert.

**Ursprung:** [Development/system/coding/bringup-zephyr/EVAL-GUIDE.md:1-162](../../Development/system/coding/bringup-zephyr/EVAL-GUIDE.md#L1)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u109"></a>
**U109 · METHODE / PRÜFVERFAHREN**

EVAL-GUIDE labels filter coefficients and BPM thresholds as initial evaluation candidates rather than optimality claims, and distinguishes earlier confirmed wiring from acceptance of new firmware.

**Ursprung:** [Development/system/coding/bringup-zephyr/EVAL-GUIDE.md:8-17](../../Development/system/coding/bringup-zephyr/EVAL-GUIDE.md#L8)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u112"></a>
**U112 · METHODE / PRÜFVERFAHREN**

EVAL-GUIDE notes host timing is not MCU CPU-load evidence and static memory-fit/linking does not establish heap peaks or runtime stack headroom.

**Ursprung:** [Development/system/coding/bringup-zephyr/EVAL-GUIDE.md:38-43,93-98](../../Development/system/coding/bringup-zephyr/EVAL-GUIDE.md#L38)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u111"></a>
**U111 · EIGENE ANFORDERUNG · ANNAHME**

EVAL-GUIDE requires >=10 minutes of combined operation, zero audio processing deadline misses and >=25% stack headroom in every thread/ISR; TLS included if configured.

> **Überholt (Stand integration, 2026-10-22):** Die Dauerlaufprüfung von ≥10 Minuten ist ersetzt; ≥25 % Stack-/Heap-Reserve bleibt. Aktuell: Vorschlag: 30-Minuten-Soak mit Wasserständen während TLS und BPM, DMA-SRAM und PSRAM getrennt, zusätzlich kleinster größter freier Block und Allokationsfehlerpfade. – siehe [Latenzbudgets 11.10. (Resources)](../../Development/system/planning/mvp-decisions-2026-10-11.md#latency-research-and-proposed-budgets), [Entscheidungsregister D10](../../Development/system/planning/implementation-readiness.md#decision-register).

**Ursprung:** [Development/system/coding/bringup-zephyr/EVAL-GUIDE.md:81-98](../../Development/system/coding/bringup-zephyr/EVAL-GUIDE.md#L81)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u119"></a>
**U119 · RISIKO / EINORDNUNG**

EVAL-GUIDE says no integrated physical test was performed for the later firmware evaluation and records inherited wiring confirmation only; no new-firmware acceptance should be inferred.

**Ursprung:** [Development/system/coding/bringup-zephyr/EVAL-GUIDE.md:13-17,117-120](../../Development/system/coding/bringup-zephyr/EVAL-GUIDE.md#L13)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u123"></a>
**U123 · RISIKO / EINORDNUNG**

EVAL-GUIDE says the INMP441 usable low-frequency band is a hardware constraint; separate listening/analysis branches allow shared-vs-separate filter comparison but do not establish improved clinical recognition.

**Ursprung:** [Development/system/coding/bringup-zephyr/EVAL-GUIDE.md:153-157](../../Development/system/coding/bringup-zephyr/EVAL-GUIDE.md#L153)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u110"></a>
**U110 · EIGENE ANFORDERUNG · ANNAHME**

EVAL-GUIDE sets engineering acceptance targets: measured live latency <30 ms; provisional BPM MAE ≤5 BPM with ≥90% valid windows on defined clean fixtures; playback retained pitch within 2% at 440 Hz; physical input response ≤35 ms.

> **Überholt (Stand integration, 2026-10-22):** Mehrere EVAL-GUIDE-Zielwerte sind ersetzt: gemessene Live-Latenz <30 ms, BPM „≥90 % gültige Fenster“, Tonhöhe ±2 % bei 440 Hz und Eingabereaktion ≤35 ms. Aktuell: BPM (REQ-06): 10 Sitzungen à 30 s, jedes Ergebnis innerhalb ±5 BPM oder ±10 % gegen Pulsoximeter oder Smartwatch (14.10.). Latenz wird nach Gehör geprüft (REQ-05); <30 ms bleibt internes Designziel (P03). Replay ist keine Anforderung mehr (14.10.). Bedienreaktion ≤100 ms und Status ≤500 ms sind Kandidaten (P10). – siehe [MVP-Entscheidungen 14.10. (Verhalten)](../../Development/system/planning/mvp-decisions-2026-10-14.md#behavior), [Systemanforderungen](../../Development/system/requirements/system-requirements.md#system-requirements-mvp), [Designparameter P03/P10](../../Development/system/design/parameters.md#design-parameters-internal).

**Ursprung:** [Development/system/coding/bringup-zephyr/EVAL-GUIDE.md:67-79](../../Development/system/coding/bringup-zephyr/EVAL-GUIDE.md#L67)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u015"></a>
**U015 · METHODENVORSCHLAG · ANNAHME**

Intern vorgeschlagene objektive Primärmetriken: Murmur-Detektierbarkeit, BPM-Fehler gegen Referenz, CPU-Last und Latenz; eine Pilot-Hörstudie n≈5–10 wäre unterstützend.

> **Neuerer Stand (Stand integration, 2026-10-22):** Latenz ist keine gemessene Metrik mehr. Aktuell: Latenz wird nach Gehör geprüft (REQ-05), da kein Zweikanal-Aufnahmeaufbau verfügbar ist (14.10.). – siehe [MVP-Entscheidungen 14.10. (Umfang)](../../Development/system/planning/mvp-decisions-2026-10-14.md#scope).

**Ursprung:** [preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:27-30](../../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md#L27)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u026"></a>
**U026 · EIGENE ENTSCHEIDUNG / ENTWURFSEMPFEHLUNG**

Interne Messentscheidung: keine formale akustische Kettencharakterisierung mit Kalibrieraufbau; „Ton hörbar, Herz-Sounds hörbar“ als ausreichend betrachtet.

**Ursprung:** [preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:47](../../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md#L47)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u013"></a>
**U013 · OFFENE FRAGE · OFFEN**

Q2 fragt, ob sich der Filter für menschliche Murmur-Erkennung vom Filter für BPM-Genauigkeit unterscheidet und beide live nutzbar sind.

**Ursprung:** [preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:22](../../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md#L22)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u019"></a>
**U019 · EIGENE ENTSCHEIDUNG / ENTWURFSEMPFEHLUNG**

Q2-Arbeitsdefinition: Murmur-Filter „besser“ bedeutet höhere Detektionssicherheit/Konfidenz; BPM-Filter „besser“ bedeutet höhere Genauigkeit und weniger Störungen/Ausreißer.

**Ursprung:** [preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:40](../../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md#L40)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u014"></a>
**U014 · OFFENE FRAGE · OFFEN**

Q3 fragt, ob reduzierte Wiedergabegeschwindigkeit die menschliche Murmur-Detektierbarkeit messbar verbessert.

**Ursprung:** [preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:23](../../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md#L23)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.
