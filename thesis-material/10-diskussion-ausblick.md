# Diskussion und Ausblick

[Zum Einstieg](README.md) · [Offene Punkte](offene-punkte.md)

Widersprüche und Einschränkungen → Übertragbarkeit → begründete nächste Schritte.

**8 aktive Einheiten.** Schreibreihenfolge: Definition → Mechanismus → Werte → Folgerung. Die Aussagen sind Material, kein fertiger Fließtext.

## Schreibbausteine

### Mechanismen und Zusammenhänge

<a id="u100"></a>
**U100 · PROJEKTDOKUMENTATION**

widersprueche.md Stand 2026-08-15; offene Punkte zuletzt als Recherche-Stand 2026-08-11 ausgewiesen; die Arbeitskopie enthält spätere Updates (u. a. 2026-09-16/10-02) in Hardware-/README-Material.

**Ursprung:** [preThesis/02-entscheidungen/widersprueche.md:1-4](../preThesis/02-entscheidungen/widersprueche.md#L1); [preThesis/02-entscheidungen/open-questions.md:7-11](../preThesis/02-entscheidungen/open-questions.md#L7); [preThesis/05-hardware/hardware.md:32-34](../preThesis/05-hardware/hardware.md#L32); [Development/system/coding/bringup-zephyr/README.md:1-160](https://github.com/DemonicPsychoII/DigitalStethoscope/blob/23c1ea492270b897532896179e35f873eee823be/Development/system/coding/bringup-zephyr/README.md?plain=1#L1) (**Herkunft verschoben:** seit b2c3dde zu einem kurzen Einstiegs-README verdichtet; die Zeilenangaben gelten nur für die zitierte Fassung. Link zeigt diese historische Fassung. Aktuell: [Bring-up-README](../Development/system/coding/bringup-zephyr/README.md))
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

### Folgerungen, Entwurfsentscheidungen und Grenzen

<a id="b079"></a>
**B079 · WIDERSPRUCH · WIDERSPRUCH · QUELLENSET UNVOLLSTÄNDIG · ersetzt U061**

Die R07-Angabe von 30 Hz LFRO für SPH18R1LM4H-1 weicht von der Knowles/SELTECH-Portfolioangabe 35 Hz ab; Modellrevision und Quelle müssen vor einer Bauteilvergleichstabelle geklärt werden.

**Ursprung:** [preThesis/03-recherche/R07-bruststueck-mems.md:183-202](../preThesis/03-recherche/R07-bruststueck-mems.md#L183)
**Belege:** [Seltech · knowles_portfolio_2023](https://cdn.thomasnet.com/ccp/30973684/351950.pdf) — Fundstelle: Digital portfolio table, PDF p. 13 (aus Stage 1; am Original prüfen)
**Vor Verwendung klären:** [Widersprüche](offene-punkte.md#widersprueche).

<a id="a079"></a>
**A079 · VERWORFENE ALTERNATIVE · ANNAHME**

R04 nennt 0,75×-Resampling mit Tonhöhenänderung als robuste Minimalfunktion, die als nicht frequenztreu zu kennzeichnen wäre.

**Ursprung:** [preThesis/03-recherche/R04-time-stretch.md:308-324](../preThesis/03-recherche/R04-time-stretch.md#L308)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="a078"></a>
**A078 · VERWORFENE ALTERNATIVE · ANNAHME**

R04 nennt Offline-Time-Stretching oder Verarbeitung auf PC/Smartphone als Alternativen, falls On-device-Verarbeitung Qualitäts- oder Zeitziele verfehlt.

**Ursprung:** [preThesis/03-recherche/R04-time-stretch.md:308-324](../preThesis/03-recherche/R04-time-stretch.md#L308)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="b075"></a>
**B075 · WIDERSPRUCH · WIDERSPRUCH**

R07 behandelt die Kavität näherungsweise als Helmholtz-Resonator; Nussbaumer und Agarwal modellieren dagegen das Bruststück, den Brustkorb und die haltende Hand als gekoppeltes System und führen die maßgebliche Resonanz nicht auf eine isolierte kleine Luftmasse im Hals nach Helmholtz zurück. Die 21-ml-Schätzung ist daher nicht ohne Weiteres auf die reale Stethoskopkopplung übertragbar.

**Ursprung:** [preThesis/03-recherche/R07-bruststueck-mems.md:107-136](../preThesis/03-recherche/R07-bruststueck-mems.md#L107); [preThesis/03-recherche/R08-messmethode-akustik.md:84-97](../preThesis/03-recherche/R08-messmethode-akustik.md#L84)
**Belege:** [Nussbaumer, M 2022 · nussbaumer_stethoscope_acoustics](https://www.repository.cam.ac.uk/items/feadd88b-9e03-44fb-a875-c49f7c550259) — Seite prüfen · 🔒 Volltextzugang prüfen: Publisher full text paywalled; Cambridge record is open.; [Alanazi, A., Atcherson, S., Franklin, C., & Bryan, M 2020 · frequency_response_stethoscopes](https://doi.org/10.4103/sjmms.sjmms_118_19) — Seite prüfen; [Weiss, D 2019 · invitro_stethoscopes](https://pmc.ncbi.nlm.nih.gov/articles/PMC6339642/) — Seite prüfen
**Vor Verwendung klären:** [Widersprüche](offene-punkte.md#widersprueche).

<a id="u120"></a>
**U120 · RISIKO / EINORDNUNG**

README distinguishes wiring confirmation dated 2026-09-16 from later speed-switch and SD-card mapping; Rev A speed switch GPIO2/39/47 is in default build but not covered by that wiring confirmation.

**Ursprung:** [Development/system/coding/bringup-zephyr/README.md:3-8,64-83](https://github.com/DemonicPsychoII/DigitalStethoscope/blob/23c1ea492270b897532896179e35f873eee823be/Development/system/coding/bringup-zephyr/README.md?plain=1#L3) (**Herkunft verschoben:** seit b2c3dde zu einem kurzen Einstiegs-README verdichtet; die Zeilenangaben gelten nur für die zitierte Fassung. Link zeigt diese historische Fassung. Aktuell: [Bring-up-README](../Development/system/coding/bringup-zephyr/README.md))
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u038"></a>
**U038 · OFFENE FRAGE · OFFEN**

W1 ist noch offen; dokumentierte Optionen sind Q1/AP 2.2 qualitativ umformulieren, Q1 streichen/Arbeitszeit umverteilen oder R08-Minimalmessung ausführen; Abstimmung mit Betreuer steht aus.

> **Neuerer Stand (Stand integration, 2026-10-22):** Von den drei W1-Optionen gilt die Herausnahme der Kettenmessung (S05); D09 ist seit 14.10. geschlossen. Aktuell: keine Kettenmessung; Q1/AP 2.2 qualitativ behandeln. Ob die Abstimmung mit dem Betreuer erfolgt ist, nennt D09 nicht, siehe offene Punkte. – siehe [Entscheidungsregister D09](../Development/system/planning/implementation-readiness.md#decision-register), [Produktumfang](../Development/system/spec/product-scope.md#goal-and-boundary).

**Ursprung:** [preThesis/02-entscheidungen/widersprueche.md:23-32](../preThesis/02-entscheidungen/widersprueche.md#L23)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.

<a id="u037"></a>
**U037 · WIDERSPRUCH · WIDERSPRUCH**

W1: Aufgabenbeschreibungen führen Q1, Kettencharakterisierung und AP 2.2 auf, die interne Entscheidung verwirft gleichzeitig die formale Messung; die vorgesehenen Playback-Signale durchlaufen die reale Bruststückkopplung nicht.

> **Neuerer Stand (Stand integration, 2026-10-22):** Der Entwurf folgt der Abgabefassung (S05): Komponenteneignung über Datenblätter/Literatur und funktionaler Audiotest, keine gemessene Aussage zur Übertragungskette. D09 ist seit 14.10. geschlossen. Aktuell: keine Messung der akustischen Übertragungskette; laut 11.10. ist keine Messausrüstung/kein zweites Mikrofon verfügbar, laut 14.10. auch kein Zweikanal-Aufnahmeaufbau. – siehe [Entscheidungsregister D09](../Development/system/planning/implementation-readiness.md#decision-register), [MVP-Entscheidungen 14.10. (Umfang)](../Development/system/planning/mvp-decisions-2026-10-14.md#scope), [Produktumfang](../Development/system/spec/product-scope.md#goal-and-boundary).

**Ursprung:** [preThesis/02-entscheidungen/widersprueche.md:5-21](../preThesis/02-entscheidungen/widersprueche.md#L5)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.
**Vor Verwendung klären:** [Widersprüche](offene-punkte.md#widersprueche).
