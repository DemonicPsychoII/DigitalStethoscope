# Offene Punkte / To clarify — vor Finalisierung der Aufgabenbeschreibung

> Zum Annotieren: pro Punkt eigene Entscheidung/Notiz unter **→** ergänzen. Status: [ ] offen · [x] geklärt

> Zum Annotieren von human-only, nutze ein '>' ohne pfeil unter dem eignentlichen **→** Notiz-Feld

> **Recherche-Stand 2026-08-11:** Zu den faktischen Punkten wurden 12 Recherchen gefahren. Die
> Ergebnisse stehen unter **→ R##** in Kurzform; die vollständigen Berichte mit allen Quellen liegen
> in `../03-recherche/R##-*.md`. Die Recherche liefert Entscheidungsgrundlagen — die Häkchen bleiben offen,
> bis du bzw. der Betreuer entschieden habt. Punkte ohne Recherche sind als *Entscheidungspunkt*
> markiert: dort gibt es nichts nachzuschlagen.

 ## 1. Wissenschaftlicher Kern & Nachweisführung

  

- [ ] **Objektive Murmur-Metrik definieren:** Was genau ist „Murmur-Detektierbarkeit"? SNR im Murmur-Band, Spektralkontrast, Envelope-Kennwert? Vorab festlegen, sonst ist der Nachweis angreifbar.

  → **R01** (`../03-recherche/R01-murmur-metrik.md`): Es gibt **keine einzelne normierte Kennzahl**. Für einen
  Filtervergleich auf *identischem* Eingangsmaterial sind drei Größen am besten geeignet und sollten
  gemeinsam berichtet werden:
  1. **Bandbegrenzte Murmur-SNR** (gepaarte Differenz):
     `SNR_M = 10·log10( Σ_Ws x_B²[n] / ( |Ws|/|Wd| · Σ_Wd x_B²[n] ) )`
     mit `x_B` = im Murmurband bandpassgefiltertes Signal, `Ws` = systolisches Murmurfenster (S1→S2),
     `Wd` = diastolisches Referenzfenster ohne S1/S2.
  2. **Murmur-zu-S1/S2-Energieverhältnis** `E_M/(E_S1+E_S2)`.
  3. **Envelope-Kontrast** (Hüllkurvenenergie Murmurfenster vs. diastolische Referenz).

  **Kritisch:** Die Zeitfenster müssen für beide Filter **identisch** aus *einer* Referenzsegmentierung
  stammen. Wird pro Filter neu segmentiert, beeinflusst der Filter Messgröße und Segmentierung
  gleichzeitig — der Nachweis wäre wertlos.

  Bandgrenzen aus der Literatur: **25–400 Hz** für viele Murmuranalysen, 20–500 / 20–800 Hz für
  breitere PCG-Analysen. Eine bloße Verbesserung des **breitbandigen** SNR oder der RMS-Amplitude
  beweist ausdrücklich **nicht**, dass ein Murmur besser detektierbar ist.

> Für die Thesis abgespeckt bedeutet das Murmor-Detektieren ein 'Ist es da / nicht da?' auf Basis von ~n=5-10 Test-Hörern, darunter normale Software-Entwickler sowie medizinisch geschulte Personen. Dazu wichtig ist das Auswählen von Test-Audiodateien bei denen die Lage nicht eindeutig ist, also die Murmurs nicht offensichtlich sind.

- [ ] **Referenz / Ground Truth:** Woher kommen Signale mit *bekanntem* Murmur (Simulator/Trainingsherz, annotierte Datenbank z. B. PhysioNet, echte Patienten)?

  → **R02** (`../03-recherche/R02-ground-truth.md`): **CirCor DigiScope v1.0.3** (PhysioNet) ist die klar beste
  öffentliche Quelle — 1.568 Personen, 5.272 Aufnahmen, **4 kHz**, Lizenz **ODC-By 1.0**, kein
  Credentialing. Annotiert sind Murmur present/absent/unknown, Lokalisation (PV/TV/AV/MV/Phc),
  systolisch/diastolisch, Timing, Form, Tonhöhe, Qualität **und Grad**, dazu S1/S2-Segmentierung als TSV.
  *Einschränkung:* pädiatrische Kohorte (0–21 Jahre) — in der Arbeit erwähnen.

  **PhysioNet/CinC 2016** (3.126 Aufnahmen, 2 kHz) hat nur normal/abnormal und ist als Murmur-Ground-Truth
  **nicht** geeignet.

  Simulatoren: Sakamoto ~9.092 USD, SAM Basic ~3.750 USD, PAT Basic ~2.200 USD — für die Arbeit zu teuer.
  Bezahlbare Option: **3B Scientific Hand-Held Auscultation Trainer** + Murmur-Soundkarte (16 Murmurs)
  für ~£227. Empfehlung: CirCor als Hauptdatensatz, Simulator nur optional für reproduzierbare
  Kopplungstests am realen Bruststück.

> Daten aus einer solchen Datenbank oder aus einer Studie sind für die Thesis ausreichend, minimieren Aufwand und bei Playback Funktionalität auch zeitlich realistisch.

- [ ] **BPM-Referenz:** Vergleichsbasis für BPM-Genauigkeit (EKG, Referenz-Stethoskop, annotierter Datensatz)? Zielgenauigkeit (± x BPM) festlegen.

  → **R03** (`../03-recherche/R03-bpm-referenz.md`): Referenz ist das **synchron aufgezeichnete EKG** (R-Zacken,
  R-R-Intervalle) — Goldstandard. Auswertung über **Bland-Altman** plus MAE/MAPE.
  - **Mindestziel:** ±10 % oder ±5 bpm, je nachdem was größer ist (Toleranz aus ANSI/AAMI EC13 und
    IEC 60601-2-27).
  - **Ambitioniertes Ziel:** MAE ≤5 bpm, MAPE ≤5 % in Ruhe, ≥95 % innerhalb der vorab definierten
    Übereinstimmungsgrenzen.

  **Caveat für die Formulierung:** Beide Normen gelten ausdrücklich für **EKG-basierte Monitore**, nicht
  für PCG-Geräte. Die Toleranz darf als begründete Zielgröße verwendet, aber nicht als
  Konformitätsaussage formuliert werden.

> BPM-Referenz ist noch nicht festgelegt, aber ein Vergleich mit einem Pulsoxy oder Smartwatch ist realistisch und möglich. EKG wäre die beste Referenz, ist aber aufwendig und sehe ich nicht zwingend als nötig (genauigkeit-wise).

- [ ] **Erfolgskriterium für Q2:** Ab welchem Unterschied gilt „die zwei Filter unterscheiden sich zweckabhängig" als belegt? Schwelle/Effektgröße vorab definieren.

  → **R01, Abschnitt 7** (`../03-recherche/R01-murmur-metrik.md`): Es existiert **keine belegte dB-Schwelle**
  dafür, ab wann ein Filter „besser" ist. Die Literatur gibt nur Kontextwerte (z. B. 14 dB SNR für
  Zeitbestimmung — ausdrücklich *keine* Detektierbarkeitsschwelle). Ein Satz wie „1 dB Unterschied ist
  klinisch relevant" wäre nicht haltbar.

  Tragfähiges Vorgehen stattdessen:
  - **eine primäre Metrik vorab einfrieren** (Vorschlag: bandbegrenzte Murmur-SNR), Rest als sekundär;
  - gepaarter Test über alle Signale: **Wilcoxon-Vorzeichen-Rang** (nichtparametrisch, robust bei kleinem n);
  - **Effektgröße** Cohen's `d_z` bzw. rank-biseriale Korrelation **mit Konfidenzintervall** berichten;
  - bei mehreren Bändern/Metriken **Holm-Bonferroni** korrigieren.

  Für „zweckabhängig unterschiedlich" ist die saubere Formulierung eine **Interaktion**: Filter A gewinnt
  im tieffrequenten Band, Filter B im höherfrequenten — nicht „A ist besser als B".

> Ein Filter ist 'besser', wenn der Hörende die Murmurs mit mehr Sicherheit erkennt und hört, also die Detektierbarkeit und die Konfidence höher ist.
> Beim BPM Filter heißt besser, dass die Genauigkeit der Messung höher sowie Störgeräusche und Ausreißer geringer sind.

- [ ] **Q3 Wiedergabegeschwindigkeit:** Welche Faktoren (0,5× / 0,75×)? Pitch-Shift-Problem — langsameres Abspielen verschiebt Frequenzen aus dem diagnostischen Band. Time-Stretch ohne Tonhöhenänderung nötig? Rechenaufwand on-device?

  → **R04** (`../03-recherche/R04-time-stretch.md`): Time-Stretch ohne Tonhöhenänderung ist **sinnvoll, aber als
  Hörhilfe zu deklarieren**, nicht als diagnostisch validiertes Verfahren. Originalgeschwindigkeit muss
  parallel verfügbar bleiben, weil die zeitlichen Verhältnisse (S1–S2-Abstand, Systolen-/Diastolendauer)
  auseinandergezogen werden.

  **Verfahren: WSOLA** (bzw. transientenmodifizierte Variante), nicht Phase-Vocoder — S1/S2 sind kurze
  transiente Ereignisse, für die der Phase-Vocoder artefaktanfälliger ist.

  **Rechenaufwand auf dem ESP32-S3 ist unkritisch:** WSOLA grob 20–50 Mio. Zyklen/s ≈ **8–21 % eines
  240-MHz-Kerns**. Phase-Vocoder (512-pt Float-FFT, 8 kHz, 25 % Hop) ~10–30 Mio. Zyklen/s, aber mehr RAM
  und höhere Latenz. Der kritische Punkt ist die Qualität und die Echtzeitpufferung, nicht die Rechenleistung.

> Die Wiedergabegeschwindigkeit ist ein Feature, welches vor allem bei hohen Frequenzen (BPM) und bei Murmurs die Erkennung erleichtert. Es ist keine Anforderung zu beweisen, dass es tatsächlich Medizinisch relevant ist, sondern dass es die Erkennung erleichtert.
 

## 2. Pilot-Hörstudie (Machbarkeit)

 

- [ ] **Teilnehmer:** Laien oder medizinisch Geschulte? Bei Laien fraglich, ob Murmur-Erkennung aussagekräftig ist.

  → **R05** (`../03-recherche/R05-hoerstudie-design.md`): **Laien sind vertretbar**, wenn die Aufgabe als
  **Diskrimination** und nicht als Diagnose gestellt wird — also ABX/2AFC („klingt A oder B anders?" /
  „in welchem Signal ist das Geräusch hörbar?") statt „welche Klappenerkrankung liegt vor?".

  Belegt: In der Auskultationsliteratur korreliert die **diagnostische** Fähigkeit mit klinischer Erfahrung,
  die reine **Unterscheidung** Herzgeräusch vs. normaler Herzton dagegen nicht. Genau diese Unterscheidung
  ist die für Q2 relevante Größe.

> Beide, ein mal Entwickler aus meiner Abteilung und Medizinstudenten und Ärzte mit Erfahrung. Davor kurze Einführung in wie sich ein Murmur anhört sodass alle die gleiche Basis haben. Fragen werden rein vorhanden / nicht vorhanden und Sicherheitsskala sein. Keine Diagnose, keine Klassifikation.

- [ ] **Ethik / Datenschutz:** Braucht die THA ein Ethikvotum / Einwilligung? Patientendaten oder nur synthetische/aufgezeichnete Signale?

  → **R06** (`../03-recherche/R06-ethik-datenschutz.md`): **Wahrscheinlich kein förmliches Ethikvotum nötig**,
  sofern ausschließlich gesunde, einwilligungsfähige Erwachsene teilnehmen, das Risiko minimal ist und
  keine eigenen Patientendaten erhoben werden. Trotzdem: **dokumentierte ethische Selbsteinschätzung durch
  den Betreuer + Anfrage bei der zuständigen THA-Stelle bzw. der GEHBa vor Studienbeginn.**

  Datenschutz:
  - **vollständig anonymisierte** Aufnahmen fallen aus der DSGVO heraus;
  - **pseudonymisierte / nur de-identifizierte** Aufnahmen bleiben personenbezogen;
  - Herzschall kann zusätzlich **Gesundheitsdatum nach Art. 9 DSGVO** sein;
  - bei PhysioNet-Daten kommt die **Lizenz** (ODC-By 1.0) als eigenständige Pflicht hinzu.

  Der Weg „nur öffentliche Datenbank + synthetische Signale, keine eigenen Aufnahmen" reduziert den
  Aufwand erheblich und ist die empfohlene Variante.

> Aktuelle Einschätzung: nein, zu aufwändig und unnötig wenn man auf die richtigen Lizenzen achtet kann man die Kopfschmerzen direkt umgehen.

- [ ] **Studiendesign:** Blindung, Randomisierung der Filterkonditionen, Anzahl Stimuli, Auswertung (bei n ≈ 5–10 nur explorativ). Reicht „unterstützend" dem Betreuer?

  → **R05** (`../03-recherche/R05-hoerstudie-design.md`): Sauberstes Design ist ein **verblindetes, randomisiertes,
  within-subject ABX- oder 2AFC-Hörexperiment** mit mehreren unabhängigen Aufnahmen, kontrollierter
  Lautheit, neutralen Stimuluscodes, kurzen Übungsdurchgängen und Pausen.

  Auswertung bei n = 5–10: **Rohdaten, individuelle Trefferquoten, Mediane, Effektgrößen und exakte
  Unsicherheitsintervalle**. Formale p-Werte höchstens ergänzend und ausdrücklich als explorativ
  gekennzeichnet.

  Die Studie muss von Anfang an als **explorative Hör- und Machbarkeitspilotstudie** deklariert werden —
  nicht als Nachweis klinischer Überlegenheit. Das ist zugleich die Antwort auf „reicht unterstützend":
  ja, aber nur wenn der Anspruch entsprechend formuliert ist. *(Ob dem Betreuer das genügt, bleibt
  abzustimmen.)*

> Die Studie ist nur unterstützend, um die Filter zu validieren. Es ist keine klinische Studie und soll auch nicht als solche verstanden werden. Es geht nur darum, dass die Filter die Murmurs besser hörbar machen und die BPM Messung genauer ist. Und ob man bei der BPM verstärkung die Murmurs überhaupt noch hört oder ob der gleiche Filter für beides hergenommen werden kann. Die Studie ist nur ein kleiner Teil der Arbeit und soll die Filter validieren, nicht klinisch bewerten.

- [ ] **Fallback:** Was, wenn die Studie ausfällt? Ist der objektive Teil allein tragfähig?

  → *Entscheidungspunkt — keine Recherche.* Hängt an der Abstimmung mit Betreuer/Firma. Randnotiz aus
  R01/R05: Der objektive Teil (Q1/Q2 über Metriken auf CirCor-Daten) ist methodisch eigenständig und
  benötigt die Hörstudie nicht, solange die Arbeit keine Aussage zur *wahrgenommenen* Hörbarkeit trifft.

> Ein funktionierendes Gerät ist das zentrale Thema, danach die Filter-Validierung sowie die BPM via FHIR Kommunikation. Zur not wird die Studie gestrichen um die Funktionalität zu gewährleisten.

 

## 3. Hardware & Akustische Kette

 

- [ ] **Bruststück-Kopplung:** Wie wird das analoge Bruststück akustisch/mechanisch an das MEMS-Mikrofon gekoppelt? Bestimmt Q1 maßgeblich, Baurisiko.

  → **R07** (`../03-recherche/R07-bruststueck-mems.md`): Empfohlener Aufbau — **Membran des Bruststücks behalten**,
  auf der hautabgewandten Seite eine **sehr kleine, abgedichtete Mikrofonkammer**, MEMS-Mikrofon
  **direkt hinter der Membran**, akustischer Weg kurz und mit großem Querschnitt. **Kein langer Schlauch.**

  Wichtigste Erkenntnis zur Helmholtz-Resonanz: Eine kleine Kammer erzeugt **keine** tiefe Resonanz — für
  20 Hz wäre bei üblichen Halsabmessungen ein Volumen von ca. **21 ml** nötig, konstruktiv groß und stark
  verfärbend. Richtige Strategie ist deshalb, die Resonanz **aus dem Band 20–600 Hz heraus nach oben** zu
  legen: Kammer klein, kurz und gut bedämpft.

  **Leckage ist der kritische Baufehler** — bei höheren Frequenzen kaum sichtbar, dämpft aber 20–40 Hz
  deutlich. Die in der Literatur dokumentierte Einfachvariante (5 cm Schlauch, 6 mm Innendurchmesser,
  Kondensatormikrofon) ist unterhalb 60 Hz nicht optimal.

> Das Mikrofon wird an die Öffnung von Membran -> Hohlraum -> Schlauchöffnung = Mikrofon gekoppelt. Dadurch dass das Physische Bruststück erhalten bleibt und man zwischen 2 Bauformen durch Drehen wechseln kann, kann man dadurch die gesamte Origial-Funktionalität des Stethoskopes beibehalten und bei Zeit vergleichen.

- [ ] **MEMS-Auswahl:** Genügt die untere Grenzfrequenz für die S3/S4-Bande (~20–60 Hz)? Konkretes Bauteil fixieren oder als offen kennzeichnen.

  → **R07** (`../03-recherche/R07-bruststueck-mems.md`): **Achtung — die naheliegenden Standardteile fallen durch.**
  `LFRO` = unterer −3-dB-Punkt relativ zu 1 kHz.

  | Bauteil | Ausgang | LFRO | SNR | Eignung 20 Hz |
  |---|---|---:|---:|---|
  | TDK ICS-40180 | analog | 60 Hz | 65 dBA | **nein** |
  | TDK ICS-43434 | I²S | 60 Hz | 64 dBA | **nein** |
  | Knowles SPH0645LM4H-1 | I²S | 45 Hz | 65 dB(A) | **nein** |
  | Infineon IM69D130 | PDM | 28 Hz | 69 dB(A) | bedingt |
  | Knowles SPH0655LM4H-1 | PDM | 25 Hz | 66 dB(A) | gut |
  | **Knowles SPK18R1LM4H-1 „Hyperion"** | PDM | **20 Hz** | 70,5 dB(A) | **sehr gut** |
  | **Knowles SPK01A0LR5H-1 „Raptor"** | analog | **17 Hz** | 72 dB(A) | **sehr gut** |
  | **Infineon IM68A130** | analog | **10 Hz** | 68 dB(A) | **sehr gut** |

  **Beschaffungsabwägung:** Der IM69D130 hat als einziger Kandidat ein bequemes Fertigboard
  (Shield2Go mit ADAU7002, PDM→I²S), liegt bei 20 Hz aber schon im Abfall. Die Knowles-Typen sind
  akustisch besser, kommen aber nur als Flexboard/Muskie-Evalsystem — Lieferzeit und Lötbarkeit vorab prüfen.
  Der SPH0645 (verbreitetstes I²S-Hobbymodul) scheidet mit 45 Hz aus.

> Bereits vorhanden ist INMP441 auf einem Breakout Board. Mit den Limitationen umzugehen und diese zu evaluieren kann hier ein Teil der Arbeit sein.

- [ ] **Messmethode Q1:** Charakterisierung der akustischen Kette (Kalibrierlautsprecher, Sweep, Referenzmikrofon)? Equipment-Verfügbarkeit?

  → **R08** (`../03-recherche/R08-messmethode-akustik.md`): **Es existiert keine verbindliche akustische Produktnorm
  für elektronische Stethoskope** — das ist in der Literatur ausdrücklich festgestellt und sollte in der
  Arbeit so zitiert werden, statt eine Norm zu suggerieren.

  Empfohlene Minimalvariante (hochschulüblich beschaffbar):
  `Lautsprecher → kleiner abgedichteter Koppler → Bruststück → MEMS → ADC`,
  Schalldruck **unmittelbar am Bruststückeingang** mit kalibriertem Referenzmikrofon gemessen;
  Übertragungsfunktion = Stethoskopsignal / Referenzsignal. Anregung als **ESS-Sweep mit Deconvolution**
  über **10–1000 Hz**.

  Kein Freifeldaufbau (Stethoskop einfach vor einen Lautsprecher halten) — nicht reproduzierbar.
  Shaker + Kunstbrustkorb wäre bezüglich mechanischer Ankopplung realistischer, aber deutlich aufwendiger.

> Keine spezifische Messmethode festgelegt und wird auch nicht festgelegt werden, da die Messung der akustischen Kette nicht zwingend notwendig ist, um die Filter zu validieren. So lange der Ton hörbar ist und man die Herz-sounds hört ist es ausreichend. Die Studie nimmt eh voraufgenommene und wieder abgespielte Sounds um Komplexität zu reduzieren, sodass eine kompletten Ketten-Eval den Rahmen noch weiter sprengen würde.

- [ ] **DAC / Kopfhörer-Pfad:** Latenz-Ziel für „Echtzeit" quantifizieren (z. B. < 30 ms end-to-end).

  → **R09** (`../03-recherche/R09-latenz.md`): **Zielwert ≤10 ms end-to-end, Entwicklungsziel ≤5 ms.**
  Ab ca. 10–15 ms wird die Verzögerung bemerkbar, ab ~15–30 ms als störend beschrieben. Die in der
  Aufgabenstellung angedachten 30 ms wären also **zu großzügig**.

  Budgetierung: Jede A/D- bzw. D/A-Wandlung kostet typisch 1–1,5 ms. Ein Bluetooth-Pfad scheidet damit
  praktisch aus. Offizielle Latenzangaben von 3M Littmann CORE/3200 oder Eko sind **nicht öffentlich
  auffindbar** — kein Vergleichswert zitierbar.

> Latenz festlegung ist wichtig, bei 0.5x Wiedergabegeschwindigkeit ist die Latenz nicht mehr relevant, da man die Zeit hat, um die Wiedergabe zu hören. Bei 1x Wiedergabegeschwindigkeit wäre die Idee nach den bekannten Werten <30ms, besser <10ms zu gehen (erneute Recherche dazu wäre sinnvoll).
 

## 4. Software / Plattform

 

- [ ] **C vs. Zephyr:** Entscheidung auf AP 1.2 vertagt — Entscheidungskriterien vorab notieren; spätes Umschwenken verschiebt AP 2.x.

  → **R10** (`../03-recherche/R10-esp32-plattform.md`): Klare Empfehlung **ESP-IDF (C/FreeRTOS)**. Zephyr ist auf
  dem ESP32-S3 grundsätzlich nutzbar (Board, Kernel, Netzwerk, mbedTLS, generischer I²S-Treiber), aber
  genau bei der hier nötigen Kombination — **PDM-Audio + Audio-DMA + WiFi + TLS + esp-dsp** — deutlich
  risikoreicher. Da ein spätes Umschwenken AP 2.x verschiebt, spricht das für eine frühe Festlegung auf
  ESP-IDF statt für eine Vertagung auf AP 1.2.

> Probeweise vor Thesis-Start mit Zephyr Tests durchführen. Finale Entscheidung zu Thesis Beginn

- [ ] **Rechenbudget:** Passen 3 Filter + BPM + Time-Stretch + TLS gleichzeitig in Echtzeit auf den ESP32-S3? Frühe CPU/RAM-Abschätzung.

  → **R10** (`../03-recherche/R10-esp32-plattform.md`): **Ja, voraussichtlich** — unter fünf Bedingungen:
  blockweise Filterverarbeitung per DMA, `esp-dsp` mit ESP32-S3-optimierter Implementierung, BPM-Erkennung
  auf **heruntergesampelter Hüllkurve**, TLS/FHIR **nicht** synchron in einer hochpriorisierten Audio-Task,
  und ein **externer I²S-DAC/Verstärker** für die Wiedergabe.

  **Der Engpass ist nicht die Rechenzeit der Filter oder der BPM-Erkennung**, sondern:
  1. zusammenhängender **interner** RAM während des TLS-Handshakes,
  2. Task-/DMA-/Buffer-Planung bei gleichzeitigem WiFi-Verkehr,
  3. optional die Last des Time-Stretchings.

  Randbedingung: 512 KB On-Chip-SRAM; **PSRAM ersetzt den DMA-fähigen internen RAM nicht.**

> Bedingungen einhaltbar, Test sollte das auch mal investigieren vom Rechenaufwand + RAM. PCM5102A DAC ist eine eingeplante Komponente (I2S) und übernimmt die Wiedergabe. WIFI Verkehr außerhalb der live-Wiedergabe oder als Low Prio thread falls die Daten länger zum übertragen brauchen dürfen, ansonsten bei Problemen Evaluatino von Prios und Task-Management.

- [ ] **FHIR / TLS:** Zertifikatshandling auf dem ESP32 (Speicher, Uhrzeit für Zertifikatsprüfung), FHIR-Ressourcenprofil (Observation, LOINC-Code Heart rate)?

  → **R11** (`../03-recherche/R11-fhir-tls.md`): **FHIR** — `Observation` nach Core-Profil **Vital Signs** (R4 und R5
  gleiches Muster), Pflichtfelder: `status`, `category` = `vital-signs`, `code` = LOINC **8867-4**
  (Heart rate), `subject` → `Patient/…`, `effectiveDateTime`, `valueQuantity` mit
  `system = http://unitsofmeasure.org` und UCUM-Code **`/min`**. Vollständiges minimales JSON-Beispiel im Bericht.

  **TLS** — drei praktische Stolpersteine:
  1. **Systemzeit muss vor dem Handshake per SNTP gesetzt sein**, sonst schlägt die Gültigkeitsprüfung fehl
     (klassischer Boot-Reihenfolge-Fehler).
  2. **Einzelnes gepinntes Root-CA** spart Flash und Parsing-Aufwand gegenüber dem ESP-IDF-CA-Bundle; das
     Bundle ist flexibler, muss aber bei CA-Wechsel/-Ablauf gepflegt werden. Für einen festen eigenen
     FHIR-Server → pinnen.
  3. **Heap:** ESP-IDF-FAQ nennt ~**40–50 kB freien Heap** für einen stabilen Handshake. Entscheidend ist
     der freie **interne** Heap **während** des Handshakes (also bei laufender Audioverarbeitung), nicht
     der Wert nach dem Boot. → deckt sich mit dem in R10 identifizierten Engpass.

> Die FHIR-Kommunikation ist von der Firma verlangt, kann aber durch e.g. hardcoded Secret strings zur Authentifizierung abgekürzt werden. Json-Generierung und Parsing mit gemessenem BPM und anschließendem Verschicken sollte dennoch möglich sein.
 

## 5. Scope-Abgrenzung

 

- [ ] **Lungenmodus „rein interface":** Kein funktionierender Audiopfad im Lungenmodus, oder nur keine Bewertung? Präzisieren.

  → *Entscheidungspunkt — keine Recherche.* Reine Scope-Festlegung mit Betreuer/Firma.

> Lungenmodus heißt keine BPM-Messung, nur Symbole und Interface, keine anderen Filter, keine Time-Stretch Funktionalität, kein FHIR. Nur die live-wiedergabe.

- [ ] **Dreiwegeschalter vs. Potentiometer:** Was steuert das Poti (Lautstärke? Wiedergabegeschwindigkeit?) — im Bedienkonzept noch nicht eindeutig.

  → *Entscheidungspunkt — keine Recherche.* Randnotiz aus R04: Falls das Poti die Wiedergabegeschwindigkeit
  stellen soll, wäre eine **stufenlose** Verstellung beim Time-Stretch ungünstig (Neuberechnung der
  WSOLA-Parameter im laufenden Betrieb). Feste Stufen 1,0× / 0,75× / 0,5× passen besser zu einem Schalter
  als zu einem Poti.

> Poti die Lautstärke, Schalter die Wiedergabegeschwindigkeit, 2. Schalter Filter. Falls Touch bei Display einfach zu implementieren ist, kann man Konfiguration auch dorhin auslagern, sodass man das physische Bedieninterface minimiert.
> Dennoch sind genug Bautiele (potis, 3-posi-Schalter, LED-Knöpfe) vorhanden.

 

## 6. Zeit- & Aufwandsplanung

 

- [ ] **Risikoreichste APs:** Bruststück-Kopplung (AP 2.2) und Echtzeit-Audiopfad (AP 2.1) sind Zeitfresser — Puffer gezielt dorthin?

  → *Entscheidungspunkt — keine Recherche.* Randnotiz aus R07/R09/R10: Die Recherche stützt die Einschätzung.
  Zusätzlich sollte Puffer für die **MEMS-Beschaffung** eingeplant werden (Knowles-Flexboards sind kein
  Lagerartikel) und für die **TLS-/RAM-Integration**, die als eigentlicher Engpass identifiziert wurde.

> aktuell Hardware zum testen bereits vorhanden, Beschaffung sollte demnach zwar eingeplant werden, intern für mich ist es aber nur einen Puffer für Mehr Zeit.

- [ ] **Das „…" aus der Annotation:** Weitere separate Posten? (Meetings/Reviews mit Betreuer, Beschaffungs-/Lieferzeiten Hardware, Urlaub/Feiertage)

  → *Entscheidungspunkt — keine Recherche.*

> Wöchentliche Meetings, biweekly mit Prof, ... an sich alles was sonst noch anfallen kann.

- [ ] **Kalenderplan:** Onboarding + Zeitplan-Erstellung + Puffer als Termine verorten — Wochen-/Gantt-Plan ergänzen?

  → *Entscheidungspunkt — keine Recherche.* Harte Randbedingung aus R12: Bearbeitungszeit **4 Monate ab dem
  nächsten 20. des Anmeldemonats**, keine Anmeldung im August.

> Anmeldung in jedem Monat möglich, meine Anmeldung würde ich ende September anstreben, sodass die Bearbeitungszeit von 4 Monaten ab 20. Oktober läuft. Somit wäre die Abgabe Ende Januar. Puffer für Beschaffung und Testen einplanen, sodass die Abgabe nicht gefährdet ist.
> Planung folgt

 

## 7. Formales (THA)

 

- [ ] **Titel-Länge / Format:** Entspricht der Titel den THA-Vorgaben (max. Länge, deutsch/englisch)?

  → **R12** (`../03-recherche/R12-tha-formales.md`): **Keine öffentlich auffindbare THA-Regel** zu Titellänge,
  Titelsprache oder Übersetzungspflicht. Das lässt sich nicht recherchieren — **beim Prüfungsamt bzw.
  Betreuer direkt erfragen.**

  Belegt ist dagegen:
  - Anmeldung läuft **digital über das DMS**; im ersten Schritt sind **Titel und Prüfer noch nicht** anzugeben,
    der final abgestimmte Titel wird erst nach Freigabe durch das Studierendensekretariat eingetragen.
  - **Bearbeitungszeit 4 Monate**, Beginn am **nächsten 20. des Monats** nach DMS-Anmeldung.
  - **Keine Anmeldung im August möglich.**
  - Titeländerung möglich, Eintragung bis **spätestens 2 Wochen vor dem Abgabetermin**.

  ⚠ Die Fristangaben stammen teils von der **Fakultät Gestaltung**; ein Merkblatt Maschinenbau/Umwelt nennt
  abweichend **max. 5 Monate** APO-Bearbeitungszeit. Die Werte sind also **fakultätsabhängig** — für
  Elektrotechnik/Informatik unbedingt die eigene SPO und die Fakultätsseite prüfen.

> Bestätigung bereits eingegangen, nächster Schritt sind Prüfer und Titel plus Firmendokumente für die Anmeldung.

- [ ] **Betreuer-Freigabe:** Sind Q1–Q3 und die Hybrid-Bewertung mit Betreuer *und* Firma abgestimmt?

  → *Entscheidungspunkt — keine Recherche.*

> Beide wissen von der initial erarbeiteten Aufgabenbeschreibung, von beiden kam ein 'ist eigentlich so ok'
