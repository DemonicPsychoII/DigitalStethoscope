# DSP und Filter

[Zum Einstieg](../README.md) · [Offene Punkte](../offene-punkte.md)

Filterwirkung → Hüllkurven und Spektralmerkmale → Rechenaufwand.

**7 aktive Einheiten.** Schreibreihenfolge: Definition → Mechanismus → Werte → Folgerung. Die Aussagen sind Material, kein fertiger Fließtext.

**Schreibhinweis:** Literaturgrundlagen erklären das Verfahren. Zielwerte, Architekturentscheidungen und Berichtsempfehlungen als solche benennen und später in Anforderungen/Methodik begründen.

## Schreibbausteine

### Werte und dokumentierte Befunde

<a id="c016"></a>
**C016 · LITERATURMESSUNG / BENCHMARK · QUELLENSET UNVOLLSTÄNDIG**

Der ESP-DSP-Benchmark weist für `dsps_biquad_f32` auf ESP32-S3 17 552 Zyklen pro 1 024 Eingangssamples aus (O2-optimierte Assembly-Implementierung).

**Ursprung:** [preThesis/03-recherche/R10-esp32-plattform.md:213-231](../../preThesis/03-recherche/R10-esp32-plattform.md#L213)
**Belege:** [Espressif Systems · esp_dsp_benchmarks](https://docs.espressif.com/projects/esp-dsp/en/latest/esp32/esp-dsp-benchmarks.html) — Fundstelle: IIR Filters row; benchmark methodology (aus Stage 1; am Original prüfen); [Espressif Systems · esp_dsp_api](https://docs.espressif.com/projects/esp-dsp/en/latest/esp32/esp-dsp-apis.html) — Seite prüfen

<a id="c019"></a>
**C019 · LITERATURMESSUNG / BENCHMARK · QUELLENSET UNVOLLSTÄNDIG**

Der ESP-DSP-Benchmark weist für ESP32-S3 97 847 Zyklen für `dsps_fft2r_fc32` mit 1 024 komplexen Punkten bei O2 aus.

**Ursprung:** [preThesis/03-recherche/R10-esp32-plattform.md:285-307](../../preThesis/03-recherche/R10-esp32-plattform.md#L285)
**Belege:** [Espressif Systems · esp_dsp_benchmarks](https://docs.espressif.com/projects/esp-dsp/en/latest/esp32/esp-dsp-benchmarks.html) — Fundstelle: FFTs Radix-2, 1024 complex points row (aus Stage 1; am Original prüfen); [Espressif Systems · esp_dsp_api](https://docs.espressif.com/projects/esp-dsp/en/latest/esp32/esp-dsp-apis.html) — Seite prüfen

<a id="c017"></a>
**C017 · LITERATURMESSUNG / BENCHMARK · QUELLENSET UNVOLLSTÄNDIG**

Der ESP-DSP-Benchmark weist für ESP32-S3 bei `dsps_fir_f32` mit 256 Koeffizienten 443 671 Zyklen für 1 024 Samples aus; dezimierend (Faktor 4) sind es 115 499 Zyklen.

**Ursprung:** [preThesis/03-recherche/R10-esp32-plattform.md:233-256](../../preThesis/03-recherche/R10-esp32-plattform.md#L233)
**Belege:** [Espressif Systems · esp_dsp_benchmarks](https://docs.espressif.com/projects/esp-dsp/en/latest/esp32/esp-dsp-benchmarks.html) — Fundstelle: FIR Filters rows (aus Stage 1; am Original prüfen); [Espressif Systems · esp_dsp_api](https://docs.espressif.com/projects/esp-dsp/en/latest/esp32/esp-dsp-apis.html) — Seite prüfen

### Folgerungen, Entwurfsentscheidungen und Grenzen

<a id="a007"></a>
**A007 · METHODE / PRÜFVERFAHREN**

Envelope-Energie kann mit RMS-, Hilbert- oder Shannon-Energie des Murmurfensters bestimmt werden.

**Ursprung:** [preThesis/03-recherche/R01-murmur-metrik.md:53](../../preThesis/03-recherche/R01-murmur-metrik.md#L53)
**Belege:** [Hilbert-envelope features for cardiac disease classi 2022 · hilbert_env](https://www.sciencedirect.com/science/article/pii/S1746809422003780) — Fundstelle: Abstract (publisher page; full text paywalled) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [Arjoune, Y 2024 · shannon_env](https://pmc.ncbi.nlm.nih.gov/articles/PMC11469632/) — Seite prüfen; [Noponen, A.-L., Lukkarinen, S., & Sepponen, R · murmur_text](https://accesscardiology.mhmedical.com/content.aspx?bookid=382&sectionid=40663653) — Fundstelle: Chapter 2, Clinical Auscultation and Conventional Phonocardiography (web lines 144–150) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig

<a id="a008"></a>
**A008 · METHODE / PRÜFVERFAHREN**

Murmur-Dauer oder Flächenanteil oberhalb eines Hüllkurvenschwellwerts ist stark schwellenabhängig.

**Ursprung:** [preThesis/03-recherche/R01-murmur-metrik.md:55](../../preThesis/03-recherche/R01-murmur-metrik.md#L55)
**Belege:** [Hilbert-envelope features for cardiac disease classi 2022 · hilbert_env](https://www.sciencedirect.com/science/article/pii/S1746809422003780) — Fundstelle: Abstract (publisher page; full text paywalled) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [Arjoune, Y 2024 · shannon_env](https://pmc.ncbi.nlm.nih.gov/articles/PMC11469632/) — Seite prüfen; [Delgado-Trejos, E., Quiceno-Manrique, A 2009 · digital_auscultation_murmur](https://link.springer.com/article/10.1007/s10439-008-9611-z) — Fundstelle: Introduction, murmur and heart cycle description (existing registry reports web lines 71–85) (aus Stage 1; am Original prüfen)

<a id="a006"></a>
**A006 · METHODE / PRÜFVERFAHREN**

Spektrale Entropie und Flachheit beschreiben die Verteilung normalisierter Spektralenergie und sind allein eingeschränkt interpretierbar.

**Ursprung:** [preThesis/03-recherche/R01-murmur-metrik.md:52](../../preThesis/03-recherche/R01-murmur-metrik.md#L52)
**Belege:** [Noponen, A.-L., Lukkarinen, S., & Sepponen, R · murmur_text](https://accesscardiology.mhmedical.com/content.aspx?bookid=382&sectionid=40663653) — Fundstelle: Chapter 2, Clinical Auscultation and Conventional Phonocardiography (web lines 144–150) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [Delgado-Trejos, E., Quiceno-Manrique, A 2009 · digital_auscultation_murmur](https://link.springer.com/article/10.1007/s10439-008-9611-z) — Fundstelle: Introduction, murmur and heart cycle description (existing registry reports web lines 71–85) (aus Stage 1; am Original prüfen); [Wen, H 2023 · murmur_filter](https://arxiv.org/abs/2303.02988) — Fundstelle: Section 2.1, preprocessing pipeline (arXiv text lines 13–26) (aus Stage 1; am Original prüfen)

<a id="a005"></a>
**A005 · METHODE / PRÜFVERFAHREN**

Spektraler Schwerpunkt und Roll-off beschreiben spektrale Form, belegen aber allein keine bessere Murmur-Detektierbarkeit.

**Ursprung:** [preThesis/03-recherche/R01-murmur-metrik.md:51](../../preThesis/03-recherche/R01-murmur-metrik.md#L51)
**Belege:** [Noponen, A.-L., Lukkarinen, S., & Sepponen, R · murmur_text](https://accesscardiology.mhmedical.com/content.aspx?bookid=382&sectionid=40663653) — Fundstelle: Chapter 2, Clinical Auscultation and Conventional Phonocardiography (web lines 144–150) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [Delgado-Trejos, E., Quiceno-Manrique, A 2009 · digital_auscultation_murmur](https://link.springer.com/article/10.1007/s10439-008-9611-z) — Fundstelle: Introduction, murmur and heart cycle description (existing registry reports web lines 71–85) (aus Stage 1; am Original prüfen); [Wen, H 2023 · murmur_filter](https://arxiv.org/abs/2303.02988) — Fundstelle: Section 2.1, preprocessing pipeline (arXiv text lines 13–26) (aus Stage 1; am Original prüfen)
