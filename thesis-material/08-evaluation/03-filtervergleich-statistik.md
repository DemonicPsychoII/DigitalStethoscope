# Evaluation: Filtervergleich und Statistik

[Zum Einstieg](../README.md) · [Offene Punkte](../offene-punkte.md)

Vergleichsgrößen definieren → fairer Versuchsaufbau → gepaarte Auswertung.

**16 aktive Einheiten.** Schreibreihenfolge: Definition → Mechanismus → Werte → Folgerung. Die Aussagen sind Material, kein fertiger Fließtext.

## Schreibbausteine

### Begriffe und Definitionen

<a id="a002"></a>
**A002 · LITERATURFAKT / REGEL**

Bandbegrenzte Murmur-SNR kann als 10·log10(P_Murmur/P_Noise) oder 20·log10(A_Signal/A_Noise) berechnet werden.

**Ursprung:** [preThesis/03-recherche/R01-murmur-metrik.md:45-48](../../preThesis/03-recherche/R01-murmur-metrik.md#L45)
**Belege:** [Noponen, A.-L., Lukkarinen, S., & Sepponen, R · murmur_text](https://accesscardiology.mhmedical.com/content.aspx?bookid=382&sectionid=40663653) — Fundstelle: Chapter 2, Clinical Auscultation and Conventional Phonocardiography (web lines 144–150) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [Delgado-Trejos, E., Quiceno-Manrique, A 2009 · digital_auscultation_murmur](https://link.springer.com/article/10.1007/s10439-008-9611-z) — Fundstelle: Introduction, murmur and heart cycle description (existing registry reports web lines 71–85) (aus Stage 1; am Original prüfen); [Wen, H 2023 · murmur_filter](https://arxiv.org/abs/2303.02988) — Fundstelle: Section 2.1, preprocessing pipeline (arXiv text lines 13–26) (aus Stage 1; am Original prüfen)

<a id="a011"></a>
**A011 · LITERATURFAKT / REGEL**

Bei synthetisch verrauschter PCG mit clean signal x und Rauschen n gilt x_in=x+n; SNR_out−SNR_in ist eine mögliche SNR-Änderung.

**Ursprung:** [preThesis/03-recherche/R01-murmur-metrik.md:64-106](../../preThesis/03-recherche/R01-murmur-metrik.md#L64)
**Belege:** [Noponen, A.-L., Lukkarinen, S., & Sepponen, R · murmur_text](https://accesscardiology.mhmedical.com/content.aspx?bookid=382&sectionid=40663653) — Fundstelle: Chapter 2, Clinical Auscultation and Conventional Phonocardiography (web lines 144–150) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [Delgado-Trejos, E., Quiceno-Manrique, A 2009 · digital_auscultation_murmur](https://link.springer.com/article/10.1007/s10439-008-9611-z) — Fundstelle: Introduction, murmur and heart cycle description (existing registry reports web lines 71–85) (aus Stage 1; am Original prüfen); [Wen, H 2023 · murmur_filter](https://arxiv.org/abs/2303.02988) — Fundstelle: Section 2.1, preprocessing pipeline (arXiv text lines 13–26) (aus Stage 1; am Original prüfen)

<a id="a003"></a>
**A003 · LITERATURFAKT / REGEL**

Murmur-to-S1/S2-Ratio kann als E_M/(E_S1+E_S2) angegeben werden und ist nicht gleich SNR.

**Ursprung:** [preThesis/03-recherche/R01-murmur-metrik.md:47-49](../../preThesis/03-recherche/R01-murmur-metrik.md#L47)
**Belege:** [Noponen, A.-L., Lukkarinen, S., & Sepponen, R · murmur_text](https://accesscardiology.mhmedical.com/content.aspx?bookid=382&sectionid=40663653) — Fundstelle: Chapter 2, Clinical Auscultation and Conventional Phonocardiography (web lines 144–150) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [Delgado-Trejos, E., Quiceno-Manrique, A 2009 · digital_auscultation_murmur](https://link.springer.com/article/10.1007/s10439-008-9611-z) — Fundstelle: Introduction, murmur and heart cycle description (existing registry reports web lines 71–85) (aus Stage 1; am Original prüfen); [Wen, H 2023 · murmur_filter](https://arxiv.org/abs/2303.02988) — Fundstelle: Section 2.1, preprocessing pipeline (arXiv text lines 13–26) (aus Stage 1; am Original prüfen)

<a id="a013"></a>
**A013 · LITERATURFAKT / REGEL**

R01 nennt 20·log10(A_S/(4σ_N)) als reale PCG-SNR-Definition; 4σ_N wird als angenommene 95-%-Rauschamplitude bei Normalverteilung interpretiert.

**Ursprung:** [preThesis/03-recherche/R01-murmur-metrik.md:107-126](../../preThesis/03-recherche/R01-murmur-metrik.md#L107)
**Belege:** [Noponen, A.-L., Lukkarinen, S., & Sepponen, R · murmur_text](https://accesscardiology.mhmedical.com/content.aspx?bookid=382&sectionid=40663653) — Fundstelle: Chapter 2, Clinical Auscultation and Conventional Phonocardiography (web lines 144–150) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [Delgado-Trejos, E., Quiceno-Manrique, A 2009 · digital_auscultation_murmur](https://link.springer.com/article/10.1007/s10439-008-9611-z) — Fundstelle: Introduction, murmur and heart cycle description (existing registry reports web lines 71–85) (aus Stage 1; am Original prüfen); [Wen, H 2023 · murmur_filter](https://arxiv.org/abs/2303.02988) — Fundstelle: Section 2.1, preprocessing pipeline (arXiv text lines 13–26) (aus Stage 1; am Original prüfen)

### Mechanismen und Zusammenhänge

<a id="a010"></a>
**A010 · LITERATURFAKT / REGEL · ersetzt U043**

Eine Verbesserung von breitbandigem SNR oder RMS allein belegt keine bessere Murmur-Detektierbarkeit.

**Ursprung:** [preThesis/03-recherche/R01-murmur-metrik.md:22-41](../../preThesis/03-recherche/R01-murmur-metrik.md#L22)
**Belege:** [Noponen, A.-L., Lukkarinen, S., & Sepponen, R · murmur_text](https://accesscardiology.mhmedical.com/content.aspx?bookid=382&sectionid=40663653) — Fundstelle: Chapter 2, Clinical Auscultation and Conventional Phonocardiography (web lines 144–150) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [Delgado-Trejos, E., Quiceno-Manrique, A 2009 · digital_auscultation_murmur](https://link.springer.com/article/10.1007/s10439-008-9611-z) — Fundstelle: Introduction, murmur and heart cycle description (existing registry reports web lines 71–85) (aus Stage 1; am Original prüfen); [Wen, H 2023 · murmur_filter](https://arxiv.org/abs/2303.02988) — Fundstelle: Section 2.1, preprocessing pipeline (arXiv text lines 13–26) (aus Stage 1; am Original prüfen)

<a id="a001"></a>
**A001 · LITERATURFAKT / REGEL · ersetzt U041**

Für Murmur-Detektierbarkeit existiert in den recherchierten Quellen keine einzelne allgemein normierte Kennzahl; verwendet werden Energie-, Spektral-, Hüllkurven- oder Detektor-Leistungsmerkmale.

**Ursprung:** [preThesis/03-recherche/R01-murmur-metrik.md:22-41](../../preThesis/03-recherche/R01-murmur-metrik.md#L22)
**Belege:** [Noponen, A.-L., Lukkarinen, S., & Sepponen, R · murmur_text](https://accesscardiology.mhmedical.com/content.aspx?bookid=382&sectionid=40663653) — Fundstelle: Chapter 2, Clinical Auscultation and Conventional Phonocardiography (web lines 144–150) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [Delgado-Trejos, E., Quiceno-Manrique, A 2009 · digital_auscultation_murmur](https://link.springer.com/article/10.1007/s10439-008-9611-z) — Fundstelle: Introduction, murmur and heart cycle description (existing registry reports web lines 71–85) (aus Stage 1; am Original prüfen); [Wen, H 2023 · murmur_filter](https://arxiv.org/abs/2303.02988) — Fundstelle: Section 2.1, preprocessing pipeline (arXiv text lines 13–26) (aus Stage 1; am Original prüfen)

<a id="u049"></a>
**U049 · LITERATURFAKT / REGEL · QUELLENSET UNVOLLSTÄNDIG**

In R01 ist keine belegte dB-Schwelle für „besserer“ Filter dokumentiert; 14 dB betrifft eine Zeitbestimmungsaufgabe und ist keine Murmur-Detektierbarkeitsschwelle.

**Ursprung:** [preThesis/02-entscheidungen/open-questions.md:74-77](../../preThesis/02-entscheidungen/open-questions.md#L74)
**Belege:** [Li, S., Li, F., Tang, S., & Xiong, W 2020 · digital_auscultation_review](https://pubmed.ncbi.nlm.nih.gov/32420352/) — Seite prüfen (Hinweis: Relevant article section/table not verified in full text during this pass.); [Maharjan, S 2023 · digital_stethoscope_characterization](https://pmc.ncbi.nlm.nih.gov/articles/PMC10753976/) — Seite prüfen (Hinweis: Relevant article section/table not verified in full text during this pass.); [Alanazi, A., Atcherson, S., Franklin, C., & Bryan, M 2020 · frequency_response_stethoscopes](https://doi.org/10.4103/sjmms.sjmms_118_19) — Seite prüfen (Hinweis: Relevant article section/table not verified in full text during this pass.)

### Werte und dokumentierte Befunde

<a id="a020"></a>
**A020 · LITERATUR- / HERSTELLERWERT**

R01 führt Cohen-d-Richtwerte 0,2/0,5/0,8 als klein/mittel/groß auf; dies sind keine klinischen Murmur-Schwellen.

**Ursprung:** [preThesis/03-recherche/R01-murmur-metrik.md:501-531](../../preThesis/03-recherche/R01-murmur-metrik.md#L501)
**Belege:** [Giavarina, D 2015 · bland_review](https://pmc.ncbi.nlm.nih.gov/articles/PMC4470095/) — Seite prüfen (übernommene Angabe: Methods overview; section/page unverified); [Delgado-Trejos, E., Quiceno-Manrique, A 2009 · digital_auscultation_murmur](https://link.springer.com/article/10.1007/s10439-008-9611-z) — Fundstelle: Introduction, murmur and heart cycle description (existing registry reports web lines 71–85) (aus Stage 1; am Original prüfen); [Noponen, A.-L., Lukkarinen, S., & Sepponen, R · murmur_text](https://accesscardiology.mhmedical.com/content.aspx?bookid=382&sectionid=40663653) — Fundstelle: Chapter 2, Clinical Auscultation and Conventional Phonocardiography (web lines 144–150) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig

### Folgerungen, Entwurfsentscheidungen und Grenzen

<a id="a009"></a>
**A009 · METHODE / PRÜFVERFAHREN**

AUC, Sensitivität, Spezifität, F1 und Balanced Accuracy benötigen Labels oder einen festgelegten Referenzdetektor.

**Ursprung:** [preThesis/03-recherche/R01-murmur-metrik.md:56](../../preThesis/03-recherche/R01-murmur-metrik.md#L56)
**Belege:** [Wen, H 2023 · murmur_filter](https://arxiv.org/abs/2303.02988) — Fundstelle: Section 2.1, preprocessing pipeline (arXiv text lines 13–26) (aus Stage 1; am Original prüfen); [Oliveira, J 2022 · circor_paper](https://arxiv.org/abs/2108.00813) — Seite prüfen (übernommene Angabe: Abstract, arXiv text lines 3–6; journal pages unverified) · 🔒 Volltextzugang prüfen: IEEE version may be paywalled; arXiv preprint is open.; [Reyna, M 2022 · physionet_challenge_2022](https://physionet.org/content/challenge-2022/1.0.0/papers/) — Fundstelle: Data Variables, lines 92–97 (aus Stage 1; am Original prüfen)

<a id="a004"></a>
**A004 · METHODE / PRÜFVERFAHREN · ANNAHME**

Bandenergieverhältnis, spektraler Kontrast und Envelope-Kontrast sind mögliche Vergleichsgrößen; Bandgrenzen und Referenzfenster sind vorab festzulegen.

**Ursprung:** [preThesis/03-recherche/R01-murmur-metrik.md:49-55](../../preThesis/03-recherche/R01-murmur-metrik.md#L49)
**Belege:** [Noponen, A.-L., Lukkarinen, S., & Sepponen, R · murmur_text](https://accesscardiology.mhmedical.com/content.aspx?bookid=382&sectionid=40663653) — Fundstelle: Chapter 2, Clinical Auscultation and Conventional Phonocardiography (web lines 144–150) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [Delgado-Trejos, E., Quiceno-Manrique, A 2009 · digital_auscultation_murmur](https://link.springer.com/article/10.1007/s10439-008-9611-z) — Fundstelle: Introduction, murmur and heart cycle description (existing registry reports web lines 71–85) (aus Stage 1; am Original prüfen); [Wen, H 2023 · murmur_filter](https://arxiv.org/abs/2303.02988) — Fundstelle: Section 2.1, preprocessing pipeline (arXiv text lines 13–26) (aus Stage 1; am Original prüfen)

<a id="a019"></a>
**A019 · METHODE / PRÜFVERFAHREN · ANNAHME**

Bei nicht normalverteilten gepaarten Differenzen nennt R01 Wilcoxon-Vorzeichen-Rang-Test, Median, Hodges–Lehmann-Schätzer und Bootstrap-Konfidenzintervall.

**Ursprung:** [preThesis/03-recherche/R01-murmur-metrik.md:544-548](../../preThesis/03-recherche/R01-murmur-metrik.md#L544)
**Belege:** [Bland, J 1986 · bland_altman](https://doi.org/10.1016/S0140-6736(86)90837-8) — Fundstelle: Abstract and bibliographic metadata; full text paywalled (aus Stage 1; am Original prüfen) · 🔒 Volltextzugang prüfen: Publisher full text may be paywalled.; [Giavarina, D 2015 · bland_review](https://pmc.ncbi.nlm.nih.gov/articles/PMC4470095/) — Seite prüfen (übernommene Angabe: Methods overview; section/page unverified); [ANSI/AAMI EC13:2002 · ec13](https://webstore.ansi.org/standards/aami/ansiaamiec132002) — Fundstelle: Clause 4.2.7 (accessible copy; official publication status not verified) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig

<a id="a012"></a>
**A012 · RISIKO / EINORDNUNG**

Eine SNR-Berechnung mit bekanntem Nutzsignal ist bei klinischen Aufnahmen nur mit Referenzsignal, paralleler Messung oder experimentell erzeugtem Rauschen möglich.

**Ursprung:** [preThesis/03-recherche/R01-murmur-metrik.md:99-106](../../preThesis/03-recherche/R01-murmur-metrik.md#L99)
**Belege:** [Noponen, A.-L., Lukkarinen, S., & Sepponen, R · murmur_text](https://accesscardiology.mhmedical.com/content.aspx?bookid=382&sectionid=40663653) — Fundstelle: Chapter 2, Clinical Auscultation and Conventional Phonocardiography (web lines 144–150) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [Delgado-Trejos, E., Quiceno-Manrique, A 2009 · digital_auscultation_murmur](https://link.springer.com/article/10.1007/s10439-008-9611-z) — Fundstelle: Introduction, murmur and heart cycle description (existing registry reports web lines 71–85) (aus Stage 1; am Original prüfen); [Wen, H 2023 · murmur_filter](https://arxiv.org/abs/2303.02988) — Fundstelle: Section 2.1, preprocessing pipeline (arXiv text lines 13–26) (aus Stage 1; am Original prüfen)

<a id="u121"></a>
**U121 · METHODE / PRÜFVERFAHREN**

EVAL-GUIDE host comparison can hold analysis filter fixed while changing listening filter, or use matched analysis/listening variants; matched mode changes two variables and must be interpreted accordingly.

**Ursprung:** [Development/system/coding/bringup-zephyr/EVAL-GUIDE.md:31-35](../../Development/system/coding/bringup-zephyr/EVAL-GUIDE.md#L31)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="a017"></a>
**A017 · METHODENVORSCHLAG · ANNAHME**

R01 empfiehlt für Filtervergleiche gleiche absolute ADC-Skalierung, Eingangsamplitude und Messkette oder eine gemeinsame Normierung am ungefilterten Signal.

**Ursprung:** [preThesis/03-recherche/R01-murmur-metrik.md:262-282](../../preThesis/03-recherche/R01-murmur-metrik.md#L262)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="a018"></a>
**A018 · METHODENVORSCHLAG · ANNAHME · ersetzt U042**

R01 empfiehlt identische Zeitfenster aus gemeinsamer Referenzsegmentierung, damit Filterwirkung nicht zugleich die Segmentierung verändert.

**Ursprung:** [preThesis/03-recherche/R01-murmur-metrik.md:128-157](../../preThesis/03-recherche/R01-murmur-metrik.md#L128)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u050"></a>
**U050 · METHODENVORSCHLAG · QUELLENSET UNVOLLSTÄNDIG**

R01 schlägt vor, eine primäre Metrik vorab festzulegen, gepaarte Wilcoxon-Tests, Effektgröße samt Konfidenzintervall und bei Mehrfachtests Holm-Bonferroni zu nutzen.

**Ursprung:** [preThesis/02-entscheidungen/open-questions.md:79-86](../../preThesis/02-entscheidungen/open-questions.md#L79)
**Belege:** [Teresi, J 2022 · pilot_guidelines](https://pmc.ncbi.nlm.nih.gov/articles/PMC8849521/) — Fundstelle: Sections 1–2 (aus Stage 1; am Original prüfen); [Bland, J 1986 · bland_altman](https://doi.org/10.1016/S0140-6736(86)90837-8) — Seite prüfen (Hinweis: Relevant article section/table not verified in full text during this pass.) · 🔒 Volltextzugang prüfen: Publisher full text may be paywalled.; [Liu, C 2016 · open_heart_sound_database](https://pmc.ncbi.nlm.nih.gov/articles/PMC7199391/) — Seite prüfen (Hinweis: Relevant article section/table not verified in full text during this pass.)
