# Linkkorrekturen und Suchprotokoll

[Zum Einstieg](README.md)

Prüfdatum: 05.10.2026; spätere Prüfungen tragen ihr eigenes Datum. Änderungen liegen ausschließlich in [_build/source-overrides.json](_build/source-overrides.json) und [_build/stage2-corrections.json](_build/stage2-corrections.json); Stage 1 bleibt unverändert. Direkte HTTP-Proben: [_build/link-probes.json](_build/link-probes.json). Ein Suchtreffer allein genügt nicht zum Reparieren eines Links. Keine Seitenzahlen wurden neu festgelegt.

## Verifiziert korrigiert

### frequency_response_stethoscopes

**Geprüft:** 2026-10-24

Bindestriche im DOI durch Unterstriche ersetzt. PMC-Metadaten nennen den korrigierten DOI; direkter Abruf führt zum Ovid-Verlag mit passendem Titel und Alanazi. Alter DOI: https://doi.org/10.4103/sjmms.sjmms-118-19. Die PMC-URL bleibt als alternative Fundstelle, kann aber eine Browserprüfung verlangen.

**Vorher:** https://pmc.ncbi.nlm.nih.gov/articles/PMC7305673/; DOI: https://doi.org/10.4103/sjmms.sjmms-118-19

**Jetzt:** [Fundstelle](https://doi.org/10.4103/sjmms.sjmms_118_19) · ok — HTTP 200 über korrigierten DOI am 2026-10-24; Titel geprüft

**Identitätsnachweise:** [Primärquelle 1](https://doi.org/10.4103/sjmms.sjmms_118_19)

### ec13

Defekte PDF-Kopie durch offiziellen Katalogeintrag derselben Norm ANSI/AAMI EC13-2002 ersetzt. Titel und Ausgabe stimmen überein; der Katalog bestätigt keine numerischen Klauselinhalte. Originalnorm über Hochschulzugang beschaffen und Klausel prüfen.

**Vorher:** https://mdcpp.com/doc/standard/ANSIAAMIEC13-2002.pdf; DOI: unverified

**Jetzt:** [Fundstelle](https://webstore.ansi.org/standards/aami/ansiaamiec132002) · ok — offizieller ANSI-Katalog am 2026-10-05 geöffnet; Volltext kostenpflichtig

**Identitätsnachweise:** [Primärquelle 1](https://webstore.ansi.org/standards/aami/ansiaamiec132002)

### im68a130_datasheet

Herstellerlink mit dokumentiertem fileId-Parameter ersetzt die defekte URL ohne Parameter. Geöffnetes PDF identifiziert IM68A130V01, Revision 1.10, 2024-01-19 und dieselben 10-Hz-/68-dB(A)-/130-dB-SPL-Spezifikationen. Seitenverweise der Einheiten bleiben unverändert ungeprüft.

**Vorher:** https://www.infineon.com/assets/row/public/documents/24/49/infineon-im68a130-datasheet-en.pdf; DOI: unverified

**Jetzt:** [Fundstelle](https://www.infineon.com/assets/row/public/documents/24/49/infineon-im68a130-datasheet-en.pdf?fileId=8ac78c8c85ecb34701860371623f1204) · ok — Hersteller-PDF am 2026-10-05 geöffnet, 16 Seiten

**Identitätsnachweise:** [Primärquelle 1](https://www.infineon.com/assets/row/public/documents/24/49/infineon-im68a130-datasheet-en.pdf?fileId=8ac78c8c85ecb34701860371623f1204)

### pilot_guidelines

**Geprüft:** 2026-10-24

Titel und PMC-URL gehören zu Teresi et al. (2022); Referenz und DOI des Ausgangseintrags (Leon et al. 2011, 10.1177/0163278711410553) bezeichneten ein anderes Werk, dessen DOI am 2026-10-12 bei doi.org nicht auflöste (HTTP 404). Stage 1 hat den Inhalt am PMC-Volltext geprüft, daher wird das PMC-Werk übernommen. Ausgangsreferenz: Leon, A. C. et al. (2011). Evaluation & the Health Professions, 34(4), 452–476.

**Vorher:** https://pmc.ncbi.nlm.nih.gov/articles/PMC8849521/; DOI: https://doi.org/10.1177/0163278711410553

**Jetzt:** [Fundstelle](https://pmc.ncbi.nlm.nih.gov/articles/PMC8849521/) · ok — HTTP 200 am 2026-10-24; Volltext als PMC-Seite abgerufen

**Identitätsnachweise:** [Primärquelle 1](https://pmc.ncbi.nlm.nih.gov/articles/PMC8849521/)

## Metadaten korrigiert, Link weiterhin defekt

### fda_ec13_guidance

**Geprüft:** 2026-10-24

Defekten PDF-Link durch die von der FDA-Guidance-Suche gelistete HTML-Seite desselben Dokuments ersetzt. FDA nennt dort laut Stage-2-Notiz das Ausgabedatum 5. November 1998; das im Ausgangseintrag genannte Jahr 2023 ist nicht das Publikationsjahr. Dass die HTML-Fassung den vollständigen Leitlinientext enthält, ist nicht unabhängig belegt: Die Öffnung wurde nur gemeldet, ein unabhängiger Abruf am 2026-10-05 und erneut am 2026-10-12 lieferte HTTP 404, und link-probes.json enthält keinen FDA-Abruf. Diese Leitlinie bezieht sich auf EC13-1992, nicht automatisch auf EC13:2002.

**Vorher:** https://www.fda.gov/media/71947/download; DOI: unverified

**Jetzt:** [Fundstelle](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/cardiac-monitor-guidance-including-cardiotachometer-and-rate-alarm-guidance-industry) · broken (HTTP 404) — exakte URL am 2026-10-24 erneut geprüft; Ersatzfundstelle unbestätigt

**Identitätsnachweise:** [Primärquelle 1](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/cardiac-monitor-guidance-including-cardiotachometer-and-rate-alarm-guidance-industry)

### tha_faq_ba

**Geprüft:** 2026-10-24

Die historische URL ist weiterhin nicht erreichbar; keine ungeprüfte Ersatzquelle eingesetzt.

**Vorher:** https://www.tha.de/index.php/Binaries/Binary89415/FAQ-Bachelorarbeit-02.26-clean.pdf; DOI: unverified

**Jetzt:** [Fundstelle](https://www.tha.de/index.php/Binaries/Binary89415/FAQ-Bachelorarbeit-02.26-clean.pdf) · broken (HTTP 404) — exakte URL am 2026-10-24 erneut geprüft; Ersatzfundstelle unbestätigt

**Identitätsnachweise:** [Primärquelle 1](https://www.tha.de/index.php/Binaries/Binary89415/FAQ-Bachelorarbeit-02.26-clean.pdf)

### tha_mb_merblatt

**Geprüft:** 2026-10-24

Die historische URL ist weiterhin nicht erreichbar; keine ungeprüfte Ersatzquelle eingesetzt.

**Vorher:** https://www.tha.de/Binaries/Binary77874/Merkblatt-Bachelorarbeit.pdf; DOI: unverified

**Jetzt:** [Fundstelle](https://www.tha.de/Binaries/Binary77874/Merkblatt-Bachelorarbeit.pdf) · broken (HTTP 404) — exakte URL am 2026-10-24 erneut geprüft; Ersatzfundstelle unbestätigt

**Identitätsnachweise:** [Primärquelle 1](https://www.tha.de/Binaries/Binary77874/Merkblatt-Bachelorarbeit.pdf)

## Metadaten korrigiert, Link war nicht defekt

### goh_chestpiece

**Geprüft:** 2026-10-12

Ausgangs-DOI 10.1109/SENNANO57767.2023 bezeichnet den Tagungsband, nicht den Artikel. Artikel-DOI per Crossref-Datensatz und doi.org-Auflösung geprüft. Bisherige Institutions-URL: https://staffprofiles.bournemouth.ac.uk/display/journal-article/388323.

**Vorher:** https://staffprofiles.bournemouth.ac.uk/display/journal-article/388323; DOI: https://doi.org/10.1109/SENNANO57767.2023

**Jetzt:** [Fundstelle](https://doi.org/10.1109/SENNANO57767.2023.10352567) · ok — DOI am 2026-10-12 aufgelöst (HTTP 302 zu IEEE Xplore 10352567); Crossref nennt Titel, Goh als Erstautor, S. 137–140

**Identitätsnachweise:** [Primärquelle 1](https://api.crossref.org/works/10.1109/SENNANO57767.2023.10352567), [Primärquelle 2](https://ieeexplore.ieee.org/document/10352567/)

### esp_dsp_benchmarks

**Geprüft:** 2026-10-12

Schlüssel kam in round2/C-sources.json und round2/D-sources.json mit unterschiedlichen Metadaten vor; sources-merged.json behielt den allgemeineren D-Eintrag. Spezifischere C-Metadaten (ESP32-S3-Spalte, geprüfte Tabellen) übernommen; dieselbe Espressif-Seite.

**Vorher:** https://docs.espressif.com/projects/esp-dsp/en/latest/esp32/esp-dsp-benchmarks.html; DOI: unverified

**Jetzt:** [Fundstelle](https://docs.espressif.com/projects/esp-dsp/en/latest/esp32/esp-dsp-benchmarks.html) · ok

**Identitätsnachweise:** [Primärquelle 1](https://docs.espressif.com/projects/esp-dsp/en/latest/esp32/esp-dsp-benchmarks.html)

### physionet_challenge_2022

**Geprüft:** 2026-10-24

DOI und Seitenzahlen sind nicht verifiziert; Stage-1-Audit bleibt unverändert.

**Vorher:** https://physionet.org/content/challenge-2022/1.0.0/; DOI: https://doi.org/10.22489/CinC.2022.049

**Jetzt:** [Fundstelle](https://physionet.org/content/challenge-2022/1.0.0/) · ok

**Identitätsnachweise:** [Primärquelle 1](https://physionet.org/content/challenge-2022/1.0.0/)

## Korrekturen an Einheiten und Schlüsseln

- [U098](08-evaluation/07-firmware-funktion-ressourcen.md#u098) (2026-10-12): Ursprungsliste in inventory-merged.json/inventory.json war eine Kopie der U100-Ursprünge; inventory.md nennt die Traceability-JSON, die die Aussage tatsächlich belegt. Ursprüngliche Liste: preThesis/02-entscheidungen/widersprueche.md:1-4; preThesis/02-entscheidungen/open-questions.md:7-11; preThesis/05-hardware/hardware.md:32-34; Development/system/coding/bringup-zephyr/README.md:1-160.
- [C032](03-grundlagen-technisch/08-fhir-tls.md#c032) (2026-10-12): THA-FAQ zur Bachelorarbeit (DMS-Anmeldung, Fristen) belegt keine FHIR-Referenzsemantik. Quellenset bleibt als unvollständig markiert.
- [U046](04-stand-der-technik.md#u046) (2026-10-12): circor_dataset stand zugleich in `sources` und `removed` (Begründung dort: keine Relevanz für Simulatorpreise). Quellenset jetzt leer und weiterhin unvollständig, bis datierte Hersteller-/Händlerpreise geprüft sind.
- [C008](03-grundlagen-technisch/03-i2s-audiopfad.md#c008) (2026-10-24): Die ESP-DSP-API belegt keine I²S-Controller- oder PDM-Konvertierungsmodi. Das Quellenset bleibt unvollständig; die passende ESP-IDF-I²S-Referenz ist noch zu prüfen.
- [C009](03-grundlagen-technisch/03-i2s-audiopfad.md#c009) (2026-10-24): Die ESP-DSP-API belegt keine I²S-Controller- oder PDM-Konvertierungsmodi. Das Quellenset bleibt unvollständig; die passende ESP-IDF-I²S-Referenz ist noch zu prüfen.
- [C011](03-grundlagen-technisch/03-i2s-audiopfad.md#c011) (2026-10-24): Die ESP-DSP-API belegt keine I²S-Controller- oder PDM-Konvertierungsmodi. Das Quellenset bleibt unvollständig; die passende ESP-IDF-I²S-Referenz ist noch zu prüfen.
- [pilot_sample_size](quellen.md#pilot_sample_size) (2026-10-12): aufgeteilt in [pilot_sample_size_sim_lewis](quellen.md#pilot_sample_size_sim_lewis), [pilot_sample_size_hertzog](quellen.md#pilot_sample_size_hertzog). Der Schlüssel bezeichnete in round2/B-sources.json Sim & Lewis (2012), in round2/D-sources.json Hertzog (2008); sources-merged.json behielt nur Hertzog, obwohl die B-Einheiten auf den Sim-&-Lewis-PubMed-Eintrag verlinken. Aufgeteilt nach Herkunftsrunde.

## Unrepariert: sichtbar defekt

- [aes_lester_boley_2007](quellen.md#aes_lester_boley_2007): **LINK DEFEKT**. Gleicher AES-Treffer gefunden; direkter Abruf endet mit Timeout bzw. Werkzeugfehler. Kein sicher funktionierender Ersatz.
- [ecm_datasheet_im69d130](quellen.md#ecm_datasheet_im69d130): **LINK DEFEKT**. Hersteller-PDF und älterer dgdl-Link gefunden, beide direkt nicht erreichbar (404). Produktseite ist kein Ersatz für dieselbe Datenblattfassung.
- [fda_ec13_guidance](quellen.md#fda_ec13_guidance): **LINK DEFEKT**. PDF-Link und gelistete HTML-Seite lieferten bei unabhängigem Abruf am 2026-10-05 und 2026-10-12 HTTP 404; Metadaten sind korrigiert, der Volltext ist nicht unabhängig geprüft. Dokument über die FDA-Guidance-Suche (Titel „Cardiac Monitor Guidance (including Cardiotachometer and Rate Alarm)“) erneut finden; falls dort nicht verfügbar, archivierte Fassung beim Originalanbieter oder über eine Hochschulbibliothek beschaffen.
- [ics40180_datasheet](quellen.md#ics40180_datasheet): **LINK DEFEKT**. Herstellerkandidat DS-000021-v1.22.pdf aus bibliografischem Verweis geprüft; HTTP 404. Keine gesicherte Herstellerfassung erreichbar.
- [tha_bachelor_faq](quellen.md#tha_bachelor_faq): **LINK DEFEKT**. THA-Suche nach Dokumenttitel, FAQ 02.26, Merkblatt und Abschlussarbeitsseite ergab keinen verifiziert erreichbaren identischen Ersatz. Fakultätsportal oder Hochschulzugang verwenden; nicht durch fachfremde Regeln ersetzen.
- [tha_bachelor_gestaltung](quellen.md#tha_bachelor_gestaltung): **LINK DEFEKT**. THA-Suche nach Dokumenttitel, FAQ 02.26, Merkblatt und Abschlussarbeitsseite ergab keinen verifiziert erreichbaren identischen Ersatz. Fakultätsportal oder Hochschulzugang verwenden; nicht durch fachfremde Regeln ersetzen.
- [tha_bachelor_maschinenbau](quellen.md#tha_bachelor_maschinenbau): **LINK DEFEKT**. THA-Suche nach Dokumenttitel, FAQ 02.26, Merkblatt und Abschlussarbeitsseite ergab keinen verifiziert erreichbaren identischen Ersatz. Fakultätsportal oder Hochschulzugang verwenden; nicht durch fachfremde Regeln ersetzen.
- [tha_elektrotechnik_duration](quellen.md#tha_elektrotechnik_duration): **LINK DEFEKT**. Passenden offiziellen PDF-Suchtreffer gefunden; direkter Abruf HTTP 404. Kein verifiziert erreichbarer Ersatz.
- [tha_faq_ba](quellen.md#tha_faq_ba): **LINK DEFEKT**. THA-Suche nach Dokumenttitel, FAQ 02.26, Merkblatt und Abschlussarbeitsseite ergab keinen verifiziert erreichbaren identischen Ersatz. Fakultätsportal oder Hochschulzugang verwenden; nicht durch fachfremde Regeln ersetzen.
- [tha_gestaltung_ba](quellen.md#tha_gestaltung_ba): **LINK DEFEKT**. THA-Suche nach Dokumenttitel, FAQ 02.26, Merkblatt und Abschlussarbeitsseite ergab keinen verifiziert erreichbaren identischen Ersatz. Fakultätsportal oder Hochschulzugang verwenden; nicht durch fachfremde Regeln ersetzen.
- [tha_mb_merblatt](quellen.md#tha_mb_merblatt): **LINK DEFEKT**. THA-Suche nach Dokumenttitel, FAQ 02.26, Merkblatt und Abschlussarbeitsseite ergab keinen verifiziert erreichbaren identischen Ersatz. Fakultätsportal oder Hochschulzugang verwenden; nicht durch fachfremde Regeln ersetzen.

Updated by GPT-6.1-Sol on behalf of Nico running in codex.
