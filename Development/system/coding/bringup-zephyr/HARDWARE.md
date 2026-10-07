# Evaluation hardware

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

The authoritative mapping is the [devicetree overlay](boards/esp32s3_devkitc_procpu.overlay). No existing
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

See the [operating guide](OPERATING-GUIDE.md) for SD mounting and controls.
The existing wiring was confirmed working on 2026-09-16; this is not acceptance
of the current firmware and excludes the later speed-switch/SD mapping.

Updated by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
