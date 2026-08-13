# Q3 Wiedergabegeschwindigkeit / Time-Stretch ohne Pitch-Shift

- **Run-ID:** R04-time-stretch
- **Preset:** medium
- **Modell:** preset/medium

## Fragestellung

```
Kontext: Bachelorarbeit, digitales Stethoskop auf ESP32-S3. Herzschall soll verlangsamt wiedergegeben werden (z. B. 0,5x / 0,75x), um Geraeusche hoerbarer zu machen. Problem: einfaches Verlangsamen verschiebt die Frequenzen aus dem diagnostischen Band (ca. 20-600 Hz).

Hauptfrage: Ist eine Verlangsamung der Herzschall-Wiedergabe ohne Tonhoehenaenderung (Time-Stretch) diagnostisch sinnvoll, und welche Verfahren kommen auf einem Mikrocontroller in Frage?

Unterfrage 1: Welche Time-Stretch-Verfahren (WSOLA, SOLA, PSOLA, Phase-Vocoder) sind fuer Signale mit transienten Anteilen wie S1/S2 geeignet, und welche Artefakte sind bei Faktoren 0,5x-0,75x zu erwarten?
Unterfrage 2: Welcher Rechen- und Speicheraufwand ist fuer WSOLA bzw. Phase-Vocoder bei ~2-8 kHz Abtastrate auf einem ESP32-S3 (240 MHz Xtensa LX7, Dual Core, mit DSP-Instruktionen) realistisch - gibt es publizierte Benchmarks oder existierende Implementierungen?

Antwort auf Deutsch, mit Quellen. Falls Time-Stretch on-device unrealistisch ist, bitte klar sagen und Alternativen nennen (z. B. Offline-Wiedergabe, Pitch-Shift-Toleranz).
```

## Ergebnis

## Kurzantwort

**Ja, eine Wiedergabe mit 0,5× oder 0,75× Geschwindigkeit ohne Tonhöhenänderung kann für die auditive Beurteilung von Herzgeräuschen sinnvoll sein – aber primär als zusätzliche Hörhilfe, nicht als diagnostisch validiertes Verfahren.** Die Frequenzlage von S1, S2 und vielen Herzgeräuschen bleibt dabei erhalten. Es werden jedoch die zeitlichen Verhältnisse verändert: S1 und S2 sowie systolische und diastolische Intervalle werden auseinandergezogen. Deshalb sollte immer zusätzlich eine Wiedergabe mit Originalgeschwindigkeit beziehungsweise eine unveränderte Aufzeichnung verfügbar sein.

Für ein ESP32-S3-Projekt ist **WSOLA beziehungsweise eine für transiente Signale modifizierte WSOLA-Variante die naheliegendste On-device-Lösung**. Ein kleiner Phase-Vocoder ist bei 2–8 kHz prinzipiell ebenfalls realisierbar, benötigt aber mehr Speicher, verursacht höhere Latenz und ist bei den transienten Anteilen von S1/S2 anfälliger für Artefakte. Eine vollständige klinische Beurteilung sollte nicht ausschließlich auf der verlangsamten Wiedergabe beruhen.

---

## 1. Medizinisch-akustische Einordnung

Herzschall ist kein stationäres, harmonisches Signal wie ein längerer Vokal. S1 und S2 sind kurze, nichtstationäre Ereignisse mit breitbandigen und zeitlich veränderlichen Anteilen. Literaturwerte liegen je nach Messmethode und Zielbereich ungefähr bei:

- S1/S2 überwiegend im Bereich von etwa **20–250 beziehungsweise 20–300 Hz**,
- Herzgeräusche häufig bis etwa **500–700 Hz**,
- für die allgemeine Auskultation werden teilweise Bereiche bis etwa **1,2 kHz** angegeben. [web:1][web:3][web:4]

Die im Projekt genannte Bandbreite von ungefähr **20–600 Hz** ist daher als praktischer Arbeitsbereich plausibel.

Bei einfacher Geschwindigkeitsänderung durch Resampling gilt näherungsweise:

\[
f_\mathrm{neu}=r f_\mathrm{alt}
\]

mit dem Geschwindigkeitsfaktor \(r\).

| Wiedergabegeschwindigkeit | Zeitdauer | Frequenzverschiebung |
|---|---:|---:|
| 0,5× | 2,0-fach | auf 50 % |
| 0,75× | 1,333-fach | auf 75 % |

Ein 600-Hz-Anteil würde bei 0,5× somit auf etwa 300 Hz verschoben. Ein 20-Hz-Anteil läge danach bei 10 Hz und wäre kaum noch hörbar. Bei 0,75× wäre der Bereich weniger problematisch, aber ebenfalls nach unten verschoben.

Beim **Time-Stretching ohne Tonhöhenänderung** bleiben die Spektralbereiche dagegen näherungsweise erhalten. Der Nutzen besteht daher darin, dass kurze Ereignisse und Geräuschverläufe länger wahrgenommen werden können, ohne sie in einen anderen Frequenzbereich zu verschieben.

Wichtig ist aber: Time-Stretching erzeugt keine neue diagnostische Information. Es kann die Wahrnehmbarkeit verbessern, verändert jedoch die Zeitstruktur und kann Artefakte hinzufügen. Für eine wissenschaftlich belastbare Aussage wäre ein Vergleichstest mit Original- und verlangsamten Signalen durch erfahrene Hörer beziehungsweise Ärztinnen und Ärzte erforderlich.

---

## 2. Vergleich der Verfahren

| Verfahren | Grundprinzip | Eignung für S1/S2 und Herzgeräusche | Typische Artefakte bei 0,5×–0,75× | Einschätzung für ESP32-S3 |
|---|---|---|---|---|
| **SOLA** | Überlappende Signalabschnitte werden so zusammengefügt, dass die Wellenformen möglichst gut anschließen | Grundsätzlich geeignet, aber weniger robust als WSOLA | Periodische Phasensprünge, Knacken, hörbare Übergänge, bei Transienten Verdopplung oder Auslassen | Einfach; als Baseline oder Prototyp geeignet |
| **WSOLA** | Wie SOLA, zusätzlich Suche nach derjenigen Analyseposition mit maximaler Wellenformähnlichkeit | **Am besten geeignet für eine einfache Echtzeitlösung**; funktioniert gut bei quasi-monophonen, kurzzeitigen Ereignissen | Stottern, Transientenverdopplung, Transientenauslassen, leichte Modulation; bei großer Streckung zunehmend auffällig | **Sehr gut realisierbar**, relativ wenig Speicher und keine FFT erforderlich |
| **PSOLA/TD-PSOLA** | Signal wird an erkannten Perioden beziehungsweise Grundtonperioden segmentiert und synchron überlagert | Für stimmhafte Sprache gut, für Herzschall meist ungeeignet, da S1/S2 nicht zuverlässig periodisch oder tonal sind | Falsche Periodenschätzung, Phasen- und Amplitudensprünge, unnatürliche Klangfarbe | Rechenaufwand nicht das Hauptproblem; robuste Periodenschätzung wäre das Problem |
| **Phase-Vocoder** | STFT, Änderung der zeitlichen Position der Spektralrahmen, Phasenrekonstruktion und inverse STFT | Für stationäre beziehungsweise tonalere Geräuschanteile gut; für S1/S2 nur mit Transientenerkennung oder Phase-Locking empfehlenswert | Transientenschmierung, „phasiness“, Nachhall-/Echoeindruck, Verlust der Schärfe von S2 | Möglich, aber höhere Latenz, mehr Speicher und komplexere Implementierung |
| **Hybrid WSOLA/Phase-Vocoder** | WSOLA für Transienten, Phase-Vocoder für stationäre Anteile | Qualitativ wahrscheinlich am besten | Je nach Umschaltung zusätzliche Übergangsartefakte | Für einen zweiten Entwicklungsschritt sinnvoll, nicht als Minimalimplementierung |

### WSOLA

WSOLA ist für dieses Projekt besonders interessant, weil die Methode im Zeitbereich arbeitet und die Anschlussstelle zwischen zwei Segmenten über eine Ähnlichkeitssuche optimiert. Dadurch werden hörbare Sprünge gegenüber einfachem OLA reduziert. SoundTouch verwendet beispielsweise eine WSOLA-ähnliche Zeitbereichsmethode und nennt für seine Implementierung eine typische Latenz von ungefähr 100 ms. [web:47]

Der zentrale Nachteil ist das Verhalten an Transienten. Für WSOLA sind insbesondere folgende Artefakte dokumentiert:

- **Transient doubling/stuttering**: Ein kurzer Impuls kann durch überlappende, verschobene Frames doppelt oder mehrfach erscheinen.
- **Transient skipping**: Ein Ereignis kann bei ungünstiger Segmentwahl teilweise übersprungen werden.
- Amplitudenmodulation oder leichtes „Flattern“ an S1/S2.

Diese Artefakte sind bei stark transienten Signalen besonders problematisch. [web:48][web:50]

Für Herzschall ist die Situation etwas günstiger als bei Schlagzeugsignalen: S1 und S2 sind zwar transiente Ereignisse, aber typischerweise nicht so kurz und impulsartig wie ein Schlagzeugattack. Andererseits ist gerade ihre zeitliche Form diagnostisch relevant. Deshalb sollte die WSOLA-Implementierung nicht blind auf beliebige Musikparameter abgestimmt werden.

Sinnvolle Maßnahmen sind:

1. **Transientenerkennung** mit Energieanstieg, spektralem Flux oder kurzzeitiger Hüllkurve.
2. Während eines erkannten S1/S2-Angriffs die Segmentierung nicht mehrfach über denselben Transienten laufen lassen.
3. Kürzere Frames oder spezielle Behandlung transienter Abschnitte.
4. Begrenzung der maximalen Suchverschiebung.
5. A/B-Vergleich zwischen Original, 0,75× und 0,5×.

Eine Transientenerkennung mit separater Behandlung ist auch für andere TSM-Verfahren ein etablierter Ansatz. [web:21][web:23]

### Phase-Vocoder

Der klassische Phase-Vocoder erhält die Frequenzen gut, ist aber anfällig für:

- **Transientenschmierung**: S2 kann weniger scharf und „weicher“ klingen.
- **Phasigkeit**: ein leicht künstlicher, flanger- oder hallähnlicher Eindruck.
- Verlust der vertikalen Phasenkohärenz zwischen Frequenzkanälen.
- Bei zu langen Fenstern: schlechte Zeitauflösung.
- Bei zu kurzen Fenstern: schlechte Frequenzauflösung und instabilere Tonhöhen-/Phasenverfolgung.

Diese Artefakte sind in der Literatur gut beschrieben. [web:51][web:53][web:56]

Für S1/S2 wäre ein einfacher Phase-Vocoder daher nicht die erste Wahl. Besser wären:

- **identity phase locking**,
- Onset-/Transientenerkennung,
- transientenbewusstes Phase-Vocoder-Verfahren,
- oder eine Hybridlösung aus WSOLA für Transienten und Phase-Vocoder für längere, stationäre Herzgeräuschanteile.

Ein solches hybrides Prinzip – Phase-Vocoder für tonale beziehungsweise stationäre Anteile und WSOLA für Transienten – wird auch in existierenden Time-Stretching-Bibliotheken verwendet. [web:41]

### PSOLA

PSOLA ist vor allem dann stark, wenn ein Signal eine gut definierte Grundperiode besitzt, beispielsweise bei Sprache. Herzschall enthält aber:

- stark gedämpfte und breitbandige Ereignisse,
- unterschiedliche Komponenten in S1 und S2,
- Geräuschanteile und mögliche Murmurs,
- keine durchgehend zuverlässige Grundfrequenz.

Eine pitch-synchrone Segmentierung kann daher bei Herzschall eher Fehlentscheidungen erzeugen. PSOLA wäre für dieses Projekt nur dann interessant, wenn ausschließlich ein stark periodischer, länger andauernder Anteil verarbeitet werden soll. Für vollständige Phonokardiogramme ist es nicht die bevorzugte Methode.

---

## 3. Realistische Parameter

Für eine erste Implementierung wären beispielsweise folgende Parameter plausibel:

### WSOLA bei 8 kHz

- Frame-Länge: **20–40 ms**, also 160–320 Samples
- Überlappung: **50–75 %**
- Synthese-Hop: etwa 5–15 ms
- Suchbereich: etwa **±5–10 ms**
- 16-Bit-Festkomma statt Float möglich
- Ringpuffer mit einigen Frames

Bei 2 kHz entspricht ein 30-ms-Frame nur 60 Samples. Das spart zwar Rechenzeit, verschlechtert aber die zeitliche und spektrale Darstellung. Für hörbare Wiedergabe ist 4–8 kHz daher wesentlich angenehmer. Bei 2 kHz liegt die Nyquist-Frequenz bei 1 kHz und reicht formal für 600 Hz, lässt aber wenig Reserve für Filter, Mikrofoncharakteristik und Anti-Aliasing.

### Phase-Vocoder bei 8 kHz

Beispiel:

- FFT-Größe: 256 oder 512
- Fenster: etwa 32–64 ms
- Hop-Größe: 25–50 % der FFT-Größe
- Hann-Fenster
- Phase-Voraussage pro Frequenz-Bin
- inverse FFT und Overlap-Add

Bei 8 kHz liefert eine 512-Punkt-FFT eine Binbreite von:

\[
\Delta f=\frac{8000}{512}\approx 15{,}6\ \mathrm{Hz}
\]

Eine 256-Punkt-FFT liefert etwa 31,25 Hz. Für niedrige Herzschallfrequenzen ist die größere FFT zwar spektral attraktiver, erhöht jedoch Latenz und verschlechtert die zeitliche Auflösung. Bei 2 kHz wären 512 Samples bereits 256 ms – für eine unmittelbare Auskultation wahrscheinlich zu träge.

---

## 4. Rechen- und Speicheraufwand auf dem ESP32-S3

### Verfügbare Benchmarks

Espressif veröffentlicht Benchmarks für die ESP-DSP-Bibliothek. Für den ESP32-S3 werden unter anderem folgende Werte angegeben:

| Operation | ESP32-S3, optimierte Implementierung |
|---|---:|
| 256-Punkt-Float-Dot-Product | 432 Zyklen |
| 256-Punkt-16-Bit-Dot-Product | 307 Zyklen |
| 256-Punkt-Float-FFT, Radix-2 | 20.139 Zyklen |
| 512-Punkt-Float-FFT, Radix-2 | 44.594 Zyklen |
| 1024-Punkt-Float-FFT, Radix-4 | 64.482 Zyklen |
| 256-Punkt-16-Bit-FFT | 3.412 Zyklen |
| 512-Punkt-16-Bit-FFT | 7.294 Zyklen |
| 1024-Punkt-16-Bit-FFT | 15.623 Zyklen |

Das sind Einzelbenchmarks der DSP-Grundoperationen, nicht vollständige Time-Stretching-Benchmarks. [web:31]

Bei 240 MHz entsprechen beispielsweise:

- 20.139 Zyklen etwa **84 µs**,
- 44.594 Zyklen etwa **186 µs**,
- 64.482 Zyklen etwa **269 µs**.

Die tatsächliche Zeit eines vollständigen Algorithmus ist größer, weil Fensterung, Magnituden-/Phasenberechnung, Phasenakkumulatoren, Bufferverwaltung, Overlap-Add und Audio-I/O hinzukommen.

### Grobe WSOLA-Schätzung

Eine WSOLA-Iteration benötigt typischerweise:

- mehrere Korrelationsberechnungen über den Überlappungsbereich,
- Auswahl des besten Kandidaten,
- Fensterung,
- Overlap-Add,
- Kopieren beziehungsweise Ringpufferverwaltung.

Für moderate Parameter und 16-Bit-DSP-Code ist auf dem ESP32-S3 eine **Echtzeitimplementierung sehr realistisch**. Eine grobe Größenordnung ist:

- wenige 10.000 bis einige 100.000 Zyklen pro Synthese-Hop, abhängig von Suchbereich und Korrelation,
- bei 8 kHz typischerweise etwa 70–200 Hops/s,
- damit grob einige Millionen bis einige zehn Millionen Zyklen/s.

Selbst eine konservative Größenordnung von 20–50 Millionen Zyklen/s entspricht bei 240 MHz ungefähr 8–21 % einer CPU-Kernkapazität. Für eine optimierte, einkanalige Implementierung ist WSOLA daher nicht grundsätzlich zu groß für den ESP32-S3. Der kritische Punkt ist eher die Qualität und die Echtzeitpufferung als die reine Rechenleistung.

Der Speicherbedarf liegt typischerweise nur bei:

- einigen Audioframes,
- einem Korrelationspuffer,
- Fensterkoeffizienten,
- Ein-/Ausgangs-Ringpuffern.

Je nach Implementierung sind **wenige Kilobyte bis einige zehn Kilobyte internes RAM** plausibel. Für eine reine Wiedergabe muss nicht die gesamte Aufzeichnung im RAM liegen; sie kann aus Flash, PSRAM oder einer Datei gestreamt werden.

### Grobe Phase-Vocoder-Schätzung

Für einen Phase-Vocoder mit 512-Punkt-Float-FFT und 25-%-Hop bei 8 kHz ergeben sich etwa 62,5 Analyseframes/s. Pro Frame werden mindestens benötigt:

- eine Vorwärts-FFT,
- eine inverse FFT,
- komplexe Spektralverarbeitung,
- Fensterung und Overlap-Add.

Die beiden FFTs liegen größenordnungsmäßig bei etwa:

\[
2 \cdot 44.594 \approx 89.000
\]

Zyklen pro Frame, bevor die zusätzliche Phasenverarbeitung berücksichtigt wird. Damit liegt der reine FFT-Anteil bei rund 5,6 Millionen Zyklen/s. Mit den übrigen Operationen ist eine Größenordnung von **10–30 Millionen Zyklen/s** für eine einfache Float-Implementierung plausibel. Eine 1024-Punkt-Variante kann trotz weniger Frames/s eine höhere Latenz und mehr Bufferbedarf verursachen.

Auch der Phase-Vocoder ist somit grundsätzlich machbar. Allerdings muss zusätzlich Speicher reserviert werden für:

- komplexe FFT- und IFFT-Puffer,
- Magnituden und Phasen,
- vorherige Phasenwerte,
- Fenster,
- Overlap-Add-Puffer,
- eventuell Transientenerkennung.

Bei 512 Punkten sind **einige 10 kB RAM** für eine schlanke Implementierung realistisch; mit Float-Puffern, mehreren Kanälen und komfortabler Bufferverwaltung kann der Bedarf deutlich höher werden. Bei 2 kHz wird die Rechenlast geringer, aber die für ausreichende Frequenzauflösung erforderliche Fensterdauer wird problematisch.

### Gibt es publizierte ESP32-S3-Time-Stretching-Benchmarks?

Nach den auffindbaren Quellen gibt es **ESP-DSP-Benchmarks für die notwendigen Grundoperationen**, aber keinen etablierten, direkt vergleichbaren Benchmark „WSOLA beziehungsweise Phase-Vocoder auf ESP32-S3 bei 8 kHz“ mit vollständiger Codebasis und festen Qualitätsparametern. Die Espressif-Werte sind deshalb eine gute Grundlage für eine Abschätzung, ersetzen aber keinen Messversuch auf dem konkreten Board.

Existierende Implementierungen sind überwiegend:

- allgemeine WSOLA-Implementierungen,
- SoundTouch mit WSOLA-ähnlicher Zeitbereichsmethode,
- PC-/Desktop-Phase-Vocoder,
- Forschungs- und Python-Bibliotheken wie PyTSMod mit OLA, WSOLA, TD-PSOLA und Phase-Vocoder. [web:47][web:65]

Sie können als Referenz für Algorithmen dienen, müssen für ESP-IDF/C angepasst, speicherseitig reduziert und hinsichtlich Float/Festkomma sowie Echtzeitverhalten vermessen werden.

---

## 5. Empfohlene Architektur für die Bachelorarbeit

### Stufe 1: Baseline

1. Mikrofonaufnahme bei 8 kHz, 16 Bit, mono.
2. Anti-Aliasing- und Hochpassfilter, beispielsweise unterhalb von 15–20 Hz.
3. Originalwiedergabe.
4. Resampling auf 0,5× und 0,75× als bewusst einfache Vergleichsreferenz.
5. WSOLA ohne Transientenerkennung.
6. WSOLA mit einfacher Transientenerkennung.
7. Messung von:
   - CPU-Last,
   - RAM,
   - Latenz,
   - Dropouts,
   - Frequenzlage,
   - S1/S2-Dauer,
   - subjektiven Artefakten.

### Stufe 2: Qualitätsverbesserung

Für die bevorzugte Lösung würde ich empfehlen:

- **WSOLA als Hauptverfahren**,
- 0,75× als Standardmodus,
- 0,5× als optionaler, stärker artefaktgefährdeter Modus,
- getrennte Behandlung von transienten und stationären Abschnitten,
- kein PSOLA für das komplette Signal,
- Phase-Vocoder nur als Vergleich oder zweite, anspruchsvollere Variante.

Ein sinnvoller Hörtest sollte dieselben Aufnahmen in drei Bedingungen abspielen:

1. Originalgeschwindigkeit,
2. Resampling mit Tonhöhenänderung,
3. WSOLA mit erhaltener Tonhöhe.

Bewertet werden könnten insbesondere die Erkennung von:

- S1 und S2,
- S3/S4,
- systolischen und diastolischen Geräuschen,
- hochfrequenten Murmurs,
- Klicks und Reibegeräuschen.

---

## 6. Falls On-device-Time-Stretching verworfen wird

Falls die verfügbare Entwicklungszeit oder die gewünschte Audioqualität für eine Echtzeit-WSOLA nicht ausreicht, sind diese Alternativen sinnvoll:

1. **Offline-Time-Stretching**  
   Die Aufnahme wird zunächst gespeichert und anschließend auf dem ESP32 oder auf einem PC/Smartphone verarbeitet. Dadurch sind komplexere Transientenerkennung und Phase-Locking möglich.

2. **Vorverarbeitung auf einem Smartphone oder PC**  
   Das ESP32-Stethoskop liefert PCM beziehungsweise WAV; die verlangsamte Wiedergabe erfolgt in einer App. Das ist qualitativ und experimentell am einfachsten.

3. **Nur 0,75× mit normaler Tonhöhe**  
   0,75× ist deutlich weniger anspruchsvoll als 0,5× und verursacht normalerweise weniger Artefakte.

4. **Normale Wiedergabe mit einstellbarer Verstärkung und Filterung**  
   Für diagnostische Zwecke kann eine gute Bandpassfilterung, Rauschunterdrückung, Lautstärkeanhebung und Kopfhörerwiedergabe sinnvoller sein als eine starke zeitliche Manipulation.

5. **Resampling als Vergleichs- oder Notfallmodus**  
   0,75× mit Tonhöhenverschiebung kann als robuste Minimalfunktion dienen, sollte aber ausdrücklich als nicht frequenztreue Wiedergabe gekennzeichnet werden.

## Schlussfolgerung

Für die Bachelorarbeit lautet die wahrscheinlich beste technische Entscheidung:

> **Ein einkanaliges WSOLA-Time-Stretching mit transientenbewusster Segmentierung ist auf dem ESP32-S3 bei 2–8 kHz realistisch und für Herzschall wahrscheinlich geeigneter als ein einfacher Phase-Vocoder.**

Ein Phase-Vocoder ist auf dem ESP32-S3 zwar ebenfalls realisierbar, aber ohne Transientenerkennung ist mit einer hörbaren Schmierung und einem künstlichen, phasigen Klang zu rechnen. **PSOLA ist wegen der fehlenden stabilen Periodizität des Herzschalls nicht die bevorzugte Lösung.**

Diagnostisch sollte die verlangsamte Wiedergabe als **zusätzliche Hörhilfe** verstanden werden. Sie kann das Erkennen länger dauernder oder schwacher Geräuschanteile erleichtern, darf aber nicht die unveränderte Originalwiedergabe und eine spätere klinische Validierung ersetzen.

## Quellen

1. [Time-Scale Modification Algorithms For Music Audio Signals](https://www.scribd.com/document/403092782/2011-DriedgerJonathan-TSM-MasterThesis-pdf)
2. [Audio Time Stretching with Controllable Phase Coherence - PitchTech](https://www.pitchtech.ch/Confs/AES142/index.html)
3. [Masterthesis](https://reposit.haw-hamburg.de/bitstream/20.500.12738/15713/1/MA_Latenzoptimierte%20Tonh%C3%B6henverschiebung.pdf)
4. [[PDF] Time Stretching & Pitch Shifting with the Web Audio API](https://repository.gatech.edu/bitstreams/f4b1290d-061f-45ab-8016-dfa8240b024e/download)
5. [[PDF] improved pvsola time-stretching and pitch-shifting for polyphonic](https://www.dafx12.york.ac.uk/papers/dafx12_submission_26.pdf)
6. [Time-Scale Modification Algorithms for Music Audio Signals](https://audiolabs-erlangen.de/content/05_fau/professor/00_mueller/01_group/2011_DriedgerJonathan_TSM_MasterThesis.pdf)
7. [[PDF] Time scale modification of audio using Non-negative Matrix ...](https://www.dafx.de/paper-archive/2019/DAFx2019_paper_38.pdf)
8. [Transient detection and preservation in the phase vocoder](https://quod.lib.umich.edu/i/icmc/bbp2372.2003.074?rgn=main;view=fulltext)
9. [[2202.07382] Phase Vocoder Done Right](https://arxiv.org/abs/2202.07382)
10. [PVSOLA: A Phase Vocoder with Synchronized OverLap-Add](http://recherche.ircam.fr/pub/dafx11/Papers/57_e.pdf)
11. [UNIVERSIT `A DI PADOVA](https://thesis.unipd.it/retrieve/6b0fb0a0-ebc7-4553-92b4-76661ac353f1/tesi.pdf)
12. [[PDF] Time Stretching & Pitch Shifting with the Web Audio API: Where are we at? | Semantic Scholar](https://www.semanticscholar.org/paper/Time-Stretching-&-Pitch-Shifting-with-the-Web-Audio-Dias-Matos/7a4c90f7d2de4c457073ff6c5a862cbd4db05f33)
13. [A new approach to transient processing in the phase vocoder](https://hal.science/hal-01161124/document)
14. [PhaVoRIT: A Phase Vocoder for Real-Time Interactive Time ...](https://hci.rwth-aachen.de/publications/karrer2006a.pdf)
15. [Audio Time-Scale Modification in the Context of Professional ...](https://www.mtg.upf.edu/files/publications/Phd-2002-Jordi-Bonada.pdf)
16. [Espressif DSP Library Benchmarks - ESP32](https://docs.espressif.com/projects/esp-dsp/en/latest/esp32/esp-dsp-benchmarks.html)
17. [Benchmark - ESP32-S3 - — ESP-SR latest documentation](https://docs.espressif.com/projects/esp-sr/en/latest/esp32s3/benchmark/README.html)
18. [FFT and Transforms | espressif/esp-dsp | DeepWiki](https://deepwiki.com/espressif/esp-dsp/4.2-fft-and-transforms)
19. [Read the Docs Template Documentation](https://espressif-docs.readthedocs-hosted.com/_/downloads/esp-dsp/en/latest/pdf/)
20. [Benchmarking Framework | espressif/esp-dsp | DeepWiki](https://deepwiki.com/espressif/esp-dsp/5.1-benchmarking-framework)
21. [ESP32-S3 Technical Reference Manual](https://documentation.espressif.com/esp32-s3_technical_reference_manual_en.html)
22. [Practical FFT on the ESP32-S3: DSP Acceleration and Real-World Usage](https://www.reddit.com/r/esp32/comments/1r5xhkz/practical_fft_on_the_esp32s3_dsp_acceleration_and/)
23. [espressif/esp-dsp • v1.2.0 • ESP Component Registry](https://components.espressif.com/components/espressif/esp-dsp/versions/1.2.0?language=)
24. [Audio FFT calculation on ESP32 or dedicated DSP?](https://www.reddit.com/r/embedded/comments/rg5rco/audio_fft_calculation_on_esp32_or_dedicated_dsp/)
25. [timestretch - Lib.rs](https://lib.rs/crates/timestretch)
26. [tmiw/esp32s3-benchmark](https://github.com/tmiw/esp32s3-benchmark)
27. [Writing a WSOLA time-stretcher for the Speech SDK](https://www.speechbase.ai/blog/writing-a-wsola-time-stretcher)
28. [Benchmark for Time-Stretching based on simple Phase ...](https://www.reddit.com/r/DSP/comments/1b0ffz6/benchmark_for_timestretching_based_on_simple/)
29. [jatinchowdhury18/time-stretcher](https://github.com/jatinchowdhury18/time-stretcher)
30. [Frequency Responses of Conventional and Amplified ... - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC7305673/)
31. [Analysis of the Four Heart Sounds Statistical Study and ...](https://clinicalcasereportsjournal.com/article/1000046/analysis-of-the-four-heart-sounds-statistical-study-and-spectro-temporal-characteristics)
32. [Computerized Heart Sounds Analysis](https://www.intechopen.com/chapters/19510)
33. [[PDF] Phonocardiographic Signal and Electrocardiographic Signal ...](https://pdfs.semanticscholar.org/1d4b/bd3793a61beb32b110efd8559588f69c7d1b.pdf)
34. [Chapter 39 - Auscultation of the Heart: General Principles](https://ia800603.us.archive.org/12/items/EvidenceBasedPhysicalDiagnosis/39AuscultationOfTheHeartGeneralPrinciples.pdf)
35. [Stethoscope Performance](https://thoracickey.com/stethoscope-performance/)
36. [12.4 Phonocardiogram (PCG) signal processing - Fiveable](https://fiveable.me/advanced-signal-processing/unit-12/phonocardiogram-pcg-signal-processing/study-guide/qvhCqH5XnP8wUiss)
37. [[PDF] CLASSIFICATION OF HEART SOUNDS USING TIME - DSpace](https://dspace.vut.cz/bitstreams/bae73908-5ddd-4939-9196-b8713c567749/download)
38. [Novel phonocardiography system for heartbeat detection from ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC10474097/)
39. [A Novel Digital Phonocardiography Method to Identify the ...](https://www.internationaljournalssrg.org/IJEEE/2022/Volume9-Issue12/IJEEE-V9I12P102.pdf)
40. [Digital Auscultation Analysis for Heart Murmur Detection](https://link.springer.com/article/10.1007/s10439-008-9611-z)
41. [University of Central Florida](https://stars.library.ucf.edu/cgi/viewcontent.cgi?article=2538&context=honorstheses)
42. [Spectral analysis of heart sounds associated with coronary ...](https://pubmed.ncbi.nlm.nih.gov/34649235/)
43. [Phono-spectrographic analysis of heart murmur in children](https://pmc.ncbi.nlm.nih.gov/articles/PMC1906774/)
44. [Computer aided analysis of phonocardiogram - PubMed](https://pubmed.ncbi.nlm.nih.gov/17701776/)
45. [GitHub - tmdarwen/PhaseVocoder: A cross platform command line utility allowing for time expansion/compression, pitch shifting and resampling of audio.](https://github.com/tmdarwen/PhaseVocoder)
46. [Phase Vocoder](https://github.com/ybdarrenwang/PhaseVocoder)
47. [Time-stretching (WSOLA) incorrect length output · Issue #206](https://github.com/JorenSix/TarsosDSP/issues/206)
48. [KAIST-MACLab/PyTSMod: An open-source Python ...](https://github.com/KAIST-MACLab/PyTSMod)
49. [Build software better, together](https://github.com/topics/phase-vocoder?l=c++)
50. [phase-vocoder](https://oramics.github.io/dsp-kit/api/module-phase-vocoder.html)
51. [TimeStretch - audiomentations documentation](https://iver56.github.io/audiomentations/waveform_transforms/time_stretch/)
52. [0xfe/vexwarp: Audio Time Stretching and Pitch Shifting](https://github.com/0xfe/vexwarp)
53. [Phase Vocoder — functional_phase_vocoder • torchaudio](https://mlverse.github.io/torchaudio/reference/functional_phase_vocoder.html)
54. [time stretching algorithm for audio without pitch shifting](https://github.com/Abletobetable/time-stretch)
55. [GitHub - bilibili/soundtouch: SoundTouch library compiled for ijkplayer/Android http://www.surina.net/soundtouch/sourcecode.html](https://github.com/bilibili/soundtouch)
56. [soundtouch/README.md at master · rspeyer/soundtouch](https://github.com/rspeyer/soundtouch/blob/master/README.md)
57. [A Review of Time-Scale Modification of Music Signals](https://sites.units.it/ramponi/teaching/DSP/materials/S03.4a/Driedger16_Review.pdf)
58. [UNIVERSIT `](https://thesis.unipd.it/bitstream/20.500.12608/16470/1/tesi.pdf)
59. [TSM Toolbox: MATLAB Implementations of Time-Scale ...](https://www.audiolabs-erlangen.de/content/resources/MIR/TSMtoolbox/2014_DriedgerMueller_TSM-Toolbox_DAFX.pdf)
60. [Proc. of the 8th Int. Conference on Digital Audio Effects (DAFx’05), Madrid, Spain, September 20-22, 2005](https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=ecd7529ab7059e2348e1d007f7a02370bdd05edc)
61. [Improving Time-Scale Modification of Music Signals Using ...](https://qmro.qmul.ac.uk/xmlui/bitstream/123456789/12184/2/Driedger%20Improving%20Time-Scale%20Modification%20of%20Music%20Signals%20Using%20Harmonic-Percussive%20Separation%202013%20Accepted.pdf)
62. [Phase Vocoder Done Right](https://ltfat.org/notes/ltfatnote050.pdf)
63. [AUDIO TIME STRETCHING WITH AN ADAPTIVE ... - PitchTech](https://www.pitchtech.ch/Confs/ICASSP2017/0000716.pdf)
64. [varispeed-sample/VarispeedDemo/SoundTouch/SoundTouchSettings.cs at master · naudio/varispeed-sample](https://github.com/naudio/varispeed-sample/blob/master/VarispeedDemo/SoundTouch/SoundTouchSettings.cs)
65. [IEEE/ACM TRANSACTIONS ON AUDIO, SPEECH AND LANGUAGE PROCESSING](http://arxiv.org/pdf/1612.05156.pdf)
66. [Time-scale Modification using the Phase Vocoder](https://old.iem.at/projekte/dsp/hammer/hammer.pdf)
67. [[PDF] A Review of Time-Scale Modification of Music Signals † | Semantic Scholar](https://www.semanticscholar.org/paper/A-Review-of-Time-Scale-Modification-of-Music-%E2%80%A0-Driedger-M%C3%BCller/0ac0fed7476412c7d85073e1cc2dd0923a1ce90f)
68. [Audio Time Stretching with an Adaptive Multiresolution Phase ...](https://www.pitchtech.ch/Confs/ICASSP2017/index.html)
