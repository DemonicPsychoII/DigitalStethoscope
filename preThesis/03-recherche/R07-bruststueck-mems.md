# Bruststueck-Kopplung an MEMS-Mikrofon + Bauteilauswahl

- **Run-ID:** R07-bruststueck-mems
- **Preset:** medium
- **Modell:** preset/medium

## Fragestellung

```
Kontext: Bachelorarbeit, digitales Stethoskop. Ein analoges Stethoskop-Bruststueck soll akustisch/mechanisch an ein MEMS-Mikrofon gekoppelt werden. Relevantes Band: ca. 20-600 Hz, inkl. S3/S4 bei ca. 20-60 Hz.

Hauptfrage: Wie koppelt man ein Stethoskop-Bruststueck praktisch an ein MEMS-Mikrofon, und welche konkreten Bauteile erfuellen die untere Grenzfrequenz?

Unterfrage 1: Welche Kopplungsvarianten sind in Publikationen und Open-Source-Projekten zu digitalen Stethoskopen dokumentiert (Mikrofon direkt in der Schlauchkammer, kurzer Schlauchstummel mit abgeschlossenem Hohlraum, Membran-/Kavitaets-Ankopplung, Kontakt-/Vibrationsaufnehmer statt Luftschall)? Welche Effekte hat das Hohlraumvolumen auf den Frequenzgang (Helmholtz-Resonanz), und welche Fehler sind typisch (Leckage, Koerperschall, Reibgeraeusche)?
Unterfrage 2: Welche konkreten, beschaffbaren MEMS-Mikrofone (Hersteller, Typenbezeichnung, digital I2S/PDM vs. analog) haben eine ausreichend tiefe untere Grenzfrequenz fuer 20 Hz - z. B. Infineon IM69D130, TDK/InvenSense ICS-40180 oder ICS-43434, Knowles-Typen - mit Angabe von -3 dB-Punkt, Rauschen (AOP/SNR) und Verfuegbarkeit als Breakout?

Antwort auf Deutsch, mit Datenblatt-Links und konkreten Zahlenwerten.
```

## Ergebnis

## Kurzfazit

Für eine Bachelorarbeit mit einem analogen Stethoskop-Bruststück würde ich **nicht** versuchen, das MEMS-Mikrofon über einen langen Schlauch und einen absichtlich kleinen Helmholtz-Hohlraum anzukoppeln. Die praktisch robusteste Lösung ist:

1. **Membran des Bruststücks beibehalten**,
2. auf der der Haut abgewandten Seite eine **sehr kleine, abgedichtete Mikrofonkammer** vorsehen,
3. das MEMS-Mikrofon möglichst **direkt hinter der Membran** platzieren,
4. den akustischen Weg kurz und mit großem Querschnitt ausführen,
5. die komplette Konstruktion mit einem Lautsprecher oder Kalibriersignal von **10–1000 Hz** vermessen.

Die Auswahl des Mikrofons ist für 20 Hz entscheidend: **ICS-40180 und ICS-43434 sind für 20 Hz nicht ausreichend spezifiziert**, da ihre untere Grenzfrequenz bei etwa 60 Hz liegt. Geeigneter sind beispielsweise **Infineon IM68A130**, **Infineon IM69D130** mit Einschränkung sowie mehrere **Knowles-Typen mit 17–25 Hz LFRO**.

---

# 1. Praktische Kopplung des Bruststücks an ein MEMS-Mikrofon

## Empfohlener mechanischer Aufbau

Ein geeigneter Aufbau ist:

```text
Brust / Haut
   │
   ▼
Stethoskopmembran
   │  sehr kleine Luftkammer
   ▼
akustische Öffnung des MEMS-Mikrofons
   │
MEMS-Mikrofon auf kleiner Leiterplatte
   │
PDM/I²S/Analog-Auswerteelektronik
```

### Konstruktive Empfehlungen

- Das Mikrofon sollte **nicht lose im großen Innenraum des Bruststücks** liegen.
- Die Mikrofonöffnung muss zur Membran zeigen; bei einem **Bottom-Port-Mikrofon** muss die Öffnung auf der Leiterplatte exakt mit einem akustischen Kanal fluchten.
- Der Abstand zwischen Membran und Mikrofon sollte typischerweise nur wenige Millimeter betragen.
- Die Kammer muss gegenüber der Umgebung möglichst gut abgedichtet werden.
- Flexible Dichtungen aus Silikon oder weichem TPU sind geeigneter als harte, spielfreie Kunststoffkontakte.
- Das Mikrofon selbst sollte mechanisch vom Gehäuse entkoppelt werden, beispielsweise durch eine dünne Elastomerlagerung. Andernfalls werden Griff-, Reib- und Körperschallgeräusche direkt auf das Mikrofon übertragen.
- Für die Bachelorarbeit sollte die Mikrofonkammer austauschbare Einsätze besitzen, zum Beispiel mit 10, 50, 100 und 500 mm³ Volumen.

Die grundlegenden akustischen Untersuchungen zu Stethoskopen zeigen, dass ein kleineres Kammervolumen den Schalldruck beziehungsweise die Übertragung verbessern kann, während Schläuche tiefe Frequenzen abschwächen und stehende Wellen erzeugen. Eine Membran kann die Übertragung dämpfen und Resonanzen verschieben, erlaubt aber kleinere Luftvolumina. [web:29]

---

# 2. Dokumentierte Kopplungsvarianten

| Variante | Typischer Aufbau | Vorteile | Nachteile und typische Fehler |
|---|---|---|---|
| **Mikrofon direkt im Bruststück** | MEMS- oder Elektretmikrofon unmittelbar hinter der Stethoskopmembran | Kürzester akustischer Weg; geringe Schlauchverluste; gute Chancen für 20–600 Hz | Sehr empfindlich gegenüber Körperschall, Membrananschlag, Montageabweichungen und Leckagen |
| **Kurzer Schlauchstummel mit Mikrofon am Ende** | Bruststück – kurzer Silikon-/Vinylschlauch – Mikrofonkammer | Einfach nachzubauen; Mikrofon bleibt außerhalb des Bruststücks | Schlauchdämpfung, stehende Wellen, zusätzliche Hohlraumresonanz und Reibegeräusche |
| **Membran-/Kavitätsankopplung** | Stethoskopmembran speist eine definierte, abgedichtete Mikrofonkammer | Mechanisch gut reproduzierbar; Mikrofon kann geschützt im Gehäuse sitzen | Kammervolumen und Öffnung bestimmen den Frequenzgang stark; falsche Dimensionierung erzeugt Resonanzüberhöhungen |
| **Mikrofon in Schlauchkammer** | MEMS-Mikrofon sitzt in einer vergrößerten Kammer am Schlauchende oder im Ersatz-Ohrstück | Einfacher Prototyp; geringe Änderung am Bruststück | Großer Totraum, Helmholtz-Resonanz, Verluste im Schlauch und erhöhte Empfindlichkeit gegenüber Handhabungsgeräuschen |
| **Kontakt-/Vibrationsaufnehmer** | Piezoelement, piezoresistiver Sensor, Beschleunigungssensor oder Kontaktmikrofon direkt am Bruststück | Umgeht die Luftschallübertragung und ist weniger empfindlich gegenüber Umgebungslärm | Erfasst Körperschall statt ausschließlich Luftschall; starke Abhängigkeit von Anpressdruck und mechanischer Befestigung |
| **Hybridaufbau** | MEMS-Mikrofon plus Piezo-/Beschleunigungssensor | Luft- und Körperschallsignal können verglichen oder fusioniert werden | Höherer Schaltungs- und Kalibrieraufwand |

Ein Open-Source-Beispiel ist das **Fioscope**. Dort wird ein vorhandenes Stethoskop-Bruststück mit einer etwa **5 cm langen Leitung mit 8 mm Innendurchmesser** verbunden; am anderen Ende sitzt ein kleines Mikrofon in einem 3D-gedruckten Gehäuse. Das Bruststück besitzt eine Kunststoffmembran mit etwa 40 mm Durchmesser und ungefähr 0,35 mm Dicke. [web:21]

Ein weiteres einfaches elektronisches Stethoskop verwendet ein gewöhnliches Bruststück, einen etwa **5 cm langen Schlauch mit 6 mm Innendurchmesser** und ein Kondensatormikrofon am Schlauchende. [web:27] Diese Lösung ist mechanisch einfach, ist aber für eine möglichst unverfälschte Übertragung unterhalb von 60 Hz nicht optimal.

Die Literatur dokumentiert außerdem direkte elektronische Bruststücke mit Elektretmikrofonen, Sensorarrays sowie piezoelektrische, piezoresistive und beschleunigungsbasierte Kontaktaufnehmer. Beispielsweise werden ein PZT-Sensor mit einer Empfindlichkeit von 9,2 V/g unterhalb 1 kHz und ein Beschleunigungssensor als Kontaktmikrofon beschrieben. [web:16]

---

# 3. Einfluss des Hohlraumvolumens: Helmholtz-Resonanz

Eine abgeschlossene Kammer mit einer kleinen Öffnung beziehungsweise einem kurzen Hals verhält sich näherungsweise wie ein Helmholtz-Resonator:

\[
f_H =
\frac{c}{2\pi}
\sqrt{\frac{A}{V L_\mathrm{eff}}}
\]

mit

- \(f_H\): Resonanzfrequenz,
- \(c\): Schallgeschwindigkeit, etwa 343 m/s,
- \(A\): Querschnittsfläche des Halses,
- \(V\): Hohlraumvolumen,
- \(L_\mathrm{eff}\): effektive Halslänge einschließlich Endkorrekturen.

Die Abhängigkeit von Querschnitt, Volumen und Halslänge ist für Helmholtz-Resonatoren gut dokumentiert. [web:22]

### Konsequenzen

- Größeres Volumen \(V\) → **niedrigere Resonanzfrequenz**.
- Größere Öffnung \(A\) → **höhere Resonanzfrequenz**.
- Längerer Hals → **niedrigere Resonanzfrequenz**.
- Eine Resonanz innerhalb von 20–600 Hz kann die Herzgeräusche stark verfälschen.
- Eine Resonanz oberhalb des Nutzbands ist meist weniger problematisch, sofern ihre Flanken nicht bis in den Messbereich reichen.
- Starke Dämpfung durch weiche Dichtungen und Verluste im Schlauch reduziert die Güte, senkt aber auch den Nutzpegel.

### Zahlenbeispiel

Für einen Hals mit

- Innendurchmesser 6 mm,
- Querschnitt \(A \approx 28,3\,\text{mm}^2\),
- effektiver Länge \(L_\mathrm{eff}=10\) mm,

würde eine Helmholtz-Resonanz bei 20 Hz rechnerisch ein Volumen von ungefähr **21 ml** erfordern. Ein kleiner Hohlraum von beispielsweise 0,1–1 ml liegt bei denselben Halsabmessungen dagegen deutlich höher im Frequenzbereich.

Das ist ein wichtiger praktischer Punkt: Eine kleine Kammer erzeugt nicht automatisch eine tiefe Resonanz. Für eine Resonanz bei 20 Hz wäre entweder ein sehr großes Volumen oder ein sehr kleiner beziehungsweise sehr langer Hals nötig. Eine absichtlich auf 20 Hz abgestimmte Kammer wäre deshalb konstruktiv relativ groß und würde den Frequenzgang wahrscheinlich stark verfärben.

Für den beschriebenen Anwendungsfall ist daher besser:

> **Die Helmholtz-Resonanz nicht in das Band 20–600 Hz legen, sondern den akustischen Weg kurz halten und die Kammer klein sowie stark bedämpft ausführen.**

---

# 4. Typische Fehlerquellen

## Leckagen

Leckagen zwischen Membran, Bruststück und Mikrofonkammer führen zu:

- Verlust von statischem beziehungsweise niederfrequentem Druck,
- zusätzlicher Hochpasswirkung,
- veränderlichem Frequenzgang bei unterschiedlichem Anpressdruck,
- erhöhter Empfindlichkeit gegenüber Außengeräuschen.

Für 20-Hz-Signale ist die Abdichtung besonders kritisch. Eine kleine Leckage kann bei höheren Frequenzen kaum auffallen, aber den Bereich um 20–40 Hz deutlich abschwächen.

## Körperschall

Typische Quellen sind:

- Berührung des Gehäuses,
- Kabelbewegung,
- Druckänderungen der Hand,
- Reibung zwischen Membranring und Gehäuse,
- Anschlagen der Membran,
- Vibrationen der Leiterplatte.

Der Membranring sollte deshalb weich gedichtet, das Mikrofon aber nicht starr mit einer großen Gehäusefläche gekoppelt werden.

## Reibungs- und Handhabungsgeräusche

Beim Verschieben des Bruststücks entstehen häufig impulsartige Geräusche mit großem Pegel. Diese sind nicht unbedingt akustische Herzsignale, sondern mechanisch eingekoppelte Störungen. Die Literaturübersicht nennt für die beschriebenen Systeme allerdings keine quantitative Messung von Reibegeräuschen oder Leckageeffekten; diese Punkte müssen im eigenen Aufbau experimentell untersucht werden. [web:16]

## Schlauchverluste und stehende Wellen

Ein Schlauch ist nicht nur eine Leitung mit vernachlässigbarer Dämpfung. Er bildet zusammen mit Bruststück, Kammer und Mikrofon eine akustische Impedanz. In der Stethoskop-Akustik werden ausdrücklich eine Abschwächung tiefer Frequenzen und verzerrende stehende Wellen im Schlauch beschrieben. [web:29]

Für einen ersten Prototyp würde ich daher zwei Varianten parallel bauen:

1. **direkte Kammerankopplung**,  
2. **5-cm-Schlauchankopplung**.

Beide sollten mit demselben Mikrofon und derselben Elektronik vermessen werden.

---

# 5. Geeignete MEMS-Mikrofone

Die Herstellerangabe **LFRO** beziehungsweise **low-frequency roll-off** entspricht dem unteren -3-dB-Punkt relativ zur Empfindlichkeit bei 1 kHz. [web:33]

## Vergleich geeigneter und ungeeigneter Kandidaten

| Hersteller | Typenbezeichnung | Ausgang | Untere Grenzfrequenz / LFRO | Rauschen beziehungsweise SNR | AOP | Breakout/Evaluation | Eignung für 20 Hz |
|---|---|---:|---:|---:|---:|---|---|
| **Infineon** | **IM68A130** | Analog, single-ended | **10 Hz**, -3 dB relativ zu 1 kHz | **68 dB(A) SNR**; näherungsweise etwa 22 dB(A) äquivalentes Rauschen | **130 dB SPL** bei 10 % THD | Infineon-Flex-Evaluationsboards; kein verbreitetes Arduino-Hobbybreakout bekannt | **Sehr gut** |
| **Infineon** | **IM69D130** | Digital **PDM** | **28 Hz**, -3 dB | **69 dB(A) SNR**, äquivalenter Rauschboden etwa 25 dB SPL | **130 dB SPL** | Infineon **IM69D130 Microphone Shield2Go**, Flex-Evaluationboard | **Bedingt geeignet**; 20 Hz liegt bereits unterhalb des -3-dB-Punkts |
| **TDK/InvenSense** | **ICS-40180** | Analog, single-ended | **60 Hz**, -3 dB | **65 dBA SNR** | **124 dB SPL** | SparkFun Analog MEMS Microphone Breakout verfügbar | **Nicht ausreichend für S3/S4 bei 20–60 Hz** |
| **TDK/InvenSense** | **ICS-43434** | Digital **I²S** | **60 Hz**, untere Grenzfrequenz | **64 dBA SNR**, etwa 30 dBA SPL EIN | **120 dB SPL** | Breakout beispielsweise von EMMIC erhältlich | **Nicht ausreichend für 20 Hz** |
| **Knowles** | **SPK01A0LR5H-1 Raptor** | Analog, single-ended | **17 Hz**, -3 dB | **72 dB(A) SNR** | 122 dB SPL bei 1 % THD; 130 dB SPL bei 10 % THD | KAS-700-0175 On-Flex; Evaluationsboard verfügbar | **Sehr gut** |
| **Knowles** | **SPH21C3LR5H-1 Falcon** | Analog, differentiell | **18 Hz**, -3 dB | **68,5 dB(A) SNR** | 125/134 dB SPL bei 1/10 % THD | Knowles-Muskie-Evaluation; kein typisches Hobbybreakout | **Sehr gut** |
| **Knowles** | **SPK18R1LM4H-1 Hyperion** | Digital **PDM** | **20 Hz**, -3 dB | **70,5 dB(A) SNR** | 125/128 dB SPL bei 1/10 % THD | KAS-700-0192 On-Flex; Muskie-Evaluation | **Sehr gut** |
| **Knowles** | **SPH0655LM4H-1 Cornell II** | Digital **PDM** | **25 Hz**, -3 dB | **66 dB(A) SNR** | 130,5/132,5 dB SPL bei 1/10 % THD | KAS-700-0153 On-Flex; Muskie-Evaluation | **Gut, aber 20 Hz leicht gedämpft** |
| **Knowles** | **SPH18R1LM4H-1 Titan** | Digital **PDM** | **30 Hz**, -3 dB | **68,5 dB(A) SNR** | 123/129 dB SPL bei 1/10 % THD | KAS-700-0172 On-Flex; Muskie-Evaluation | **Bedingt geeignet** |
| **Knowles** | **SPH0645LM4H-1 Crawford** | Digital **I²S** | **45 Hz**, -3 dB | **65 dB(A) SNR** | 110/120 dB SPL bei 1/10 % THD | KAS-700-0137 On-Flex; verschiedene I²S-Module erhältlich | **Nicht ausreichend für 20–40 Hz** |

Die Werte der Knowles-Typen stammen aus dem aktuellen Knowles-Mikrofon-Auswahlleitfaden; dort wird LFRO ausdrücklich als -3-dB-Punkt relativ zur Empfindlichkeit bei 1 kHz definiert. [web:33] Für den IM68A130 nennt Infineon 10 Hz LFRO, 68 dB(A) SNR und 130 dB SPL AOP. [web:47] Beim IM69D130 sind 28 Hz LFRO, 69 dB(A) SNR und 130 dB SPL AOP angegeben. [web:6][web:1]

---

# 6. Bewertung der vom Fragesteller genannten TDK-/Infineon-Kandidaten

## Infineon IM69D130

Der IM69D130 ist elektrisch attraktiv:

- digitaler **PDM-Ausgang**,
- 69 dB(A) SNR,
- 130 dB SPL AOP,
- 28-Hz-LFRO,
- sehr kleine Bauform.

Er ist für den Bereich ab etwa 30 Hz gut verwendbar, aber **nicht ideal, wenn 20 Hz mit voller Amplitude und ohne Korrektur erfasst werden sollen**. Bei 20 Hz befindet man sich bereits im Abfallbereich. Die Herstellerdaten nennen eine 28-Hz-Grenze. [web:6]

Für einen Prototyp ist der IM69D130 trotzdem interessant, weil ein fertiges Shield2Go-Board existiert, das das PDM-Signal über einen ADAU7002 in I²S umsetzt. [web:55]

## TDK/InvenSense ICS-40180

Der ICS-40180 ist ein analoges Mikrofon mit:

- 60 Hz unterem -3-dB-Punkt,
- 65 dBA SNR,
- etwa 124 dB SPL AOP,
- analogem single-ended Ausgang.

Ein SparkFun-Breakout ist verfügbar. [web:43][web:44]

Für normale Lungengeräusche und Herzkomponenten oberhalb etwa 80 Hz kann er brauchbar sein. Für **S3/S4 bei 20–60 Hz ist er jedoch keine gute Wahl**, weil gerade der obere Teil dieses Bereichs bereits am unteren Übertragungsrand liegt.

## TDK/InvenSense ICS-43434

Der ICS-43434 besitzt:

- digitalen **I²S-Ausgang**,
- 24-Bit-Datenpfad,
- 64 dBA SNR,
- 120 dB SPL AOP,
- 60 Hz untere Grenzfrequenz.

TDK und das Datenblatt geben einen Frequenzbereich von ungefähr 60 Hz bis 20 kHz an. [web:2][web:4] Ein kleines EMMIC-Breakout mit 2,54-mm-Anschlüssen ist erhältlich. [web:42]

Der ICS-43434 ist deshalb für ein einfaches I²S-Projekt bequem, aber für die gestellte Anforderung **20–60 Hz nicht ausreichend**.

---

# 7. Meine konkrete Empfehlung

## Beste analoge Lösung

**Infineon IM68A130**

- 10 Hz LFRO,
- 68 dB(A) SNR,
- 130 dB SPL AOP,
- analoger Ausgang,
- sehr gut für einen eigenen rauscharmen Vorverstärker und ADC.

Er ist besonders geeignet, wenn die Bachelorarbeit die komplette analoge Signalkette untersuchen soll.

## Beste digitale Lösung

**Knowles SPK18R1LM4H-1 Hyperion**

- PDM,
- 20-Hz-LFRO,
- 70,5 dB(A) SNR,
- 128 dB SPL AOP bei 10 % THD.

Die Beschaffung erfolgt eher über Knowles-Flexboards oder das Muskie-Evaluationssystem als über ein klassisches Hobbybreakout. [web:33]

## Praktisch am einfachsten für ein digitales Entwicklungsboard

**Infineon IM69D130**

- fertige Shield2Go-Hardware,
- PDM- beziehungsweise I²S-Anbindung,
- ausreichend gute Rauschdaten,
- aber leichte Dämpfung bei 20 Hz.

Für die Arbeit sollte dann eine digitale Entzerrung untersucht werden. Eine Entzerrung kann den Amplitudenabfall korrigieren, aber **nicht das Mikrofonrauschen oder fehlende Signalanteile unterhalb der Grenzfrequenz zurückholen**.

## Nicht als Hauptkandidat für S3/S4

- TDK/InvenSense **ICS-40180**
- TDK/InvenSense **ICS-43434**
- Knowles **SPH0645LM4H-1**
- Knowles **SPH18R1LM4H-1**

Diese Bauteile sind für Sprache, Lungengeräusche und allgemeine Audioaufzeichnung interessant, liegen mit 30–60 Hz LFRO aber zu hoch für eine unverfälschte Erfassung des gesamten Bereichs 20–60 Hz.

---

# 8. Empfohlener Versuchsplan

Für die Bachelorarbeit würde ich mindestens diese vier Messaufbauten vergleichen:

| Aufbau | Mikrofonposition | Ziel |
|---|---|---|
| A | IM68A130 direkt hinter der Membran | Referenz für maximal kurze Luftankopplung |
| B | IM69D130 direkt hinter der Membran | Vergleich analog gegen PDM |
| C | IM68A130 über 5-cm-Schlauch | Einfluss des Schlauchs |
| D | Piezo- oder Beschleunigungssensor am Bruststück | Vergleich Luftschall gegen Körperschall |

Zu messen wären:

- Übertragungsfunktion von **10 Hz bis 1 kHz**,
- -3-dB-Grenzfrequenz,
- Resonanzfrequenzen,
- Einfluss verschiedener Kammervolumina,
- Einfluss einer definierten Leckage,
- Einfluss des Anpressdrucks,
- Körperschall bei Gehäuseberührung,
- Reibegeräusche beim Verschieben,
- SNR bei einem synthetischen 20-, 30-, 40- und 60-Hz-Signal.

Die zentrale Designentscheidung lautet damit:

> Für 20–600 Hz sollte das Mikrofon möglichst direkt und abgedichtet an die Bruststückmembran gekoppelt werden. Als erste Bauteile sind der **Infineon IM68A130** und der **Knowles SPK18R1LM4H-1** am überzeugendsten; der **IM69D130** ist eine praktikable digitale Alternative, während ICS-40180 und ICS-43434 für 20-Hz-Anteile zu hochpassig sind.

## Quellen

1. [MEMS and ECM Sensor Technologies for Cardiorespiratory ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC11548498/)
2. [Design optimization of 3D printed digital stetheocope ...](https://eprints.bournemouth.ac.uk/39307/)
3. [[PDF] Exploring Microphone Technologies for Digital Auscultation Devices](https://cris.unibo.it/retrieve/handle/11585/950564/15e85546-f2e7-4a1d-adcd-4e50b55b041b/micromachines-14-02092.pdf)
4. [Stethoscope acoustics](https://www.sciencedirect.com/science/article/abs/pii/S0022460X22003893)
5. [stive gabin's Post](https://www.linkedin.com/posts/stive-gabin-7132571a9_esp32-inmp441-bpm-activity-7436112206229835776-RBpB)
6. [GitHub - Fioscopeco/Fioscope_3d_print_v1: An affordable, open-source, high-quality digital stethoscope accessible to everyone using 3D-printed, widely accessible parts, and your smartphone. Based on the medically approved glia-x Stethoscope.](https://github.com/Fioscopeco/Fioscope_3d_print_v1)
7. [Résonateur de Helmholtz](https://ressources.univ-lemans.fr/AccesLibre/UM/Pedago/physique/02/meca/resohelm.html)
8. [Don't Miss a Beat](https://myrmanshelby.github.io/digital-stethoscope-landing-page/)
9. [Measurements on quarterwavelength tubes and Helmholtz ...](https://scispace.com/pdf/measurements-on-quarterwavelength-tubes-and-helmholtz-1enc8keds8.pdf)
10. [© 2025 IJRTI | Volume 10, Issue 4 April 2025 | ISSN: 2456-3315](https://ijrti.org/papers/IJRTI2504311.pdf)
11. [A bat-shape piezoresistor electronic stethoscope based on MEMS technology](https://www.sciencedirect.com/science/article/abs/pii/S0263224119307079)
12. [A simple electronic stethoscope for recording and playback of heart sounds](https://journals.physiology.org/doi/pdf/10.1152/advan.00073.2012)
13. [OMES: An Open-Source Multi-Sensor Modular Electronic Stethoscope](https://doaj.org/article/3016336f54954ef08db9f481e6e90905)
14. [Stethoscope acoustics](https://www.repository.cam.ac.uk/items/feadd88b-9e03-44fb-a875-c49f7c550259)
15. [Acoustic Design for MEMS Microphones - EDN](https://www.edn.com/acoustic-design-for-mems-microphones/)
16. [[PDF] IM69D130 - Mouser Electronics](https://www.mouser.com/datasheet/2/196/Infineon-IM69D130-DS-v01_00-EN-1274301.pdf)
17. [EV_ICS-43434-FX ICS-43434 TDK InvenSense Datasheet](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/8908/EV_ICS-43434-FX.pdf)
18. [ICS-40180 Datasheet | TDK InvenSense](https://invensense.tdk.com/download-pdf/ics-40180-datasheet/)
19. [ICS-43434 : Detailed Information - MEMS Microphones (Microphone)](https://product.tdk.com/en/search/sw_piezo/mic/mems-mic/info?part_no=ICS-43434)
20. [[PDF] Infineon-xensiv-mems-microphones-products-and-applications ...](https://www.allaboutcircuits.com/uploads/articles/Infineon-xensiv-mems-microphones-products-and-applications-presentation.pdf)
21. [IM69D130 - MEMS microphones](https://www.infineon.com/part/IM69D130)
22. [How to Use ICS-43434: Examples, Pinouts, and Specs](https://docs.cirkitdesigner.com/component/d7421ae3-66ea-459c-91fb-27eec1c310ab/ics-43434)
23. [EMMIC-ICS43434](https://www.cdiweb.com/datasheets/invensense/emmic-ics43434-ds.pdf)
24. [ICS-43434 : Detaillierte Informationen](https://product.tdk.com/de/search/sw_piezo/mic/mems-mic/info?part_no=ICS-43434)
25. [ICS-40180 : Detailed Information - MEMS Microphones (Microphone)](https://product.tdk.com/en/search/sw_piezo/mic/mems-mic/info?part_no=ICS-40180)
26. [.](https://www.xonelec.com/mpn/tdk/ics40180)
27. [ICS-40180 Datasheet(PDF) - TDK Electronics - ALLDATASHEET.COM](https://www.alldatasheet.com/datasheet-pdf/pdf/1137959/TDK/ICS-40180.html)
28. [ICS-43434 Datasheet, Alternatives & Specs - PartGenie](https://www.partgenie.ai/parts/ics-43434-mfg-001194)
29. [ICS-40180 | TDK InvenSense - WorldICTown](https://www.worldictown.com/productdetail/ICS-40180)
30. [My MEMS microphones notes etc. | Øyvind Teig](https://www.teigfam.net/oyvind/home/technology/243-my-mems-microphones-notes/)
31. [[PDF] MEMS Microphone - Knowles](https://www.knowles.com/docs/default-source/default-document-library/mm20-33366-000.pdf?Status=Master&sfvrsn=5bb171b1_0)
32. [[PDF] frequency-response-and-latency-of-mems-microphones---theory ...](https://www.knowles.com/docs/default-source/default-document-library/frequency-response-and-latency-of-mems-microphones---theory-and-practice.pdf?sfvrsn=4)
33. [MEMS MICROPHONES FOR FULL RANGE AUDIO AND ULTRASONIC](https://www.knowles.com/docs/default-source/default-document-library/mic-selection-guide-r5.pdf?sfvrsn=5fb74db1_7)
34. [SPH0645LM4H-B I2S Output Digital Microphone - Catalogs](https://pdf.directindustry.com/pdf/knowles-electronics-llc/sph0645lm4h-b-i2s-output-digital-microphone/127265-630002.html)
35. [[PDF] Knowles SPH0645LM4H-B SiSonic™ I2S digital microphone ...](https://www.mouser.com/datasheet/2/218/kas-700-0137-crawford-mic-on-flex-product-brief-re-1624260.pdf)
36. [[PDF] mm25 mems microphone high snr trimmable - Knowles](https://www.knowles.com/docs/default-source/default-document-library/an-19-mm25-mems-microphone.pdf?sfvrsn=b1ff71b1_9)
37. [[PDF] IM69D130 - Infineon Technologies](https://www.infineon.com/assets/row/public/documents/24/45/infineon-im69d130-pb--productbrief-en.pdf)
38. [Knowles slashes power consumption in MEMS microphones - News](https://siliconsemiconductor.net/article/94136/Knowles_slashes_power_consumption_in_MEMS_microphones)
39. [Mems Microphone - Spm0408he5h | PDF](https://www.scribd.com/document/70478883/Mems-Microphone-Spm0408he5h)
40. [Knowles Debuts Trio of SiSonic MEMS Microphones for High ...](https://audioxpress.com/news/knowles-debuts-trio-of-sisonic-mems-microphones-for-high-performance-tws-and-hearable-designs)
41. [MEMS Microphone Hookup Guide  ](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/2859/MEMS_Microphone_Hookup_Guide_Web.pdf)
42. [GitHub - sparkfun/SparkFun_Analog_MEMS_Microphone_Breakout_ICS-40180: Breakout board for the ICS-40180 bottom-port analog MEMs microphone by InvenSense.](https://github.com/sparkfun/SparkFun_Analog_MEMS_Microphone_Breakout_ICS-40180)
43. [SparkFun Analog MEMS Microphone Breakout - ICS-40180](https://www.robotshop.com/products/sparkfun-analog-mems-microphone-breakout-ics-40180)
44. [[PDF] knowles mems microphones portfolio - Thomasnet](https://cdn.thomasnet.com/ccp/30973684/351950.pdf)
45. [Infineon/IM69D130-Microphone-Shield2Go - GitHub](https://github.com/Infineon/IM69D130-Microphone-Shield2Go)
46. [EVAL-IM69D130V01-FLEX - Evaluation Boards | Infineon Technologies](https://www.infineon.com/evaluation-board/EVAL-IM69D130V01-FLEX)
47. [Evaluation Board, Shield2Go MEMS Microphone, 2 x XENSIV ...](https://at.farnell.com/en-AT/infineon/s2gomemsmicim69dtobo1/eval-board-mems-microphone/dp/3014284)
48. [EVALIM69D130FLEXKITTOBO1 INFINEON, Evaluation Kit ...](https://www.newark.com/infineon/evalim69d130flexkittobo1/evaluation-kit-mems-microphone/dp/63AK1619)
49. [Infineon Technologies XENSIV™ MEMS Microphone Flex Evaluation Boards](https://www.mouser.ca/new/infineon/infineon-xensiv-mems-boards/)
50. [Infineon S2GOMEMSMICIM69DTOBO1 Microphone Sensor Evaluation Board for IM69D130 IM69D130 Module](https://uk.rs-online.com/web/p/sensor-development-tools/2601162)
51. [EVALIM69D130FLEXKITTOBO1 Infineon Technologies - DigiKey](https://www.digikey.com/en/products/detail/infineon-technologies/EVALIM69D130FLEXKITTOBO1/8638920)
52. [Buy Infineon Evaluation Board for IM69D130 ...](https://www.industrybuying.com/controller-boards-infineon-IND.CON.536424592)
53. [SPH88R1LM4H-1](https://www.knowles.com/docs/default-source/default-document-library/sph18r1lm4h-1_titan_datasheet.pdf)
54. [Evaluation and Demonstration Boards and Kits(31) - HT Electronics](https://www.htelec.com/products/category/evaluation-boards-evaluation-and-demonstration-boards-and-kits/1338/all/1)
55. [KNOWLES' MEMS Microphone Eval-Kit Muskie | CODICO.com](https://www.codico.com/en/en/current/news/knowles-new-mems-microphone-evaluation-kit-muskie)
56. [[PDF] AN18 Knowles Flex Circuit and Coupons for Testing](https://www.knowles.com/docs/default-source/default-document-library/an18-knowles-flex-circuit-and-coupons-for-testing_updated.pdf)
57. [SPK01A0LR5H-1-7中文资料_最新报价](https://item.szlcsc.com/24031738.html)
58. [kc10143-c_muskie_mic_eval_bd](https://www.knowles.com/docs/default-source/model-downloads/kc10143_muskie_mic_eval_bd.pdf?sfvrsn=402876b1_8)
59. [[PDF] IM68A130V01](https://www.mouser.com/datasheet/3/70/1/Infineon_IM68A130_DataSheet_v01_10_EN.pdf)
60. [IM68A130 - MEMS microphones - Infineon Technologies](https://www.infineon.com/part/IM68A130)
61. [mems microphones digital (pdm) microphones](https://www.knowles.com/docs/default-source/default-document-library/mic-selection-guide-r5.pdf)
62. [XENSIV™ MEMS microphones - Infineon Technologies](https://www.infineon.com/assets/row/public/documents/24/66/infineon-xensiv-mems-microphones-productselectionguide-en.pdf)
63. [XENSIV IM68A130A: High-Performance Analog MEMS ...](https://components101.com/news/xensiv-im68a130a-high-performance-analog-mems-microphone-for-automotive-anc-applications)
64. [Audio Microphone Chips](https://www.globalspec.com/ds/4869/areaspec/microphone_type_audio)
65. [SPK01A0LR5H-1 - Seltech](https://seltech-international.com/product/spk01a0lr5h-1/)
66. [IM68A130 - 消费类 MEMS 麦克风 | Infineon英飞凌官网](https://www.infineon.cn/part/IM68A130)
