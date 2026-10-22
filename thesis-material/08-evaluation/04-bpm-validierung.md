# Evaluation: BPM-Validierung

[Zum Einstieg](../README.md) · [Offene Punkte](../offene-punkte.md)

Referenz synchronisieren → Fehlermaße → eigene Toleranzen → Auswertung.

**16 aktive Einheiten.** Schreibreihenfolge: Definition → Mechanismus → Werte → Folgerung. Die Aussagen sind Material, kein fertiger Fließtext.

## Schreibbausteine

### Begriffe und Definitionen

<a id="a049"></a>
**A049 · LITERATURFAKT / REGEL**

Bland–Altman-Bias ist der Mittelwert der Differenzen; 95-%-Übereinstimmungsgrenzen sind mittlere Differenz ±1,96 SD.

**Ursprung:** [preThesis/03-recherche/R03-bpm-referenz.md:63-71](../../preThesis/03-recherche/R03-bpm-referenz.md#L63)
**Belege:** [Bland, J 1986 · bland_altman](https://doi.org/10.1016/S0140-6736(86)90837-8) — Fundstelle: Abstract and bibliographic metadata; full text paywalled (aus Stage 1; am Original prüfen) · 🔒 Volltextzugang prüfen: Publisher full text may be paywalled.; [Giavarina, D 2015 · bland_review](https://pmc.ncbi.nlm.nih.gov/articles/PMC4470095/) — Seite prüfen (übernommene Angabe: Methods overview; section/page unverified); [ANSI/AAMI EC13:2002 · ec13](https://webstore.ansi.org/standards/aami/ansiaamiec132002) — Fundstelle: Clause 4.2.7 (accessible copy; official publication status not verified) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig

<a id="a047"></a>
**A047 · LITERATURFAKT / REGEL**

Der Fehler pro Messung lautet e_i=HR_PCG,i−HR_EKG,i.

**Ursprung:** [preThesis/03-recherche/R03-bpm-referenz.md:63-71](../../preThesis/03-recherche/R03-bpm-referenz.md#L63)
**Belege:** [Bland, J 1986 · bland_altman](https://doi.org/10.1016/S0140-6736(86)90837-8) — Fundstelle: Abstract and bibliographic metadata; full text paywalled (aus Stage 1; am Original prüfen) · 🔒 Volltextzugang prüfen: Publisher full text may be paywalled.; [Giavarina, D 2015 · bland_review](https://pmc.ncbi.nlm.nih.gov/articles/PMC4470095/) — Seite prüfen (übernommene Angabe: Methods overview; section/page unverified); [ANSI/AAMI EC13:2002 · ec13](https://webstore.ansi.org/standards/aami/ansiaamiec132002) — Fundstelle: Clause 4.2.7 (accessible copy; official publication status not verified) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig

<a id="a048"></a>
**A048 · LITERATURFAKT / REGEL**

MAE ist der Mittelwert absoluter bpm-Fehler; MAPE ist der mittlere absolute Fehler relativ zur EKG-Herzfrequenz in Prozent.

**Ursprung:** [preThesis/03-recherche/R03-bpm-referenz.md:63-71](../../preThesis/03-recherche/R03-bpm-referenz.md#L63)
**Belege:** [Bland, J 1986 · bland_altman](https://doi.org/10.1016/S0140-6736(86)90837-8) — Fundstelle: Abstract and bibliographic metadata; full text paywalled (aus Stage 1; am Original prüfen) · 🔒 Volltextzugang prüfen: Publisher full text may be paywalled.; [Giavarina, D 2015 · bland_review](https://pmc.ncbi.nlm.nih.gov/articles/PMC4470095/) — Seite prüfen (übernommene Angabe: Methods overview; section/page unverified); [ANSI/AAMI EC13:2002 · ec13](https://webstore.ansi.org/standards/aami/ansiaamiec132002) — Fundstelle: Clause 4.2.7 (accessible copy; official publication status not verified) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig

### Mechanismen und Zusammenhänge

<a id="a050"></a>
**A050 · LITERATURFAKT / REGEL**

Ein Korrelationskoeffizient zeigt Zusammenhang, aber keinen ausreichenden Nachweis der Übereinstimmung zweier Messverfahren.

**Ursprung:** [preThesis/03-recherche/R03-bpm-referenz.md:71-85](../../preThesis/03-recherche/R03-bpm-referenz.md#L71)
**Belege:** [Bland, J 1986 · bland_altman](https://doi.org/10.1016/S0140-6736(86)90837-8) — Fundstelle: Abstract and bibliographic metadata; full text paywalled (aus Stage 1; am Original prüfen) · 🔒 Volltextzugang prüfen: Publisher full text may be paywalled.; [Giavarina, D 2015 · bland_review](https://pmc.ncbi.nlm.nih.gov/articles/PMC4470095/) — Seite prüfen (übernommene Angabe: Methods overview; section/page unverified); [ANSI/AAMI EC13:2002 · ec13](https://webstore.ansi.org/standards/aami/ansiaamiec132002) — Fundstelle: Clause 4.2.7 (accessible copy; official publication status not verified) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig

### Werte und dokumentierte Befunde

<a id="a052"></a>
**A052 · LITERATUR- / HERSTELLERWERT · ersetzt U048**

ANSI/AAMI EC13:2002 nennt für EKG-Herzfrequenzmesser mindestens 30–200 bpm und Anzeigeabweichung höchstens ±10 % oder ±5 bpm, je nachdem, welcher Wert größer ist.

**Ursprung:** [preThesis/03-recherche/R03-bpm-referenz.md:87-110](../../preThesis/03-recherche/R03-bpm-referenz.md#L87)
**Belege:** [ANSI/AAMI EC13:2002 · ec13](https://webstore.ansi.org/standards/aami/ansiaamiec132002) — Fundstelle: Clause 4.2.7 (accessible copy; official publication status not verified) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [IEC 60601-2-27:2011 · iec60601](https://webstore.iec.ch/en/publication/2638) — Fundstelle: Scope / standard description; accuracy clause not inspected (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [U.S 1998 · fda_ec13_guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/cardiac-monitor-guidance-including-cardiotachometer-and-rate-alarm-guidance-industry) — Seite prüfen · **LINK DEFEKT**

<a id="a055"></a>
**A055 · LITERATUR- / HERSTELLERWERT**

Die Normlogik max(5 bpm, 10 % des Referenzwertes) ergibt bei 40 bpm ±5 bpm, 60 bpm ±6 bpm, 100 bpm ±10 bpm und 200 bpm ±20 bpm.

**Ursprung:** [preThesis/03-recherche/R03-bpm-referenz.md:100-111](../../preThesis/03-recherche/R03-bpm-referenz.md#L100)
**Belege:** [ANSI/AAMI EC13:2002 · ec13](https://webstore.ansi.org/standards/aami/ansiaamiec132002) — Fundstelle: Clause 4.2.7 (accessible copy; official publication status not verified) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [IEC 60601-2-27:2011 · iec60601](https://webstore.iec.ch/en/publication/2638) — Fundstelle: Scope / standard description; accuracy clause not inspected (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [U.S 1998 · fda_ec13_guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/cardiac-monitor-guidance-including-cardiotachometer-and-rate-alarm-guidance-industry) — Seite prüfen · **LINK DEFEKT**

<a id="a053"></a>
**A053 · LITERATUR- / HERSTELLERWERT**

R03 nennt für IEC 60601-2-27 ±10 % oder ±5/min sowie Bereiche 30–200/min (Erwachsene), 30–250/min (pädiatrisch/neonatal).

**Ursprung:** [preThesis/03-recherche/R03-bpm-referenz.md:89-93,113-143](../../preThesis/03-recherche/R03-bpm-referenz.md#L89)
**Belege:** [IEC 60601-2-27:2011 · iec60601](https://webstore.iec.ch/en/publication/2638) — Fundstelle: Scope / standard description; accuracy clause not inspected (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [ANSI/AAMI EC13:2002 · ec13](https://webstore.ansi.org/standards/aami/ansiaamiec132002) — Fundstelle: Clause 4.2.7 (accessible copy; official publication status not verified) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [U.S 1998 · fda_ec13_guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/cardiac-monitor-guidance-including-cardiotachometer-and-rate-alarm-guidance-industry) — Seite prüfen · **LINK DEFEKT**

<a id="u124"></a>
**U124 · EIGENER ZIELWERT / VORLÄUFIGER VORSCHLAG**

The evaluation protocol describes an eight-second rectified-envelope autocorrelation window with updates each second; host reports include MAE, RMSE, bias, maximum error and valid-window coverage after acquisition.

**Ursprung:** [Development/system/coding/bringup-zephyr/README.md:22-24](https://github.com/DemonicPsychoII/DigitalStethoscope/blob/23c1ea492270b897532896179e35f873eee823be/Development/system/coding/bringup-zephyr/README.md?plain=1#L22) (**Herkunft verschoben:** seit b2c3dde zu einem kurzen Einstiegs-README verdichtet; die Zeilenangaben gelten nur für die zitierte Fassung. Link zeigt diese historische Fassung. Aktuell: [Bring-up-README](../../Development/system/coding/bringup-zephyr/README.md))
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

### Folgerungen, Entwurfsentscheidungen und Grenzen

<a id="u018"></a>
**U018 · OFFENE FRAGE · OFFEN**

BPM-Referenz bleibt offen; Pulsoximeter oder Smartwatch gelten intern als realistisch, EKG als aufwendigere Referenz; interner Zielkorridor ±5 bpm / ±10 %.

> **Neuerer Stand (Stand integration, 2026-10-22):** Die BPM-Referenz für die Abnahme ist festgelegt. Aktuell: Pulsoximeter oder Smartwatch, gleichzeitig gemessen; bestanden innerhalb ±5 BPM oder ±10 % (14.10., REQ-06). – siehe [MVP-Entscheidungen 14.10. (Verhalten)](../../Development/system/planning/mvp-decisions-2026-10-14.md#behavior), [Systemanforderungen](../../Development/system/requirements/system-requirements.md#system-requirements-mvp).

**Ursprung:** [preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:39](../../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md#L39)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="c020"></a>
**C020 · OFFENE FRAGE · OFFEN**

Der Bericht findet keinen ESP32-S3-spezifischen belastbaren publizierten Benchmark für seine Hüllkurven-/Autokorrelations-BPM-Variante; deren Laufzeit ist daher auf dem Prototyp zu messen.

**Ursprung:** [preThesis/03-recherche/R10-esp32-plattform.md:258-281](../../preThesis/03-recherche/R10-esp32-plattform.md#L258)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="a054"></a>
**A054 · RISIKO / EINORDNUNG**

Die EKG-Monitor-Toleranz ist laut R03 kein Konformitätsnachweis für ein PCG-/Stethoskopgerät.

**Ursprung:** [preThesis/03-recherche/R03-bpm-referenz.md:22-29,145-150](../../preThesis/03-recherche/R03-bpm-referenz.md#L22)
**Belege:** [ANSI/AAMI EC13:2002 · ec13](https://webstore.ansi.org/standards/aami/ansiaamiec132002) — Fundstelle: Clause 4.2.7 (accessible copy; official publication status not verified) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [IEC 60601-2-27:2011 · iec60601](https://webstore.iec.ch/en/publication/2638) — Fundstelle: Scope / standard description; accuracy clause not inspected (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [U.S 1998 · fda_ec13_guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/cardiac-monitor-guidance-including-cardiotachometer-and-rate-alarm-guidance-industry) — Seite prüfen · **LINK DEFEKT**

<a id="a051"></a>
**A051 · METHODE / PRÜFVERFAHREN**

R03 nennt Bias, 95-%-Limits of Agreement, MAE, MAPE und Anteile innerhalb definierter Toleranzen als Ergebnisgrößen.

**Ursprung:** [preThesis/03-recherche/R03-bpm-referenz.md:76-85](../../preThesis/03-recherche/R03-bpm-referenz.md#L76)
**Belege:** [Bland, J 1986 · bland_altman](https://doi.org/10.1016/S0140-6736(86)90837-8) — Fundstelle: Abstract and bibliographic metadata; full text paywalled (aus Stage 1; am Original prüfen) · 🔒 Volltextzugang prüfen: Publisher full text may be paywalled.; [Giavarina, D 2015 · bland_review](https://pmc.ncbi.nlm.nih.gov/articles/PMC4470095/) — Seite prüfen (übernommene Angabe: Methods overview; section/page unverified); [ANSI/AAMI EC13:2002 · ec13](https://webstore.ansi.org/standards/aami/ansiaamiec132002) — Fundstelle: Clause 4.2.7 (accessible copy; official publication status not verified) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig

<a id="a057"></a>
**A057 · METHODENVORSCHLAG · ANNAHME**

R03 schlägt als ambitioniertes Ziel MAE ≤3 bpm, MAPE ≤5 % und mindestens 95 % innerhalb ±5 bpm bei ruhigen Probanden vor.

**Ursprung:** [preThesis/03-recherche/R03-bpm-referenz.md:139-143](../../preThesis/03-recherche/R03-bpm-referenz.md#L139)
**Belege:** [ANSI/AAMI EC13:2002 · ec13](https://webstore.ansi.org/standards/aami/ansiaamiec132002) — Fundstelle: Clause 4.2.7 (accessible copy; official publication status not verified) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [IEC 60601-2-27:2011 · iec60601](https://webstore.iec.ch/en/publication/2638) — Fundstelle: Scope / standard description; accuracy clause not inspected (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [U.S 1998 · fda_ec13_guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/cardiac-monitor-guidance-including-cardiotachometer-and-rate-alarm-guidance-industry) — Seite prüfen · **LINK DEFEKT**

<a id="a056"></a>
**A056 · METHODENVORSCHLAG · ANNAHME**

R03 schlägt MAE ≤5 bpm, MAPE ≤10 % und mindestens 90 % der Fenster innerhalb definierter Toleranz als Entwicklungsziel vor.

> **Überholt (Stand integration, 2026-10-22):** Das R03-Entwicklungsziel (MAE ≤5 bpm, MAPE ≤10 %, ≥90 % der Fenster) und der Sitzungs-MAE-Vorschlag vom 11.10. sind nicht der Projektweg. Aktuell: Vergleich mit gleichzeitig gemessenem Pulsoximeter oder Smartwatch, bestanden innerhalb ±5 BPM oder ±10 %; kein fester Signalqualitäts-Schwellwert (14.10.). REQ-06: 10 Sitzungen à 30 s, jedes Ergebnis innerhalb der Toleranz. Bereich 30–200 BPM ist Kandidat (P06). – siehe [MVP-Entscheidungen 14.10. (Verhalten)](../../Development/system/planning/mvp-decisions-2026-10-14.md#behavior), [Systemanforderungen](../../Development/system/requirements/system-requirements.md#system-requirements-mvp), [Designparameter P06](../../Development/system/design/parameters.md#design-parameters-internal).

**Ursprung:** [preThesis/03-recherche/R03-bpm-referenz.md:113-143](../../preThesis/03-recherche/R03-bpm-referenz.md#L113)
**Belege:** [ANSI/AAMI EC13:2002 · ec13](https://webstore.ansi.org/standards/aami/ansiaamiec132002) — Fundstelle: Clause 4.2.7 (accessible copy; official publication status not verified) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [IEC 60601-2-27:2011 · iec60601](https://webstore.iec.ch/en/publication/2638) — Fundstelle: Scope / standard description; accuracy clause not inspected (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [U.S 1998 · fda_ec13_guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/cardiac-monitor-guidance-including-cardiotachometer-and-rate-alarm-guidance-industry) — Seite prüfen · **LINK DEFEKT**

<a id="c022"></a>
**C022 · RISIKO / EINORDNUNG · ANNAHME**

R10 kennzeichnet Bewegungsartefakte, Doppelpeaks und variable Herztöne als Robustheitsprobleme für BPM-Schätzung, getrennt von CPU-Rechenkosten.

**Ursprung:** [preThesis/03-recherche/R10-esp32-plattform.md:271-281](../../preThesis/03-recherche/R10-esp32-plattform.md#L271)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="c021"></a>
**C021 · METHODENVORSCHLAG · ANNAHME**

R10 schlägt für BPM eine gefilterte Amplituden-/Energiehüllkurve, Tiefpass, Reduktion auf 100–250 Hz und Autokorrelation über ein 2–8-s-Fenster mit Peaksuche im physiologischen BPM-Bereich vor.

**Ursprung:** [preThesis/03-recherche/R10-esp32-plattform.md:258-281](../../preThesis/03-recherche/R10-esp32-plattform.md#L258)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.
