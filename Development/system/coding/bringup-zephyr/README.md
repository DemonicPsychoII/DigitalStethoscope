# Zephyr Hardware Bring-up — Digital Stethoscope

Combined test app to verify **all components work** before the thesis starts:
pushbutton + LED, one SP3T 3-way switch, INMP441 microphone, PCM5102A DAC,
ILI9341 display with touch, and the potentiometer. Also serves as the hands-on
Zephyr trial run (decision C vs. Zephyr, see `preThesis/01-aufgabenbeschreibung`).

Board target: **`esp32s3_devkitc/esp32s3/procpu`** (ESP32-S3-DevKitC-1, N16R8).

## Behavior

At boot every peripheral of the pin map is probed, **one try plus 3 retries**
each. Only the peripherals that answer are enabled afterwards — a missing part
never blocks the rest of the test.

| Peripheral | Presence check | Enabled behavior |
|---|---|---|
| Pushbutton + LED | GPIO controller ready, pins configurable | each press **toggles** the button LED |
| SP3T switch | one throw is pulled low (common pole on GND) | position reported in the status line |
| Potentiometer | ADC ready + one successful conversion | dims the display backlight |
| Backlight (LEDC) | PWM ready + duty accepted | driven by the poti, otherwise 100 % |
| Display ILI9341 | driver ready, capabilities sane, blanking off | shows a solid colour |
| Touch XPT2046 | driver ready (SPI transfer at init) | each touch **rotates** to the next colour |
| Mic INMP441 | an I2S RX block is read and its samples are not constant | audio source |
| DAC PCM5102A | I2S TX configured, block queued, stream started | mic audio is looped through to it |

Mic and DAC are only started together: the loopback thread stays unstarted if
either of them is missing.

### Console output (PuTTY, 115200 8N1)

1. A one-shot probe report listing the connected peripherals and, for the
   missing ones, the errno plus a wiring hint.
2. Then a status line **every 500 ms** containing only the connected
   peripherals, e.g.
   `btn=0 led=1 | sw=2 | poti=1780mV | backlight=53% | colour=blue | touch=4@118,203 | audio blocks=812 errs=0 peak=91 |`
3. If **no** peripheral answered at all, no status line is produced — a single
   static message is repeated every 5 s instead:
   `no peripherals connected - check wiring and power, then reset`

> The mic check rejects a block whose 32-bit samples are all identical (an
> unwired SD line). A powered INMP441 always dithers, so this only misfires if
> the mic is muted at the hardware level.

> Exactly **one** SP3T is wired (4-pin type: 1 common + 3 throws). Both SP3T of
> the final device are the identical part, so testing one covers both; which of
> them ends up selecting the filter and which the playback speed is not decided
> by this bring-up. The position labels below are the filter naming, used only
> as an example.

---

## 1. Pin map

Matches the overlay. The firmware builds and runs on the board; the per-component
state is tracked in §4.

### Pushbutton, switch, potentiometer

| Component | Signal | ESP32-S3 GPIO |
|---|---|---|
| Pushbutton | switch → GND | **GPIO16** (pull-up) |
| Pushbutton | LED (+ series resistor) | **GPIO17** |
| SP3T switch | common → GND | — |
| SP3T switch | pos 1 (Raw) | **GPIO18** (pull-up) |
| SP3T switch | pos 2 (Murmur) | **GPIO21** (pull-up) |
| SP3T switch | pos 3 (BPM) | **GPIO38** (pull-up) |
| Potentiometer | wiper | **GPIO1** (ADC1_CH0) |
| Potentiometer | ends | 3V3 / GND |

### INMP441 microphone (I2S0, RX)

| INMP441 | ESP32-S3 |
|---|---|
| VDD | **3V3** (not 5V) |
| GND | **GND** |
| SCK (bit clock) | **GPIO4** |
| WS / LRCLK | **GPIO5** |
| SD (data out) | **GPIO6** |
| L/R | **GND** → left channel |

### PCM5102A / WCMCU-5102 DAC (I2S1, TX)

| Module pin | ESP32-S3 | Note |
|---|---|---|
| VIN | **5V** | board has a 3.3 V regulator |
| GND | **GND** | |
| SCK | **GND** | ⚠️ enables the internal PLL — floating = silence |
| BCK | **GPIO40** | |
| LCK (LRCK) | **GPIO41** | |
| DIN | **GPIO42** | |
| FLT / DEMP / FMT | **GND** | |
| XSMT (silkscreen often `XMT`) | **3V3** | active low — LOW mutes everything |
| L / R / G | jack tip / ring / sleeve | mono signal duplicated to both channels |

Output is line level (2.1 V<sub>RMS</sub>), not headphone drive — a buffer stage
remains an open hardware item.

### ILI9341 display + XPT2046 touch (SPI2)

| Signal | ESP32-S3 |
|---|---|
| SCK (shared) | **GPIO12** |
| MOSI / SDI (shared) | **GPIO11** |
| MISO / SDO (shared) | **GPIO13** |
| Display CS | **GPIO10** |
| Touch CS | **GPIO7** |
| DC | **GPIO14** |
| RESET | **GPIO9** |
| Backlight LED (**PWM**, LEDC ch0) | **GPIO8** |
| Touch PENIRQ | **GPIO15** |

SCK/MOSI/MISO go to *both* halves of the module; only the CS lines are separate.

> ⚠️ **Backlight current.** The `LED` pin often drives 3–4 parallel LEDs
> (40–60 mA). Measure it before connecting to GPIO8 — above ~10 mA use a small
> N-MOSFET (2N7002/BSS138) with its gate on GPIO8.

> **Reserved on N16R8 — do NOT use:** GPIO33–37 (octal PSRAM), GPIO26–32 (flash),
> GPIO43/44 (UART console), GPIO19/20 (USB), GPIO0/3/45/46 (strapping).
> GPIO22–25 do not exist on the S3. None are used above.

> **DevKitC-1 revision.** On **v1.1** the onboard RGB LED sits on GPIO38 (v1.0:
> GPIO48). The switch input still works because the WS2812 data pin is high
> impedance, but if position 3 misbehaves, move it to GPIO48.

Change pins in `boards/esp32s3_devkitc_procpu.overlay`, then rebuild.

---

## 2. Toolchain

Installed under `Development/system/coding/tools/zephyrproject`:

| Component | Version |
|---|---|
| Python (venv interpreter) | 3.12.10 |
| west | 1.5.0 |
| Zephyr SDK | 1.0.1 (`xtensa-espressif_esp32s3_zephyr-elf` only) |
| CMake / Ninja / 7-Zip | 4.4.2 / 1.13.2 / 26.02 |
| esptool | 5.3.1 |

> Keep this folder out of version control — it is ~50k files. It is git-ignored
> and recreated by `Development/system/coding/tools/setup-toolchain.ps1`:
>
> ```powershell
> .\Development\system\coding\tools\setup-toolchain.ps1
> ```
>
> The script performs every step below automatically and is idempotent. The
> manual procedure is kept here as reference and for troubleshooting.

One-time setup (prerequisites installed separately: Python 3.12, CMake, Ninja,
7-Zip, git):

```powershell
$zp = "C:\SVN\DigitalStethoscope-B.Thesis-\Development\system\coding\tools\zephyrproject"

py -3.12 -m venv "$zp\.venv"
& "$zp\.venv\Scripts\Activate.ps1"
pip install west

Set-Location $zp
west init .
west update --narrow -o=--depth=1
pip install -r "$zp\zephyr\scripts\requirements.txt"
west zephyr-export
west blobs fetch hal_espressif          # REQUIRED for ESP32 targets
west packages pip --install             # pulls esptool >= 5.0.2

west sdk install -t xtensa-espressif_esp32s3_zephyr-elf -d "$zp"
```

Windows quirks worth knowing:

- `west init` can abort with `PermissionError` while cleaning up
  `.west\manifest-tmp` (file lock from AV/indexer). The clone itself is fine —
  delete that temp folder and write `.west\config` by hand:
  `[manifest]` / `path = zephyr` / `file = west.yml`.
- `west zephyr-export` must run **after** `pip install -r requirements.txt`,
  otherwise it dies on a missing `jsonschema`.
- The SDK ships as `.7z`; without 7-Zip on PATH the install aborts inside
  patoolib. If `west sdk install` still cannot launch the setup script, run
  `zephyr-sdk-1.0.1\setup.cmd /c` and `setup.cmd /t <toolchain>` directly.

---

## 3. Build, flash, monitor

Everything in one paste — environment, build, flash, monitor:

```powershell
$zp  = "C:\SVN\DigitalStethoscope-B.Thesis-\Development\system\coding\tools\zephyrproject"
$app = "C:\SVN\DigitalStethoscope-B.Thesis-\Development\system\coding\bringup-zephyr"
& "$zp\.venv\Scripts\Activate.ps1"; $env:ZEPHYR_BASE = "$zp\zephyr"; Set-Location $app
west build -b esp32s3_devkitc/esp32s3/procpu . ; west flash --esp-device COM6 ; west espressif monitor -p COM6
```

Or step by step. Every new terminal session:

```powershell
$zp  = "C:\SVN\DigitalStethoscope-B.Thesis-\Development\system\coding\tools\zephyrproject"
$app = "C:\SVN\DigitalStethoscope-B.Thesis-\Development\system\coding\bringup-zephyr"
& "$zp\.venv\Scripts\Activate.ps1"
$env:ZEPHYR_BASE = "$zp\zephyr"
Set-Location $app
```

Then:

```powershell
west build -b esp32s3_devkitc/esp32s3/procpu .
west flash --esp-device COM6
west espressif monitor -p COM6      # quit with Ctrl+]
```

Add `--pristine` to the build **only** after changing the overlay or `prj.conf`.
For plain `main.c` edits the incremental build is much faster.

Find the port if it moves — the ESP32 is the one with `CH343` in its name:

```powershell
Get-CimInstance Win32_PnPEntity | ? Name -match "COM\d+" | Select Name
```

PuTTY works as a monitor too: `Serial`, `COM6`, `115200`. Only one program may
hold the port — close PuTTY before flashing.

### Which USB socket

The DevKitC-1 has two USB-C sockets:

| Socket | Purpose |
|---|---|
| **`UART`** | flashing + console (CH343 bridge → GPIO43/44) |
| `USB` | native USB; **use it as a second power feed** |

Both sockets feed the same 5 V rail through separate diodes, so plugging in
**both cables at once is safe and recommended**: the display backlight alone can
brown out the board when it is powered through the `UART` socket only. A
brownout looks exactly like broken hardware — dark LEDs, blank display, and the
COM port vanishing mid-session.

### Troubleshooting

| Message / symptom | Cause | Fix |
|---|---|---|
| `Could not open COM6, the port is busy` | PuTTY or a monitor still attached | close it |
| `...or doesn't exist` | board not on `UART`, or it dropped off the bus | re-plug; add the second cable for power |
| `No serial data received` | esptool cannot enter the bootloader | hold **BOOT**, tap **RST**, release **BOOT**, retry |
| Flash succeeds but console stays silent | board stayed in the bootloader | tap **RST** once |
| Console floods with one repeated warning | a driver is spamming faster than 115200 can drain | raise that subsystem's log level in `prj.conf` |

---

## 4. Bring-up status and test order

The firmware probes every peripheral at boot (one try plus 3 retries) and prints
an explicit report:

```
---- peripheral probe: 5 of 8 connected (max 3 retries each) ----
[ OK ] pushbutton + LED (GPIO16/17)  (attempt 1)
[ -- ] mic INMP441      (I2S0)  not connected (err -61) - check BCLK/WS/SD and L/R to GND
```

Only the peripherals listed as `[ OK ]` are enabled. Afterwards their live state
is logged every 500 ms, again only for what is connected:

```
btn=0 led=1 | sw=2 | poti=2942mV | backlight=89% | colour=blue | touch=4@118,203 |
```

If the probe finds nothing at all, the status line is suppressed and this static
message repeats every 5 s instead:

```
no peripherals connected - check wiring and power, then reset
```

> A `[ OK ]` for the display proves only that the driver could send its init
> sequence. ILI9341 over MIPI-DBI is write-only, so it reports success even with
> no panel attached. Trust the colour on the panel instead.

### Status as of the first hardware session

| Component | State |
|---|---|
| Console, ADC, boot | ✅ |
| Pushbutton + LED | ✅ |
| Potentiometer | ✅ full swing over the whole travel |
| SP3T positions 1 + 2 | ✅ |
| Display + backlight | ✅ (only when adequately powered) |
| SP3T position 3 (GPIO38) | ❌ open — devicetree verified correct, so wiring or pin |
| INMP441 microphone | ❌ open — `i2s_read` returns `-EIO` |
| PCM5102A DAC, touch | not yet verified |

### Test order

1. **Boot + console** — expect the `=== Stethoscope hardware bring-up ===` banner.
2. **Probe report** — note which peripherals report `[ -- ]` and why.
3. **Button + LED** — each press toggles the LED; `led=0/1` in the status line.
4. **Switch** — flipping the SP3T changes `sw=1/2/3`.
5. **Potentiometer** — `poti=…mV` sweeps and dims the backlight.
6. **Display** — a solid colour fills the panel.
7. **Touch** — every touch rotates to the next colour and increments `touch=…`.
8. **Audio** — tap near the INMP441; hear it on the PCM5102A output and watch
   `peak=…` react.

---

## 5. Devicetree notes

Things that already broke the build once and would break it again after a
Zephyr upgrade:

- **`/zephyr,user` holds the ad-hoc GPIO/PWM/ADC references.** Plain nodes
  without a `compatible` have no binding, so `gpios` specifier cells never
  resolve and every `_VAL_pin` macro goes missing.
- **The ILI9341 is a `mipi-dbi` bus device**, so it hangs off a
  `zephyr,mipi-dbi-spi` controller (`spi-dev = <&spi2>`), *not* off `&spi2`
  directly. Needs `CONFIG_MIPI_DBI=y`.
- **The label `touch` is taken** by the SoC's built-in touch sensor node — the
  XPT2046 uses `touchscreen`.
- **I2S needs GDMA**: `CONFIG_DMA=y` *and* `&dma { status = "okay"; }`.
- **`gpio0` covers GPIO0–31 only.** GPIO32–48 live on `gpio1` with
  `index = GPIO − 32`, so GPIO38 is `<&gpio1 6>`.
- **ADC attenuation is expressed as gain**: `ADC_GAIN_1_4` = 12 dB = 0–3.1 V.
  `ADC_GAIN_1` would clip the poti at ~1.1 V.

Still unverified against real hardware:

- I2S pinmux macros (`I2S0_I_BCK_GPIO4`, `I2S1_O_BCK_GPIO40`, …) and
  `LEDC_CH0_GPIO8` — they compile, but the routing is untested.
- XPT2046 calibration: `min-x/max-x/min-y/max-y` are placeholders.
- SPI runs at 10 MHz for bring-up; raise it once the image is stable.
- INMP441 sends 24-bit data in a 32-bit slot; the loopback passes the left
  channel through and duplicates it to both DAC channels.

## 6. Runtime pitfalls

Two independent bugs made the console look completely dead. Both are fixed, but
the failure mode is worth remembering:

- **Never busy-loop in a driver thread.** The audio thread runs at priority 5;
  the deferred logging thread at 14. A `continue` without `k_msleep()` in the
  `i2s_read()` error path starved the logger permanently — not one byte was
  emitted, not even the boot banner. `CONFIG_LOG_MODE_IMMEDIATE=y` now makes
  logging independent of thread scheduling.
- **A floating interrupt pin can saturate the console.** An unconnected PENIRQ
  produced ~34 KB of `input: Event dropped` warnings every 3 s — exactly 100 %
  of the 115200 link. Real log lines never got through. Fixed with an internal
  pull-up on the pin plus `CONFIG_INPUT_LOG_LEVEL_ERR=y`.

Both looked identical from the outside: a silent board. When the console goes
quiet, capture **raw bytes** rather than decoded lines — the byte count alone
tells you whether the chip is mute or drowning.

### Known configuration gaps

| Symbol | Current | Should be (N16R8) |
|---|---|---|
| `CONFIG_ESPTOOLPY_FLASHSIZE` | `"2MB"` | `16MB` |
| `CONFIG_ESP_SPIRAM` | not set | `y` (8 MB octal PSRAM) |

Irrelevant for bring-up, but the audio buffers and the TLS handshake heap will
need both.

---

## Files

```
bringup-zephyr/
├── CMakeLists.txt
├── prj.conf
├── boards/
│   └── esp32s3_devkitc_procpu.overlay
└── src/
    └── main.c
```
