# Widersprüche und überholte Aussagen zwischen den Projektdokumenten

> **Stand: 2026-10-07**, abgeglichen mit `integration` (`23c1ea4`, 2026-10-06).
> Register für Quellenkonflikte; aktuelle Entscheidungen und offene Nachweise stehen in
> [open-questions.md](open-questions.md). „Aufgelöst“ bedeutet hier: Die aktuelle Quelle
> legt die Behandlung fest. Es bedeutet keine Freigabe offener Detailparameter oder Gerätetests.
> Ältere Aufgabenbeschreibungen und Rechercheberichte bleiben historische Quellen.

## W1 — Akustische Kette und frühere Q1/AP-2.2-Forderung

**Status: für den aktuellen Scope aufgelöst; D09 bestätigt die Behandlung als Entwurf,
Scope-Reconciliation bleibt vor Baseline-Freigabe zu bestätigen.**

Die ältere [Aufgabenbeschreibung](../01-aufgabenbeschreibung/Aufgabenbeschreibung.md) und
[interne Fassung](../01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md) fordern Q1,
Bewertungsgrundlage (a) und AP 2.2 zur messtechnischen Charakterisierung der akustischen Kette.
Die damaligen Nutzerannotationen lehnen einen Kalibrieraufbau ab.

Die [aktuelle Abgabefassung](../01-aufgabenbeschreibung/Aufgabenbeschreibung-Abgabe.md)
schließt die messtechnische Charakterisierung ausdrücklich aus. Komponenten werden anhand
von Datenblättern und Fachliteratur beurteilt. Der [Produktscope](../../Development/system/spec/product-scope.md)
folgt dieser Quelle S05. R08 ist damit Hintergrundwissen, kein verpflichtendes Messverfahren.
Die frühere Aussage „alle drei Aufgabenbeschreibungen fordern Q1“ trifft nicht mehr zu.

**Konsequenz:** Kein neuer Kalibrieraufbau und keine Umverteilung alter AP-Stunden ohne neue
Planung. Funktionale Herzschallwiedergabe überprüfen; aus digitalen Playback-/Fixture-Tests
keine Aussage über die reale Bruststück-Übertragungsfunktion oder kompensierte S3/S4-Dämpfung ableiten.

## W2 — SP3T-Nummerierung und Bestätigung der Verdrahtung

**Status: funktionale Zuordnung und Pin-Baseline aufgelöst; Speed-/SD-Hardwarebestätigung offen.**

Historisch: Intern/Originalannotationen nennen Schalter 1 = Speed und Schalter 2 = Filter;
[hardware.md](../05-hardware/hardware.md) nennt die umgekehrte Nummerierung. Die Behauptung,
die Firmware teste nur einen Schalter, ist überholt.

Das aktuelle [Eval-README](../../Development/system/coding/bringup-zephyr/README.md) und
[Overlay](../../Development/system/coding/bringup-zephyr/boards/esp32s3_devkitc_procpu.overlay)
ordnen die Funktionen verbindlich zu:

- **Filter:** Raw/Murmur/BPM, GPIO18/21/38.
- **Speed:** 1×/0,75×/0,5×, GPIO2/39/47.
- **SD:** CS GPIO48, SPI mit Display und Touch geteilt.

**Konsequenz:** Funktionsnamen statt Schalter-Nummern verwenden. Beide Schalter und SD sind
im Default-Build abgebildet. Nicos Verdrahtungsbestätigung vom 2026-09-16 deckt die späteren
Speed-/SD-Ergänzungen nicht ab; Kontakttabelle und Carrier-Revision bleiben zu prüfen (VT-12).
Die historischen Hinweise in hardware.md sind kein aktueller Firmware-Nachweis.

## W3 — ESP-IDF-Präferenz vs. gewählte Zephyr-Architektur

**Status: Plattformwahl aufgelöst; Architekturimplementierung offen.**

R10 und die interne Aufgabenbeschreibung bevorzugen ESP-IDF. Die spätere gespeicherte
Architekturentscheidung S04 wählt **Zephyr**. Der aktuelle Architekturentwurf folgt S04:
Application/Services/Zephyr-Adapter, reines C für DSP in Services, zunächst ein Kern und
Kommunikation über begrenzte Events/Buffer-Handles.

**Konsequenz:** Die Plattformwahl nicht erneut als unentschieden darstellen. Bring-up nutzt
bereits Zephyr, implementiert aber nicht automatisch die vorgeschlagene Worker-/Controller-
Architektur. Die [Readiness-Entscheidungen](../../Development/system/planning/implementation-readiness.md)
und D11 zur separaten Thesis-Struktur bleiben offen; kein neuer Firmware-Umbau durch diese Aktualisierung.

## W4 — Pflicht zur Murmur-/Hörverbesserung vs. aktuelle Evaluation

**Status: Scope aufgelöst; konkrete Evaluationsplanung offen (D04–D06).**

Die frühere Q2/Q3-Fassung fordert den belegten Mehrwert der zwei Filter und eine messbare
Verbesserung menschlicher Murmur-Detektierbarkeit. Die aktuelle Abgabefassung verlangt den
quantitativen Vergleich der automatischen Herzfrequenzbestimmung, literaturgestützte auditive
Anforderungen sowie Funktionsnachweise. Der Vergleich ist ergebnisoffen; die Hörevaluation ist optional.

**Konsequenz:** Keine Filterüberlegenheit oder klinische Relevanz vorwegnehmen. R01/R05 liefern
Methodenvorschläge, keine beschlossenen Primärmetriken oder Pflichtstudie. Bei Ausfall der
Hörevaluation bleiben BPM-Evaluation und Funktionsnachweise erforderlich. Öffentliche
Datensatzlizenzen ersetzen keine Klärung von Einwilligung/Teilnehmerdaten bei eigener Hörevaluation.

## W5 — Gleichzeitiges TLS/Audio vs. Netzwerk außerhalb des Hörens

**Status: Architekturentscheidung aufgelöst; Übergabemechanismus offen (D01).**

Frühere Rechenbudgetnotizen und S03 betrachten simultanes Audio/TLS als Lastfall.
S04 entscheidet, Netzwerkoperationen **außerhalb des Live-Hörens** auszuführen.
Der Entwurf sieht ein eingefrorenes gültiges Sitzungsergebnis, Stoppen des Hörens und eine
exklusive Idle-Lease für NET vor. FHIR wird vom Gerät initiiert, nicht durch Server-Polling.

**Konsequenz:** Überlappung als Fehler-/Störungsfall prüfen, nicht als normalen Betriebsmodus.
Der Offline-Default der Evaluationsfirmware ist kein Nachweis des vorgeschlagenen NET/CTL-Vertrags.
Profil, Patient, Authentifizierung und Zeit bleiben D08; echte Secrets bleiben außerhalb Git.

## W6 — Bring-up-Werte vs. Thesis-Akzeptanzgrenzen

**Status: offen; als Kandidaten getrennt (D03–D06/D10/D13).**

Bring-up implementiert u. a. 16 kHz/128 Frames, Filter 40–800 und 25–150 Hz,
8 s BPM-Fenster/1 s Update, 30–200 BPM sowie 5 s Replay-Clip. Der Spezifikationsentwurf
übernimmt bzw. ergänzt Kandidaten (z. B. 30 s Messsitzung, Qualität/Coverage und Soak-Dauer).
Diese Werte sind keine freigegebenen wissenschaftlichen oder produktspezifischen Grenzwerte.

**Konsequenz:** 8 ms Blockdauer nicht als gemessene End-to-End-Latenz berichten.
Filterbänder, Referenz, Fehlerstatistik, Ressourcen-/Queue-Margen und Replay-/Fixture-Format
vor Abnahme festlegen. Geplante VT-Prozeduren sind kein ausgeführter Testnachweis.
Klasse B/SOUP als Architekturabsicht nicht mit regulatorischer Konformität gleichsetzen.

## W7 — Kalendernotiz vs. verbindliche Termine und Aufwand

**Status: offen für Termine; aktuelle Aufwandsbasis festgelegt.**

Die historische Notiz kombiniert „vier Monate ab 20. Oktober“ mit „Abgabe Ende Januar“;
das ist rechnerisch nicht konsistent. Die damalige Recherche enthält außerdem teilweise
Fristen anderer Fakultäten. Die aktuelle Abgabefassung lässt verbindliche Start-/Abgabetermine
bis zur Bestätigung offen.

**Konsequenz:** Keine Frist aus den alten Notizen ableiten. Bestätigte Termine, Titel, Prüfer
und Firmendokumente nachtragen. Für Aufwand gelten 320 h Kernarbeit + 64 h Puffer und
separate Firmeneinarbeitung 40–80 h; die alte AP-Gliederung ist historische Planung.
Die Readiness-Schätzung 24–37 h umfasst verbleibende Vorbereitung, nicht die gesamte Thesis.

Updated by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
