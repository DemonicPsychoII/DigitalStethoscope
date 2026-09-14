# Entwicklung eines digitalen Echtzeit-Stethoskops mit FHIR-Anbindung

## Aufgabenbeschreibung

Ziel der Bachelorarbeit ist die Entwicklung und Evaluation eines eingebetteten digitalen Stethoskop-Prototyps auf Basis eines vorhandenen analogen Bruststücks. Das Gerät soll Herzschallsignale erfassen, in Echtzeit verarbeiten und über Kopfhörer wiedergeben. Zu den Funktionen gehören eine wählbare Signalfilterung, die automatische Herzfrequenzbestimmung sowie die sichere Übertragung der ermittelten Herzfrequenz an ein System mit einer Schnittstelle nach dem Standard HL7 FHIR (Fast Healthcare Interoperability Resources). Ergänzend wird eine Wiedergabe mit reduzierter Geschwindigkeit als Hörhilfe implementiert.

Im Mittelpunkt steht die Untersuchung des Einflusses der Signalfilterung auf die Genauigkeit und Zuverlässigkeit der automatischen Herzfrequenzbestimmung. Dazu werden geeignete Filtervarianten ausgewählt, implementiert und unter definierten Testbedingungen verglichen. Die Anforderungen an die Filterung für die auditive Wiedergabe werden anhand der Fachliteratur hergeleitet und den Anforderungen der automatischen Auswertung gegenübergestellt. Auf dieser Grundlage wird diskutiert, inwieweit eine gemeinsame Filterung für beide Anwendungen geeignet ist.

Die automatische Herzfrequenzbestimmung wird quantitativ gegenüber einer geeigneten Referenz evaluiert. Testsignale, Referenzen, Bewertungsmetriken und Versuchsabläufe werden in der Planungsphase festgelegt. Der Echtzeit-Audiopfad, die wählbare Filterung, die reduzierte Wiedergabegeschwindigkeit und die sichere FHIR-Übertragung werden anhand definierter Funktionskriterien überprüft. Eine explorative Hörevaluation kann die literaturgestützte Betrachtung der auditiven Wiedergabe ergänzen, sofern die organisatorischen und zeitlichen Voraussetzungen gegeben sind.

Die Auswahl der Hardware- und Softwareplattform, der Signalverarbeitungsverfahren und des Bedienkonzepts erfolgt auf Grundlage der erarbeiteten Anforderungen. Das Ergebnis der Arbeit ist ein funktionsfähiger Prototyp mit dokumentierten Entwurfsentscheidungen, einer quantitativen Evaluation der Herzfrequenzbestimmung und einer Einordnung der technischen Grenzen.

Der Untersuchungsumfang konzentriert sich auf die digitale Signalverarbeitung und die prototypische Systemintegration. Die Eignung der Komponenten zur Signalerfassung wird anhand von Datenblättern und Fachliteratur beurteilt; eine messtechnische Charakterisierung der akustischen Übertragungskette ist nicht Bestandteil der Arbeit. Ebenfalls ausgenommen sind die Gehäuseentwicklung, dauerhafte Audiospeicherung, maschinelle Geräuschklassifikation sowie der Nachweis eines klinischen Nutzens oder einer regulatorischen Konformität.

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

Eine Personenwoche entspricht 40 Arbeitsstunden. Für Komponenten werden vorläufig 1–3 Wochen Lieferzeit als Kalenderzeit eingeplant; Recherche und Softwareplanung laufen parallel. Die Beschaffung beginnt frühzeitig nach der Komponentenauswahl. Die Ausarbeitung erfolgt entwicklungsbegleitend. Die Einarbeitung in der Firma wird separat mit 40–80 h angesetzt. Aufwandsschätzungen und Lieferzeiten werden in der Detailplanung konkretisiert; verbindliche Start- und Abgabetermine nach Bestätigung ergänzt.
