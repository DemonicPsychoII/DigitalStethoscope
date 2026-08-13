# FHIR-Ressourcenprofil und TLS-Zertifikatshandling auf ESP32

- **Run-ID:** R11-fhir-tls
- **Preset:** low
- **Modell:** preset/low

## Fragestellung

```
Kontext: Bachelorarbeit, digitales Stethoskop auf ESP32-S3. Die gemessene Herzfrequenz soll als FHIR-Ressource ueber eine TLS-gesicherte Verbindung an einen Server uebertragen werden.

Hauptfrage: Wie sieht eine minimale, standardkonforme FHIR-Uebertragung einer Herzfrequenz aus, und was ist beim TLS-Zertifikatshandling auf einem ESP32 zu beachten?

Unterfrage 1: Wie ist eine FHIR-Observation fuer Herzfrequenz korrekt aufgebaut (FHIR R4/R5, Profil 'Vitalsigns', LOINC-Code fuer Heart rate, UCUM-Einheit, Pflichtfelder status/category/subject/effectiveDateTime)? Bitte ein minimales JSON-Beispiel.
Unterfrage 2: Welche praktischen Stolpersteine gibt es bei mbedTLS auf dem ESP32 - Speicherbedarf des Root-CA-Bundles vs. einzelnes gepinntes Zertifikat, Notwendigkeit korrekter Systemzeit (SNTP) fuer die Gueltigkeitspruefung, Verhalten bei Zertifikatsablauf, und Heap-Bedarf des Handshakes?

Antwort auf Deutsch, mit Quellen (FHIR-Spezifikation, ESP-IDF-Dokumentation) und konkretem JSON-Beispiel.
```

## Ergebnis

## Kurzantwort

Eine minimale, standardkonforme Übertragung besteht aus einer **FHIR-`Observation`** mit dem Vital-Signs-Profil, dem LOINC-Code **8867-4 (Heart rate)**, dem UCUM-Code **`/min`**, einem numerischen `valueQuantity` sowie den Angaben zu Status, Patient und Messzeitpunkt. Die Ressource wird anschließend als JSON über eine per TLS authentisierte HTTPS-Verbindung übertragen.

Für den ESP32-S3 sollte der Server mindestens über einen vertrauenswürdigen **Root-CA-Zertifikatsanker** geprüft werden. Das kann entweder ein einzelnes CA-Zertifikat oder das ESP-IDF-Zertifikatsbundle sein. Die Systemzeit muss vor der Zertifikatsprüfung korrekt gesetzt werden, typischerweise per SNTP.

## 1. FHIR-Observation für die Herzfrequenz

### Profil und Pflichtinhalte

Das FHIR-Core-Profil **Vital Signs** gilt sowohl für FHIR R4 als auch für FHIR R5 grundsätzlich nach demselben Muster. Für eine Herzfrequenz sind insbesondere folgende Inhalte erforderlich:

| FHIR-Element | Minimaler Inhalt |
|---|---|
| `resourceType` | `Observation` |
| `status` | z. B. `final` |
| `category` | Code `vital-signs` aus `http://terminology.hl7.org/CodeSystem/observation-category` |
| `code` | LOINC `8867-4`, `Heart rate` |
| `subject` | Referenz auf eine `Patient`-Ressource |
| `effectiveDateTime` | Zeitpunkt der Messung |
| `valueQuantity.value` | numerischer Herzfrequenzwert |
| `valueQuantity.unit` | z. B. `beats/min` |
| `valueQuantity.system` | `http://unitsofmeasure.org` |
| `valueQuantity.code` | `/min` |

Das Vital-Signs-Profil verlangt eine Statusangabe, die Kategorie `vital-signs`, einen passenden LOINC-Code, einen Patienten, einen Messzeitpunkt und einen numerischen Messwert mit standardisierter UCUM-Einheit. Für Herzfrequenz ist der vorgesehene LOINC-Code **8867-4** und die UCUM-Einheit **`/min`**. [web:1]

`subject` sollte dabei auf eine `Patient`-Ressource verweisen, beispielsweise `Patient/123`. Die Patient-Ressource muss nicht Bestandteil derselben HTTP-Anfrage sein; sie kann bereits auf dem FHIR-Server existieren.

### Minimales JSON-Beispiel

```json
{
  "resourceType": "Observation",
  "id": "heart-rate-20260811-001",
  "status": "final",
  "category": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/observation-category",
          "code": "vital-signs",
          "display": "Vital Signs"
        }
      ]
    }
  ],
  "code": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "8867-4",
        "display": "Heart rate"
      }
    ],
    "text": "Herzfrequenz"
  },
  "subject": {
    "reference": "Patient/123"
  },
  "effectiveDateTime": "2026-08-11T10:15:30Z",
  "valueQuantity": {
    "value": 72,
    "unit": "beats/min",
    "system": "http://unitsofmeasure.org",
    "code": "/min"
  }
}
```

Der numerische Wert `72` bedeutet in diesem Beispiel 72 Herzschläge pro Minute. Der Code `/min` ist der maschinenlesbare UCUM-Code; `beats/min` ist die menschenlesbare Einheit. Ein optionaler `device`-Verweis kann ergänzt werden, wenn das digitale Stethoskop als FHIR-`Device` registriert ist. Ebenso kann ein `performer` angegeben werden, ist für das minimale Beispiel aber nicht erforderlich.

Ein Senden an einen FHIR-Server erfolgt typischerweise mit:

```http
POST /fhir/Observation HTTP/1.1
Host: fhir.example.org
Content-Type: application/fhir+json
Accept: application/fhir+json
Authorization: Bearer <token>
```

Der HTTP-Body ist das oben dargestellte JSON. Die Übertragung muss über HTTPS erfolgen, also beispielsweise:

```text
https://fhir.example.org/fhir/Observation
```

Die FHIR-Spezifikation definiert die Ressource und ihre Semantik; die TLS-Sicherung erfolgt auf der darunterliegenden HTTP- beziehungsweise Transportebene.

### R4/R5-Hinweis

Für dieses Minimalbeispiel gibt es zwischen R4 und R5 keinen relevanten Unterschied bei den verwendeten Elementen. Wichtig ist jedoch, dass der Server und das verwendete Implementierungsleitfaden-Profil dieselbe FHIR-Version erwarten. Die URL des verwendeten Profils kann mit einem zusätzlichen `meta.profile` angegeben werden, beispielsweise:

```json
"meta": {
  "profile": [
    "http://hl7.org/fhir/StructureDefinition/vitalsigns"
  ]
}
```

Für eine streng profilbezogene Implementierung sollte die konkrete Profil-URL aus der Zielumgebung verwendet und anschließend mit einem FHIR-Validator geprüft werden.

## 2. TLS-Zertifikatshandling auf dem ESP32-S3

### Einzelnes CA-Zertifikat versus Root-CA-Bundle

ESP-TLS unterstützt unter anderem:

- ein einzelnes CA-Zertifikat über `cacert_buf` und `cacert_bytes`,
- einen globalen CA-Speicher,
- das ESP-IDF-X.509-Zertifikatsbundle über `crt_bundle_attach = esp_crt_bundle_attach`. [web:16]

Ein einzelnes CA-Zertifikat ist hinsichtlich Flash- und meist auch RAM-Bedarf günstiger. Es eignet sich, wenn der Server kontrolliert wird und dessen Zertifikatskette dauerhaft auf einer bekannten Root-CA beruht. Gepinnt werden sollte vorzugsweise die **Root-CA** und nicht das kurzlebige Server- oder Intermediate-Zertifikat. Das reduziert die Häufigkeit notwendiger Firmwareupdates.

Das CA-Bundle ist flexibler, weil damit viele öffentliche Zertifizierungsstellen unterstützt werden. Dafür enthält es wesentlich mehr Zertifikatsdaten und benötigt entsprechend zusätzlichen Flash-Speicher sowie Ressourcen beim Parsen und bei der Zertifikatsvalidierung. Ein Bundle verhindert außerdem nicht automatisch jedes Wartungsproblem: Wenn eine Root-CA abläuft, entfernt oder geändert wird, muss das Bundle aktualisiert werden. [web:21]

Für eine Bachelorarbeits-Demonstration mit genau einem eigenen FHIR-Server ist daher meist folgende Strategie sinnvoll:

```c
esp_tls_cfg_t cfg = {
    .cacert_buf   = server_root_ca_pem,
    .cacert_bytes = sizeof(server_root_ca_pem),
    .common_name  = "fhir.example.org"
};
```

Bei einer öffentlichen, wechselnden Serverlandschaft kann dagegen das Bundle zweckmäßiger sein:

```c
esp_tls_cfg_t cfg = {
    .crt_bundle_attach = esp_crt_bundle_attach
};
```

Die Serveridentität darf nicht durch `skip_server_verification` oder `skip_common_name` abgeschaltet werden. `skip_common_name` deaktiviert sowohl die Prüfung des Hostnamens gegen CN/SAN als auch SNI und sollte nur für kontrollierte Testfälle verwendet werden. [web:16]

### Korrekte Systemzeit und SNTP

mbedTLS kann die Gültigkeitszeiträume von X.509-Zertifikaten prüfen. Dafür muss die Option zur Zeit-/Datumsprüfung aktiviert sein. Ist sie aktiviert, vergleicht mbedTLS die Felder `valid from` und `valid to` mit der aktuellen Systemzeit. Eine falsche oder noch nicht gesetzte ESP32-Uhr kann daher dazu führen, dass ein eigentlich gültiges Zertifikat als noch nicht gültig oder als abgelaufen bewertet wird. ESP-IDF nennt dafür unter anderem die Fehler `MBEDTLS_X509_BADCERT_FUTURE` und `MBEDTLS_X509_BADCERT_EXPIRED`. [web:18]

Der typische Ablauf ist deshalb:

1. WLAN-Verbindung herstellen.
2. DNS beziehungsweise Netzwerkzugang abwarten.
3. Uhrzeit über SNTP synchronisieren.
4. Erst danach die HTTPS-/FHIR-Verbindung aufbauen.
5. Bei fehlender Zeit-Synchronisation nicht einfach die Zertifikatsprüfung deaktivieren.

Konzeptionell:

```c
initialize_wifi();
wait_until_ip_address_is_obtained();

initialize_sntp();
wait_until_system_time_is_valid();

send_fhir_observation_over_https();
```

Beim ersten Boot nach einem Reset oder bei einer RTC ohne Batterie ist die Uhr häufig zunächst auf einen ungültigen Standardwert gesetzt. Das ist besonders relevant, wenn unmittelbar nach dem WLAN-Verbindungsaufbau ein TLS-Handshake gestartet wird.

### Verhalten bei Zertifikatsablauf

Läuft das Serverzertifikat oder eine benötigte CA ab, schlägt die Zertifikatsprüfung fehl. Ein automatischer Zeit- oder Zertifikats-Workaround auf dem ESP32 wäre sicherheitswidrig. Stattdessen müssen:

- das Serverzertifikat rechtzeitig erneuert,
- gegebenenfalls das einzelne Root-CA-Zertifikat aktualisiert,
- bei Verwendung des Bundles das Bundle aktualisiert,
- und die Firmware beziehungsweise Zertifikatsdaten kontrolliert ausgerollt werden.

Das Endgerät sollte den TLS-Fehler protokollieren und eine erneute Verbindung später versuchen, aber **nicht** auf ungesichertes HTTP zurückfallen. Bei Zertifikatswechseln sollte geprüft werden, ob die neue Serverkette weiterhin zur eingebauten Root-CA passt.

### Heap-Bedarf des TLS-Handshakes

Der TLS-Handshake benötigt deutlich mehr Heap als die spätere Übertragung eines kleinen JSON-Dokuments. Die ESP-IDF-FAQ nennt typischerweise etwa **40–50 kB freien Heap** für einen stabilen TLS-Handshake; Fragmentierung oder zu wenig zusammenhängender Speicher können den Handshake trotzdem scheitern lassen. [web:17]

Die ESP-IDF-Dokumentation zeigt als Größenordnung für Mbed TLS bei aktivierter Servervalidierung beispielsweise ungefähr:

- Standardkonfiguration: circa **42 kB**,
- ohne dauerhaft gespeichertes Peer-Zertifikat: circa **38,5 kB**,
- mit dynamischen TX-/RX-Puffern: circa **22 kB**.

Diese Werte sind konfigurations- und versionsabhängig und stellen keine harte Mindestanforderung für jedes ESP32-S3-System dar. [web:19]

Praktische Maßnahmen:

- freien **internen** Heap unmittelbar vor dem Handshake messen,
- große Audio-Puffer während des Handshakes freigeben oder verkleinern,
- dynamische TLS-TX-/RX-Puffer aktivieren,
- Peer-Zertifikate nach dem Handshake nicht behalten, wenn sie nicht benötigt werden,
- PSRAM für geeignete Mbed-TLS-Allokationen konfigurieren,
- `CONFIG_MBEDTLS_SSL_IN_CONTENT_LEN` nicht zu klein wählen; die ESP-IDF weist insbesondere auf eine notwendige Größenordnung bis maximal 16 kB für TLS-Eingabedaten hin. [web:17][web:20]

Für das Stethoskop ist außerdem zu beachten, dass die Herzfrequenzmessung und die Audioverarbeitung ihre Speicheranforderungen nicht nur während des HTTP-POSTs, sondern auch während DNS, TCP-Aufbau und TLS-Handshake behalten können. Der relevante Test ist deshalb der tatsächlich verfügbare Heap **während** des Handshakes, nicht nur der Heap direkt nach dem Boot.

## Empfohlene Minimalarchitektur

Für die konkrete Bachelorarbeit bietet sich folgende Minimalarchitektur an:

1. Herzfrequenz aus dem Audiosignal bestimmen.
2. Messwert zusammen mit einem UTC-Zeitstempel erfassen.
3. JSON-`Observation` gemäß dem Beispiel erzeugen.
4. SNTP-Zeit synchronisieren.
5. HTTPS-Verbindung mit aktivierter Serverzertifikats- und Hostnamenprüfung aufbauen.
6. Das Root-CA-Zertifikat des FHIR-Servers entweder einzeln im Firmware-Image hinterlegen oder das ESP-IDF-Bundle verwenden.
7. `POST /fhir/Observation` mit `Content-Type: application/fhir+json` senden.
8. HTTP- und FHIR-Fehlerantworten auswerten und bei transienten Fehlern mit Backoff wiederholen.

Damit sind sowohl die FHIR-Anforderungen an eine minimale Herzfrequenz-Observation als auch die wesentlichen Sicherheits- und Ressourcenanforderungen des ESP32-S3 abgedeckt.

## Quellen

1. [Observation-vitalsigns - FHIR v6.0.0-ballot4](https://build.fhir.org/observation-vitalsigns.html)
2. [FHIR Vital Signs profiles API standards - NHS England Digital](https://digital.nhs.uk/developer/api-catalogue/fhir-vital-signs-standards)
3. [Vital Signs - Elation Help Center](https://help.elationhealth.com/articles/fhir/uscdi-vital-signs)
4. [Patient heart rate - XML Representation](https://hl7.eu/fhir/imaging-r5/0.1.0-snapshot1/Observation-HRObservation.xml.html)
5. [Vital Sign Heart Rate Example with component Heart Rate Rhythm](https://fhir.medirecords.com/Observation-hrtbb6-e771-4801-ad05-63b33737189f.json.html)
6. [Observation-example-heart-rate](http://fhir.outburn.co.il/R4-spec/observation-example-heart-rate.html)
7. [Heart Rate - Vital Signs with Qualifying Elements v2.0.0](https://build.fhir.org/ig/HL7/cimi-vital-signs/StructureDefinition-heart-rate.html)
8. [StructureDefinition/ObservationVitalSigns](https://nrces.in/ndhm/fhir/r4/StructureDefinition-ObservationVitalSigns.html)
9. [Vital Signs - FHIR Implementation Guide for ABDM v6.5.0 - NRCeS](https://nrces.in/ndhm/fhir/r4/ValueSet-ndhm-vital-signs.html)
10. [Observation Heart Rate Profile - v1.0.0 - Cambio](https://fhir.openservices.cambio.se/site/StructureDefinition-ObservationHeartRate.html)
11. [Observation: Medical Test Result (EU core) - HL7 Europe -](https://hl7.eu/fhir/base/2.0.0/StructureDefinition-medicalTestResult-eu-core.html)
12. [Observation - FHIR v6.0.0-ballot4](https://build.fhir.org/observation.html)
13. [Vital Signs](https://fhir.interweavedigital.com/ValueSet-observation-vitalsignresult.html)
14. [vital | API Developer Portal](https://devportal-dev.blueshieldca.com/bsc/fhir-sandbox/vital)
15. [Observation-vitals-panel.json - hl7.fhir.us.core - GitHub](https://github.com/google/fhir/blob/master/spec/hl7.fhir.us.core/3.0.0/package/Observation-vitals-panel.json)
16. [ESP-TLS - ESP32 - — ESP-IDF Programming Guide v6.0.2 ...](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/protocols/esp_tls.html)
17. [ESP-TLS - - — ESP-FAQ latest documentation](https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/protocols/esp-tls.html)
18. [Project Configuration - ESP32 - — ESP-IDF Programming ...](https://docs.espressif.com/projects/esp-idf/en/v4.4.5/esp32/api-reference/kconfig.html)
19. [Mbed TLS - ESP32 - — ESP-IDF Programming Guide v6. ...](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/protocols/mbedtls.html)
20. [Mbed TLS - - — ESP-FAQ latest documentation](https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/protocols/mbedtls.html)
21. [Security Overview - ESP32-C61 - — ESP-IDF Programming ...](https://docs.espressif.com/projects/esp-idf/en/stable/esp32c61/security/security.html)
22. [ESP-TLS - ESP32 - — ESP-IDF 编程指南v6.0.2 文档](https://docs.espressif.com/projects/esp-idf/zh_CN/stable/esp32/api-reference/protocols/esp_tls.html)
23. [Wi-Fi 库 - ESP32-S3 - — ESP-IDF 编程指南 v5.3.1 文档](https://docs.espressif.com/projects/esp-idf/zh_CN/v5.3.1/esp32s3/api-reference/network/esp_wifi.html)
24. [ESP HTTPS OTA - ESP32](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/system/esp_https_ota.html)
25. [ESP-Techpedia_EN - Technical Documents](https://docs.espressif.com/projects/esp-techpedia/en/latest/ESP-Techpedia-en-master.pdf)
