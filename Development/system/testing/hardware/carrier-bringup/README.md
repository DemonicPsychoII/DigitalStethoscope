# Eval carrier peripheral test

Minimal Zephyr firmware that checks each peripheral of the evaluation carrier on its own and
logs every driver result on the UART console. Use it to tell a board fault from an application
fault before debugging the [app](../../../coding/app/README.md) or the archived
[bring-up firmware](../../../../../preThesis/06-bringup-zephyr/README.md). It is a developer
aid; it records no test evidence and does not replace the owner-run target procedures.

## Board and pin map

ESP32-S3-DevKitC-1 v1.0 (N16R8) on the `DigitalStethoscope_Eval` carrier. The pin map comes
from the Eval schematics at Altium commit `a8f23a2` (production package of 13 October 2026),
read from the `.SchDoc` net labels, ports and wires.

| Part | Signal | ESP32-S3 | Carrier detail |
| --- | --- | --- | --- |
| J3 INMP441 | SCK / WS / SD | GPIO4 / 5 / 6 | L/R to GND (left slot), R1 100k pull-down on SD |
| J4 PCM5102A | BCK / LRCK / DIN | GPIO40 / 41 / 42 | SCK, FMT, FLT, DMP to GND (PLL mode); XSMT high via R2 |
| J6 button | contact | GPIO16 | R11 pull-up, closes to GND |
| J6 button LED | anode | GPIO17 | R12 330 Ω, active high |
| J7 potentiometer | wiper | GPIO1 (ADC1 channel 0) | R13 1k, C8 100 nF; ends at 3V3 and GND |
| J8 filter switch | footprint pads 1 / 2 / 3 / 4 | GND / GPIO18 / GPIO21 / GPIO38 | R14–R16 pull-ups |
| RGB status light | WS2812 data | GPIO48 (SPI3 MOSI) | shares the unused SD_CS net (R20 pull-up) |

### J8 as fitted

The footprint expects the switch common on pad 1. The fitted SP3T slide switch has its common
on part pin 2, so the common lands on the GPIO18 pad and the throws on GND, GPIO21 and GPIO38.
Pad-link scan on 10 November 2026 (this firmware, board above):

| Position | Measured connection | Decoded as |
| --- | --- | --- |
| 1 | GPIO18 to GND | Raw |
| 2 | GPIO18 to GPIO21 | Murmur |
| 3 | GPIO18 to GPIO38 | BPM |

Each slide breaks contact for 10 to 20 ms. The firmware reads Raw directly, otherwise drives
GPIO18 low for 20 µs and reads which pad follows, and debounces for 30 ms. Only low is driven.
Decoding J8 in firmware for this board is Nico's decision of 10 November 2026.

## What it does

- **Boot pin probe:** reads each input with the internal pull-up and then pull-down. 1/1 means an
  external pull-up, 0/0 a contact to GND, 1/0 that the pin follows the internal pull.
- **Button LED:** blinks three times at boot, then lights while the button is held.
- **Potentiometer:** logged in millivolts; it sets the white brightness of the RGB status light.
- **Microphone:** I2S0 receive, 16 kHz, two 32-bit slots. Per second: blocks, errors, minimum,
  maximum, mean and AC RMS of both slots; raw words every 5 s.
- **DAC:** I2S1 transmit. Default is microphone passthrough: left slot, one-pole DC blocker
  (about 20 Hz), gain ×16 with saturation, both channels, muted for the first second while the
  INMP441 settles. Per second: blocks, slab, FIFO and clipping counters.

Shell commands on the console (115200 baud):

```text
carrier loopback [gain 1..256]   microphone passthrough, optional gain
carrier tone <Hz> [percent]      sine on both DAC channels
carrier silence                  zeros on the DAC
carrier led <on|off|button>      button LED mode
carrier probe                    repeat the boot pin probe
carrier status                   one-line counters
```

## Build and flash

From the repository root, with the pinned toolchain from
[`setup-toolchain.ps1`](../../../coding/tools/setup-toolchain.ps1):

```powershell
Development/system/testing/hardware/carrier-bringup/build.ps1 -Pristine         # -> build-carrier/
Development/system/coding/tools/flash-firmware.ps1 4 -BuildDir build-carrier   # COM4
```

The build lives here rather than as a `build-firmware.ps1` target, so `coding/` keeps no
reference to testing material.

Flashing writes only the image from offset 0; the settings and server profile partitions stay.
Flash the app again afterwards for normal use.

## Results of 10 November 2026

Board above, this firmware. Counters are from the serial log; perception is Nico's report.

| Part | Result |
| --- | --- |
| Button | Debounced presses and releases logged |
| Button LED | Boot blink commands accepted; lighting while held not separately reported |
| Potentiometer and RGB light | Sweep 0 to 3083 mV; brightness follows (Nico) |
| Microphone | 112 000 blocks without an error; left slot varies, right slot zero |
| DAC | 440 Hz full-scale tone heard (Nico); 112 006 blocks without an error |
| Passthrough | Sounds good (Nico); 57 629 blocks, 5 FIFO underruns at start, no overruns |
| J8 | Three positions as in the table above (pad-link scan); the decoder read Murmur at boot, a full slide through all positions is still open |

The bring-up firmware stopped its audio about 19 s after boot on the same board, after a block
processing time of 11.8 ms against the 8 ms block period and a failing restart. This firmware
streamed on the same pins without errors, so that failure belongs to the bring-up firmware.
