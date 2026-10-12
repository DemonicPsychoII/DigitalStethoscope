# MEMS-Mikrofone

[Zum Einstieg](../README.md) · [Offene Punkte](../offene-punkte.md)

LFRO und Kennwerte → Schnittstellen und Bauteilvergleich → Grenzen der Entzerrung.

**10 aktive Einheiten.** Schreibreihenfolge: Definition → Mechanismus → Werte → Folgerung. Die Aussagen sind Material, kein fertiger Fließtext.

**Schreibhinweis:** Literaturgrundlagen erklären das Verfahren. Zielwerte, Architekturentscheidungen und Berichtsempfehlungen als solche benennen und später in Anforderungen/Methodik begründen.

## Schreibbausteine

### Begriffe und Definitionen

<a id="b080"></a>
**B080 · LITERATURFAKT / REGEL**

Der Knowles/SELTECH-Portfolioleitfaden definiert LFRO als den -3-dB-Punkt relativ zur Mikrofonempfindlichkeit bei 1 kHz.

**Ursprung:** [preThesis/03-recherche/R07-bruststueck-mems.md:183-202](../../preThesis/03-recherche/R07-bruststueck-mems.md#L183)
**Belege:** [Seltech · knowles_portfolio_2023](https://cdn.thomasnet.com/ccp/30973684/351950.pdf) — Fundstelle: LFRO definition, PDF p. 5 (aus Stage 1; am Original prüfen); [Infineon Technologies · ecm_datasheet_im69d130](https://www.infineon.com/assets/row/public/documents/24/49/infineon-im69d130-datasheet-en.pdf) — Seite prüfen · **LINK DEFEKT**; [Knowles/Syntiant · knowles_spk18_datasheet](https://www.mouser.com/datasheet/3/6144/1/SPK18R1LM4H_1_Hyperion_Datasheet.pdf) — Seite prüfen

### Mechanismen und Zusammenhänge

<a id="b055"></a>
**B055 · LITERATURFAKT / REGEL**

Eine digitale Entzerrung kann den Amplitudenabfall im Mikrofonfrequenzgang ausgleichen, aber fehlende Signalanteile oder den Rauschboden unterhalb der Grenzfrequenz nicht zurückgewinnen.

**Ursprung:** [preThesis/03-recherche/R07-bruststueck-mems.md:272-281](../../preThesis/03-recherche/R07-bruststueck-mems.md#L272)
**Belege:** [Infineon Technologies · ecm_datasheet_im69d130](https://www.infineon.com/assets/row/public/documents/24/49/infineon-im69d130-datasheet-en.pdf) — Fundstelle: Table 1, Acoustic specifications; datasheet p. 4 (aus Stage 1; am Original prüfen) · **LINK DEFEKT**; [Infineon Technologies · ecm_product_im69d130](https://www.infineon.com/cms/de/product/sensor/mems-microphones/mems-microphones-for-consumer/im69d130/) — Fundstelle: Features/product specification (aus Stage 1; am Original prüfen); [MEMS and ECM Sensor Technologies for Cardiorespirato 2024 · mems_cardiorespiratory_review](https://arxiv.org/abs/2406.12432) — Seite prüfen

<a id="b049"></a>
**B049 · LITERATURFAKT / REGEL**

R07 bewertet IM69D130 für Signale ab etwa 30 Hz als geeignet, aber 20 Hz liegt bereits unterhalb des spezifizierten 28-Hz-LFRO.

**Ursprung:** [preThesis/03-recherche/R07-bruststueck-mems.md:204-216](../../preThesis/03-recherche/R07-bruststueck-mems.md#L204)
**Belege:** [Infineon Technologies · ecm_datasheet_im69d130](https://www.infineon.com/assets/row/public/documents/24/49/infineon-im69d130-datasheet-en.pdf) — Fundstelle: Table 1, Acoustic specifications; datasheet p. 4 (aus Stage 1; am Original prüfen) · **LINK DEFEKT**; [Infineon Technologies · ecm_product_im69d130](https://www.infineon.com/cms/de/product/sensor/mems-microphones/mems-microphones-for-consumer/im69d130/) — Fundstelle: Features/product specification (aus Stage 1; am Original prüfen); [MEMS and ECM Sensor Technologies for Cardiorespirato 2024 · mems_cardiorespiratory_review](https://arxiv.org/abs/2406.12432) — Seite prüfen

### Werte und dokumentierte Befunde

<a id="b048"></a>
**B048 · LITERATUR- / HERSTELLERWERT**

Der Hersteller spezifiziert IM69D130 als PDM-Mikrofon mit 28-Hz-LFRO, 69 dB(A) SNR und 130 dB SPL AOP.

**Ursprung:** [preThesis/03-recherche/R07-bruststueck-mems.md:183-216](../../preThesis/03-recherche/R07-bruststueck-mems.md#L183)
**Belege:** [Infineon Technologies · ecm_datasheet_im69d130](https://www.infineon.com/assets/row/public/documents/24/49/infineon-im69d130-datasheet-en.pdf) — Fundstelle: Table 1, Acoustic specifications; datasheet p. 4 (aus Stage 1; am Original prüfen) · **LINK DEFEKT**; [Infineon Technologies · ecm_product_im69d130](https://www.infineon.com/cms/de/product/sensor/mems-microphones/mems-microphones-for-consumer/im69d130/) — Fundstelle: Features/product specification (aus Stage 1; am Original prüfen); [MEMS and ECM Sensor Technologies for Cardiorespirato 2024 · mems_cardiorespiratory_review](https://arxiv.org/abs/2406.12432) — Seite prüfen

<a id="b051"></a>
**B051 · LITERATUR- / HERSTELLERWERT · ANNAHME · ersetzt U061**

Laut R07 besitzt ICS-43434 einen digitalen I²S-Ausgang und eine 60-Hz-Untergrenze; Herstellerdaten nennen 65 dBA SNR im High-Performance-Modus (64 dBA im Low-Power-Modus) und 120 dB SPL AOP; R07 bewertet ihn als nicht ausreichend für 20–60 Hz.

**Ursprung:** [preThesis/03-recherche/R07-bruststueck-mems.md:231-247](../../preThesis/03-recherche/R07-bruststueck-mems.md#L231)
**Belege:** [TDK InvenSense · ics43434_datasheet_verified](https://invensense.tdk.com/wp-content/uploads/2016/02/DS-000069-ICS-43434-v1.2.pdf) — Seite prüfen; [TDK InvenSense · ics43434_product](https://www.invensense.tdk.com/en-us/products/microphone/ics-43434) — Fundstelle: Product details/features (aus Stage 1; am Original prüfen); [MEMS and ECM Sensor Technologies for Cardiorespirato 2024 · mems_cardiorespiratory_review](https://arxiv.org/abs/2406.12432) — Seite prüfen

<a id="b050"></a>
**B050 · LITERATUR- / HERSTELLERWERT · ANNAHME · ersetzt U061**

Laut R07 liegt ICS-40180 mit analogem Ausgang, 60-Hz-LFRO, 65-dBA-SNR und etwa 124-dB-SPL-AOP zu hoch für eine unverfälschte Erfassung von S3/S4-Anteilen bei 20–60 Hz.

**Ursprung:** [preThesis/03-recherche/R07-bruststueck-mems.md:218-229](../../preThesis/03-recherche/R07-bruststueck-mems.md#L218)
**Belege:** [TDK InvenSense · ics40180_datasheet](https://invensense.tdk.com/wp-content/uploads/2015/02/ICS-40180_DS.pdf) — Seite prüfen · **LINK DEFEKT**; [TDK Product Center · ics40180_product](https://product.tdk.com/en/search/sw_piezo/mic/mems-mic/info?part_no=ICS-40180) — Fundstelle: Electrical characteristics (aus Stage 1; am Original prüfen); [MEMS and ECM Sensor Technologies for Cardiorespirato 2024 · mems_cardiorespiratory_review](https://arxiv.org/abs/2406.12432) — Seite prüfen

<a id="b053"></a>
**B053 · LITERATUR- / HERSTELLERWERT · ANNAHME**

R07 empfiehlt IM68A130 als analoge Alternative und die Herstellerdaten spezifizieren 10-Hz-LFRO, 68-dB(A)-SNR und 130-dB-SPL-AOP.

**Ursprung:** [preThesis/03-recherche/R07-bruststueck-mems.md:249-260](../../preThesis/03-recherche/R07-bruststueck-mems.md#L249)
**Belege:** [Infineon Technologies · im68a130_datasheet](https://www.infineon.com/assets/row/public/documents/24/49/infineon-im68a130-datasheet-en.pdf?fileId=8ac78c8c85ecb34701860371623f1204) — Seite prüfen; [Infineon Technologies · im68a130_product](https://www.infineon.com/part/IM68A130) — Fundstelle: Product details/features (aus Stage 1; am Original prüfen); [MEMS and ECM Sensor Technologies for Cardiorespirato 2024 · mems_cardiorespiratory_review](https://arxiv.org/abs/2406.12432) — Seite prüfen

<a id="b078"></a>
**B078 · LITERATUR- / HERSTELLERWERT · ersetzt U061**

R07 führt Knowles SPH0645LM4H-B als I²S-MEMS-Mikrofon mit 45-Hz-LFRO, 65-dB(A)-SNR und 120-dB-SPL-AOP auf; die Herstellerunterlage bestätigt diese Werte.

**Ursprung:** [preThesis/03-recherche/R07-bruststueck-mems.md:183-202](../../preThesis/03-recherche/R07-bruststueck-mems.md#L183)
**Belege:** [Knowles · knowles_sph0645_flex](https://www.mouser.com/datasheet/2/218/kas-700-0137-crawford-mic-on-flex-product-brief-re-1624260.pdf) — Fundstelle: Key Parameters Specifications, PDF p. 1 (aus Stage 1; am Original prüfen); [MEMS and ECM Sensor Technologies for Cardiorespirato 2024 · mems_cardiorespiratory_review](https://arxiv.org/abs/2406.12432) — Seite prüfen; [Acoustic Methods for Pulmonary Diagnosis · pulmonary_acoustic_methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC6874908/) — Seite prüfen

<a id="b052"></a>
**B052 · LITERATUR- / HERSTELLERWERT · ersetzt U061**

R07 listet SPK18R1LM4H-1 als digitales PDM-MEMS-Mikrofon mit 20-Hz-LFRO, 70,5-dB(A)-SNR und 128-dB-SPL-AOP bei 10 % THD.

**Ursprung:** [preThesis/03-recherche/R07-bruststueck-mems.md:183-202](../../preThesis/03-recherche/R07-bruststueck-mems.md#L183)
**Belege:** [Knowles/Syntiant · knowles_spk18_datasheet](https://www.mouser.com/datasheet/3/6144/1/SPK18R1LM4H_1_Hyperion_Datasheet.pdf) — Fundstelle: Table 3, acoustic characteristics (aus Stage 1; am Original prüfen); [MEMS and ECM Sensor Technologies for Cardiorespirato 2024 · mems_cardiorespiratory_review](https://arxiv.org/abs/2406.12432) — Seite prüfen; [Acoustic Methods for Pulmonary Diagnosis · pulmonary_acoustic_methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC6874908/) — Seite prüfen

### Folgerungen, Entwurfsentscheidungen und Grenzen

<a id="b054"></a>
**B054 · EIGENE ENTSCHEIDUNG / ENTWURFSEMPFEHLUNG · ANNAHME**

R07 empfiehlt IM69D130 als praktisch verfügbare digitale Alternative; ein Shield2Go-Board mit ADAU7002 wird als Breakoutoption genannt.

**Ursprung:** [preThesis/03-recherche/R07-bruststueck-mems.md:204-216](../../preThesis/03-recherche/R07-bruststueck-mems.md#L204)
**Belege:** [Infineon Technologies · ecm_datasheet_im69d130](https://www.infineon.com/assets/row/public/documents/24/49/infineon-im69d130-datasheet-en.pdf) — Fundstelle: Table 1, Acoustic specifications; datasheet p. 4 (aus Stage 1; am Original prüfen) · **LINK DEFEKT**; [Infineon Technologies · ecm_product_im69d130](https://www.infineon.com/cms/de/product/sensor/mems-microphones/mems-microphones-for-consumer/im69d130/) — Fundstelle: Features/product specification (aus Stage 1; am Original prüfen); [MEMS and ECM Sensor Technologies for Cardiorespirato 2024 · mems_cardiorespiratory_review](https://arxiv.org/abs/2406.12432) — Seite prüfen
