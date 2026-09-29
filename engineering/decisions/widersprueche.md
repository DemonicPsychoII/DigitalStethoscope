# Widersprüche zwischen den Projektdokumenten

> Stand: 2026-08-15. Sammelstelle für Aussagen, die sich zwischen den Dokumenten
> widersprechen und noch aufgelöst werden müssen. Kein Entscheidungsdokument —
> Entscheidungen gehören nach [open-questions.md](open-questions.md) bzw. in die
> Aufgabenbeschreibung.

## W1 — Q1 / akustische Kette vs. AP 2.2 (offen)

**Betroffen:** [Aufgabenbeschreibung.md](../../thesis/brief/Aufgabenbeschreibung.md),
[Aufgabenbeschreibung-Abgabe.md](../../thesis/brief/Aufgabenbeschreibung-Abgabe.md),
[Aufgabenbeschreibung-Intern.md](../../thesis/brief/Aufgabenbeschreibung-Intern.md),
[R08-messmethode-akustik.md](../../research/investigations/R08-messmethode-akustik.md)

Die interne Fassung legt fest:

> „Keine formale Ketten-Charakterisierung mit Kalibrieraufbau. Kriterium: Ton
> hörbar, Herz-Sounds hörbar → ausreichend."

Gleichzeitig steht in **allen drei** Aufgabenbeschreibungen unverändert:

- **Q1** als Fragestellung („Dämpft die Kopplung … die S3/S4-/Murmur-Bande …?"),
- Bewertungsgrundlage **(a)** „Charakterisierung der akustischen Kette (Q1)",
- **AP 2.2** „Charakterisierung der akustischen Kette (Q1) und daraus
  abgeleiteter Filterentwurf · 0,5 PW" (intern zusätzlich als Risiko-AP markiert).

Verschärfend: Die Signale der Bewertung sind **voraufgenommene Playback-Sounds**,
die die reale Bruststück-Kopplung gar nicht durchlaufen — genau die Kopplung, um
die es in Q1 geht.

**Auflösung nötig — eine von drei Varianten:**

1. Q1 + (a) + AP 2.2 auf ein qualitatives Kriterium herunterziehen (passend zur
   internen Entscheidung), oder
2. Q1 streichen und die 0,5 PW aus AP 2.2 umverteilen, oder
3. die Messmethode aus R08 doch durchführen (Minimalvariante: Koppler +
   Referenzmikrofon + ESS-Sweep) und die interne Entscheidung revidieren.

→ **Mit Betreuer abzustimmen, bevor die Aufgabenbeschreibung eingereicht wird.**

## W2 — Nummerierung der beiden SP3T-Schalter (unkritisch)

**Betroffen:** [Aufgabenbeschreibung-Intern.md](../../thesis/brief/Aufgabenbeschreibung-Intern.md),
[open-questions.md](open-questions.md), [hardware.md](../../hardware/assembly/hardware.md)

- Intern / open-questions: Schalter 1 = Wiedergabegeschwindigkeit, Schalter 2 = Filter
- hardware.md: Wahlschalter 1 = Filter, Wahlschalter 2 = Wiedergabegeschwindigkeit

Beide SP3T sind **dasselbe Bauteil**, die Zuordnung ist damit frei und erst bei
der Verdrahtung festzulegen. Die Bring-up-Firmware testet bewusst nur **einen**
Schalter, weil der zweite identisch ist. Vor dem finalen Aufbau die Zuordnung an
einer Stelle verbindlich festschreiben und die andere Stelle nachziehen.
