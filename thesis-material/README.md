# Schreibbaukasten für Nicos Bachelorarbeit

DigitalStethoscope · ESP32/Zephyr · TH Augsburg · Abgabe laut Nico: **11.01.2027**.

Hier liegen geordnete Schreibbausteine aus 349 Informationseinheiten, keine fertige Thesis und keine neue Hardwarevalidierung. **327 aktive Aussagen** werden gezeigt; **22 ältere IDs** bleiben über „ersetzt …“ und den [Einheitenindex](einheitenindex.md) auffindbar. Die 26 Ersatz-Einheiten können dieselbe ältere ID aufteilen. Das unveränderte Verzeichnis `_stage1/` ist der Audit-Trail; sein HANDOFF beschreibt teilweise einen älteren Inventarstand.

## Jetzt mit Grundlagen anfangen

1. [Medizinische Grundlagen](02-grundlagen-medizinisch.md): Herzzyklus, S1/S2, Murmurs und Frequenzbereiche erklären.
2. [Akustik/Bruststück](03-grundlagen-technisch/01-akustik-bruststueck.md), [MEMS](03-grundlagen-technisch/02-mems-mikrofone.md) und [I²S](03-grundlagen-technisch/03-i2s-audiopfad.md): den Weg vom Herzschall zu digitalen Samples beschreiben.
3. [DSP/Filter](03-grundlagen-technisch/04-dsp-filter.md), [BPM](03-grundlagen-technisch/05-bpm-erkennung.md) und [Time-Stretch](03-grundlagen-technisch/06-time-stretch.md): Verfahren und Grenzen erläutern.
4. [Embedded/RTOS](03-grundlagen-technisch/07-embedded-rtos-esp32.md), [FHIR/TLS](03-grundlagen-technisch/08-fhir-tls.md) und [Latenz](03-grundlagen-technisch/09-latenz.md) ergänzen.

Pro Absatz eine Kernaussage wählen, Originalbeleg öffnen und die genaue Fundstelle prüfen. Zuerst allgemeine Begriffe/Mechanismen schreiben; Bauteilwahl und eigene Grenzwerte anschließend in Anforderungen/Architektur begründen. Ungeklärte Zahlen als Arbeitsnotiz stehen lassen. Die Reihenfolge innerhalb der Dateien lautet Definition → Mechanismus → Werte → Folgerung, innerhalb großer Kapitel zusätzlich nach Thema.

**Materiallücken:** Die technischen Grundlagen im Inventar sind keine vollständige Lehrbuchdarstellung. Für I²S-Taktsignale/Framing, Abtasttheorem/Quantisierung, FIR/IIR-Grundprinzipien, MEMS-Wandlungsprinzip, RTOS-Scheduling und die BPM-Schätzpipeline sind zusätzliche passende Primär- oder Lehrbuchbelege nötig. Diese Lücken verhindern das Schreiben der bereits belegten Abschnitte nicht. Historische ESP-IDF-Empfehlungen von der aktuellen Zephyr-Implementierung trennen.

## Vor Zahlenübernahme beachten

- **Widersprüche:** W1 (Q1/AP 2.2 versus gestrichene Kettenmessung), W2 (Schalterzuordnung), CirCor 5.272/5.282, Helmholtz-Modell und Knowles-LFRO. Sie stehen zuerst in [offene-punkte.md](offene-punkte.md#widersprueche).
- **Eigene Zielwerte:** 40–800 Hz / 25–150 Hz, <30 ms bzw. ≤10/≤5 ms und BPM-Akzeptanzgrenzen sind vorläufige Entwicklungsentscheidungen, keine allgemeingültigen Literaturgrenzen.
- **Quellenstand des Audits:** 230 zitierbedürftige Einheiten, 207 davon mit mindestens drei Quellen, 49 unvollständige Quellensets. 323 von 670 Quellenverweisen haben exakt `page: unverified`. Nico muss diese Seiten prüfen.
- **Defekte Links:** ursprünglich 15 Einträge, betroffen 72 Einheiten. 4 verifiziert repariert, 11 sichtbar defekt, 3 weitere Einträge nur in den Metadaten korrigiert; weiterhin betroffen: 27 Audit-Einheiten. [Korrekturprotokoll](linkkorrekturen.md). Der Leon-/Teresi-Metadatenkonflikt der Pilotstudienquelle ist in Stage 2 aufgelöst.
- Build-/Host-/QC-Erfolg belegt keine integrierte physische Funktion. Historische Messungen nur mit Datum und Firmwarestand verwenden.
- **Stand integration 2026-10-22:** W1 ist im Projekt entschieden: Abgabefassung ohne Kettenmessung (D09, 14.10.); die Abstimmung mit dem Betreuer ist offen. W2 betrifft den im MVP nicht geforderten Geschwindigkeitsschalter und die Trägerplatine. Latenz- und BPM-Ziele gelten seit 14.10. (REQ-05, REQ-06). Details: [Abgleich mit integration](#abgleich-mit-integration).

## Abgleich mit integration

Die Bausteine entstanden vor neueren Projektentscheidungen auf `integration` (Stand 2026-10-22, Commit 638633b). Überholte Aussagen bleiben unverändert stehen; direkt darunter steht ein Hinweis „Überholt“ bzw. „Neuerer Stand“ mit Link auf das maßgebliche Dokument. Die Hinweise kommen aus [_build/integration-notes.json](_build/integration-notes.json) und überstehen jede Regenerierung. Nicht eindeutig entschiedene Punkte stehen unter [Offene Punkte](offene-punkte.md#integration-abgleich).

| ID | Hinweis | Was sich geändert hat |
|---|---|---|
| [U002](05-anforderungen.md#u002) | Überholt | Verlangsamte Wiedergabe gehört nicht zum MVP-Umfang (Feedback 2026-10-07, Entscheidung 2026-10-11). Seit 14.10. sind alle optionalen Anforderungen vorerst entfernt, darunter verlangsamte Wiedergabe. |
| [U005](08-evaluation/01-fragen-kriterien.md#u005) | Überholt | Reduzierte Wiedergabegeschwindigkeit ist kein Prüfgegenstand mehr. Seit 14.10. gilt eine Anforderung nur, wenn Nico sie am Gerät mit verfügbarer Ausrüstung eindeutig prüfen kann. |
| [U020](05-anforderungen.md#u020) | Überholt | WSOLA-Stufen 1,0×/0,75×/0,5× sind kein MVP-Bestandteil. Seit 14.10. ist Replay auch keine optionale Anforderung mehr. |
| [U032](06-systemarchitektur.md#u032) | Überholt | Das MVP hat weder Display noch Touch; Geschwindigkeitsschalter und Replay sind seit 14.10. keine Anforderung mehr. Die Patientenauswahl über die Handyseite (12.10.) ist am 15.10. entfallen. |
| [U031](05-anforderungen.md#u031) | Überholt | Der Lungenmodus gehört nicht zum MVP. Seit 14.10. sind optionale Anforderungen vorerst entfernt, darunter Lung. |
| [U028](06-systemarchitektur.md#u028) | Überholt | Die Plattformentscheidung ist nicht mehr offen; die ESP-IDF-Präferenz der internen Fassung ist durch S04 ersetzt. |
| [U035](06-systemarchitektur.md#u035) | Überholt | Die Auswahl zwischen C/ESP-IDF und C/Zephyr ist getroffen. |
| [C013](06-systemarchitektur.md#c013) | Überholt | Die R10-Empfehlung für ESP-IDF ist historischer Recherchekontext, keine Projektentscheidung. |
| [U085](06-systemarchitektur.md#u085) | Neuerer Stand | Beschreibt die Bring-up-Firmware. Die neue Firmware hat eine andere Modulstruktur (13.10.). |
| [U105](06-systemarchitektur.md#u105) | Neuerer Stand | Beschreibt die Thread-Aufteilung der Bring-up-Firmware mit Display. |
| [U104](07-implementierung.md#u104) | Neuerer Stand | Der Lungenmodus der Bring-up-Firmware ist kein MVP-Bestandteil. |
| [U082](11-formales-projektmanagement.md#u082) | Überholt | Eine Verstärkerstufe hinter dem PCM5102A gehört nicht mehr zum Projekt. |
| [U033](11-formales-projektmanagement.md#u033) | Überholt | Die Abgabe Ende Januar ist ersetzt. |
| [C001](03-grundlagen-technisch/09-latenz.md#c001) | Überholt | ≤10 ms bzw. ≤5 ms End-to-End sind nicht das Projektziel; die R09-Aussage einer universellen 10–15-ms-Grenze ist laut Literaturprüfung vom 11.10. nur eingeschränkt belastbar. |
| [C007](03-grundlagen-technisch/09-latenz.md#c007) | Neuerer Stand | Eine Messung der End-to-End-Latenz ist im Projekt nicht vorgesehen. |
| [U015](08-evaluation/01-fragen-kriterien.md#u015) | Neuerer Stand | Latenz ist keine gemessene Metrik mehr. |
| [U108](08-evaluation/07-firmware-funktion-ressourcen.md#u108) | Neuerer Stand | Eine getrennte Messung der akustisch-elektrischen End-to-End-Latenz ist im Projekt nicht vorgesehen. |
| [C027](06-systemarchitektur.md#c027) | Überholt | Die 10–40-ms-DMA-Startwerte sind durch die gewählte Blockgröße ersetzt. |
| [U110](08-evaluation/01-fragen-kriterien.md#u110) | Überholt | Mehrere EVAL-GUIDE-Zielwerte sind ersetzt: gemessene Live-Latenz <30 ms, BPM „≥90 % gültige Fenster“, Tonhöhe ±2 % bei 440 Hz und Eingabereaktion ≤35 ms. |
| [U111](08-evaluation/01-fragen-kriterien.md#u111) | Überholt | Die Dauerlaufprüfung von ≥10 Minuten ist ersetzt; ≥25 % Stack-/Heap-Reserve bleibt. |
| [A056](08-evaluation/04-bpm-validierung.md#a056) | Überholt | Das R03-Entwicklungsziel (MAE ≤5 bpm, MAPE ≤10 %, ≥90 % der Fenster) und der Sitzungs-MAE-Vorschlag vom 11.10. sind nicht der Projektweg. |
| [U018](08-evaluation/04-bpm-validierung.md#u018) | Neuerer Stand | Die BPM-Referenz für die Abnahme ist festgelegt. |
| [A040](08-evaluation/02-datensaetze-referenz.md#a040) | Überholt | Synchron aufgezeichnetes EKG als primäre BPM-Referenz ist nicht der Abnahmeweg des Projekts; die R03-Empfehlung bleibt Recherchekontext. |
| [A045](08-evaluation/02-datensaetze-referenz.md#a045) | Überholt | Synchrone PCG-/EKG-Aufnahme mit R-Zacken-Detektion ist nicht der Abnahmeweg des Projekts. |
| [U107](07-implementierung.md#u107) | Überholt | Beschreibt die Bring-up-Firmware (gültiger aktueller BPM, Low-Priority-Worker, `PUT`, Server-Readback, Konfiguration nur im RAM). Das MVP-Zielverhalten ist anders festgelegt; Patientenprüfung, `PUT` und Readback vom 12.10. sind am 15.10. entfallen. |
| [U126](08-evaluation/07-firmware-funktion-ressourcen.md#u126) | Überholt | „Retry is explicit“ und der Readback-Abgleich gelten für das MVP nicht mehr; ein Patient steht nur bei serverseitiger Verknüpfung in der Observation. |
| [C039](09-ethik-datenschutz-regulatorik.md#c039) | Neuerer Stand | Die Wiederholung ist seit 14.10. festgelegt; Zertifikats-/Hostnamenprüfung und kein HTTP-Fallback gelten weiter. |
| [C043](06-systemarchitektur.md#c043) | Neuerer Stand | Der Pfad ist konkretisiert: bedingtes Anlegen statt einfachem `POST`, feste Wiederholungsgrenze statt Backoff. Der `PUT`-/Readback-Pfad vom 12.10. ist am 15.10. entfallen. |
| [C029](03-grundlagen-technisch/08-fhir-tls.md#c029) | Überholt | Nur `subject` als feste Angabe ist überholt; Vital-Signs-Kategorie, LOINC 8867-4 und UCUM `/min` gelten weiter. |
| [C031](07-implementierung.md#c031) | Neuerer Stand | Das Beispiel mit festem `Patient/123` als `subject` entspricht nicht dem Projektpfad. |
| [U068](03-grundlagen-technisch/08-fhir-tls.md#u068) | Neuerer Stand | Die Patient-Referenz ist im Projekt nicht immer vorhanden. |
| [U037](10-diskussion-ausblick.md#u037) | Neuerer Stand | Der Entwurf folgt der Abgabefassung (S05): Komponenteneignung über Datenblätter/Literatur und funktionaler Audiotest, keine gemessene Aussage zur Übertragungskette. D09 ist seit 14.10. geschlossen. |
| [U038](10-diskussion-ausblick.md#u038) | Neuerer Stand | Von den drei W1-Optionen gilt die Herausnahme der Kettenmessung (S05); D09 ist seit 14.10. geschlossen. |

## Kapitelkarte

Die Zahlen zählen aktive Aussagen, nicht ersetzte IDs, Querverweise oder Quellen.

| Kapitel / Schreibdatei | Aktive Einheiten |
|---|---:|
| [Einleitung und Motivation](01-einleitung.md) | 2 |
| [Medizinische Grundlagen](02-grundlagen-medizinisch.md) | 6 |
| [Akustik und Bruststück](03-grundlagen-technisch/01-akustik-bruststueck.md) | 11 |
| [MEMS-Mikrofone](03-grundlagen-technisch/02-mems-mikrofone.md) | 10 |
| [I²S und digitaler Audiopfad](03-grundlagen-technisch/03-i2s-audiopfad.md) | 5 |
| [DSP und Filter](03-grundlagen-technisch/04-dsp-filter.md) | 7 |
| [BPM-Erkennung](03-grundlagen-technisch/05-bpm-erkennung.md) | 1 |
| [Time-Stretch und verlangsamte Wiedergabe](03-grundlagen-technisch/06-time-stretch.md) | 14 |
| [Embedded-System, RTOS und ESP32](03-grundlagen-technisch/07-embedded-rtos-esp32.md) | 1 |
| [FHIR und TLS](03-grundlagen-technisch/08-fhir-tls.md) | 9 |
| [Latenz und Echtzeit](03-grundlagen-technisch/09-latenz.md) | 3 |
| [Stand der Technik](04-stand-der-technik.md) | 14 |
| [Anforderungen und Abgrenzung](05-anforderungen.md) | 9 |
| [Systemarchitektur](06-systemarchitektur.md) | 39 |
| [Implementierung](07-implementierung.md) | 7 |
| [Evaluation: Fragen und Annahmekriterien](08-evaluation/01-fragen-kriterien.md) | 16 |
| [Evaluation: Datensätze und Referenzen](08-evaluation/02-datensaetze-referenz.md) | 19 |
| [Evaluation: Filtervergleich und Statistik](08-evaluation/03-filtervergleich-statistik.md) | 16 |
| [Evaluation: BPM-Validierung](08-evaluation/04-bpm-validierung.md) | 16 |
| [Evaluation: Explorative Hörstudie](08-evaluation/05-hoerstudie.md) | 33 |
| [Evaluation: Akustische Übertragungskette](08-evaluation/06-akustische-kette.md) | 18 |
| [Evaluation: Firmware, Funktion und Ressourcen](08-evaluation/07-firmware-funktion-ressourcen.md) | 28 |
| [Ethik, Datenschutz und Regulatorik](09-ethik-datenschutz-regulatorik.md) | 17 |
| [Diskussion und Ausblick](10-diskussion-ausblick.md) | 8 |
| [Formales und Projektmanagement](11-formales-projektmanagement.md) | 18 |

## Marker und Nutzung

| Marker | Bedeutung beim Schreiben |
|---|---|
| LITERATURFAKT / REGEL; LITERATUR- / HERSTELLERWERT | Externe Aussage; Originalbelege und Geltungsbereich prüfen. |
| LITERATURMESSUNG / BENCHMARK | Ergebnis fremder Messung, kein Messwert dieses Prototyps. |
| EIGENE ENTSCHEIDUNG / ENTWURFSEMPFEHLUNG | Projektentscheidung oder Rechercheempfehlung; Status der tatsächlichen Übernahme prüfen. |
| EIGENER ZIELWERT / VORLÄUFIGER VORSCHLAG; EIGENE ANFORDERUNG | Eigener Sollwert/Umfang; Literatur kann begründen, macht daraus aber keine Normvorgabe. |
| PROJEKTDOKUMENTATION / BESTANDSWERT | Dokumentierter Preis, Bestand oder Verdrahtungswert; kein eigener Sollwert. |
| EIGENER DOKUMENTIERTER BEFUND; PROJEKTDOKUMENTATION | Repository-Nachweis mit Versions-/Zeitbezug. |
| METHODENVORSCHLAG; METHODE / PRÜFVERFAHREN | Geplantes oder beschriebenes Vorgehen; Durchführung gesondert nachweisen. |
| ANNAHME / OFFEN / WIDERSPRUCH / RISIKO | Noch prüfen oder entscheiden; nicht stillschweigend als erwiesen übernehmen. |
| QUELLENSET UNVOLLSTÄNDIG | Stage-1-Flag; Belegqualität prüfen und Lücke bearbeiten. |
| Seite prüfen | Keine verifizierte Seitenzahl; vorhandener Hinweis ist nur eine Suchhilfe. |
| 🔒 / LINK DEFEKT | Volltextzugang eingeschränkt/ungeklärt oder Link nicht zuverlässig erreichbar. |
| ersetzt U… | Aktueller Schreibbaustein ersetzt diese Audit-ID; Original im Audit nachlesbar. |

`confirmed` wird nicht eigens angezeigt: Es bedeutet im Inventar dokumentiert, nicht unabhängig wahrheitsgeprüft. Auch vorhandene Abschnitts-/Tabellenverweise sind aus Stage 1 übernommen. Alle Aussagen behalten exakt ihre Quellsprache; einzelne englische Firmwareeinheiten sind deshalb weiterhin Englisch.

[Quellenverzeichnis](quellen.md) führt alle 105 Audit-Schlüssel mit zitierenden IDs sowie 50 Zusatzquellen außerhalb des Audits (Projektentscheidungen, LED-Recherche) ohne Audit-IDs. [quellen.bib](quellen.bib) enthält konservative Minimal-Einträge und kennzeichnet fehlende Metadaten; es ist noch kein abgabefertiges Literaturverzeichnis. [Einheitenindex](einheitenindex.md) führt jede Audit-ID zur Schreibstelle. [Offene Punkte](offene-punkte.md) sind die Arbeitsliste für Entscheidungen, Seiten und Quellenlücken.

## Regenerieren und prüfen

```bash
python thesis-material/_build/build.py
```

Der Generator benötigt nur die Python-Standardbibliothek und keinen Netzwerkzugang. Redaktionelle Änderungen im Generator bzw. in `_build/source-overrides.json` pflegen, Quellen außerhalb des Audits in `_build/supplemental-sources.json`; erzeugte Dateien werden überschrieben. `_stage1/` wird ausschließlich gelesen. Die Vollständigkeitsprüfung kontrolliert alle 349 IDs in den Kapiteldateien, jede aktive Aussage genau einmal, alle Quellenreferenzen und lokale Linkziele. Ergebnis: [vollstaendigkeit.md](vollstaendigkeit.md); maschinenlesbar: [_build/check.json](_build/check.json).

Updated by GPT-6.1-Sol on behalf of Nico running in codex.
