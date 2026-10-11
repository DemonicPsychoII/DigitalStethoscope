# Medizinische Grundlagen

[Zum Einstieg](README.md) · [Offene Punkte](offene-punkte.md)

Herzzyklus → Herztöne → Herzgeräusche → Auskultationsbandbreite.

**6 aktive Einheiten.** Schreibreihenfolge: Definition → Mechanismus → Werte → Folgerung. Die Aussagen sind Material, kein fertiger Fließtext.

**Schreibhinweis:** Literaturgrundlagen erklären das Verfahren. Zielwerte, Architekturentscheidungen und Berichtsempfehlungen als solche benennen und später in Anforderungen/Methodik begründen.

## Schreibbausteine

### Begriffe und Definitionen

<a id="u074"></a>
**U074 · LITERATURFAKT / REGEL**

Die Forschungsberichte beschreiben Herzgeräusche als Folge turbulenter Strömung und unterscheiden systolische bzw. diastolische Murmurs nach Auftreten im Zyklus.

**Ursprung:** [preThesis/03-recherche/R01-murmur-metrik.md:197-245](../preThesis/03-recherche/R01-murmur-metrik.md#L197)
**Belege:** [Delgado-Trejos, E., Quiceno-Manrique, A 2009 · digital_auscultation_murmur](https://link.springer.com/article/10.1007/s10439-008-9611-z) — Fundstelle: Introduction, heart cycle/murmur description (web text lines 71–73; 85). (aus Stage 1; am Original prüfen); [Li, S., Li, F., Tang, S., & Xiong, W 2020 · digital_auscultation_review](https://pubmed.ncbi.nlm.nih.gov/32420352/) — Seite prüfen (Hinweis: Relevant article section/table not verified in full text during this pass.); [Liu, C 2016 · open_heart_sound_database](https://pmc.ncbi.nlm.nih.gov/articles/PMC7199391/) — Seite prüfen (Hinweis: Relevant article section/table not verified in full text during this pass.)

<a id="u073"></a>
**U073 · LITERATURFAKT / REGEL**

S1 und S2 sind die zwei regelmäßig wiederkehrenden Herztöne pro Herzzyklus; der Abschnitt S1→S2 entspricht der Systole, S2→nächstes S1 der Diastole.

**Ursprung:** [preThesis/03-recherche/R01-murmur-metrik.md:148-153](../preThesis/03-recherche/R01-murmur-metrik.md#L148); [preThesis/02-entscheidungen/open-questions.md:24-25](../preThesis/02-entscheidungen/open-questions.md#L24)
**Belege:** [Delgado-Trejos, E., Quiceno-Manrique, A 2009 · digital_auscultation_murmur](https://link.springer.com/article/10.1007/s10439-008-9611-z) — Fundstelle: Introduction, heart cycle/murmur description (web text lines 71–73; 85). (aus Stage 1; am Original prüfen); [Li, S., Li, F., Tang, S., & Xiong, W 2020 · digital_auscultation_review](https://pubmed.ncbi.nlm.nih.gov/32420352/) — Seite prüfen (Hinweis: Relevant article section/table not verified in full text during this pass.); [Liu, C 2016 · open_heart_sound_database](https://pmc.ncbi.nlm.nih.gov/articles/PMC7199391/) — Seite prüfen (Hinweis: Relevant article section/table not verified in full text during this pass.)

### Mechanismen und Zusammenhänge

<a id="a060"></a>
**A060 · LITERATURFAKT / REGEL**

R04 beschreibt S1/S2 als kurze, nichtstationäre Ereignisse mit breitbandigen, zeitlich veränderlichen Anteilen.

**Ursprung:** [preThesis/03-recherche/R04-time-stretch.md:30-46](../preThesis/03-recherche/R04-time-stretch.md#L30)
**Belege:** [Noponen, A.-L., Lukkarinen, S., & Sepponen, R · murmur_text](https://accesscardiology.mhmedical.com/content.aspx?bookid=382&sectionid=40663653) — Fundstelle: Chapter 2, Clinical Auscultation and Conventional Phonocardiography (web lines 144–150) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [Luisada, A 1961 · highfreq_pcg](https://www.sciencedirect.com/science/article/pii/0002914961901783) — Fundstelle: Abstract (publisher page) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [Driedger, J., & Müller, M 2016 · tsm_review](https://www.mdpi.com/2076-3417/6/2/57) — Seite prüfen (übernommene Angabe: Abstract and review overview; article section/page unverified)

### Werte und dokumentierte Befunde

<a id="a014"></a>
**A014 · LITERATUR- / HERSTELLERWERT**

R01 nennt 10–140 Hz als S1-Schwerpunkt, 10–200 Hz für S2/tiefe Komponenten und 20–200 Hz für tieffrequente Herzschallanteile und tiefe Murmurs.

**Ursprung:** [preThesis/03-recherche/R01-murmur-metrik.md:197-215](../preThesis/03-recherche/R01-murmur-metrik.md#L197)
**Belege:** [Noponen, A.-L., Lukkarinen, S., & Sepponen, R · murmur_text](https://accesscardiology.mhmedical.com/content.aspx?bookid=382&sectionid=40663653) — Fundstelle: Chapter 2, Clinical Auscultation and Conventional Phonocardiography (web lines 144–150) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [Luisada, A 1961 · highfreq_pcg](https://www.sciencedirect.com/science/article/pii/0002914961901783) — Fundstelle: Abstract (publisher page) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [Delgado-Trejos, E., Quiceno-Manrique, A 2009 · digital_auscultation_murmur](https://link.springer.com/article/10.1007/s10439-008-9611-z) — Fundstelle: Introduction, murmur and heart cycle description (existing registry reports web lines 71–85) (aus Stage 1; am Original prüfen)

<a id="a015"></a>
**A015 · LITERATUR- / HERSTELLERWERT**

R01 nennt 20–500 Hz als breiten Herzschallbereich, 25–400 Hz als Vorverarbeitung einer PCG-Murmurklassifikation und 30–800/0–800 Hz für weitere Analysen.

**Ursprung:** [preThesis/03-recherche/R01-murmur-metrik.md:197-215](../preThesis/03-recherche/R01-murmur-metrik.md#L197)
**Belege:** [Wen, H 2023 · murmur_filter](https://arxiv.org/abs/2303.02988) — Fundstelle: Section 2.1, preprocessing pipeline (arXiv text lines 13–26) (aus Stage 1; am Original prüfen); [Luisada, A 1961 · highfreq_pcg](https://www.sciencedirect.com/science/article/pii/0002914961901783) — Fundstelle: Abstract (publisher page) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [Noponen, A.-L., Lukkarinen, S., & Sepponen, R · murmur_text](https://accesscardiology.mhmedical.com/content.aspx?bookid=382&sectionid=40663653) — Fundstelle: Chapter 2, Clinical Auscultation and Conventional Phonocardiography (web lines 144–150) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig

<a id="a016"></a>
**A016 · LITERATUR- / HERSTELLERWERT**

R01 nennt 50–1200 Hz als breiten Bereich der kardiopulmonalen Auskultation.

**Ursprung:** [preThesis/03-recherche/R01-murmur-metrik.md:197-215](../preThesis/03-recherche/R01-murmur-metrik.md#L197)
**Belege:** [Noponen, A.-L., Lukkarinen, S., & Sepponen, R · murmur_text](https://accesscardiology.mhmedical.com/content.aspx?bookid=382&sectionid=40663653) — Fundstelle: Chapter 2, Clinical Auscultation and Conventional Phonocardiography (web lines 144–150) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [Luisada, A 1961 · highfreq_pcg](https://www.sciencedirect.com/science/article/pii/0002914961901783) — Fundstelle: Abstract (publisher page) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [Delgado-Trejos, E., Quiceno-Manrique, A 2009 · digital_auscultation_murmur](https://link.springer.com/article/10.1007/s10439-008-9611-z) — Fundstelle: Introduction, murmur and heart cycle description (existing registry reports web lines 71–85) (aus Stage 1; am Original prüfen)

