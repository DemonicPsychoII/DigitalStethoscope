# Integrated evaluation protocol

## Scope and baseline

Use the [submission brief](../../../thesis/brief/Aufgabenbeschreibung-Abgabe.md) as the deliverable baseline: live filtered
headphone audio, automatic heart rate, reduced-speed listening and secure FHIR
transfer; compare filter variants quantitatively against a suitable reference.
The internal versions add concrete controls and heart/lung/point selection.
Formal acoustic transfer-chain characterization and permanent audio storage are
excluded; the RAM clip is volatile. The filter coefficients and BPM thresholds
in this firmware are initial evaluation candidates, not a claim of optimality.

The user confirmed existing evaluation wiring working on 2026-09-16. Preserve
that wiring; do not reclassify historical tests or infer new-firmware acceptance.
Each new run records operator, board/module revision, pin-map revision, firmware
binary hash, source revision/dirty state, build configuration, fixture identity,
reference method and measured outcome. No integrated physical test was performed
by the software implementation session.

## Host tests and repeatable input

Use Python 3.12 or newer. From the application directory:

```sh
python -m pip install --require-hashes -r tools/requirements.txt
python -m pytest -q tests/host
python tools/evaluate.py generate reference.wav --kind heart --bpm 72 --seconds 12
python tools/evaluate.py evaluate reference.wav --reference-bpm 72 --reference "synthetic 72 BPM" --output results/reference72
```

Host comparisons hold the analysis filter at `bpm` while changing the listening
filter. Use `--analysis-filter raw` or `murmur` for another fixed analysis path,
or `--analysis-filter matched` to compare the paired listening/analysis variants.
Each report records both filters and the selected analysis mode; matched results
change two variables and must be interpreted accordingly.

The tool compiles **the same C DSP** used on the ESP32 with GCC, then exports
filtered WAVs, per-second estimator CSVs and a JSON comparison (MAE, RMSE, bias,
maximum error and valid-window coverage after the 8-second acquisition window).
Input must be mono 16-bit PCM at 16 kHz; conversion must be explicit and recorded.
The fixed `--reference-bpm` mode is for constant-reference segments. Split varying
rate recordings into suitably annotated segments; it is not a time-aligned ECG
comparison implementation. Host timing is not MCU CPU-load evidence.

Synthetic fixtures cover known rates, silence, noise, DC, carrier tones, filter
response, replay pitch/duration and invalid FHIR payloads. For the thesis, add
licensed heart-sound recordings and synchronized reference annotations; repeated
synthetic pulses alone are insufficient to establish physiological accuracy.
Use both digital injection (isolates software) and controlled acoustic playback
through the chestpiece (exercises the assembled capture chain).

To exercise the device DSP from a WAV of at most the configured clip capacity:

```sh
python tools/evaluate.py upload short-fixture.wav --port /dev/ttyUSB0
```

This clears the volatile fixture, uploads signed 16-bit samples with acknowledged
serial commands and selects source 3. The fixture repeats at the original rate;
use a seamless segment or account for the loop boundary in reference annotations.
Volume remains under the potentiometer unless disabled explicitly. Clear a fixture
with `stetho fixture reset`; select `stetho set source 0` to return to the mic.
Neither firmware clip nor fixture is written to flash.

## Hardware acceptance matrix

All thresholds below are engineering acceptance targets for this prototype.
Record actual values and resolve changes to targets before a comparative study.
The existing 35 ms input requirement is measured from stable GPIO edge to handler.

| ID | Requirement / procedure | Pass criterion and evidence |
|---|---|---|
| E01 | DAC tone at low volume; verify amplifier/headphones and scope output | Correct 440 Hz output on both channels, no clipping; electrical/acoustic observation, not just TX acceptance |
| E02 | Raw live microphone/chestpiece path; apply repeatable transient and record source/output together | Audible signal, measured live latency <30 ms target; save waveform and measurement method |
| E03 | All three filters and volume controls; repeat identical tones/WAVs | Expected frequency responses, monotonic volume, mute at zero, no unsafe wraparound; retain gain and clipping statistics |
| E04 | BPM comparison per analysis filter on reference segments | Report MAE/RMSE/bias/max error and coverage; provisional target <=5 BPM MAE with >=90% valid windows on defined clean fixtures; report failures rather than discarding them |
| E05 | Noise, silence, constant carrier, clipped signal, change of source/analysis/mode | No valid stale BPM after acquisition reset; no FHIR send from invalid/test sources; report false-positive results on realistic noise |
| E06 | Capture maximum clip; replay at 100/75/50; return live; repeat and interrupt | Expected duration N/(16 kHz * speed), retained pitch within 2% on a 440 Hz reference, no buffer overrun; host tests plus captured DAC output |
| E07 | Press button/change filter while dashboard redraws and audio runs | Exactly one accepted stable transition; <=35 ms GPIO response; no persistent state divergence under event saturation; record scope and latency logs |
| E08 | Touch targets at corners/centre and each action row | Correct target/action per press and release, no repeats; update panel-specific calibration overlay if needed |
| E09 | Heart/lung, point and diagnostics modes | Lung = raw live/no BPM/replay/FHIR; point index retained; diagnostic colour/LED/backlight tests work; independent volume and brightness |
| E10 | Audio recovery: controlled stream fault or resource-starvation fault injection | RX/TX failure visible, bounded automatic restart (three attempts), clean buffers and manual restart; no tight loop/reset; unplugging a write-only DAC alone may not produce a driver error |
| E11 | Optional second SP3T fitted and combined controls | Verify all three contacts and simultaneous independent filter/speed operation; record extension wiring separately |
| E12 | Configured HAPI-FHIR endpoint behind TLS; valid microphone BPM | HTTP acceptance AND server readback matches Patient, LOINC, quantity, unit, measurement timestamp and resource ID |
| E13 | Wrong CA, wrong hostname, expired certificate, unset clock, network outage, 4xx/5xx | No successful transfer/readback for rejected cases; visible error; audio continues; explicit retry after restoration; no insecure fallback |
| E14 | >=10 min combined audio/filter/replay/display/touch/GPIO/ADC/logging; include TLS if configured | No unexpected restarts/dropouts/clipping, zero processing deadline misses, measured latency maintained, >=25% stack headroom in every thread/ISR |

For E07 event saturation, use a test image or debugger to temporarily stall the
consumer until the queue fills, then release it. Check current stable GPIO state
is eventually delivered. The policy reconciles state; it cannot reconstruct an
entire press/release that occurs while the consumer is stalled indefinitely.

Record stack high-water data with `qc.conf`; for network stress combine profiles:
`-DEXTRA_CONF_FILE="network.conf;qc.conf;/absolute/path/to/local-network.conf"`.
Use the actual returned thread names and ISR stack report. A successful link
only proves static memory fit; heap peaks and runtime headroom require this run.
I2S slab occupancy is a CPU-side diagnostic, not a replacement for oscilloscope
latency or driver FIFO measurements. Separate RX/TX errors include stream errors
without pretending every error has an unambiguous electrical cause.

Collect telemetry while physically exercising the controls (close other monitors):

```sh
python tools/evaluate.py record --port /dev/ttyUSB0 --seconds 600 \
  --operator "YOUR NAME" --wiring-revision "confirmed-base-2026-09-16" \
  --signal "fixture SHA256 or acoustic/reference description" \
  --firmware build-eval/zephyr/zephyr.bin --output results/combined
```

The supplied binary hash is recorded; the operator must confirm it is the image
actually flashed. This command does not flash, change controls or mark a test PASS.
The capture also saves `console.log` with latency and stack-analyzer messages.
Store scope/audio captures and signed verdicts alongside the telemetry manifest.

## Touch calibration

The dashboard uses the controller's 240x320 coordinate space; action rows are
192–223 (filter/speed), 224–255 (capture/replay), 256–287 (live/mode), 288–319
(point/brightness), with left/right split at x=120. Current devicetree min/max
values are inherited from the working assembly, not newly measured here.
Use diagnostics mode to inspect logged touch coordinates at the corners and
centre. If incorrect, obtain raw extrema in a calibration build with min=0,
max=4095, then update `min-x/max-x/min-y/max-y` and the driver's inversion/swap
properties in a local overlay according to the pinned XPT2046 binding. Rebuild,
verify all corners and record the resulting overlay; do not infer calibration
from a single touch. Serial commands remain available during calibration.

## FHIR test setup and readback

No host, port, Patient or Wi-Fi network is preconfigured. Once chosen, use a
non-production test Patient and provision a hostname-matching server certificate.
HAPI can sit behind a TLS reverse proxy. Firmware supports TLS 1.2 with
ECDHE-RSA/ECDHE-ECDSA AES-128-GCM and a PEM root CA embedded at build time.
Use a short chain that fits the configured 4096-byte TLS input record buffer,
or increase that buffer and repeat the memory/stack stress tests.

After explicit Wi-Fi connection, clock sync and `stetho net configure`, send a
valid microphone measurement using `stetho net send`. The log prints the
Observation ID, UTC measurement time and BPM. Validate the stored resource:

```sh
python tools/evaluate.py readback \
  https://YOUR-HOST/fhir/Observation/ID-FROM-LOG \
  --ca /path/to/root-ca.pem --patient YOUR-TEST-PATIENT \
  --bpm 72.5 --timestamp 2026-09-16T12:00:00Z --output results/fhir-readback.json
```

Substitute actual logged values. Optional authorization comes from the
`STETHO_FHIR_TOKEN` environment variable on the host. The readback client verifies
HTTPS and refuses plain HTTP. The operation reads an existing resource; it does
not create a test Patient or configure a remote server.

## Remaining scientific and physical limits

The INMP441's usable low-frequency band remains a hardware constraint. Separate
listening and analysis branches allow a fair shared-vs-separate-filter comparison;
they do not establish that any selected filter improves clinical recognition.
The BPM estimator is a reproducible starting point and can confuse double sounds,
irregular rhythms, motion and harmonics. WSOLA quality must be judged on heart
sounds as well as steady-tone pitch tests. Formal acoustic characterization,
clinical claims, permanent recording and manufacturing/regulatory validation are
outside this software upgrade.
