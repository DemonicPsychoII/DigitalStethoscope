# Objektive Murmur-Metrik + Erfolgskriterium Q2

- **Run-ID:** R01-murmur-metrik
- **Preset:** medium
- **Modell:** preset/medium

## Fragestellung

```
Kontext: Bachelorarbeit, digitales Stethoskop (ESP32-S3, MEMS-Mikrofon). Es soll objektiv nachgewiesen werden, dass eine digitale Filterung die 'Murmur-Detektierbarkeit' in Herzschall-Aufnahmen verbessert, und dass sich zwei Filtercharakteristiken (z. B. Bell- vs. Diaphragm-Nachbildung) zweckabhaengig unterscheiden.

Hauptfrage: Welche objektiven, in der Literatur etablierten Metriken quantifizieren die Detektierbarkeit von Herzgeraeuschen (murmurs) in Phonokardiogramm-Signalen, und welche davon sind fuer einen Filtervergleich auf identischem Eingangsmaterial geeignet?

Unterfrage 1: Wie werden SNR im Murmur-Band, Spektralkontrast bzw. Envelope-basierte Kennwerte in der PCG-Literatur konkret berechnet (Bandgrenzen, Referenzfenster, Normierung)?
Unterfrage 2: Welche Schwellen oder Effektgroessen gelten in vergleichbaren Arbeiten als belegter Unterschied zwischen zwei Verarbeitungsketten (z. B. dB-Differenz, Cohen's d, statistische Tests bei gepaarten Signalen)?

Bitte praezise, mit Quellenangaben (Paper, Standards), Antwort auf Deutsch. Nenne konkrete Zahlenwerte und Bandgrenzen wo verfuegbar.
```

## Ergebnis

## Kurzantwort

Für die **Murmur-Detektierbarkeit** in Phonokardiogrammen existiert derzeit **keine einzelne, allgemein normierte Kennzahl**. In der Literatur werden vielmehr vier Klassen objektiver Größen verwendet:

1. **SNR bzw. Murmur-to-Noise-Ratio** im interessierenden Frequenzband,
2. **relative Energie- oder Pegelgrößen** des Murmurs gegenüber S1/S2 oder gegenüber diastolischen Referenzfenstern,
3. **spektrale Merkmale** wie Bandenergieverhältnisse, spektraler Schwerpunkt, Roll-off, Entropie oder spektrale Flachheit,
4. **zeitliche/envelope-basierte Größen** wie Hüllkurvenenergie, systolisch-diastolisches Energieverhältnis und Murmur-Dauer.

Für einen Vergleich zweier Filter auf **identischem Eingangsmaterial** sind besonders geeignet:

- gepaarte Differenz der bandbegrenzten Murmur-SNR,
- gepaarte Differenz des Murmur-zu-S1/S2-Energieverhältnisses,
- gepaarte Differenz des spektralen Kontrasts zwischen Murmur- und Referenzband,
- gepaarte Differenz von Hüllkurvenenergie und Hüllkurvenkontrast,
- zusätzlich eine aufgabennähere Kennzahl wie AUC, Sensitivität oder F1 eines festgelegten Murmur-Detektors.

Eine bloße Verbesserung des breitbandigen SNR oder der RMS-Amplitude beweist dagegen **nicht**, dass ein Murmur besser detektierbar ist.

---

# 1. Geeignete objektive Metriken

| Metrik | Typische Berechnung | Eignung für Filtervergleich auf identischem Eingang |
|---|---|---|
| Murmur-Band-SNR | \(10\log_{10}(P_\mathrm{Murmur}/P_\mathrm{Noise})\) oder \(20\log_{10}(A_\mathrm{Signal}/A_\mathrm{Noise})\) | Sehr gut, wenn Murmur- und Referenzfenster eindeutig definiert sind |
| Murmur-to-S1/S2-Ratio | \(E_M/(E_{S1}+E_{S2})\), meist in Prozent | Gut zur Quantifizierung der relativen Hervorhebung; nicht identisch mit SNR |
| Bandenergieverhältnis | Energie im hohen bzw. murmurrelevanten Band geteilt durch Gesamtenergie | Gut, sofern die Bandgrenzen vorab festgelegt werden |
| Spektraler Kontrast | Pegel- oder Energieunterschied zwischen Murmurband und Referenzband bzw. zwischen systolischem und diastolischem Fenster | Sehr gut für Bell-/Diaphragm-Vergleiche |
| Spektraler Schwerpunkt/Roll-off | Frequenz, unterhalb der z. B. 95 % der Spektralenergie liegen | Gut als ergänzende Formmetrik, aber kein direkter Detektierbarkeitsnachweis |
| Spektrale Entropie/Flachheit | Verteilung der normalisierten Spektralenergie | Ergänzend geeignet; geringe Interpretierbarkeit als alleinige Murmur-Metrik |
| Envelope-Energie | RMS-, Hilbert- oder Shannon-Energie der Hüllkurve im Murmurfenster | Gut, insbesondere für systolische Murmurs |
| Envelope-Kontrast | Verhältnis oder Differenz von Hüllkurvenenergie im Murmurfenster zur diastolischen Referenz | Sehr gut für identische Eingangssignale |
| Murmur-Dauer bzw. Flächenanteil | Anteil der systolischen/diastolischen Zeit oberhalb eines definierten Hüllkurvenschwellwerts | Gut, aber stark schwellenabhängig |
| Detektorleistung | AUC, Sensitivität, Spezifität, F1, balanced accuracy | Am direktesten; benötigt jedoch Labels oder einen definierten Referenzdetektor |

Die PCG-Literatur verwendet beispielsweise 25–400 Hz für viele Murmur-Analysen, 20–500 Hz bzw. 20–800 Hz für breitere Herzschallanalysen und 0–800 Hz in einer neueren Murmur-Grading-Arbeit. In dieser Arbeit wurde ein 3-s-Fenster mit 25-ms-Hamming-Fenstern, 512-Punkt-FFT und 0–800 Hz verwendet; höhere Frequenzen wurden ausgeschlossen, weil Murmurs dort selten manifest seien. [web:63][web:91]

---

# 2. SNR im Murmur-Band

## 2.1 Allgemeine Definition

Bei bekanntem Referenzsignal \(x(t)\) und Rauschsignal \(n(t)\) lautet die übliche Definition:

\[
\mathrm{SNR}_{\mathrm{dB}}
 =
10\log_{10}
\left(
\frac{\sum_{n\in W}x^2[n]}
{\sum_{n\in W}n^2[n]}
\right)
\]

oder äquivalent über RMS-Werte:

\[
\mathrm{SNR}_{\mathrm{dB}}
 =
20\log_{10}
\left(
\frac{x_\mathrm{RMS}}{n_\mathrm{RMS}}
\right).
\]

Für synthetisch verrauschte PCG-Signale wird häufig ein bekanntes sauberes Signal verwendet. Dann ist beispielsweise

\[
x_\mathrm{in}=x+n
\]

und für die Verarbeitungskette

\[
\Delta \mathrm{SNR}
 =
\mathrm{SNR}_{\mathrm{out}}
 -
\mathrm{SNR}_{\mathrm{in}}.
\]

Diese Definition ist methodisch sauber, weil das Nutzsignal bekannt ist. Sie ist bei klinischen Aufnahmen jedoch nur möglich, wenn ein Referenzsignal, eine parallele Messung oder ein experimentell erzeugtes Rauschsignal vorliegt. [web:62]

## 2.2 SNR mit einem rauscharmen Referenzfenster

Für reale PCG-Aufnahmen wurde auch folgende Definition verwendet:

\[
\mathrm{SNR}
 =
20\log_{10}
\left(
\frac{A_S}{4\sigma_N}
\right).
\]

Dabei ist:

- \(A_S\): Peak-to-Peak-Amplitude des untersuchten Herzschalls,
- \(\sigma_N\): Standardabweichung des Rauschens,
- \(4\sigma_N\): angenommene 95-%-Rauschamplitude bei normalverteiltem Rauschen.

Das Rauschen wurde dort in einem Abschnitt zwischen **70 % und 85 % des Herzzyklus** bestimmt, in dem kein Herzschall erwartet wurde. Für die Schätzung der Schallverschlusslatenz wurde ein SNR von **mindestens 14 dB** als ausreichend für eine Unsicherheit unter 1 ms angegeben. Diese Schwelle ist aber **keine Murmur-Detektierbarkeitsschwelle**; sie betrifft die zeitliche Bestimmung von Herzschallkomponenten. [web:61]

## 2.3 Empfohlene Definition für die Bachelorarbeit

Für einen Filtervergleich würde ich drei SNR-Varianten parallel auswerten:

### A. Murmur-gegen-diastolisches Rauschen

Für einen systolischen Murmur:

\[
\mathrm{SNR}_{M}
 =
10\log_{10}
\left(
\frac{
\sum_{n\in W_S} x_B^2[n]
}{
\frac{|W_S|}{|W_D|}
\sum_{n\in W_D} x_B^2[n]
}
\right)
\]

mit:

- \(x_B[n]\): bandpassgefiltertes Signal im Murmurband,
- \(W_S\): systolisches Murmurfenster zwischen S1 und S2,
- \(W_D\): diastolisches Referenzfenster, vorzugsweise ein Abschnitt ohne S1, S2 und bekannte diastolische Geräusche.

Die Zeitfenster müssen für beide Filter **identisch** sein. Zur Vermeidung von Randartefakten sollten die gleichen S1-/S2-Grenzen aus einer Referenzsegmentierung verwendet werden.

### B. Murmur-gegen-S1/S2

\[
\mathrm{MR}_{E}
 =
10\log_{10}
\left(
\frac{E_M}{E_{S1}+E_{S2}}
\right)
\]

mit

\[
E_W=\sum_{n\in W}x_B^2[n].
\]

Diese Größe zeigt, ob ein Filter den Murmur relativ zu den dominanten Herzschallkomponenten hervorhebt oder abschwächt.

### C. Murmur-to-background ratio

Wenn separate Rauschaufnahmen verfügbar sind:

\[
\mathrm{MBR}
 =
10\log_{10}
\left(
\frac{E_{M,\;B}}
{E_{N,\;B}}
\right),
\]

wobei \(B\) beispielsweise 25–400 Hz oder 20–500 Hz ist.

Diese Kennzahl ist der eigentlichen Detektierbarkeit am nächsten. Ohne separates Rauschsignal ist das diastolische Referenzfenster ein praktikabler Ersatz, aber kein reines Rauschsignal.

---

# 3. Bandgrenzen aus der PCG-Literatur

Es gibt keine einheitliche Murmur-Bandgrenze. Die Auswahl hängt von Murmurtyp, Sensor, Abtastrate und Zielsetzung ab.

| Frequenzbereich | Verwendung in der Literatur |
|---|---|
| 10–140 Hz | Typischer Schwerpunkt von S1 |
| 10–200 Hz | Typischer Bereich von S2 und tieferen Herzschallkomponenten |
| 20–200 Hz | Tieffrequente Herzschallkomponenten und tiefe Murmurs |
| 20–500 Hz | Häufig verwendeter breiter Herzschallbereich; auch als Gesamtenergieband für Murmur-Ratios |
| 25–400 Hz | Häufige Vorverarbeitung für PCG-Murmurklassifikation |
| 30–800 Hz | Spektrale Merkmale und mögliche höherfrequente Murmurs |
| 0–800 Hz | Murmur-Grading in einer modernen PCG-Arbeit |
| <300 Hz | In einer Stethoskop-Frequenzübersicht angegebener Bereich für viele Murmurs |
| 50–1200 Hz | Breiter Bereich der kardiopulmonalen Auskultation |

Herzgeräusche werden in Übersichtsarbeiten häufig ungefähr mit **20–650 Hz** angegeben; die für die Diagnose besonders relevanten Herzschallbereiche liegen teilweise bei **70–120 Hz**. Murmurs können jedoch deutlich oberhalb des dominanten S1-/S2-Bereichs liegen. [web:17]

Eine PCG-Klassifikationsarbeit verwendete Spektralmagnituden von **30 bis 790 Hz** und teilte den Bereich in 27 Bänder mit jeweils etwa **30 Hz** Breite auf, beispielsweise 10–40, 40–70 und 70–100 Hz. Als Merkmal wurde der Anteil der Spektralmagnitudensumme eines Bandes an der Gesamt-Spektralmagnitudensumme verwendet. [web:94]

Für die praktische Auswertung des ESP32-S3-Systems wäre folgende Aufteilung gut begründbar:

\[
B_1=20\text{–}80\ \mathrm{Hz}
\]

\[
B_2=80\text{–}150\ \mathrm{Hz}
\]

\[
B_3=150\text{–}300\ \mathrm{Hz}
\]

\[
B_4=300\text{–}500\ \mathrm{Hz}
\]

und optional

\[
B_5=500\text{–}800\ \mathrm{Hz}.
\]

Damit können Bell- und Diaphragm-Filter nicht nur über eine einzige Gesamtzahl, sondern über ihre frequenzabhängige Wirkung verglichen werden.

---

# 4. Spektralkontrast und spektrale Kennwerte

## 4.1 Bandenergie-Kontrast

Eine robuste, einfach interpretierbare Definition ist:

\[
C_B
 =
10\log_{10}
\left(
\frac{E_{B,M}}{E_{B,R}}
\right),
\]

wobei:

- \(E_{B,M}\): Energie im Band \(B\) während des Murmurfensters,
- \(E_{B,R}\): Energie im gleichen Band während des Referenzfensters.

Alternativ kann der Kontrast zwischen einem Murmurband und einem Herzschallband berechnet werden:

\[
C_{M/H}
 =
10\log_{10}
\left(
\frac{E_{150\text{–}400,\;S}}
{E_{20\text{–}150,\;S}}
\right).
\]

Wichtig ist, die Normierung nicht pro Filter unabhängig vorzunehmen. Eine Normierung jedes Ausgangssignals auf seinen eigenen Maximalwert kann einen tatsächlichen Pegelunterschied zwischen den Filtern entfernen. Für einen Filtervergleich sollten daher bevorzugt verwendet werden:

- dieselbe absolute ADC-Skalierung,
- dieselbe Eingangsamplitude,
- dieselbe Messkette,
- oder eine gemeinsame Normierung anhand des ungefilterten Eingangssignals.

## 4.2 Spektraler Schwerpunkt

Der spektrale Schwerpunkt lautet:

\[
f_c
 =
\frac{\sum_k f_k P[k]}
{\sum_k P[k]}.
\]

Er beschreibt die Schwerpunktfrequenz des Leistungsspektrums. Ein Filter, das höherfrequente Murmuranteile stärker passieren lässt, kann \(f_c\) erhöhen. Der Schwerpunkt ist aber kein direktes SNR-Maß, weil eine Pegelsteigerung und eine Rauschsteigerung sich teilweise aufheben können.

## 4.3 Spectral roll-off

Der 95-%-Roll-off ist die Frequenz \(f_{95}\), unterhalb derer 95 % der Spektralenergie liegen:

\[
\sum_{f\le f_{95}}P(f)
 =
0{,}95\sum_fP(f).
\]

Dieses Merkmal wurde in PCG-Arbeiten zusammen mit spektralem Schwerpunkt, spektraler Flussgröße und spektraler Energie als Standardmerkmal des Spektrums verwendet. [web:105]

## 4.4 Spektrale Entropie und Flachheit

Mit der normierten Spektralverteilung

\[
p_k=\frac{P[k]}{\sum_jP[j]}
\]

lautet die normalisierte Spektralentropie:

\[
H
 =
-\frac{\sum_k p_k\log p_k}{\log K}.
\]

Die spektrale Flachheit ist beispielsweise:

\[
SF
 =
\frac{
\exp\left(\frac1K\sum_k\log P[k]\right)
}{
\frac1K\sum_kP[k]
}.
\]

Diese Werte können unterscheiden, ob Energie konzentriert oder breit verteilt ist. Ein Murmur ist jedoch nicht immer spektral „rauschähnlich“. Entropie und Flachheit sollten deshalb nur ergänzend und nicht als alleiniger Nachweis einer verbesserten Detektierbarkeit eingesetzt werden.

---

# 5. Envelope-basierte Kennwerte

## 5.1 Shannon-Energie

Eine häufig verwendete Hüllkurve ist die Average-Shannon-Energy:

\[
E_{\mathrm{Sh}}(m)
 =
-\frac1N
\sum_{n=1}^{N}
x_\mathrm{norm}^2[n]\,
\log\left(x_\mathrm{norm}^2[n]\right).
\]

In einer neueren Segmentierungsarbeit wurde die Shannon-Energie über **20-ms-Fenster** mit **50 % Überlappung** berechnet. Die normalisierte Hüllkurve wurde anschließend über eine Schwelle von 0 nach Mittelwertsubtraktion segmentiert. [web:55]

Eine andere Arbeit verwendete eine Schwelle von **70 % des Maximums der normalisierten Energiehüllkurve**, um Herzschallkomponenten und Murmurabschnitte zu separieren. [web:46]

Diese festen Schwellen sind jedoch stark datenabhängig. Für einen Filtervergleich sollten S1-/S2-Zeitgrenzen nicht für jeden Filter neu geschätzt werden, weil der Filter sonst gleichzeitig die Segmentierung und die Messgröße beeinflusst.

## 5.2 Hilbert-Hüllkurve

Für das bandbegrenzte Signal \(x_B(t)\) ist die analytische Signalhüllkurve:

\[
e_H(t)
 =
\left|
x_B(t)+j\,\mathcal H\{x_B(t)\}
\right|,
\]

wobei \(\mathcal H\{\cdot\}\) die Hilbert-Transformation ist.

Eine PCG-Arbeit zur Analyse verrauschter Aufnahmen verwendete eine Vorverarbeitung von **25–400 Hz** mit kaskadierten Butterworth-Filtern und normierte die resultierenden Signale. [web:63]

Geeignete Kennwerte sind:

\[
E_{\mathrm{env},M}
 =
\frac1{|W_M|}
\sum_{n\in W_M}e_H^2[n]
\]

und

\[
C_{\mathrm{env}}
 =
10\log_{10}
\left(
\frac{E_{\mathrm{env},M}}
{E_{\mathrm{env},R}}
\right).
\]

Zusätzlich kann der Zeitanteil oberhalb einer Schwelle \(T\) bestimmt werden:

\[
D_T
 =
\frac{
\#\{n\in W_S:e_H[n]>T\}
}{
|W_S|
}.
\]

Die Schwelle sollte beispielsweise als

\[
T=\operatorname{Median}(e_H)+
k\cdot \operatorname{MAD}(e_H)
\]

aus einem Referenzabschnitt geschätzt werden. Das ist für einen Filtervergleich besser als eine filterspezifische Schwelle relativ zum jeweiligen Maximum.

## 5.3 Energetic Ratio

Eine in PCG-Arbeiten verwendete relative Murmurenergie ist:

\[
ER
 =
\frac{E_M}
{E_M+E_{S1}+E_{S2}}
\cdot100\%.
\]

Dabei ist \(E_M\) die Murmurenergie und \(E_{S1},E_{S2}\) die Energie der beiden Haupt-Herzschallkomponenten. In vergleichbaren Arbeiten wurden folgende grobe Schweregrade verwendet:

- **1–30 %:** leichter Murmur,
- **30–70 %:** mittlerer Murmur,
- **70–100 %:** schwerer Murmur.

Diese Grenzen stammen aus Arbeiten zur Murmur-Schweregradklassifikation und sind **keine validierten Schwellen für eine Filterverbesserung**. [web:76][web:83]

Eine alternative Definition verwendet die Energie im Bereich **100–500 Hz** dividiert durch die Gesamtenergie **20–500 Hz**; eine weitere Variante verwendet **50–500 Hz** dividiert durch **20–500 Hz**. [web:84]

Für die Arbeit sollte daher exakt eine Definition gewählt werden, beispielsweise:

\[
ER_{20\text{–}500}
 =
\frac{
E_{150\text{–}500,\;S}
}{
E_{20\text{–}500,\;S}
}.
\]

Das verhindert, dass die dominante Tieffrequenzenergie von S1/S2 den relativen Murmuranteil vollständig verdeckt.

---

# 6. Bell- versus Diaphragm-Vergleich

Die klassische qualitative Zuordnung lautet:

- **Bell:** bevorzugt tiefe Frequenzen,
- **Diaphragm:** bevorzugt höhere Frequenzen.

Für elektronische bzw. digitale Stethoskope ist diese Zuordnung allerdings nicht automatisch gültig; sie muss über die tatsächliche Übertragungsfunktion des Systems nachgewiesen werden.

Eine Vergleichsstudie mit identischem akustischem Eingang verwendete simulierte normale Herzschläge sowie Aorten- und Pulmonalstenose-Signale. Gemessen wurde die RMS-Amplitude bei **85, 250, 400, 550 und 1050 Hz**. Die beiden elektronischen Stethoskope zeigten gegenüber dem nicht verstärkten Stethoskop insbesondere im Bereich **550–1050 Hz** eine Verstärkung von **19–32 dB**; bei etwa 85 Hz lagen die Gewinne bei **4–10 dB**. Die Studie verwendete jedoch nur die Diaphragmaseite und enthielt keinen statistischen Bell-versus-Diaphragm-Test. [web:17]

Für die Bachelorarbeit sollte der Vergleich daher nicht nur über einen breitbandigen RMS-Wert erfolgen, sondern als frequenzabhängige Tabelle:

| Kennwert | Bell-Nachbildung | Diaphragm-Nachbildung | Vergleich |
|---|---:|---:|---:|
| Gain bei 20–80 Hz |  |  |  |
| Gain bei 80–150 Hz |  |  |  |
| Gain bei 150–300 Hz |  |  |  |
| Gain bei 300–500 Hz |  |  |  |
| Murmur-SNR |  |  |  |
| Murmur-to-S1/S2-Ratio |  |  |  |
| Envelope-Kontrast |  |  |  |
| AUC des Murmur-Detektors |  |  |  |

Dabei muss der Filtervergleich mit **demselben Eingangssignal und derselben Zeitreferenz** durchgeführt werden.

---

# 7. Welche Schwellen und Effektgrößen sind belegt?

## 7.1 SNR-Schwellen

Eine allgemeingültige Murmur-SNR-Schwelle ist nicht etabliert.

Belegt sind unter anderem:

- **14 dB SNR:** ausreichend für eine Unsicherheit unter 1 ms bei der Bestimmung von Herzschallverschlusslatenzen; nicht als Murmur-Detektierbarkeitsschwelle interpretieren. [web:61]
- Bei synthetischer PCG-Verrauschung wurden SNR-Bereiche von **0–15 dB** untersucht. Bei **0 dB** zeigte eine Hilbert-Envelope-Methode gegenüber einer Baseline eine absolute Sensitivitätsverbesserung von **9,2 Prozentpunkten**. Das ist ein Methodenvergleich und keine universelle klinische Schwelle. [web:63]
- In einer Arbeit zur nichtlinearen PCG-Verarbeitung wurde eine AUC von **0,96 bei 0 dB SNR** berichtet; der Ansatz stabilisierte sich ungefähr bei **−5 dB**. Auch das bezieht sich auf ein bestimmtes künstliches Rauschmodell. [web:35]
- In einer Arbeit zur fötalen PCG stieg das SNR nach Wavelet-Filterung von ungefähr **0,15 dB** auf **15,86 dB**; der Unterschied war mit **\(p<10^{-14}\)** signifikant. Diese Zahlen sind wegen des fötalen Signals und der verwendeten Referenz nicht direkt auf adulte Murmurs übertragbar. [web:14]

Daraus folgt: Für zwei Filter sollte nicht behauptet werden, ein Unterschied von beispielsweise 1 dB sei grundsätzlich klinisch relevant. Stattdessen sollte die Arbeit den beobachteten Unterschied mit Konfidenzintervall und Effektgröße berichten.

## 7.2 Cohen’s \(d\) bei gepaarten Daten

Für jedes identische Signal bzw. jeden Herzzyklus wird zunächst die Differenz gebildet:

\[
d_i=M_{i,A}-M_{i,B}.
\]

Dann:

\[
d_z
 =
\frac{\bar d}{s_d}.
\]

Dabei sind \(\bar d\) der mittlere gepaarte Unterschied und \(s_d\) seine Standardabweichung.

Die üblichen groben Interpretationsgrenzen sind:

- \(d\approx0{,}2\): kleiner Effekt,
- \(d\approx0{,}5\): mittlerer Effekt,
- \(d\approx0{,}8\): großer Effekt. [web:19][web:25]

Diese Grenzen sind allgemeine Konventionen, keine PCG-spezifischen klinischen Grenzwerte. Für die Arbeit wäre beispielsweise folgende Interpretation vertretbar:

- \(|d|<0{,}2\): praktisch kleiner Unterschied,
- \(0{,}2\le |d|<0{,}5\): kleiner bis moderater Unterschied,
- \(0{,}5\le |d|<0{,}8\): moderater Unterschied,
- \(|d|\ge0{,}8\): großer Unterschied.

## 7.3 Statistische Tests

Für zwei Filter A und B auf identischem Material:

### Bei annähernd normalverteilten Differenzen

- gepaarter t-Test,
- Mittelwertdifferenz,
- 95-%-Konfidenzintervall,
- Cohen’s \(d_z\),
- zusätzlich Bland-Altman-Darstellung.

### Bei nicht normalverteilten Differenzen

- Wilcoxon-Vorzeichen-Rang-Test,
- Median der Differenzen,
- Hodges-Lehmann-Schätzer,
- Bootstrap-Konfidenzintervall.

Das Signifikanzniveau kann auf

\[
\alpha=0{,}05
\]

gesetzt werden. Bei mehreren Frequenzbändern oder mehreren Metriken sollte eine Korrektur, beispielsweise Holm-Bonferroni oder eine vorab definierte primäre Metrik, verwendet werden.

Wichtig: Viele Herzzyklen desselben Patienten sind **keine unabhängigen Stichproben**. Für eine belastbare Aussage sollten die Kennwerte zunächst pro Herzzyklus und anschließend pro Aufnahme oder Patient aggregiert werden. Der statistische Test sollte dann auf Aufnahme- oder Patientenebene erfolgen, nicht auf allen Samples der Aufnahme.

---

# 8. Empfohlenes Auswertungsschema

Für die Bachelorarbeit würde ich folgende primäre Hypothese definieren:

> Filter A und Filter B unterscheiden sich hinsichtlich der Murmur-Detektierbarkeit, gemessen als bandbegrenzter Murmur-zu-Referenz-Kontrast im identischen systolischen Zeitfenster.

## Primäre Metrik

\[
C_M
 =
10\log_{10}
\left(
\frac{
E_{150\text{–}400,\;S}
}{
E_{150\text{–}400,\;D}
}
\right)
\]

mit:

- \(S\): systolisches Murmurfenster,
- \(D\): diastolisches Referenzfenster,
- gemeinsamer Frequenzbereich 150–400 Hz.

## Sekundäre Metriken

1. \(\mathrm{SNR}_{20\text{–}500}\),
2. \(ER=E_M/(E_M+E_{S1}+E_{S2})\),
3. Envelope-Kontrast,
4. spektraler Schwerpunkt,
5. 95-%-Roll-off,
6. AUC eines einfachen, vorab eingefrorenen Murmur-Detektors.

## Berichtete Ergebnisgrößen

Für jede Metrik:

\[
\Delta M
 =
M_A-M_B
\]

sowie:

- Mittelwert oder Median,
- 95-%-Konfidenzintervall,
- \(p\)-Wert,
- Cohen’s \(d_z\) oder rank-biseriale Effektgröße,
- Anzahl der Aufnahmen/Patienten,
- verwendetes Frequenzband,
- verwendete Zeitfenster,
- Normierungsverfahren.

## Wesentliche methodische Warnung

Ein Filter kann das Signal subjektiv oder quantitativ „lauter“ machen, ohne die Murmur-Detektierbarkeit zu verbessern. Deshalb sollten **RMS/Gain** nur als Übertragungskennwerte verwendet werden. Der eigentliche Nachweis sollte mindestens eine relative Murmur-Metrik enthalten, beispielsweise Murmur-SNR, Murmur-to-S1/S2-Ratio oder Envelope-Kontrast. Für die stärkste Aussage ist zusätzlich ein reproduzierbarer Detektor mit AUC- oder F1-Vergleich sinnvoll.

Für elektronische Stethoskope existiert zudem nach der einschlägigen Literatur weiterhin kein allgemein akzeptiertes akustisches Standardverfahren zur Charakterisierung der Übertragungsfunktion. Deshalb sollten die Bandgrenzen und Auswertefenster in der Arbeit explizit begründet und vor der Auswertung festgelegt werden. [web:106][web:107]

## Quellen

1. [Beyond Heart Murmur Detection: Automatic ... - PMC - NIH](https://pmc.ncbi.nlm.nih.gov/articles/PMC10482086/)
2. [[PDF] Phonocardiogram signal analysis for murmur diagnosing using ...](https://jestec.taylors.edu.my/Vol%2012%20issue%209%20September%202017/12_9_7.pdf)
3. [Detection of cardiac sounds components: a pilot study](https://ijeecs.iaescore.com/index.php/IJEECS/article/view/20924)
4. [Phonocardiogram (PCG) Murmur Detection Based on the ...](https://www.mdpi.com/1424-8220/24/20/6646)
5. [Nonlinear Phonocardiographic Signal Processing](https://www.diva-portal.org/smash/get/diva2:17719/FULLTEXT01.pdf)
6. [[PDF] Heart Murmur Detection in Phonocardiographic Signals Using ...](https://cinc.org/2022/Program/accepted/280_Preprint.pdf)
7. [9060749](http://article.aascit.org/file/pdf/9060749.pdf)
8. [Automatic Murmur Grading from Phonocardiogram](https://arxiv.org/abs/2209.13385)
9. [Heart rate study using the cardiac sounds](https://www.tandfonline.com/doi/full/10.1080/03091902.2025.2570159)
10. [Detection of Heart Murmurs in Phonocardiograms with ...](https://www.cinc.org/archives/2022/pdf/CinC2022-020.pdf)
11. [[PDF] PATHOLOGY CARDIAC MONITORING STUDY OF THE ...](http://www.jatit.org/volumes/Vol101No10/29Vol101No10.pdf)
12. [Hilbert-Envelope Features for Cardiac Disease Classification from Noisy Phonocardiograms](https://www.medrxiv.org/content/10.1101/2020.11.17.20233064v1.full.pdf)
13. [Phonocardiogram (PCG) Murmur Detection Based on the ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC11511235/)
14. [[PDF] a study of Kalman and Butterworth filters](https://beei.org/index.php/EEI/article/download/8674/4697)
15. [Can Heart Sound Denoising Be Beneficial in Phonocardiogram Classification Tasks?](https://lirias.kuleuven.be/retrieve/657793)
16. [[PDF] Digital Stethoscope within the Field of Cardiology: Current State ...](https://srcpublishers.com/index.php/cardiology-research-reviews/article/download/5650/5862/20617)
17. [[PDF] ABSTRAK](https://repo.poltekkes-surabaya.ac.id/8422/4/4.%20Abstrak.pdf)
18. [A Robust Low-Cost Adaptive Filtering Technique For ...](https://www.scribd.com/document/963361682/79-a-Robust-Low-cost-Adaptive-Filtering-Technique-for-Phonocardiogram)
19. [Review of Phonocardiogram Signal Analysis: Insights from ...](https://www.mdpi.com/2079-9292/13/16/3222)
20. [Filters for phono-cardiography - Medical & Biological Engineering & Computing](https://link.springer.com/article/10.1007/BF02474500)
21. [Journal of Material Sciences & Applied Engineering](https://www.mkscienceset.com/articles_file/724-_article1772099188.pdf)
22. [(PDF) A robust sliding window adaptive filtering technique ...](https://www.academia.edu/103880008/A_robust_sliding_window_adaptive_filtering_technique_for_phonocardiogram_signal_denoising)
23. [Improving Heart Valve Disease Detection](https://www.dicardiology.com/article/improving-heart-valve-disease-detection)
24. [Novel phonocardiography system for heartbeat detection from ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC10474097/)
25. [A Deep Learning Algorithm for Automated Cardiac Murmur Detection Via a Digital Stethoscope Platform](https://www.medrxiv.org/content/10.1101/2020.04.01.20050518v2.full.pdf)
26. [A comparative study of single-channel signal processing methods in fetal phonocardiography](https://journals.plos.org/plosone/article/figures?id=10.1371/journal.pone.0269884)
27. [Artificial-intelligence-enabled digital stethoscope improves ...](https://academic.oup.com/ehjdh/article/7/2/ztag003/8425125)
28. [Fetal Phonocardiogram Denoising by Wavelet Transformation:](https://www.cinc.org/archives/2017/pdf/331-075.pdf)
29. [A Low-Cost Multistage Cascaded Adaptive Filter Configuration for Noise Reduction in Phonocardiogram Signal](https://onlinelibrary.wiley.com/doi/10.1155/2022/3039624)
30. [Table 3. Analysis of a sample of 78 students in project units with paired sample t-test. N represents the sample size, M denotes the mean, SD indicates the standard deviation, Cohen’s d signifies the effect size, and the 95% confidence interval for d is provided.](https://pmc.ncbi.nlm.nih.gov/articles/PMC12810817/table/pone.0340806.t003/)
31. [Frequency Responses of Conventional and Amplified ... - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC7305673/)
32. [[PDF] Commentary on "A review of effect sizes and their confidence intervals, Part I: The Cohen's d family": The degrees of freedom for paired samples designs. | Semantic Scholar](https://www.semanticscholar.org/paper/Commentary-on-%22A-review-of-effect-sizes-and-their-d-Fitts/99e1c44a7dc8c2eb2190ebf1aa031b9bb2041fdd)
33. [Paired T-Tests using Effect Size](https://www.ncss.com/wp-content/themes/ncss/pdf/Procedures/PASS/Paired_T-Tests_using_Effect_Size.pdf)
34. [Cohen's d for Paired Samples](https://real-statistics.com/students-t-distribution/paired-sample-t-test/cohens-d-paired-samples/)
35. [Cohen's d and Other Standardized Differences — cohens_d](https://easystats.github.io/effectsize/reference/cohens_d.html)
36. [Phonocardiography(PCG)](https://fr.slideshare.net/slideshow/phonocardiographypcg/71507625)
37. [Cohen's d for the Paired Design: A Better Way to Find ...](https://thenewstatistics.com/itns/2021/04/08/cohens-d-for-the-paired-design-a-better-way-to-find-the-confidence-interval/)
38. [13.8: Effect Size](https://stats.libretexts.org/Bookshelves/Applied_Statistics/Learning_Statistics_with_R_-_A_tutorial_for_Psychology_Students_and_other_Beginners_(Navarro)/13:_Comparing_Two_Means/13.08:_Effect_Size)
39. [Paired t-test](https://rcompanion.org/handbook/I_04.html)
40. [Standardized Differences - CRAN](https://cran.r-project.org/web/packages/effectsize/vignettes/standardized_differences.html)
41. [Guide to Effect Sizes and Confidence Intervals](https://matthewbjane.quarto.pub/Guide-to-Effect-Sizes-and-Confidence-Intervals.pdf)
42. [Acoustic Stethoscopes | Biomedical Instrumentation & Technology](https://array.aami.org/doi/full/10.2345/i0899-8205-40-5-367.1)
43. [Effect size - Wikipedia](https://en.wikipedia.org/wiki/Effect_size)
44. [Conflict in confidence intervals for mean difference and confidence interval for Cohen'd effect size](https://stats.stackexchange.com/questions/87068/conflict-in-confidence-intervals-for-mean-difference-and-confidence-interval-for)
45. [Heart energy signature spectrogram for cardiovascular diagnosis](https://pmc.ncbi.nlm.nih.gov/articles/PMC1899182/)
46. [Heartbeat Cardiac Sounds Analysis | ClinicSearch](https://clinicsearchonline.org/article/heartbeat-cardiac-sounds-analysis)
47. [Comparison of Spectral and Sparse Feature Extraction ...](https://www.scielo.org.mx/scielo.php?script=sci_arttext&pid=S0188-95322023000400006)
48. [Graphic Representations and Frequency Parameters of ...](https://www.mecs-press.org/ijigsp/ijigsp-v10-n7/IJIGSP-V10-N7-4.pdf)
49. [Analog Signals](https://bmes16.wordpress.com/wp-content/uploads/2017/03/spectra-lecture.pdf)
50. [J Med Res Surg,](https://respubjournals.com/medical-research-surgery/pdf/2020/v1i8/The-Impact-of-Murmur-s-Severity-on-the-Cardiac-Variability.pdf)
51. [Heart Sound Classification Using Gaussian Mixture Models](https://www2.cs.arizona.edu/~pachecoj/courses/csc696h_fall22/lectures/projstatus_mary.pdf)
52. [Microsoft Word - 5. Karel - Frequency ..](https://ejournal.atmajaya.ac.id/index.php/JTE/article/download/6195/2874)
53. [[PDF] The study of the impact of murmurs on heart sounds by using ...](https://reference-global.com/download/article/10.2478/pjmpe-2024-0011.pdf)
54. [Using Spectral Acoustic Features to Identify Abnormal ...](https://www.cinc.org/archives/2016/pdf/160-401.pdf)
55. [A novel hybrid energy fraction and entropy-based approach for systolic heart murmurs identification](https://www.sciencedirect.com/science/article/abs/pii/S0957417414006897)
56. [INSTITUTE OF PHYSICS PUBLISHING](https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=67c7bd444fc926cdb201b451e6e72845078ecba4)
57. [Automated Assessment of the Quality of Phonocardographic ... - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8588421/)
58. [Bayesian denoising framework of phonocardiogram based on a new dynamical model](https://sharif.edu/~mbshams/files/25.pdf)
59. [DENOISING OF PCG SIGNAL BY USING WAVELET ...](https://bioinfopublication.org/files/articles/4_1_5_ACR.pdf)
60. [Biomed. Eng.-Biomed. Tech. 2019; aop](https://sci-hub.se/downloads/2019-12-20/74/rouis2019.pdf)
61. [Determination of Signal to Noise Ratio of Electrocardiograms Filtered by Band Pass and Savitzky-Golay Filters](https://www.sciencedirect.com/science/article/pii/S221201731200415X/pdf?md5=b8a7e02f6ba72c58abbb3dd8da52ac1c&pid=1-s2.0-S221201731200415X-main.pdf)
62. [An innovative multi-level singular value decomposition and ...](https://www.sciencedirect.com/science/article/abs/pii/S1746809417300848)
63. [Robust Denoising of Phonocardiogram Signals Using Time ...](https://ieeexplore.ieee.org/iel7/6287639/10005208/10136709.pdf)
64. [Ali et al. - 2023 - Deep Learning Framework for Denoising Heart ...](https://www.studocu.com/my/document/multimedia-university/health-promotion-and-wellness/ali-et-al-2023-deep-learning-framework-for-denoising-heart-sounds-in/163606970)
65. [[PDF] DENOISING OF HEART SOUND SIGNAL USING WAVELET ... - IJRET](https://ijret.org/volumes/2013v02/i04/IJRET20130204056.pdf)
66. [Real-time heart sound denoising for cardiac disease detection using ...](https://ojs.acad-pub.com/index.php/SV/article/view/1705)
67. [HAL Id: hal-00879037](https://hal.science/hal-00879037/file/Text-hal.pdf)
68. [Spectral and SNR improvement analysis of normal and abnormal ...](https://www.sciencedirect.com/science/article/abs/pii/S0167739X18318132)
69. [Microsoft Word - worldcomp09_word_template V.4](https://crss.utdallas.edu/CILab/IPCV2009.pdf)
70. [Heartbeat Cardiac Sounds Signals Analysis by Using the Energy ...](https://auctoresonline.org/article/heartbeat-cardiac-sounds-signals-analysis-by-using-the-energy-envelogram)
71. [[PDF] Proposed Algorithm for Implementation of Shannon Energy ...](https://www.semanticscholar.org/paper/Proposed-Algorithm-for-Implementation-of-Shannon-Saini/4b125c3952379107f55410c71ca3f178f7e4abac)
72. [Hilbert-Envelope Features for Cardiac Disease Classification from Noisy Phonocardiograms](https://www.medrxiv.org/content/10.1101/2020.11.17.20233064v2.full.pdf)
73. [IJECT Vol. 7, Issue 1, Jan - March 2016](http://www.iject.org/vol71acsect/2-mehak-saini.pdf)
74. [[PDF] Heart Sound Signal Modeling and Segmentation based on ...](https://crss.utdallas.edu/CILab/AsiaLinkConference_Jakarta_2007.pdf)
75. [A Noise-Robust Heart Sound Segmentation Algorithm Based on ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC11469632/)
76. [[PDF] Phonocardiography Signal Segmentation for Telemedicine ...](https://accedacris.ulpgc.es/bitstream/10553/48815/1/MurilloRendon.pdf)
77. [[PDF] Processing of the Phonocardiographic Signal − Methods for the ...](https://liu.diva-portal.org/smash/get/diva2:22548/FULLTEXT01.pdf)
78. [Digital Auscultation Analysis for Heart Murmur Detection](https://link.springer.com/article/10.1007/s10439-008-9611-z)
79. [[PDF] Comparative study on PCG envelope Extraction](https://bit.kuas.edu.tw/2025/vol16/N2/16.JIHMSP-250207.pdf)
80. [Multistage decision-based heart sound delineation method for automated analysis of heart sounds and murmurs - PubMed](https://pubmed.ncbi.nlm.nih.gov/26713160/)
81. [Methods and Results in Characterizing Electronic ...](https://cinc.org/archives/2002/pdf/653.pdf)
82. [BIOEN 481 Stethoscope Testing Report](https://www.scribd.com/document/146423201/BIOEN-481-Stethoscope-Testing-Report)
83. [[PDF] Acoustical Design of Digital Stethoscope for Improved Performance](https://www.comsol.jp/paper/download/153149/thiagarajan_paper.pdf)
84. [CORE 500 Digital Stethoscope (K233609) — FDA 510(k)](https://fda.innolitics.com/device/K233609)
85. [Orly Maor Consultant 25 Sirkin Street Kfar Saba, 4442157 Re ...](https://www.accessdata.fda.gov/cdrh_docs/pdf23/K233313.pdf)
86. [Technical Characterization of Digital Stethoscopes](https://pmc.ncbi.nlm.nih.gov/articles/PMC10753976/)
87. [Electronic Stethoscope - mu ltime dia](https://multimedia.3m.com/mws/media/369448O/3mtm-littmannr-stethoscopes.pdf)
88. [AV-16(3).dvi](http://hydromech.org.ua/content/pdf/av/av-16-3(46-57).pdf)
89. [Phonometric](https://www.jstage.jst.go.jp/article/ihj1960/23/5/23_5_711/_pdf)
90. [Wherever you are](https://fcc.report/FCC-ID/2A65V-SMARTHO-D2/5917950.pdf)
91. [Phonometric approach to the analysis of cardiac acoustic phenomena - PubMed](https://pubmed.ncbi.nlm.nih.gov/7239106/)
92. [Stethoscope with digital frequency translation for improved ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC6863143/)
93. [Phonocardiogram - Wikipedia](https://en.wikipedia.org/wiki/Phonocardiogram)
94. [10.1515 - Cdbme 2019 0066 | PDF | Resonance | Decibel](https://www.scribd.com/document/838058240/10-1515-cdbme-2019-0066)
95. [Significance of Frequency Domain Features of PCG ...](https://biomedpharmajournal.org/vol13no2/significance-of-frequency-domain-features-of-pcg-records-for-murmur-detection-an-investigation/)
96. [Selection of dynamic features based on time-frequency representations for heart murmur detection from phonocardiographic signals - PubMed](https://pubmed.ncbi.nlm.nih.gov/19921435/)
97. [PCG Classification Using Multidomain Features and SVM ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC6077676/)
98. [Classification of Murmurs in PCG Using Combined ...](https://cinc.org/2022/Program/accepted/65_Preprint.pdf)
99. [UNIVERSITY OF SOUTHAMPTON](https://eprints.soton.ac.uk/425886/1/00349389.pdf)
100. [Identifying Abnormalities in Heart Sound data using ...](https://www.diva-portal.org/smash/get/diva2:1980582/FULLTEXT01.pdf)
101. [2024 IEEE INTERNATIONAL WORKSHOP ON MACHINE LEARNING FOR SIGNAL PROCESSING, SEPT. 22–25, 2024, LONDON, UK](http://arxiv.org/pdf/2407.18424.pdf)
102. [Multiscale analysis of heart sound signals in the wavelet ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC11937596/)
103. [Murmur identification and outcome prediction in ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC10981708/)
104. [Heart Sound Clustering using a Combination of Temporal, ...](https://cinc.org/archives/2012/pdf/0217.pdf)
