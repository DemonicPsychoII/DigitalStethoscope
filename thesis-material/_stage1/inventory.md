# Stage 1 inventory

133 information units. Each entry repeats the JSON fields; source keys resolve through `sources.json`.

## U001 — requirement / Einleitung/Motivation

- **Aussage:** Ziel ist ein eingebetteter digitaler Stethoskop-Prototyp auf Basis eines vorhandenen analogen Bruststücks, der Herzschall erfasst, in Echtzeit filtert und über Kopfhörer wiedergibt, automatisch die Herzfrequenz bestimmt und sicher als HL7-FHIR-Ressource überträgt.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Abgabe.md:5
- **Status:** confirmed
- **Zitat nötig:** nein

## U002 — requirement / Anforderungen

- **Aussage:** Zusätzlich soll eine Wiedergabe mit reduzierter Geschwindigkeit als Hörhilfe implementiert und ihre Aufnahme in den Funktionsumfang anhand marktverfügbarer Geräte begründet werden.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Abgabe.md:5
- **Status:** confirmed
- **Zitat nötig:** nein

## U003 — requirement / Anforderungen

- **Aussage:** Untersucht wird der Einfluss wählbarer Filtervarianten auf Genauigkeit und Zuverlässigkeit der automatischen Herzfrequenzbestimmung; auditive Filteranforderungen sollen literaturgestützt hergeleitet und mit den Anforderungen der automatischen Auswertung verglichen werden.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Abgabe.md:7
- **Status:** confirmed
- **Zitat nötig:** nein

## U004 — requirement / Evaluation/Methodik

- **Aussage:** Die BPM-Bestimmung wird quantitativ gegen eine geeignete Referenz evaluiert; Testsignale, Referenzen, Metriken und Versuchsabläufe sollen vorab festgelegt werden.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Abgabe.md:9
- **Status:** confirmed
- **Zitat nötig:** nein

## U005 — requirement / Evaluation/Methodik

- **Aussage:** Der Echtzeit-Audiopfad, Filterwahl, reduzierte Wiedergabegeschwindigkeit und sichere FHIR-Übertragung werden anhand definierter Funktionskriterien geprüft.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Abgabe.md:9
- **Status:** confirmed
- **Zitat nötig:** nein

## U006 — requirement / Evaluation/Methodik

- **Aussage:** Eine explorative Hörevaluation ist optional, sofern Organisation und Zeit es erlauben.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Abgabe.md:9
- **Status:** confirmed
- **Zitat nötig:** nein

## U007 — decision / Anforderungen

- **Aussage:** Komponenteneignung wird anhand von Datenblättern und Fachliteratur beurteilt; messtechnische Charakterisierung der akustischen Übertragungskette ist in der Abgabefassung ausgeschlossen.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Abgabe.md:13
- **Status:** confirmed
- **Zitat nötig:** nein

## U008 — requirement / Anforderungen

- **Aussage:** Ausgeschlossen sind Gehäuseentwicklung, dauerhafte Audiospeicherung, maschinelle Geräuschklassifikation, klinischer Nutzennachweis und regulatorische Konformität.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Abgabe.md:13
- **Status:** confirmed
- **Zitat nötig:** nein

## U009 — parameter / Projektmanagement/Formales

- **Aussage:** Aufwandsschätzung: 320 h Kernarbeit (8 Personenwochen) plus etwa 64 h Puffer; eine Personenwoche entspricht 40 h.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Abgabe.md:17-30
- **Status:** confirmed
- **Zitat nötig:** nein

## U010 — requirement / Anforderungen

- **Aussage:** In der internen Fassung sind drei Filterzustände vorgesehen: Raw (Referenz), murmur-optimiert und BPM-optimiert; die Wahl soll im laufenden Betrieb möglich sein.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:11,64
- **Status:** confirmed
- **Zitat nötig:** nein

## U011 — fact / Stand der Technik

- **Aussage:** Interne Begründung: ein für menschliche Murmur-Erkennung geeigneter Filter muss nicht derselbe sein wie einer für amplituden-/hüllkurvenbasierte Herzfrequenzbestimmung.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:17
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:** digital_stethoscope_characterization (https://pmc.ncbi.nlm.nih.gov/articles/PMC10753976/; Abschnitt/Seite: unverified); frequency_response_stethoscopes (https://pmc.ncbi.nlm.nih.gov/articles/PMC7305673/; Abschnitt/Seite: unverified)
- **Quellen unvollständig:** ja; bitte ergänzen/verifizieren.

## U012 — open-question / Systemarchitektur

- **Aussage:** Q1 fragt, ob die Kopplung MEMS-Mikrofon plus analoges Bruststück S3/S4-/Murmur-Anteile gegenüber dem analogen Hörpfad dämpft und inwieweit Filterauslegung dies kompensiert.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:21
- **Status:** open
- **Zitat nötig:** nein

## U013 — open-question / Evaluation/Methodik

- **Aussage:** Q2 fragt, ob sich der Filter für menschliche Murmur-Erkennung vom Filter für BPM-Genauigkeit unterscheidet und beide live nutzbar sind.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:22
- **Status:** open
- **Zitat nötig:** nein

## U014 — open-question / Evaluation/Methodik

- **Aussage:** Q3 fragt, ob reduzierte Wiedergabegeschwindigkeit die menschliche Murmur-Detektierbarkeit messbar verbessert.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:23
- **Status:** open
- **Zitat nötig:** nein

## U015 — method / Evaluation/Methodik

- **Aussage:** Intern vorgeschlagene objektive Primärmetriken: Murmur-Detektierbarkeit, BPM-Fehler gegen Referenz, CPU-Last und Latenz; eine Pilot-Hörstudie n≈5–10 wäre unterstützend.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:27-30
- **Status:** assumption
- **Zitat nötig:** nein

## U016 — decision / Evaluation/Methodik

- **Aussage:** Für Murmur-Detektierbarkeit ist intern eine binäre Antwort vorhanden/nicht vorhanden plus Sicherheitsskala durch etwa 5–10 Entwickler und medizinisch geschulte Personen vorgeschlagen; keine Diagnose oder Klassifikation.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:37
- **Status:** confirmed
- **Zitat nötig:** nein

## U017 — decision / Evaluation/Methodik

- **Aussage:** Als öffentliche Ground Truth ist CirCor DigiScope mit ODC-By 1.0 und Playback voraufgenommener Sounds vorgeschlagen; die genaue Datensatzwahl ist als „und/oder“ formuliert.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:38
- **Status:** assumption
- **Zitat nötig:** nein

## U018 — open-question / Evaluation/Methodik

- **Aussage:** BPM-Referenz bleibt offen; Pulsoximeter oder Smartwatch gelten intern als realistisch, EKG als aufwendigere Referenz; interner Zielkorridor ±5 bpm / ±10 %.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:39
- **Status:** open
- **Zitat nötig:** nein

## U019 — decision / Evaluation/Methodik

- **Aussage:** Q2-Arbeitsdefinition: Murmur-Filter „besser“ bedeutet höhere Detektionssicherheit/Konfidenz; BPM-Filter „besser“ bedeutet höhere Genauigkeit und weniger Störungen/Ausreißer.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:40
- **Status:** confirmed
- **Zitat nötig:** nein

## U020 — decision / Anforderungen

- **Aussage:** Verlangsamung ist intern als Hörhilfe und nicht als diagnostischer Validitätsnachweis eingeordnet; WSOLA mit Stufen 1,0× / 0,75× / 0,5× ist vorgeschlagen, Originalgeschwindigkeit bleibt verfügbar.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:41
- **Status:** confirmed
- **Zitat nötig:** nein

## U021 — method / Evaluation/Methodik

- **Aussage:** Vorgeschlagene Hörstudie: verblindet, randomisiert, within-subject ABX/2AFC; kurze Einführung zum Murmur; als explorative Machbarkeitspilotstudie; notfalls zugunsten Funktionalität streichbar.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:42
- **Status:** assumption
- **Zitat nötig:** nein

## U022 — risk / Ethik/Datenschutz/Regulatorik

- **Aussage:** Die interne Ethikannahme lautet: kein Ethikvotum angestrebt, sofern nur öffentliche/lizenzkonforme Daten und keine eigenen Patientenaufnahmen genutzt werden.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:43
- **Status:** assumption
- **Zitat nötig:** nein

## U023 — decision / Systemarchitektur

- **Aussage:** Die Membran des Bruststücks soll erhalten bleiben; Kopplung Mikrofon an Hohlraum-/Schlauchöffnung ermöglicht laut interner Planung zwei durch Drehen vergleichbare Bauformen.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:44
- **Status:** confirmed
- **Zitat nötig:** nein

## U024 — decision / Systemarchitektur

- **Aussage:** INMP441 ist gesetzt und bereits als Breakout vorhanden; laut interner Festlegung wird seine untere Grenzfrequenz als Randbedingung dokumentiert statt die Bauteilauswahl neu aufzurollen.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:45
- **Status:** confirmed
- **Zitat nötig:** nein

## U025 — decision / Systemarchitektur

- **Aussage:** PCM5102A ist als I²S-DAC eingeplant.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:46
- **Status:** confirmed
- **Zitat nötig:** nein

## U026 — decision / Evaluation/Methodik

- **Aussage:** Interne Messentscheidung: keine formale akustische Kettencharakterisierung mit Kalibrieraufbau; „Ton hörbar, Herz-Sounds hörbar“ als ausreichend betrachtet.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:47
- **Status:** confirmed
- **Zitat nötig:** nein

## U027 — parameter / Anforderungen

- **Aussage:** Interne Echtzeitlatenzvorstellung: bei 0,5× unkritisch; für 1,0× Zielband <30 ms, besser <10 ms.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:48
- **Status:** confirmed
- **Zitat nötig:** nein

## U028 — decision / Systemarchitektur

- **Aussage:** Plattformentscheidung intern zunächst offen: ESP-IDF (C/FreeRTOS) Favorit; Zephyr-Probeläufe vor Thesis-Start, finale Entscheidung zu Thesis-Beginn.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:49
- **Status:** open
- **Zitat nötig:** nein

## U029 — decision / Systemarchitektur

- **Aussage:** Wi-Fi/FHIR soll außerhalb der Live-Wiedergabe oder als Low-Priority-Task laufen; CPU/RAM soll früh geprüft werden.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:50
- **Status:** confirmed
- **Zitat nötig:** nein

## U030 — requirement / Systemarchitektur

- **Aussage:** FHIR-Ziel intern: Observation (Vital Signs, LOINC 8867-4, UCUM /min), SNTP vor TLS-Handshake und gepinntes Root-CA; Authentisierung darf vereinfacht werden, BPM-JSON-Erzeugung und Versand sollen enthalten sein.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:51
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:** fhir_r4_vitals (https://hl7.org/fhir/R4/observation-vitalsigns.html; Abschnitt/Seite: Vital Signs table, Heart rate row (web text lines 50–51).); loinc_8867 (https://loinc.org/8867-4; Abschnitt/Seite: LOINC term name lines 46–59; Example Units table lines 232–238.)
- **Quellen unvollständig:** ja; bitte ergänzen/verifizieren.

## U031 — requirement / Anforderungen

- **Aussage:** Lungenmodus: Interface/Symbole und Live-Wiedergabe; keine BPM, Filter, Time-Stretch- oder FHIR-Funktion.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:52
- **Status:** confirmed
- **Zitat nötig:** nein

## U032 — decision / Systemarchitektur

- **Aussage:** Bedienvorschlag: Potentiometer für Lautstärke, Schalter für Wiedergabegeschwindigkeit und Filter; optional Touchdisplay zur Konfiguration.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:53
- **Status:** confirmed
- **Zitat nötig:** nein

## U033 — parameter / Projektmanagement/Formales

- **Aussage:** Interne Terminplanung nennt Anmeldung Ende September, Bearbeitungsstart 20. Oktober und Abgabe Ende Januar; der formale Ausgang hängt von tatsächlicher Anmeldung und Fakultätsregeln ab.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:54
- **Status:** assumption
- **Zitat nötig:** nein

## U034 — requirement / Anforderungen

- **Aussage:** Intern als nicht Teil der Arbeit bezeichnet: Gehäuse, Audio-Persistenz, alternative Bruststückgeometrien, MDR/IEC-62304-Konformität und ML-basierte Klassifikation.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:60
- **Status:** confirmed
- **Zitat nötig:** nein

## U035 — decision / Systemarchitektur

- **Aussage:** Interne Programmiersprachen-/Framework-Auswahl: C/ESP-IDF oder C/Zephyr nach Hands-on-Phase; Kriterium ist schnellste tragfähige Echtzeit-Audio-Umsetzung.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:62
- **Status:** open
- **Zitat nötig:** nein

## U036 — parameter / Projektmanagement/Formales

- **Aussage:** Kernaufwand intern auf 320 h verteilt: Phase 1 64 h, Phase 2 156 h, Phase 3 100 h.
- **Ursprung:** preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:75-118
- **Status:** confirmed
- **Zitat nötig:** nein

## U037 — contradiction / Diskussion/Ausblick

- **Aussage:** W1: Aufgabenbeschreibungen führen Q1, Kettencharakterisierung und AP 2.2 auf, die interne Entscheidung verwirft gleichzeitig die formale Messung; die vorgesehenen Playback-Signale durchlaufen die reale Bruststückkopplung nicht.
- **Ursprung:** preThesis/02-entscheidungen/widersprueche.md:5-21
- **Status:** contradicted
- **Zitat nötig:** nein

## U038 — open-question / Diskussion/Ausblick

- **Aussage:** W1 ist noch offen; dokumentierte Optionen sind Q1/AP 2.2 qualitativ umformulieren, Q1 streichen/Arbeitszeit umverteilen oder R08-Minimalmessung ausführen; Abstimmung mit Betreuer steht aus.
- **Ursprung:** preThesis/02-entscheidungen/widersprueche.md:23-32
- **Status:** open
- **Zitat nötig:** nein

## U039 — contradiction / Systemarchitektur

- **Aussage:** W2: Nummerierung der beiden SP3T-Schalter weicht ab: intern/open-questions ordnen Schalter 1 Geschwindigkeit und Schalter 2 Filter zu, Hardwareliste ordnet Schalter 1 Filter und Schalter 2 Geschwindigkeit zu.
- **Ursprung:** preThesis/02-entscheidungen/widersprueche.md:34-42
- **Status:** contradicted
- **Zitat nötig:** nein

## U040 — decision / Systemarchitektur

- **Aussage:** W2 wird als unkritisch eingestuft, da beide Bauteile identisch seien; Zuordnung soll vor finalem Aufbau verbindlich festgeschrieben werden; Bring-up prüft bewusst einen Schalter.
- **Ursprung:** preThesis/02-entscheidungen/widersprueche.md:44-48
- **Status:** open
- **Zitat nötig:** nein

## U041 — method / Evaluation/Methodik

- **Aussage:** R01 berichtet, dass keine einzelne normierte Murmur-Detektierbarkeitskennzahl vorliegt; für identische Eingangsdaten werden bandbegrenzte Murmur-SNR, Murmur-zu-S1/S2-Energieverhältnis und Hüllkurvenkontrast vorgeschlagen.
- **Ursprung:** preThesis/02-entscheidungen/open-questions.md:17-27
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:** digital_auscultation_murmur (https://doi.org/10.1007/s10439-008-9611-z; Abschnitt/Seite: Introduction, heart cycle/murmur description (web text lines 71–73; 85).)
- **Quellen unvollständig:** ja; bitte ergänzen/verifizieren.

## U042 — method / Evaluation/Methodik

- **Aussage:** Für Filtervergleich sollen identische Zeitfenster aus einer gemeinsamen Referenzsegmentierung stammen, damit Filterwirkung nicht zugleich die Segmentierung verändert.
- **Ursprung:** preThesis/02-entscheidungen/open-questions.md:29-31
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:** digital_auscultation_murmur (https://doi.org/10.1007/s10439-008-9611-z; Abschnitt/Seite: Introduction, heart cycle/murmur description (web text lines 71–73; 85).)
- **Quellen unvollständig:** ja; bitte ergänzen/verifizieren.

## U043 — fact / Grundlagen (medizinisch: Herztöne, Murmurs, Auskultation)

- **Aussage:** In R01 werden 25–400 Hz für viele Murmuranalysen und 20–500 bzw. 20–800 Hz für breitere PCG-Analysen genannt; breitbandiges SNR oder RMS allein belegt keine bessere Murmur-Detektierbarkeit.
- **Ursprung:** preThesis/02-entscheidungen/open-questions.md:33-35
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:** digital_auscultation_murmur (https://doi.org/10.1007/s10439-008-9611-z; Abschnitt/Seite: Introduction, heart cycle/murmur description (web text lines 71–73; 85).); frequency_response_stethoscopes (https://pmc.ncbi.nlm.nih.gov/articles/PMC7305673/; Abschnitt/Seite: unverified)
- **Quellen unvollständig:** ja; bitte ergänzen/verifizieren.

## U044 — fact / Evaluation/Methodik

- **Aussage:** R02 nennt CirCor DigiScope v1.0.3: 1.568 Personen, 5.272 Aufnahmen, 4 kHz, ODC-By 1.0, Murmur-Status/Ort/Timing/Form/Tonhöhe/Qualität/Grad sowie S1/S2-Segmentierung; Kohorte 0–21 Jahre.
- **Ursprung:** preThesis/02-entscheidungen/open-questions.md:41-45
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:** circor_dataset (https://doi.org/10.13026/tshs-mw03; Abschnitt/Seite: unverified); circor_paper (https://doi.org/10.1109/JBHI.2021.3137048; Abschnitt/Seite: unverified); physionet_challenge_2022 (https://physionet.org/content/challenge-2022/1.0.0/papers/; Abschnitt/Seite: unverified)

## U045 — fact / Evaluation/Methodik

- **Aussage:** R02 bewertet PhysioNet/CinC 2016 mit 3.126 Aufnahmen, 2 kHz und nur normal/abnormal als nicht geeignet für Murmur-Ground-Truth.
- **Ursprung:** preThesis/02-entscheidungen/open-questions.md:47-48
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:** circor_paper (https://doi.org/10.1109/JBHI.2021.3137048; Abschnitt/Seite: unverified); physionet_challenge_2022 (https://physionet.org/content/challenge-2022/1.0.0/papers/; Abschnitt/Seite: unverified)
- **Quellen unvollständig:** ja; bitte ergänzen/verifizieren.

## U046 — parameter / Stand der Technik

- **Aussage:** R02 nennt Simulator-Preise: Sakamoto ca. 9.092 USD, SAM Basic ca. 3.750 USD, PAT Basic ca. 2.200 USD; 3B Scientific Hand-Held Trainer plus Murmur-Soundkarte mit 16 Murmurs ca. £227.
- **Ursprung:** preThesis/02-entscheidungen/open-questions.md:50-53
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:** circor_dataset (https://doi.org/10.13026/tshs-mw03; Abschnitt/Seite: unverified)
- **Quellen unvollständig:** ja; bitte ergänzen/verifizieren.

## U047 — method / Evaluation/Methodik

- **Aussage:** R03 empfiehlt synchron aufgezeichnetes EKG mit R-Zacken/R-R-Intervallen als BPM-Referenz sowie Bland–Altman und MAE/MAPE als Auswertung.
- **Ursprung:** preThesis/02-entscheidungen/open-questions.md:59-60
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:** ec13_standard (https://mdcpp.com/doc/standard/ANSIAAMIEC13-2002.pdf; Abschnitt/Seite: unverified); hr_accuracy_review (https://pmc.ncbi.nlm.nih.gov/articles/PMC12505149/; Abschnitt/Seite: unverified)
- **Quellen unvollständig:** ja; bitte ergänzen/verifizieren.

## U048 — fact / Evaluation/Methodik

- **Aussage:** R03 nennt als Mindestziel ±10 % oder ±5 bpm (je nachdem welcher Betrag größer ist) aus ANSI/AAMI EC13 und IEC 60601-2-27; diese Grenzwerte gelten für EKG-Monitore und dürfen nicht als PCG-Konformität behauptet werden.
- **Ursprung:** preThesis/02-entscheidungen/open-questions.md:61-68
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:** ec13_standard (https://mdcpp.com/doc/standard/ANSIAAMIEC13-2002.pdf; Abschnitt/Seite: unverified); hr_accuracy_review (https://pmc.ncbi.nlm.nih.gov/articles/PMC12505149/; Abschnitt/Seite: unverified); fda_ec13_guidance (https://www.fda.gov/regulatory-information/search-fda-guidance-documents/cardiac-monitor-guidance-including-cardiotachometer-and-rate-alarm-guidance-industry; Abschnitt/Seite: unverified)

## U049 — fact / Evaluation/Methodik

- **Aussage:** In R01 ist keine belegte dB-Schwelle für „besserer“ Filter dokumentiert; 14 dB betrifft eine Zeitbestimmungsaufgabe und ist keine Murmur-Detektierbarkeitsschwelle.
- **Ursprung:** preThesis/02-entscheidungen/open-questions.md:74-77
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:** digital_auscultation_murmur (https://doi.org/10.1007/s10439-008-9611-z; Abschnitt/Seite: Introduction, heart cycle/murmur description (web text lines 71–73; 85).)
- **Quellen unvollständig:** ja; bitte ergänzen/verifizieren.

## U050 — method / Evaluation/Methodik

- **Aussage:** R01 schlägt vor, eine primäre Metrik vorab festzulegen, gepaarte Wilcoxon-Tests, Effektgröße samt Konfidenzintervall und bei Mehrfachtests Holm-Bonferroni zu nutzen.
- **Ursprung:** preThesis/02-entscheidungen/open-questions.md:79-86
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:**
- **Quellen unvollständig:** ja; bitte ergänzen/verifizieren.

## U051 — method / Grundlagen (technisch: Akustik, MEMS, I2S, DSP/Filter, BPM, Time-Stretch, Embedded/RTOS, FHIR/TLS)

- **Aussage:** R04 empfiehlt pitch-erhaltendes Time-Stretching nur als Hörhilfe, Originaltempo parallel beizubehalten und WSOLA bzw. transientschonende Varianten für S1/S2-Transienten zu erwägen.
- **Ursprung:** preThesis/02-entscheidungen/open-questions.md:93-99
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:** wsola_roelands (https://doi.org/10.21437/Eurospeech.1993-59; Abschnitt/Seite: Abstract and bibliographic record (web text lines 4–18).); wsola_verhelst (https://researchportal.vub.be/en/publications/an-overlap-add-technique-based-on-waveform-similarity-wsola-for-h/; Abschnitt/Seite: unverified)
- **Quellen unvollständig:** ja; bitte ergänzen/verifizieren.

## U052 — parameter / Evaluation/Methodik

- **Aussage:** R04 schätzt WSOLA bei 20–50 Mio. Zyklen/s als 8–21 % eines 240-MHz-Kerns; Phase-Vocoder bei 512-Punkt Float-FFT, 8 kHz, 25 % Hop mit 10–30 Mio. Zyklen/s; laut Bericht liegen Risiken eher bei Qualität/Puffern.
- **Ursprung:** preThesis/02-entscheidungen/open-questions.md:101-103
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:** wsola_roelands (https://doi.org/10.21437/Eurospeech.1993-59; Abschnitt/Seite: Abstract and bibliographic record (web text lines 4–18).)
- **Quellen unvollständig:** ja; bitte ergänzen/verifizieren.

## U053 — method / Evaluation/Methodik

- **Aussage:** R05 schlägt für Laien eine Diskriminationsaufgabe statt Diagnose vor; die Recherche behauptet, diagnostische Fähigkeit korreliere mit Erfahrung, einfache Herzgeräusch/Normal-Unterscheidung dagegen nicht.
- **Ursprung:** preThesis/02-entscheidungen/open-questions.md:112-120
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:**
- **Quellen unvollständig:** ja; bitte ergänzen/verifizieren.

## U054 — method / Evaluation/Methodik

- **Aussage:** R05 schlägt verblindetes, randomisiertes within-subject ABX/2AFC mit mehreren Aufnahmen, kontrollierter Lautheit, neutralen Codes, Übung und Pausen vor.
- **Ursprung:** preThesis/02-entscheidungen/open-questions.md:142-146
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:**
- **Quellen unvollständig:** ja; bitte ergänzen/verifizieren.

## U055 — method / Evaluation/Methodik

- **Aussage:** Bei n=5–10 empfiehlt R05 Rohdaten, individuelle Trefferquoten, Mediane, Effektgrößen und Unsicherheitsintervalle; p-Werte allenfalls explorativ.
- **Ursprung:** preThesis/02-entscheidungen/open-questions.md:148-155
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:**
- **Quellen unvollständig:** ja; bitte ergänzen/verifizieren.

## U056 — risk / Ethik/Datenschutz/Regulatorik

- **Aussage:** R06 hält ein formelles Ethikvotum bei gesunden einwilligungsfähigen Erwachsenen, minimalem Risiko und ohne eigene Patientendaten für wahrscheinlich entbehrlich; empfiehlt dennoch Betreuer-Selbsteinschätzung und Anfrage bei THA/GEHBa.
- **Ursprung:** preThesis/02-entscheidungen/open-questions.md:126-129
- **Status:** assumption
- **Zitat nötig:** ja
- **Quellen:**
- **Quellen unvollständig:** ja; bitte ergänzen/verifizieren.

## U057 — definition / Ethik/Datenschutz/Regulatorik

- **Aussage:** R06 unterscheidet vollständig anonymisierte Daten von pseudonymisierten/de-identifizierten personenbezogenen Daten und weist Herzschall als möglicherweise Gesundheitsdatum nach DSGVO Art. 9 aus.
- **Ursprung:** preThesis/02-entscheidungen/open-questions.md:131-138
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:** health_data_guidance (https://health.ec.europa.eu/system/files/2021-02/ms_rules_health-data_en_0.pdf; Abschnitt/Seite: unverified)
- **Quellen unvollständig:** ja; bitte ergänzen/verifizieren.

## U058 — decision / Systemarchitektur

- **Aussage:** R07 empfiehlt Membran beizubehalten, eine kleine abgedichtete Mikrofonkammer direkt dahinter und kurzen akustischen Weg statt langen Schlauchs.
- **Ursprung:** preThesis/02-entscheidungen/open-questions.md:175-177
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:** digital_stethoscope_characterization (https://pmc.ncbi.nlm.nih.gov/articles/PMC10753976/; Abschnitt/Seite: unverified); frequency_response_stethoscopes (https://pmc.ncbi.nlm.nih.gov/articles/PMC7305673/; Abschnitt/Seite: unverified); invitro_stethoscopes (https://pmc.ncbi.nlm.nih.gov/articles/PMC6339642/; Abschnitt/Seite: unverified)

## U059 — parameter / Grundlagen (technisch: Akustik, MEMS, I2S, DSP/Filter, BPM, Time-Stretch, Embedded/RTOS, FHIR/TLS)

- **Aussage:** R07 gibt als Helmholtz-Resonanzabschätzung für 20 Hz ca. 21 ml bei üblichen Halsabmessungen an und empfiehlt eine kleine, kurze, bedämpfte Kammer, um Resonanz oberhalb des Bands 20–600 Hz zu legen.
- **Ursprung:** preThesis/02-entscheidungen/open-questions.md:179-182
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:** digital_stethoscope_characterization (https://pmc.ncbi.nlm.nih.gov/articles/PMC10753976/; Abschnitt/Seite: unverified); invitro_stethoscopes (https://pmc.ncbi.nlm.nih.gov/articles/PMC6339642/; Abschnitt/Seite: unverified)
- **Quellen unvollständig:** ja; bitte ergänzen/verifizieren.

## U060 — risk / Systemarchitektur

- **Aussage:** R07 bezeichnet Leckage als kritischen Baufehler mit starker Dämpfung bei 20–40 Hz; ein in der Literatur genannter Aufbau mit 5-cm-Schlauch, 6-mm-Innendurchmesser und Kondensatormikrofon sei unter 60 Hz nicht optimal.
- **Ursprung:** preThesis/02-entscheidungen/open-questions.md:184-186
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:** digital_stethoscope_characterization (https://pmc.ncbi.nlm.nih.gov/articles/PMC10753976/; Abschnitt/Seite: unverified); frequency_response_stethoscopes (https://pmc.ncbi.nlm.nih.gov/articles/PMC7305673/; Abschnitt/Seite: unverified); invitro_stethoscopes (https://pmc.ncbi.nlm.nih.gov/articles/PMC6339642/; Abschnitt/Seite: unverified)

## U061 — parameter / Grundlagen (technisch: Akustik, MEMS, I2S, DSP/Filter, BPM, Time-Stretch, Embedded/RTOS, FHIR/TLS)

- **Aussage:** R07 vergleicht Mikrofone nach LFRO (unterer −3-dB-Punkt relativ zu 1 kHz): ICS-40180 60 Hz, ICS-43434 60 Hz, SPH0645LM4H-1 45 Hz, IM69D130 28 Hz, SPH0655LM4H-1 25 Hz, SPK18R1LM4H-1 20 Hz, SPK01A0LR5H-1 17 Hz, IM68A130 10 Hz.
- **Ursprung:** preThesis/02-entscheidungen/open-questions.md:192-204
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:**
- **Quellen unvollständig:** ja; bitte ergänzen/verifizieren.

## U062 — risk / Systemarchitektur

- **Aussage:** R07 nennt beim IM69D130 ein einfach erhältliches Shield2Go mit ADAU7002, bei Knowles-Typen Flexboard/Muskie-Evalsystem und mögliche Liefer-/Lötprobleme; SPH0645 mit 45 Hz wird für 20 Hz als ungeeignet bewertet.
- **Ursprung:** preThesis/02-entscheidungen/open-questions.md:206-209
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:**
- **Quellen unvollständig:** ja; bitte ergänzen/verifizieren.

## U063 — method / Evaluation/Methodik

- **Aussage:** R08 sagt, es gebe keine verbindliche akustische Produktnorm für elektronische Stethoskope und schlägt Lautsprecher, abgedichteten Koppler, Bruststück, MEMS/ADC sowie Referenzmikrofon am Bruststückeingang und ESS-Deconvolution von 10–1000 Hz vor.
- **Ursprung:** preThesis/02-entscheidungen/open-questions.md:215-226
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:** digital_stethoscope_characterization (https://pmc.ncbi.nlm.nih.gov/articles/PMC10753976/; Abschnitt/Seite: unverified); frequency_response_stethoscopes (https://pmc.ncbi.nlm.nih.gov/articles/PMC7305673/; Abschnitt/Seite: unverified); invitro_stethoscopes (https://pmc.ncbi.nlm.nih.gov/articles/PMC6339642/; Abschnitt/Seite: unverified)

## U064 — parameter / Anforderungen

- **Aussage:** R09 empfiehlt ≤10 ms End-to-End und Entwicklungsziel ≤5 ms; Bericht nennt Wahrnehmbarkeit ab etwa 10–15 ms, Störung ab 15–30 ms und typische A/D- bzw. D/A-Latenz 1–1,5 ms.
- **Ursprung:** preThesis/02-entscheidungen/open-questions.md:232-238
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:** digital_stethoscope_characterization (https://pmc.ncbi.nlm.nih.gov/articles/PMC10753976/; Abschnitt/Seite: unverified)
- **Quellen unvollständig:** ja; bitte ergänzen/verifizieren.

## U065 — decision / Systemarchitektur

- **Aussage:** R10 empfiehlt ESP-IDF statt Zephyr für die benötigte Kombination aus PDM-Audio, Audio-DMA, Wi-Fi, TLS und esp-dsp; Zephyr sei grundsätzlich nutzbar, aber risikoreicher.
- **Ursprung:** preThesis/02-entscheidungen/open-questions.md:249-253
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:**
- **Quellen unvollständig:** ja; bitte ergänzen/verifizieren.

## U066 — fact / Systemarchitektur

- **Aussage:** R10 hält Rechenbudget grundsätzlich für ausreichend unter Bedingungen: DMA-blockweise Filter, ESP32-S3-optimiertes esp-dsp, BPM auf heruntergesampelter Hüllkurve, TLS nicht in hochpriorisierter Audiotask und externer I²S-DAC/Verstärker.
- **Ursprung:** preThesis/02-entscheidungen/open-questions.md:259-267
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:**
- **Quellen unvollständig:** ja; bitte ergänzen/verifizieren.

## U067 — risk / Systemarchitektur

- **Aussage:** R10 nennt 512 KB On-Chip-SRAM und weist darauf hin, dass PSRAM DMA-fähigen internen RAM nicht ersetzt; Engpässe seien zusammenhängender interner TLS-Heap, Task/DMA/Buffer-Planung bei Wi-Fi sowie optional Time-Stretching.
- **Ursprung:** preThesis/02-entscheidungen/open-questions.md:264-269
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:**
- **Quellen unvollständig:** ja; bitte ergänzen/verifizieren.

## U068 — definition / Grundlagen (technisch: Akustik, MEMS, I2S, DSP/Filter, BPM, Time-Stretch, Embedded/RTOS, FHIR/TLS)

- **Aussage:** R11 beschreibt Heart Rate Observation mit vital-signs, LOINC 8867-4, Patient-Referenz, effectiveDateTime, valueQuantity, UCUM /min.
- **Ursprung:** preThesis/02-entscheidungen/open-questions.md:275-278
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:** fhir_r4_vitals (https://hl7.org/fhir/R4/observation-vitalsigns.html; Abschnitt/Seite: Vital Signs table, Heart rate row (web text lines 50–51).); loinc_8867 (https://loinc.org/8867-4; Abschnitt/Seite: LOINC term name lines 46–59; Example Units table lines 232–238.); fhir_hr_example (https://fhir.hl7.org/fhir/observation-example-heart-rate.html; Abschnitt/Seite: unverified)

## U069 — risk / Systemarchitektur

- **Aussage:** R11 nennt SNTP vor TLS-Zertifikatsprüfung, einzelnes gepinntes Root-CA als platzsparendere Alternative zum Bundle und ESP-IDF-FAQ-Schätzung von ca. 40–50 kB freiem internem Heap für stabilen Handshake.
- **Ursprung:** preThesis/02-entscheidungen/open-questions.md:280-288
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:**
- **Quellen unvollständig:** ja; bitte ergänzen/verifizieren.

## U070 — formal-rule / Projektmanagement/Formales

- **Aussage:** R12 berichtet keine öffentlich auffindbare THA-weite Regel zu Titellänge, Titelsprache oder Übersetzungspflicht; diese Punkte sollen Prüfungsamt/Betreuer klären.
- **Ursprung:** preThesis/03-recherche/R12-tha-formales.md:24-29,51-53
- **Status:** open
- **Zitat nötig:** nein

## U071 — formal-rule / Projektmanagement/Formales

- **Aussage:** R12 nennt digitale DMS-Anmeldung, formale Vorprüfung, vier Monate Bearbeitungszeit ab nächstem 20. nach Anmeldung und keine Anmeldung im August.
- **Ursprung:** preThesis/03-recherche/R12-tha-formales.md:33-40
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:**
- **Quellen unvollständig:** ja; bitte ergänzen/verifizieren.

## U072 — formal-rule / Projektmanagement/Formales

- **Aussage:** R12 nennt fakultätsspezifische Unterschiede: Gestaltung-Beispiel 14. März–14. Juli / Titeländerung bis zwei Wochen vor Abgabe; Maschinenbau/Umwelt-Merkblatt nennt maximal fünf Monate.
- **Ursprung:** preThesis/03-recherche/R12-tha-formales.md:39-47
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:**
- **Quellen unvollständig:** ja; bitte ergänzen/verifizieren.

## U073 — definition / Grundlagen (medizinisch: Herztöne, Murmurs, Auskultation)

- **Aussage:** S1 und S2 sind die zwei regelmäßig wiederkehrenden Herztöne pro Herzzyklus; der Abschnitt S1→S2 entspricht der Systole, S2→nächstes S1 der Diastole.
- **Ursprung:** preThesis/03-recherche/R01-murmur-metrik.md:148-153; preThesis/02-entscheidungen/open-questions.md:24-25
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:** digital_auscultation_murmur (https://doi.org/10.1007/s10439-008-9611-z; Abschnitt/Seite: Introduction, heart cycle/murmur description (web text lines 71–73; 85).)
- **Quellen unvollständig:** ja; bitte ergänzen/verifizieren.

## U074 — definition / Grundlagen (medizinisch: Herztöne, Murmurs, Auskultation)

- **Aussage:** Die Forschungsberichte beschreiben Herzgeräusche als Folge turbulenter Strömung und unterscheiden systolische bzw. diastolische Murmurs nach Auftreten im Zyklus.
- **Ursprung:** preThesis/03-recherche/R01-murmur-metrik.md:197-245
- **Status:** confirmed
- **Zitat nötig:** ja
- **Quellen:** digital_auscultation_murmur (https://doi.org/10.1007/s10439-008-9611-z; Abschnitt/Seite: Introduction, heart cycle/murmur description (web text lines 71–73; 85).)
- **Quellen unvollständig:** ja; bitte ergänzen/verifizieren.

## U075 — parameter / Systemarchitektur

- **Aussage:** Bestandsliste: ESP32-S3 N16R8 DevKitC-1 mit 16 MB Flash und 8 MB PSRAM.
- **Ursprung:** preThesis/05-hardware/hardware.md:8-9
- **Status:** confirmed
- **Zitat nötig:** nein

## U076 — parameter / Systemarchitektur

- **Aussage:** Bestandsliste: PCM5102A I²S-DAC zur Kopfhörerwiedergabe und INMP441 I²S-MEMS-Mikrofon zur Aufnahme.
- **Ursprung:** preThesis/05-hardware/hardware.md:10-11
- **Status:** confirmed
- **Zitat nötig:** nein

## U077 — parameter / Systemarchitektur

- **Aussage:** Bestandsliste: 10-kΩ-Potentiometer am ADC für Lautstärke; Fasizi ILI9341 240×320 TFT mit Touch über SPI.
- **Ursprung:** preThesis/05-hardware/hardware.md:13-14
- **Status:** confirmed
- **Zitat nötig:** nein

## U078 — parameter / Systemarchitektur

- **Aussage:** Hardwaredokumentation führt zwei SP3T-THT-Schalter auf: Filterwahl Raw/Murmur/BPM und Wiedergabegeschwindigkeit 1,0×/0,75×/0,5×.
- **Ursprung:** preThesis/05-hardware/hardware.md:15-16
- **Status:** confirmed
- **Zitat nötig:** nein

## U079 — decision / Systemarchitektur

- **Aussage:** Hardwaredokumentation hält fest, dass INMP441s untere Grenzfrequenz die nutzbare Bandbreite begrenzt und Bauteilauswahl abgeschlossen ist.
- **Ursprung:** preThesis/05-hardware/hardware.md:20-21
- **Status:** confirmed
- **Zitat nötig:** nein

## U080 — open-question / Systemarchitektur

- **Aussage:** I²S-Peripherie- und Pinzuordnung für INMP441 und PCM5102A war in der Hardwareplanung noch festzulegen.
- **Ursprung:** preThesis/05-hardware/hardware.md:24
- **Status:** open
- **Zitat nötig:** nein

## U081 — risk / Systemarchitektur

- **Aussage:** PSRAM ersetzt nicht DMA-fähigen internen SRAM; TLS-Handshake-Heap wird als kritischer Engpass vermerkt.
- **Ursprung:** preThesis/05-hardware/hardware.md:26
- **Status:** confirmed
- **Zitat nötig:** nein

## U082 — open-question / Projektmanagement/Formales

- **Aussage:** Zu beschaffen/klären: Kopfhörer bzw. Verstärkerstufe hinter PCM5102A sowie Verkabelung/Adapterplatine und Steckbrett- oder Lötaufbau.
- **Ursprung:** preThesis/05-hardware/hardware.md:28-30
- **Status:** open
- **Zitat nötig:** nein

## U083 — fact / Projektmanagement/Formales

- **Aussage:** Forschungslog verzeichnet 12 Rechercheläufe R01–R12, alle als OK, mit Presets und ausgewiesener Summe von 0,3590 USD.
- **Ursprung:** preThesis/03-recherche/research-log.txt:1-15
- **Status:** confirmed
- **Zitat nötig:** nein

## U084 — method / Projektmanagement/Formales

- **Aussage:** runs.json enthält die Suchprompts und Fragestellungen für alle zwölf R01–R12-Recherchen; es ist ein Prompt-/Provenienzprotokoll, keine unabhängige Primärquelle.
- **Ursprung:** preThesis/03-recherche/runs.json:1-74
- **Status:** confirmed
- **Zitat nötig:** nein

## U085 — fact / Systemarchitektur

- **Aussage:** README beschreibt die Bring-up-Firmware als ESP32-S3-Zephyr-Anwendung mit Audio-, DSP-, FHIR/Netzwerk-, Display-/Touch-, GPIO- und SD-Speichermodulen; konkrete Datenflussdetails sind der README-Architektursektion zu entnehmen.
- **Ursprung:** Development/system/coding/bringup-zephyr/README.md:1-120
- **Status:** confirmed
- **Zitat nötig:** nein

## U086 — fact / Systemarchitektur

- **Aussage:** README dokumentiert INMP441 als Audioeingang und PCM5102A als externen Audioausgang; die Verkabelung/Pinbelegung wird im README als Eval-Träger-Rev A geführt.
- **Ursprung:** Development/system/coding/bringup-zephyr/README.md:1-160
- **Status:** confirmed
- **Zitat nötig:** nein

## U087 — measurement / Systemarchitektur

- **Aussage:** README-Update 2026-10-02 meldet Rev A-Verdrahtung für Geschwindigkeits-Schalter (GPIO2/39/47) und LCD-SD am geteilten SPI2 (CS GPIO48); Standard-Firmware bildet beides ab.
- **Ursprung:** Development/system/coding/bringup-zephyr/README.md:1-160
- **Status:** confirmed
- **Zitat nötig:** nein

## U088 — measurement / Implementierung

- **Aussage:** README-Update 2026-09-16 meldet bestätigte Eval-Verdrahtung; historischer Hardwareplan listet nur einen standardmäßig verdrahteten physischen Schalter; Wiedergabegeschwindigkeit sei per Touch/Serial erreichbar gewesen; optionaler zweiter Overlay-Schalter separat unverifiziert.
- **Ursprung:** preThesis/05-hardware/hardware.md:32-34
- **Status:** confirmed
- **Zitat nötig:** nein

## U089 — method / Evaluation/Methodik

- **Aussage:** EVAL-GUIDE definiert physische Annahmekriterien und trennt Software-Build-Nachweis von Hardware-Funktion; ungeprüfte Positionen bleiben offen bzw. blockiert.
- **Ursprung:** Development/system/coding/bringup-zephyr/EVAL-GUIDE.md:1-162
- **Status:** confirmed
- **Zitat nötig:** nein

## U090 — method / Evaluation/Methodik

- **Aussage:** TEST-PROTOCOL definiert manuelle Hardwareprüfungen, Verdrahtungs-/Electrical-Safety-, Audio-, Display-, Touch-, GPIO-, SD-, Netzwerk-/FHIR-Prüfungen und PASS/FAIL/BLOCKED-Evidenz.
- **Ursprung:** Development/system/coding/bringup-zephyr/TEST-PROTOCOL.md:1-1517
- **Status:** confirmed
- **Zitat nötig:** nein

## U091 — measurement / Evaluation/Methodik

- **Aussage:** QC-EVALUATION meldet 100/100 PASS für statischen THA-baseline-Vergleich, datiert 2026-09-24; der Bericht sagt ausdrücklich, dass dies keine Compilation, Instrumentierung, Elektroprüfung, Audiomessung oder manuelle Hardwareprüfung ersetzt.
- **Ursprung:** Development/system/testing/QC-EVALUATION.md:1-9
- **Status:** confirmed
- **Zitat nötig:** nein

## U092 — risk / Evaluation/Methodik

- **Aussage:** QC-EVALUATION nennt als offene Aktionen: I²S/LEDC-Pinmux und XPT2046-Kalibrierung validieren, Touch-Callback-Zustand absichern, Eingabepolling ≤20 ms dokumentieren, Laufzeitfehlerbehandlung prüfen sowie Ergebnisse an Firmware-Commit binden.
- **Ursprung:** Development/system/testing/QC-EVALUATION.md:26-40
- **Status:** confirmed
- **Zitat nötig:** nein

## U093 — method / Evaluation/Methodik

- **Aussage:** CI-QUALITY-GATES dokumentiert gepinnte Zephyr- und Werkzeugversionen, wiederholbare lokale/CI-Prüfungen sowie getrennte Builds und statische Prüfungen; Quelle beschreibt Entwicklungs-/Verifikationsmethode, keine medizinische Evidenz.
- **Ursprung:** Development/system/testing/CI-QUALITY-GATES.md:1-57
- **Status:** confirmed
- **Zitat nötig:** nein

## U094 — method / Evaluation/Methodik

- **Aussage:** CI-Hardwaregrenze: ESP32-S3-Build belegt Kompilierung/Linken und Ressourcen-Fit, aber nicht Mikrofon-, DAC-, Display-, Touch-, GPIO-, ADC-, PWM- oder Verdrahtungsfunktion.
- **Ursprung:** Development/system/testing/CI-QUALITY-GATES.md:87-107
- **Status:** confirmed
- **Zitat nötig:** nein

## U095 — method / Evaluation/Methodik

- **Aussage:** Testing-README unterscheidet QC-Score von funktionaler Evaluation; CI-Hosttests und Offline/QC/Netzwerk-QC-Builds schließen die physische Hardware-Abnahmematrix nicht ab.
- **Ursprung:** Development/system/testing/README.md:27-40
- **Status:** confirmed
- **Zitat nötig:** nein

## U097 — measurement / Evaluation/Methodik

- **Aussage:** QC-Ergebnis JSON dokumentiert 10 Kontrollen mit Score je 10 und Gate PASS; Verifikation basiert teils auf Heuristiken, und erforderliche Maßnahmen bleiben trotz PASS ausgewiesen.
- **Ursprung:** Development/system/testing/qc-eval-results.json:1-92
- **Status:** confirmed
- **Zitat nötig:** nein

## U098 — method / Evaluation/Methodik

- **Aussage:** THA-baseline-traceability.json bindet den institutionalisierten Vergleich an Revision 4698995f203f73f4b264e4355ca30e2712163729 und drei SHA-256-Einträge.
- **Ursprung:** Development/system/testing/tha-baseline-traceability.json:1-10
- **Status:** confirmed
- **Zitat nötig:** nein

## U099 — fact / Einleitung/Motivation

- **Aussage:** Root README beschreibt das Repository als ESP32-S3-Evaluierungsfirmware und Testmaterial für die Bachelorarbeit.
- **Ursprung:** README.md:1-7
- **Status:** confirmed
- **Zitat nötig:** nein

## U100 — fact / Diskussion/Ausblick

- **Aussage:** widersprueche.md Stand 2026-08-15; offene Punkte zuletzt als Recherche-Stand 2026-08-11 ausgewiesen; die Arbeitskopie enthält spätere Updates (u. a. 2026-09-16/10-02) in Hardware-/README-Material.
- **Ursprung:** preThesis/02-entscheidungen/widersprueche.md:1-4; preThesis/02-entscheidungen/open-questions.md:7-11; preThesis/05-hardware/hardware.md:32-34; Development/system/coding/bringup-zephyr/README.md:1-160
- **Status:** confirmed
- **Zitat nötig:** nein

## U101 — parameter / Implementierung

- **Aussage:** Firmware README documents 16 kHz, stereo 32-bit I²S, 128-frame blocks (8 ms), two silent TX priming blocks (16 ms), and DMA slabs in internal SRAM.
- **Ursprung:** Development/system/coding/bringup-zephyr/README.md:15-17
- **Status:** confirmed
- **Zitat nötig:** nein

## U102 — parameter / Implementierung

- **Aussage:** Firmware README documents initial listening-filter candidates: Raw, Murmur 40–800 Hz, BPM 25–150 Hz, using second-order Butterworth high-pass/low-pass sections and 20 ms exponential crossfades; cutoffs are explicitly engineering candidates, not optimal validated values.
- **Ursprung:** Development/system/coding/bringup-zephyr/README.md:18-21
- **Status:** assumption
- **Zitat nötig:** nein

## U103 — parameter / Implementierung

- **Aussage:** Firmware README documents BPM update once per second, provisional 30–200 BPM range and quality gating.
- **Ursprung:** Development/system/coding/bringup-zephyr/README.md:22-23
- **Status:** assumption
- **Zitat nötig:** nein

## U104 — fact / Implementierung

- **Aussage:** Firmware README states BPM analysis uses newly captured samples at the original sample rate; lung mode is live Raw listening without BPM, replay or FHIR.
- **Ursprung:** Development/system/coding/bringup-zephyr/README.md:43-44
- **Status:** confirmed
- **Zitat nötig:** nein

## U105 — fact / Systemarchitektur

- **Aussage:** Firmware README separates display, audio and optional network work into threads; input events do not wait for full-screen redraw, and failed GPIO event delivery retries.
- **Ursprung:** Development/system/coding/bringup-zephyr/README.md:48-49
- **Status:** confirmed
- **Zitat nötig:** nein

## U106 — parameter / Systemarchitektur

- **Aussage:** Firmware README gives default GPIO mapping for the filter switch as positions Raw/Murmur/BPM on GPIO 18/21/38; mapping is explicitly tied to evaluation carrier wiring.
- **Ursprung:** Development/system/coding/bringup-zephyr/README.md:64-83
- **Status:** confirmed
- **Zitat nötig:** nein

## U107 — fact / Implementierung

- **Aussage:** Firmware README states configuration and tokens remain in RAM, FHIR sending requires valid recent BPM and a low-priority worker issues TLS PUT to HAPI-FHIR; server readback is used as evidence.
- **Ursprung:** Development/system/coding/bringup-zephyr/README.md:227-262
- **Status:** confirmed
- **Zitat nötig:** nein

## U108 — method / Evaluation/Methodik

- **Aussage:** Firmware README says software diagnostics count 8 ms deadline misses and RX/TX/allocation failures, but slab use is not exact hardware FIFO depth; end-to-end acoustic/electrical latency must be measured separately.
- **Ursprung:** Development/system/coding/bringup-zephyr/README.md:217-222
- **Status:** confirmed
- **Zitat nötig:** nein

## U109 — method / Evaluation/Methodik

- **Aussage:** EVAL-GUIDE labels filter coefficients and BPM thresholds as initial evaluation candidates rather than optimality claims, and distinguishes earlier confirmed wiring from acceptance of new firmware.
- **Ursprung:** Development/system/coding/bringup-zephyr/EVAL-GUIDE.md:8-17
- **Status:** confirmed
- **Zitat nötig:** nein

## U110 — requirement / Evaluation/Methodik

- **Aussage:** EVAL-GUIDE sets engineering acceptance targets: measured live latency <30 ms; provisional BPM MAE ≤5 BPM with ≥90% valid windows on defined clean fixtures; playback retained pitch within 2% at 440 Hz; physical input response ≤35 ms.
- **Ursprung:** Development/system/coding/bringup-zephyr/EVAL-GUIDE.md:67-79
- **Status:** assumption
- **Zitat nötig:** nein

## U111 — requirement / Evaluation/Methodik

- **Aussage:** EVAL-GUIDE requires >=10 minutes of combined operation, zero audio processing deadline misses and >=25% stack headroom in every thread/ISR; TLS included if configured.
- **Ursprung:** Development/system/coding/bringup-zephyr/EVAL-GUIDE.md:81-98
- **Status:** assumption
- **Zitat nötig:** nein

## U112 — method / Evaluation/Methodik

- **Aussage:** EVAL-GUIDE notes host timing is not MCU CPU-load evidence and static memory-fit/linking does not establish heap peaks or runtime stack headroom.
- **Ursprung:** Development/system/coding/bringup-zephyr/EVAL-GUIDE.md:38-43,93-98
- **Status:** confirmed
- **Zitat nötig:** nein

## U113 — measurement / Evaluation/Methodik

- **Aussage:** TEST-PROTOCOL historical result: button/LED passed; fitted switch was only two-position (3PDT) and could not exercise the intended third position.
- **Ursprung:** Development/system/coding/bringup-zephyr/TEST-PROTOCOL.md:1432-1434
- **Status:** confirmed
- **Zitat nötig:** nein

## U114 — measurement / Evaluation/Methodik

- **Aussage:** TEST-PROTOCOL historical result: potentiometer measured 0–3083 mV monotonic; display/backlight was partial because touch generated several events per tap and audio stopped at first display redraw.
- **Ursprung:** Development/system/coding/bringup-zephyr/TEST-PROTOCOL.md:1436-1437
- **Status:** confirmed
- **Zitat nötig:** nein

## U115 — measurement / Evaluation/Methodik

- **Aussage:** TEST-PROTOCOL historical result: INMP441 microphone peak tracked real sound (81–32643) with zero errors over 30 s on documented pins.
- **Ursprung:** Development/system/coding/bringup-zephyr/TEST-PROTOCOL.md:1439
- **Status:** confirmed
- **Zitat nötig:** nein

## U116 — measurement / Evaluation/Methodik

- **Aussage:** TEST-PROTOCOL historical result: PCM5102A passed I²S probe only; write-only I²S accepts a block even when module is unplugged, so this did not prove audible jack output.
- **Ursprung:** Development/system/coding/bringup-zephyr/TEST-PROTOCOL.md:1440
- **Status:** confirmed
- **Zitat nötig:** nein

## U117 — measurement / Evaluation/Methodik

- **Aussage:** TEST-PROTOCOL marked full assembly skipped because of the then-existing display/audio defect; later protocol sections record corrective findings and a subsequent no-board run where T00–T10 were blocked for lack of flash/physical measurements.
- **Ursprung:** Development/system/coding/bringup-zephyr/TEST-PROTOCOL.md:1442,1499-1513
- **Status:** confirmed
- **Zitat nötig:** nein

## U118 — measurement / Implementierung

- **Aussage:** TEST-PROTOCOL diagnosis: 240×320×2-byte screen fill at 10 MHz takes about 120 ms, exceeding audio RX ring budget and causing I²S error state; recovery work was identified.
- **Ursprung:** Development/system/coding/bringup-zephyr/TEST-PROTOCOL.md:1468-1471
- **Status:** confirmed
- **Zitat nötig:** nein

## U119 — risk / Evaluation/Methodik

- **Aussage:** EVAL-GUIDE says no integrated physical test was performed for the later firmware evaluation and records inherited wiring confirmation only; no new-firmware acceptance should be inferred.
- **Ursprung:** Development/system/coding/bringup-zephyr/EVAL-GUIDE.md:13-17,117-120
- **Status:** confirmed
- **Zitat nötig:** nein

## U120 — risk / Diskussion/Ausblick

- **Aussage:** README distinguishes wiring confirmation dated 2026-09-16 from later speed-switch and SD-card mapping; Rev A speed switch GPIO2/39/47 is in default build but not covered by that wiring confirmation.
- **Ursprung:** Development/system/coding/bringup-zephyr/README.md:3-8,64-83
- **Status:** confirmed
- **Zitat nötig:** nein

## U121 — method / Evaluation/Methodik

- **Aussage:** EVAL-GUIDE host comparison can hold analysis filter fixed while changing listening filter, or use matched analysis/listening variants; matched mode changes two variables and must be interpreted accordingly.
- **Ursprung:** Development/system/coding/bringup-zephyr/EVAL-GUIDE.md:31-35
- **Status:** confirmed
- **Zitat nötig:** nein

## U122 — method / Evaluation/Methodik

- **Aussage:** EVAL-GUIDE says synthetic pulses alone cannot establish physiological accuracy and recommends licensed heart-sound recordings with synchronized reference annotations; digital injection isolates software while controlled acoustic playback exercises the assembled capture chain.
- **Ursprung:** Development/system/coding/bringup-zephyr/EVAL-GUIDE.md:45-50
- **Status:** confirmed
- **Zitat nötig:** nein

## U123 — risk / Diskussion/Ausblick

- **Aussage:** EVAL-GUIDE says the INMP441 usable low-frequency band is a hardware constraint; separate listening/analysis branches allow shared-vs-separate filter comparison but do not establish improved clinical recognition.
- **Ursprung:** Development/system/coding/bringup-zephyr/EVAL-GUIDE.md:153-157
- **Status:** confirmed
- **Zitat nötig:** nein

## U124 — parameter / Implementierung

- **Aussage:** The evaluation protocol describes an eight-second rectified-envelope autocorrelation window with updates each second; host reports include MAE, RMSE, bias, maximum error and valid-window coverage after acquisition.
- **Ursprung:** Development/system/coding/bringup-zephyr/README.md:22-24
- **Status:** confirmed
- **Zitat nötig:** nein

## U125 — measurement / Evaluation/Methodik

- **Aussage:** Hardware report historic 2026-08 test had no verified end-to-end loopback, audible DAC output, or simultaneous full assembly; the microphone itself passed the reported 30-second input test.
- **Ursprung:** Development/system/coding/bringup-zephyr/TEST-PROTOCOL.md:1439-1449
- **Status:** confirmed
- **Zitat nötig:** nein

## U126 — requirement / Evaluation/Methodik

- **Aussage:** The evaluation protocol requires server readback to match Patient, LOINC, quantity, unit, timestamp and resource ID; TLS negative cases must not transfer successfully, audio must continue, and retry is explicit.
- **Ursprung:** Development/system/coding/bringup-zephyr/EVAL-GUIDE.md:84-85
- **Status:** confirmed
- **Zitat nötig:** nein

## U127 — measurement / Evaluation/Methodik

- **Aussage:** Integrated build evidence dated 2026-09-24 records PASS for offline, QC and network-QC/second-switch ESP32-S3 builds with zero application compiler warnings; network-QC used 334,320 bytes internal DRAM segment and 2,089,472 bytes external DRAM window.
- **Ursprung:** Development/system/coding/bringup-zephyr/evidence/integrated-build-results.json:1-200
- **Status:** confirmed
- **Zitat nötig:** nein

## U128 — measurement / Evaluation/Methodik

- **Aussage:** Integrated host evidence records 73 passing tests for portable C DSP/FHIR functions, evaluation CLI and Python HTTPS readback (explicitly not the on-device TLS stack); Zephyr native_sim logic has 10 passing tests.
- **Ursprung:** Development/system/coding/bringup-zephyr/evidence/integrated-build-results.json:1-200
- **Status:** confirmed
- **Zitat nötig:** nein

## U129 — measurement / Evaluation/Methodik

- **Aussage:** Hardware-results evidence for commit 2cd6d4c (2026-08-14) records 4 PASS, 4 PARTIAL, 3 BLOCKED cases; record is retrospective and lacks flashed-binary hash.
- **Ursprung:** Development/system/coding/bringup-zephyr/evidence/hardware-results.json:1-200
- **Status:** confirmed
- **Zitat nötig:** nein

## U130 — measurement / Evaluation/Methodik

- **Aussage:** Hardware-results evidence for commit 418f9ba (2026-08-19) records all 11 physical cases BLOCKED because no board was attached/flashed; compile/simulation is not physical acceptance.
- **Ursprung:** Development/system/coding/bringup-zephyr/evidence/hardware-results.json:1-200
- **Status:** confirmed
- **Zitat nötig:** nein

## U131 — measurement / Evaluation/Methodik

- **Aussage:** Wiring-confirmation JSON records a user statement dated 2026-09-16 about the existing evaluation assembly; it has no board revision, captures or flashed-image hash and does not cover second-switch extension or new-firmware acceptance.
- **Ursprung:** Development/system/coding/bringup-zephyr/evidence/wiring-confirmation.json:1-10
- **Status:** confirmed
- **Zitat nötig:** nein

## U132 — method / Evaluation/Methodik

- **Aussage:** hardware-results.schema.json requires schema_version and records_by_firmware_commit, organizing hardware verdicts by firmware commit.
- **Ursprung:** Development/system/coding/bringup-zephyr/evidence/hardware-results.schema.json:1-100
- **Status:** confirmed
- **Zitat nötig:** nein

## U133 — measurement / Evaluation/Methodik

- **Aussage:** logic-tests.txt records 10 passing app_logic cases covering audio recovery, brightness, degraded-mode decisions, error handling, probe/retry transitions, status formatting, switch decoding and touch color transitions.
- **Ursprung:** Development/system/coding/bringup-zephyr/evidence/logic-tests.txt:1-40
- **Status:** confirmed
- **Zitat nötig:** nein

<!-- created by GPT-6-Luna on behalf of Nico running in T3 Code through Codex. -->
