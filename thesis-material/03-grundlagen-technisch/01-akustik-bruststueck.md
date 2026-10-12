# Akustik und Bruststück

[Zum Einstieg](../README.md) · [Offene Punkte](../offene-punkte.md)

Schalldruck und Übertragung → Kopplung → Resonanzmodelle → Grenzen.

**11 aktive Einheiten.** Schreibreihenfolge: Definition → Mechanismus → Werte → Folgerung. Die Aussagen sind Material, kein fertiger Fließtext.

**Schreibhinweis:** Literaturgrundlagen erklären das Verfahren. Zielwerte, Architekturentscheidungen und Berichtsempfehlungen als solche benennen und später in Anforderungen/Methodik begründen.

**Achtung:** Helmholtz-Abschätzung und gekoppeltes Bruststückmodell widersprechen sich; [B075](../10-diskussion-ausblick.md#b075) vor Zahlenübernahme lesen.

## Schreibbausteine

### Begriffe und Definitionen

<a id="b042"></a>
**B042 · LITERATURFAKT / REGEL · ANNAHME**

R07 verwendet für die Hohlraumkopplung eine vereinfachte Helmholtz-Resonanzabschätzung mit f_H = c/(2π)·√(A/(V·L_eff)); deren Anwendbarkeit auf das gekoppelte Stethoskop-Brust-System ist fraglich.

**Ursprung:** [preThesis/03-recherche/R07-bruststueck-mems.md:107-116](../../preThesis/03-recherche/R07-bruststueck-mems.md#L107)
**Belege:** [Weiss, D 2019 · invitro_stethoscopes](https://pmc.ncbi.nlm.nih.gov/articles/PMC6339642/) — Seite prüfen; [Alanazi, A., Atcherson, S., Franklin, C., & Bryan, M 2020 · frequency_response_stethoscopes](https://doi.org/10.4103/sjmms.sjmms_118_19) — Seite prüfen; [Nussbaumer, M 2022 · nussbaumer_stethoscope_acoustics](https://www.repository.cam.ac.uk/items/feadd88b-9e03-44fb-a875-c49f7c550259) — Seite prüfen · 🔒 Volltextzugang prüfen: Publisher full text paywalled; Cambridge record is open.

<a id="b068"></a>
**B068 · LITERATURFAKT / REGEL**

R08 definiert den Schalldruckpegel als Lp = 20 log10(p_rms / 20 μPa).

**Ursprung:** [preThesis/03-recherche/R08-messmethode-akustik.md:264-276](../../preThesis/03-recherche/R08-messmethode-akustik.md#L264)
**Belege:** [IEC 61672-1:2013 · iec61672_1](https://webstore.ansi.org/standards/iec/iec61672ed2013) — Seite prüfen · 🔒 Volltext kostenpflichtig; [IEC 60268-5:2003+A1:2007 · iec60268_5](https://webstore.iec.ch/en/publication/1224) — Fundstelle: Scope/product page (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [Weiss, D 2019 · invitro_stethoscopes](https://pmc.ncbi.nlm.nih.gov/articles/PMC6339642/) — Seite prüfen

<a id="b070"></a>
**B070 · LITERATURFAKT / REGEL**

R08 definiert THD als Verhältnis der quadratischen Summe der Obertonamplituden zur Grundschwingungsamplitude.

**Ursprung:** [preThesis/03-recherche/R08-messmethode-akustik.md:315-358](../../preThesis/03-recherche/R08-messmethode-akustik.md#L315)
**Belege:** [Farina, A 2000 · farina_ess](https://aes.org/publications/elibrary-page/?id=10211) — Seite prüfen (übernommene Angabe: Abstract; paper page unverified) · 🔒 Volltext kostenpflichtig; [Ćirić, D 2013 · ciric_swept_sine](https://www.sciencedirect.com/science/article/abs/pii/S0003682X12002563) — Fundstelle: pp. 375–382 (metadata verified) (aus Stage 1; am Original prüfen) · 🔒 Volltextzugang prüfen: Full text may be paywalled.; [IEC 60268-5:2003+A1:2007 · iec60268_5](https://webstore.iec.ch/en/publication/1224) — Fundstelle: Scope/product page (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig

### Mechanismen und Zusammenhänge

<a id="b071"></a>
**B071 · LITERATURFAKT / REGEL**

IEC 60268-5 behandelt Lautsprechermessverfahren mit Sinus-, spezifizierten Rausch- oder Impulssignalen, aber ist keine Stethoskop-Prüfnorm.

**Ursprung:** [preThesis/03-recherche/R08-messmethode-akustik.md:360-374](../../preThesis/03-recherche/R08-messmethode-akustik.md#L360)
**Belege:** [IEC 61672-1:2013 · iec61672_1](https://webstore.ansi.org/standards/iec/iec61672ed2013) — Seite prüfen · 🔒 Volltext kostenpflichtig; [IEC 60268-5:2003+A1:2007 · iec60268_5](https://webstore.iec.ch/en/publication/1224) — Fundstelle: Scope/product page (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [Weiss, D 2019 · invitro_stethoscopes](https://pmc.ncbi.nlm.nih.gov/articles/PMC6339642/) — Seite prüfen

<a id="b047"></a>
**B047 · LITERATURFAKT / REGEL**

R07 beschreibt Schlauchdämpfung tiefer Frequenzen und stehende Wellen als Risiken für die Stethoskopübertragung.

**Ursprung:** [preThesis/03-recherche/R07-bruststueck-mems.md:166-180](../../preThesis/03-recherche/R07-bruststueck-mems.md#L166)
**Belege:** [Weiss, D 2019 · invitro_stethoscopes](https://pmc.ncbi.nlm.nih.gov/articles/PMC6339642/) — Seite prüfen; [Alanazi, A., Atcherson, S., Franklin, C., & Bryan, M 2020 · frequency_response_stethoscopes](https://doi.org/10.4103/sjmms.sjmms_118_19) — Seite prüfen; [Nussbaumer, M 2022 · nussbaumer_stethoscope_acoustics](https://www.repository.cam.ac.uk/items/feadd88b-9e03-44fb-a875-c49f7c550259) — Seite prüfen · 🔒 Volltextzugang prüfen: Publisher full text paywalled; Cambridge record is open.

<a id="b072"></a>
**B072 · LITERATURFAKT / REGEL**

R08 ordnet IEC 61672-1 als Referenz für Klassen-1/2-Schallpegelmesser und Referenzmikrofon-Auswahl ein, nicht als Stethoskopnorm.

**Ursprung:** [preThesis/03-recherche/R08-messmethode-akustik.md:360-374](../../preThesis/03-recherche/R08-messmethode-akustik.md#L360)
**Belege:** [IEC 61672-1:2013 · iec61672_1](https://webstore.ansi.org/standards/iec/iec61672ed2013) — Seite prüfen · 🔒 Volltext kostenpflichtig; [IEC 60268-5:2003+A1:2007 · iec60268_5](https://webstore.iec.ch/en/publication/1224) — Fundstelle: Scope/product page (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [Weiss, D 2019 · invitro_stethoscopes](https://pmc.ncbi.nlm.nih.gov/articles/PMC6339642/) — Seite prüfen

<a id="b043"></a>
**B043 · LITERATURFAKT / REGEL · ANNAHME**

Unter der Helmholtz-Modellannahme sinkt die Resonanzfrequenz bei größerem Volumen und längerer Halslänge und steigt bei größerem Halsquerschnitt.

**Ursprung:** [preThesis/03-recherche/R07-bruststueck-mems.md:107-116](../../preThesis/03-recherche/R07-bruststueck-mems.md#L107)
**Belege:** [Weiss, D 2019 · invitro_stethoscopes](https://pmc.ncbi.nlm.nih.gov/articles/PMC6339642/) — Seite prüfen; [Alanazi, A., Atcherson, S., Franklin, C., & Bryan, M 2020 · frequency_response_stethoscopes](https://doi.org/10.4103/sjmms.sjmms_118_19) — Seite prüfen; [Nussbaumer, M 2022 · nussbaumer_stethoscope_acoustics](https://www.repository.cam.ac.uk/items/feadd88b-9e03-44fb-a875-c49f7c550259) — Seite prüfen · 🔒 Volltextzugang prüfen: Publisher full text paywalled; Cambridge record is open.

### Werte und dokumentierte Befunde

<a id="b044"></a>
**B044 · EIGENER ZIELWERT / VORLÄUFIGER VORSCHLAG · ANNAHME**

R07 berechnet im vereinfachten Helmholtz-Modell für 6-mm-Halsdurchmesser, A ≈ 28,3 mm² und effektive Länge 10 mm ein Volumen von ungefähr 21 ml für eine 20-Hz-Resonanz; dies ist eine theoretische Abschätzung.

**Ursprung:** [preThesis/03-recherche/R07-bruststueck-mems.md:118-136](../../preThesis/03-recherche/R07-bruststueck-mems.md#L118)
**Belege:** [Weiss, D 2019 · invitro_stethoscopes](https://pmc.ncbi.nlm.nih.gov/articles/PMC6339642/) — Seite prüfen; [Alanazi, A., Atcherson, S., Franklin, C., & Bryan, M 2020 · frequency_response_stethoscopes](https://doi.org/10.4103/sjmms.sjmms_118_19) — Seite prüfen; [Nussbaumer, M 2022 · nussbaumer_stethoscope_acoustics](https://www.repository.cam.ac.uk/items/feadd88b-9e03-44fb-a875-c49f7c550259) — Seite prüfen · 🔒 Volltextzugang prüfen: Publisher full text paywalled; Cambridge record is open.

<a id="u059"></a>
**U059 · EIGENER ZIELWERT / VORLÄUFIGER VORSCHLAG · QUELLENSET UNVOLLSTÄNDIG**

R07 gibt als Helmholtz-Resonanzabschätzung für 20 Hz ca. 21 ml bei üblichen Halsabmessungen an und empfiehlt eine kleine, kurze, bedämpfte Kammer, um Resonanz oberhalb des Bands 20–600 Hz zu legen.

**Ursprung:** [preThesis/02-entscheidungen/open-questions.md:179-182](../../preThesis/02-entscheidungen/open-questions.md#L179)
**Belege:** [Morse, P 1948 · helmholtz_textbook](https://archive.org/details/vibrationsound0000mors) — Seite prüfen (Hinweis: Relevant article section/table not verified in full text during this pass.); [Exploring Microphone Technologies for Digital Auscul 2023 · mems_microphones_review](https://www.mdpi.com/2072-666X/14/11/2092) — Seite prüfen (Hinweis: Relevant article section/table not verified in full text during this pass.); [Weiss, D 2019 · invitro_stethoscopes](https://pmc.ncbi.nlm.nih.gov/articles/PMC6339642/) — Seite prüfen (Hinweis: Relevant article section/table not verified in full text during this pass.)

### Folgerungen, Entwurfsentscheidungen und Grenzen

<a id="b046"></a>
**B046 · RISIKO / EINORDNUNG**

Berührung, Kabelbewegung, Handdruck, Reibung am Membranring und Leiterplattenvibration werden als mögliche Körperschall-/Handhabungsstörungen benannt.

**Ursprung:** [preThesis/03-recherche/R07-bruststueck-mems.md:149-165](../../preThesis/03-recherche/R07-bruststueck-mems.md#L149)
**Belege:** [MEMS and ECM Sensor Technologies for Cardiorespirato 2024 · mems_cardiorespiratory_review](https://arxiv.org/abs/2406.12432) — Seite prüfen; [Acoustic Methods for Pulmonary Diagnosis · pulmonary_acoustic_methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC6874908/) — Seite prüfen; [Delgado-Trejos, E., Quiceno-Manrique, A 2009 · digital_auscultation_murmur](https://link.springer.com/article/10.1007/s10439-008-9611-z) — Fundstelle: Introduction, heart cycle/murmur description (web text lines 71–73; 85). (aus Stage 1; am Original prüfen)

<a id="b045"></a>
**B045 · RISIKO / EINORDNUNG**

R07 bewertet Leckagen an Membran, Bruststück und Mikrofonkammer als potenzielle Ursache für Hochpasswirkung und Dämpfung niederfrequenter Signale um 20–40 Hz.

**Ursprung:** [preThesis/03-recherche/R07-bruststueck-mems.md:138-147](../../preThesis/03-recherche/R07-bruststueck-mems.md#L138)
**Belege:** [Alanazi, A., Atcherson, S., Franklin, C., & Bryan, M 2020 · frequency_response_stethoscopes](https://doi.org/10.4103/sjmms.sjmms_118_19) — Seite prüfen; [Weiss, D 2019 · invitro_stethoscopes](https://pmc.ncbi.nlm.nih.gov/articles/PMC6339642/) — Seite prüfen; [Goh, R 2023 · goh_chestpiece](https://staffprofiles.bournemouth.ac.uk/display/journal-article/388323) — Fundstelle: pp. 137–140 (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig
