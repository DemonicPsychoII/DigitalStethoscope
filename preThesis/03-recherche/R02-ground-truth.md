# Referenz / Ground Truth fuer Murmur-Signale

- **Run-ID:** R02-ground-truth
- **Preset:** low
- **Modell:** preset/low

## Fragestellung

```
Kontext: Bachelorarbeit, digitales Stethoskop. Es werden Herzschall-Signale mit *bekanntem* Murmur als Ground Truth benoetigt.

Hauptfrage: Welche Quellen fuer annotierte Herzschall-Signale mit bekanntem Murmur stehen fuer eine studentische Abschlussarbeit realistisch zur Verfuegung?

Unterfrage 1: Welche oeffentlichen, annotierten PCG-Datenbanken existieren (z. B. PhysioNet/CinC 2016, CirCor DigiScope 2022) - Umfang, Annotationstiefe (Murmur-Grad, Timing, Lokalisation), Abtastrate und Lizenzbedingungen fuer akademische Nutzung?
Unterfrage 2: Welche Herzschall-Simulatoren / Auskultations-Trainingsmodelle (z. B. Kyoto Kagaku, Laerdal, SimMan, guenstige Alternativen) eignen sich, um reproduzierbar definierte Murmurs akustisch am Bruststueck einzuspielen - inkl. ungefaehrer Preisklasse?

Antwort auf Deutsch, mit Links und Lizenzhinweisen.
```

## Ergebnis

## Kurzfazit

Für eine studentische Bachelorarbeit sind **zwei öffentliche Quellen besonders realistisch**:

1. **CirCor DigiScope Phonocardiogram Dataset** – mit Abstand am besten geeignet, wenn ein *bekanntes Murmur* mit klinischer Annotation benötigt wird. Es enthält Murmur-Präsenz, Auskultationsort, am besten hörbaren Ort, systolisch/diastolisch, Timing, Form, Tonhöhe, Qualität und Murmur-Grad.
2. **PhysioNet/CinC Challenge 2016** – sehr einfach zugänglich und gut für Normal-/Abnormal- oder Signalverarbeitungsaufgaben, aber **nicht geeignet**, wenn der konkrete Murmur-Typ oder sein Grad Ground Truth sein soll.

Simulatoren sind als **kontrollierte Zusatzquelle** sinnvoll. Für ein digitales Stethoskop können damit reproduzierbare Aufnahmen am realen Bruststück erzeugt werden. Sie ersetzen jedoch keine klinischen Patientendaten: Die abgespielten Geräusche sind meist Aufnahmen oder synthetische Trainingssignale, und ihre Übertragbarkeit auf echte Thoraxbedingungen muss experimentell validiert werden.

---

## 1. Öffentliche annotierte PCG-Datenbanken

| Quelle | Umfang | Annotationstiefe | Abtastrate | Lizenz / akademische Nutzung | Eignung |
|---|---:|---|---:|---|---|
| **CirCor DigiScope Phonocardiogram Dataset v1.0.3** ([PhysioNet-Link](https://physionet.org/content/circor-heart-sound/1.0.3/)) | 1.568 Personen, 5.272 PCG-Aufnahmen, Alter 0–21 Jahre, insgesamt über 33,5 Stunden; Aufnahmen 4,8–80,4 s | **Sehr hoch:** Murmur `Present/Absent/Unknown`; Murmur-Lokalisation `PV`, `TV`, `AV`, `MV`, `Phc`; am besten hörbare Lokalisation; systolisch/diastolisch; Timing; Form; Tonhöhe; Qualität; Grad. Zusätzlich S1/S2- und Systole/Diastole-Segmentierung in TSV-Dateien | In den Headern pro Patient angegeben; im Datensatz typischerweise **4.000 Hz** | **Open Data Commons Attribution License v1.0 (ODC-By 1.0)**; öffentlich zugänglich, keine Credentialing-Anforderung. Namensnennung und Einhaltung der Lizenzbedingungen erforderlich. | **Beste öffentliche Ground-Truth-Quelle für Murmurs** |
| **PhysioNet/CinC Challenge 2016 – Classification of Heart Sound Recordings** ([PhysioNet-Link](https://physionet.org/challenge/2016/)) | Rund 3.126 Aufnahmen aus fünf Datenbanken, typischerweise 5 s bis gut 120 s; Aufnahmen aus klinischen und nichtklinischen Quellen, einzelne präcordiale Ableitung | Normal/Abnormal/Unsure; aktualisierte Signalqualitätsannotation; zusätzlich automatische und handkorrigierte S1/S2-/Systole-/Diastole-Segmentierung. **Kein verlässlicher Murmur-Grad, kein standardisierter konkreter Murmur-Typ und keine detaillierte Murmur-Timingannotation** | **2.000 Hz**, WAV | **ODC-By 1.0**, öffentlich zugänglich; keine gesonderte akademische Lizenz. Challenge-Software und Challenge-Paper können zusätzliche eigene Lizenzen haben. | Gut für Klassifikation, Segmentierung und Signalqualität; **nur eingeschränkt als Murmur-Ground-Truth** |
| **PhysioNet Challenge 2022 / CirCor Challenge-Daten** ([Challenge-Seite](https://moody-challenge.physionet.org/2022/)) | Basiert auf CirCor; ein Teil der Daten wurde für Training öffentlich bereitgestellt, Challenge-Validierungs-/Testdaten waren zunächst zurückgehalten | Murmur-Präsenz und klinisches Outcome als Challenge-Aufgabe; die detaillierten CirCor-Annotationsfelder sind die wichtigere Quelle | CirCor-Dateiformat, überwiegend 4 kHz | Die konkrete Dataset-Version und deren Lizenzseite maßgeblich; für die Bachelorarbeit sollte direkt die aktuell heruntergeladene PhysioNet-Version zitiert werden | Als Benchmark relevant; für reproduzierbare Arbeit besser direkt **CirCor v1.0.3** verwenden |
| **PASCAL Classifying Heart Sounds / ähnliche kleinere Open-Heart-Sound-Sammlungen** | Kleine, heterogene Sammlungen, meist deutlich weniger Aufnahmen als CirCor oder Challenge 2016 | Häufig nur Klassen wie normal, murmur, extra heart sound; teilweise keine Patient-, Orts- oder Timingannotation | Je nach Teilquelle unterschiedlich | Lizenz ist je Teilquelle zu prüfen; bei Kopien auf Kaggle, GitHub oder Hugging Face nicht automatisch mit der Originallizenz gleichzusetzen | Nur als Ergänzung; nicht bevorzugt, wenn belastbare Murmur-Ground-Truth verlangt wird |

### CirCor im Detail

CirCor ist für die Fragestellung besonders wertvoll, weil die Annotationen nicht nur „Murmur vorhanden“ enthalten. Die Subject-Description-Dateien liefern unter anderem:

- Murmur: **Present, Absent oder Unknown**
- betroffene Auskultationsorte
- **Most audible location**
- systolisches Timing: early-, mid-, late- oder holosystolic
- systolische Form: crescendo, decrescendo, diamond oder plateau
- systolische Tonhöhe: low, medium oder high
- systolischer Grad: I/VI, II/VI oder III/VI
- systolische Qualität: blowing, harsh oder musical
- diastolisches Timing, Form, Tonhöhe, Grad und Qualität
- klinisches Outcome: Normal oder Abnormal

Die Auskultationsorte sind Pulmonal-, Trikuspidal-, Aorten- und Mitralklappenpunkt sowie `Phc` für andere Orte. Pro Aufnahmestelle existieren WAV-, Header- und TSV-Dateien. Die TSV-Dateien markieren S1, systolische Phase, S2 und diastolische Phase. Diese Annotationstiefe ist auf der offiziellen PhysioNet-Datensatzseite dokumentiert. cite[web:17]

Wichtige Einschränkung: Der Datensatz besteht überwiegend aus **pädiatrischen Aufnahmen**. Außerdem werden hohe systolische Grade ab III/VI zusammengefasst; Grade III, IV, V und VI sind also nicht getrennt. Für eine Arbeit sollte daher beispielsweise nicht behauptet werden, ein exakt getrenntes Levine-Grad-IV- oder Grad-V-Label zu besitzen. cite[web:17]

### PhysioNet/CinC 2016 im Detail

Die Challenge-2016-Daten sind mit etwa 3.126 Aufnahmen größer und sehr gut dokumentiert. Alle Aufnahmen wurden auf 2 kHz resampelt und als WAV-Dateien bereitgestellt. Verfügbar sind Normal-/Abnormal-/Unsure-Labels sowie Segmentierungen der vier Zustände S1, S2, Systole und Diastole; für den Trainingsbestand gibt es sowohl Springer-Segmentierungen als auch handkorrigierte Segmentierungen. cite[web:16]

Für die konkrete Murmur-Analyse ist die Datenbank allerdings schwächer: Die Abnormal-Klasse kann unterschiedliche Herzklappenfehler oder andere Erkrankungen umfassen, und die spezifische Pathologie beziehungsweise der Murmur-Grad ist im Datensatz nicht systematisch angegeben. cite[web:16]

### Lizenzpraktische Hinweise

Die PhysioNet-Datensätze sind nicht „frei von jeder Bedingung“. Für die genannten Datensätze gilt **Open Data Commons Attribution License v1.0**. Praktisch bedeutet das für eine Bachelorarbeit:

- Lizenztext und Datensatzversion in die Arbeit aufnehmen
- PhysioNet und die ursprüngliche Datensatzpublikation zitieren
- Herkunft und Änderungen dokumentieren
- beim Weitergeben abgeleiteter Dateien die Lizenz- und Attributionspflichten beachten
- nicht automatisch annehmen, dass ein Mirror auf Kaggle, GitHub oder Hugging Face dieselben Rechte vermittelt

PhysioNet unterscheidet grundsätzlich zwischen Open Access, Restricted Access und Credentialed Access. CirCor und Challenge 2016 sind in den genannten Versionen als öffentlich zugängliche Daten mit Lizenzbedingungen ausgewiesen. cite[web:18]

---

## 2. Herzschall-Simulatoren und Auskultations-Trainingsmodelle

### Vergleich geeigneter Systeme

| System | Reproduzierbare Murmurs am Bruststück | Typische Ausstattung | Ungefähre Preisklasse | Einschätzung für Bachelorarbeit |
|---|---|---|---:|---|
| **Kyoto Kagaku Cardiology Patient Simulator „K“ ver. 2** ([Herstellerseite](https://www.kyotokagaku.com/en/products_data/mw10/)) | Ja; Lautsprecher im Modell, Auskultation mit echtem Stethoskop; mehrere definierte Fälle und Auskultationspunkte | 88 Fälle insgesamt, darunter 14 Herzkrankheits-Simulationen und 12 normale Herzgeräuschfälle; präzise Klappen-Auskultationsorte; teilweise ECG, Pulse und Apex Beat | **Individuelles Angebot**, erfahrungsgemäß hohe fünfstellige bis sechsstellige Euroklasse möglich | Technisch sehr gut und realitätsnah, aber für eine einzelne studentische Arbeit meist nur über Skills-Lab, Hochschule oder Ausleihe realistisch |
| **Laerdal SimMan 3G/3G PLUS/ALS mit SimPad** ([SimPad-Beispiel mit Herzsounds](https://www.worldpoint.com/laerdal-simpad-plus-system-2)) | Ja, sofern das konkrete SimMan-Modell und die Software-/Soundbibliothek die benötigten Herzgeräusche enthalten | Programmierbare Herzsounds, teils ECG-synchron; Beispiele: Aortenstenose, systolisches/diastolisches Murmur, Mitralprolaps, VSD, ASD, pulmonale Stenose und weitere | Einzelkomponenten können einige tausend US-Dollar kosten; ein kompletter SimMan-Aufbau typischerweise **hohe fünfstellige bis sechsstellige Euroklasse** bzw. institutionelles Angebot | Sehr gut für klinische Simulation, aber teuer; nur sinnvoll, wenn bereits im Labor vorhanden |
| **Sakamoto Auscultation Simulator II** ([Produktseite](https://www.gtsimulators.com/products/sakamoto-auscultation-simulator-ii-m164-1-skm164)) | Ja, mit auswählbaren Herzgeräuschen und Auskultationspunkten | 20 Herzschalloptionen, darunter Aortenstenose, Mitralstenose, Mitralinsuffizienz, VSD, ASD, pulmonale Stenose, systolische und diastolische Geräusche | ungefähr **9.000–10.000 US-Dollar** | Gute kontrollierte Quelle, aber für privaten Kauf teuer; institutioneller Verleih realistischer |
| **SAM Basic Adult Auscultation Manikin** | Ja, sofern mit Soundmodul bzw. kompatibler Soundkarte erworben; echter Stethoskopkontakt | Adultes Auskultationsmodell, oft mit Bibliotheken für Herz-, Lungen- und Darmgeräusche | ungefähr **3.500–5.000 US-Dollar** bzw. etwa **3.000–5.000 Euro**, je nach Ausstattung | Einer der realistischeren professionellen Kompromisse |
| **PAT Basic Pediatric Auscultation Trainer** | Ja, mit entsprechendem Audiomodul; pädiatrischer Thorax | Pädiatrische Auskultationspunkte und Soundbibliothek | ungefähr **2.000–3.000 US-Dollar** | Interessant als Ergänzung zu CirCor, weil CirCor ebenfalls pädiatrisch ist |
| **Evo AuRA** ([Produktseite](https://elevatehealth.net/product/evo-aura-auscultation-training/)) | Ja; elektronische Wiedergabe am Stethoskop | Herz-, Lungen- und Darmgeräusche einschließlich Murmurs; digitale Pathologiebibliothek | etwa **2.995 US-Dollar** | Für ein kleineres Budget vergleichsweise interessant; vor Kauf klären, ob die konkreten Auskultationsorte und Soundausgänge für Messaufnahmen zugänglich sind |
| **3B Scientific Hand-Held Auscultation Trainer** mit Basic Murmurs Sound Card | Eingeschränkt ja; kleine, tragbare Lösung mit Soundkarte und echtem Stethoskop | Soundkarte mit **16 verschiedenen Murmur-Aufnahmen**, laut Händler aus echten Patientenaufnahmen | Trainer und Soundkarten zusammen meist etwa **einige hundert bis ca. 1.500 Euro**; die Murmur-Soundkarte wird beispielsweise mit rund £226,68 inkl. VAT angeboten | Preislich für eine studentische Vorstudie attraktiv; weniger anatomisch und weniger flexibel als ein Ganzkörpermodell |
| **Selbstbau: Lautsprecher/Exciter unter Silikon- oder Thoraxplatte** | Ja, technisch sehr gut reproduzierbar, wenn Lautstärke, Position, Last und Wiedergabedatei fixiert werden | WAV-Abspielung über Exciter, Mini-Lautsprecher oder Körperschallwandler; definierte Positionen und Pegel | ungefähr **100–1.000 Euro**, abhängig von Mechanik, Sensorik und Kalibrierung | Für eine Bachelorarbeit oft die beste Kosten-Nutzen-Lösung, aber als eigener Prüfstand zu validieren und nicht als klinischer Simulator zu bezeichnen |

Kyoto Kagaku beschreibt ausdrücklich die Wiedergabe realer Herzgeräusche, die Verwendung eines normalen Stethoskops und präzise positionierte Klappen-Auskultationsstellen. Das Modell enthält 88 Fälle und ist daher für Trainingszwecke sehr leistungsfähig. Der Hersteller veröffentlicht jedoch keinen Listenpreis, sondern verweist auf ein Angebot. cite[web:1]

Bei professionellen Modellen liegen die Preise stark auseinander. Als Orientierung werden beispielsweise ein Sakamoto-Aus­kultationssimulator mit etwa 9.092 US-Dollar, SAM Basic mit etwa 3.750 US-Dollar und PAT Basic mit etwa 2.200 US-Dollar angeboten. cite[web:4]cite[web:12] Ein deutlich günstigeres System ist ein Handheld-Trainer mit einer Soundkarte für 16 Murmurs; dort wird die Murmur-Soundkarte mit etwa £226,68 inklusive britischer Mehrwertsteuer gelistet. cite[web:3]

Laerdal-SimMan-Systeme können zahlreiche programmierbare Herzgeräusche enthalten, darunter Aortenstenose, systolische und diastolische Murmurs, Mitralprolaps, VSD und ASD. Der Preis eines SimPad-Systems allein wird beispielhaft mit 2.433 US-Dollar angegeben; der komplette SimMan-Aufbau ist deutlich teurer. cite[web:11]

---

## 3. Was ist für ein digitales Stethoskop tatsächlich empfehlenswert?

### Variante A: CirCor als Hauptdatensatz

Für eine rein datenbasierte Bachelorarbeit wäre folgende Kombination sinnvoll:

- WAV-Dateien aus CirCor verwenden
- nur `Murmur = Present` und `Murmur = Absent` als Hauptgruppen verwenden
- `Unknown` ausschließen oder separat behandeln
- Murmur-Lokalisation über `PV`, `TV`, `AV`, `MV` auswerten
- systolische und diastolische Annotation getrennt analysieren
- S1/S2-Segmentierung aus den TSV-Dateien nutzen
- Subjektweise und nicht aufnahmeweise in Training/Test aufteilen, damit Aufnahmen derselben Person nicht in beide Gruppen gelangen
- die vorhandenen Murmur-Metadaten als Ground Truth und nicht aus dem Signal selbst abgeleitete Klassen verwenden

Das ist die **realistischste öffentlich zugängliche Lösung**, wenn die Arbeit einen bekannten Murmur mit klinischer Annotation benötigt.

### Variante B: CirCor plus Simulator

Für die Validierung eines digitalen Stethoskops ist eine Kombination aus echten Daten und kontrollierter Wiedergabe besser:

1. **CirCor** für realistische, patientenbasierte Signale und klinische Annotation.
2. **Simulator oder eigener Prüfstand** für:
   - identische Wiederholungen
   - definierte Positionen
   - verschiedene Lautstärken
   - kontrolliertes Hintergrundrauschen
   - reproduzierbare Änderungen von Herzfrequenz und Signalpegel
3. Vergleich der Ergebnisse des digitalen Stethoskops mit:
   - direktem Line-out- oder Referenzmikrofonsignal
   - digitaler WAV-Originaldatei
   - Simulator-Ausgangssignal

### Variante C: Günstiger Eigenbau

Ein realistischer studentischer Aufbau wäre:

- Murmur-WAV-Datei, beispielsweise aus CirCor oder einer lizenzkonformen Soundbibliothek
- Audiointerface oder Raspberry Pi/Notebook
- kleiner Lautsprecher oder Körperschall-Exciter
- Silikon-/Kunststoffplatte oder dünne Thoraxattrappe
- definierte Bruststückpositionen
- konstante Lautstärkeeinstellung
- Referenzmikrofon oder Referenzstethoskop
- wiederholte Messung desselben Signals mindestens 10–20-mal

Damit erhält man zwar einen **reproduzierbaren technischen Prüfstand**, aber kein physiologisch vollständiges Patientenmodell. Das sollte in der Arbeit ausdrücklich als „akustischer Prüfaufbau“ oder „Phantom“ bezeichnet werden.

---

## 4. Wichtige methodische Einschränkungen

1. **Murmur-Grad ist nicht gleich akustischer Schalldruckpegel.**  
   Ein Levine-Grad II/VI beschreibt die klinische Hörbarkeit unter Untersuchungsbedingungen und kann nicht ohne Weiteres in dB SPL oder eine digitale Amplitude übersetzt werden.

2. **Auskultationsort ist nicht zwingend Signalursprung.**  
   CirCor annotiert, wo ein Murmur hörbar war beziehungsweise am stärksten gehört wurde. Das ist eine klinische Lokalisation, keine exakte physikalische Quelle.

3. **Simulator-Sounds sind keine neuen Ground-Truth-Patienten.**  
   Wenn ein Simulator eine Aortenstenose abspielt, ist die Ground Truth primär die ausgewählte Sounddatei bzw. der Fall des Simulators. Die Aufnahme am digitalen Stethoskop enthält zusätzlich Übertragungs-, Kontakt- und Raumakustikeffekte.

4. **Die Lizenz des Simulator-Soundmaterials ist separat zu prüfen.**  
   Eine kommerzielle Soundkarte oder ein Simulator darf nicht automatisch kopiert, extrahiert oder als Datensatz weiterveröffentlicht werden. Für die Arbeit sollte die Lizenz beziehungsweise eine schriftliche Hochschulfreigabe dokumentiert werden.

5. **CirCor ist überwiegend pädiatrisch.**  
   Für Aussagen über Erwachsene sollte daher zusätzlich ein erwachsener Simulator oder ein klinischer Kooperationsdatensatz eingeplant werden.

## Konkrete Empfehlung

Für die Bachelorarbeit würde ich priorisieren:

1. **CirCor DigiScope v1.0.3 als primäre öffentliche Datenquelle**
2. **PhysioNet/CinC 2016 nur ergänzend** für Segmentierung, Normal-/Abnormal-Vergleiche und Robustheitstests
3. **Eigenbau mit Lautsprecher/Exciter oder ein vorhandener SAM/PAT-/Kyoto-Kagaku-Simulator** für reproduzierbare Messungen am digitalen Stethoskop
4. Falls kein Simulator über die Hochschule verfügbar ist: **Handheld-Trainer oder eigener akustischer Phantomaufbau** statt Anschaffung eines kompletten SimMan- oder Kyoto-Kagaku-Systems

Damit sind sowohl die klinische Murmur-Annotation als auch die reproduzierbare technische Messbarkeit abgedeckt.

## Quellen

1. [Classification of Heart Sound Recordings](https://physionet.org/challenge/2016/)
2. [The CirCor DigiScope Phonocardiogram Dataset v1.0.3](https://physionet.org/content/circor-heart-sound/1.0.3/)
3. [PhysioNet Databases](https://www.physionet.org/about/database/)
4. [PhysioNet/CinC Challenge 2016: Training Sets](https://archive.physionet.org/pn3/challenge/2016/)
5. [Heart Murmur Detection from Phonocardiogram Recordings](https://physionet.org/content/?topic=phonocardiogram)
6. [Classification of Normal/Abnormal Heart Sound Recordings](https://moody-challenge.physionet.org/2016/papers/challenge2016.pdf)
7. [README.md · miguellmartins/circor-digiscope-physionet22 at main](https://huggingface.co/datasets/miguellmartins/circor-digiscope-physionet22/blob/main/README.md)
8. [BUET Multi-disease Heart Sound Dataset](https://arxiv.org/html/2409.00724v1)
9. [Model-driven Heart Rate Estimation and Heart Murmur ...](https://arxiv.org/html/2407.18424v1)
10. [The CirCor DigiScope Dataset: From Murmur Detection ... - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9253493/)
11. [Classification of Heart Sound Recordings: The ...](https://www.physionet.org/content/challenge-2016/1.0.0/training-d/RECORDS)
12. [An Open Access Database for the Evaluation of Heart Sound ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC7199391/)
13. [PhysioNet Challenge2016:Heart sound classification](https://www.kaggle.com/datasets/bjoernjostein/physionet-challenge-2016)
14. [Resources](https://physionet.org/content/?csrfmiddlewaretoken=lIU0mZC30K2DHE8r81LLfywZW2voWdN7nBv6M8aApladVAAGG8xpXbdePUcDWhWp&amp;topic=&amp;csrfmiddlewaretoken=lIU0mZC30K2DHE8r81LLfywZW2voWdN7nBv6M8aApladVAAGG8xpXbdePUcDWhWp&amp;csrfmiddlewaretoken=lIU0mZC30K2DHE8r81LLfywZW2voWdN7nBv6M8aApladVAAGG8xpXbdePUcDWhWp&amp;orderby=relevance-desc&amp;types=0&amp;types=1&amp;types=2&amp;types=3&page=26)
15. [PhysioNet/CinC Challenge 2016](https://physionet.org/news/post/221/)
16. [Cardiology Patient Simulator "K" ver 2 | Heart Sounds & ECG ...](https://www.kyotokagaku.com/en/products_data/mw10/)
17. [Cardiology Patient Simulator "K" ver.2 | KYOTO KAGAKU](https://www.kyotokagaku.com/en/products_introduction/mw10/)
18. [Auscultation Trainers | Health and Care](https://www.healthandcare.co.uk/auscultation-trainers.html)
19. [Auscultation Simulator II](https://www.gtsimulators.com/products/sakamoto-auscultation-simulator-ii-m164-1-skm164)
20. [Auscultation - MedicalSupplies.co.uk](https://www.medicalsupplies.co.uk/auscultation.html)
21. [Lung Sound Auscultation Trainer "LSAT" ver.2](https://www.kyotokagaku.com/en/products_data/mw28/)
22. [MATT: MedVision Auscultation Task Trainer](https://www.coastems.com/products/matt-medvision-auscultation-task-trainer)
23. [Search | Products | KYOTO KAGAKU](https://www.kyotokagaku.com/en/products/search_result/)
24. [心臓病患者シミュレータ イチローIIA | 京都科学](https://www.kyotokagaku.com/jp/products_introduction/mw41_jp/)
25. [Evo AuRA](https://elevatehealth.net/product/evo-aura-auscultation-training/)
26. [Laerdal® SimPad® PLUS 2 System IE](https://www.worldpoint.com/laerdal-simpad-plus-system-2)
27. [Auscultation Trainers - Medical Simulators - Anatomy Warehouse](https://anatomywarehouse.com/simulators/task-trainers/auscultation/)
28. [CardioSim VII (portable) | 718-2710 made by Cardionics | CPR Savers and First Aid Supply](https://cpr-savers.com/CardioSim-VII-portable_p_7701.html)
29. [Auscultation Simulators - Heart, Lung & Bowel Sound Trainers](https://simandskills.co.uk/collections/auscultation-simulators)
30. [Auscultation Simulator](https://www.healthandcare.co.uk/auscultation-trainers/auscultation-simulator.html)
