# Messmethode zur Charakterisierung der akustischen Kette

- **Run-ID:** R08-messmethode-akustik
- **Preset:** low
- **Modell:** preset/low

## Fragestellung

```
Kontext: Bachelorarbeit, digitales Stethoskop. Die akustische Kette (Bruststueck -> Kopplung -> MEMS-Mikrofon -> ADC) soll messtechnisch charakterisiert werden (Frequenzgang, Rauschen, Linearitaet) im Band 20-1000 Hz.

Hauptfrage: Mit welchem Messaufbau charakterisiert man die akustische Uebertragungskette eines digitalen Stethoskops reproduzierbar, mit hochschulueblichem Equipment?

Unterfrage 1: Welche Anregungsverfahren und Auswertungen sind ueblich (Sinus-Sweep/ESS mit Deconvolution, rosa Rauschen, Stepped Sine), welche Anregungsquelle eignet sich fuer 20-1000 Hz (Lautsprecher mit Koppler, Shaker, Kunstbrustkorb/Phantom mit definierter Impedanz) und wie wird gegen ein Referenzmikrofon kalibriert?
Unterfrage 2: Welche Normen oder etablierten Verfahren gibt es fuer die Charakterisierung von Stethoskopen bzw. Auskultationsgeraeten (z. B. Arbeiten zur Stethoskop-Frequenzgangmessung, ANSI/IEC-Bezuege), und welche Minimalvariante ist mit einem guten Studiolautsprecher + Messmikrofon (z. B. Class-2 Messmikrofon) noch belastbar?

Antwort auf Deutsch, mit Quellen und einer konkreten Empfehlung fuer einen minimalen, belastbaren Aufbau.
```

## Ergebnis

## Kurzantwort

Für eine **reproduzierbare Charakterisierung der gesamten akustischen Kette** empfehle ich keinen Freifeldaufbau mit dem Stethoskop einfach vor einem Lautsprecher, sondern einen **definierten akustischen Koppler bzw. Kunstbrustkorb**:

> **Lautsprecher oder Shaker → definierter Brust-/Kopplungskörper → Stethoskop-Bruststück → internes MEMS-Mikrofon → ADC**

Dabei wird der Schalldruck unmittelbar am Eingang des Bruststücks mit einem **kalibrierten Referenzmikrofon** gemessen. Die Übertragungsfunktion wird anschließend als Verhältnis von digitalem Stethoskopsignal zu Referenzmikrofonsignal bestimmt. Für eine Bachelorarbeit ist ein **Lautsprecher mit kleinem, abgedichtetem Koppler und Referenzmikrofon** die beste Minimalvariante; ein Shaker mit Kunstbrust ist hinsichtlich der mechanischen Ankopplung realistischer, aber deutlich aufwendiger.

Für elektronische Stethoskope existiert derzeit keine allgemein verbindliche akustische Produktnorm. Eine einschlägige Arbeit stellt ausdrücklich fest, dass keine etablierten akustischen Standards für elektronische Stethoskope existieren. [web:3] Auch neuere Untersuchungen konventioneller und verstärkter Stethoskope weisen darauf hin, dass bislang keine einheitlichen Normen oder Parameter zur akustischen Charakterisierung von Stethoskopen bestehen. [web:5]

---

## 1. Empfohlener Messaufbau

### 1.1 Blockschaltbild

```text
Audio-Interface / DAW
        │
        ▼
Anregungssignal: ESS oder Stepped Sine
        │
        ▼
Leistungsverstärker
        │
        ▼
Tieftonfähiger Lautsprecher
        │
        ▼
definierter akustischer Koppler / Kunstbrust
        │
        ├── Referenzmikrofon
        │       │
        │       ▼
        │   Mikrofonvorverstärker / ADC
        │
        └── Bruststück des digitalen Stethoskops
                │
                ▼
          MEMS-Mikrofon + interner ADC
                │
                ▼
          aufgezeichnetes Digitalsignal
```

Der wesentliche Messwert ist die komplexe Übertragungsfunktion

\[
H_\mathrm{Steth}(f)
=
\frac{X_\mathrm{Steth}(f)}
     {P_\mathrm{ref}(f)}
\]

mit

- \(X_\mathrm{Steth}(f)\): Ausgangsspektrum des digitalen Stethoskops,
- \(P_\mathrm{ref}(f)\): Schalldruckspektrum am Bruststück,
- \(f\): Frequenz.

Für einen reinen relativen Frequenzgang genügt auch die Quotientenbildung zwischen Stethoskop- und Referenzkanal. Für eine absolute Empfindlichkeit muss das Referenzmikrofon in Pascal kalibriert sein.

### 1.2 Mechanischer Koppler

Der Koppler sollte folgende Eigenschaften besitzen:

- definierte, reproduzierbare Auflagefläche für das Bruststück,
- möglichst luftdichte Abdichtung,
- definierte akustische Impedanz oder zumindest dokumentierte Geometrie,
- Anschlussmöglichkeit für das Referenzmikrofon,
- definierte Anpresskraft des Bruststücks,
- Möglichkeit, Membran- und Glockenbetrieb getrennt zu untersuchen.

Eine einfache Variante ist eine **starre oder halbstarre Kammer** mit einer elastischen Kontaktfläche, auf die das Bruststück aufgelegt wird. Das Referenzmikrofon sitzt möglichst nahe an der Bruststückfläche, ohne die akustische Last wesentlich zu verändern.

Die wissenschaftlich anspruchsvollere Variante ist eine **Kunstbrust mit definierter mechanischer bzw. akustischer Impedanz**. In der Literatur wurden beispielsweise ein mit Flüssigkeit gefüllter Gummiball und ein mechanischer Shaker verwendet; außerdem wurden Phantomaufbauten zur Annäherung an die Impedanz der menschlichen Brustwand beschrieben. [web:41] Eine weitere Arbeit modelliert die Stethoskopakustik anhand eines Phantomaufbaus und vergleicht dessen Impedanz mit derjenigen des menschlichen Brustkorbs. [web:45]

### 1.3 Anregungsquelle

#### Variante A: Lautsprecher mit Koppler — Empfehlung für die Minimalvariante

Ein guter Studiolautsprecher oder kleiner Tieftonlautsprecher ist für 20–1000 Hz grundsätzlich geeignet, sofern:

- der Frequenzgang im Messbereich bekannt oder mit dem Referenzmikrofon korrigiert wird,
- bei 20–50 Hz ausreichend Schalldruck erzeugt wird,
- keine Übersteuerung oder Strömungsgeräusche auftreten,
- der Koppler möglichst geschlossen und mechanisch stabil ist.

Die Lautsprechermessung selbst lässt sich an Verfahren aus IEC 60268-5 anlehnen. Diese Norm behandelt unter anderem Messungen mit Sinussignalen, breitbandigem Rauschen, bandbegrenztem rosa Rauschen und Impulssignalen. [web:39] Für Lautsprecher werden außerdem ein kalibriertes Mikrofon und definierte Messbedingungen empfohlen. [web:42]

Der Lautsprecher sollte nicht als „ideale“ Quelle angenommen werden. Gemessen wird daher immer gleichzeitig der tatsächlich am Bruststück anliegende Schalldruck. Damit wird der Lautsprecherfrequenzgang weitgehend aus dem Ergebnis herausdividiert.

#### Variante B: Shaker mit Kunstbrust

Ein Shaker ist sinnvoll, wenn die **mechanische Anregung der Brustwand** untersucht werden soll. Er eignet sich besonders für:

- Untersuchungen der Auflage- und Kontaktmechanik,
- Vergleich verschiedener Bruststücke,
- Untersuchung des Einflusses der Anpresskraft,
- realistischere Simulation der Übertragung vom Körper auf das Bruststück.

Nachteile sind:

- schwierige Definition der Eingangsgröße,
- keine unmittelbar einfache Schalldruckkalibrierung,
- Abhängigkeit von Masse, Steifigkeit und Dämpfung des Phantoms,
- höhere mechanische und messtechnische Komplexität.

Für die erste Charakterisierung des MEMS-/ADC-Pfades würde ich deshalb zunächst den **akustischen Lautsprecher-Koppler** verwenden und den Shaker als Erweiterung behandeln.

---

## 2. Anregungsverfahren und Auswertung

### 2.1 Exponentieller Sinus-Sweep / ESS

Für die Hauptmessung ist ein **exponentieller Swept-Sine von 20 bis 1000 Hz** am geeignetsten.

Vorteile:

- gute Energieverteilung über den gesamten Frequenzbereich,
- hoher Signal-Rausch-Abstand,
- ein einzelner Sweep liefert den gesamten Frequenzgang,
- Impulsantwort und Frequenzgang können durch Deconvolution gewonnen werden,
- nichtlineare Verzerrungen erscheinen zeitlich getrennt und können ausgewertet werden.

Bei der ESS-Methode wird das aufgezeichnete Signal mit einem inversen Sweep dekonvolviert. Dadurch entsteht eine Impulsantwort; aus deren Fourier-Transformation erhält man Betrag und Phase der Übertragungsfunktion. Das Grundprinzip — Ausgangsspektrum durch Eingangsspektrum zu teilen oder alternativ per Deconvolution eine Impulsantwort zu bestimmen — ist in der akustischen Messtechnik etabliert. [web:32] Für logarithmische Sweeps wird außerdem der Vorteil beschrieben, dass harmonische Verzerrungen zeitlich getrennt von der linearen Impulsantwort erscheinen. [web:34]

Praktische Einstellungen:

- Startfrequenz: 15 oder 20 Hz,
- Endfrequenz: 1200 oder 1500 Hz,
- Auswertebereich: 20–1000 Hz,
- Sweepdauer: etwa 10–30 s,
- mindestens 3 Wiederholungen,
- Vorlauf und Nachlauf zur Erfassung des Einschwingens,
- identische Pegel und identische mechanische Position für alle Wiederholungen.

Die Auswertung sollte umfassen:

1. Deconvolution,
2. Ausschneiden der linearen Impulsantwort,
3. FFT,
4. Betrag in dB,
5. Phase beziehungsweise Gruppenlaufzeit,
6. Mittelwert und Standardabweichung über mehrere Wiederholungen,
7. separate Auswertung harmonischer Verzerrungen, sofern der Dynamikbereich ausreicht.

### 2.2 Stepped Sine

Ein **gestufter Sinus** ist die beste Methode für:

- präzise Pegel- und Frequenzgangmessung,
- Linearitätsuntersuchungen,
- THD-Messung,
- Verifikation einzelner Frequenzpunkte.

Geeignete Frequenzen sind beispielsweise:

```text
20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160,
200, 250, 315, 400, 500, 630, 800, 1000 Hz
```

Für eine detaillierte Kennlinie kann ein Abstand von 1/12 Oktave oder 1/24 Oktave verwendet werden.

Bei jeder Frequenz:

1. Pegel einschwingen lassen,
2. mehrere Perioden aufzeichnen,
3. erste Perioden verwerfen,
4. Amplitude und Phase per synchroner Demodulation oder FFT bestimmen,
5. zweiten und dritten Oberton auswerten,
6. den Pegel in mehreren Stufen wiederholen.

Für Linearität werden beispielsweise fünf Pegelstufen verwendet, etwa 60, 70, 80, 90 und 100 dB SPL am Koppler. Die genaue obere Grenze richtet sich nach der zulässigen Belastung des Bruststücks und dem Übersteuerungsverhalten des Stethoskops.

### 2.3 Rosa Rauschen

Rosa Rauschen mit Terz- oder Oktavbandanalyse ist nützlich für:

- schnelle Plausibilitätskontrolle,
- Pegel- und Rauschmessungen,
- Ermittlung breitbandiger Übertragungsfunktionen,
- Prüfung des Betriebs unter realitätsnaher breitbandiger Anregung.

Für die präzise Bestimmung des Frequenzgangs ist es jedoch weniger günstig als ESS oder Stepped Sine, da das Ergebnis stärker von Mittelungsdauer, Fensterung, Raumreflexionen und Signal-Rausch-Verhältnis abhängt.

Eine sinnvolle Kombination ist daher:

- **ESS** für den vollständigen Frequenzgang,
- **Stepped Sine** für Linearität und Verzerrung,
- **rosa Rauschen** für Plausibilitäts- und Rauschmessungen.

---

## 3. Kalibrierung mit Referenzmikrofon

### 3.1 Mikrofonkalibrierung

Das Referenzmikrofon wird vor der Messreihe mit einem akustischen Kalibrator, typischerweise bei:

- 1 kHz,
- 94 dB SPL oder 114 dB SPL,

kalibriert. Für Class-2-Messmikrofone sind solche Kalibratoren üblich; ein Beispiel erzeugt 94 dB SPL bei 1 kHz. [web:24]

Wichtig ist, dass nicht nur die Empfindlichkeit bei 1 kHz, sondern möglichst auch der **Frequenzgang des Mikrofons** berücksichtigt wird. IEC 61672-1 definiert Anforderungen an Schallpegelmesser der Klassen 1 und 2; für Class 2 liegt die untere Referenzgrenze typischerweise bei 20 Hz, mit größeren Toleranzen als bei Class 1. [web:19] Ein konkretes Class-2-Messmikrofon ist beispielsweise für 20 Hz bis 16 kHz spezifiziert. [web:16]

Für den Bereich 20–1000 Hz ist ein gutes Class-2-Mikrofon daher grundsätzlich verwendbar, aber:

- die Unsicherheit nahe 20 Hz ist größer,
- der individuelle Frequenzgang muss bekannt sein,
- der Kalibrierstatus sollte dokumentiert werden,
- ein 1/4-Zoll-Mikrofon kann wegen geringerer Richtwirkung und kleinerer Bauform vorteilhaft sein.

### 3.2 Referenzkanal während der Messung

Das Referenzmikrofon sollte **während jeder Messung gleichzeitig** mit dem Stethoskop aufzeichnen. Dadurch werden folgende Einflüsse automatisch korrigiert:

- Frequenzgang des Lautsprechers,
- Verstärkerfrequenzgang,
- Pegelschwankungen,
- teilweise auch zeitliche Drift.

Es wird nicht lediglich das elektrische Lautsprechersignal als Eingangssignal verwendet, weil dieses den tatsächlich am Bruststück wirksamen Schalldruck nicht beschreibt.

Die korrigierte Übertragungsfunktion lautet beispielsweise:

\[
H_\mathrm{corr}(f)
=
\frac{X_\mathrm{Steth}(f)}
     {X_\mathrm{ref}(f)}
\cdot
H_\mathrm{ref,kal}(f)
\]

Dabei bezeichnet \(H_\mathrm{ref,kal}(f)\) den kalibrierten Frequenzgang des Referenzmikrofons.

Wenn nur der relative Frequenzgang des Stethoskops benötigt wird, kann auf die absolute Korrektur verzichtet werden; dann muss aber klar angegeben werden, dass das Ergebnis **relativ zum Schalldruck am Kopplereingang** ist.

### 3.3 Pegeldefinition

Der Pegel sollte als Schalldruckpegel am Referenzmikrofon angegeben werden:

\[
L_p = 20 \log_{10}\left(\frac{p_\mathrm{rms}}{20\,\mu\mathrm{Pa}}\right)
\]

Die Messung sollte mindestens bei einem festen Referenzpegel durchgeführt werden. Für die Linearität sind mehrere Pegel erforderlich.

Bei sehr tiefen Frequenzen ist zu beachten, dass Entlüftungsöffnungen und Druckausgleichssysteme von Mikrofonen den Tieffrequenzgang beeinflussen können. Dieser Effekt ist in der akustischen Kalibriertechnik bekannt und muss insbesondere unterhalb von etwa 20 Hz berücksichtigt werden. [web:30] Im Bereich ab 20 Hz ist er bei einem geeigneten Messmikrofon beherrschbar, sollte aber durch die Datenblattkorrektur und eine dokumentierte Messgeometrie berücksichtigt werden.

---

## 4. Messung von Rauschen

Das Eigenrauschen sollte ohne akustische Anregung bestimmt werden:

1. Lautsprecher abgeschaltet,
2. Bruststück im Koppler montiert,
3. Stethoskop eingeschaltet,
4. mindestens 30–60 s aufzeichnen,
5. mehrere Wiederholungen durchführen.

Auswertung:

- Zeitverlauf auf Ausreißer und Störgeräusche,
- RMS-Wert im Band 20–1000 Hz,
- PSD beziehungsweise Leistungsdichtespektrum,
- 1/3-Oktav- oder schmalbandige Darstellung,
- gegebenenfalls A-bewerteter Wert, aber nur zusätzlich.

Für das Stethoskop ist die breitbandige Rauschleistung

\[
N_{20-1000}
=
\sqrt{\int_{20}^{1000} S_x(f)\,df}
\]

sinnvoller als ausschließlich ein A-bewerteter Pegel, da der relevante Auskultationsbereich tieffrequent ist.

Die Rauschmessung sollte außerdem bei mindestens zwei Verstärkungsstufen erfolgen. So lässt sich unterscheiden zwischen:

- Mikrofon- und Analograuschen,
- ADC-Rauschen,
- digitaler Verstärkung,
- eventuell aktivierter Rauschunterdrückung oder Filterung.

---

## 5. Messung der Linearität

Die Linearität wird bei mehreren Frequenzen und Pegeln bestimmt, zum Beispiel:

- Frequenzen: 25, 50, 100, 200, 500 und 1000 Hz,
- Pegel: fünf Stufen über den vorgesehenen Betriebsbereich,
- mindestens drei Wiederholungen pro Punkt.

Auszuwerten sind:

### Amplitudenlinearität

\[
L_\mathrm{out}
=
a \, L_\mathrm{in} + b
\]

Bewertet werden:

- Abweichung von der Regressionsgeraden,
- Kompression,
- Pegelabhängigkeit des Frequenzgangs,
- Übersteuerungsgrenze.

### Nichtlineare Verzerrung

Bei Stepped Sine können die Oberwellen ausgewertet werden:

\[
\mathrm{THD}
=
\frac{
\sqrt{A_2^2 + A_3^2 + \dots}
}{
A_1
}
\]

mit \(A_1\) als Grundschwingungsamplitude und \(A_2, A_3,\dots\) als Obertonamplituden.

Wichtig: Bei einem digitalen Stethoskop können digitale Filter, AGC, Noise-Gates oder dynamische Kompression aktiv sein. Deshalb muss die Firmware-Konfiguration dokumentiert und möglichst auf einen linearen beziehungsweise unveränderten Modus eingestellt werden.

---

## 6. Relevante Normen und ihre Einordnung

| Norm/Quelle | Relevanz für die Arbeit |
|---|---|
| **IEC 61672-1 / ANSI S1.4** | Anforderungen an Schallpegelmesser der Klassen 1 und 2; relevant für Auswahl und Einordnung des Referenzmikrofons, aber keine Stethoskopnorm. [web:28][web:19] |
| **IEC 60268-5** | Messverfahren für Lautsprecher mit Sinus, Rauschen und Impulssignalen; als methodische Orientierung für die Anregungsquelle geeignet. [web:39][web:42] |
| **IEC 60268-4** | Eigenschaften und Messungen von Schall­system­mikrofonen; ausdrücklich nicht primär für Messmikrofone vorgesehen. Daher nur eingeschränkt einschlägig. [web:1] |
| **IEC 60318-5** | Akustischer Koppler mit definierter akustischer Impedanz für Hörgeräte und Einsteckhörer; nicht direkt für Stethoskope gedacht, aber als Konzept für einen definierten Koppler relevant. [web:6] |
| **ANSI/ASA S3.7** | Messung und Kalibrierung von Hörern und Wandlern mit Kopplern beziehungsweise Ohrsimulatoren; methodisch übertragbar, aber keine direkte Stethoskopnorm. [web:9] |
| **IEC 60118-0** | Messung von Hörgeräteeigenschaften mit akustischem Koppler beziehungsweise Ohrsimulator; hilfreich für die Idee einer definierten akustischen Last. [web:2] |
| **Arbeiten zu elektronischen Stethoskopen** | Beschreiben Shaker-, Flüssigkeitsball-, Phantom- und Impedanzrohrverfahren; zeigen zugleich, dass eine einheitliche Norm fehlt. [web:3][web:41] |

Die Normen sollten in der Arbeit daher als **methodische Bezugspunkte** bezeichnet werden, nicht als direkte Prüfanforderungen für das digitale Stethoskop.

---

## 7. Konkrete Minimalvariante mit Hochschulausrüstung

### Empfohlene Ausstattung

1. **Audio-Interface mit zwei synchronen Eingangskanälen**
   - Kanal 1: kalibriertes Referenzmikrofon,
   - Kanal 2: analoger oder digitaler Ausgang des Stethoskops, sofern zugänglich.

2. **Guter Studiolautsprecher oder kleiner Tieftonlautsprecher**
   - nutzbarer Frequenzbereich bis mindestens 20 Hz,
   - ausreichend Schalldruck ohne deutliche Verzerrung.

3. **Class-2-Messmikrofon**
   - mit individueller Empfindlichkeitskalibrierung,
   - vorzugsweise mit bekanntem Frequenzgang bis 20 Hz.

4. **Akustischer Koppler**
   - starre Kammer oder definierte kleine Kontaktfläche,
   - definierter Montageanschlag,
   - definierte Anpresskraft,
   - Anschluss für Referenzmikrofon.

5. **Schallpegelkalibrator**
   - 94 dB SPL bei 1 kHz,
   - Kalibrierung vor und nach der Messreihe.

6. **Messsoftware**
   - MATLAB, Python, REW, ARTA oder vergleichbare Software,
   - ESS-Erzeugung und Deconvolution,
   - FFT/FRF,
   - RMS-, PSD- und THD-Auswertung.

### Durchführung

1. Referenzmikrofon mit 94 dB bei 1 kHz kalibrieren.
2. Koppler und Bruststück mechanisch reproduzierbar montieren.
3. Referenzmikrofon unmittelbar am Kopplervolumen positionieren.
4. ESS 20–1000 Hz bei moderatem Pegel abspielen.
5. Referenz- und Stethoskopsignal synchron aufzeichnen.
6. Mehrfach messen und mitteln.
7. Frequenzgang als Verhältnis beider Kanäle bestimmen.
8. Stepped-Sine-Messung bei mehreren Pegeln für Linearität und THD durchführen.
9. Ohne Anregung das Eigenrauschen messen.
10. Messunsicherheit und Wiederholbarkeit bestimmen.

### Belastbarkeit dieser Minimalvariante

Der Aufbau ist belastbar für:

- relativen Frequenzgang der vollständigen Kette,
- Vergleich verschiedener Bruststücke oder Betriebsmodi,
- Rauschmessungen,
- Pegelabhängigkeit,
- grobe bis mittlere Linearitäts- und Verzerrungsbewertung,
- reproduzierbare Vergleiche innerhalb derselben Messanordnung.

Er ist **nicht** ohne Weiteres belastbar für:

- direkte Aussagen über den Frequenzgang im menschlichen Brustkorb,
- absolute klinische Empfindlichkeit,
- Übertragbarkeit auf jede Anpresskraft oder Körperstelle,
- normgerechte Produktzertifizierung,
- exakte Bestimmung der akustischen Impedanz des Brustkorbs.

## Konkrete Empfehlung für die Bachelorarbeit

Ich würde als Hauptaufbau wählen:

> **Tieftonlautsprecher in einem geschlossenen, selbstgebauten akustischen Koppler; kalibriertes Class-2-Referenzmikrofon im Kopplervolumen; digitales Stethoskop auf definierter Kontaktfläche; synchroner Zweikanal-Scan mit ESS; Verifikation durch Stepped Sine; getrennte Rauschmessung.**

Der Aufbau sollte zunächst mit einem **linearen Kontrollmikrofon beziehungsweise einem bekannten Mikrofon** validiert werden. Zusätzlich sollten drei Größen dokumentiert werden:

- genaue Kopplergeometrie,
- Anpresskraft und Position des Bruststücks,
- Schalldruckpegel am Referenzmikrofon.

Damit erhält man trotz begrenztem Hochschulequipment eine nachvollziehbare und wiederholbare Messung der Kette **Bruststück → Kopplung → MEMS-Mikrofon → ADC**. Der entscheidende methodische Punkt ist, den tatsächlichen Eingangsschalldruck am Bruststück mit dem Referenzmikrofon zu messen und nicht lediglich das elektrische Lautsprechersignal als Referenz zu verwenden.

## Quellen

1. [IEC 60268-4](https://webstore.ansi.org/preview-pages/iec/preview_iec60268-4%7Bed6.0%7Den.pdf)
2. [IEC 60118-0 Ed. 4.0 b:2022](https://webstore.ansi.org/standards/iec/iec60118ed2022)
3. [Methods and Results in Characterizing Electronic ...](https://cinc.org/archives/2002/pdf/653.pdf)
4. [ANSI/ASA S3.55-2015/Part 3/IEC 60318-3:2015 (R2020)](https://webstore.ansi.org/standards/asa/ansiasas3552015partiec60318-2415765)
5. [Frequency Responses of Conventional and Amplified Stethoscopes ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC7305673/)
6. [IEC 60318-5 Ed. 1.0 b:2006](https://webstore.ansi.org/standards/iec/iec60318ed2006)
7. [AV-16(3).dvi](http://hydromech.org.ua/content/pdf/av/av-16-3(46-57).pdf)
8. [EN IEC 60318-8:2022 - Acoustic Coupler for High-Frequency ...](https://standards.iteh.ai/catalog/standards/clc/2a38d639-39db-4677-9e50-d3781a8dd3b1/en-iec-60318-8-2022)
9. [ANSI/ASA S3.7-2016](https://webstore.ansi.org/preview-pages/ASA/preview_ANSI+ASA+S3.7-2016+(R2020).pdf)
10. [Technical characterisation of digital stethoscopes: towards scalable artificial intelligence-based auscultation - PubMed](https://pubmed.ncbi.nlm.nih.gov/36794318/)
11. [Brotech Electronics Stethoscope Acoustic Performance Evaluation Tool User Manual 2021-12-29](https://www.brotechelectronics.com/Stethoscope_Evaluation_Tool_User_Manual%202021-12-29.pdf)
12. [BIOEN 481 Stethoscope Testing Report](https://www.scribd.com/document/146423201/BIOEN-481-Stethoscope-Testing-Report)
13. [Active and Passive Stethoscope Frequency Transfer Functions](https://isip.piconepress.com/conferences/ieee_spmb/2014/papers/p01_09.pdf)
14. [[PDF] Система электронной аускультации: метод измерения ...](https://pdfs.semanticscholar.org/296b/e3d6db0c610bd5cbfc65a364950cfe2e2252.pdf)
15. [[PDF] frequency response of stethoscopes](https://www.kar.fi/KARAudio/Publications/publications/nam98.pdf)
16. [Approach for frequency response-calibration for ...](https://www.diva-portal.org/smash/get/diva2:1762551/FULLTEXT01.pdf)
17. [[PDF] Building and Room Acoustics Measurements with Sine-Sweep ...](https://pub.dega-akustik.de/DAGA_1999-2008/data/articles/001658.pdf)
18. [Frequency response of a microphone using a sine sweep](https://dsp.stackexchange.com/questions/59756/frequency-response-of-a-microphone-using-a-sine-sweep)
19. [index.md](https://jmrplens.github.io/phonometry/guides/room-impulse-response/index.md)
20. [Flat and curved parametric acoustic loudspeakers ...](https://dael.euracoustics.org/confs/fa2025/data/articles/000405.pdf)
21. [Convention Paper - Angelo Farina](https://www.angelofarina.it/Public/papers/226-AES122.pdf)
22. [Surround-Sound-Impulse-Response. ...](http://arqen.com/wp-content/docs/Surround-Sound-Impulse-Response.pdf)
23. [[PDF] only for research purposes not for sale copyright www.psqca.com.pk](https://psqca.com.pk/cs/newitems2021/electronics/28-PS%20IEC%2060268-5-2014_FINAL.pdf)
24. [IEC 60268-5:2003+AMD1:2007 CSV | IEC](https://webstore.iec.ch/en/publication/1224)
25. [IEC 60268-5:1989+AMD1:1993 CSV](https://webstore.iec.ch/en/publication/14422)
26. [Loudspeaker Electroacoustic Measurements](https://www.admess.de/tl_files/admess-2013/pdf/Audio%20Precision/AppNote%20-%20Loudspeaker%20EA%20Measurements-1.pdf)
27. [AcousticsCheck - Apps on Google Play](https://play.google.com/store/apps/details?id=se.bllund.akustikkollen)
28. [Surround Sound Impulse Response](http://arqen.com/wp-content/docs/Surround-Sound-IR-Poster.pdf)
29. [Stethoscope acoustics](https://www.repository.cam.ac.uk/items/feadd88b-9e03-44fb-a875-c49f7c550259)
30. [PMP22 Class 2 Measurement Microphone - PLACID Measurement microphones](https://placidinstruments.com/product/pmp22-class-2-measurement-microphone/)
31. [Castle Sonus GA216I Class 2 Integrating Sound Level Meter](https://www.castlegroup.co.uk/products/castle-sonus-ga216i-class-2-integrating-sound-level-meter.html)
32. [Cost-effective Measurement Microphone I NTi Audio](https://www.nti-audio.com/en/products/measurement-microphones/class-2)
33. [SonaVyx™ — IEC 61672-1 Complete Guide: Sound Level Meter ...](https://sonavyx.com/en/insights/iec-61672-complete-guide)
34. [Measurement Microphones Price List | PDF | Decibel | Sound](https://www.scribd.com/document/535153905/Measurement-Microphones-2020)
35. [OPERATING MANUAL](https://images.thomann.de/pics/atg/atgdata/document/manual/242618_measurement_microphones_manual.pdf)
36. [24](https://www.belram.be/wp-content/uploads/2020/07/Measurement-Microphones-Specifications.pdf)
37. [[PDF] Piccolo II](https://www.norsonic.ch/wordpress/wp-content/uploads/Piccolo-II_Specsheet1.pdf)
38. [Sound Level Meter - Noise Level Meter](https://www.pce-instruments.com/english/measuring-instruments/test-meters/sound-level-meter-noise-level-meter-kat_40095.htm?_start=37)
39. [18. Technical Data XL2](https://images.thomann.de/pics/atg/atgdata/document/specs/technical_data_xl2.pdf)
40. [INTERNATIONAL STANDARD NORME INTERNATIONALE](https://www.vde-verlag.de/iec-normen/preview-pdf/info_iec61672-1%7Bed2.0%7Db.pdf)
41. [[PDF] Sound level meter](https://www.instrukart.com/wp-content/uploads/2017/04/DS_Testo-816-1-Sound-Level-Meter_Ver1.0.pdf)
42. [IEC 61672-1 Ed. 2.0 b:2013](https://webstore.ansi.org/standards/iec/iec61672ed2013)
43. [Class 2 Sound Level Meter ST-21D - Scarlet Tech](https://scarlet-tech.com/products/class-2-sound-level-meter-st21d/)
44. [Acoustic metrology – an overview of calibration methods and their uncertainties](https://www.metrology-journal.org/articles/ijmqe/pdf/2013/02/ijmqe130045.pdf)
