# Digitales Echtzeit-Stethoskop auf ESP32-S3 mit FHIR-Anbindung

**Zweckoptimierte Echtzeitfilter und Wiedergabegeschwindigkeit zur Verbesserung der menschlichen Herzgeräuscherkennung und der automatischen Herzfrequenzbestimmung**

## Beschreibung

Auf Basis eines vorhandenen analogen Bruststücks wird ein eingebettetes digitales Stethoskop auf einem ESP32-S3 aufgebaut. Das Gerät nimmt das Auskultationssignal über ein I2S-MEMS-Mikrofon auf, verarbeitet es in Echtzeit auf dem Mikrocontroller und gibt es über einen I2S-DAC an Kopfhörer aus. Über einen **Dreiwegeschalter** wählt der Anwender im laufenden Betrieb zwischen drei Filterkonditionen — **Raw (Referenz)**, **murmur-optimiert** und **BPM-optimiert** — und kann zusätzlich die **Wiedergabegeschwindigkeit** reduzieren, um leise Herzgeräusche (Murmurs) besser hörbar zu machen. Parallel bestimmt das Gerät die Herzfrequenz on-device und stellt sie als FHIR-Observation über TLS an einen lokalen HAPI-FHIR-Server bereit. Die Bedienung erfolgt über Display, Taster, Dreiwegeschalter und Potentiometer; Herz- und Lungenmodus sowie die Auskultationspunkte sind wählbar.

Der Kern der Arbeit ist ein **funktionierendes, validiertes Gerät**: nachweislich echtzeitfähiger Audiopfad, funktionierende FHIR/TLS-Übertragung und der **belegte Nutzen** der beiden zweckgebundenen Filter sowie der Wiedergabegeschwindigkeit — der Filter ist damit kein bloßes Feature, sondern eine validierte Fähigkeit.

## Wissenschaftlicher Kern

Den wissenschaftlichen Kern bildet ein messbarer Zielkonflikt der Filterauslegung: Die Filterung, die ein menschlicher Zuhörer zur Erkennung von Herzgeräuschen benötigt, ist nicht notwendig dieselbe, die die amplituden-/hüllkurvenbasierte Herzfrequenzbestimmung optimal unterstützt. Statt einer einzelnen Kompromissfilterung stellt das Gerät daher **zwei zweckoptimierte Filter** bereit und **weist deren jeweiligen Mehrwert nach**. Der Konflikt wird an der realen akustischen Kette (Bruststück → Mikrofon → ADC) unter den Rechenrestriktionen des eingebetteten Systems untersucht.

### Fragestellungen

- **Q1 – Erhalt tieffrequenter Anteile:** Dämpft die Kopplung MEMS-Mikrofon + analoges Bruststück die S3/S4-/Murmur-Bande gegenüber dem analogen Hörpfad, und wie weit lässt sich dies durch die Filterauslegung kompensieren?
- **Q2 – Zweckkonflikt der Filterwahl:** Unterscheidet sich der Filter, der die **menschliche Murmur-Erkennung** am besten unterstützt, vom Filter, der die **BPM-Genauigkeit** am besten unterstützt — und lassen sich beide über den Dreiwegeschalter live nutzbar machen?
- **Q3 – Wiedergabegeschwindigkeit:** Verbessert eine reduzierte Wiedergabegeschwindigkeit die menschliche Murmur-Detektierbarkeit messbar?

### Bewertungsgrundlagen (Hybrid: objektiv primär, Pilotstudie unterstützend)

- (a) Charakterisierung der akustischen Kette (Q1, S3/S4-/Murmur-Band)
- (b) **Objektive Primärmetriken:** Murmur-Detektierbarkeit (z. B. SNR / Spektralkontrast im Murmur-Band) und BPM-Fehler gegen Referenz, jeweils pro Filter; plus Rechenkosten (CPU-Last, Latenz)
- (c) **Unterstützende Pilot-Hörstudie** (n ≈ 5–10) über die drei Filterkonditionen und die Wiedergabegeschwindigkeit
- (d) Nachweis der End-to-End-FHIR/TLS-Übertragung

## Scope

**Aufgebaut, aber nicht wissenschaftlich bewertet:** Lungenmodus (rein interface), Bedien-UX (Display/Taster/Schalter/Poti), FHIR-Übertragung der Herzfrequenz (Funktionsnachweis, keine Studie).

**Nicht Bestandteil der Arbeit:** Gehäuse, Audio-Persistenz, alternative Bruststückgeometrien, regulatorische Konformität (MDR/IEC 62304) sowie ML-basierte Geräuschklassifikation.

**Programmiersprache:** C (hardware-nah, ESP-IDF) oder C in Zephyr (RTOS) → Entscheidung nach kurzer Hands-on-Phase mit der Hardware (AP 1.2); Kriterium: schnellste tragfähige Umsetzung des Echtzeit-Audiopfads.

**Bedienkonzept Dreiwegeschalter:** Position 1 = **Raw** (ungefiltert, Referenz/Studien-Baseline), Position 2 = **Murmur** (murmur-optimierter Filter), Position 3 = **BPM** (BPM-optimierter Filter). Alle drei live im laufenden Betrieb umschaltbar.

## Zeitbudget

Die **Kernarbeitspakete** umfassen **mindestens 320 h ≈ 8,0 PW** (1 PW = 40 h) und bilden die Anforderung an den Arbeitsumfang der Thesis. **Separat und nicht in den 320 h enthalten** sind:

- **Einarbeitung in der Firma:** 1–2 Wochen (≈ 40–80 h)
- **Zeitplan-Erstellung** (detaillierte Terminplanung zu Projektbeginn)
- **Puffer für Unvorhergesehenes:** rund 20 % der 320 h (≈ 64 h), großzügig angesetzt
- **Hardware-Beschaffung & Lieferzeiten:** eigener Puffer eingeplant, da Sensor-/DAC-/Bauteil-Beschaffung nicht immer lagerverfügbar ist
- **Laufende Termine:** wöchentliche Firmen-Meetings sowie regelmäßige Abstimmung mit dem betreuenden Professor

> Die Zeitplanung ist bewusst **konservativ** gehalten. Bei den bekannten Risikopaketen (Echtzeit-Audiopfad, Bruststück-Kopplung, TLS-Integration) ist zusätzlicher Spielraum vorgesehen, sodass unerwartete Verzögerungen die Abgabe nicht gefährden.

## Kernarbeitspakete (mind. 320 h ≈ 8,0 PW)

### Phase 1 — Anforderungen & Architektur (1,6 PW)

- **AP 1.1** Anforderungen, Scope, Problemstellung finalisieren · 0,2 PW
- **AP 1.2** Hardware festlegen, beschaffen, erste Inbetriebnahme; Plattformentscheidung C vs. Zephyr nach Hands-on · 0,3 PW
- **AP 1.3** Vertiefte Recherche (I2S-Audio, Biquad/FIR-Filter, S3/S4-/Murmur-Spektren, Hüllkurven-BPM, FHIR/TLS) · 0,6 PW
- **AP 1.4** System- & Code-Architektur, Task-Schnitt, Doku-Struktur · 0,4 PW
- **AP 1.5** Design-Review mit Betreuer/Firma, Freigabe · 0,1 PW

> ★ **Meilenstein:** Architektur freigegeben

**Summe Phase 1:** 1,6 PW (64 h)

### Phase 2 — Implementierung (3,9 PW)

- **AP 2.1** Audio-Echtzeitpfad: I2S-Mikrofon → Ringpuffer → I2S-DAC · 0,7 PW
- **AP 2.2** Charakterisierung der akustischen Kette (Q1) und daraus abgeleiteter Filterentwurf · 0,5 PW
- **AP 2.3** Drei Filterkonditionen (Raw / Murmur / BPM, Biquad/FIR), live umschaltbar via Dreiwegeschalter · 0,7 PW
- **AP 2.4** BPM-Detektor (amplituden-/hüllkurvenbasiert) · 0,5 PW
- **AP 2.5** Bedien-UX (Display/Taster/Schalter/Poti), Modus-/Punktauswahl, Wiedergabegeschwindigkeit · 0,6 PW
- **AP 2.6** FHIR-Observation über TLS an HAPI-FHIR (Docker) · 0,5 PW
- **AP 2.7** Integration & Verfeinerung anhand erster Befunde · 0,4 PW
- _laufend_ Fortschritt/Entscheidungen dokumentieren, Blocker verfolgen (in APs enthalten)

> ★ **Meilenstein:** Implementierung abgeschlossen & System validiert

**Summe Phase 2:** 3,9 PW (156 h)

### Phase 3 — Evaluation, Dokumentation & hochschulöffentlicher Vortrag (2,5 PW)

- **AP 3.1** Objektive Evaluation (primär): Murmur-Detektierbarkeit (SNR/Spektralkontrast), BPM-Genauigkeit vs. Referenz, Rechenkosten · 0,6 PW
- **AP 3.2** Pilot-Hörstudie (unterstützend, n ≈ 5–10) über 3 Filter + Wiedergabegeschwindigkeit · 0,4 PW
- **AP 3.3** Ergebnisse auswerten · 0,3 PW
- **AP 3.4** Thesis schreiben (Rohfassung, läuft ab Phase 2 mit) · 0,7 PW
- **AP 3.5** Überarbeiten/Polieren, Abbildungen/Referenzen/Anhang · 0,3 PW
- **AP 3.6** Abgabe + hochschulöffentlichen Vortrag an der THA vorbereiten & halten · 0,2 PW

> ★ **Meilenstein:** Thesis abgegeben & verteidigt

**Summe Phase 3:** 2,5 PW (100 h)

**Summe Kernarbeitspakete:** 8,0 PW = 320 h (Phase 1: 1,6 · Phase 2: 3,9 · Phase 3: 2,5)

## Terminrahmen

- **Anmeldung:** Ende September; Bearbeitungszeit **4 Monate ab dem 20. Oktober**, Abgabe entsprechend **Ende Januar**.
- **Puffer:** Beschaffungs-/Lieferzeiten der Hardware sowie unvorhergesehener Mehraufwand sind gesondert eingeplant, damit der Abgabetermin auch bei Verzögerungen sicher gehalten werden kann.
- **Priorisierung bei Zeitdruck:** Ein funktionierendes, validiertes Gerät hat Vorrang. Sollte es eng werden, wird zuerst der Umfang der unterstützenden Pilot-Hörstudie reduziert, bevor die Kernfunktionalität (Audiopfad, Filter, BPM, FHIR/TLS) eingeschränkt wird.
