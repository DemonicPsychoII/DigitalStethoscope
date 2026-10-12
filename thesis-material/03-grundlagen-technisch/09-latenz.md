# Latenz und Echtzeit

[Zum Einstieg](../README.md) · [Offene Punkte](../offene-punkte.md)

End-to-End-Begriff → kontextabhängige Wahrnehmung → vorläufige Entwicklungsziele.

**3 aktive Einheiten.** Schreibreihenfolge: Definition → Mechanismus → Werte → Folgerung. Die Aussagen sind Material, kein fertiger Fließtext.

**Schreibhinweis:** Literaturgrundlagen erklären das Verfahren. Zielwerte, Architekturentscheidungen und Berichtsempfehlungen als solche benennen und später in Anforderungen/Methodik begründen.

## Schreibbausteine

### Werte und dokumentierte Befunde

<a id="c006"></a>
**C006 · LITERATUR- / HERSTELLERWERT · ANNAHME · QUELLENSET UNVOLLSTÄNDIG**

Der Bericht nennt pro A/D- und D/A-Wandlung typischerweise rund 1–1,5 ms; die verwendete Quelle ist ein nichtakademischer Technik-Blog und die Angabe ist nicht unabhängig abgesichert.

**Ursprung:** [preThesis/03-recherche/R09-latenz.md:33](../../preThesis/03-recherche/R09-latenz.md#L33)
**Belege:** [Wang, Y 2018 · wang_low_latency_thesis](https://qmro.qmul.ac.uk/xmlui/bitstream/handle/123456789/44697/WANG_Yonghao_Final_PhD_070918.pdf?sequence=1) — Seite prüfen

<a id="c001"></a>
**C001 · EIGENER ZIELWERT / VORLÄUFIGER VORSCHLAG · ANNAHME · ersetzt U064**

Für das geplante digitale Stethoskop wird als Literatur-basiertes Entwicklungsziel eine End-to-End-Latenz ≤10 ms empfohlen; ≤5 ms wird als bevorzugtes Ziel genannt.

> **Überholt (Stand integration, 2026-10-12):** ≤10 ms bzw. ≤5 ms End-to-End sind nicht mehr das Projektziel; die R09-Aussage einer universellen 10–15-ms-Grenze ist laut neuerer Literaturprüfung nur eingeschränkt belastbar. Aktuell: Vorschlag (nicht freigegeben): Live-Hören <30 ms als Basisziel, <10 ms als Stretch-Ziel, stabile Verzögerung; Messung mit gemeinsamem Takt inklusive Mikrofon, Puffern, DSP, DAC und Verstärker. – siehe [Latenzbudgets 11.10.](../../Development/system/planning/mvp-decisions-2026-10-11.md#latency-research-and-proposed-budgets).

**Ursprung:** [preThesis/03-recherche/R09-latenz.md:22,35](../../preThesis/03-recherche/R09-latenz.md#L22)
**Belege:** [Lester, M 2007 · aes_lester_boley_2007](https://secure.aes.org/forum/pubs/conventions/?elib=14256) — Fundstelle: Abstract; AES Convention 123, Paper 7198 (aus Stage 1; am Original prüfen) · **LINK DEFEKT** · 🔒 Volltextzugang prüfen: unverified; [Wang, Y 2018 · wang_low_latency_thesis](https://qmro.qmul.ac.uk/xmlui/bitstream/handle/123456789/44697/WANG_Yonghao_Final_PhD_070918.pdf?sequence=1) — Seite prüfen; [The influence of rhythm on detection of auditory and 2020 · rhythm_audio_vibrotactile_2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7181424/) — Seite prüfen (übernommene Angabe: Abstract; exact page unverified)

### Folgerungen, Entwurfsentscheidungen und Grenzen

<a id="c007"></a>
**C007 · METHODE / PRÜFVERFAHREN**

R09 fordert, „Echtzeit“ für die Live-Auskultation über eine messbare End-to-End-Latenz zu operationalisieren.

**Ursprung:** [preThesis/03-recherche/R09-latenz.md:10-17](../../preThesis/03-recherche/R09-latenz.md#L10)
**Belege:** Keine externen Belege im Inventar; Projektursprung verwenden.
