# Digital stethoscope — integrated evaluation firmware

ESP32-S3-DevKitC-1 **N16R8**, Zephyr, INMP441, PCM5102A, ILI9341/XPT2046,
potentiometer, illuminated button, filter and speed switches and the LCD module's
SD card, as wired on evaluation carrier Rev A. The existing evaluation wiring was
confirmed working by the user on **2026-09-16**; its signal assignments are
preserved. That confirmation is distinct from testing this new firmware, and it
predates the speed switch and SD card mapping.

The default build is **offline**: no Wi-Fi connection or FHIR transmission.
The optional network build also starts without credentials, server configuration
or automatic connection/transmission. Configure and connect explicitly when ready.

## Functions and controls

- 16 kHz, stereo 32-bit I2S; microphone left channel is duplicated to DAC L/R.
  128-frame blocks (8 ms), two silent TX priming blocks (16 ms), DMA in internal SRAM.
- Listening filters: Raw, initial Murmur candidate (40–800 Hz), initial BPM
  candidate (25–150 Hz). Second-order Butterworth HP + LP sections; 20 ms
  exponential crossfades. **These cutoffs are engineering candidates**, pending
  literature justification and evaluation, not established optimal filters.
- Independent analysis filter, 8-second rectified-envelope autocorrelation window,
  one update per second, provisional 30–200 BPM range and quality gating.
  The quality percentage is a periodicity score, not clinical confidence.
- Potentiometer: volume, 0–8× gain with a squared control curve, smoothing and
  saturation. Start at minimum. Brightness is a separate setting.
- Filter switch: positions 1/2/3 select Raw/Murmur/BPM. Touch or serial selection
  remains active until the next physical switch transition.
- Speed switch: positions 1/2/3 select 1.00×/0.75×/0.50× replay, with the same
  last-transition-wins rule. With no switch fitted all contacts read open and
  touch/serial stay in control.
- SD card: mounted read/write at `/SD:` when a FAT/exFAT card is inserted before
  boot. There is no card-detect line; after inserting later use `fs mount fat /SD:`.
  The firmware never formats a card. Browse with `fs ls /SD:`.
- Button: begin a volatile clip, or stop capture/replay and return to live.
  LED indicates active capture/replay. Default clip capacity: **5 seconds**.
- Touch dashboard: filter/speed, capture/replay, live/heart-lung, point/brightness.
  Positions are also selectable through the serial shell, independently of touch
  calibration. `point` is an operator-entered index 1–5 on screen, not an inferred
  anatomical location; record its anatomical meaning in each evaluation run.
- Replay: bounded recorded clip at 1× / 0.75× / 0.5× using waveform-similarity
  overlap-add (WSOLA), preserving pitch approximately. Ends at live playback.
  BPM always uses newly captured samples at the original sampling rate.
- Lung mode: live Raw listening, no BPM or replay, FHIR send refused.
- Diagnostics mode retains button/LED, potentiometer/backlight and colour tests.
- Sources: microphone, low-level 440 Hz tone, synthetic two-sound heartbeat,
  or a volatile host-uploaded PCM fixture. Test sources cannot be sent as FHIR.
- Display, audio and optional network work run in separate threads. Input
  events never wait for a full-screen redraw. Failed GPIO event delivery retries
  the latest stable state instead of losing synchronization permanently.

## Confirmed signal map

| Component | Signal | GPIO |
|---|---|---|
| INMP441 | SCK / WS / SD | 4 / 5 / 6 |
| PCM5102A | BCK / LRCK / DIN | 40 / 41 / 42 |
| SPI display + touch | SCK / MOSI / MISO | 12 / 11 / 13 |
| ILI9341 | CS / DC / RESET | 10 / 14 / 9 |
| Backlight | LEDC PWM control | 8 |
| XPT2046 | CS / PENIRQ | 7 / 15 |
| Button / button LED | input / output | 16 / 17 |
| Potentiometer | ADC1 channel 0 | 1 |
| Filter switch | Raw / Murmur / BPM | 18 / 21 / 38 |
| Speed switch (carrier J9) | 1.00× / 0.75× / 0.50× | 2 / 39 / 47 |
| SD card (LCD module, carrier J11) | CS; SCK / MOSI / MISO shared with SPI2 | 48 |

The authoritative mapping is `boards/esp32s3_devkitc_procpu.overlay`. No existing
signal pin was moved. GPIO38 also connects to the RGB LED on DevKitC-1 v1.1;
do not enable a competing RGB LED driver. Record the actual PCB revision.
GPIO35–37 must not be repurposed on the octal-PSRAM module; GPIO43/44 serve the
UART console and GPIO19/20 native USB. The map avoids boot-strapping pins.

Retain the confirmed module-level wiring: common GND; INMP441 VDD=3.3 V,
L/R=GND (left channel); PCM5102A SCK=GND for PLL operation, FMT/DEMP/FLT low,
XSMT high; use the supply voltage appropriate to the fitted DAC breakout.
Keep the existing backlight driver and LED current limiting. PCM5102A is a
line-output DAC: headphones require the appropriate amplifier stage in the
assembly, not a firmware gain setting as a substitute.

The speed switch (GPIO2/39/47, common GND) and SD chip select (GPIO48) are part
of the default build because carrier Rev A wires them. Neither is **covered by
the wiring confirmation** yet. GPIO39 cannot also serve an external JTAG probe.
Firmware expects three positions with exactly one active contact; check the
physical contact truth table of the fitted switch.

The SD card uses SPI mode on the display/touch bus. Its chip select is the third
`cs-gpios` entry, so the SPI driver holds GPIO48 high from boot even when no card
is fitted; the carrier adds a 10 kΩ pull-up (R20) for the time before that. Each SD
request locks the bus, so display redraws and touch reads wait for it. GPIO48
also drives the RGB LED on DevKitC-1 v1.0: keep any LED strip driver disabled.

## Build and flash

For reproducible setup on Windows/Linux and build-time comparison across devices,
see [Build-time analysis](../../testing/BUILD-TIMES.md). The shared setup installs
pinned tools in `.ci-workspace`; the benchmark records clean-build timings, logs
and machine metadata without publishing or flashing firmware.

### Homelab cloud downloads

On the configured homelab, use the repository's
`python Development/system/testing/ci/run_ci.py build` entry point from the repository root
with the Zephyr Python environment activated. After all three profiles succeed, it publishes
their `zephyr.bin` outputs to
[Personal Cloud → Firmware](https://homelab-server.tail15fafc.ts.net:8443/#firmware) in the
`local` group, replacing the previous local build once every profile has uploaded. Downloads require Tailscale and cloud sign-in. Firmware is not flashed automatically.

GitHub builds arrive there too, grouped by source: add the `firmware` label to a PR to publish
a build of every push (`PR #N`, newest only, deleted when the PR closes), use *Run workflow*
for any branch, and `integration` is built daily when it has changed (newest only). See
`Development/system/testing/CI-QUALITY-GATES.md`.

Each image identifies itself. The first console line after Zephyr's banner, and the shell
command `stetho version`, print the build identity, which is also the cloud version string:

```text
Digital Stethoscope firmware pr-12 1a2b3c4d5e6f+merge qc 20261002T031705Z
```

That is channel, the first 12 characters of the source commit (`+merge`: a PR build of GitHub's
merge into the base branch; `-dirty`: uncommitted tracked changes), profile and UTC build time.
`run_ci.py` supplies it as `-DSTETHO_BUILD_ID`; a direct `west build` prints `local`.

This integration uses the installed `cloud-publish` command and a separate upload-only credential
in the build user's `~/.config/personal-cloud/publisher.token`. Keep that credential outside the
repository. Hosted GitHub Actions skips publication; other machines without `cloud-publish`
retain normal local builds. Publishing failures fail the command visibly. Direct `west build`
commands below do not publish automatically; append `&& cloud-publish --project 'Digital
Stethoscope' --version BUILD_VERSION --board esp32s3_devkitc/esp32s3/procpu path/to/zephyr.bin`
when publishing a manually built variant. Supply `--commit` to record source provenance; such
uploads appear under *Earlier builds*, without a channel.

### Toolchain and commands

Pinned Zephyr revision: 357467a011cd2557a1a3f0b4be83d817c4addc9b

Pinned hal_espressif revision: 3d4d922a4d2994f844790ec031a584ec71240485

Zephyr SDK 1.0.1; west 1.5.0. See `Development/system/testing/ci/setup_zephyr.sh`
for a fresh workspace. Work from an activated Zephyr environment (Python 3.12+,
CMake, Ninja, esptool >=5.0.2, Espressif binary blobs). Commands below assume the
current directory is this application:

```sh
west build --pristine -b esp32s3_devkitc/esp32s3/procpu . -d build-eval
west flash -d build-eval --esp-device /dev/ttyUSB0
west espressif monitor -p /dev/ttyUSB0
```

On Windows substitute `COM6` or the actual UART bridge port. Only one monitor or
host evaluation script may own the port at a time; console is 115200 baud.
Use the UART socket for flashing/console and the already verified power setup.

Profiles:

```sh
# Stack measurement under simultaneous workload
west build --pristine -b esp32s3_devkitc/esp32s3/procpu . -d build-qc -- -DEXTRA_CONF_FILE=qc.conf

# Optional network capability; still disconnected/unconfigured at boot
west build --pristine -b esp32s3_devkitc/esp32s3/procpu . -d build-network -- -DEXTRA_CONF_FILE=network.conf
```

The overlay/config now describe 16 MB flash and 8 MB octal PSRAM. The clip and
fixture arrays use external RAM; the I2S slabs stay in DMA-capable internal RAM.
The default 5-second arrays use 160 kB each. Change `CONFIG_STETHO_CAPTURE_SECONDS`
(1–20) to resize both. `CONFIG_STETHO_POT_MAX_MV=3100` sets volume full scale;
calibrate against the physical ADC sweep (historical maximum was 3083 mV).

## Serial shell

```text
stetho status
stetho set filter 0
stetho set analysis 2
stetho set speed 75
stetho capture
stetho replay
stetho live
stetho restart
stetho set heart 0
stetho set heart 1
stetho set point 0
stetho set brightness 80
stetho set diagnostics 1
stetho color 3
stetho set diagnostics 0
```

`filter` and `analysis`: 0 Raw, 1 Murmur, 2 BPM. `speed`: 100, 75, 50.
`point`: 0–4. `volume`/`brightness`: 0–100. `heart`/`diagnostics`/`pot`: 0 or 1.
To control volume by shell, first issue `stetho set pot 0`; restore `pot 1`
afterward. Pot volume is otherwise sampled every 100 ms.

```text
stetho set pot 0
stetho set volume 10
stetho set source 1
stetho set source 2
stetho set bpm 72
stetho set source 0
```

Sources: 0 microphone, 1 low-level tone, 2 synthetic heart, 3 uploaded fixture.
Generated signals enter the **same** filtering, BPM and output path as the mic.
A failed microphone probe does not prevent DAC test-source operation.
A source/analysis/mode/reference-rate change resets BPM acquisition and cancels
active capture/replay. Filter and volume changes are smoothed. Clip capture stores
filtered audio before volume. Replaying a clip uses its recorded filter; changing
the live filter does not reprocess that clip. Capture a new clip for comparison.
At slow speed incoming live samples continue serving BPM but do not accumulate
an unbounded playback queue. Stop/restart interrupts the current clip operation.

`stetho status` returns one JSON object suitable for host collection: levels in
parts per million of digital full scale, clipping totals, processing maximum,
8 ms deadline misses, RX/TX/allocation failures, slab usage, recovery totals,
BPM validity/quality, clip status and network result. Slab usage is **not** an exact
hardware FIFO depth. RX/TX error counters include driver-reported stream failures;
the Zephyr API does not distinguish every physical underrun/overrun cause.
Counters are cumulative since boot. Processing time excludes blocking I/O;
measure end-to-end acoustic/electrical latency separately.

## Wi-Fi and FHIR (optional)

No server, test Patient, credentials or CA has been chosen. There is no default
connection and no automatic send. Configuration and tokens live only in RAM;
shell command history is disabled. Credentials entered on the console can still
appear in terminal captures, so enter them outside evaluation logging.

When the test server is chosen, add a local, untracked configuration file:

```text
CONFIG_STETHO_CA_FILE="/absolute/path/to/public-root-ca.pem"
```

Build with `-DEXTRA_CONF_FILE="network.conf;/absolute/path/to/local-network.conf"`.
Only the **public root certificate** is embedded. The network profile accepts
TLS 1.2 ECDHE-RSA/ECDHE-ECDSA AES-128-GCM certificates/ciphersuites. Hostname,
certificate chain and dates are verified; no insecure fallback exists.

Connect explicitly using Zephyr's `wifi connect` command (see `wifi connect -h`
for SSID/security/key options). Then configure and synchronize the clock:

```text
stetho net configure fhir.example.test 443 /fhir test-patient
stetho net sync your-time-server.example.test
stetho net send
```

Alternatively `stetho net time UNIX_SECONDS` sets the current UTC time locally.
SNTP is unauthenticated, so use a trusted lab time source. Optional bearer token:
`stetho net token TOKEN`. Reset clears all runtime configuration.

Sending requires a running microphone source, heart mode, a valid recent BPM
result, current clock and configured CA/server/Patient. It freezes that result
and its measurement time into a FHIR R4 heart-rate Observation (LOINC 8867-4,
UCUM `/min`, vital-signs category). A low-priority worker issues a TLS PUT to a
boot/measurement-specific resource ID. Explicitly retrying the same measurement
uses the same ID; there is no automatic retransmission or retry storm. Server
must support client-assigned Observation IDs. HTTP 200/201 is transport acceptance;
use the host readback tool to prove stored content. Network loss or TLS failure
is reported without stopping audio. See `EVAL-GUIDE.md` for negative tests.

## Verification and evidence

- `tests/host`: the exact portable DSP/FHIR C implementation compiled on the host.
- `tools/evaluate.py`: WAV generation/comparison, serial fixture upload, structured
  telemetry capture and verified HTTPS FHIR server readback.
- `EVAL-GUIDE.md`: requirement-to-test mapping and integrated hardware protocol.
- `TEST-PROTOCOL.md` / `evidence/hardware-results.json`: historical component
  evidence; it is not automatically promoted to this firmware.
- `evidence/wiring-confirmation.json`: the user's current wiring confirmation.
- `evidence/integrated-build-results.json`: software verification for this upgrade.

Host/build tests cannot establish headphone output, physiological accuracy,
physical input latency or stack headroom under the complete workload. In
particular, periodicity-based BPM can confuse S1/S2, harmonics, motion and noise.
Use annotated/reference signals and report invalid-result coverage along with
error; do not report synthetic-test success as clinical validation.
