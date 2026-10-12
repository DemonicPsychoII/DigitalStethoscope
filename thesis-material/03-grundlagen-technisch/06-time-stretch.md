# Time-Stretch und verlangsamte Wiedergabe

[Zum Einstieg](../README.md) · [Offene Punkte](../offene-punkte.md)

Resampling/TSM → SOLA/WSOLA → Phase-Vocoder → Artefakte und Startparameter.

**14 aktive Einheiten.** Schreibreihenfolge: Definition → Mechanismus → Werte → Folgerung. Die Aussagen sind Material, kein fertiger Fließtext.

**Schreibhinweis:** Literaturgrundlagen erklären das Verfahren. Zielwerte, Architekturentscheidungen und Berichtsempfehlungen als solche benennen und später in Anforderungen/Methodik begründen.

## Schreibbausteine

### Begriffe und Definitionen

<a id="a068"></a>
**A068 · LITERATURFAKT / REGEL**

Ein Phase-Vocoder verändert zeitliche Positionen von STFT-Rahmen, rekonstruiert Phasen und führt inverse STFT aus.

**Ursprung:** [preThesis/03-recherche/R04-time-stretch.md:63-68,95-113](../../preThesis/03-recherche/R04-time-stretch.md#L63)
**Belege:** [Driedger, J., & Müller, M 2016 · tsm_review](https://www.mdpi.com/2076-3417/6/2/57) — Seite prüfen (übernommene Angabe: Abstract and review overview; article section/page unverified); [Prusa, Z 2022 · phase_vocoder](https://ltfat.org/notes/ltfatnote050.pdf) — Seite prüfen (übernommene Angabe: Abstract and Introduction (PDF; document pages unverified)); [Roelands, M., & Verhelst, W 1993 · wsola_roelands](https://www.isca-archive.org/eurospeech_1993/roelands93_eurospeech.html) — Fundstelle: Abstract and bibliographic record (aus Stage 1; am Original prüfen)

<a id="a063"></a>
**A063 · LITERATURFAKT / REGEL**

SOLA verbindet überlappende Abschnitte mit möglichst gutem Wellenformanschluss; R04 nennt Phasensprünge, Knacken und Transientenartefakte.

**Ursprung:** [preThesis/03-recherche/R04-time-stretch.md:63-68](../../preThesis/03-recherche/R04-time-stretch.md#L63)
**Belege:** [Driedger, J., & Müller, M 2016 · tsm_review](https://www.mdpi.com/2076-3417/6/2/57) — Seite prüfen (übernommene Angabe: Abstract and review overview; article section/page unverified); [Roelands, M., & Verhelst, W 1993 · wsola_roelands](https://www.isca-archive.org/eurospeech_1993/roelands93_eurospeech.html) — Fundstelle: Abstract and bibliographic record (aus Stage 1; am Original prüfen); [Prusa, Z 2022 · phase_vocoder](https://ltfat.org/notes/ltfatnote050.pdf) — Seite prüfen (übernommene Angabe: Abstract and Introduction (PDF; document pages unverified))

<a id="a058"></a>
**A058 · LITERATURFAKT / REGEL**

Time-Scale Modification verändert die Signaldauer ohne Tonhöhenänderung; Resampling mit Faktor r verschiebt Frequenzen näherungsweise auf f_neu=r·f_alt.

**Ursprung:** [preThesis/03-recherche/R04-time-stretch.md:22-60](../../preThesis/03-recherche/R04-time-stretch.md#L22)
**Belege:** [Driedger, J., & Müller, M 2016 · tsm_review](https://www.mdpi.com/2076-3417/6/2/57) — Seite prüfen (übernommene Angabe: Abstract and review overview; article section/page unverified); [Roelands, M., & Verhelst, W 1993 · wsola_roelands](https://www.isca-archive.org/eurospeech_1993/roelands93_eurospeech.html) — Fundstelle: Abstract and bibliographic record (aus Stage 1; am Original prüfen); [Prusa, Z 2022 · phase_vocoder](https://ltfat.org/notes/ltfatnote050.pdf) — Seite prüfen (übernommene Angabe: Abstract and Introduction (PDF; document pages unverified))

<a id="a064"></a>
**A064 · LITERATURFAKT / REGEL**

WSOLA ergänzt SOLA durch Suche nach einer Analyseposition mit maximaler Wellenformähnlichkeit.

**Ursprung:** [preThesis/03-recherche/R04-time-stretch.md:63-68](../../preThesis/03-recherche/R04-time-stretch.md#L63)
**Belege:** [Roelands, M., & Verhelst, W 1993 · wsola_roelands](https://www.isca-archive.org/eurospeech_1993/roelands93_eurospeech.html) — Fundstelle: Abstract and bibliographic record (aus Stage 1; am Original prüfen); [Driedger, J., & Müller, M 2016 · tsm_review](https://www.mdpi.com/2076-3417/6/2/57) — Seite prüfen (übernommene Angabe: Abstract and review overview; article section/page unverified); [Prusa, Z 2022 · phase_vocoder](https://ltfat.org/notes/ltfatnote050.pdf) — Seite prüfen (übernommene Angabe: Abstract and Introduction (PDF; document pages unverified))

### Mechanismen und Zusammenhänge

<a id="a061"></a>
**A061 · LITERATURFAKT / REGEL**

Pitch-erhaltendes Time-Stretching erhält Frequenzlage näherungsweise, verändert aber zeitliche Verhältnisse und kann Artefakte hinzufügen.

**Ursprung:** [preThesis/03-recherche/R04-time-stretch.md:22-60](../../preThesis/03-recherche/R04-time-stretch.md#L22)
**Belege:** [Driedger, J., & Müller, M 2016 · tsm_review](https://www.mdpi.com/2076-3417/6/2/57) — Seite prüfen (übernommene Angabe: Abstract and review overview; article section/page unverified); [Roelands, M., & Verhelst, W 1993 · wsola_roelands](https://www.isca-archive.org/eurospeech_1993/roelands93_eurospeech.html) — Fundstelle: Abstract and bibliographic record (aus Stage 1; am Original prüfen); [Prusa, Z 2022 · phase_vocoder](https://ltfat.org/notes/ltfatnote050.pdf) — Seite prüfen (übernommene Angabe: Abstract and Introduction (PDF; document pages unverified))

<a id="a067"></a>
**A067 · LITERATURFAKT / REGEL · ANNAHME**

R04 beschreibt PSOLA als perioden-/grundtonsynchrone Segmentierung und bewertet sie für vollständige PCG wegen fehlender stabiler Periodizität als ungeeignet.

**Ursprung:** [preThesis/03-recherche/R04-time-stretch.md:63-68,116-127](../../preThesis/03-recherche/R04-time-stretch.md#L63)
**Belege:** [Driedger, J., & Müller, M 2016 · tsm_review](https://www.mdpi.com/2076-3417/6/2/57) — Seite prüfen (übernommene Angabe: Abstract and review overview; article section/page unverified); [Roelands, M., & Verhelst, W 1993 · wsola_roelands](https://www.isca-archive.org/eurospeech_1993/roelands93_eurospeech.html) — Fundstelle: Abstract and bibliographic record (aus Stage 1; am Original prüfen); [Prusa, Z 2022 · phase_vocoder](https://ltfat.org/notes/ltfatnote050.pdf) — Seite prüfen (übernommene Angabe: Abstract and Introduction (PDF; document pages unverified))

### Werte und dokumentierte Befunde

<a id="a059"></a>
**A059 · LITERATUR- / HERSTELLERWERT**

Bei 0,5× verdoppelt sich Dauer und Frequenzlage sinkt auf 50 %; bei 0,75× wird Dauer 1,333-fach und Frequenzlage sinkt auf 75 %.

**Ursprung:** [preThesis/03-recherche/R04-time-stretch.md:48-60](../../preThesis/03-recherche/R04-time-stretch.md#L48)
**Belege:** [Driedger, J., & Müller, M 2016 · tsm_review](https://www.mdpi.com/2076-3417/6/2/57) — Seite prüfen (übernommene Angabe: Abstract and review overview; article section/page unverified); [Roelands, M., & Verhelst, W 1993 · wsola_roelands](https://www.isca-archive.org/eurospeech_1993/roelands93_eurospeech.html) — Fundstelle: Abstract and bibliographic record (aus Stage 1; am Original prüfen); [Prusa, Z 2022 · phase_vocoder](https://ltfat.org/notes/ltfatnote050.pdf) — Seite prüfen (übernommene Angabe: Abstract and Introduction (PDF; document pages unverified))

<a id="a073"></a>
**A073 · LITERATUR- / HERSTELLERWERT**

Bei 8 kHz und 512-Punkt-FFT beträgt die Frequenzbinbreite rund 15,6 Hz; bei 256 Punkten rund 31,25 Hz.

**Ursprung:** [preThesis/03-recherche/R04-time-stretch.md:154-163](../../preThesis/03-recherche/R04-time-stretch.md#L154)
**Belege:** [Driedger, J., & Müller, M 2016 · tsm_review](https://www.mdpi.com/2076-3417/6/2/57) — Seite prüfen (übernommene Angabe: Abstract and review overview; article section/page unverified); [Roelands, M., & Verhelst, W 1993 · wsola_roelands](https://www.isca-archive.org/eurospeech_1993/roelands93_eurospeech.html) — Fundstelle: Abstract and bibliographic record (aus Stage 1; am Original prüfen); [Prusa, Z 2022 · phase_vocoder](https://ltfat.org/notes/ltfatnote050.pdf) — Seite prüfen (übernommene Angabe: Abstract and Introduction (PDF; document pages unverified))

<a id="a072"></a>
**A072 · EIGENER ZIELWERT / VORLÄUFIGER VORSCHLAG · ANNAHME**

R04 listet Phase-Vocoder-Beispielparameter FFT 256/512, Fenster 32–64 ms, Hop 25–50 %, Hann-Fenster und Overlap-Add.

**Ursprung:** [preThesis/03-recherche/R04-time-stretch.md:144-153](../../preThesis/03-recherche/R04-time-stretch.md#L144)
**Belege:** [Driedger, J., & Müller, M 2016 · tsm_review](https://www.mdpi.com/2076-3417/6/2/57) — Seite prüfen (übernommene Angabe: Abstract and review overview; article section/page unverified); [Roelands, M., & Verhelst, W 1993 · wsola_roelands](https://www.isca-archive.org/eurospeech_1993/roelands93_eurospeech.html) — Fundstelle: Abstract and bibliographic record (aus Stage 1; am Original prüfen); [Prusa, Z 2022 · phase_vocoder](https://ltfat.org/notes/ltfatnote050.pdf) — Seite prüfen (übernommene Angabe: Abstract and Introduction (PDF; document pages unverified))

<a id="a071"></a>
**A071 · EIGENER ZIELWERT / VORLÄUFIGER VORSCHLAG · ANNAHME**

R04 listet WSOLA-Startparameter bei 8 kHz: Frames 20–40 ms, Überlappung 50–75 %, Synthese-Hop 5–15 ms, Suchbereich ±5–10 ms.

**Ursprung:** [preThesis/03-recherche/R04-time-stretch.md:129-141](../../preThesis/03-recherche/R04-time-stretch.md#L129)
**Belege:** [Driedger, J., & Müller, M 2016 · tsm_review](https://www.mdpi.com/2076-3417/6/2/57) — Seite prüfen (übernommene Angabe: Abstract and review overview; article section/page unverified); [Roelands, M., & Verhelst, W 1993 · wsola_roelands](https://www.isca-archive.org/eurospeech_1993/roelands93_eurospeech.html) — Fundstelle: Abstract and bibliographic record (aus Stage 1; am Original prüfen); [Prusa, Z 2022 · phase_vocoder](https://ltfat.org/notes/ltfatnote050.pdf) — Seite prüfen (übernommene Angabe: Abstract and Introduction (PDF; document pages unverified))

### Folgerungen, Entwurfsentscheidungen und Grenzen

<a id="a069"></a>
**A069 · RISIKO / EINORDNUNG · QUELLENSET UNVOLLSTÄNDIG**

R04 nennt beim Phase-Vocoder Transientenschmierung, phasigen/hallähnlichen Eindruck und Phasenkohärenzverlust als mögliche Artefakte.

**Ursprung:** [preThesis/03-recherche/R04-time-stretch.md:95-113](../../preThesis/03-recherche/R04-time-stretch.md#L95)
**Belege:** [Driedger, J., & Müller, M 2016 · tsm_review](https://www.mdpi.com/2076-3417/6/2/57) — Seite prüfen (übernommene Angabe: Abstract and review overview; article section/page unverified); [Prusa, Z 2022 · phase_vocoder](https://ltfat.org/notes/ltfatnote050.pdf) — Seite prüfen (übernommene Angabe: Abstract and Introduction (PDF; document pages unverified))

<a id="a070"></a>
**A070 · METHODE / PRÜFVERFAHREN · QUELLENSET UNVOLLSTÄNDIG**

R04 nennt Identity Phase Locking, Onset-/Transientenerkennung und Hybrid WSOLA/Phase-Vocoder als mögliche Gegenmaßnahmen.

**Ursprung:** [preThesis/03-recherche/R04-time-stretch.md:104-113](../../preThesis/03-recherche/R04-time-stretch.md#L104)
**Belege:** [Driedger, J., & Müller, M 2016 · tsm_review](https://www.mdpi.com/2076-3417/6/2/57) — Seite prüfen (übernommene Angabe: Abstract and review overview; article section/page unverified); [Prusa, Z 2022 · phase_vocoder](https://ltfat.org/notes/ltfatnote050.pdf) — Seite prüfen (übernommene Angabe: Abstract and Introduction (PDF; document pages unverified))

<a id="a066"></a>
**A066 · RISIKO / EINORDNUNG**

R04 nennt Transientenverdopplung, Transientenauslassen, Stottern und Amplitudenmodulation als mögliche WSOLA-Artefakte.

**Ursprung:** [preThesis/03-recherche/R04-time-stretch.md:71-90](../../preThesis/03-recherche/R04-time-stretch.md#L71)
**Belege:** [Driedger, J., & Müller, M 2016 · tsm_review](https://www.mdpi.com/2076-3417/6/2/57) — Seite prüfen (übernommene Angabe: Abstract and review overview; article section/page unverified); [Roelands, M., & Verhelst, W 1993 · wsola_roelands](https://www.isca-archive.org/eurospeech_1993/roelands93_eurospeech.html) — Fundstelle: Abstract and bibliographic record (aus Stage 1; am Original prüfen); [Prusa, Z 2022 · phase_vocoder](https://ltfat.org/notes/ltfatnote050.pdf) — Seite prüfen (übernommene Angabe: Abstract and Introduction (PDF; document pages unverified))

<a id="a062"></a>
**A062 · EIGENE ENTSCHEIDUNG / ENTWURFSEMPFEHLUNG · ANNAHME · ersetzt U051**

R04 ordnet verlangsamte Wiedergabe als zusätzliche Hörhilfe, nicht als diagnostisch validiertes Verfahren ein; Originalgeschwindigkeit soll verfügbar bleiben.

**Ursprung:** [preThesis/03-recherche/R04-time-stretch.md:22-60](../../preThesis/03-recherche/R04-time-stretch.md#L22)
**Belege:** [Driedger, J., & Müller, M 2016 · tsm_review](https://www.mdpi.com/2076-3417/6/2/57) — Seite prüfen (übernommene Angabe: Abstract and review overview; article section/page unverified); [Roelands, M., & Verhelst, W 1993 · wsola_roelands](https://www.isca-archive.org/eurospeech_1993/roelands93_eurospeech.html) — Fundstelle: Abstract and bibliographic record (aus Stage 1; am Original prüfen); [Prusa, Z 2022 · phase_vocoder](https://ltfat.org/notes/ltfatnote050.pdf) — Seite prüfen (übernommene Angabe: Abstract and Introduction (PDF; document pages unverified))
