# Systemarchitektur

[Zum Einstieg](README.md) · [Offene Punkte](offene-punkte.md)

Bruststück und Hardware → Signalpfade → Bedienung → Tasks/Speicher → Netzwerk.

**39 aktive Einheiten.** Schreibreihenfolge: Definition → Mechanismus → Werte → Folgerung. Die Aussagen sind Material, kein fertiger Fließtext.

## Bruststück, Mikrofon und Kopplung

### Begriffe und Definitionen

<a id="b039"></a>
**B039 · LITERATURFAKT / REGEL**

R07 unterscheidet direkte Mikrofonankopplung, kurzen Schlauchstummel, Membran-/Kavitätsankopplung, Mikrofon in Schlauchkammer, Kontaktaufnehmer und Hybridaufbau; Varianten unterscheiden sich hinsichtlich Schlauchverlusten, Körperschallkopplung und Komplexität.

**Ursprung:** [preThesis/03-recherche/R07-bruststueck-mems.md:67-105](../preThesis/03-recherche/R07-bruststueck-mems.md#L67)
**Belege:** [MEMS and ECM Sensor Technologies for Cardiorespirato 2024 · mems_cardiorespiratory_review](https://arxiv.org/abs/2406.12432) — Seite prüfen; [Acoustic Methods for Pulmonary Diagnosis · pulmonary_acoustic_methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC6874908/) — Seite prüfen; [Delgado-Trejos, E., Quiceno-Manrique, A 2009 · digital_auscultation_murmur](https://link.springer.com/article/10.1007/s10439-008-9611-z) — Fundstelle: Introduction, heart cycle/murmur description (web text lines 71–73; 85). (aus Stage 1; am Original prüfen)

### Werte und dokumentierte Befunde

<a id="u076"></a>
**U076 · EIGENER ZIELWERT / VORLÄUFIGER VORSCHLAG**

Bestandsliste: PCM5102A I²S-DAC zur Kopfhörerwiedergabe und INMP441 I²S-MEMS-Mikrofon zur Aufnahme.

**Ursprung:** [preThesis/05-hardware/hardware.md:10-11](../preThesis/05-hardware/hardware.md#L10)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

### Folgerungen, Entwurfsentscheidungen und Grenzen

<a id="b037"></a>
**B037 · METHODE / PRÜFVERFAHREN**

Bei Bottom-Port-Mikrofonen muss die Mikrofonöffnung der Leiterplatte mit dem akustischen Kanal fluchten; R07 nennt wenige Millimeter Abstand und möglichst gute Abdichtung als Konstruktionsziele.

**Ursprung:** [preThesis/03-recherche/R07-bruststueck-mems.md:38-65](../preThesis/03-recherche/R07-bruststueck-mems.md#L38)
**Belege:** [Alanazi, A., Atcherson, S., Franklin, C., & Bryan, M 2020 · frequency_response_stethoscopes](https://doi.org/10.4103/sjmms.sjmms_118_19) — Seite prüfen; [Weiss, D 2019 · invitro_stethoscopes](https://pmc.ncbi.nlm.nih.gov/articles/PMC6339642/) — Seite prüfen; [Goh, R 2023 · goh_chestpiece](https://doi.org/10.1109/SENNANO57767.2023.10352567) — Fundstelle: pp. 137–140 (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig

<a id="u023"></a>
**U023 · EIGENE ENTSCHEIDUNG / ENTWURFSEMPFEHLUNG**

Die Membran des Bruststücks soll erhalten bleiben; Kopplung Mikrofon an Hohlraum-/Schlauchöffnung ermöglicht laut interner Planung zwei durch Drehen vergleichbare Bauformen.

**Ursprung:** [preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:44](../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md#L44)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="b038"></a>
**B038 · METHODE / PRÜFVERFAHREN**

Für Mikrofonmontage nennt R07 weiche Silikon-/TPU-Dichtungen sowie mechanische Entkopplung gegen Griff-, Reibungs- und Körperschall.

**Ursprung:** [preThesis/03-recherche/R07-bruststueck-mems.md:56-65](../preThesis/03-recherche/R07-bruststueck-mems.md#L56)
**Belege:** [Alanazi, A., Atcherson, S., Franklin, C., & Bryan, M 2020 · frequency_response_stethoscopes](https://doi.org/10.4103/sjmms.sjmms_118_19) — Seite prüfen; [Weiss, D 2019 · invitro_stethoscopes](https://pmc.ncbi.nlm.nih.gov/articles/PMC6339642/) — Seite prüfen; [Goh, R 2023 · goh_chestpiece](https://doi.org/10.1109/SENNANO57767.2023.10352567) — Fundstelle: pp. 137–140 (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig

<a id="u012"></a>
**U012 · OFFENE FRAGE · OFFEN**

Q1 fragt, ob die Kopplung MEMS-Mikrofon plus analoges Bruststück S3/S4-/Murmur-Anteile gegenüber dem analogen Hörpfad dämpft und inwieweit Filterauslegung dies kompensiert.

**Ursprung:** [preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:21](../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md#L21)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u060"></a>
**U060 · RISIKO / EINORDNUNG · QUELLENSET UNVOLLSTÄNDIG**

R07 bezeichnet Leckage als kritischen Baufehler mit starker Dämpfung bei 20–40 Hz; ein in der Literatur genannter Aufbau mit 5-cm-Schlauch, 6-mm-Innendurchmesser und Kondensatormikrofon sei unter 60 Hz nicht optimal.

**Ursprung:** [preThesis/02-entscheidungen/open-questions.md:184-186](../preThesis/02-entscheidungen/open-questions.md#L184)
**Belege:** [Maharjan, S 2023 · digital_stethoscope_characterization](https://pmc.ncbi.nlm.nih.gov/articles/PMC10753976/) — Seite prüfen (Hinweis: Relevant article section/table not verified in full text during this pass.); [Alanazi, A., Atcherson, S., Franklin, C., & Bryan, M 2020 · frequency_response_stethoscopes](https://doi.org/10.4103/sjmms.sjmms_118_19) — Seite prüfen (Hinweis: Relevant article section/table not verified in full text during this pass.); [Weiss, D 2019 · invitro_stethoscopes](https://pmc.ncbi.nlm.nih.gov/articles/PMC6339642/) — Seite prüfen (Hinweis: Relevant article section/table not verified in full text during this pass.)

<a id="b036"></a>
**B036 · EIGENE ENTSCHEIDUNG / ENTWURFSEMPFEHLUNG · ANNAHME · ersetzt U058**

R07 empfiehlt, die Bruststückmembran beizubehalten und das Mikrofon in einer kleinen, abgedichteten Kammer unmittelbar hinter der Membran mit kurzem akustischem Weg zu platzieren.

**Ursprung:** [preThesis/03-recherche/R07-bruststueck-mems.md:22-55](../preThesis/03-recherche/R07-bruststueck-mems.md#L22)
**Belege:** [Alanazi, A., Atcherson, S., Franklin, C., & Bryan, M 2020 · frequency_response_stethoscopes](https://doi.org/10.4103/sjmms.sjmms_118_19) — Seite prüfen; [Weiss, D 2019 · invitro_stethoscopes](https://pmc.ncbi.nlm.nih.gov/articles/PMC6339642/) — Seite prüfen; [Goh, R 2023 · goh_chestpiece](https://doi.org/10.1109/SENNANO57767.2023.10352567) — Fundstelle: pp. 137–140 (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig

## Audiohardware und getrennte Signalpfade

### Mechanismen und Zusammenhänge

<a id="u086"></a>
**U086 · PROJEKTDOKUMENTATION**

README dokumentiert INMP441 als Audioeingang und PCM5102A als externen Audioausgang; die Verkabelung/Pinbelegung wird im README als Eval-Träger-Rev A geführt.

**Ursprung:** [Development/system/coding/bringup-zephyr/README.md:1-160](../Development/system/coding/bringup-zephyr/README.md#L1)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

### Werte und dokumentierte Befunde

<a id="c018"></a>
**C018 · EIGENER ZIELWERT / VORLÄUFIGER VORSCHLAG · ANNAHME**

Abgeleitet aus den Benchmarkzahlen schätzt R10 drei parallele 256-Tap-FIR-Filter bei 8 kHz auf rund 10,4 Mio. Zyklen/s beziehungsweise 4,3 % eines 240-MHz-Kerns.

**Ursprung:** [preThesis/03-recherche/R10-esp32-plattform.md:245-256,367-371](../preThesis/03-recherche/R10-esp32-plattform.md#L245)
**Belege:** [Espressif Systems · esp_dsp_benchmarks](https://docs.espressif.com/projects/esp-dsp/en/latest/esp32/esp-dsp-benchmarks.html) — Fundstelle: FIR Filters row; ESP32S3 O2 (aus Stage 1; am Original prüfen); [Espressif Systems · esp_s3_datasheet](https://documentation.espressif.com/esp32-s3_datasheet_en.pdf) — Seite prüfen; [Espressif Systems · esp_dsp_api](https://docs.espressif.com/projects/esp-dsp/en/latest/esp32/esp-dsp-apis.html) — Seite prüfen

### Folgerungen, Entwurfsentscheidungen und Grenzen

<a id="u079"></a>
**U079 · EIGENE ENTSCHEIDUNG / ENTWURFSEMPFEHLUNG**

Hardwaredokumentation hält fest, dass INMP441s untere Grenzfrequenz die nutzbare Bandbreite begrenzt und Bauteilauswahl abgeschlossen ist.

**Ursprung:** [preThesis/05-hardware/hardware.md:20-21](../preThesis/05-hardware/hardware.md#L20)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u024"></a>
**U024 · EIGENE ENTSCHEIDUNG / ENTWURFSEMPFEHLUNG**

INMP441 ist gesetzt und bereits als Breakout vorhanden; laut interner Festlegung wird seine untere Grenzfrequenz als Randbedingung dokumentiert statt die Bauteilauswahl neu aufzurollen.

**Ursprung:** [preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:45](../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md#L45)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u025"></a>
**U025 · EIGENE ENTSCHEIDUNG / ENTWURFSEMPFEHLUNG**

PCM5102A ist als I²S-DAC eingeplant.

**Ursprung:** [preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:46](../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md#L46)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="a065"></a>
**A065 · EIGENE ENTSCHEIDUNG / ENTWURFSEMPFEHLUNG · ANNAHME**

R04 empfiehlt WSOLA als einfache Echtzeitoption für das Projekt; die Eignung für Herzschall bleibt zu prüfen.

**Ursprung:** [preThesis/03-recherche/R04-time-stretch.md:63-80](../preThesis/03-recherche/R04-time-stretch.md#L63)
**Belege:** [Driedger, J., & Müller, M 2016 · tsm_review](https://www.mdpi.com/2076-3417/6/2/57) — Seite prüfen (übernommene Angabe: Abstract and review overview; article section/page unverified); [Roelands, M., & Verhelst, W 1993 · wsola_roelands](https://www.isca-archive.org/eurospeech_1993/roelands93_eurospeech.html) — Fundstelle: Abstract and bibliographic record (aus Stage 1; am Original prüfen); [Prusa, Z 2022 · phase_vocoder](https://ltfat.org/notes/ltfatnote050.pdf) — Seite prüfen (übernommene Angabe: Abstract and Introduction (PDF; document pages unverified))

<a id="a077"></a>
**A077 · EIGENE ENTSCHEIDUNG / ENTWURFSEMPFEHLUNG · ANNAHME**

R04 empfiehlt WSOLA als Hauptverfahren, 0,75× als Standard und 0,5× als optionalen Modus mit erhöhtem Artefaktrisiko.

**Ursprung:** [preThesis/03-recherche/R04-time-stretch.md:281-290](../preThesis/03-recherche/R04-time-stretch.md#L281)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u062"></a>
**U062 · RISIKO / EINORDNUNG · QUELLENSET UNVOLLSTÄNDIG**

R07 nennt beim IM69D130 ein einfach erhältliches Shield2Go mit ADAU7002, bei Knowles-Typen Flexboard/Muskie-Evalsystem und mögliche Liefer-/Lötprobleme; SPH0645 mit 45 Hz wird für 20 Hz als ungeeignet bewertet.

**Ursprung:** [preThesis/02-entscheidungen/open-questions.md:206-209](../preThesis/02-entscheidungen/open-questions.md#L206)
**Belege:** [Infineon Technologies · mic_datasheet_infineon](https://www.infineon.com/part/IM69D130) — Seite prüfen (Hinweis: Relevant article section/table not verified in full text during this pass.); [Knowles · mic_datasheet_knowles](https://www.knowles.com/docs/default-source/default-document-library/mic-selection-guide-r5.pdf) — Seite prüfen (Hinweis: Relevant article section/table not verified in full text during this pass.); [Exploring Microphone Technologies for Digital Auscul 2023 · mems_microphones_review](https://www.mdpi.com/2072-666X/14/11/2092) — Seite prüfen (Hinweis: Relevant article section/table not verified in full text during this pass.)

## Bedienung, Pins und Verdrahtung

### Mechanismen und Zusammenhänge

<a id="u105"></a>
**U105 · PROJEKTDOKUMENTATION**

Firmware README separates display, audio and optional network work into threads; input events do not wait for full-screen redraw, and failed GPIO event delivery retries.

**Ursprung:** [Development/system/coding/bringup-zephyr/README.md:48-49](../Development/system/coding/bringup-zephyr/README.md#L48)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u085"></a>
**U085 · PROJEKTDOKUMENTATION**

README beschreibt die Bring-up-Firmware als ESP32-S3-Zephyr-Anwendung mit Audio-, DSP-, FHIR/Netzwerk-, Display-/Touch-, GPIO- und SD-Speichermodulen; konkrete Datenflussdetails sind der README-Architektursektion zu entnehmen.

**Ursprung:** [Development/system/coding/bringup-zephyr/README.md:1-120](../Development/system/coding/bringup-zephyr/README.md#L1)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

### Werte und dokumentierte Befunde

<a id="u077"></a>
**U077 · EIGENER ZIELWERT / VORLÄUFIGER VORSCHLAG**

Bestandsliste: 10-kΩ-Potentiometer am ADC für Lautstärke; Fasizi ILI9341 240×320 TFT mit Touch über SPI.

**Ursprung:** [preThesis/05-hardware/hardware.md:13-14](../preThesis/05-hardware/hardware.md#L13)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u106"></a>
**U106 · EIGENER ZIELWERT / VORLÄUFIGER VORSCHLAG**

Firmware README gives default GPIO mapping for the filter switch as positions Raw/Murmur/BPM on GPIO 18/21/38; mapping is explicitly tied to evaluation carrier wiring.

**Ursprung:** [Development/system/coding/bringup-zephyr/README.md:64-83](../Development/system/coding/bringup-zephyr/README.md#L64)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u078"></a>
**U078 · EIGENER ZIELWERT / VORLÄUFIGER VORSCHLAG**

Hardwaredokumentation führt zwei SP3T-THT-Schalter auf: Filterwahl Raw/Murmur/BPM und Wiedergabegeschwindigkeit 1,0×/0,75×/0,5×.

**Ursprung:** [preThesis/05-hardware/hardware.md:15-16](../preThesis/05-hardware/hardware.md#L15)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u087"></a>
**U087 · EIGENER DOKUMENTIERTER BEFUND**

README-Update 2026-10-02 meldet Rev A-Verdrahtung für Geschwindigkeits-Schalter (GPIO2/39/47) und LCD-SD am geteilten SPI2 (CS GPIO48); Standard-Firmware bildet beides ab.

**Ursprung:** [Development/system/coding/bringup-zephyr/README.md:1-160](../Development/system/coding/bringup-zephyr/README.md#L1)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

### Folgerungen, Entwurfsentscheidungen und Grenzen

<a id="u032"></a>
**U032 · EIGENE ENTSCHEIDUNG / ENTWURFSEMPFEHLUNG**

Bedienvorschlag: Potentiometer für Lautstärke, Schalter für Wiedergabegeschwindigkeit und Filter; optional Touchdisplay zur Konfiguration.

> **Überholt (Stand integration, 2026-10-12):** Das MVP hat weder Display noch Touch; Geschwindigkeitsschalter/Speed-Presets sind optional. Aktuell: Bedienung über Taster (Start/Stop, Quittierung, langer Druck ≥2 s im Idle öffnet das Hotspot-Portal), Filterschalter und Potentiometer; Patientenzuordnung und WLAN-Einrichtung über eine Handy-Browserseite im Geräte-Hotspot. – siehe [MVP-Entscheidungen 12.10.](../Development/system/planning/mvp-decisions-2026-10-12.md#confirmed-decisions), [MVP-Entscheidungen 11.10.](../Development/system/planning/mvp-decisions-2026-10-11.md#confirmed-scope-and-behavior).

**Ursprung:** [preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:53](../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md#L53)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u080"></a>
**U080 · OFFENE FRAGE · OFFEN**

I²S-Peripherie- und Pinzuordnung für INMP441 und PCM5102A war in der Hardwareplanung noch festzulegen.

**Ursprung:** [preThesis/05-hardware/hardware.md:24](../preThesis/05-hardware/hardware.md#L24)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u040"></a>
**U040 · EIGENE ENTSCHEIDUNG / ENTWURFSEMPFEHLUNG · OFFEN**

W2 wird als unkritisch eingestuft, da beide Bauteile identisch seien; Zuordnung soll vor finalem Aufbau verbindlich festgeschrieben werden; Bring-up prüft bewusst einen Schalter.

**Ursprung:** [preThesis/02-entscheidungen/widersprueche.md:44-48](../preThesis/02-entscheidungen/widersprueche.md#L44)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u039"></a>
**U039 · WIDERSPRUCH · WIDERSPRUCH**

W2: Nummerierung der beiden SP3T-Schalter weicht ab: intern/open-questions ordnen Schalter 1 Geschwindigkeit und Schalter 2 Filter zu, Hardwareliste ordnet Schalter 1 Filter und Schalter 2 Geschwindigkeit zu.

**Ursprung:** [preThesis/02-entscheidungen/widersprueche.md:34-42](../preThesis/02-entscheidungen/widersprueche.md#L34)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.
**Vor Verwendung klären:** [Widersprüche](offene-punkte.md#widersprueche).

## Plattform, Tasks und Ressourcen

### Werte und dokumentierte Befunde

<a id="u075"></a>
**U075 · EIGENER ZIELWERT / VORLÄUFIGER VORSCHLAG**

Bestandsliste: ESP32-S3 N16R8 DevKitC-1 mit 16 MB Flash und 8 MB PSRAM.

**Ursprung:** [preThesis/05-hardware/hardware.md:8-9](../preThesis/05-hardware/hardware.md#L8)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="c027"></a>
**C027 · EIGENER ZIELWERT / VORLÄUFIGER VORSCHLAG · ANNAHME · QUELLENSET UNVOLLSTÄNDIG**

R10 nennt 10–40-ms-DMA-Blöcke und zwei bis vier DMA-Puffer lediglich als Startwerte; die endgültige Audiolatenz und Robustheit sind vom gewählten Blockformat und Scheduling abhängig.

> **Überholt (Stand integration, 2026-10-12):** Die 10–40-ms-DMA-Startwerte sind durch die gewählte Blockgröße ersetzt. Aktuell: 128 Frames bei 16 kHz (8 ms) je Block; Vorschlag ≤4 ms kritische Ausführung pro Block, Scheduling- und Wartezeiten getrennt messen. – siehe [Latenzbudgets 11.10.](../Development/system/planning/mvp-decisions-2026-10-11.md#latency-research-and-proposed-budgets), [Entscheidungsregister D10](../Development/system/planning/implementation-readiness.md#decision-register).

**Ursprung:** [preThesis/03-recherche/R10-esp32-plattform.md:334-344](../preThesis/03-recherche/R10-esp32-plattform.md#L334)
**Belege:** [Espressif Systems · esp_i2s_s3](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/i2s.html) — Fundstelle: Data Transport (aus Stage 1; am Original prüfen); [Espressif Systems · esp_s3_datasheet](https://documentation.espressif.com/esp32-s3_datasheet_en.pdf) — Seite prüfen

### Folgerungen, Entwurfsentscheidungen und Grenzen

<a id="u035"></a>
**U035 · EIGENE ENTSCHEIDUNG / ENTWURFSEMPFEHLUNG · OFFEN**

Interne Programmiersprachen-/Framework-Auswahl: C/ESP-IDF oder C/Zephyr nach Hands-on-Phase; Kriterium ist schnellste tragfähige Echtzeit-Audio-Umsetzung.

> **Überholt (Stand integration, 2026-10-12):** Die Auswahl zwischen C/ESP-IDF und C/Zephyr ist getroffen. Aktuell: C/Zephyr für das MVP; ein Frameworkwechsel würde Gerätekonfiguration, Synchronisation, Netzwerk und Verifikation erneut erfordern. – siehe [Framework- und Transportbewertung](../Development/system/planning/framework-and-transport-evaluation.md#recommendation-for-the-next-discussion).

**Ursprung:** [preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:62](../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md#L62)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u028"></a>
**U028 · EIGENE ENTSCHEIDUNG / ENTWURFSEMPFEHLUNG · OFFEN**

Plattformentscheidung intern zunächst offen: ESP-IDF (C/FreeRTOS) Favorit; Zephyr-Probeläufe vor Thesis-Start, finale Entscheidung zu Thesis-Beginn.

> **Überholt (Stand integration, 2026-10-12):** Die Plattformentscheidung ist nicht mehr offen; die ESP-IDF-Präferenz der internen Fassung ist durch S04 ersetzt. Aktuell: Zephyr wird für das MVP beibehalten, solange die On-Target-Prüfungen keinen konkreten Blocker zeigen. – siehe [Framework- und Transportbewertung](../Development/system/planning/framework-and-transport-evaluation.md#recommendation-for-the-next-discussion), [Quellenregister S04/S06](../Development/system/spec/product-scope.md#source-register-and-precedence).

**Ursprung:** [preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:49](../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md#L49)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

## Netzwerk- und Übertragungspfad

### Folgerungen, Entwurfsentscheidungen und Grenzen

<a id="c043"></a>
**C043 · METHODENVORSCHLAG · ANNAHME**

Der in R11 vorgeschlagene Übertragungspfad lautet: BPM-Observation mit Zeitstempel erzeugen, Uhrzeit synchronisieren, verifiziertes HTTPS aufbauen, FHIR-JSON per POST senden, HTTP-/FHIR-Antworten prüfen und transiente Fehler mit Backoff erneut versuchen.

> **Überholt (Stand integration, 2026-10-12):** Übertragung per `POST` mit Backoff-Wiederholung ist nicht der Projektpfad. Aktuell: `PUT /Observation/{id}` mit stabiler Ressourcen-ID und anschließendem Readback, ohne Wiederholungswarteschlange; vor dem `PUT` wird `Device.patient` erneut gelesen und `Device.meta.versionId` festgehalten. Vorgeschlagen: Nach dem Observation-Readback wird das Device erneut gelesen; jede Versionsänderung ergibt „Unverified“ mit normalem Fehler statt „Sent“ (fängt auch A→B→A-Umzuordnungen, kann falsch-positiv sein). Ohne atomare Bedingung über `Device` und `Observation` bleibt eine Umzuordnung zwischen Prüfung und `PUT` ein sichtbar gemachtes Restrisiko. – siehe [Design: Delivery](../Development/system/design/interfaces-and-behavior.md#delivery-clock-and-configuration), [MVP-Entscheidungen 12.10.](../Development/system/planning/mvp-decisions-2026-10-12.md#proposed-behavior).

**Ursprung:** [preThesis/03-recherche/R11-fhir-tls.md:220-233](../preThesis/03-recherche/R11-fhir-tls.md#L220)
**Belege:** [HL7 · fhir_r4_vitals_official](https://hl7.org/fhir/R4/observation-vitalsigns.html) — Fundstelle: Vital Signs Profile (aus Stage 1; am Original prüfen); [Espressif Systems · esp_tls_s3](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/protocols/esp_tls.html) — Fundstelle: TLS Server Verification (aus Stage 1; am Original prüfen); [Espressif Systems · esp_tls_faq](https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/protocols/esp-tls.html) — Fundstelle: Question on certificate expiry (aus Stage 1; am Original prüfen)

<a id="u030"></a>
**U030 · EIGENE ANFORDERUNG**

FHIR-Ziel intern: Observation (Vital Signs, LOINC 8867-4, UCUM /min), SNTP vor TLS-Handshake und gepinntes Root-CA; Authentisierung darf vereinfacht werden, BPM-JSON-Erzeugung und Versand sollen enthalten sein.

**Ursprung:** [preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:51](../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md#L51)
**Belege:** [HL7 · fhir_r4_vitals](https://www.hl7.org/fhir/R4/observation-vitalsigns.html) — Fundstelle: Vital Signs table, Heart rate row (aus Stage 1; am Original prüfen); [Regenstrief Institute · loinc_8867](https://loinc.org/8867-4/) — Seite prüfen (Hinweis: Relevant article section/table not verified in full text during this pass.); [HL7 · fhir_hr_example](https://www.hl7.org/fhir/R4/observation-example-heart-rate.json.html) — Seite prüfen (Hinweis: Relevant article section/table not verified in full text during this pass.); [HL7 · fhir_tls_security](https://www.hl7.org/fhir/R4/secpriv-module.html) — Seite prüfen (Hinweis: Relevant article section/table not verified in full text during this pass.)

<a id="u081"></a>
**U081 · RISIKO / EINORDNUNG**

PSRAM ersetzt nicht DMA-fähigen internen SRAM; TLS-Handshake-Heap wird als kritischer Engpass vermerkt.

**Ursprung:** [preThesis/05-hardware/hardware.md:26](../preThesis/05-hardware/hardware.md#L26)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="c025"></a>
**C025 · EIGENE ENTSCHEIDUNG / ENTWURFSEMPFEHLUNG · ANNAHME · ersetzt U066**

R10 bewertet das Rechenbudget als voraussichtlich ausreichend, sofern Filter blockweise mit DMA und ESP32-S3-optimiertem esp-dsp laufen, BPM auf einer heruntergesampelten Hüllkurve bestimmt wird, TLS/FHIR außerhalb der hochpriorisierten Audio-Task bleibt und ein externer I²S-DAC oder -Verstärker verwendet wird.

**Ursprung:** [preThesis/03-recherche/R10-esp32-plattform.md:20-57,363-395](../preThesis/03-recherche/R10-esp32-plattform.md#L20)
**Belege:** [Espressif Systems · esp_dsp_benchmarks](https://docs.espressif.com/projects/esp-dsp/en/latest/esp32/esp-dsp-benchmarks.html) — Fundstelle: FIR Filters; IIR Filters (aus Stage 1; am Original prüfen); [Espressif Systems · esp_i2s_s3](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/i2s.html) — Fundstelle: Overview of All Modes; Data Transport (aus Stage 1; am Original prüfen); [Espressif Systems · esp_tls_faq](https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/protocols/esp-tls.html) — Fundstelle: Question on handshake memory (aus Stage 1; am Original prüfen)

<a id="c013"></a>
**C013 · EIGENE ENTSCHEIDUNG / ENTWURFSEMPFEHLUNG · ANNAHME · ersetzt U065**

R10 bewertet ESP-IDF mit FreeRTOS als risikoärmere Basis für die konkrete Kombination aus ESP32-S3-PDM/I²S, DMA, Wi-Fi, TLS und Espressif-DSP-Bibliothek; Zephyr wird als grundsätzlich nutzbar, aber integrationsintensiver eingeordnet.

> **Überholt (Stand integration, 2026-10-12):** Die R10-Empfehlung für ESP-IDF ist historischer Recherchekontext, keine Projektentscheidung. Aktuell: Zephyr bleibt Plattform des MVP; ESP-IDF-Komponenten sind keine Drop-in-Bibliotheken unter Zephyr. – siehe [Framework- und Transportbewertung](../Development/system/planning/framework-and-transport-evaluation.md#recommendation-for-the-next-discussion), [Quellenregister S06](../Development/system/spec/product-scope.md#source-register-and-precedence).

**Ursprung:** [preThesis/03-recherche/R10-esp32-plattform.md:20-57,363-395](../preThesis/03-recherche/R10-esp32-plattform.md#L20)
**Belege:** [Espressif Systems · esp_i2s_s3](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/i2s.html) — Fundstelle: Overview of All Modes; Application Example (aus Stage 1; am Original prüfen); [Zephyr Project · zephyr_s3_board](https://docs.zephyrproject.org/latest/boards/espressif/esp32s3_devkitc/doc/index.html) — Fundstelle: Board Support Package; Supported Features (aus Stage 1; am Original prüfen); [Zephyr Project · zephyr_i2s_binding](https://docs.zephyrproject.org/latest/build/dts/api/bindings/i2s/espressif,esp32-i2s.html) — Fundstelle: Binding properties (aus Stage 1; am Original prüfen)

<a id="c028"></a>
**C028 · RISIKO / EINORDNUNG · ANNAHME · ersetzt U067**

R10 bewertet TLS-Handshake/CA-Prüfung und zusammenhängenden internen Heap, DMA-/Taskplanung unter WLAN-Verkehr sowie optionales hochwertiges Time-Stretching als wahrscheinliche Engpässe; nicht die einfachen IIR-/FIR-Pfade.

**Ursprung:** [preThesis/03-recherche/R10-esp32-plattform.md:363-395](../preThesis/03-recherche/R10-esp32-plattform.md#L363)
**Belege:** [Espressif Systems · esp_tls_faq](https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/protocols/esp-tls.html) — Fundstelle: Question on handshake memory (aus Stage 1; am Original prüfen); [Espressif Systems · esp_dsp_benchmarks](https://docs.espressif.com/projects/esp-dsp/en/latest/esp32/esp-dsp-benchmarks.html) — Fundstelle: FIR Filters; IIR Filters (aus Stage 1; am Original prüfen); [Espressif Systems · esp_i2s_s3](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/i2s.html) — Fundstelle: Data Transport (aus Stage 1; am Original prüfen)

<a id="c026"></a>
**C026 · EIGENE ENTSCHEIDUNG / ENTWURFSEMPFEHLUNG · ANNAHME · ersetzt U029**

R10 empfiehlt, TLS/FHIR nicht synchron in der zeitkritischen Audio-Task auszuführen, Audio- und Netzwerkpfad getrennt zu planen und Heap-/Stack-Wasserstände sowie Pufferlaufzeiten im Prototyp zu beobachten.

**Ursprung:** [preThesis/03-recherche/R10-esp32-plattform.md:311-359](../preThesis/03-recherche/R10-esp32-plattform.md#L311)
**Belege:** [Espressif Systems · esp_tls_faq](https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/protocols/esp-tls.html) — Fundstelle: Question on TLS handshake memory (aus Stage 1; am Original prüfen); [Espressif Systems · esp_i2s_s3](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/i2s.html) — Fundstelle: Data Transport (aus Stage 1; am Original prüfen); [Espressif Systems · esp_mbedtls_s3](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/protocols/mbedtls.html) — Seite prüfen

<a id="c036"></a>
**C036 · EIGENE ENTSCHEIDUNG / ENTWURFSEMPFEHLUNG · ANNAHME · ersetzt U069**

R11 beschreibt ein einzelnes, kontrolliertes Root-CA-Zertifikat als speichersparendere Wahl bei einem bekannten Server und ein CA-Bundle als flexibler für unterschiedliche öffentliche Zertifizierungsstellen; konkrete Flash-/RAM-Unterschiede sind in diesem Bericht nicht quantifiziert.

**Ursprung:** [preThesis/03-recherche/R11-fhir-tls.md:128-158](../preThesis/03-recherche/R11-fhir-tls.md#L128)
**Belege:** [Espressif Systems · esp_tls_s3](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/protocols/esp_tls.html) — Fundstelle: TLS Server Verification (aus Stage 1; am Original prüfen); [Espressif Systems · esp_mbedtls_s3](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/protocols/mbedtls.html) — Seite prüfen; [Espressif Systems · esp_tls_faq](https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/protocols/esp-tls.html) — Fundstelle: Question on handshake memory (aus Stage 1; am Original prüfen)

<a id="c037"></a>
**C037 · EIGENE ANFORDERUNG**

Wenn mbedTLS die X.509-Gültigkeitszeiträume validiert, benötigt es eine zutreffende Systemzeit; R11 schlägt deshalb Netzwerkverbindung und SNTP-Zeitsynchronisierung vor dem TLS-Aufbau vor.

**Ursprung:** [preThesis/03-recherche/R11-fhir-tls.md:160-184](../preThesis/03-recherche/R11-fhir-tls.md#L160)
**Weiterer Kapitelbezug:** Ethik/Datenschutz/Regulatorik
**Belege:** [Espressif Systems · esp_tls_s3](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/protocols/esp_tls.html) — Fundstelle: TLS Server Verification (aus Stage 1; am Original prüfen); [Espressif Systems · esp_mbedtls_s3](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/protocols/mbedtls.html) — Seite prüfen; [Espressif Systems · esp_tls_faq](https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/protocols/esp-tls.html) — Fundstelle: Questions on certificate verification and expiry (aus Stage 1; am Original prüfen)
