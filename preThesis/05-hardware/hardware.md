> Update 2026-09-16: the user confirmed the existing Eval wiring working. The maintained signal map and integrated test instructions are in [the Eval README](../../Development/system/coding/bringup-zephyr/README.md). The inventory below is historical; only one physical switch is mapped by default, and playback speed is available through touch/serial. A second-switch overlay is optional and separately unverified.

# Hardware — aktueller Stand

> Stand: 2026-08-13. Vorhandene Komponenten für Aufbau und Tests. Rollen gemäß Bedien- und
> Signalpfadkonzept aus der Aufgabenbeschreibung.

## Stückliste

| Komponente | Bezeichnung | Schnittstelle | Rolle im System |
|---|---|---|---|
| MCU | ESP32-S3 **N16R8** DevKitC-1 (16 MB Flash, 8 MB PSRAM) | — | Rechenplattform, Echtzeit-Audioverarbeitung, WiFi/TLS |
| Audio-DAC | **PCM5102A** | I²S | Wiedergabe an Kopfhörer |
| MEMS-Mikrofon | **INMP441** | I²S | Aufnahme des Auskultationssignals |
| Bedientaster | LED-Tastschalter 12×12×7 mm | GPIO | Taster mit Statusanzeige (z. B. Modus/Bestätigung) |
| Potentiometer | 10 kΩ | ADC | **Lautstärke** |
| Display | Fasizi **ILI9341** 240×320 TFT LCD, Touch | SPI (+ Touch) | Anzeige; optional Touch-Konfiguration |
| Wahlschalter 1 | **SP3T** THT Kippschalter, 100 mA, 13×3,5 mm | GPIO | Filter: Raw / Murmur / BPM |
| Wahlschalter 2 | **SP3T** THT Kippschalter, 100 mA, 13×3,5 mm | GPIO | Wiedergabegeschwindigkeit: 1,0× / 0,75× / 0,5× |

## Hinweise / offene Punkte

- **PCM5102A** ✅ bestätigt — I²S-DAC für die Wiedergabe.
- **INMP441** ✅ bestätigt — untere Grenzfrequenz limitiert. Das Mikrofon ist gesetzt: die Entwicklung findet **innerhalb dieser Randbedingung** statt, Q1 wird entsprechend nur im nutzbaren Band beantwortet. Kein Vergleich gegen die in `03-recherche/R07-bruststueck-mems.md` empfohlenen Tieftontypen.
- **Bedienkonzept:** Poti = Lautstärke, SP3T 1 = Filter (Raw/Murmur/BPM), SP3T 2 = Wiedergabegeschwindigkeit (1,0×/0,75×/0,5×). Zwei SP3T ✅ vorhanden. Optional Auslagerung einer Funktion auf das Touch-Display.
- **I²S-Bus-Aufteilung:** INMP441 (Eingang) und PCM5102A (Ausgang) — Zuordnung der I²S-Peripherie/Pins in der Architektur (AP 1.4) festlegen.
- **PSRAM (R8 = 8 MB):** ersetzt nicht den DMA-fähigen internen SRAM; TLS-Handshake-Heap bleibt kritischer Engpass (siehe `03-recherche/R10-esp32-plattform.md`, `R11-fhir-tls.md`).

## Noch zu beschaffen / zu klären

- Kopfhörer / Verstärkerstufe hinter PCM5102A
- Verkabelung/Adapterplatine, ggf. Steckbrett vs. Lötaufbau
