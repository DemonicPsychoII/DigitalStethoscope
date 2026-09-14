# Entwicklung eines digitalen Echtzeit-Stethoskops mit FHIR-Anbindung

## Aufgabenbeschreibung

Ziel ist die Entwicklung und Evaluation eines eingebetteten digitalen Stethoskop-Prototyps auf Basis eines vorhandenen analogen Bruststücks. Er soll Herzschallsignale erfassen, in Echtzeit filtern und über Kopfhörer wiedergeben, die Herzfrequenz automatisch bestimmen und sicher über HL7 FHIR (Fast Healthcare Interoperability Resources) übertragen. Ergänzend wird eine Wiedergabe mit reduzierter Geschwindigkeit als Hörhilfe implementiert. Ihre Aufnahme in den Funktionsumfang wird anhand vergleichbarer marktverfügbarer Geräte begründet.

Untersucht wird der Einfluss wählbarer Filtervarianten auf die Genauigkeit und Zuverlässigkeit der automatischen Herzfrequenzbestimmung. Die Varianten werden unter definierten Testbedingungen verglichen. Auditive Filteranforderungen werden literaturgestützt hergeleitet und denen der automatischen Auswertung gegenübergestellt. Ergebnisoffen wird diskutiert, ob eine gemeinsame Filterung für beide Anwendungen geeignet ist.

Die automatische Herzfrequenzbestimmung wird quantitativ gegenüber einer geeigneten Referenz evaluiert. Testsignale, Referenzen, Bewertungsmetriken und Versuchsabläufe werden in der Planungsphase festgelegt. Der Echtzeit-Audiopfad, die wählbare Filterung, die reduzierte Wiedergabegeschwindigkeit und die sichere FHIR-Übertragung werden anhand definierter Funktionskriterien überprüft. Eine explorative Hörevaluation kann die literaturgestützte Betrachtung der auditiven Wiedergabe ergänzen, sofern die organisatorischen und zeitlichen Voraussetzungen gegeben sind.

Hardware- und Softwareplattform, Signalverarbeitungsverfahren und Bedienkonzept werden anhand der erarbeiteten Anforderungen ausgewählt. Ergebnis ist ein funktionsfähiger Prototyp mit dokumentierten Entwurfsentscheidungen, Evaluation und Einordnung seiner Grenzen.

Die Eignung der Komponenten zur Signalerfassung wird anhand von Datenblättern und Fachliteratur beurteilt; eine messtechnische Charakterisierung der akustischen Übertragungskette ist nicht Bestandteil der Arbeit. Ebenfalls ausgenommen sind die Gehäuseentwicklung, dauerhafte Audiospeicherung, maschinelle Geräuschklassifikation sowie der Nachweis eines klinischen Nutzens oder einer regulatorischen Konformität.

## Geschätzter Arbeitsaufwand

| Arbeitspaket | Aufwand |
|---|---:|
| Anforderungen, Recherche und Evaluationsplanung | 24 h |
| Systemplanung: Komponenten, Schnittstellen und Aufbaukonzept | 16 h |
| Softwareplanung: Architektur, Datenfluss und Aufgabenverteilung | 16 h |
| Beschaffung: Verfügbarkeit prüfen, Auswahl und Bestellung | 8 h |
| Hardwareaufbau und Inbetriebnahme | 24 h |
| Softwareentwicklung: Audioverarbeitung, Herzfrequenz, Bedienung und FHIR | 104 h |
| Systemintegration, Funktionstests und Fehlerbehebung | 28 h |
| Evaluation und Ergebnisauswertung | 44 h |
| Ausarbeitung, Überarbeitung und Vortrag | 56 h |
| **Kernarbeit gesamt** | **320 h (8 Personenwochen)** |
| Zusätzlicher Puffer (ca. 20 %) | 64 h |

Eine Personenwoche entspricht 40 Arbeitsstunden. Für Komponenten werden vorläufig 1–3 Wochen Lieferzeit als Kalenderzeit eingeplant; Recherche und Softwareplanung laufen parallel. Die Ausarbeitung erfolgt entwicklungsbegleitend. Die Einarbeitung in der Firma wird separat mit 40–80 h angesetzt. Aufwandsschätzungen und Lieferzeiten werden in der Detailplanung konkretisiert; verbindliche Start- und Abgabetermine nach Bestätigung ergänzt.
