# Implementierung

[Zum Einstieg](README.md) · [Offene Punkte](offene-punkte.md)

Dokumentierten Softwarestand mit Versions- und Verdrahtungsbezug beschreiben.

**7 aktive Einheiten.** Schreibreihenfolge: Definition → Mechanismus → Werte → Folgerung. Die Aussagen sind Material, kein fertiger Fließtext.

## Schreibbausteine

### Mechanismen und Zusammenhänge

<a id="c031"></a>
**C031 · LITERATURFAKT / REGEL**

Die im Bericht gezeigte JSON-Beispielressource verwendet `status: final`, die Kategorie `vital-signs`, ein LOINC-Herzfrequenz-`code`, `Patient/123` als `subject`, `effectiveDateTime` und ein `valueQuantity`-Objekt.

> **Neuerer Stand (Stand integration, 2026-10-22):** Das Beispiel mit festem `Patient/123` als `subject` entspricht nicht dem Projektpfad. Aktuell: `device = Device/{id}`; `subject` nur bei serverseitiger Patientenverknüpfung (16.10.); `effectiveDateTime` = Ende des Messintervalls (D08). – siehe [MVP-Entscheidungen 16.10.](../Development/system/planning/mvp-decisions-2026-10-16.md#confirmed-decisions), [MVP-Entscheidungen 15.10.](../Development/system/planning/mvp-decisions-2026-10-15.md#resulting-behavior).

**Ursprung:** [preThesis/03-recherche/R11-fhir-tls.md:51-92](../preThesis/03-recherche/R11-fhir-tls.md#L51)
**Belege:** [HL7 · fhir_r4_vitals_official](https://hl7.org/fhir/R4/observation-vitalsigns.html) — Fundstelle: Vital Signs Profile; Heart rate row (aus Stage 1; am Original prüfen); [Regenstrief Institute · loinc_8867_official](https://loinc.org/8867-4) — Fundstelle: Term details (aus Stage 1; am Original prüfen); [HL7 · fhir_observation_r4](https://hl7.org/fhir/R4/observation.html) — Seite prüfen

<a id="u104"></a>
**U104 · PROJEKTDOKUMENTATION**

Firmware README states BPM analysis uses newly captured samples at the original sample rate; lung mode is live Raw listening without BPM, replay or FHIR.

> **Neuerer Stand (Stand integration, 2026-10-22):** Der Lungenmodus der Bring-up-Firmware ist kein MVP-Bestandteil. Aktuell: MVP nur Herz; Lung ist optional und braucht das Display (14.10.). – siehe [MVP-Entscheidungen 14.10. (Umfang)](../Development/system/planning/mvp-decisions-2026-10-14.md#scope).

**Ursprung:** [Development/system/coding/bringup-zephyr/README.md:43-44](https://github.com/DemonicPsychoII/DigitalStethoscope/blob/23c1ea492270b897532896179e35f873eee823be/Development/system/coding/bringup-zephyr/README.md?plain=1#L43) (**Herkunft verschoben:** seit b2c3dde zu einem kurzen Einstiegs-README verdichtet; die Zeilenangaben gelten nur für die zitierte Fassung. Link zeigt diese historische Fassung. Aktuell: [Bring-up-README](../preThesis/06-bringup-zephyr/README.md))
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u107"></a>
**U107 · PROJEKTDOKUMENTATION**

Firmware README states configuration and tokens remain in RAM, FHIR sending requires valid recent BPM and a low-priority worker issues TLS PUT to HAPI-FHIR; server readback is used as evidence.

> **Überholt (Stand integration, 2026-10-22):** Beschreibt die Bring-up-Firmware (gültiger aktueller BPM, Low-Priority-Worker, `PUT`, Server-Readback, Konfiguration nur im RAM). Das MVP-Zielverhalten ist anders festgelegt; Patientenprüfung, `PUT` und Readback vom 12.10. sind am 15.10. entfallen. Aktuell: Nur eine abgeschlossene Messsitzung (≥15 s) ist sendefähig; kein Netzwerkverkehr während der Messung. Nach Stop `POST /Observation` mit `If-None-Exist` und Verweis auf das vom Server vergebene Device; `201`/`200` gilt als Quittung, kein Readback (15.10.). `subject` nur, wenn der Server einen Patienten mit dem Device verknüpft hat (16.10.). Fehlgeschlagene Sendung: bis zu 3 Wiederholungen innerhalb 10 s (14.10.). Ungültiger BPM: Fehler an den Server und Anzeige am Gerät (14.10.). WLAN-Zugangsdaten und Device-ID liegen persistent im Flash (Zephyr-Settings-Partition, 15.10.); gespeichert wird erst nach erfolgreichem Beitritt mit Adresse (19.10.). – siehe [MVP-Entscheidungen 15.10.](../Development/system/planning/mvp-decisions-2026-10-15.md#resulting-behavior), [MVP-Entscheidungen 16.10.](../Development/system/planning/mvp-decisions-2026-10-16.md#confirmed-decisions), [MVP-Entscheidungen 14.10.](../Development/system/planning/mvp-decisions-2026-10-14.md#behavior), [MVP-Entscheidungen 19.10.](../Development/system/planning/mvp-decisions-2026-10-19.md#current-rules-and-amendments).

**Ursprung:** [Development/system/coding/bringup-zephyr/README.md:227-262](https://github.com/DemonicPsychoII/DigitalStethoscope/blob/23c1ea492270b897532896179e35f873eee823be/Development/system/coding/bringup-zephyr/README.md?plain=1#L227) (**Herkunft verschoben:** seit b2c3dde zu einem kurzen Einstiegs-README verdichtet; die Zeilenangaben gelten nur für die zitierte Fassung. Link zeigt diese historische Fassung. Aktuell: [Bring-up-README](../preThesis/06-bringup-zephyr/README.md))
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

### Werte und dokumentierte Befunde

<a id="u101"></a>
**U101 · PROJEKTDOKUMENTATION / BESTANDSWERT**

Firmware README documents 16 kHz, stereo 32-bit I²S, 128-frame blocks (8 ms), two silent TX priming blocks (16 ms), and DMA slabs in internal SRAM.

**Ursprung:** [Development/system/coding/bringup-zephyr/README.md:15-17](https://github.com/DemonicPsychoII/DigitalStethoscope/blob/23c1ea492270b897532896179e35f873eee823be/Development/system/coding/bringup-zephyr/README.md?plain=1#L15) (**Herkunft verschoben:** seit b2c3dde zu einem kurzen Einstiegs-README verdichtet; die Zeilenangaben gelten nur für die zitierte Fassung. Link zeigt diese historische Fassung. Aktuell: [Bring-up-README](../preThesis/06-bringup-zephyr/README.md))
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u103"></a>
**U103 · PROJEKTDOKUMENTATION / BESTANDSWERT · ANNAHME**

Firmware README documents BPM update once per second, provisional 30–200 BPM range and quality gating.

**Ursprung:** [Development/system/coding/bringup-zephyr/README.md:22-23](https://github.com/DemonicPsychoII/DigitalStethoscope/blob/23c1ea492270b897532896179e35f873eee823be/Development/system/coding/bringup-zephyr/README.md?plain=1#L22) (**Herkunft verschoben:** seit b2c3dde zu einem kurzen Einstiegs-README verdichtet; die Zeilenangaben gelten nur für die zitierte Fassung. Link zeigt diese historische Fassung. Aktuell: [Bring-up-README](../preThesis/06-bringup-zephyr/README.md))
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u102"></a>
**U102 · PROJEKTDOKUMENTATION / BESTANDSWERT · ANNAHME**

Firmware README documents initial listening-filter candidates: Raw, Murmur 40–800 Hz, BPM 25–150 Hz, using second-order Butterworth high-pass/low-pass sections and 20 ms exponential crossfades; cutoffs are explicitly engineering candidates, not optimal validated values.

**Ursprung:** [Development/system/coding/bringup-zephyr/README.md:18-21](https://github.com/DemonicPsychoII/DigitalStethoscope/blob/23c1ea492270b897532896179e35f873eee823be/Development/system/coding/bringup-zephyr/README.md?plain=1#L18) (**Herkunft verschoben:** seit b2c3dde zu einem kurzen Einstiegs-README verdichtet; die Zeilenangaben gelten nur für die zitierte Fassung. Link zeigt diese historische Fassung. Aktuell: [Bring-up-README](../preThesis/06-bringup-zephyr/README.md))
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u088"></a>
**U088 · EIGENER DOKUMENTIERTER BEFUND**

README-Update 2026-09-16 meldet bestätigte Eval-Verdrahtung; historischer Hardwareplan listet nur einen standardmäßig verdrahteten physischen Schalter; Wiedergabegeschwindigkeit sei per Touch/Serial erreichbar gewesen; optionaler zweiter Overlay-Schalter separat unverifiziert.

**Ursprung:** [preThesis/05-hardware/hardware.md:32-34](../preThesis/05-hardware/hardware.md#L32)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.
