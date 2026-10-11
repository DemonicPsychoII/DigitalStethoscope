# Linkkorrekturen und Suchprotokoll

[Zum Einstieg](README.md)

Prüfdatum: 05.10.2026. Änderungen liegen ausschließlich in [_build/source-overrides.json](_build/source-overrides.json); Stage 1 bleibt unverändert. Direkte HTTP-Proben: [_build/link-probes.json](_build/link-probes.json). Ein Suchtreffer allein genügt nicht zum Reparieren eines Links. Keine Seitenzahlen wurden neu festgelegt.

## Verifiziert korrigiert

### frequency_response_stethoscopes

Bindestriche im DOI durch Unterstriche ersetzt. PMC-Metadaten nennen den korrigierten DOI; direkter Abruf führt zum Ovid-Verlag mit passendem Titel und Alanazi. Alter DOI: https://doi.org/10.4103/sjmms.sjmms-118-19. Die PMC-URL bleibt als alternative Fundstelle, kann aber eine Browserprüfung verlangen.

**Vorher:** https://pmc.ncbi.nlm.nih.gov/articles/PMC7305673/; DOI: https://doi.org/10.4103/sjmms.sjmms-118-19

**Jetzt:** [Fundstelle](https://doi.org/10.4103/sjmms.sjmms_118_19) · ok — korrigierter DOI am 2026-10-05, HTTP 200 nach Weiterleitung zum Verlag

**Identitätsnachweise:** [Primärquelle 1](https://pmc.ncbi.nlm.nih.gov/articles/PMC7305673/), [Primärquelle 2](https://doi.org/10.4103/sjmms.sjmms_118_19)

### fda_ec13_guidance

Defekten PDF-Link durch offizielle HTML-Fassung desselben Dokuments ersetzt. FDA nennt Ausgabedatum 5. November 1998; das im Ausgangseintrag genannte Jahr 2023 ist nicht das Publikationsjahr. HTML enthält den Leitlinientext. Diese Leitlinie bezieht sich auf EC13-1992, nicht automatisch auf EC13:2002.

**Vorher:** https://www.fda.gov/media/71947/download; DOI: unverified

**Jetzt:** [Fundstelle](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/cardiac-monitor-guidance-including-cardiotachometer-and-rate-alarm-guidance-industry) · broken (HTTP 404) bei Nachprüfung am 2026-10-05 — Sol meldete die HTML-Fassung als geöffnet, ein unabhängiger Abruf lieferte 404; Dokument über FDA-Guidance-Suche manuell finden

**Identitätsnachweise:** [Primärquelle 1](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/cardiac-monitor-guidance-including-cardiotachometer-and-rate-alarm-guidance-industry)

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

## Unrepariert: sichtbar defekt

- [aes_lester_boley_2007](quellen.md#aes_lester_boley_2007): **LINK DEFEKT**. Gleicher AES-Treffer gefunden; direkter Abruf endet mit Timeout bzw. Werkzeugfehler. Kein sicher funktionierender Ersatz.
- [ecm_datasheet_im69d130](quellen.md#ecm_datasheet_im69d130): **LINK DEFEKT**. Hersteller-PDF und älterer dgdl-Link gefunden, beide direkt nicht erreichbar (404). Produktseite ist kein Ersatz für dieselbe Datenblattfassung.
- [fda_ec13_guidance](quellen.md#fda_ec13_guidance): **LINK DEFEKT**. THA-Suche nach Dokumenttitel, FAQ 02.26, Merkblatt und Abschlussarbeitsseite ergab keinen verifiziert erreichbaren identischen Ersatz. Fakultätsportal oder Hochschulzugang verwenden; nicht durch fachfremde Regeln ersetzen.
- [ics40180_datasheet](quellen.md#ics40180_datasheet): **LINK DEFEKT**. Herstellerkandidat DS-000021-v1.22.pdf aus bibliografischem Verweis geprüft; HTTP 404. Keine gesicherte Herstellerfassung erreichbar.
- [pilot_guidelines](quellen.md#pilot_guidelines): **LINK DEFEKT**. Titel gefunden, aber Werkidentität widersprüchlich (Leon 2011 versus Teresi 2022). Korrekturkandidat DOI 10.1097/MLR.0000000000001664; direkter Abruf HTTP 403. Aussagepassung zum PMC-Artikel prüfen, bevor Metadaten ersetzt werden.
- [tha_bachelor_faq](quellen.md#tha_bachelor_faq): **LINK DEFEKT**. THA-Suche nach Dokumenttitel, FAQ 02.26, Merkblatt und Abschlussarbeitsseite ergab keinen verifiziert erreichbaren identischen Ersatz. Fakultätsportal oder Hochschulzugang verwenden; nicht durch fachfremde Regeln ersetzen.
- [tha_bachelor_gestaltung](quellen.md#tha_bachelor_gestaltung): **LINK DEFEKT**. THA-Suche nach Dokumenttitel, FAQ 02.26, Merkblatt und Abschlussarbeitsseite ergab keinen verifiziert erreichbaren identischen Ersatz. Fakultätsportal oder Hochschulzugang verwenden; nicht durch fachfremde Regeln ersetzen.
- [tha_bachelor_maschinenbau](quellen.md#tha_bachelor_maschinenbau): **LINK DEFEKT**. THA-Suche nach Dokumenttitel, FAQ 02.26, Merkblatt und Abschlussarbeitsseite ergab keinen verifiziert erreichbaren identischen Ersatz. Fakultätsportal oder Hochschulzugang verwenden; nicht durch fachfremde Regeln ersetzen.
- [tha_elektrotechnik_duration](quellen.md#tha_elektrotechnik_duration): **LINK DEFEKT**. Passenden offiziellen PDF-Suchtreffer gefunden; direkter Abruf HTTP 404. Kein verifiziert erreichbarer Ersatz.
- [tha_faq_ba](quellen.md#tha_faq_ba): **LINK DEFEKT**. THA-Suche nach Dokumenttitel, FAQ 02.26, Merkblatt und Abschlussarbeitsseite ergab keinen verifiziert erreichbaren identischen Ersatz. Fakultätsportal oder Hochschulzugang verwenden; nicht durch fachfremde Regeln ersetzen.
- [tha_gestaltung_ba](quellen.md#tha_gestaltung_ba): **LINK DEFEKT**. THA-Suche nach Dokumenttitel, FAQ 02.26, Merkblatt und Abschlussarbeitsseite ergab keinen verifiziert erreichbaren identischen Ersatz. Fakultätsportal oder Hochschulzugang verwenden; nicht durch fachfremde Regeln ersetzen.
- [tha_mb_merblatt](quellen.md#tha_mb_merblatt): **LINK DEFEKT**. THA-Suche nach Dokumenttitel, FAQ 02.26, Merkblatt und Abschlussarbeitsseite ergab keinen verifiziert erreichbaren identischen Ersatz. Fakultätsportal oder Hochschulzugang verwenden; nicht durch fachfremde Regeln ersetzen.

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
