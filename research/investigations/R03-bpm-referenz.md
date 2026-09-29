# BPM-Referenz und Zielgenauigkeit

- **Run-ID:** R03-bpm-referenz
- **Preset:** low
- **Modell:** preset/low

## Fragestellung

```
Kontext: Bachelorarbeit, digitales Stethoskop mit Herzfrequenz-Bestimmung (BPM) aus dem Herzschall.

Hauptfrage: Womit wird die BPM-Genauigkeit eines Herzschall-basierten Geraets ueblicherweise verglichen, und welche Zielgenauigkeit ist begruendbar?

Unterfrage 1: Welche Referenzverfahren sind ueblich (EKG als Goldstandard, kommerzielles Referenz-Stethoskop, annotierte Datenbank-Labels) und wie wird die Uebereinstimmung ausgewertet (Bland-Altman, mittlerer absoluter Fehler, Prozentfehler)?
Unterfrage 2: Welche Genauigkeitsanforderungen nennen einschlaegige Normen bzw. Publikationen fuer Herzfrequenzmessung (z. B. ANSI/AAMI EC13, IEC 60601-2-27, Wearable-Studien) - konkrete Toleranzen wie +/- 5 bpm oder +/- 10 %?

Antwort auf Deutsch, mit Quellen und konkreten Zahlenwerten.
```

## Ergebnis

## Kurzantwort

Die BPM eines herzschallbasierten Geräts sollte **primär mit einer synchron aufgezeichneten ECG-/EKG-basierten Herzfrequenz** verglichen werden. Das EKG ist wegen der eindeutig detektierbaren R-Zacken die geeignetste Referenz für die zeitliche Schlagfolge. Für eine Bachelorarbeit ist als **begründbare Zielgröße** sinnvoll:

- **Mindestziel:** Fehler entsprechend **±10 % oder ±5 bpm, je nachdem, welcher Grenzwert größer ist** – dies entspricht der in ANSI/AAMI EC13 und IEC 60601-2-27 genannten Toleranz für EKG-Herzfrequenzmonitore. [web:31][web:33]
- **Ambitioniertes Entwicklungsziel:** **MAE ≤5 bpm und MAPE ≤5 %** unter Ruhebedingungen; zusätzlich sollten mindestens 95 % der Messungen innerhalb der vorab definierten Übereinstimmungsgrenzen liegen.
- Für ein nichtklinisches Prototypgerät sollte die Normtoleranz nicht als automatische Konformitätserklärung verstanden werden: ANSI/AAMI EC13 und IEC 60601-2-27 beziehen sich ausdrücklich auf **EKG-basierte Herzfrequenzmonitore**, nicht unmittelbar auf ein PCG-/Stethoskopgerät. [web:31]

## 1. Geeignete Referenzverfahren

| Referenzverfahren | Eignung für die BPM-Validierung | Bewertung |
|---|---|---|
| **Synchron aufgezeichnetes EKG, vorzugsweise 3-Kanal-EKG oder Holter-EKG** | Beste Referenz; die Herzfrequenz wird aus den R-R-Intervallen beziehungsweise R-Zacken bestimmt | **Primäre Referenz / Goldstandard** |
| **Simuliertes EKG-Testsignal** | Geeignet für technische Verifikation über einen großen Frequenzbereich, z. B. 30–200 bpm | Sehr gut für Funktions- und Grenzbereichstests, aber kein klinischer Patiententest |
| **Kommerzielles Referenz-Stethoskop** | Praktisch möglich, aber die manuelle Auskultation ist zeitlich weniger exakt und kann bei Geräuschen, Doppelzählungen oder Auslassungen fehleranfällig sein | Sekundäre Plausibilitätsreferenz, nicht ideale Goldstandard-Referenz |
| **Digitales Referenzstethoskop beziehungsweise zweiter PCG-Kanal** | Misst ein ähnliches physikalisches Signal und kann zur Gerätevergleichbarkeit beitragen | Nützlich für Vergleichstests, aber methodisch kein unabhängiger Goldstandard |
| **Annotierte Herzschall-Datenbank** | Geeignet, wenn synchrones EKG oder verlässliche Beat-Zeitpunkte vorhanden sind | Nur dann belastbare BPM-Referenz; reine S1-/S2- oder Normal-/Abnormal-Labels reichen nicht automatisch |
| **Aus EKG abgeleitete Datenbank-Labels** | Gut geeignet, sofern die Labeldefinition, Zeitfenster und EKG-basierte Berechnung dokumentiert sind | Als Ground Truth verwendbar, aber Berechnung und Fensterlänge offenlegen |

Bei einer PCG-Studie wurden beispielsweise synchrones D2-EKG und Phonokardiogramm aufgezeichnet; die EKG-Herzfrequenz wurde mit Pan-Tompkins aus den R-Zacken bestimmt und anschließend als Referenz für die PCG-Schätzung verwendet. Bei sauberem PCG lagen 770 von 812 Herzzyklen innerhalb eines relativen Fehlers von 5 %, der Medianfehler betrug 0,1 %. [web:14]

Eine große offene Herzschall-Datenbank umfasst 2.435 Aufnahmen von 1.297 Personen. Allerdings enthalten nur bestimmte Teilmengen ein synchrones EKG; die bereitgestellten Annotationen betreffen überwiegend S1, Systole, S2 und Diastole und sind **keine flächendeckenden BPM-Labels**. [web:1] Deshalb sollte aus solchen Datenbanken die Referenz-BPM selbst aus dem synchronen EKG oder aus klar definierten Beat-Zeitpunkten berechnet werden.

### Empfehlung für die Bachelorarbeit

Für jeden Messabschnitt sollte möglichst Folgendes vorliegen:

1. PCG/Herzschall und EKG **zeitlich synchron** aufnehmen.
2. EKG-R-Zacken automatisch detektieren und stichprobenartig visuell kontrollieren.
3. Eine identische Auswerteperiode verwenden, zum Beispiel 10 s, 30 s oder 60 s.
4. Referenz-BPM berechnen als

\[
HR_{\mathrm{EKG}}=\frac{60}{\overline{RR}\,[\mathrm{s}]}
\]

oder als mittlere Schlagzahl pro Zeitfenster.
5. PCG-BPM und EKG-BPM nur dann vergleichen, wenn beide Werte demselben Zeitfenster zugeordnet sind.

## 2. Übliche Auswertemethoden

| Kennzahl | Definition | Aussage |
|---|---|---|
| **Fehler pro Messung** | \(e_i=HR_{\mathrm{PCG},i}-HR_{\mathrm{EKG},i}\) | Vorzeichenbehaftete Abweichung |
| **Bias / mittlerer Fehler** | \(\overline e\) | Systematische Über- oder Unterschätzung |
| **MAE** | \(\frac{1}{n}\sum |e_i|\) | Durchschnittlicher absoluter Fehler in bpm |
| **MAPE / mittlerer absoluter Prozentfehler** | \(\frac{100}{n}\sum \left|\frac{e_i}{HR_{\mathrm{EKG},i}}\right|\) | Relativer Fehler in Prozent |
| **Bland–Altman-Bias** | Mittelwert der Differenzen | Systematischer Unterschied zwischen beiden Verfahren |
| **95-%-Übereinstimmungsgrenzen** | \(\overline e\pm1{,}96\,SD_e\) | Bereich, in dem ungefähr 95 % der Differenzen liegen |
| **Anteil innerhalb einer Toleranz** | z. B. Anteil mit \(|e_i|\leq5\) bpm | Anschauliche klinische beziehungsweise technische Erfüllungsrate |
| **Korrelationskoeffizient** | z. B. Pearson-\(r\) | Nur Zusammenhang; kein ausreichender Nachweis der Übereinstimmung |

Für die Arbeit sollte die **Bland–Altman-Auswertung nicht durch eine Korrelation ersetzt werden**. Eine hohe Korrelation kann vorliegen, obwohl ein systematischer Bias oder große Einzelabweichungen bestehen. Empfehlenswert ist daher die gemeinsame Berichterstattung von:

- Bias in bpm,
- 95-%-Limits of Agreement in bpm,
- MAE in bpm,
- MAPE in Prozent,
- Anteil der Werte innerhalb von ±5 bpm,
- Anteil der Werte innerhalb von ±10 %.

Eine Wearable-Validierungsstudie nutzte genau diese Kombination aus mittlerem Fehler, MAE, MAPE, Bland–Altman-Analyse mit 95-%-Übereinstimmungsgrenzen und Konkordanzkorrelation. Gegen ein ambulantes EKG betrugen die 24-Stunden-Werte beispielsweise für die Apple Watch 3: **MAE 4,72 bpm, MAPE 5,86 %, Bias −1,80 bpm und Limits of Agreement −16,31 bis +12,71 bpm**. Für Fitbit Charge 2 wurden **MAE 4,71 bpm, MAPE 5,96 %, Bias −3,47 bpm und Limits of Agreement −15,55 bis +8,62 bpm** berichtet. [web:18]

Wichtig ist dabei: Ein kleiner MAE bedeutet nicht automatisch, dass jede Einzelmessung ausreichend genau ist. Im genannten Beispiel war der durchschnittliche Fehler zwar ungefähr 5 bpm, die Bland–Altman-Grenzen waren jedoch deutlich weiter. Das sollte bei der Interpretation des eigenen Geräts ausdrücklich berücksichtigt werden.

## 3. Normative Genauigkeitsanforderungen

| Norm beziehungsweise Quelle | Anwendungsbereich | Genannte Herzfrequenzgenauigkeit | Herzfrequenzbereich |
|---|---|---:|---:|
| **ANSI/AAMI EC13:2002** | EKG-Herzfrequenzmonitore, Herzfrequenzanzeigen und Alarme | **±10 % des Eingangswerts oder ±5 bpm, je nachdem, welcher Wert größer ist** | Erwachsene mindestens **30–200 bpm**; pädiatrisch/neonatal mindestens bis **250 bpm** |
| **IEC 60601-2-27** | EKG-Überwachungsgeräte | **±10 % oder ±5/min, je nachdem, welcher Wert größer ist** | Erwachsene mindestens **30–200/min**; pädiatrisch/neonatal mindestens **30–250/min** |
| **Wearable-Validierungsstudien** | Meist PPG-, Brustgurt- oder andere tragbare Geräte gegen EKG | Häufige Akzeptanzgrenze: **MAPE <10 %** beziehungsweise **±10 %**; teilweise strengere Kriterien von **±5 %** oder **±5 bpm** | Abhängig vom Studienprotokoll |
| **PCG-Herzfrequenz-Publikationen** | Herzschallbasierte Schätzung gegen synchrones EKG | Häufig relativer Fehler, MAE oder Trefferquote innerhalb ±5 %/±5 bpm | Häufig Ruhe- oder kontrollierte Bedingungen |

ANSI/AAMI EC13 fordert für die Anzeige eines EKG-Herzfrequenzmonitors eine Abweichung von höchstens **±10 % des Eingangswerts oder ±5 bpm, je nachdem, welcher Wert größer ist**. Der geforderte Erwachsenenbereich beträgt mindestens **30 bis 200 bpm**. [web:31]

IEC 60601-2-27 nennt ebenfalls eine Genauigkeit von **±10 % oder ±5/min, je nachdem, welcher Wert größer ist**, und einen Mindestanzeigebereich von **30–200/min für Erwachsene** beziehungsweise **30–250/min für neonatale und pädiatrische Anwendung**. [web:33]

Die Formulierung „je nachdem, welcher Wert größer ist“ ist relevant:

| Referenz-BPM | ±10 % | ±5 bpm | Zulässige Normabweichung |
|---:|---:|---:|---:|
| 40 bpm | ±4 bpm | ±5 bpm | **±5 bpm** |
| 60 bpm | ±6 bpm | ±5 bpm | **±6 bpm** |
| 80 bpm | ±8 bpm | ±5 bpm | **±8 bpm** |
| 100 bpm | ±10 bpm | ±5 bpm | **±10 bpm** |
| 150 bpm | ±15 bpm | ±5 bpm | **±15 bpm** |
| 200 bpm | ±20 bpm | ±5 bpm | **±20 bpm** |

Damit ist die Norm **nicht gleichbedeutend mit einer generellen ±5-bpm-Anforderung**. Bei niedriger Herzfrequenz dominiert der absolute Grenzwert von 5 bpm; ab 50 bpm dominiert zunehmend der Prozentwert.

## 4. Was ist als Zielgenauigkeit begründbar?

Für ein digitales Stethoskop im Rahmen einer Bachelorarbeit würde ich folgende Zieldefinition empfehlen:

### Primäres Mindestkriterium

\[
|HR_{\mathrm{PCG}}-HR_{\mathrm{EKG}}|
\leq \max(5\ \mathrm{bpm},\,0{,}10\cdot HR_{\mathrm{EKG}})
\]

Das entspricht der Normlogik von ANSI/AAMI EC13 und IEC 60601-2-27. Es sollte aber als **Benchmark beziehungsweise Entwicklungsziel** bezeichnet werden, nicht als Behauptung einer Normkonformität des PCG-Geräts.

### Zusätzliche quantitative Kriterien

Eine gut begründbare Validierung wäre:

- **MAE ≤5 bpm** im Gesamtdatensatz,
- **MAPE ≤10 %**,
- mindestens **90 % der Messfenster innerhalb ±10 % beziehungsweise ±5 bpm**,
- Bland–Altman-Bias möglichst nahe **0 bpm**,
- Berichterstattung der **95-%-Übereinstimmungsgrenzen**,
- getrennte Auswertung für Ruhe, Bewegung, unterschiedliche Herzfrequenzbereiche und Signalqualitäten.

Als strengeres Ziel kann zusätzlich formuliert werden:

- **MAE ≤3 bpm**,
- **MAPE ≤5 %**,
- mindestens **95 % der Werte innerhalb ±5 bpm** bei ruhigen, normofrequenten Probanden.

Die strengere Zielgröße ist mit der Literatur plausibel, aber nicht universell normativ vorgeschrieben. In einer Wearable-Studie wurden beispielsweise die Gerätevalidität und die Akzeptanz über **MAPE <10 %** definiert; zugleich wird dort erwähnt, dass frühere Arbeiten teils die strengere Grenze von **±5 %** verwendeten. [web:18] Eine weitere klinische Wearable-Studie bewertete die Genauigkeit explizit als Anteil der Messungen innerhalb **±5 bpm gegenüber EKG** bei Ruhe und innerhalb **±10 bpm** bei induzierter supraventrikulärer Tachykardie. [web:28]

## Schlussfolgerung für die Arbeit

Die methodisch stärkste Aussage wäre:

> „Die aus dem Herzschall bestimmte Herzfrequenz wird gegen eine synchron aufgezeichnete, aus den EKG-R-R-Intervallen bestimmte Referenz-Herzfrequenz validiert. Als normnahes Mindestkriterium wird eine Abweichung von höchstens ±10 % oder ±5 bpm, je nachdem, welcher Grenzwert größer ist, verwendet. Zusätzlich werden MAE, MAPE, Bias, Bland–Altman-95-%-Übereinstimmungsgrenzen und der Anteil der Messungen innerhalb definierter Toleranzgrenzen berichtet.“

Für einen Prototypen ist daher **±10 % beziehungsweise ±5 bpm als begründbares Mindestziel** angemessen. Wenn das Gerät unter Ruhebedingungen entwickelt und getestet wird, ist **MAE ≤5 bpm, MAPE ≤5–10 %** ein realistisches und wissenschaftlich gut vertretbares Ziel; eine uneingeschränkte klinische Tauglichkeit lässt sich daraus jedoch nicht ableiten.

## Quellen

1. [ANSI/AAMI EC13:2002, Cardiac monitors, heart rate meters ...](https://mdcpp.com/doc/standard/ANSIAAMIEC13-2002.pdf)
2. [1. Technical Data](http://darvallvet.com/wordpress/wp-content/uploads/2017/03/Vet-Trends-V-plus-Technical-Data.pdf)
3. [IEC 60601-2-27](https://www.normsplash.com/FreeDownload/179516115/IEC-60601-2-27-2011-en-fr.pdf)
4. [drager-vista-120-data-sheet](https://www.scribd.com/document/784798501/drager-vista-120-data-sheet)
5. [PM 7000 Specsht RevB.indd](https://media.supplychain.nhs.uk/media/documents/N0889184/Specification/31467_N0889184%20PM%207000%20Specifications.pdf)
6. [CARESCAPE Patient Data Module - Medisap](https://www.medisap.cz/wp-content/uploads/2021/10/GE-pdm-spec-sheet.pdf)
7. [ANSI/AAMI EC13-2002](https://webstore.ansi.org/standards/aami/ansiaamiec132002)
8. [ANSI/AAMI EC13:1992](https://webstore.ansi.org/standards/aami/ansiaamiec131992)
9. [Facial video photoplethysmography for measuring average ...](https://www.frontiersin.org/journals/physiology/articles/10.3389/fphys.2025.1638809/full)
10. [Ge Corometrics 259cx A | PDF | Monitoring (Medicine) - Scribd](https://www.scribd.com/document/939218878/Ge-Corometrics-259cx-A)
11. [IEC 60601-2-27:2011/COR1:2012 - IEC 60601-2-27:2011/COR1:2012](https://cdn.standards.iteh.ai/samples/20099/85bde6eb6d3c43869ba30f862bdb0736/IEC-60601-2-27-2011-COR1-2012.pdf)
12. [IEEE 1417-1996](https://standards.ieee.org/ieee/1417/2119/)
13. [[PDF] Performance Specifications](https://m.media-amazon.com/images/I/91ce4znpegL.pdf)
14. [EN 60601-2-27:2014 ECG Monitor Safety and ...](https://standards.iteh.ai/catalog/standards/clc/cf5294a7-6255-451f-b61c-f059b054b839/en-60601-2-27-2014)
15. [Cardiac Monitor Guidance Cardiotachometer and Rate Alarm](https://www.fda.gov/media/71947/download)
16. [The Validation and Accuracy of Wearable Heart Rate Trackers ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC12483337/)
17. [Accuracy of Heart Rate Measurement Under Transient States](https://documentserver.uhasselt.be/bitstream/1942/47708/1/Accuracy%20of%20Heart%20Rate%20Measurement%20Under%20Transient%20States_%20A%20Validation%20Study%20of%20Wearables%20for%20Real-Life%20Monitoring.pdf)
18. [Accuracy of Consumer Wearable Heart Rate Measurement ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC6431828/)
19. [[PDF] Validation of heart rate measured by the consumer-level wearable ...](https://pdfs.semanticscholar.org/0c96/075f7cb95da347a35d752f8c4bf37ef0aea8.pdf)
20. [LECTURE NOTES](http://essay.utwente.nl/71386/1/Teekens_MA_BMS.pdf)
21. [Validation of Wearable Digital Devices for Heart Rate ...](https://www.e-arm.org/journal/view.php?number=4315)
22. [PPG Ieee Ansi Wearable Testing Standards | ChatPPG](https://chatppg.com/blog/ppg-ieee-ansi-wearable-testing-standards)
23. [Validation of nocturnal resting heart rate and heart rate variability in ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC12367097/)
24. [A Validation Study: Fitbit Charge 2 Heart Rate Measurement ...](https://yorkspace.library.yorku.ca/server/api/core/bitstreams/81f3d2d1-319f-480e-8689-b61546450573/content)
25. [Accuracy of wrist-worn wearable devices for determining exercise intensity](https://journals.sagepub.com/doi/pdf/10.1177/20552076221124393)
26. [Validation of a Wearable Sensor Prototype for Measuring ...](https://biomedeng.jmir.org/2024/1/e57373)
27. [Implications for Heart Failure Management in Home](https://assets.cureus.com/uploads/original_article/pdf/329018/20250307-283154-3yycqf.pdf)
28. [Assessing Accuracy of Wrist-Worn Wearable Devices in ...](https://pubmed.ncbi.nlm.nih.gov/30808083/)
29. [Assessing the Accuracy of Four Heart Rate Wearables and ...](https://pubmed.ncbi.nlm.nih.gov/39905563/)
30. [Determination of heart rate variability with an electronic ...](https://pubmed.ncbi.nlm.nih.gov/23014860/)
31. [An Open Access Database for the Evaluation of Heart Sound ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC7199391/)
32. [Robustness of electrocardiogram signal quality indices - PMC - NIH](https://pmc.ncbi.nlm.nih.gov/articles/PMC9006023/)
33. [Comprehensive Dataset and Signal Processing Framework for Phonocardiogram-Based Heart Rate and Blood Pressure Estimation](https://arxiv.org/pdf/2605.23516v1.pdf)
34. [Resources - PhysioNet Index](https://physionet.org/content/?topic=ecg&page=10)
35. [Heart](https://physionet.org/content/?topic=heart)
36. [Evaluation of a digital stethoscope for electrocardiographic ...](https://www.sciencedirect.com/science/article/pii/S0737080624000558)
37. [Databases](https://www.physionet.org/about/database/)
38. [LUDB: a new open-access validation tool for electrocardiogram ...](https://arxiv.org/pdf/1809.03393v4.pdf)
39. [Evaluation of a new smartphone-based stethoscope with ...](https://www.sciencedirect.com/science/article/pii/S0034528825000384)
40. [Digital Stethoscope - Aaron Davis and Brandon Richter](https://people.ece.cornell.edu/land/courses/ece4760/FinalProjects/s2004/bcr5/index.htm)
41. [[PDF] Digital Stethoscope within the Field of Cardiology: Current State ...](https://srcpublishers.com/index.php/cardiology-research-reviews/article/download/5650/5862/20617)
42. [Transformer-based heart language model with electrocardiogram annotations](https://www.nature.com/articles/s41598-024-84270-x)
43. [[PDF] Deep PPG: Large-Scale Heart Rate Estimation with Convolutional ...](https://ubi29.informatik.uni-siegen.de/usi/pdf/ubi_sensors2019.pdf)
44. [HEART RATE ESTIMATION FROM PHONOCARDIOGRAM SIGNALS USING NON-NEGATIVE MATRIX FACTORIZATION](https://www.gipsa-lab.grenoble-inp.fr/~bertrand.rivet/references/RivetICASSP2019b.pdf)
45. [Estimation of Beat-to-Beat Interval and Systolic Time Intervals Using Phono- and Seismocardiograms - PubMed](https://pubmed.ncbi.nlm.nih.gov/31947135/)
