# Schreibbaukasten für Nicos Bachelorarbeit

DigitalStethoscope · ESP32/Zephyr · TH Augsburg · Abgabe laut Nico: **11.01.2027**.

Hier liegen geordnete Schreibbausteine aus 350 Informationseinheiten, keine fertige Thesis und keine neue Hardwarevalidierung. **328 aktive Aussagen** werden gezeigt; **22 ältere IDs** bleiben über „ersetzt …“ und den [Einheitenindex](einheitenindex.md) auffindbar. Die 26 Ersatz-Einheiten können dieselbe ältere ID aufteilen. Das unveränderte Verzeichnis `_stage1/` ist der Audit-Trail; sein HANDOFF beschreibt teilweise einen älteren Inventarstand.

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
- **Quellenstand des Audits:** 230 zitierbedürftige Einheiten, 211 davon mit mindestens drei Quellen, 46 unvollständige Quellensets. 328 von 676 Quellenverweisen haben exakt `page: unverified`. Nico muss diese Seiten prüfen.
- **Defekte Links:** ursprünglich 15 Einträge, betroffen 72 Einheiten. Vier verifiziert repariert, elf sichtbar defekt; weiterhin betroffen: 32 Audit-Einheiten. [Korrekturprotokoll](linkkorrekturen.md). Die Pilotstudienquelle enthält zusätzlich einen ungelösten Metadatenkonflikt.
- Build-/Host-/QC-Erfolg belegt keine integrierte physische Funktion. Historische Messungen nur mit Datum und Firmwarestand verwenden.

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
| [Evaluation: Firmware, Funktion und Ressourcen](08-evaluation/07-firmware-funktion-ressourcen.md) | 29 |
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
| EIGENER DOKUMENTIERTER BEFUND; PROJEKTDOKUMENTATION | Repository-Nachweis mit Versions-/Zeitbezug. |
| METHODENVORSCHLAG; METHODE / PRÜFVERFAHREN | Geplantes oder beschriebenes Vorgehen; Durchführung gesondert nachweisen. |
| ANNAHME / OFFEN / WIDERSPRUCH / RISIKO | Noch prüfen oder entscheiden; nicht stillschweigend als erwiesen übernehmen. |
| QUELLENSET UNVOLLSTÄNDIG | Stage-1-Flag; Belegqualität prüfen und Lücke bearbeiten. |
| Seite prüfen | Keine verifizierte Seitenzahl; vorhandener Hinweis ist nur eine Suchhilfe. |
| 🔒 / LINK DEFEKT | Volltextzugang eingeschränkt/ungeklärt oder Link nicht zuverlässig erreichbar. |
| ersetzt U… | Aktueller Schreibbaustein ersetzt diese Audit-ID; Original im Audit nachlesbar. |

`confirmed` wird nicht eigens angezeigt: Es bedeutet im Inventar dokumentiert, nicht unabhängig wahrheitsgeprüft. Auch vorhandene Abschnitts-/Tabellenverweise sind aus Stage 1 übernommen. Alle Aussagen behalten exakt ihre Quellsprache; einzelne englische Firmwareeinheiten sind deshalb weiterhin Englisch.

[Quellenverzeichnis](quellen.md) führt alle 103 Schlüssel mit zitierenden IDs. [quellen.bib](quellen.bib) enthält konservative Minimal-Einträge und kennzeichnet fehlende Metadaten; es ist noch kein abgabefertiges Literaturverzeichnis. [Einheitenindex](einheitenindex.md) führt jede Audit-ID zur Schreibstelle. [Offene Punkte](offene-punkte.md) sind die Arbeitsliste für Entscheidungen, Seiten und Quellenlücken.

## Regenerieren und prüfen

```bash
python thesis-material/_build/build.py
```

Der Generator benötigt nur die Python-Standardbibliothek und keinen Netzwerkzugang. Redaktionelle Änderungen im Generator bzw. in `_build/source-overrides.json` pflegen; erzeugte Dateien werden überschrieben. `_stage1/` wird ausschließlich gelesen. Die Vollständigkeitsprüfung kontrolliert alle 350 IDs in den Kapiteldateien, jede aktive Aussage genau einmal, alle Quellenreferenzen und lokale Linkziele. Ergebnis: [vollstaendigkeit.md](vollstaendigkeit.md); maschinenlesbar: [_build/check.json](_build/check.json).

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
