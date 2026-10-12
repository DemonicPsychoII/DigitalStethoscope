# FHIR und TLS

[Zum Einstieg](../README.md) · [Offene Punkte](../offene-punkte.md)

Observation und Kodierung → Patient/Zeitbezug → Transport und Zertifikatsprüfung.

**9 aktive Einheiten.** Schreibreihenfolge: Definition → Mechanismus → Werte → Folgerung. Die Aussagen sind Material, kein fertiger Fließtext.

**Schreibhinweis:** Literaturgrundlagen erklären das Verfahren. Zielwerte, Architekturentscheidungen und Berichtsempfehlungen als solche benennen und später in Anforderungen/Methodik begründen.

## Schreibbausteine

### Begriffe und Definitionen

<a id="c033"></a>
**C033 · LITERATURFAKT / REGEL**

FHIR-Semantik und Profilierung liegen auf Anwendungsebene; TLS sichert die darunterliegende HTTPS-Transportverbindung und ersetzt keine FHIR-Profilvalidierung.

**Ursprung:** [preThesis/03-recherche/R11-fhir-tls.md:94-124](../../preThesis/03-recherche/R11-fhir-tls.md#L94)
**Belege:** [HL7 · fhir_observation_r4](https://hl7.org/fhir/R4/observation.html) — Seite prüfen; [Espressif Systems · esp_tls_s3](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/protocols/esp_tls.html) — Fundstelle: Overview (aus Stage 1; am Original prüfen); [HL7 · fhir_r4_vitals_official](https://hl7.org/fhir/R4/observation-vitalsigns.html) — Fundstelle: Vital Signs Profile (aus Stage 1; am Original prüfen)

<a id="c029"></a>
**C029 · LITERATURFAKT / REGEL**

Für Herzfrequenz empfiehlt der Bericht eine FHIR-`Observation` mit vital-signs-Kategorie, LOINC 8867-4, `subject`, Messzeitpunkt und numerischem `valueQuantity` mit UCUM-System und Code `/min`.

**Ursprung:** [preThesis/03-recherche/R11-fhir-tls.md:22-49](../../preThesis/03-recherche/R11-fhir-tls.md#L22)
**Weiterer Kapitelbezug:** Ethik/Datenschutz/Regulatorik
**Belege:** [HL7 · fhir_r4_vitals_official](https://hl7.org/fhir/R4/observation-vitalsigns.html) — Fundstelle: Vital Signs Profile; Heart rate row (aus Stage 1; am Original prüfen); [Regenstrief Institute · loinc_8867_official](https://loinc.org/8867-4) — Fundstelle: Term details; Example Units (aus Stage 1; am Original prüfen); [HL7 · fhir_observation_r4](https://hl7.org/fhir/R4/observation.html) — Seite prüfen

<a id="u068"></a>
**U068 · LITERATURFAKT / REGEL**

R11 beschreibt Heart Rate Observation mit vital-signs, LOINC 8867-4, Patient-Referenz, effectiveDateTime, valueQuantity, UCUM /min.

**Ursprung:** [preThesis/02-entscheidungen/open-questions.md:275-278](../../preThesis/02-entscheidungen/open-questions.md#L275)
**Belege:** [HL7 · fhir_r4_vitals](https://www.hl7.org/fhir/R4/observation-vitalsigns.html) — Fundstelle: Vital Signs table, Heart rate row (aus Stage 1; am Original prüfen); [Regenstrief Institute · loinc_8867](https://loinc.org/8867-4/) — Seite prüfen (Hinweis: Relevant article section/table not verified in full text during this pass.); [HL7 · fhir_hr_example](https://www.hl7.org/fhir/R4/observation-example-heart-rate.json.html) — Seite prüfen (Hinweis: Relevant article section/table not verified in full text during this pass.)

### Mechanismen und Zusammenhänge

<a id="c030"></a>
**C030 · LITERATURFAKT / REGEL**

Das FHIR-R4-Profil Vital Signs identifiziert die Herzfrequenz mit LOINC-Code 8867-4; die zugehörige Größe verwendet eine UCUM-Einheit wie `/min`.

**Ursprung:** [preThesis/03-recherche/R11-fhir-tls.md:32-49](../../preThesis/03-recherche/R11-fhir-tls.md#L32)
**Belege:** [HL7 · fhir_r4_vitals_official](https://hl7.org/fhir/R4/observation-vitalsigns.html) — Fundstelle: Vital Signs Profile; Heart rate row (aus Stage 1; am Original prüfen); [Regenstrief Institute · loinc_8867_official](https://loinc.org/8867-4) — Fundstelle: Term details; Example Units (aus Stage 1; am Original prüfen); [HL7 · fhir_observation_r4](https://hl7.org/fhir/R4/observation.html) — Seite prüfen

<a id="c032"></a>
**C032 · LITERATURFAKT / REGEL · QUELLENSET UNVOLLSTÄNDIG**

Der `Patient`-Verweis in `Observation.subject` kann auf eine bereits vorhandene Serverressource zeigen und muss nicht zusammen mit der Observation übertragen werden.

**Ursprung:** [preThesis/03-recherche/R11-fhir-tls.md:47-50](../../preThesis/03-recherche/R11-fhir-tls.md#L47)
**Korrektur Stage 2 (2026-10-12):** THA-FAQ zur Bachelorarbeit (DMS-Anmeldung, Fristen) belegt keine FHIR-Referenzsemantik. Quellenset bleibt als unvollständig markiert. Quelle: [_build/stage2-corrections.json](../_build/stage2-corrections.json).
**Belege:** [HL7 · fhir_r4_vitals_official](https://hl7.org/fhir/R4/observation-vitalsigns.html) — Fundstelle: Vital Signs Profile (aus Stage 1; am Original prüfen); [HL7 · fhir_observation_r4](https://hl7.org/fhir/R4/observation.html) — Seite prüfen

<a id="c034"></a>
**C034 · LITERATURFAKT / REGEL**

ESP-TLS bietet serverseitige Zertifikatsprüfung unter anderem über CA-Puffer, globalen CA-Speicher oder X.509-Zertifikatsbundle; ohne konfigurierte Verifikationsmethode schlägt der Verbindungsaufbau fehl.

**Ursprung:** [preThesis/03-recherche/R11-fhir-tls.md:126-158](../../preThesis/03-recherche/R11-fhir-tls.md#L126)
**Belege:** [Espressif Systems · esp_tls_s3](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/protocols/esp_tls.html) — Fundstelle: TLS Server Verification (aus Stage 1; am Original prüfen); [Espressif Systems · esp_mbedtls_s3](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/protocols/mbedtls.html) — Seite prüfen; [Espressif Systems · esp_tls_faq](https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/protocols/esp-tls.html) — Fundstelle: Question on server certificate verification (aus Stage 1; am Original prüfen)

<a id="c038"></a>
**C038 · LITERATURFAKT / REGEL · QUELLENSET UNVOLLSTÄNDIG**

R11 nennt `MBEDTLS_X509_BADCERT_FUTURE` und `MBEDTLS_X509_BADCERT_EXPIRED` als mögliche Folgen einer Systemzeit, die außerhalb des Zertifikatszeitraums liegt.

**Ursprung:** [preThesis/03-recherche/R11-fhir-tls.md:160-184](../../preThesis/03-recherche/R11-fhir-tls.md#L160)
**Belege:** [Espressif Systems · esp_mbedtls_s3](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/protocols/mbedtls.html) — Seite prüfen; [Espressif Systems · esp_tls_s3](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/protocols/esp_tls.html) — Fundstelle: TLS Server Verification (aus Stage 1; am Original prüfen); [Espressif Systems · esp_tls_faq](https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/protocols/esp-tls.html) — Fundstelle: Question on certificate expiry (aus Stage 1; am Original prüfen)

### Werte und dokumentierte Befunde

<a id="c040"></a>
**C040 · EIGENER ZIELWERT / VORLÄUFIGER VORSCHLAG**

Die Espressif-FAQ schätzt, dass ein ESP32-TLS-Handshake typischerweise 40–50 kB freien Heap für temporäre Allokationen benötigt; Heap-Fragmentierung kann auch bei nominell ausreichendem freien Speicher zum Fehlschlag führen.

**Ursprung:** [preThesis/03-recherche/R11-fhir-tls.md:197-207](../../preThesis/03-recherche/R11-fhir-tls.md#L197)
**Weiterer Kapitelbezug:** Systemarchitektur
**Belege:** [Espressif Systems · esp_tls_faq](https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/protocols/esp-tls.html) — Fundstelle: Question: How much memory is required for a stable TLS handshake? (aus Stage 1; am Original prüfen); [Espressif Systems · esp_mbedtls_s3](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/protocols/mbedtls.html) — Seite prüfen; [Espressif Systems · esp_tls_s3](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/protocols/esp_tls.html) — Fundstelle: Overview (aus Stage 1; am Original prüfen)

<a id="c041"></a>
**C041 · LITERATUR- / HERSTELLERWERT · QUELLENSET UNVOLLSTÄNDIG**

R11 nennt ungefähre Mbed-TLS-Heapwerte von 42 kB in der Standardkonfiguration, 38,5 kB nach Freigabe des Peer-Zertifikats und 22 kB mit dynamischen TX/RX-Puffern; die Werte hängen ausdrücklich von Version und Konfiguration ab.

**Ursprung:** [preThesis/03-recherche/R11-fhir-tls.md:201-218](../../preThesis/03-recherche/R11-fhir-tls.md#L201)
**Belege:** [Espressif Systems · esp_mbedtls_s3](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/protocols/mbedtls.html) — Seite prüfen; [Espressif Systems · esp_tls_faq](https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/protocols/esp-tls.html) — Fundstelle: Question on handshake memory (aus Stage 1; am Original prüfen)
