# Anforderungen und Abgrenzung

[Zum Einstieg](README.md) · [Offene Punkte](offene-punkte.md)

Funktionsumfang → eigene Zielwerte → ausdrücklich ausgeschlossene Nachweise.

**9 aktive Einheiten.** Schreibreihenfolge: Definition → Mechanismus → Werte → Folgerung. Die Aussagen sind Material, kein fertiger Fließtext.

## Schreibbausteine

### Werte und dokumentierte Befunde

<a id="u027"></a>
**U027 · EIGENER ZIELWERT / VORLÄUFIGER VORSCHLAG**

Interne Echtzeitlatenzvorstellung: bei 0,5× unkritisch; für 1,0× Zielband <30 ms, besser <10 ms.

**Ursprung:** [preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:48](../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md#L48)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

### Folgerungen, Entwurfsentscheidungen und Grenzen

<a id="u008"></a>
**U008 · EIGENE ANFORDERUNG**

Ausgeschlossen sind Gehäuseentwicklung, dauerhafte Audiospeicherung, maschinelle Geräuschklassifikation, klinischer Nutzennachweis und regulatorische Konformität.

**Ursprung:** [preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Abgabe.md:13](../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Abgabe.md#L13)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u010"></a>
**U010 · EIGENE ANFORDERUNG**

In der internen Fassung sind drei Filterzustände vorgesehen: Raw (Referenz), murmur-optimiert und BPM-optimiert; die Wahl soll im laufenden Betrieb möglich sein.

**Ursprung:** [preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:11,64](../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md#L11)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u034"></a>
**U034 · EIGENE ANFORDERUNG**

Intern als nicht Teil der Arbeit bezeichnet: Gehäuse, Audio-Persistenz, alternative Bruststückgeometrien, MDR/IEC-62304-Konformität und ML-basierte Klassifikation.

**Ursprung:** [preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:60](../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md#L60)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u007"></a>
**U007 · EIGENE ENTSCHEIDUNG / ENTWURFSEMPFEHLUNG**

Komponenteneignung wird anhand von Datenblättern und Fachliteratur beurteilt; messtechnische Charakterisierung der akustischen Übertragungskette ist in der Abgabefassung ausgeschlossen.

**Ursprung:** [preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Abgabe.md:13](../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Abgabe.md#L13)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u031"></a>
**U031 · EIGENE ANFORDERUNG**

Lungenmodus: Interface/Symbole und Live-Wiedergabe; keine BPM, Filter, Time-Stretch- oder FHIR-Funktion.

> **Überholt (Stand integration, 2026-10-22):** Der Lungenmodus gehört nicht zum MVP. Seit 14.10. sind optionale Anforderungen vorerst entfernt, darunter Lung. Aktuell: Nur Herz. Lung ist optional und braucht das Display. – siehe [MVP-Entscheidungen 14.10. (Umfang)](../Development/system/planning/mvp-decisions-2026-10-14.md#scope), [Produktumfang](../Development/system/spec/product-scope.md#goal-and-boundary).

**Ursprung:** [preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:52](../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md#L52)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u003"></a>
**U003 · EIGENE ANFORDERUNG**

Untersucht wird der Einfluss wählbarer Filtervarianten auf Genauigkeit und Zuverlässigkeit der automatischen Herzfrequenzbestimmung; auditive Filteranforderungen sollen literaturgestützt hergeleitet und mit den Anforderungen der automatischen Auswertung verglichen werden.

**Ursprung:** [preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Abgabe.md:7](../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Abgabe.md#L7)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u020"></a>
**U020 · EIGENE ENTSCHEIDUNG / ENTWURFSEMPFEHLUNG**

Verlangsamung ist intern als Hörhilfe und nicht als diagnostischer Validitätsnachweis eingeordnet; WSOLA mit Stufen 1,0× / 0,75× / 0,5× ist vorgeschlagen, Originalgeschwindigkeit bleibt verfügbar.

> **Überholt (Stand integration, 2026-10-22):** WSOLA-Stufen 1,0×/0,75×/0,5× sind kein MVP-Bestandteil. Seit 14.10. ist Replay auch keine optionale Anforderung mehr. Aktuell: Die Idee bleibt in den Entscheidungen vom 11.10. festgehalten; MVP-BPM arbeitet mit begrenztem Streaming-Zustand statt Sitzungsaufnahme. – siehe [MVP-Entscheidungen 14.10. (Anforderungen)](../Development/system/planning/mvp-decisions-2026-10-14.md#requirements), [Design: MVP-Sitzungsbasis](../Development/system/design/interfaces-and-behavior.md#mvp-session-baseline).

**Ursprung:** [preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:41](../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md#L41)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u002"></a>
**U002 · EIGENE ANFORDERUNG**

Zusätzlich soll eine Wiedergabe mit reduzierter Geschwindigkeit als Hörhilfe implementiert und ihre Aufnahme in den Funktionsumfang anhand marktverfügbarer Geräte begründet werden.

> **Überholt (Stand integration, 2026-10-22):** Verlangsamte Wiedergabe gehört nicht zum MVP-Umfang (Feedback 2026-10-07, Entscheidung 2026-10-11). Seit 14.10. sind alle optionalen Anforderungen vorerst entfernt, darunter verlangsamte Wiedergabe. Aktuell: keine Anforderung; die Idee bleibt in den Entscheidungen vom 11.10. festgehalten. Der Wortlaut der Aufgabenbeschreibung selbst ist nicht angepasst, siehe offene Punkte. – siehe [MVP-Entscheidungen 14.10. (Anforderungen)](../Development/system/planning/mvp-decisions-2026-10-14.md#requirements), [MVP-Entscheidungen 11.10.](../Development/system/planning/mvp-decisions-2026-10-11.md#confirmed-scope-and-behavior), [Systemanforderungen: entfernte Anforderungen](../Development/system/requirements/system-requirements.md#retired-requirements).

**Ursprung:** [preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Abgabe.md:5](../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Abgabe.md#L5)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.
