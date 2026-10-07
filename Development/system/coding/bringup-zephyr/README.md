# Digital stethoscope — evaluation firmware

Zephyr evaluation firmware for ESP32-S3-DevKitC-1 **N16R8** on carrier Rev A:
INMP441 microphone, PCM5102A DAC, ILI9341/XPT2046 display/touch, physical
controls and SD card. This implementation is separate from the
[proposed thesis design](../../README.md).

**Offline by default:** no Wi-Fi or FHIR transmission. The optional network
profile also boots without credentials, server configuration or automatic connection/send.

## Build

Install Python 3.12+ and Git, then run from the repository root:

```powershell
python Development/system/testing/ci/setup_zephyr.py
```

See [Windows/Linux setup and benchmarks](../../testing/BUILD-TIMES.md) for
prerequisites and a build without publication or flashing. In the activated
Zephyr environment, from this application directory:

```sh
west build --pristine -b esp32s3_devkitc/esp32s3/procpu . -d build-eval
```

Pinned Zephyr revision: 357467a011cd2557a1a3f0b4be83d817c4addc9b

Other tool pins live in [toolchain.json](../../testing/ci/toolchain.json).
[Build and flash](BUILD-GUIDE.md) covers profiles, console ports, memory sizing,
cloud downloads and build identity (`stetho version`). Hardware flashing, serial
and device-network operations require owner authorization.

## Basic use

Start with volume at minimum and a suitable headphone amplifier: the PCM5102A
is a line-output DAC. The potentiometer controls volume; the filter switch selects
Raw/Murmur/BPM and the speed switch selects 1×/0.75×/0.5× replay. Touch/shell
selection lasts until the next physical switch transition.

The button captures a volatile clip (default 5 seconds), or cancels capture/replay
and returns to live. Replay preserves pitch approximately; BPM continues using
new original-rate audio. Lung mode provides Raw live audio and refuses BPM,
replay and FHIR send. Test sources cannot be sent as FHIR.

Once connected to the authorized console, basic commands are:

```text
stetho status
stetho set filter 0
stetho capture
stetho replay
stetho live
```

The [operating guide](OPERATING-GUIDE.md) documents all controls, shell values,
SD mounting, test sources, clip semantics and telemetry limitations.

## Hardware and verification

Read the [signal map and electrical cautions](HARDWARE.md) before wiring.
The 2026-09-16 wiring confirmation predates the speed switch and SD mapping;
it does not validate this firmware. Record the actual board revision and check
GPIO/RGB-LED conflicts. Keep the existing backlight driver and LED current limiting.

Filter bands, BPM range and quality thresholds are engineering candidates.
The periodicity score is not clinical confidence; synthetic/host/build success
cannot establish physiological accuracy, physical latency or complete-load stack headroom.

- [Host DSP/FHIR tests](tests/host) and [evaluation tools](tools/evaluate.py)
- [Integrated physical acceptance and FHIR readback](EVAL-GUIDE.md)
- [Optional network setup and credential/TLS precautions](NETWORK.md)
- [Historical component protocol](TEST-PROTOCOL.md) and [hardware results](evidence/hardware-results.json)
- [Wiring confirmation](evidence/wiring-confirmation.json) and [integrated software evidence](evidence/integrated-build-results.json)

Historical component evidence is not automatically acceptance of this firmware.
Use annotated/reference signals and report invalid-result coverage with BPM error.

Updated by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
