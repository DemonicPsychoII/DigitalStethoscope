# Evaluation: Datensätze und Referenzen

[Zum Einstieg](../README.md) · [Offene Punkte](../offene-punkte.md)

Daten/Lizenzen → Labels → Auswahl → unabhängige BPM-Referenz.

**19 aktive Einheiten.** Schreibreihenfolge: Definition → Mechanismus → Werte → Folgerung. Die Aussagen sind Material, kein fertiger Fließtext.

**Achtung:** CirCor-Aufnahmenzahl 5.272/5.282 ist ungeklärt; [A021](#a021) sichtbar stehen lassen.

## Schreibbausteine

### Mechanismen und Zusammenhänge

<a id="a027"></a>
**A027 · LITERATURFAKT / REGEL**

CinC 2016 enthält laut R02 rund 3.126 Aufnahmen, resampelt auf 2 kHz und als WAV-Dateien.

**Ursprung:** [preThesis/03-recherche/R02-ground-truth.md:35-40,61-68](../../preThesis/03-recherche/R02-ground-truth.md#L35)
**Belege:** [Liu, C 2016 · physionet2016](https://physionet.org/challenge/2016/) — Seite prüfen; [Reyna, M 2022 · physionet_challenge_2022](https://physionet.org/content/challenge-2022/1.0.0/papers/) — Fundstelle: Data Variables, lines 92–97 (aus Stage 1; am Original prüfen); [Oliveira, J 2022 · circor_dataset](https://physionet.org/content/circor-heart-sound/1.0.3/) — Fundstelle: Data Description, lines 112–205; access/license lines 342–350 (aus Stage 1; am Original prüfen)

<a id="a028"></a>
**A028 · LITERATURFAKT / REGEL · ersetzt U045**

CinC 2016 enthält Normal/Abnormal/Unsure und S1/S2-/Systole-/Diastole-Segmentierung, aber keine standardisierten Murmur-Typen oder Murmurgrade.

**Ursprung:** [preThesis/03-recherche/R02-ground-truth.md:38,61-68](../../preThesis/03-recherche/R02-ground-truth.md#L38)
**Belege:** [Liu, C 2016 · physionet2016](https://physionet.org/challenge/2016/) — Seite prüfen; [Reyna, M 2022 · physionet_challenge_2022](https://physionet.org/content/challenge-2022/1.0.0/papers/) — Fundstelle: Data Variables, lines 92–97 (aus Stage 1; am Original prüfen); [Oliveira, J 2022 · circor_paper](https://arxiv.org/abs/2108.00813) — Seite prüfen (übernommene Angabe: Abstract, arXiv text lines 3–6; journal pages unverified) · 🔒 Volltextzugang prüfen: IEEE version may be paywalled; arXiv preprint is open.

<a id="a023"></a>
**A023 · LITERATURFAKT / REGEL**

CirCor enthält Murmurstatus Present/Absent/Unknown sowie Ort, am besten hörbare Lokalisation, Timing, Form, Tonhöhe, Qualität und Grad.

**Ursprung:** [preThesis/03-recherche/R02-ground-truth.md:35-57](../../preThesis/03-recherche/R02-ground-truth.md#L35)
**Belege:** [Oliveira, J 2022 · circor_dataset](https://physionet.org/content/circor-heart-sound/1.0.3/) — Fundstelle: Data Description, lines 112–205; access/license lines 342–350 (aus Stage 1; am Original prüfen); [Oliveira, J 2022 · circor_paper](https://arxiv.org/abs/2108.00813) — Seite prüfen (übernommene Angabe: Abstract, arXiv text lines 3–6; journal pages unverified) · 🔒 Volltextzugang prüfen: IEEE version may be paywalled; arXiv preprint is open.; [Reyna, M 2022 · physionet_challenge_2022](https://physionet.org/content/challenge-2022/1.0.0/papers/) — Fundstelle: Data Variables, lines 92–97 (aus Stage 1; am Original prüfen)

<a id="a025"></a>
**A025 · LITERATURFAKT / REGEL**

CirCor v1.0.3 steht laut R02 unter ODC-By 1.0; Attribution und Lizenzbedingungen sind einzuhalten.

**Ursprung:** [preThesis/03-recherche/R02-ground-truth.md:35-40,71-74](../../preThesis/03-recherche/R02-ground-truth.md#L35)
**Belege:** [Oliveira, J 2022 · circor_dataset](https://physionet.org/content/circor-heart-sound/1.0.3/) — Fundstelle: Data Description, lines 112–205; access/license lines 342–350 (aus Stage 1; am Original prüfen); [Oliveira, J 2022 · circor_paper](https://arxiv.org/abs/2108.00813) — Seite prüfen (übernommene Angabe: Abstract, arXiv text lines 3–6; journal pages unverified) · 🔒 Volltextzugang prüfen: IEEE version may be paywalled; arXiv preprint is open.; [Reyna, M 2022 · physionet_challenge_2022](https://physionet.org/content/challenge-2022/1.0.0/papers/) — Fundstelle: Data Variables, lines 92–97 (aus Stage 1; am Original prüfen)

<a id="a022"></a>
**A022 · LITERATURFAKT / REGEL**

CirCor wird als Datensatz bis Alter 21 Jahre mit typischer Abtastrate 4 kHz beschrieben; Header nennen die konkrete Rate pro Patient.

**Ursprung:** [preThesis/03-recherche/R02-ground-truth.md:35-40](../../preThesis/03-recherche/R02-ground-truth.md#L35)
**Belege:** [Oliveira, J 2022 · circor_dataset](https://physionet.org/content/circor-heart-sound/1.0.3/) — Fundstelle: Data Description, lines 112–205; access/license lines 342–350 (aus Stage 1; am Original prüfen); [Oliveira, J 2022 · circor_paper](https://arxiv.org/abs/2108.00813) — Seite prüfen (übernommene Angabe: Abstract, arXiv text lines 3–6; journal pages unverified) · 🔒 Volltextzugang prüfen: IEEE version may be paywalled; arXiv preprint is open.; [Reyna, M 2022 · physionet_challenge_2022](https://physionet.org/content/challenge-2022/1.0.0/papers/) — Fundstelle: Data Variables, lines 92–97 (aus Stage 1; am Original prüfen)

<a id="a024"></a>
**A024 · LITERATURFAKT / REGEL**

CirCor-TSV-Dateien enthalten Segmentierungen von S1, Systole, S2 und Diastole.

**Ursprung:** [preThesis/03-recherche/R02-ground-truth.md:42-59](../../preThesis/03-recherche/R02-ground-truth.md#L42)
**Belege:** [Oliveira, J 2022 · circor_dataset](https://physionet.org/content/circor-heart-sound/1.0.3/) — Fundstelle: Data Description, lines 112–205; access/license lines 342–350 (aus Stage 1; am Original prüfen); [Oliveira, J 2022 · circor_paper](https://arxiv.org/abs/2108.00813) — Seite prüfen (übernommene Angabe: Abstract, arXiv text lines 3–6; journal pages unverified) · 🔒 Volltextzugang prüfen: IEEE version may be paywalled; arXiv preprint is open.; [Reyna, M 2022 · physionet_challenge_2022](https://physionet.org/content/challenge-2022/1.0.0/papers/) — Fundstelle: Data Variables, lines 92–97 (aus Stage 1; am Original prüfen)

<a id="a026"></a>
**A026 · LITERATURFAKT / REGEL**

R02 beschreibt systolische CirCor-Murmurgrade I/VI, II/VI und III/VI; höhere Grade sind nicht weiter getrennt.

**Ursprung:** [preThesis/03-recherche/R02-ground-truth.md:46-55](../../preThesis/03-recherche/R02-ground-truth.md#L46)
**Belege:** [Oliveira, J 2022 · circor_dataset](https://physionet.org/content/circor-heart-sound/1.0.3/) — Fundstelle: Data Description, lines 112–205; access/license lines 342–350 (aus Stage 1; am Original prüfen); [Oliveira, J 2022 · circor_paper](https://arxiv.org/abs/2108.00813) — Seite prüfen (übernommene Angabe: Abstract, arXiv text lines 3–6; journal pages unverified) · 🔒 Volltextzugang prüfen: IEEE version may be paywalled; arXiv preprint is open.; [Reyna, M 2022 · physionet_challenge_2022](https://physionet.org/content/challenge-2022/1.0.0/papers/) — Fundstelle: Data Variables, lines 92–97 (aus Stage 1; am Original prüfen)

<a id="a044"></a>
**A044 · LITERATURFAKT / REGEL**

S1/S2- oder Normal/Abnormal-Labels liefern nicht automatisch BPM-Ground-Truth; dafür sind EKG oder verlässliche Beat-Zeitpunkte nötig.

**Ursprung:** [preThesis/03-recherche/R03-bpm-referenz.md:38-44](../../preThesis/03-recherche/R03-bpm-referenz.md#L38)
**Belege:** [Oliveira, J 2022 · circor_dataset](https://physionet.org/content/circor-heart-sound/1.0.3/) — Fundstelle: Data Description, lines 112–205; access/license lines 342–350 (aus Stage 1; am Original prüfen); [Reyna, M 2022 · physionet_challenge_2022](https://physionet.org/content/challenge-2022/1.0.0/papers/) — Fundstelle: Data Variables, lines 92–97 (aus Stage 1; am Original prüfen); [Bland, J 1986 · bland_altman](https://doi.org/10.1016/S0140-6736(86)90837-8) — Fundstelle: Abstract and bibliographic metadata; full text paywalled (aus Stage 1; am Original prüfen) · 🔒 Volltextzugang prüfen: Publisher full text may be paywalled.

### Folgerungen, Entwurfsentscheidungen und Grenzen

<a id="u017"></a>
**U017 · EIGENE ENTSCHEIDUNG / ENTWURFSEMPFEHLUNG · ANNAHME**

Als öffentliche Ground Truth ist CirCor DigiScope mit ODC-By 1.0 und Playback voraufgenommener Sounds vorgeschlagen; die genaue Datensatzwahl ist als „und/oder“ formuliert.

**Ursprung:** [preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md:38](../../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md#L38)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="a043"></a>
**A043 · RISIKO / EINORDNUNG**

Ein zweiter PCG-Kanal misst ein ähnliches physikalisches Signal und ist laut R03 kein unabhängiger Goldstandard.

**Ursprung:** [preThesis/03-recherche/R03-bpm-referenz.md:37-39](../../preThesis/03-recherche/R03-bpm-referenz.md#L37)
**Belege:** [Noponen, A.-L., Lukkarinen, S., & Sepponen, R · murmur_text](https://accesscardiology.mhmedical.com/content.aspx?bookid=382&sectionid=40663653) — Fundstelle: Chapter 2, Clinical Auscultation and Conventional Phonocardiography (web lines 144–150) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [Bland, J 1986 · bland_altman](https://doi.org/10.1016/S0140-6736(86)90837-8) — Fundstelle: Abstract and bibliographic metadata; full text paywalled (aus Stage 1; am Original prüfen) · 🔒 Volltextzugang prüfen: Publisher full text may be paywalled.; [Delgado-Trejos, E., Quiceno-Manrique, A 2009 · digital_auscultation_murmur](https://link.springer.com/article/10.1007/s10439-008-9611-z) — Fundstelle: Introduction, murmur and heart cycle description (existing registry reports web lines 71–85) (aus Stage 1; am Original prüfen)

<a id="u122"></a>
**U122 · METHODE / PRÜFVERFAHREN**

EVAL-GUIDE says synthetic pulses alone cannot establish physiological accuracy and recommends licensed heart-sound recordings with synchronized reference annotations; digital injection isolates software while controlled acoustic playback exercises the assembled capture chain.

**Ursprung:** [Development/system/coding/bringup-zephyr/EVAL-GUIDE.md:45-50](https://github.com/DemonicPsychoII/DigitalStethoscope/blob/1448340d265326e11b7a416960f35e0d2390cd6d/Development/system/coding/bringup-zephyr/EVAL-GUIDE.md?plain=1#L45) (**Herkunft verschoben:** als Vorstudienmaterial nach preThesis/06-bringup-zephyr verschoben. Die Zeilenangaben beziehen sich auf die zitierte historische Fassung. Aktuell: [EVAL-GUIDE.md](../../preThesis/06-bringup-zephyr/EVAL-GUIDE.md))
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="a030"></a>
**A030 · METHODENVORSCHLAG · ANNAHME**

Für CirCor schlägt R02 Present/Absent als Hauptgruppen und Unknown separat oder ausgeschlossen vor.

**Ursprung:** [preThesis/03-recherche/R02-ground-truth.md:104-118](../../preThesis/03-recherche/R02-ground-truth.md#L104)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="a042"></a>
**A042 · RISIKO / EINORDNUNG**

Manuelle Auskultation ist laut R03 nur sekundäre Plausibilitätsreferenz, weil zeitliche Zählfehler möglich sind.

**Ursprung:** [preThesis/03-recherche/R03-bpm-referenz.md:34-38](../../preThesis/03-recherche/R03-bpm-referenz.md#L34)
**Belege:** [Noponen, A.-L., Lukkarinen, S., & Sepponen, R · murmur_text](https://accesscardiology.mhmedical.com/content.aspx?bookid=382&sectionid=40663653) — Fundstelle: Chapter 2, Clinical Auscultation and Conventional Phonocardiography (web lines 144–150) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [Bland, J 1986 · bland_altman](https://doi.org/10.1016/S0140-6736(86)90837-8) — Fundstelle: Abstract and bibliographic metadata; full text paywalled (aus Stage 1; am Original prüfen) · 🔒 Volltextzugang prüfen: Publisher full text may be paywalled.; [Delgado-Trejos, E., Quiceno-Manrique, A 2009 · digital_auscultation_murmur](https://link.springer.com/article/10.1007/s10439-008-9611-z) — Fundstelle: Introduction, murmur and heart cycle description (existing registry reports web lines 71–85) (aus Stage 1; am Original prüfen)

<a id="a029"></a>
**A029 · EIGENE ENTSCHEIDUNG / ENTWURFSEMPFEHLUNG**

R02 bewertet CirCor als am besten geeignete öffentliche Murmur-Ground-Truth-Quelle und CinC 2016 als nur eingeschränkt passend.

**Ursprung:** [preThesis/03-recherche/R02-ground-truth.md:22-40,104-118](../../preThesis/03-recherche/R02-ground-truth.md#L22)
**Belege:** [Oliveira, J 2022 · circor_dataset](https://physionet.org/content/circor-heart-sound/1.0.3/) — Fundstelle: Data Description, lines 112–205; access/license lines 342–350 (aus Stage 1; am Original prüfen); [Oliveira, J 2022 · circor_paper](https://arxiv.org/abs/2108.00813) — Seite prüfen (übernommene Angabe: Abstract, arXiv text lines 3–6; journal pages unverified) · 🔒 Volltextzugang prüfen: IEEE version may be paywalled; arXiv preprint is open.; [Reyna, M 2022 · physionet_challenge_2022](https://physionet.org/content/challenge-2022/1.0.0/papers/) — Fundstelle: Data Variables, lines 92–97 (aus Stage 1; am Original prüfen)

<a id="a031"></a>
**A031 · METHODENVORSCHLAG**

R02 empfiehlt patientenweise statt aufnahmeweise in Trainings-/Testdaten zu teilen, damit dieselbe Person nicht in beiden Gruppen liegt.

**Ursprung:** [preThesis/03-recherche/R02-ground-truth.md:110-118](../../preThesis/03-recherche/R02-ground-truth.md#L110)
**Belege:** [Oliveira, J 2022 · circor_dataset](https://physionet.org/content/circor-heart-sound/1.0.3/) — Fundstelle: Data Description, lines 112–205; access/license lines 342–350 (aus Stage 1; am Original prüfen); [Oliveira, J 2022 · circor_paper](https://arxiv.org/abs/2108.00813) — Seite prüfen (übernommene Angabe: Abstract, arXiv text lines 3–6; journal pages unverified) · 🔒 Volltextzugang prüfen: IEEE version may be paywalled; arXiv preprint is open.; [Reyna, M 2022 · physionet_challenge_2022](https://physionet.org/content/challenge-2022/1.0.0/papers/) — Fundstelle: Data Variables, lines 92–97 (aus Stage 1; am Original prüfen)

<a id="a021"></a>
**A021 · WIDERSPRUCH · WIDERSPRUCH · QUELLENSET UNVOLLSTÄNDIG · ersetzt U044**

R02 gibt 5.272 CirCor-Aufnahmen an, während die zitierte Originalpublikation 5.282 nennt; die Aufnahmenzahl ist daher in der Recherche widersprüchlich und vor Thesis-Verwendung anhand der Version 1.0.3 zu klären.

**Ursprung:** [preThesis/03-recherche/R02-ground-truth.md:35-57](../../preThesis/03-recherche/R02-ground-truth.md#L35)
**Belege:** [Oliveira, J 2022 · circor_dataset](https://physionet.org/content/circor-heart-sound/1.0.3/) — Fundstelle: Data Description, lines 112–205; access/license lines 342–350 (aus Stage 1; am Original prüfen); [Oliveira, J 2022 · circor_paper](https://arxiv.org/abs/2108.00813) — Seite prüfen (übernommene Angabe: Abstract, arXiv text lines 3–6; journal pages unverified) · 🔒 Volltextzugang prüfen: IEEE version may be paywalled; arXiv preprint is open.; [Reyna, M 2022 · physionet_challenge_2022](https://physionet.org/content/challenge-2022/1.0.0/papers/) — Fundstelle: Data Variables, lines 92–97 (aus Stage 1; am Original prüfen)
**Vor Verwendung klären:** [Widersprüche](../offene-punkte.md#widersprueche).

<a id="a040"></a>
**A040 · METHODENVORSCHLAG · ersetzt U047**

R03 empfiehlt synchron aufgezeichnetes EKG als primäre BPM-Referenz; Herzfrequenz wird aus R-Zacken bzw. R-R-Intervallen abgeleitet.

> **Überholt (Stand integration, 2026-10-22):** Synchron aufgezeichnetes EKG als primäre BPM-Referenz ist nicht der Abnahmeweg des Projekts; die R03-Empfehlung bleibt Recherchekontext. Aktuell: Abnahme gegen gleichzeitig gemessenes Pulsoximeter oder Smartwatch, innerhalb ±5 BPM oder ±10 % (14.10., REQ-06). Anforderungen gelten nur, wenn Nico sie mit verfügbarer Ausrüstung am Gerät prüfen kann. – siehe [MVP-Entscheidungen 14.10.](../../Development/system/planning/mvp-decisions-2026-10-14.md#behavior), [Systemanforderungen](../../Development/system/requirements/system-requirements.md#system-requirements-mvp).

**Ursprung:** [preThesis/03-recherche/R03-bpm-referenz.md:30-60](../../preThesis/03-recherche/R03-bpm-referenz.md#L30)
**Belege:** [ANSI/AAMI EC13:2002 · ec13](https://webstore.ansi.org/standards/aami/ansiaamiec132002) — Fundstelle: Clause 4.2.7 (accessible copy; official publication status not verified) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [IEC 60601-2-27:2011 · iec60601](https://webstore.iec.ch/en/publication/2638) — Fundstelle: Scope / standard description; accuracy clause not inspected (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [Bland, J 1986 · bland_altman](https://doi.org/10.1016/S0140-6736(86)90837-8) — Fundstelle: Abstract and bibliographic metadata; full text paywalled (aus Stage 1; am Original prüfen) · 🔒 Volltextzugang prüfen: Publisher full text may be paywalled.

<a id="a045"></a>
**A045 · METHODENVORSCHLAG · ANNAHME**

R03 schlägt synchrone PCG-/EKG-Aufnahme, R-Zacken-Detektion mit visueller Stichprobenkontrolle und identische Auswertefenster vor.

> **Überholt (Stand integration, 2026-10-22):** Synchrone PCG-/EKG-Aufnahme mit R-Zacken-Detektion ist nicht der Abnahmeweg des Projekts. Aktuell: Abnahme gegen gleichzeitig gemessenes Pulsoximeter oder Smartwatch (REQ-06). Aufnahmen und Referenz für Host-Tests werden in der WLAN/FHIR-Phase entschieden (P06, P17). – siehe [MVP-Entscheidungen 14.10.](../../Development/system/planning/mvp-decisions-2026-10-14.md#behavior), [Designparameter P06/P17](../../Development/system/design/system/parameters.md#design-parameters-internal).

**Ursprung:** [preThesis/03-recherche/R03-bpm-referenz.md:45-60](../../preThesis/03-recherche/R03-bpm-referenz.md#L45)
**Belege:** [Bland, J 1986 · bland_altman](https://doi.org/10.1016/S0140-6736(86)90837-8) — Fundstelle: Abstract and bibliographic metadata; full text paywalled (aus Stage 1; am Original prüfen) · 🔒 Volltextzugang prüfen: Publisher full text may be paywalled.; [Giavarina, D 2015 · bland_review](https://pmc.ncbi.nlm.nih.gov/articles/PMC4470095/) — Seite prüfen (übernommene Angabe: Methods overview; section/page unverified); [ANSI/AAMI EC13:2002 · ec13](https://webstore.ansi.org/standards/aami/ansiaamiec132002) — Fundstelle: Clause 4.2.7 (accessible copy; official publication status not verified) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig

<a id="a041"></a>
**A041 · METHODE / PRÜFVERFAHREN**

Simulierte EKG-Pulse eignen sich laut R03 für technische Funktions- und Grenzbereichstests, nicht als klinischer Patiententest.

**Ursprung:** [preThesis/03-recherche/R03-bpm-referenz.md:32-39](../../preThesis/03-recherche/R03-bpm-referenz.md#L32)
**Belege:** [ANSI/AAMI EC13:2002 · ec13](https://webstore.ansi.org/standards/aami/ansiaamiec132002) — Fundstelle: Clause 4.2.7 (accessible copy; official publication status not verified) (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [IEC 60601-2-27:2011 · iec60601](https://webstore.iec.ch/en/publication/2638) — Fundstelle: Scope / standard description; accuracy clause not inspected (aus Stage 1; am Original prüfen) · 🔒 Volltext kostenpflichtig; [Reyna, M 2022 · physionet_challenge_2022](https://physionet.org/content/challenge-2022/1.0.0/papers/) — Fundstelle: Data Variables, lines 92–97 (aus Stage 1; am Original prüfen)
