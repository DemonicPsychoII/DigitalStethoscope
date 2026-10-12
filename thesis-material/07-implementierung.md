# Implementierung

[Zum Einstieg](README.md) · [Offene Punkte](offene-punkte.md)

Dokumentierten Softwarestand mit Versions- und Verdrahtungsbezug beschreiben.

**7 aktive Einheiten.** Schreibreihenfolge: Definition → Mechanismus → Werte → Folgerung. Die Aussagen sind Material, kein fertiger Fließtext.

## Schreibbausteine

### Mechanismen und Zusammenhänge

<a id="c031"></a>
**C031 · LITERATURFAKT / REGEL**

Die im Bericht gezeigte JSON-Beispielressource verwendet `status: final`, die Kategorie `vital-signs`, ein LOINC-Herzfrequenz-`code`, `Patient/123` als `subject`, `effectiveDateTime` und ein `valueQuantity`-Objekt.

**Ursprung:** [preThesis/03-recherche/R11-fhir-tls.md:51-92](../preThesis/03-recherche/R11-fhir-tls.md#L51)
**Belege:** [HL7 · fhir_r4_vitals_official](https://hl7.org/fhir/R4/observation-vitalsigns.html) — Fundstelle: Vital Signs Profile; Heart rate row (aus Stage 1; am Original prüfen); [Regenstrief Institute · loinc_8867_official](https://loinc.org/8867-4) — Fundstelle: Term details (aus Stage 1; am Original prüfen); [HL7 · fhir_observation_r4](https://hl7.org/fhir/R4/observation.html) — Seite prüfen

<a id="u104"></a>
**U104 · PROJEKTDOKUMENTATION**

Firmware README states BPM analysis uses newly captured samples at the original sample rate; lung mode is live Raw listening without BPM, replay or FHIR.

**Ursprung:** [Development/system/coding/bringup-zephyr/README.md:43-44](../Development/system/coding/bringup-zephyr/README.md#L43)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u107"></a>
**U107 · PROJEKTDOKUMENTATION**

Firmware README states configuration and tokens remain in RAM, FHIR sending requires valid recent BPM and a low-priority worker issues TLS PUT to HAPI-FHIR; server readback is used as evidence.

> **Überholt (Stand integration, 2026-10-12):** Beschreibt das Sendeverhalten der Bring-up-Firmware (gültiger aktueller BPM, Low-Priority-Worker). Das MVP-Zielverhalten ist anders festgelegt. Aktuell: Nur eine abgeschlossene Messsitzung (≥15 s, Aggregation nach Stop) ist sendefähig; Netzwerkarbeit nur im Idle unter exklusivem Netzwerk-Lease; ungültiger BPM sendet keinen Zahlenwert, sondern eine getrennte Fehlermeldung; Patient aus `Device.patient` mit Prüfung vor dem `PUT`. Vorgeschlagen: NET merkt sich dabei `Device.meta.versionId` und liest das Device nach dem Observation-Readback erneut; jede Versionsänderung ergibt „Unverified“ mit normalem Fehler statt „Sent“. FHIR bietet keine atomare Bedingung über `Device` und `Observation`, eine KIS-Änderung zwischen Prüfung und `PUT` bleibt daher ein Restrisiko, das nur sichtbar gemacht wird. – siehe [MVP-Entscheidungen 11.10.](../Development/system/planning/mvp-decisions-2026-10-11.md#confirmed-scope-and-behavior), [MVP-Entscheidungen 12.10.](../Development/system/planning/mvp-decisions-2026-10-12.md#proposed-behavior).

**Ursprung:** [Development/system/coding/bringup-zephyr/README.md:227-262](../Development/system/coding/bringup-zephyr/README.md#L227)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

### Werte und dokumentierte Befunde

<a id="u101"></a>
**U101 · EIGENER ZIELWERT / VORLÄUFIGER VORSCHLAG**

Firmware README documents 16 kHz, stereo 32-bit I²S, 128-frame blocks (8 ms), two silent TX priming blocks (16 ms), and DMA slabs in internal SRAM.

**Ursprung:** [Development/system/coding/bringup-zephyr/README.md:15-17](../Development/system/coding/bringup-zephyr/README.md#L15)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u103"></a>
**U103 · EIGENER ZIELWERT / VORLÄUFIGER VORSCHLAG · ANNAHME**

Firmware README documents BPM update once per second, provisional 30–200 BPM range and quality gating.

**Ursprung:** [Development/system/coding/bringup-zephyr/README.md:22-23](../Development/system/coding/bringup-zephyr/README.md#L22)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u102"></a>
**U102 · EIGENER ZIELWERT / VORLÄUFIGER VORSCHLAG · ANNAHME**

Firmware README documents initial listening-filter candidates: Raw, Murmur 40–800 Hz, BPM 25–150 Hz, using second-order Butterworth high-pass/low-pass sections and 20 ms exponential crossfades; cutoffs are explicitly engineering candidates, not optimal validated values.

**Ursprung:** [Development/system/coding/bringup-zephyr/README.md:18-21](../Development/system/coding/bringup-zephyr/README.md#L18)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u088"></a>
**U088 · EIGENER DOKUMENTIERTER BEFUND**

README-Update 2026-09-16 meldet bestätigte Eval-Verdrahtung; historischer Hardwareplan listet nur einen standardmäßig verdrahteten physischen Schalter; Wiedergabegeschwindigkeit sei per Touch/Serial erreichbar gewesen; optionaler zweiter Overlay-Schalter separat unverifiziert.

**Ursprung:** [preThesis/05-hardware/hardware.md:32-34](../preThesis/05-hardware/hardware.md#L32)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.
