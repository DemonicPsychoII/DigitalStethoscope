# Evaluation: Akustische Übertragungskette

[Zum Einstieg](../README.md) · [Offene Punkte](../offene-punkte.md)

Optionaler Messumfang → Koppler/Referenz → Signale → Unsicherheit. W1 zuerst klären.

**18 aktive Einheiten.** Schreibreihenfolge: Definition → Mechanismus → Werte → Folgerung. Die Aussagen sind Material, kein fertiger Fließtext.

## Schreibbausteine

### Mechanismen und Zusammenhänge

<a id="b057"></a>
**B057 · LITERATURFAKT / REGEL · ersetzt U063**

R08 hält fest, dass keine allgemein verbindliche akustische Produktnorm für elektronische Stethoskope existiert.

**Ursprung:** [preThesis/03-recherche/R08-messmethode-akustik.md:22-32](../../preThesis/03-recherche/R08-messmethode-akustik.md#L22)
**Belege:** [Weiss, D 2019 · invitro_stethoscopes](https://pmc.ncbi.nlm.nih.gov/articles/PMC6339642/) — Seite prüfen; [Alanazi, A., Atcherson, S., Franklin, C., & Bryan, M 2020 · frequency_response_stethoscopes](https://doi.org/10.4103/sjmms.sjmms_118_19) — Seite prüfen; [Nussbaumer, M 2022 · nussbaumer_stethoscope_acoustics](https://www.repository.cam.ac.uk/items/feadd88b-9e03-44fb-a875-c49f7c550259) — Seite prüfen · 🔒 Volltextzugang prüfen: Publisher full text paywalled; Cambridge record is open.; [Nussbaumer, M 2022 · nussbaumer_stethoscope_acoustics](https://www.repository.cam.ac.uk/items/feadd88b-9e03-44fb-a875-c49f7c550259) — Seite prüfen · 🔒 Volltextzugang prüfen: Publisher full text paywalled; Cambridge record is open.

### Werte und dokumentierte Befunde

<a id="b063"></a>
**B063 · EIGENER ZIELWERT / VORLÄUFIGER VORSCHLAG · ANNAHME**

R08 nennt ESS-Einstellungen von 15–20 Hz Start, 1200–1500 Hz Ende, 10–30 s Dauer und mindestens drei Wiederholungen für einen 20–1000-Hz-Auswertebereich.

**Ursprung:** [preThesis/03-recherche/R08-messmethode-akustik.md:136-168](../../preThesis/03-recherche/R08-messmethode-akustik.md#L136)
**Belege:** [Farina, A 2000 · farina_ess](https://aes.org/publications/elibrary-page/?id=10211) — Seite prüfen (übernommene Angabe: Abstract; paper page unverified) · 🔒 Volltext kostenpflichtig; [Ćirić, D 2013 · ciric_swept_sine](https://www.sciencedirect.com/science/article/abs/pii/S0003682X12002563) — Fundstelle: pp. 375–382 (metadata verified) (aus Stage 1; am Original prüfen) · 🔒 Volltextzugang prüfen: Full text may be paywalled.; [IEC 60268-5:2003+A1:2007 · iec60268_5](https://webstore.iec.ch/en/publication/1224) — Fundstelle: Scope/product page (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig

### Folgerungen, Entwurfsentscheidungen und Grenzen

<a id="b059"></a>
**B059 · METHODENVORSCHLAG**

Die Übertragungsfunktion soll als Verhältnis des Stethoskopsignals X_steth(f) zum gleichzeitig gemessenen Referenzschalldruck P_ref(f) bestimmt werden.

**Ursprung:** [preThesis/03-recherche/R08-messmethode-akustik.md:36-82](../../preThesis/03-recherche/R08-messmethode-akustik.md#L36)
**Belege:** [Weiss, D 2019 · invitro_stethoscopes](https://pmc.ncbi.nlm.nih.gov/articles/PMC6339642/) — Seite prüfen; [Alanazi, A., Atcherson, S., Franklin, C., & Bryan, M 2020 · frequency_response_stethoscopes](https://doi.org/10.4103/sjmms.sjmms_118_19) — Seite prüfen; [Nussbaumer, M 2022 · nussbaumer_stethoscope_acoustics](https://www.repository.cam.ac.uk/items/feadd88b-9e03-44fb-a875-c49f7c550259) — Seite prüfen · 🔒 Volltextzugang prüfen: Publisher full text paywalled; Cambridge record is open.; [Nowak, L 2017 · nowak_stethoscope_method](https://pubmed.ncbi.nlm.nih.gov/28372089/) — Fundstelle: 141(3), article p. 1940 (record verified) (aus Stage 1; am Original prüfen) · 🔒 Volltextzugang prüfen: Full text may be paywalled.

<a id="a034"></a>
**A034 · METHODENVORSCHLAG · ANNAHME**

Für den Selbstbau schlägt R02 mindestens 10–20 Wiederholungen desselben Signals sowie Referenzmikrofon oder Referenzstethoskop vor.

**Ursprung:** [preThesis/03-recherche/R02-ground-truth.md:141-152](../../preThesis/03-recherche/R02-ground-truth.md#L141)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="a033"></a>
**A033 · METHODE / PRÜFVERFAHREN · ANNAHME**

R02 skizziert einen Selbstbau-Prüfstand aus WAV-Quelle, Lautsprecher/Exciter, Thoraxplatte und definierten Bruststückpositionen als kontrollierte Zusatzquelle.

**Ursprung:** [preThesis/03-recherche/R02-ground-truth.md:94,141-152](../../preThesis/03-recherche/R02-ground-truth.md#L94)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="b056"></a>
**B056 · METHODENVORSCHLAG · ANNAHME**

R07 empfiehlt für Prototypvergleich direkte Kammerankopplung und 5-cm-Schlauchankopplung mit demselben Mikrofon zu messen.

**Ursprung:** [preThesis/03-recherche/R07-bruststueck-mems.md:283-319](../../preThesis/03-recherche/R07-bruststueck-mems.md#L283)
**Belege:** [Alanazi, A., Atcherson, S., Franklin, C., & Bryan, M 2020 · frequency_response_stethoscopes](https://doi.org/10.4103/sjmms.sjmms_118_19) — Seite prüfen; [Weiss, D 2019 · invitro_stethoscopes](https://pmc.ncbi.nlm.nih.gov/articles/PMC6339642/) — Seite prüfen; [Goh, R 2023 · goh_chestpiece](https://doi.org/10.1109/SENNANO57767.2023.10352567) — Fundstelle: pp. 137–140 (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig

<a id="b060"></a>
**B060 · METHODE / PRÜFVERFAHREN**

R08 beschreibt einen akustischen Koppler mit reproduzierbarer Auflagefläche, Abdichtung, dokumentierter Geometrie, Referenzmikrofonöffnung und definierter Anpresskraft.

**Ursprung:** [preThesis/03-recherche/R08-messmethode-akustik.md:84-97](../../preThesis/03-recherche/R08-messmethode-akustik.md#L84)
**Belege:** [Weiss, D 2019 · invitro_stethoscopes](https://pmc.ncbi.nlm.nih.gov/articles/PMC6339642/) — Seite prüfen; [Alanazi, A., Atcherson, S., Franklin, C., & Bryan, M 2020 · frequency_response_stethoscopes](https://doi.org/10.4103/sjmms.sjmms_118_19) — Seite prüfen; [Nussbaumer, M 2022 · nussbaumer_stethoscope_acoustics](https://www.repository.cam.ac.uk/items/feadd88b-9e03-44fb-a875-c49f7c550259) — Seite prüfen · 🔒 Volltextzugang prüfen: Publisher full text paywalled; Cambridge record is open.; [Nowak, L 2017 · nowak_stethoscope_method](https://pubmed.ncbi.nlm.nih.gov/28372089/) — Fundstelle: 141(3), article p. 1940 (record verified) (aus Stage 1; am Original prüfen) · 🔒 Volltextzugang prüfen: Full text may be paywalled.

<a id="b058"></a>
**B058 · METHODENVORSCHLAG**

R08 definiert die zu messende Kette als Bruststück → Kopplung → MEMS-Mikrofon → ADC und empfiehlt einen Lautsprecher-/Shakerantrieb mit definiertem Koppler bzw. Kunstbrust.

**Ursprung:** [preThesis/03-recherche/R08-messmethode-akustik.md:22-34](../../preThesis/03-recherche/R08-messmethode-akustik.md#L22)
**Belege:** [Weiss, D 2019 · invitro_stethoscopes](https://pmc.ncbi.nlm.nih.gov/articles/PMC6339642/) — Seite prüfen; [Alanazi, A., Atcherson, S., Franklin, C., & Bryan, M 2020 · frequency_response_stethoscopes](https://doi.org/10.4103/sjmms.sjmms_118_19) — Seite prüfen; [Nussbaumer, M 2022 · nussbaumer_stethoscope_acoustics](https://www.repository.cam.ac.uk/items/feadd88b-9e03-44fb-a875-c49f7c550259) — Seite prüfen · 🔒 Volltextzugang prüfen: Publisher full text paywalled; Cambridge record is open.; [Nowak, L 2017 · nowak_stethoscope_method](https://pubmed.ncbi.nlm.nih.gov/28372089/) — Fundstelle: 141(3), article p. 1940 (record verified) (aus Stage 1; am Original prüfen) · 🔒 Volltextzugang prüfen: Full text may be paywalled.

<a id="b066"></a>
**B066 · METHODENVORSCHLAG**

R08 empfiehlt das Referenzmikrofon vor der Messreihe mit einem Schallpegelkalibrator bei 1 kHz und typischerweise 94 dB SPL oder 114 dB SPL zu kalibrieren.

**Ursprung:** [preThesis/03-recherche/R08-messmethode-akustik.md:218-236](../../preThesis/03-recherche/R08-messmethode-akustik.md#L218)
**Belege:** [IEC 61672-1:2013 · iec61672_1](https://webstore.ansi.org/standards/iec/iec61672ed2013) — Seite prüfen · 🔒 Volltext kostenpflichtig; [IEC 60268-5:2003+A1:2007 · iec60268_5](https://webstore.iec.ch/en/publication/1224) — Fundstelle: Scope/product page (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [Weiss, D 2019 · invitro_stethoscopes](https://pmc.ncbi.nlm.nih.gov/articles/PMC6339642/) — Seite prüfen

<a id="b069"></a>
**B069 · METHODENVORSCHLAG · ANNAHME**

R08 empfiehlt eine Rauschmessung ohne akustische Anregung über 30–60 s mit RMS im Band 20–1000 Hz und PSD-Auswertung.

**Ursprung:** [preThesis/03-recherche/R08-messmethode-akustik.md:278-313](../../preThesis/03-recherche/R08-messmethode-akustik.md#L278)
**Belege:** [Weiss, D 2019 · invitro_stethoscopes](https://pmc.ncbi.nlm.nih.gov/articles/PMC6339642/) — Seite prüfen; [Alanazi, A., Atcherson, S., Franklin, C., & Bryan, M 2020 · frequency_response_stethoscopes](https://doi.org/10.4103/sjmms.sjmms_118_19) — Seite prüfen; [Nussbaumer, M 2022 · nussbaumer_stethoscope_acoustics](https://www.repository.cam.ac.uk/items/feadd88b-9e03-44fb-a875-c49f7c550259) — Seite prüfen · 🔒 Volltextzugang prüfen: Publisher full text paywalled; Cambridge record is open.; [Nowak, L 2017 · nowak_stethoscope_method](https://pubmed.ncbi.nlm.nih.gov/28372089/) — Fundstelle: 141(3), article p. 1940 (record verified) (aus Stage 1; am Original prüfen) · 🔒 Volltextzugang prüfen: Full text may be paywalled.

<a id="b062"></a>
**B062 · METHODENVORSCHLAG**

R08 empfiehlt einen exponentiellen Swept-Sine (ESS) für den Frequenzgang; Deconvolution des inversen Sweeps ergibt Impulsantwort und Frequenzgang, während Verzerrungsanteile zeitlich separiert werden können.

**Ursprung:** [preThesis/03-recherche/R08-messmethode-akustik.md:136-168](../../preThesis/03-recherche/R08-messmethode-akustik.md#L136)
**Belege:** [Farina, A 2000 · farina_ess](https://aes.org/publications/elibrary-page/?id=10211) — Seite prüfen (übernommene Angabe: Abstract; paper page unverified) · 🔒 Volltext kostenpflichtig; [Ćirić, D 2013 · ciric_swept_sine](https://www.sciencedirect.com/science/article/abs/pii/S0003682X12002563) — Fundstelle: pp. 375–382 (metadata verified) (aus Stage 1; am Original prüfen) · 🔒 Volltextzugang prüfen: Full text may be paywalled.; [IEC 60268-5:2003+A1:2007 · iec60268_5](https://webstore.iec.ch/en/publication/1224) — Fundstelle: Scope/product page (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig

<a id="b061"></a>
**B061 · METHODENVORSCHLAG**

R08 empfiehlt Lautsprecher plus Koppler als Minimalaufbau; ein Shaker mit Kunstbrust ist mechanisch realistischer, aber komplexer und erfordert die Definition der mechanischen Eingangsgröße.

**Ursprung:** [preThesis/03-recherche/R08-messmethode-akustik.md:99-132](../../preThesis/03-recherche/R08-messmethode-akustik.md#L99)
**Belege:** [Weiss, D 2019 · invitro_stethoscopes](https://pmc.ncbi.nlm.nih.gov/articles/PMC6339642/) — Seite prüfen; [Alanazi, A., Atcherson, S., Franklin, C., & Bryan, M 2020 · frequency_response_stethoscopes](https://doi.org/10.4103/sjmms.sjmms_118_19) — Seite prüfen; [Nussbaumer, M 2022 · nussbaumer_stethoscope_acoustics](https://www.repository.cam.ac.uk/items/feadd88b-9e03-44fb-a875-c49f7c550259) — Seite prüfen · 🔒 Volltextzugang prüfen: Publisher full text paywalled; Cambridge record is open.; [Nowak, L 2017 · nowak_stethoscope_method](https://pubmed.ncbi.nlm.nih.gov/28372089/) — Fundstelle: 141(3), article p. 1940 (record verified) (aus Stage 1; am Original prüfen) · 🔒 Volltextzugang prüfen: Full text may be paywalled.

<a id="b064"></a>
**B064 · METHODENVORSCHLAG**

R08 empfiehlt Stepped Sine zur Prüfung einzelner Frequenzpunkte, Pegellinearität und THD mit mehreren Pegelstufen.

**Ursprung:** [preThesis/03-recherche/R08-messmethode-akustik.md:170-197](../../preThesis/03-recherche/R08-messmethode-akustik.md#L170)
**Belege:** [Farina, A 2000 · farina_ess](https://aes.org/publications/elibrary-page/?id=10211) — Seite prüfen (übernommene Angabe: Abstract; paper page unverified) · 🔒 Volltext kostenpflichtig; [Ćirić, D 2013 · ciric_swept_sine](https://www.sciencedirect.com/science/article/abs/pii/S0003682X12002563) — Fundstelle: pp. 375–382 (metadata verified) (aus Stage 1; am Original prüfen) · 🔒 Volltextzugang prüfen: Full text may be paywalled.; [IEC 60268-5:2003+A1:2007 · iec60268_5](https://webstore.iec.ch/en/publication/1224) — Fundstelle: Scope/product page (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig

<a id="b074"></a>
**B074 · METHODENVORSCHLAG**

R08 empfiehlt, Kopplergeometrie, Anpresskraft und Bruststückposition zu dokumentieren, Referenz- und Testkanäle synchron aufzuzeichnen und Wiederholungsmessungen für die Unsicherheit zu berichten.

**Ursprung:** [preThesis/03-recherche/R08-messmethode-akustik.md:378-419](../../preThesis/03-recherche/R08-messmethode-akustik.md#L378)
**Belege:** [Weiss, D 2019 · invitro_stethoscopes](https://pmc.ncbi.nlm.nih.gov/articles/PMC6339642/) — Seite prüfen; [Alanazi, A., Atcherson, S., Franklin, C., & Bryan, M 2020 · frequency_response_stethoscopes](https://doi.org/10.4103/sjmms.sjmms_118_19) — Seite prüfen; [Nussbaumer, M 2022 · nussbaumer_stethoscope_acoustics](https://www.repository.cam.ac.uk/items/feadd88b-9e03-44fb-a875-c49f7c550259) — Seite prüfen · 🔒 Volltextzugang prüfen: Publisher full text paywalled; Cambridge record is open.; [Nowak, L 2017 · nowak_stethoscope_method](https://pubmed.ncbi.nlm.nih.gov/28372089/) — Fundstelle: 141(3), article p. 1940 (record verified) (aus Stage 1; am Original prüfen) · 🔒 Volltextzugang prüfen: Full text may be paywalled.

<a id="b067"></a>
**B067 · METHODENVORSCHLAG**

R08 empfiehlt, Referenz- und Stethoskopsignal synchron aufzuzeichnen, damit Lautsprecher-/Verstärkerfrequenzgang und Pegelschwankungen über das gemessene Eingangssignal korrigiert werden.

**Ursprung:** [preThesis/03-recherche/R08-messmethode-akustik.md:238-262](../../preThesis/03-recherche/R08-messmethode-akustik.md#L238)
**Belege:** [Weiss, D 2019 · invitro_stethoscopes](https://pmc.ncbi.nlm.nih.gov/articles/PMC6339642/) — Seite prüfen; [Alanazi, A., Atcherson, S., Franklin, C., & Bryan, M 2020 · frequency_response_stethoscopes](https://doi.org/10.4103/sjmms.sjmms_118_19) — Seite prüfen; [Nussbaumer, M 2022 · nussbaumer_stethoscope_acoustics](https://www.repository.cam.ac.uk/items/feadd88b-9e03-44fb-a875-c49f7c550259) — Seite prüfen · 🔒 Volltextzugang prüfen: Publisher full text paywalled; Cambridge record is open.

<a id="b065"></a>
**B065 · METHODE / PRÜFVERFAHREN**

R08 nennt rosa Rauschen mit Terz-/Oktavbandanalyse für Plausibilitäts-, Pegel- und Rauschmessung; für präzisen Frequenzgang wird ESS oder Stepped Sine bevorzugt.

**Ursprung:** [preThesis/03-recherche/R08-messmethode-akustik.md:199-216](../../preThesis/03-recherche/R08-messmethode-akustik.md#L199)
**Belege:** [Farina, A 2000 · farina_ess](https://aes.org/publications/elibrary-page/?id=10211) — Seite prüfen (übernommene Angabe: Abstract; paper page unverified) · 🔒 Volltext kostenpflichtig; [Ćirić, D 2013 · ciric_swept_sine](https://www.sciencedirect.com/science/article/abs/pii/S0003682X12002563) — Fundstelle: pp. 375–382 (metadata verified) (aus Stage 1; am Original prüfen) · 🔒 Volltextzugang prüfen: Full text may be paywalled.; [IEC 60268-5:2003+A1:2007 · iec60268_5](https://webstore.iec.ch/en/publication/1224) — Fundstelle: Scope/product page (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig

<a id="b073"></a>
**B073 · RISIKO / EINORDNUNG**

R08 weist darauf hin, dass Ergebnisse mit Koppler-/Shakeraufbau keine direkte Aussage über Frequenzgang am menschlichen Brustkorb oder klinische Empfindlichkeit erlauben.

**Ursprung:** [preThesis/03-recherche/R08-messmethode-akustik.md:421-439](../../preThesis/03-recherche/R08-messmethode-akustik.md#L421)
**Belege:** [Weiss, D 2019 · invitro_stethoscopes](https://pmc.ncbi.nlm.nih.gov/articles/PMC6339642/) — Seite prüfen; [Alanazi, A., Atcherson, S., Franklin, C., & Bryan, M 2020 · frequency_response_stethoscopes](https://doi.org/10.4103/sjmms.sjmms_118_19) — Seite prüfen; [Nussbaumer, M 2022 · nussbaumer_stethoscope_acoustics](https://www.repository.cam.ac.uk/items/feadd88b-9e03-44fb-a875-c49f7c550259) — Seite prüfen · 🔒 Volltextzugang prüfen: Publisher full text paywalled; Cambridge record is open.; [Nowak, L 2017 · nowak_stethoscope_method](https://pubmed.ncbi.nlm.nih.gov/28372089/) — Fundstelle: 141(3), article p. 1940 (record verified) (aus Stage 1; am Original prüfen) · 🔒 Volltextzugang prüfen: Full text may be paywalled.

<a id="a032"></a>
**A032 · RISIKO / EINORDNUNG**

Simulatoraufnahmen ersetzen keine klinischen Patientendaten; ihre Übertragbarkeit auf reale Thoraxbedingungen muss laut R02 experimentell geprüft werden.

**Ursprung:** [preThesis/03-recherche/R02-ground-truth.md:22-31,154-169](../../preThesis/03-recherche/R02-ground-truth.md#L22)
**Belege:** [Oliveira, J 2022 · circor_paper](https://arxiv.org/abs/2108.00813) — Seite prüfen (übernommene Angabe: Abstract, arXiv text lines 3–6; journal pages unverified) · 🔒 Volltextzugang prüfen: IEEE version may be paywalled; arXiv preprint is open.; [Reyna, M 2022 · physionet_challenge_2022](https://physionet.org/content/challenge-2022/1.0.0/papers/) — Fundstelle: Data Variables, lines 92–97 (aus Stage 1; am Original prüfen); [Noponen, A.-L., Lukkarinen, S., & Sepponen, R · murmur_text](https://accesscardiology.mhmedical.com/content.aspx?bookid=382&sectionid=40663653) — Fundstelle: Chapter 2, Clinical Auscultation and Conventional Phonocardiography (web lines 144–150) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig
