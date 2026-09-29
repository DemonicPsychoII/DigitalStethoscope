# Latenz-Ziel fuer Echtzeit-Audiopfad

- **Run-ID:** R09-latenz
- **Preset:** fast
- **Modell:** preset/fast

## Fragestellung

```
Kontext: Bachelorarbeit, digitales Stethoskop mit Echtzeit-Audiopfad (Mikrofon -> DSP -> DAC -> Kopfhoerer). 'Echtzeit' soll quantifiziert werden.

Hauptfrage: Welche End-to-End-Latenz ist fuer ein digitales Stethoskop als Zielwert begruendbar, und ab welcher Latenz wird die Verzoegerung bei Live-Auskultation stoerend?

Unterfrage 1: Welche Latenzschwellen nennt die Literatur fuer Live-Monitoring von Audio bzw. fuer taktil-auditive Kopplung (Anwender beruehrt das Bruststueck und hoert gleichzeitig) - typische Werte fuer 'nicht wahrnehmbar' vs. 'stoerend'?
Unterfrage 2: Welche Latenz geben kommerzielle elektronische Stethoskope (z. B. 3M Littmann Core/3200, Eko) an bzw. was ist aus Teardowns/Reviews bekannt?

Antwort auf Deutsch, kurz und mit Quellen. Nenne einen konkreten empfohlenen Zielwert in Millisekunden.
```

## Ergebnis

Für ein digitales Stethoskop ist ein **End-to-End-Zielwert von ≤10 ms** gut begründbar; **ideal sind eher 5 ms oder weniger**. Ab **ca. 10–15 ms** wird die Verzögerung in Live-Monitoring- und Performer-Szenarien meist bemerkbar, und **ab etwa 15–30 ms** wird sie oft als störend beschrieben.[5][3][6]

## Kurz eingeordnet
- **„Nicht wahrnehmbar / sehr gut“:** < 10 ms, in manchen Monitoring-Kontexten sogar < 6 ms als „immediate“ bzw. „excellent“ beschrieben.[6][7]
- **„Gerade noch akzeptabel“:** etwa 10–15 ms; hier beginnt bei vielen Nutzern bereits ein spürbarer Effekt.[5][6]
- **„Störend“:** ab etwa 15–30 ms, abhängig von Aufgabe, Instrument und Person.[5][3]

## Für die taktil-auditive Kopplung beim Abhören
Wenn der Anwender das Bruststück berührt und gleichzeitig hört, sollte die Latenz möglichst deutlich unter der Wahrnehmungsschwelle bleiben. Für audio-haptische Asynchronie liegen Detektionsschwellen in der Literatur zwar teils deutlich höher, aber für eine **direkte, präzise Live-Auskultation** ist ein Bereich **unter 10 ms** sinnvoller als ein bloß „eben noch nicht wahrnehmbarer“ Bereich.[8]

## Kommerzielle Geräte
In den hier vorliegenden Quellen finden sich **keine belastbaren, offiziell publizierten Latenzwerte** für konkrete Produkte wie **3M Littmann CORE/3200** oder **Eko**. Allgemein gilt aber: Jede A/D- und D/A-Wandlung addiert typischerweise etwa **1 bis 1,5 ms**; Bluetooth-/Funkpfade können die Latenz dagegen stark erhöhen.[5][4]

**Empfehlung für die Bachelorarbeit:** Als Zielwert **≤10 ms End-to-End**, mit **präferiertem Entwicklungsziel ≤5 ms**. Ab **~15 ms** würde ich die Verzögerung bei Live-Auskultation als potenziell störend bewerten.[5][6]

## Quellen

1. [Monitor Engingeers what is your latency threshold when it ...](https://www.reddit.com/r/livesound/comments/1mug4ab/monitor_engingeers_what_is_your_latency_threshold/)
2. [The Effects of Latency on Live Sound Monitoring](https://boseperformer.com/images/7/7b/AES_Latency.pdf)
3. [Low Latency Audio Processing](https://qmro.qmul.ac.uk/xmlui/bitstream/handle/123456789/44697/WANG_Yonghao_Final_PhD_070918.pdf?sequence=1)
4. [What Is Sound Latency? How to Test & Fix Audio Lag](https://ultimatepctools.com/blog/sound-latency-test-guide/)
5. [Latency and Its Effect on Performers](https://www.churchproduction.com/education/latency-and-its-affect-on-performers/)
6. [Audio Latency Calculator for Recording and Live Sound - CMUSE](https://www.cmuse.org/audio-latency-calculator/)
7. [Audio Latency Test Online — Free Browser Tool to Measure ...](https://audiolatencytest.org/)
8. [Detection Threshold of Audio Haptic Asynchrony in a Driving Context](https://arxiv.org/pdf/2307.05451v1.pdf)
9. [1](https://arxiv.org/pdf/2509.02626v1.pdf)
10. [How to measure audio latency? How much delay is tolerable by ...](https://www.provideocoalition.com/how-to-measure-audio-latency-how-much-delay-is-tolerable-by-human-beings-when-monitoring-their-own-voice-live/)
