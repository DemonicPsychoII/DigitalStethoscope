# Embedded-System, RTOS und ESP32

[Zum Einstieg](../README.md) · [Offene Punkte](../offene-punkte.md)

Plattform und Treiber → Scheduling und Speicher → dokumentierte Grenzen.

**1 aktive Einheiten.** Schreibreihenfolge: Definition → Mechanismus → Werte → Folgerung. Die Aussagen sind Material, kein fertiger Fließtext.

**Schreibhinweis:** Literaturgrundlagen erklären das Verfahren. Zielwerte, Architekturentscheidungen und Berichtsempfehlungen als solche benennen und später in Anforderungen/Methodik begründen.

**Materiallücke:** Das Inventar liefert keine zusammenhängende Einführung in RTOS, Threadprioritäten und Zephyr-Scheduling. Die ESP-IDF-Empfehlung in der Architektur ist historischer Recherchekontext; der dokumentierte Prototyp nutzt Zephyr. Grundlagen ergänzen und am tatsächlich verwendeten Stand belegen.

## Schreibbausteine

### Mechanismen und Zusammenhänge

<a id="c014"></a>
**C014 · LITERATURFAKT / REGEL**

Die Zephyr-Dokumentation enthält ein ESP32-S3-DevKitC-Boardziel und einen Espressif-ESP32-I²S-Devicetree-Binding-Eintrag.

**Ursprung:** [preThesis/03-recherche/R10-esp32-plattform.md:94-118](../../preThesis/03-recherche/R10-esp32-plattform.md#L94)
**Belege:** [Zephyr Project · zephyr_s3_board](https://docs.zephyrproject.org/latest/boards/espressif/esp32s3_devkitc/doc/index.html) — Fundstelle: Board Support Package (aus Stage 1; am Original prüfen); [Zephyr Project · zephyr_i2s_binding](https://docs.zephyrproject.org/latest/build/dts/api/bindings/i2s/espressif,esp32-i2s.html) — Fundstelle: Binding properties (aus Stage 1; am Original prüfen); [Espressif Systems · esp_i2s_s3](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/i2s.html) — Fundstelle: Introduction (aus Stage 1; am Original prüfen)
