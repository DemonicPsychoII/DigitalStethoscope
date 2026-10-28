# I²S und digitaler Audiopfad

[Zum Einstieg](../README.md) · [Offene Punkte](../offene-punkte.md)

Digitale Audioübertragung → PDM/PCM → DMA → externe Ausgabe.

**5 aktive Einheiten.** Schreibreihenfolge: Definition → Mechanismus → Werte → Folgerung. Die Aussagen sind Material, kein fertiger Fließtext.

**Schreibhinweis:** Literaturgrundlagen erklären das Verfahren. Zielwerte, Architekturentscheidungen und Berichtsempfehlungen als solche benennen und später in Anforderungen/Methodik begründen.

## Schreibbausteine

### Mechanismen und Zusammenhänge

<a id="c009"></a>
**C009 · LITERATURFAKT / REGEL · QUELLENSET UNVOLLSTÄNDIG**

Beim ESP32-S3 unterstützt ESP-IDF I²S Standard- und TDM-Modi auf I²S0/I²S1; PDM-RX/TX ist auf I²S0/I²S1 ausgewiesen.

**Ursprung:** [preThesis/03-recherche/R10-esp32-plattform.md:85](../../preThesis/03-recherche/R10-esp32-plattform.md#L85)
**Korrektur Stage 2 (2026-10-24):** Die ESP-DSP-API belegt keine I²S-Controller- oder PDM-Konvertierungsmodi. Das Quellenset bleibt unvollständig; die passende ESP-IDF-I²S-Referenz ist noch zu prüfen. Quelle: [_build/stage2-corrections.json](../_build/stage2-corrections.json).
**Belege:** [Espressif Systems · esp_i2s_s3](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/i2s.html) — Fundstelle: Overview of All Modes (aus Stage 1; am Original prüfen); [Espressif Systems · esp_s3_datasheet](https://documentation.espressif.com/esp32-s3_datasheet_en.pdf) — Seite prüfen

<a id="c008"></a>
**C008 · LITERATURFAKT / REGEL · QUELLENSET UNVOLLSTÄNDIG**

Der ESP32-S3 stellt zwei I²S-Peripherieeinheiten bereit, die Sampledaten ein- und ausgeben können; jeder Controller besitzt RX- und TX-Kanäle sowie DMA-Transport.

**Ursprung:** [preThesis/03-recherche/R10-esp32-plattform.md:85-92](../../preThesis/03-recherche/R10-esp32-plattform.md#L85)
**Korrektur Stage 2 (2026-10-24):** Die ESP-DSP-API belegt keine I²S-Controller- oder PDM-Konvertierungsmodi. Das Quellenset bleibt unvollständig; die passende ESP-IDF-I²S-Referenz ist noch zu prüfen. Quelle: [_build/stage2-corrections.json](../_build/stage2-corrections.json).
**Belege:** [Espressif Systems · esp_i2s_s3](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/i2s.html) — Fundstelle: Introduction; Overview of All Modes (aus Stage 1; am Original prüfen); [Espressif Systems · esp_s3_datasheet](https://documentation.espressif.com/esp32-s3_datasheet_en.pdf) — Seite prüfen

<a id="c012"></a>
**C012 · LITERATURFAKT / REGEL**

ESP-IDF I²S-Datenübertragung nutzt DMA; Datenblöcke werden über DMA-Puffer transportiert, und blockierende read/write APIs beziehungsweise Callback-basierte asynchrone Verarbeitung sind dokumentiert.

**Ursprung:** [preThesis/03-recherche/R10-esp32-plattform.md:85-92](../../preThesis/03-recherche/R10-esp32-plattform.md#L85)
**Belege:** [Espressif Systems · esp_i2s_s3](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/i2s.html) — Fundstelle: Data Transport (aus Stage 1; am Original prüfen); [Espressif Systems · esp_s3_datasheet](https://documentation.espressif.com/esp32-s3_datasheet_en.pdf) — Seite prüfen; [Zephyr Project · zephyr_i2s_binding](https://docs.zephyrproject.org/latest/build/dts/api/bindings/i2s/espressif,esp32-i2s.html) — Fundstelle: Binding properties (aus Stage 1; am Original prüfen)

<a id="c010"></a>
**C010 · LITERATURFAKT / REGEL**

Laut ESP-IDF-Modusübersicht besitzt der ESP32-S3 keine integrierte I²S-ADC/DAC-Funktion; die Audioausgabe des Prototyps ist daher auf einen externen Audio-DAC/-Codec oder Verstärker angewiesen.

**Ursprung:** [preThesis/03-recherche/R10-esp32-plattform.md:109-117](../../preThesis/03-recherche/R10-esp32-plattform.md#L109)
**Belege:** [Espressif Systems · esp_i2s_s3](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/i2s.html) — Fundstelle: Overview of All Modes (aus Stage 1; am Original prüfen); [Espressif Systems · esp_s3_datasheet](https://documentation.espressif.com/esp32-s3_datasheet_en.pdf) — Seite prüfen; [Zephyr Project · zephyr_s3_board](https://docs.zephyrproject.org/latest/boards/espressif/esp32s3_devkitc/doc/index.html) — Fundstelle: Supported Features (aus Stage 1; am Original prüfen)

<a id="c011"></a>
**C011 · LITERATURFAKT / REGEL · QUELLENSET UNVOLLSTÄNDIG**

PDM-zu-PCM-Konvertierung erfolgt per Hardware auf ESP32-S3-I²S0; an einem Port ohne Konverter muss die Software die rohe PDM-Datenfolge filtern und dezimieren.

**Ursprung:** [preThesis/03-recherche/R10-esp32-plattform.md:85-92](../../preThesis/03-recherche/R10-esp32-plattform.md#L85)
**Korrektur Stage 2 (2026-10-24):** Die ESP-DSP-API belegt keine I²S-Controller- oder PDM-Konvertierungsmodi. Das Quellenset bleibt unvollständig; die passende ESP-IDF-I²S-Referenz ist noch zu prüfen. Quelle: [_build/stage2-corrections.json](../_build/stage2-corrections.json).
**Belege:** [Espressif Systems · esp_i2s_s3](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/i2s.html) — Fundstelle: Overview of All Modes; PDM RX Mode in PCM Format (aus Stage 1; am Original prüfen); [Espressif Systems · esp_s3_datasheet](https://documentation.espressif.com/esp32-s3_datasheet_en.pdf) — Seite prüfen
