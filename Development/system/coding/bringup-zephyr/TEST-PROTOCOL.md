# Hardware Test Protocol — ESP32-S3 Bring-up

Test record for the digital stethoscope bring-up firmware. Start from a **bare
ESP32-S3-DevKitC-1 (N16R8)** with nothing wired, then add one component per test
case in the given order. Every test case is self-contained: wiring → build/flash
→ monitor → expected log → paste field → verdict.

- Tester: Nico F.
- Date: 14.08.2026
- Board / revision: ESP32-S3-DevKitC-1 N16R8, rev v1.___
- COM port: COM6
- Firmware commit: `2cd6d4c818be92f0bf1e1181ef0b4cd7de7ceb14` (retrospective mapping; commit created 15.08.2026, no flashed-binary hash was captured)
- Zephyr revision: `357467a011cd2557a1a3f0b4be83d817c4addc9b`
- Zephyr SDK: 1.0.1

**Legend for the verdict field:** `PASS` = works as specified · `PARTIAL` = works
with a caveat (document it) · `FAIL` = does not work · `BLOCKED` = could not test.

## Machine-readable traceability

The authoritative normalized record is `evidence/hardware-results.json`,
validated by `evidence/hardware-results.schema.json`. Its first record imports
this 14.08.2026 session under firmware commit `2cd6d4c...` with an explicit
retrospective-traceability warning. The record keyed
`39a94db...+working-tree` contains the 19.08.2026 refactor evaluation; every
physical T00–T10 verdict is `BLOCKED` because that working tree was not flashed.

`PASS` in native_sim or a cross-build never upgrades a physical verdict. A new
hardware run must use a committed firmware image and add a record containing
the commit, date, tester, exact board revision, Zephyr revision, SDK version,
test ID, verdict and captured log/measurement evidence.

---

## 0. Standing setup (do once per session)

Open PowerShell and set up the environment:

```powershell
$zp  = "C:\SVN\DigitalStethoscope-B.Thesis-\Development\system\coding\tools\zephyrproject"
$app = "C:\SVN\DigitalStethoscope-B.Thesis-\Development\system\coding\bringup-zephyr"
& "$zp\.venv\Scripts\Activate.ps1"
$env:ZEPHYR_BASE = "$zp\zephyr"
Set-Location $app
```

Build and flash (repeat after every wiring change — the firmware probes only at
boot, so **a reset is mandatory after re-wiring**):

```powershell
west build --pristine -b esp32s3_devkitc/esp32s3/procpu .
west flash --esp-device COM6
```

Open the console — either the Zephyr monitor or PuTTY:

```powershell
west espressif monitor -p COM6      # quit with Ctrl+]
```

PuTTY: `Session → Serial`, Serial line `COM6`, Speed `115200`, 8N1, no flow
control. Enable `Window → Logging → All session output` to a file so the log can
be pasted into this document.

> Only one program may hold the COM port. **Close PuTTY before flashing.**
> Plug **both** USB-C cables (`UART` + `USB`) — the backlight can brown out the
> board on a single feed, and a brownout looks exactly like broken hardware.

Rules that apply to every test below:

- **Power off** the board before changing wiring.
- Reserved pins, never use: GPIO26–32 (flash), GPIO33–37 (octal PSRAM),
  GPIO43/44 (console), GPIO19/20 (USB), GPIO0/3/45/46 (strapping).
- A component that is not wired reports `[ -- ]` in the probe report and is
  simply skipped — it never blocks the other tests.

---

## T00 — Boot and console (bare board, no wiring)

**Goal:** the toolchain, flashing and the serial console work on an empty board.

**Wiring:** none. Only the `UART` USB-C cable.

**Steps**

1. Flash the firmware.
2. Open PuTTY (115200 8N1).
3. Tap **RST** once.

**Expected log**

```
*** Booting Zephyr OS build ... ***
[00:00:00.xxx,000] <inf> bringup: === Stethoscope hardware bring-up ===
[00:00:0x.xxx,000] <inf> bringup: ---- peripheral probe: 0 of 8 connected (max 3 retries each) ----
[00:00:0x.xxx,000] <wrn> bringup: [ -- ] pushbutton + LED (GPIO16/17)  not connected (err -19) - ...
... (7 more [ -- ] lines) ...
[00:00:0x.xxx,000] <inf> bringup: no peripherals connected - check wiring and power, then reset
```

The idle message then repeats every 5 s. Backlight PWM may already report
`[ OK ]` without wiring — it is an on-chip peripheral.

**Log output**

```text
ESP-ROM:esp32s3-20210327
Build:Mar 27 2021
rst:0x1 (POWERON),boot:0x8 (SPI_FAST_FLASH_BOOT)
SPIWP:0xee
mode:DIO, clock div:1
load:0x3fc90710,len:0x3158
load:0x40374000,len:0xc6fc
load:0x50000000,len:0x24
SHA-256 comparison failed:
Calculated: 0e4b74c9847d3f6741fe9ce533935d238aa7fd10a7d9a8bbcc79ae8ab729088e
Expected: 0000000040070000000000000000000000000000000000000000000000000000
Attempting to boot anyway...
entry 0x4037993c
I (soc_init): ESP Simple boot
I (soc_init): compile time Aug 14 2026 23:42:03
W (soc_init): Unicore bootloader
I (soc_init): chip revision: v0.2
I (flash_init): Boot SPI Speed : 80MHz
I (flash_init): SPI Mode       : DIO
I (flash_init): SPI Flash Size : 8MB
I (boot): DRAM  : lma=00000020h vma=3fc90710h size=03158h ( 12632)
I (boot): IRAM  : lma=00003180h vma=40374000h size=0c6fch ( 50940)
I (boot): RTC_DATA      : lma=0000f884h vma=50000000h size=00024h (    36)
I (boot): IROM  : lma=00010000h vma=42000000h size=0a130h ( 41264)
I (boot): DROM  : lma=00020000h vma=3c010000h size=03204h ( 12804)
I (boot): libc heap size 292 kB.
I (cache): Instruction cache: size 16KB, 8Ways, cache line size 32Byte
I (spi_flash): detected chip: boya
I (spi_flash): flash io: dio
W (spi_flash): Detected size(16384k) larger than the size in the binary image header(8192k). Using the size in the binary image header.
*** Booting Zephyr OS build v4.4.0-11807-g357467a011cd ***
[00:00:00.238,000] <inf> bringup: === Stethoscope hardware bring-up ===
[00:00:00.504,000] <inf> bringup: ---- peripheral probe: 7 of 8 connected (max 3 retries each) ----
[00:00:00.504,000] <inf> bringup: [ OK ] pushbutton + LED (GPIO16/17)  (attempt 1)
[00:00:00.510,000] <inf> bringup: [ OK ] SP3T switch      (GPIO18/21/38)  (attempt 1)
[00:00:00.519,000] <inf> bringup: [ OK ] potentiometer    (GPIO1, ADC1_CH0)  (attempt 1)
[00:00:00.527,000] <inf> bringup: [ OK ] backlight PWM    (GPIO8, LEDC ch0)  (attempt 1)
[00:00:00.536,000] <inf> bringup: [ OK ] display ILI9341  (SPI2, CS GPIO10)  (attempt 1)
[00:00:00.544,000] <inf> bringup: [ OK ] touch XPT2046    (SPI2, CS GPIO7)  (attempt 1)
[00:00:00.553,000] <inf> bringup: [ OK ] DAC PCM5102A     (I2S1)  (attempt 1)
[00:00:00.560,000] <wrn> bringup: [ -- ] mic INMP441      (I2S0)  not connected (err -61) - check BCLK/WS/SD and L/R to GND
[00:00:00.737,000] <inf> bringup: display colour -> red
[00:00:00.737,000] <wrn> bringup: audio loopback disabled: microphone missing
[00:00:00.739,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=127mV | backlight=3% | colour=red | touch=0@0,0 |
[00:00:01.252,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=167mV | backlight=5% | colour=red | touch=0@0,0 |
[00:00:01.754,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=163mV | backlight=4% | colour=red | touch=0@0,0 |
[00:00:02.257,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=167mV | backlight=5% | colour=red | touch=0@0,0 |
[00:00:02.760,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=183mV | backlight=5% | colour=red | touch=0@0,0 |
[00:00:03.262,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=199mV | backlight=6% | colour=red | touch=0@0,0 |
[00:00:03.765,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=207mV | backlight=6% | colour=red | touch=0@0,0 |
[00:00:04.267,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=207mV | backlight=6% | colour=red | touch=0@0,0 |
[00:00:04.770,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=186mV | backlight=5% | colour=red | touch=0@0,0 |
[00:00:05.273,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=171mV | backlight=5% | colour=red | touch=0@0,0 |
[00:00:05.775,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=158mV | backlight=4% | colour=red | touch=0@0,0 |
[00:00:06.278,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=158mV | backlight=4% | colour=red | touch=0@0,0 |
[00:00:06.780,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=179mV | backlight=5% | colour=red | touch=0@0,0 |
[00:00:07.283,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=195mV | backlight=5% | colour=red | touch=0@0,0 |
[00:00:07.786,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=203mV | backlight=6% | colour=red | touch=0@0,0 |

```

**What I tried / assessment**

> Verdict: x PASS ☐ PARTIAL ☐ FAIL ☐ BLOCKED
>
> (What did you do, what did you observe, do you consider it working — and why?)
>
>

---

## T01 — Pushbutton + LED (GPIO16 / GPIO17)

**Goal:** GPIO input with pull-up and GPIO output both work; the interrupt-driven
press edge is detected exactly once and reaches deferred handling within 35 ms,
including the configured 25 ms debounce.

**Wiring**

- Button contact A → **GPIO16** (internal pull-up, active low)
- Button contact B → **GND**
- LED anode (via series resistor, e.g. 220 Ω) → **GPIO17**
- LED cathode → **GND**

**Steps**

1. Power off, wire, power on, flash, reset.
2. Read the probe report.
3. Press the button ~5 times slowly, watch the status line.
4. Under simultaneous audio, display redraw and logging load, drive GPIO16 with
   a signal generator and measure GPIO16's stable edge to GPIO17's LED-output
   transition on a two-channel oscilloscope. Capture at least 100 presses; the
   maximum must be <=35 ms. Confirm `input-latency-max` also stays <=35 ms.

**Expected log**

```
[ OK ] pushbutton + LED (GPIO16/17) (controller-ready, attempt 1)
...
btn=0 led=0 |
btn=1 led=1 |      <- while pressed, LED toggled on this edge
btn=0 led=1 |
btn=1 led=0 |      <- next press toggles back off
```

`led=` must change **once per press**, not per status line. The physical LED
must follow `led=`.

**Log output**

```text
ESP-ROM:esp32s3-20210327
Build:Mar 27 2021
rst:0x1 (POWERON),boot:0x8 (SPI_FAST_FLASH_BOOT)
SPIWP:0xee
mode:DIO, clock div:1
load:0x3fc90710,len:0x3158
load:0x40374000,len:0xc6fc
load:0x50000000,len:0x24
SHA-256 comparison failed:
Calculated: 0e4b74c9847d3f6741fe9ce533935d238aa7fd10a7d9a8bbcc79ae8ab729088e
Expected: 0000000040070000000000000000000000000000000000000000000000000000
Attempting to boot anyway...
entry 0x4037993c
I (soc_init): ESP Simple boot
I (soc_init): compile time Aug 14 2026 23:42:03
W (soc_init): Unicore bootloader
I (soc_init): chip revision: v0.2
I (flash_init): Boot SPI Speed : 80MHz
I (flash_init): SPI Mode       : DIO
I (flash_init): SPI Flash Size : 8MB
I (boot): DRAM  : lma=00000020h vma=3fc90710h size=03158h ( 12632)
I (boot): IRAM  : lma=00003180h vma=40374000h size=0c6fch ( 50940)
I (boot): RTC_DATA      : lma=0000f884h vma=50000000h size=00024h (    36)
I (boot): IROM  : lma=00010000h vma=42000000h size=0a130h ( 41264)
I (boot): DROM  : lma=00020000h vma=3c010000h size=03204h ( 12804)
I (boot): libc heap size 292 kB.
I (cache): Instruction cache: size 16KB, 8Ways, cache line size 32Byte
I (spi_flash): detected chip: boya
I (spi_flash): flash io: dio
W (spi_flash): Detected size(16384k) larger than the size in the binary image header(8192k). Using the size in the binary image header.
*** Booting Zephyr OS build v4.4.0-11807-g357467a011cd ***
[00:00:00.238,000] <inf> bringup: === Stethoscope hardware bring-up ===
[00:00:00.504,000] <inf> bringup: ---- peripheral probe: 7 of 8 connected (max 3 retries each) ----
[00:00:00.504,000] <inf> bringup: [ OK ] pushbutton + LED (GPIO16/17)  (attempt 1)
[00:00:00.510,000] <inf> bringup: [ OK ] SP3T switch      (GPIO18/21/38)  (attempt 1)
[00:00:00.519,000] <inf> bringup: [ OK ] potentiometer    (GPIO1, ADC1_CH0)  (attempt 1)
[00:00:00.527,000] <inf> bringup: [ OK ] backlight PWM    (GPIO8, LEDC ch0)  (attempt 1)
[00:00:00.536,000] <inf> bringup: [ OK ] display ILI9341  (SPI2, CS GPIO10)  (attempt 1)
[00:00:00.544,000] <inf> bringup: [ OK ] touch XPT2046    (SPI2, CS GPIO7)  (attempt 1)
[00:00:00.553,000] <inf> bringup: [ OK ] DAC PCM5102A     (I2S1)  (attempt 1)
[00:00:00.560,000] <wrn> bringup: [ -- ] mic INMP441      (I2S0)  not connected (err -61) - check BCLK/WS/SD and L/R to GND
[00:00:00.737,000] <inf> bringup: display colour -> red
[00:00:00.737,000] <wrn> bringup: audio loopback disabled: microphone missing
[00:00:00.739,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=1314mV | backlight=39% | colour=red | touch=0@0,0 |
[00:00:01.252,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=171mV | backlight=5% | colour=red | touch=0@0,0 |
[00:00:01.755,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=191mV | backlight=5% | colour=red | touch=0@0,0 |
[00:00:02.257,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=183mV | backlight=5% | colour=red | touch=0@0,0 |
[00:00:02.760,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=175mV | backlight=5% | colour=red | touch=0@0,0 |
[00:00:03.262,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=171mV | backlight=5% | colour=red | touch=0@0,0 |
[00:00:03.765,000] <inf> bringup: btn=0 led=1 | sw=2 | poti=71mV | backlight=2% | colour=red | touch=0@0,0 |
[00:00:04.268,000] <inf> bringup: btn=0 led=1 | sw=2 | poti=71mV | backlight=2% | colour=red | touch=0@0,0 |
[00:00:04.770,000] <inf> bringup: btn=0 led=1 | sw=2 | poti=63mV | backlight=1% | colour=red | touch=0@0,0 |
[00:00:05.273,000] <inf> bringup: btn=0 led=1 | sw=2 | poti=67mV | backlight=2% | colour=red | touch=0@0,0 |
[00:00:05.775,000] <inf> bringup: btn=0 led=1 | sw=2 | poti=71mV | backlight=2% | colour=red | touch=0@0,0 |
[00:00:06.278,000] <inf> bringup: btn=0 led=1 | sw=2 | poti=75mV | backlight=2% | colour=red | touch=0@0,0 |
[00:00:06.781,000] <inf> bringup: btn=0 led=1 | sw=2 | poti=75mV | backlight=2% | colour=red | touch=0@0,0 |
[00:00:07.283,000] <inf> bringup: btn=0 led=1 | sw=2 | poti=83mV | backlight=2% | colour=red | touch=0@0,0 |
[00:00:07.786,000] <inf> bringup: btn=0 led=1 | sw=2 | poti=75mV | backlight=2% | colour=red | touch=0@0,0 |
[00:00:08.288,000] <inf> bringup: btn=0 led=1 | sw=2 | poti=71mV | backlight=2% | colour=red | touch=0@0,0 |
[00:00:08.791,000] <inf> bringup: btn=0 led=1 | sw=2 | poti=71mV | backlight=2% | colour=red | touch=0@0,0 |
[00:00:09.294,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=167mV | backlight=5% | colour=red | touch=0@0,0 |
[00:00:09.796,000] <inf> bringup: btn=0 led=1 | sw=2 | poti=63mV | backlight=1% | colour=red | touch=0@0,0 |
[00:00:10.299,000] <inf> bringup: btn=0 led=1 | sw=2 | poti=75mV | backlight=2% | colour=red | touch=0@0,0 |
[00:00:10.801,000] <inf> bringup: btn=1 led=1 | sw=2 | poti=75mV | backlight=2% | colour=red | touch=0@0,0 |
[00:00:11.304,000] <inf> bringup: btn=1 led=0 | sw=2 | poti=171mV | backlight=5% | colour=red | touch=0@0,0 |
[00:00:11.807,000] <inf> bringup: btn=0 led=1 | sw=2 | poti=83mV | backlight=2% | colour=red | touch=0@0,0 |
[00:00:12.309,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=175mV | backlight=5% | colour=red | touch=0@0,0 |


```

**What I tried / assessment**

> Verdict: x PASS ☐ PARTIAL ☐ FAIL ☐ BLOCKED
>
> The btn log is only sometimes showing `btn=1` while pressed, but the LED always toggles exactly once per press. Additionally the LED lighting up when button pressed is visibly confirmed.
>

---

## T02 — SP3T switch, position 1 and 2 (GPIO18 / GPIO21)

**Goal:** the three-way selector is read correctly; the common pole pulls exactly
one throw low.

**Wiring**

- Common pole → **GND**
- Throw 1 (Raw) → **GPIO18**
- Throw 2 (Murmur) → **GPIO21**
- Throw 3 (BPM) → **GPIO38** (see T03, not yet wired here)

**Steps**

1. Wire common + throws 1 and 2 first. Flash, reset.
2. Flip the switch through all positions, watch `sw=`.

**Expected log**

```
[ OK ] SP3T switch      (GPIO18/21/38)  (attempt 1)
...
sw=1 |    <- position 1
sw=2 |    <- position 2
sw=0 |    <- position 3 not wired yet / mid-position
```

`sw=0` means "no throw pulled low". If the probe reports `[ -- ] ... (err -61)`,
the common pole is not on GND.

**Log output**

```text
ESP-ROM:esp32s3-20210327
Build:Mar 27 2021
rst:0x1 (POWERON),boot:0x8 (SPI_FAST_FLASH_BOOT)
SPIWP:0xee
mode:DIO, clock div:1
load:0x3fc90710,len:0x3158
load:0x40374000,len:0xc6fc
load:0x50000000,len:0x24
SHA-256 comparison failed:
Calculated: 0e4b74c9847d3f6741fe9ce533935d238aa7fd10a7d9a8bbcc79ae8ab729088e
Expected: 0000000040070000000000000000000000000000000000000000000000000000
Attempting to boot anyway...
entry 0x4037993c
I (soc_init): ESP Simple boot
I (soc_init): compile time Aug 14 2026 23:42:03
W (soc_init): Unicore bootloader
I (soc_init): chip revision: v0.2
I (flash_init): Boot SPI Speed : 80MHz
I (flash_init): SPI Mode       : DIO
I (flash_init): SPI Flash Size : 8MB
I (boot): DRAM  : lma=00000020h vma=3fc90710h size=03158h ( 12632)
I (boot): IRAM  : lma=00003180h vma=40374000h size=0c6fch ( 50940)
I (boot): RTC_DATA      : lma=0000f884h vma=50000000h size=00024h (    36)
I (boot): IROM  : lma=00010000h vma=42000000h size=0a130h ( 41264)
I (boot): DROM  : lma=00020000h vma=3c010000h size=03204h ( 12804)
I (boot): libc heap size 292 kB.
I (cache): Instruction cache: size 16KB, 8Ways, cache line size 32Byte
I (spi_flash): detected chip: boya
I (spi_flash): flash io: dio
W (spi_flash): Detected size(16384k) larger than the size in the binary image header(8192k). Using the size in the binary image header.
*** Booting Zephyr OS build v4.4.0-11807-g357467a011cd ***
[00:00:00.238,000] <inf> bringup: === Stethoscope hardware bring-up ===
[00:00:00.322,000] <inf> bringup: ---- peripheral probe: 8 of 8 connected (max 3 retries each) ----
[00:00:00.322,000] <inf> bringup: [ OK ] pushbutton + LED (GPIO16/17)  (attempt 1)
[00:00:00.328,000] <inf> bringup: [ OK ] SP3T switch      (GPIO18/21/38)  (attempt 1)
[00:00:00.336,000] <inf> bringup: [ OK ] potentiometer    (GPIO1, ADC1_CH0)  (attempt 1)
[00:00:00.345,000] <inf> bringup: [ OK ] backlight PWM    (GPIO8, LEDC ch0)  (attempt 1)
[00:00:00.353,000] <inf> bringup: [ OK ] display ILI9341  (SPI2, CS GPIO10)  (attempt 1)
[00:00:00.362,000] <inf> bringup: [ OK ] touch XPT2046    (SPI2, CS GPIO7)  (attempt 1)
[00:00:00.370,000] <inf> bringup: [ OK ] mic INMP441      (I2S0)  (attempt 2)
[00:00:00.378,000] <inf> bringup: [ OK ] DAC PCM5102A     (I2S1)  (attempt 1)
[00:00:00.550,000] <inf> bringup: display colour -> red
[00:00:00.551,000] <inf> bringup: btn=0 led=0 | sw=1 | poti=158mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=0 errs=0 peak=0 |
[00:00:00.558,000] <inf> bringup: audio loopback running (INMP441 -> PCM5102A)
[00:00:01.060,000] <inf> bringup: btn=0 led=0 | sw=1 | poti=179mV | backlight=5% | colour=red | touch=0@0,0 | audio blocks=31 errs=0 peak=0 |
[00:00:01.565,000] <inf> bringup: btn=0 led=0 | sw=1 | poti=186mV | backlight=5% | colour=red | touch=0@0,0 | audio blocks=62 errs=0 peak=0 |
[00:00:02.069,000] <inf> bringup: btn=0 led=0 | sw=1 | poti=171mV | backlight=5% | colour=red | touch=0@0,0 | audio blocks=94 errs=0 peak=0 |
[00:00:02.574,000] <inf> bringup: btn=0 led=0 | sw=1 | poti=151mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=125 errs=0 peak=0 |
[00:00:03.078,000] <inf> bringup: btn=0 led=0 | sw=1 | poti=158mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=157 errs=0 peak=0 |
[00:00:03.583,000] <inf> bringup: btn=0 led=0 | sw=1 | poti=158mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=189 errs=0 peak=0 |
[00:00:04.088,000] <inf> bringup: btn=0 led=0 | sw=1 | poti=158mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=220 errs=0 peak=0 |
[00:00:04.592,000] <inf> bringup: btn=0 led=0 | sw=1 | poti=158mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=252 errs=0 peak=0 |
[00:00:05.097,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=155mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=283 errs=0 peak=0 |
[00:00:05.601,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=155mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=315 errs=0 peak=0 |
[00:00:06.106,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=158mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=346 errs=0 peak=0 |
[00:00:06.611,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=155mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=378 errs=0 peak=0 |
[00:00:07.115,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=155mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=409 errs=0 peak=0 |
[00:00:07.620,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=155mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=441 errs=0 peak=0 |
[00:00:08.124,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=158mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=472 errs=0 peak=0 |
[00:00:08.629,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=158mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=504 errs=0 peak=0 |
[00:00:09.134,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=155mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=535 errs=0 peak=0 |
[00:00:09.638,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=155mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=567 errs=0 peak=0 |
[00:00:10.143,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=155mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=599 errs=0 peak=0 |
[00:00:10.647,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=158mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=630 errs=0 peak=0 |
[00:00:11.152,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=155mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=662 errs=0 peak=0 |
[00:00:11.657,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=155mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=693 errs=0 peak=0 |
[00:00:12.161,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=155mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=725 errs=0 peak=0 |
[00:00:12.666,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=155mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=756 errs=0 peak=0 |
[00:00:13.170,000] <inf> bringup: btn=0 led=0 | sw=1 | poti=158mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=788 errs=0 peak=0 |
[00:00:13.675,000] <inf> bringup: btn=0 led=0 | sw=1 | poti=155mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=819 errs=0 peak=0 |
[00:00:14.180,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=151mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=851 errs=0 peak=0 |
[00:00:14.684,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=151mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=882 errs=0 peak=0 |
[00:00:15.189,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=155mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=914 errs=0 peak=0 |
[00:00:15.693,000] <inf> bringup: btn=0 led=0 | sw=1 | poti=158mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=945 errs=0 peak=0 |
[00:00:16.198,000] <inf> bringup: btn=0 led=0 | sw=1 | poti=147mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=977 errs=0 peak=0 |
[00:00:16.703,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=139mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=1009 errs=0 peak=0 |
[00:00:17.207,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=155mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=1040 errs=0 peak=0 |
[00:00:17.712,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=158mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=1072 errs=0 peak=0 |
[00:00:18.217,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=155mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=1103 errs=0 peak=0 |
[00:00:18.721,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=155mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=1135 errs=0 peak=0 |
[00:00:19.226,000] <inf> bringup: btn=0 led=0 | sw=1 | poti=155mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=1166 errs=0 peak=0 |
[00:00:19.731,000] <inf> bringup: btn=0 led=0 | sw=1 | poti=155mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=1198 errs=0 peak=0 |
[00:00:20.236,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=158mV | backlight=4% | colour=red | touch=0@0,0 | audio blocks=1229 errs=0 peak=0 |

```

**What I tried / assessment**

> Verdict: ☐ PASS x PARTIAL ☐ FAIL ☐ BLOCKED
>
> No Switch position 3 detected with all GND; GPIO18, 21 and 38 connected. The log shows only sw=1 and sw=2. The switch is a 3PDT type, so the common pole is connected to GND.  
>

> Note: switch to new switch since this one might have been damaged by soldering.

---

## T03 — SP3T switch, position 3 (GPIO38) — known open item

**Goal:** close the open point from the first hardware session (`sw=3` never
appeared).

**Wiring:** add throw 3 → **GPIO38**.

**Steps**

1. Wire throw 3 to GPIO38, reset, flip to position 3.
2. If `sw=3` never appears: on DevKitC-1 **v1.1** the onboard WS2812 RGB LED
   sits on GPIO38. Move throw 3 to **GPIO48**, adjust the overlay
   (`sw1-gpios` index 2 → `<&gpio1 16 ...>`, since GPIO48 = gpio1 index 16),
   rebuild with `--pristine`, retest.
3. Cross-check with a multimeter: position 3 must show continuity to GND.

**Expected log**

```
sw=3 |
```

**Log output**

```text
(paste console output here)

```

**What I tried / assessment**

> Which pin did you end up using (GPIO38 / GPIO48 / other)? Was the overlay
> changed? Note it here — the final pin map depends on it.
>
> Verdict: ☐ PASS ☐ PARTIAL ☐ FAIL ☐ BLOCKED x SKIPPED
>
>
>

---

## T04 — Potentiometer (GPIO1, ADC1_CH0)

**Goal:** the ADC delivers the full swing over the whole travel of the poti.

**Wiring**

- End 1 → **3V3**
- Wiper (middle) → **GPIO1**
- End 2 → **GND**

**Steps**

1. Wire, reset.
2. Turn the poti slowly from one stop to the other.
3. Note the minimum and maximum `poti=` value.

**Expected log**

```
[ OK ] potentiometer    (GPIO1, ADC1_CH0)  (attempt 1)
...
poti=0mV | backlight=0% |
poti=1780mV | backlight=53% |
poti=3083mV | backlight=93% |
```

Roughly 0 mV → ≥ 3000 mV, monotonic, no jumps. The ceiling is ~3.1 V
(`ADC_GAIN_1_4`), not 3.3 V — that is expected.

**Log output**

```text
ESP-ROM:esp32s3-20210327
Build:Mar 27 2021
rst:0x1 (POWERON),boot:0xa (SPI_FAST_FLASH_BOOT)
SPIWP:0xee
mode:DIO, clock div:1
load:0x3fc90710,len:0x3158
load:0x40374000,len:0xc6fc
load:0x50000000,len:0x24
SHA-256 comparison failed:
Calculated: 0e4b74c9847d3f6741fe9ce533935d238aa7fd10a7d9a8bbcc79ae8ab729088e
Expected: 0000000040070000000000000000000000000000000000000000000000000000
Attempting to boot anyway...
entry 0x4037993c
I (soc_init): ESP Simple boot
I (soc_init): compile time Aug 14 2026 23:42:03
W (soc_init): Unicore bootloader
I (soc_init): chip revision: v0.2
I (flash_init): Boot SPI Speed : 80MHz
I (flash_init): SPI Mode       : DIO
I (flash_init): SPI Flash Size : 8MB
I (boot): DRAM  : lma=00000020h vma=3fc90710h size=03158h ( 12632)
I (boot): IRAM  : lma=00003180h vma=40374000h size=0c6fch ( 50940)
I (boot): RTC_DATA      : lma=0000f884h vma=50000000h size=00024h (    36)
I (boot): IROM  : lma=00010000h vma=42000000h size=0a130h ( 41264)
I (boot): DROM  : lma=00020000h vma=3c010000h size=03204h ( 12804)
I (boot): libc heap size 292 kB.
I (cache): Instruction cache: size 16KB, 8Ways, cache line size 32Byte
I (spi_flash): detected chip: boya
I (spi_flash): flash io: dio
W (spi_flash): Detected size(16384k) larger than the size in the binary image header(8192k). Using the size in the binary image header.
*** Booting Zephyr OS build v4.4.0-11807-g357467a011cd ***
[00:00:00.238,000] <inf> bringup: === Stethoscope hardware bring-up ===
[00:00:00.256,000] <inf> bringup: ---- peripheral probe: 8 of 8 connected (max 3 retries each) ----
[00:00:00.256,000] <inf> bringup: [ OK ] pushbutton + LED (GPIO16/17)  (attempt 1)
[00:00:00.262,000] <inf> bringup: [ OK ] SP3T switch      (GPIO18/21/38)  (attempt 1)
[00:00:00.270,000] <inf> bringup: [ OK ] potentiometer    (GPIO1, ADC1_CH0)  (attempt 1)
[00:00:00.279,000] <inf> bringup: [ OK ] backlight PWM    (GPIO8, LEDC ch0)  (attempt 1)
[00:00:00.287,000] <inf> bringup: [ OK ] display ILI9341  (SPI2, CS GPIO10)  (attempt 1)
[00:00:00.296,000] <inf> bringup: [ OK ] touch XPT2046    (SPI2, CS GPIO7)  (attempt 1)
[00:00:00.304,000] <inf> bringup: [ OK ] mic INMP441      (I2S0)  (attempt 1)
[00:00:00.312,000] <inf> bringup: [ OK ] DAC PCM5102A     (I2S1)  (attempt 1)
[00:00:00.484,000] <inf> bringup: display colour -> red
[00:00:00.484,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=0 errs=0 peak=0 |
[00:00:00.492,000] <inf> bringup: audio loopback running (INMP441 -> PCM5102A)
[00:00:00.995,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=31 errs=0 peak=0 |
[00:00:01.499,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=62 errs=0 peak=0 |
[00:00:02.004,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=94 errs=0 peak=0 |
[00:00:02.509,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=126 errs=0 peak=0 |
[00:00:03.013,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=157 errs=0 peak=0 |
[00:00:03.518,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=189 errs=0 peak=0 |
[00:00:04.023,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=2798mV | backlight=84% | colour=red | touch=0@0,0 | audio blocks=220 errs=0 peak=0 |
[00:00:04.528,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=1899mV | backlight=57% | colour=red | touch=0@0,0 | audio blocks=252 errs=0 peak=0 |
[00:00:05.033,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=1474mV | backlight=44% | colour=red | touch=0@0,0 | audio blocks=283 errs=0 peak=0 |
[00:00:05.537,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=1251mV | backlight=37% | colour=red | touch=0@0,0 | audio blocks=315 errs=0 peak=0 |
[00:00:06.042,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=1054mV | backlight=31% | colour=red | touch=0@0,0 | audio blocks=346 errs=0 peak=0 |
[00:00:06.547,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=759mV | backlight=23% | colour=red | touch=0@0,0 | audio blocks=378 errs=0 peak=0 |
[00:00:07.052,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=383mV | backlight=11% | colour=red | touch=0@0,0 | audio blocks=409 errs=0 peak=0 |
[00:00:07.556,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=0mV | backlight=0% | colour=red | touch=0@0,0 | audio blocks=441 errs=0 peak=0 |
[00:00:08.061,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=0mV | backlight=0% | colour=red | touch=0@0,0 | audio blocks=473 errs=0 peak=0 |
[00:00:08.565,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=0mV | backlight=0% | colour=red | touch=0@0,0 | audio blocks=504 errs=0 peak=0 |
[00:00:09.070,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=0mV | backlight=0% | colour=red | touch=0@0,0 | audio blocks=536 errs=0 peak=0 |

```

**What I tried / assessment**

> Measured min / max: 3083mV mV … 0 mV
>
> Verdict: x PASS ☐ PARTIAL ☐ FAIL ☐ BLOCKED
>
>
>

---

## T05 — Display ILI9341 + backlight PWM (SPI2, GPIO8)

**Goal:** SPI2 + MIPI-DBI init sequence works, the panel shows a colour, and the
poti dims the backlight.

**Wiring**

- VCC → **3V3**
- GND → **GND**
- SCK / CLK → **GPIO12**
- SDI / MOSI → **GPIO11**
- SDO / MISO → **GPIO13**
- CS → **GPIO10**
- DC / RS → **GPIO14**
- RESET → **GPIO9**
- LED (backlight) → **GPIO8**

> ⚠️ **Measure the backlight current before connecting `LED` to GPIO8.** The pin
> often drives 3–4 parallel LEDs (40–60 mA). Above ~10 mA use an N-MOSFET
> (2N7002 / BSS138) with its gate on GPIO8, drain to `LED`, source to GND.

**Steps**

1. Wire, reset. Both USB cables plugged in.
2. Check the panel: a solid **red** screen must appear.
3. Turn the poti and watch the brightness follow `backlight=…%`.

**Expected log**

```
[ OK ] backlight PWM    (GPIO8, LEDC ch0)  (attempt 1)
[ OK ] display ILI9341  (SPI2, CS GPIO10)  (attempt 1)
[00:00:0x.xxx,000] <inf> bringup: display colour -> red
...
poti=2942mV | backlight=89% | colour=red |
```

> A `[ OK ]` for the display proves only that the driver could send its init
> sequence — MIPI-DBI is write-only and succeeds with no panel attached.
> **Trust the colour on the glass, not the log.**

**Log output**

```text
ESP-ROM:esp32s3-20210327
Build:Mar 27 2021
rst:0x1 (POWERON),boot:0x8 (SPI_FAST_FLASH_BOOT)
SPIWP:0xee
mode:DIO, clock div:1
load:0x3fc90710,len:0x3158
load:0x40374000,len:0xc6fc
load:0x50000000,len:0x24
SHA-256 comparison failed:
Calculated: 0e4b74c9847d3f6741fe9ce533935d238aa7fd10a7d9a8bbcc79ae8ab729088e
Expected: 0000000040070000000000000000000000000000000000000000000000000000
Attempting to boot anyway...
entry 0x4037993c
I (soc_init): ESP Simple boot
I (soc_init): compile time Aug 14 2026 23:42:03
W (soc_init): Unicore bootloader
I (soc_init): chip revision: v0.2
I (flash_init): Boot SPI Speed : 80MHz
I (flash_init): SPI Mode       : DIO
I (flash_init): SPI Flash Size : 8MB
I (boot): DRAM  : lma=00000020h vma=3fc90710h size=03158h ( 12632)
I (boot): IRAM  : lma=00003180h vma=40374000h size=0c6fch ( 50940)
I (boot): RTC_DATA      : lma=0000f884h vma=50000000h size=00024h (    36)
I (boot): IROM  : lma=00010000h vma=42000000h size=0a130h ( 41264)
I (boot): DROM  : lma=00020000h vma=3c010000h size=03204h ( 12804)
I (boot): libc heap size 292 kB.
I (cache): Instruction cache: size 16KB, 8Ways, cache line size 32Byte
I (spi_flash): detected chip: boya
I (spi_flash): flash io: dio
W (spi_flash): Detected size(16384k) larger than the size in the binary image header(8192k). Using the size in the binary image header.
*** Booting Zephyr OS build v4.4.0-11807-g357467a011cd ***
[00:00:00.238,000] <inf> bringup: === Stethoscope hardware bring-up ===
[00:00:00.256,000] <inf> bringup: ---- peripheral probe: 8 of 8 connected (max 3 retries each) ----
[00:00:00.256,000] <inf> bringup: [ OK ] pushbutton + LED (GPIO16/17)  (attempt 1)
[00:00:00.262,000] <inf> bringup: [ OK ] SP3T switch      (GPIO18/21/38)  (attempt 1)
[00:00:00.270,000] <inf> bringup: [ OK ] potentiometer    (GPIO1, ADC1_CH0)  (attempt 1)
[00:00:00.279,000] <inf> bringup: [ OK ] backlight PWM    (GPIO8, LEDC ch0)  (attempt 1)
[00:00:00.287,000] <inf> bringup: [ OK ] display ILI9341  (SPI2, CS GPIO10)  (attempt 1)
[00:00:00.296,000] <inf> bringup: [ OK ] touch XPT2046    (SPI2, CS GPIO7)  (attempt 1)
[00:00:00.304,000] <inf> bringup: [ OK ] mic INMP441      (I2S0)  (attempt 1)
[00:00:00.312,000] <inf> bringup: [ OK ] DAC PCM5102A     (I2S1)  (attempt 1)
[00:00:00.484,000] <inf> bringup: display colour -> red
[00:00:00.484,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=0mV | backlight=0% | colour=red | touch=0@0,0 | audio blocks=0 errs=0 peak=0 |
[00:00:00.492,000] <inf> bringup: audio loopback running (INMP441 -> PCM5102A)
[00:00:00.994,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=0mV | backlight=0% | colour=red | touch=0@0,0 | audio blocks=31 errs=0 peak=0 |
[00:00:01.498,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=0mV | backlight=0% | colour=red | touch=0@0,0 | audio blocks=62 errs=0 peak=0 |
[00:00:02.002,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=0mV | backlight=0% | colour=red | touch=0@0,0 | audio blocks=94 errs=0 peak=0 |
[00:00:02.507,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=0mV | backlight=0% | colour=red | touch=0@0,0 | audio blocks=125 errs=0 peak=0 |
[00:00:03.011,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=0mV | backlight=0% | colour=red | touch=0@0,0 | audio blocks=157 errs=0 peak=0 |
[00:00:03.516,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=0mV | backlight=0% | colour=red | touch=0@0,0 | audio blocks=188 errs=0 peak=0 |
[00:00:04.020,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=0mV | backlight=0% | colour=red | touch=0@0,0 | audio blocks=220 errs=0 peak=0 |
[00:00:04.524,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=0mV | backlight=0% | colour=red | touch=0@0,0 | audio blocks=252 errs=0 peak=0 |
[00:00:05.029,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=0mV | backlight=0% | colour=red | touch=0@0,0 | audio blocks=283 errs=0 peak=0 |
[00:00:05.533,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=0mV | backlight=0% | colour=red | touch=0@0,0 | audio blocks=315 errs=0 peak=0 |
[00:00:06.038,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=0mV | backlight=0% | colour=red | touch=0@0,0 | audio blocks=346 errs=0 peak=0 |
[00:00:06.542,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=0mV | backlight=0% | colour=red | touch=0@0,0 | audio blocks=378 errs=0 peak=0 |
[00:00:07.046,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=0mV | backlight=0% | colour=red | touch=0@0,0 | audio blocks=409 errs=0 peak=0 |
[00:00:07.551,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=0mV | backlight=0% | colour=red | touch=0@0,0 | audio blocks=441 errs=0 peak=0 |
[00:00:08.055,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=0mV | backlight=0% | colour=red | touch=0@0,0 | audio blocks=472 errs=0 peak=0 |
[00:00:08.560,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=423mV | backlight=12% | colour=red | touch=0@0,0 | audio blocks=504 errs=0 peak=0 |
[00:00:09.064,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=743mV | backlight=22% | colour=red | touch=0@0,0 | audio blocks=535 errs=0 peak=0 |
[00:00:09.569,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=734mV | backlight=22% | colour=red | touch=0@0,0 | audio blocks=567 errs=0 peak=0 |
[00:00:10.074,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=1007mV | backlight=30% | colour=red | touch=0@0,0 | audio blocks=598 errs=0 peak=0 |
[00:00:10.579,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=1435mV | backlight=43% | colour=red | touch=0@0,0 | audio blocks=630 errs=0 peak=0 |
[00:00:11.083,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=1391mV | backlight=42% | colour=red | touch=0@0,0 | audio blocks=661 errs=0 peak=0 |
[00:00:11.588,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=2586mV | backlight=78% | colour=red | touch=0@0,0 | audio blocks=693 errs=0 peak=0 |
[00:00:12.093,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=725 errs=0 peak=0 |
[00:00:12.598,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=756 errs=0 peak=0 |
[00:00:13.103,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=788 errs=0 peak=0 |
[00:00:13.607,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=819 errs=0 peak=0 |
[00:00:14.112,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=851 errs=0 peak=0 |
[00:00:14.617,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=882 errs=0 peak=0 |
[00:00:15.122,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=914 errs=0 peak=0 |
[00:00:15.627,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=945 errs=0 peak=0 |
[00:00:16.131,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=977 errs=0 peak=0 |
[00:00:16.636,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=1009 errs=0 peak=0 |
[00:00:16.883,000] <inf> bringup: display colour -> green
[00:00:17.329,000] <inf> bringup: display colour -> blue
[00:00:17.470,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=blue | touch=5@199,210 | audio blocks=1017 errs=42 peak=0 |
[00:00:17.658,000] <inf> bringup: display colour -> yellow
[00:00:18.204,000] <inf> bringup: display colour -> magenta
[00:00:18.305,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=9@246,199 | audio blocks=1017 errs=92 peak=0 |
[00:00:18.810,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=9@246,199 | audio blocks=1017 errs=142 peak=0 |
[00:00:19.036,000] <inf> bringup: display colour -> cyan
[00:00:19.221,000] <inf> bringup: display colour -> white
[00:00:19.683,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=white | touch=13@252,0 | audio blocks=1017 errs=192 peak=0 |
[00:00:20.140,000] <inf> bringup: display colour -> red
[00:00:20.381,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=15@252,0 | audio blocks=1017 errs=242 peak=0 |
[00:00:20.769,000] <inf> bringup: display colour -> green
[00:00:21.051,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=green | touch=16@147,241 | audio blocks=1017 errs=292 peak=0 |
[00:00:21.259,000] <inf> bringup: display colour -> blue
[00:00:21.825,000] <inf> bringup: display colour -> yellow
[00:00:21.886,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=yellow | touch=21@252,191 | audio blocks=1017 errs=342 peak=0 |
[00:00:22.254,000] <inf> bringup: display colour -> magenta
[00:00:22.700,000] <inf> bringup: display colour -> cyan
[00:00:22.720,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=cyan | touch=27@252,5 | audio blocks=1017 errs=392 peak=0 |
[00:00:23.129,000] <inf> bringup: display colour -> white
[00:00:23.390,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=white | touch=31@252,145 | audio blocks=1017 errs=442 peak=0 |
[00:00:23.658,000] <inf> bringup: display colour -> red
[00:00:24.185,000] <inf> bringup: display colour -> green
[00:00:24.370,000] <inf> bringup: display colour -> blue
[00:00:24.390,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=blue | touch=36@170,264 | audio blocks=1017 errs=492 peak=0 |
[00:00:24.859,000] <inf> bringup: display colour -> yellow
[00:00:25.061,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=yellow | touch=37@180,258 | audio blocks=1017 errs=542 peak=0 |
[00:00:25.389,000] <inf> bringup: display colour -> magenta
[00:00:25.731,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=39@252,0 | audio blocks=1017 errs=592 peak=0 |
[00:00:26.236,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=39@252,0 | audio blocks=1017 errs=642 peak=0 |
[00:00:26.742,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=39@252,0 | audio blocks=1017 errs=692 peak=0 |
[00:00:27.248,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=39@252,0 | audio blocks=1017 errs=742 peak=0 |
[00:00:27.753,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=39@252,0 | audio blocks=1017 errs=792 peak=0 |
[00:00:27.981,000] <inf> bringup: display colour -> cyan
[00:00:28.166,000] <inf> bringup: display colour -> white
[00:00:28.588,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=white | touch=42@198,187 | audio blocks=1017 errs=842 peak=0 |
[00:00:29.038,000] <inf> bringup: display colour -> red
[00:00:29.222,000] <inf> bringup: display colour -> green
[00:00:29.423,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=green | touch=45@252,0 | audio blocks=1017 errs=892 peak=0 |
[00:00:29.772,000] <inf> bringup: display colour -> blue
[00:00:30.093,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=blue | touch=46@250,201 | audio blocks=1017 errs=942 peak=0 |
[00:00:30.562,000] <inf> bringup: display colour -> yellow
[00:00:30.764,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=yellow | touch=48@252,185 | audio blocks=1017 errs=992 peak=0 |
[00:00:31.269,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=yellow | touch=48@252,185 | audio blocks=1017 errs=1042 peak=0 |
[00:00:31.775,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=yellow | touch=48@252,185 | audio blocks=1017 errs=1092 peak=0 |
[00:00:32.281,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=yellow | touch=48@252,185 | audio blocks=1017 errs=1142 peak=0 |
[00:00:32.787,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=yellow | touch=48@252,185 | audio blocks=1017 errs=1192 peak=0 |
[00:00:33.196,000] <inf> bringup: display colour -> magenta
[00:00:33.380,000] <inf> bringup: display colour -> cyan
[00:00:33.622,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=cyan | touch=51@212,207 | audio blocks=1017 errs=1242 peak=0 |
[00:00:34.127,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=cyan | touch=51@212,207 | audio blocks=1017 errs=1292 peak=0 |
[00:00:34.633,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=cyan | touch=51@212,207 | audio blocks=1017 errs=1342 peak=0 |
[00:00:34.983,000] <inf> bringup: display colour -> white
[00:00:35.167,000] <inf> bringup: display colour -> red
[00:00:35.469,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=54@252,187 | audio blocks=1017 errs=1392 peak=0 |
[00:00:35.974,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=54@252,187 | audio blocks=1017 errs=1442 peak=0 |
[00:00:36.480,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=54@252,187 | audio blocks=1017 errs=1492 peak=0 |
[00:00:36.985,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=54@252,187 | audio blocks=1017 errs=1542 peak=0 |
[00:00:37.277,000] <inf> bringup: display colour -> green
[00:00:37.462,000] <inf> bringup: display colour -> blue
[00:00:37.824,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=blue | touch=59@252,146 | audio blocks=1017 errs=1592 peak=0 |
[00:00:38.330,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=blue | touch=59@252,146 | audio blocks=1017 errs=1642 peak=0 |
[00:00:38.835,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=blue | touch=59@252,146 | audio blocks=1017 errs=1692 peak=0 |
[00:00:39.341,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=blue | touch=59@252,146 | audio blocks=1017 errs=1742 peak=0 |
[00:00:39.710,000] <inf> bringup: display colour -> yellow
[00:00:39.895,000] <inf> bringup: display colour -> magenta
[00:00:40.176,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=62@215,216 | audio blocks=1017 errs=1792 peak=0 |
[00:00:40.406,000] <inf> bringup: display colour -> cyan
[00:00:40.591,000] <inf> bringup: display colour -> white
[00:00:40.959,000] <inf> bringup: display colour -> red
[00:00:41.143,000] <inf> bringup: display colour -> green
[00:00:41.350,000] <inf> bringup: display colour -> blue
[00:00:41.534,000] <inf> bringup: display colour -> yellow
[00:00:41.675,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=yellow | touch=84@252,0 | audio blocks=1017 errs=1842 peak=0 |
[00:00:42.205,000] <inf> bringup: display colour -> magenta
[00:00:42.346,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=85@252,121 | audio blocks=1017 errs=1892 peak=0 |
[00:00:42.851,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=85@252,121 | audio blocks=1017 errs=1942 peak=0 |
[00:00:43.120,000] <inf> bringup: display colour -> cyan
[00:00:43.522,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=cyan | touch=88@252,216 | audio blocks=1017 errs=1992 peak=0 |
[00:00:43.790,000] <inf> bringup: display colour -> white
[00:00:44.192,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=white | touch=89@180,187 | audio blocks=1017 errs=2042 peak=0 |
[00:00:44.480,000] <inf> bringup: display colour -> red
[00:00:44.862,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=92@252,189 | audio blocks=1017 errs=2092 peak=0 |
[00:00:45.368,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=92@252,189 | audio blocks=1017 errs=2142 peak=0 |
[00:00:45.978,000] <inf> bringup: display colour -> green
[00:00:46.163,000] <inf> bringup: display colour -> blue
[00:00:46.348,000] <inf> bringup: display colour -> yellow
[00:00:46.368,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=yellow | touch=97@252,168 | audio blocks=1017 errs=2192 peak=0 |
[00:00:46.878,000] <inf> bringup: display colour -> magenta
[00:00:47.123,000] <inf> bringup: display colour -> cyan
[00:00:47.203,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=cyan | touch=101@252,170 | audio blocks=1017 errs=2242 peak=0 |
[00:00:47.619,000] <inf> bringup: display colour -> white
[00:00:47.804,000] <inf> bringup: display colour -> red
[00:00:48.045,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=104@252,151 | audio blocks=1017 errs=2292 peak=0 |
[00:00:48.551,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=104@252,151 | audio blocks=1017 errs=2342 peak=0 |
[00:00:49.105,000] <inf> bringup: display colour -> green
[00:00:49.289,000] <inf> bringup: display colour -> blue
[00:00:49.390,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=blue | touch=110@252,0 | audio blocks=1017 errs=2392 peak=0 |
[00:00:49.759,000] <inf> bringup: display colour -> yellow
[00:00:50.060,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=yellow | touch=113@252,120 | audio blocks=1017 errs=2442 peak=0 |
[00:00:50.494,000] <inf> bringup: display colour -> magenta
[00:00:50.735,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=118@252,0 | audio blocks=1017 errs=2492 peak=0 |
[00:00:51.184,000] <inf> bringup: display colour -> cyan
[00:00:51.369,000] <inf> bringup: display colour -> white
[00:00:51.570,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=white | touch=121@198,202 | audio blocks=1017 errs=2542 peak=0 |
[00:00:52.076,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=white | touch=121@198,202 | audio blocks=1017 errs=2592 peak=0 |
[00:00:52.362,000] <inf> bringup: display colour -> red
[00:00:52.546,000] <inf> bringup: display colour -> green
[00:00:52.928,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=green | touch=125@252,0 | audio blocks=1017 errs=2642 peak=0 |
[00:00:53.177,000] <inf> bringup: display colour -> blue
[00:00:53.361,000] <inf> bringup: display colour -> yellow
[00:00:53.763,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=yellow | touch=128@252,133 | audio blocks=1017 errs=2692 peak=0 |
[00:00:53.971,000] <inf> bringup: display colour -> magenta
[00:00:54.434,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=131@252,0 | audio blocks=1017 errs=2742 peak=0 |
[00:00:54.939,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=131@252,0 | audio blocks=1017 errs=2792 peak=0 |
[00:00:55.409,000] <inf> bringup: display colour -> cyan
[00:00:55.610,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=cyan | touch=132@183,248 | audio blocks=1017 errs=2842 peak=0 |
[00:00:56.039,000] <inf> bringup: display colour -> white
[00:00:56.280,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=white | touch=133@167,243 | audio blocks=1017 errs=2892 peak=0 |
[00:00:56.649,000] <inf> bringup: display colour -> red
[00:00:57.034,000] <inf> bringup: display colour -> green
[00:00:57.115,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=green | touch=140@220,236 | audio blocks=1017 errs=2942 peak=0 |
[00:00:57.624,000] <inf> bringup: display colour -> blue
[00:00:57.785,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=blue | touch=141@177,237 | audio blocks=1017 errs=2992 peak=0 |
[00:00:58.291,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=blue | touch=141@177,237 | audio blocks=1017 errs=3042 peak=0 |
[00:00:58.796,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=blue | touch=141@177,237 | audio blocks=1017 errs=3092 peak=0 |
[00:00:59.145,000] <inf> bringup: display colour -> yellow
[00:00:59.330,000] <inf> bringup: display colour -> magenta
[00:00:59.787,000] <inf> bringup: display colour -> cyan
[00:00:59.972,000] <inf> bringup: display colour -> white
[00:00:59.972,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=white | touch=148@252,0 | audio blocks=1017 errs=3142 peak=0 |
[00:01:00.483,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=white | touch=148@252,0 | audio blocks=1017 errs=3192 peak=0 |
[00:01:00.989,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=white | touch=148@252,0 | audio blocks=1017 errs=3242 peak=0 |
[00:01:01.494,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=white | touch=148@252,0 | audio blocks=1017 errs=3292 peak=0 |
[00:01:02.023,000] <inf> bringup: display colour -> red
[00:01:02.207,000] <inf> bringup: display colour -> green
[00:01:02.348,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=green | touch=154@252,0 | audio blocks=1017 errs=3342 peak=0 |
[00:01:02.854,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=green | touch=154@252,0 | audio blocks=1017 errs=3392 peak=0 |
[00:01:03.263,000] <inf> bringup: display colour -> blue
[00:01:03.487,000] <inf> bringup: display colour -> yellow
[00:01:03.688,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=yellow | touch=159@252,118 | audio blocks=1017 errs=3442 peak=0 |
[00:01:04.194,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=yellow | touch=159@252,118 | audio blocks=1017 errs=3492 peak=0 |
[00:01:04.845,000] <inf> bringup: display colour -> magenta
[00:01:04.865,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=160@238,165 | audio blocks=1017 errs=3542 peak=0 |
[00:01:05.053,000] <inf> bringup: display colour -> cyan
[00:01:05.237,000] <inf> bringup: display colour -> white
[00:01:05.700,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=white | touch=168@252,0 | audio blocks=1017 errs=3592 peak=0 |
[00:01:06.212,000] <inf> bringup: display colour -> red
[00:01:06.397,000] <inf> bringup: display colour -> green
[00:01:06.582,000] <inf> bringup: display colour -> blue
[00:01:06.702,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=blue | touch=175@252,168 | audio blocks=1017 errs=3642 peak=0 |
[00:01:07.011,000] <inf> bringup: display colour -> yellow
[00:01:07.373,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=yellow | touch=180@252,0 | audio blocks=1017 errs=3692 peak=0 |
[00:01:07.661,000] <inf> bringup: display colour -> magenta
[00:01:07.846,000] <inf> bringup: display colour -> cyan
[00:01:08.251,000] <inf> bringup: display colour -> white
[00:01:08.463,000] <inf> bringup: display colour -> red
[00:01:08.647,000] <inf> bringup: display colour -> green
[00:01:08.728,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=green | touch=195@252,6 | audio blocks=1017 errs=3742 peak=0 |
[00:01:08.956,000] <inf> bringup: display colour -> blue
[00:01:09.191,000] <inf> bringup: display colour -> yellow
[00:01:09.376,000] <inf> bringup: display colour -> magenta
[00:01:09.627,000] <inf> bringup: display colour -> cyan
[00:01:09.821,000] <inf> bringup: display colour -> white
[00:01:10.006,000] <inf> bringup: display colour -> red
[00:01:10.191,000] <inf> bringup: display colour -> green
[00:01:10.375,000] <inf> bringup: display colour -> blue
[00:01:10.726,000] <inf> bringup: display colour -> yellow
[00:01:10.911,000] <inf> bringup: display colour -> magenta
[00:01:10.951,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=226@252,0 | audio blocks=1017 errs=3792 peak=0 |
[00:01:11.231,000] <inf> bringup: display colour -> cyan
[00:01:11.415,000] <inf> bringup: display colour -> white
[00:01:11.817,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=white | touch=231@252,0 | audio blocks=1017 errs=3842 peak=0 |
[00:01:12.338,000] <inf> bringup: display colour -> red
[00:01:12.522,000] <inf> bringup: display colour -> green
[00:01:12.663,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=green | touch=234@204,216 | audio blocks=1017 errs=3892 peak=0 |
[00:01:13.169,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=green | touch=234@204,216 | audio blocks=1017 errs=3942 peak=0 |
[00:01:13.457,000] <inf> bringup: display colour -> blue
[00:01:13.642,000] <inf> bringup: display colour -> yellow
[00:01:13.967,000] <inf> bringup: display colour -> magenta
[00:01:14.169,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=240@252,197 | audio blocks=1017 errs=3992 peak=0 |
[00:01:14.603,000] <inf> bringup: display colour -> cyan
[00:01:14.787,000] <inf> bringup: display colour -> white
[00:01:15.029,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=white | touch=244@213,232 | audio blocks=1017 errs=4042 peak=0 |
[00:01:15.237,000] <inf> bringup: display colour -> red
[00:01:15.699,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=245@252,0 | audio blocks=1017 errs=4092 peak=0 |
[00:01:16.205,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=245@252,0 | audio blocks=1017 errs=4142 peak=0 |
[00:01:16.877,000] <inf> bringup: display colour -> green
[00:01:17.062,000] <inf> bringup: display colour -> blue
[00:01:17.062,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=blue | touch=251@252,0 | audio blocks=1017 errs=4192 peak=0 |
[00:01:17.700,000] <inf> bringup: display colour -> yellow
[00:01:17.885,000] <inf> bringup: display colour -> magenta
[00:01:17.925,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=258@252,0 | audio blocks=1017 errs=4242 peak=0 |
[00:01:18.375,000] <inf> bringup: display colour -> cyan
[00:01:18.559,000] <inf> bringup: display colour -> white
[00:01:18.760,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=white | touch=261@252,184 | audio blocks=1017 errs=4292 peak=0 |
[00:01:19.266,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=white | touch=261@252,184 | audio blocks=1017 errs=4342 peak=0 |
[00:01:19.772,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=white | touch=261@252,184 | audio blocks=1017 errs=4392 peak=0 |
[00:01:20.205,000] <inf> bringup: display colour -> red
[00:01:20.389,000] <inf> bringup: display colour -> green
[00:01:20.611,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=green | touch=263@251,199 | audio blocks=1017 errs=4442 peak=0 |
[00:01:20.902,000] <inf> bringup: display colour -> blue
[00:01:21.284,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=blue | touch=264@219,212 | audio blocks=1017 errs=4492 peak=0 |
[00:01:21.790,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=blue | touch=264@219,212 | audio blocks=1017 errs=4542 peak=0 |
[00:01:22.380,000] <inf> bringup: display colour -> yellow
[00:01:22.564,000] <inf> bringup: display colour -> magenta
[00:01:22.625,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=268@252,0 | audio blocks=1017 errs=4592 peak=0 |
[00:01:23.130,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=268@252,0 | audio blocks=1017 errs=4642 peak=0 |
[00:01:23.636,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=268@252,0 | audio blocks=1017 errs=4692 peak=0 |
[00:01:24.142,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=268@252,0 | audio blocks=1017 errs=4742 peak=0 |
[00:01:24.648,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=268@252,0 | audio blocks=1017 errs=4792 peak=0 |
[00:01:25.154,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=268@252,0 | audio blocks=1017 errs=4842 peak=0 |
[00:01:25.673,000] <inf> bringup: display colour -> cyan
[00:01:25.858,000] <inf> bringup: display colour -> white
[00:01:26.019,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=white | touch=273@252,2 | audio blocks=1017 errs=4892 peak=0 |
[00:01:26.525,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=white | touch=273@252,2 | audio blocks=1017 errs=4942 peak=0 |
[00:01:26.793,000] <inf> bringup: display colour -> red
[00:01:26.978,000] <inf> bringup: display colour -> green
[00:01:27.360,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=green | touch=280@252,0 | audio blocks=1017 errs=4992 peak=0 |
[00:01:27.554,000] <inf> bringup: display colour -> blue
[00:01:27.738,000] <inf> bringup: display colour -> yellow
[00:01:28.187,000] <inf> bringup: display colour -> magenta
[00:01:28.371,000] <inf> bringup: display colour -> cyan
[00:01:28.532,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=cyan | touch=291@232,210 | audio blocks=1017 errs=5042 peak=0 |
[00:01:28.862,000] <inf> bringup: display colour -> white
[00:01:29.047,000] <inf> bringup: display colour -> red
[00:01:29.368,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=293@252,0 | audio blocks=1017 errs=5092 peak=0 |
[00:01:29.874,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=293@252,0 | audio blocks=1017 errs=5142 peak=0 |
[00:01:30.500,000] <inf> bringup: display colour -> green
[00:01:30.685,000] <inf> bringup: display colour -> blue
[00:01:30.745,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=blue | touch=297@252,197 | audio blocks=1017 errs=5192 peak=0 |
[00:01:31.295,000] <inf> bringup: display colour -> yellow
[00:01:31.479,000] <inf> bringup: display colour -> magenta
[00:01:31.580,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=299@238,215 | audio blocks=1017 errs=5242 peak=0 |
[00:01:31.808,000] <inf> bringup: display colour -> cyan
[00:01:32.251,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=cyan | touch=300@252,215 | audio blocks=1017 errs=5292 peak=0 |
[00:01:32.746,000] <inf> bringup: display colour -> white
[00:01:32.930,000] <inf> bringup: display colour -> red
[00:01:33.257,000] <inf> bringup: display colour -> green
[00:01:33.257,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=green | touch=304@221,225 | audio blocks=1017 errs=5342 peak=0 |
[00:01:33.450,000] <inf> bringup: display colour -> blue
[00:01:33.992,000] <inf> bringup: display colour -> yellow
[00:01:34.177,000] <inf> bringup: display colour -> magenta
[00:01:34.277,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=310@229,221 | audio blocks=1017 errs=5392 peak=0 |
[00:01:34.783,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=310@229,221 | audio blocks=1017 errs=5442 peak=0 |
[00:01:34.991,000] <inf> bringup: display colour -> cyan
[00:01:35.454,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=cyan | touch=311@210,200 | audio blocks=1017 errs=5492 peak=0 |
[00:01:35.642,000] <inf> bringup: display colour -> white
[00:01:36.168,000] <inf> bringup: display colour -> red
[00:01:36.289,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=314@207,185 | audio blocks=1017 errs=5542 peak=0 |
[00:01:36.719,000] <inf> bringup: display colour -> green
[00:01:36.904,000] <inf> bringup: display colour -> blue
[00:01:37.125,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=blue | touch=318@226,183 | audio blocks=1017 errs=5592 peak=0 |
[00:01:37.338,000] <inf> bringup: display colour -> yellow
[00:01:37.522,000] <inf> bringup: display colour -> magenta
[00:01:37.965,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=324@252,178 | audio blocks=1017 errs=5642 peak=0 |
[00:01:38.470,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=324@252,178 | audio blocks=1017 errs=5692 peak=0 |
[00:01:38.976,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=324@252,178 | audio blocks=1017 errs=5742 peak=0 |
[00:01:39.482,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=324@252,178 | audio blocks=1017 errs=5792 peak=0 |
[00:01:39.988,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=324@252,178 | audio blocks=1017 errs=5842 peak=0 |
[00:01:40.494,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=324@252,178 | audio blocks=1017 errs=5892 peak=0 |
[00:01:41.000,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=324@252,178 | audio blocks=1017 errs=5942 peak=0 |
[00:01:41.506,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=magenta | touch=324@252,178 | audio blocks=1017 errs=5992 peak=0 |

```

**What I tried / assessment**

> Panel visibly showing a colour? Backlight dimming smooth or stepped? MOSFET
> used yes/no?
>
> Verdict: ☐ PASS x PARTIAL ☐ FAIL ☐ BLOCKED
>
> LCD correctly shows displayed colour and brightness can be adjusted with the potentiometer. What couldn't be verified is the touch coordinates.
> However teh touch is buggy, with one finger touch rotating through multiple colours right after another. At times after holding down on finger lift the colour changes too with a new deteced touch even though it's still the old one.

---

## T06 — Touch XPT2046 (SPI2, CS GPIO7, PENIRQ GPIO15)

**Goal:** the touch controller shares SPI2 with the display and reports
coordinates; each touch rotates the displayed colour.

**Wiring** (bus lines are shared with T05, only these are new)

- T_CS → **GPIO7**
- T_IRQ / PENIRQ → **GPIO15**
- T_CLK / T_DIN / T_DO → shared with **GPIO12 / GPIO11 / GPIO13**

**Steps**

1. Wire, reset.
2. Tap the panel 5 times in different corners.
3. Check that the colour rotates red → green → blue → yellow → magenta → cyan →
   white → red.

**Expected log**

```
[ OK ] touch XPT2046    (SPI2, CS GPIO7)  (attempt 1)
[00:00:0x.xxx,000] <inf> bringup: display colour -> green
...
touch=4@118,203 |
```

`touch=` counts presses and must increment **once per tap**. A permanently
rising counter without touching = floating PENIRQ (interrupt storm).

**Log output**

```text
(paste console output here)

```

**What I tried / assessment**

> Coordinates plausible (0…4095 raw range, corners distinguishable)? Calibration
> values `min-x/max-x/min-y/max-y` in the overlay still fitting?
>
> Verdict: ☐ PASS ☐ PARTIAL ☐ FAIL ☐ BLOCKED x SKIPPED
>
>
>

---

## T07 — INMP441 microphone (I2S0 RX) — known open item

**Goal:** close the open point from the first hardware session (`i2s_read`
returned `-EIO`).

**Wiring**

- VDD → **3V3** (**not** 5 V)
- GND → **GND**
- SCK (bit clock) → **GPIO4**
- WS / LRCL → **GPIO5**
- SD (data out) → **GPIO6**
- L/R → **GND** (selects the left channel)

**Steps**

1. Wire, reset. Keep the wires short (< 15 cm) — I2S at 16 kHz × 32 bit is
   tolerant but not immune.
2. Read the probe report.
3. If `[ -- ] ... (err -5 / -61)`: verify L/R is really on GND, verify VDD is
   3V3, then swap SCK and WS (the most common wiring mix-up) and retest.

**Expected log**

```
[ OK ] mic INMP441      (I2S0)  (attempt 1)
```

Failure modes and their meaning:

- `-19` (`ENODEV`) — I2S device not ready; check `&dma { status = "okay" }` and
  `CONFIG_DMA=y`
- `-5` (`EIO`) — clocks run but no data is latched; wiring of SD/SCK/WS
- `-61` (`ENODATA`) — block read, but all samples identical; SD line dead or mic
  unpowered

**Log output**

```text

ESP-ROM:esp32s3-20210327
Build:Mar 27 2021
rst:0x1 (POWERON),boot:0x8 (SPI_FAST_FLASH_BOOT)
SPIWP:0xee
mode:DIO, clock div:1
load:0x3fc90710,len:0x3158
load:0x40374000,len:0xc6fc
load:0x50000000,len:0x24
SHA-256 comparison failed:
Calculated: 0e4b74c9847d3f6741fe9ce533935d238aa7fd10a7d9a8bbcc79ae8ab729088e
Expected: 0000000040070000000000000000000000000000000000000000000000000000
Attempting to boot anyway...
entry 0x4037993c
I (soc_init): ESP Simple boot
I (soc_init): compile time Aug 14 2026 23:42:03
W (soc_init): Unicore bootloader
I (soc_init): chip revision: v0.2
I (flash_init): Boot SPI Speed : 80MHz
I (flash_init): SPI Mode       : DIO
I (flash_init): SPI Flash Size : 8MB
I (boot): DRAM  : lma=00000020h vma=3fc90710h size=03158h ( 12632)
I (boot): IRAM  : lma=00003180h vma=40374000h size=0c6fch ( 50940)
I (boot): RTC_DATA      : lma=0000f884h vma=50000000h size=00024h (    36)
I (boot): IROM  : lma=00010000h vma=42000000h size=0a130h ( 41264)
I (boot): DROM  : lma=00020000h vma=3c010000h size=03204h ( 12804)
I (boot): libc heap size 292 kB.
I (cache): Instruction cache: size 16KB, 8Ways, cache line size 32Byte
I (spi_flash): detected chip: boya
I (spi_flash): flash io: dio
W (spi_flash): Detected size(16384k) larger than the size in the binary image header(8192k). Using the size in the binary image header.
*** Booting Zephyr OS build v4.4.0-11807-g357467a011cd ***
[00:00:00.238,000] <inf> bringup: === Stethoscope hardware bring-up ===
[00:00:00.256,000] <inf> bringup: ---- peripheral probe: 8 of 8 connected (max 3 retries each) ----
[00:00:00.256,000] ESP-ROM:esp32s3-20210327
Build:Mar 27 2021
rst:0x1 (POWERON),boot:0x8 (SPI_FAST_FLASH_BOOT)
SPIWP:0xee
mode:DIO, clock div:1
load:0x3fc90710,len:0x3158
load:0x40374000,len:0xc6fc
load:0x50000000,len:0x24
SHA-256 comparison failed:
Calculated: 0e4b74c9847d3f6741fe9ce533935d238aa7fd10a7d9a8bbcc79ae8ab729088e
Expected: 0000000040070000000000000000000000000000000000000000000000000000
Attempting to boot anyway...
entry 0x4037993c
I (soc_init): ESP Simple boot
I (soc_init): compile time Aug 14 2026 23:42:03
W (soc_init): Unicore bootloader
I (soc_init): chip revision: v0.2
I (flash_init): Boot SPI Speed : 80MHz
I (flash_init): SPI Mode       : DIO
I (flash_init): SPI Flash Size : 8MB
I (boot): DRAM  : lma=00000020h vma=3fc90710h size=03158h ( 12632)
I (boot): IRAM  : lma=00003180h vma=40374000h size=0c6fch ( 50940)
I (boot): RTC_DATA      : lma=0000f884h vma=50000000h size=00024h (    36)
I (boot): IROM  : lma=00010000h vma=42000000h size=0a130h ( 41264)
I (boot): DROM  : lma=00020000h vma=3c010000h size=03204h ( 12804)
I (boot): libc heap size 292 kB.
I (cache): Instruction cache: size 16KB, 8Ways, cache line size 32Byte
I (spi_flash): detected chip: boya
I (spi_flash): flash io: dio
W (spi_flash): Detected size(16384k) larger than the size in the binary image header(8192k). Using the size in the binary image header.
*** Booting Zephyr OS build v4.4.0-11807-g357467a011cd ***
[00:00:00.238,000] <inf> bringup: === Stethoscope hardware bring-up ===
[00:00:00.256,000] <inf> bringup: ---- peripheral probe: 8 of 8 connected (max 3 retries each) ----
[00:00:00.256,000] <inf> bringup: [ OK ] pushbutton + LED (GPIO16/17)  (attempt 1)
[00:00:00.262,000] <inf> bringup: [ OK ] SP3T switch      (GPIO18/21/38)  (attempt 1)
[00:00:00.270,000] <inf> bringup: [ OK ] potentiometer    (GPIO1, ADC1_CH0)  (attempt 1)
[00:00:00.279,000] <inf> bringup: [ OK ] backlight PWM    (GPIO8, LEDC ch0)  (attempt 1)
[00:00:00.287,000] <inf> bringup: [ OK ] display ILI9341  (SPI2, CS GPIO10)  (attempt 1)
[00:00:00.296,000] <inf> bringup: [ OK ] touch XPT2046    (SPI2, CS GPIO7)  (attempt 1)
[00:00:00.304,000] <inf> bringup: [ OK ] mic INMP441      (I2S0)  (attempt 1)
[00:00:00.312,000] <inf> bringup: [ OK ] DAC PCM5102A     (I2S1)  (attempt 1)
[00:00:00.484,000] <inf> bringup: display colour -> red
[00:00:00.484,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=2486mV | backlight=75% | colour=red | touch=0@0,0 | audio blocks=0 errs=0 peak=0 |
[00:00:00.492,000] <inf> bringup: audio loopback running (INMP441 -> PCM5102A)
[00:00:00.995,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=31 errs=0 peak=851 |
[00:00:01.499,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=62 errs=0 peak=3067 |
[00:00:02.004,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=94 errs=0 peak=2290 |
[00:00:02.509,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=126 errs=0 peak=1196 |
[00:00:03.014,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=157 errs=0 peak=707 |
[00:00:03.519,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=189 errs=0 peak=419 |
[00:00:04.024,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=220 errs=0 peak=408 |
[00:00:04.529,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=252 errs=0 peak=199 |
[00:00:05.034,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=283 errs=0 peak=276 |
[00:00:05.539,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=2486mV | backlight=75% | colour=red | touch=0@0,0 | audio blocks=315 errs=0 peak=81 |
[00:00:06.043,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=2978mV | backlight=90% | colour=red | touch=0@0,0 | audio blocks=346 errs=0 peak=214 |
[00:00:06.548,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=378 errs=0 peak=331 |
[00:00:07.053,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=410 errs=0 peak=269 |
[00:00:07.558,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=441 errs=0 peak=3647 |
[00:00:08.063,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=473 errs=0 peak=5289 |
[00:00:08.568,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=504 errs=0 peak=31407 |
[00:00:09.073,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=2927mV | backlight=88% | colour=red | touch=0@0,0 | audio blocks=536 errs=0 peak=732 |
[00:00:09.578,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=2950mV | backlight=89% | colour=red | touch=0@0,0 | audio blocks=567 errs=0 peak=275 |
[00:00:10.083,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=599 errs=0 peak=143 |
[00:00:10.588,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=630 errs=0 peak=399 |
[00:00:11.093,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=662 errs=0 peak=842 |
[00:00:11.598,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=694 errs=0 peak=360 |
[00:00:12.103,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=725 errs=0 peak=13590 |
[00:00:12.608,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=757 errs=0 peak=441 |
[00:00:13.113,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=788 errs=0 peak=1158 |
[00:00:13.618,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=820 errs=0 peak=1859 |
[00:00:14.123,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=851 errs=0 peak=141 |
[00:00:14.628,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=883 errs=0 peak=266 |
[00:00:15.132,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=915 errs=0 peak=836 |
[00:00:15.637,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=946 errs=0 peak=810 |
[00:00:16.142,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=978 errs=0 peak=8024 |
[00:00:16.647,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=1009 errs=0 peak=3353 |
[00:00:17.152,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=1041 errs=0 peak=4625 |
[00:00:17.657,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=1072 errs=0 peak=16062 |
[00:00:18.163,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=1104 errs=0 peak=29166 |
[00:00:18.668,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=1135 errs=0 peak=32643 |
[00:00:19.173,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=1167 errs=0 peak=32566 |
[00:00:19.678,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=1199 errs=0 peak=13231 |
[00:00:20.183,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=1230 errs=0 peak=27969 |
[00:00:20.689,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=1262 errs=0 peak=515 |
[00:00:21.194,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=1293 errs=0 peak=4588 |
[00:00:21.699,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=1325 errs=0 peak=3443 |
[00:00:22.204,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=1356 errs=0 peak=2319 |
[00:00:22.709,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=1388 errs=0 peak=1362 |
[00:00:23.214,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=1420 errs=0 peak=656 |
[00:00:23.719,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=1451 errs=0 peak=368 |
[00:00:24.224,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=1483 errs=0 peak=223 |
[00:00:24.729,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=1514 errs=0 peak=613 |
[00:00:25.234,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=1546 errs=0 peak=265 |
[00:00:25.739,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=1577 errs=0 peak=195 |
[00:00:26.244,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=1609 errs=0 peak=129 |
[00:00:26.749,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=1641 errs=0 peak=159 |
[00:00:27.254,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=1672 errs=0 peak=286 |
[00:00:27.759,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=1704 errs=0 peak=151 |
[00:00:28.264,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=1735 errs=0 peak=2381 |
[00:00:28.769,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=1767 errs=0 peak=1667 |
[00:00:29.274,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=1798 errs=0 peak=298 |
[00:00:29.779,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=3083mV | backlight=93% | colour=red | touch=0@0,0 | audio blocks=1830 errs=0 peak=599 |

```

**What I tried / assessment**

> Which wiring variants were tried? Any pin change vs. the list above?
>
> Verdict: x PASS ☐ PARTIAL ☐ FAIL ☐ BLOCKED
>
> Used was given pin out layout and working was confirmed by looking at audio peaks.
>

---

## T08 — PCM5102A DAC (I2S1 TX)

**Goal:** the DAC accepts an I2S TX stream (probe writes one silent block).

**Wiring**

- VIN → **5V** (module has its own 3.3 V regulator)
- GND → **GND**
- SCK → **GND** ⚠️ enables the internal PLL — floating = silence
- BCK → **GPIO40**
- LCK (LRCK) → **GPIO41**
- DIN → **GPIO42**
- FLT / DEMP / FMT → **GND**
- XSMT (silkscreen often `XMT`) → **3V3** (active low — LOW mutes everything)
- L / R / G → jack tip / ring / sleeve

**Steps**

1. Wire, reset.
2. Read the probe report. This test only needs the mic **not** to be present —
   the loopback thread stays off, but the DAC probe must still pass.

**Expected log**

```
[ OK ] DAC PCM5102A     (I2S1)  (attempt 1)
[00:00:0x.xxx,000] <wrn> bringup: audio loopback disabled: microphone missing
```

(The warning is expected as long as T07 is still open.)

**Log output**

```text

ESP-ROM:esp32s3-20210327
Build:Mar 27 2021
rst:0x1 (POWERON),boot:0x8 (SPI_FAST_FLASH_BOOT)
SPIWP:0xee
mode:DIO, clock div:1
load:0x3fc90710,len:0x3158
load:0x40374000,len:0xc6fc
load:0x50000000,len:0x24
SHA-256 comparison failed:
Calculated: 0e4b74c9847d3f6741fe9ce533935d238aa7fd10a7d9a8bbcc79ae8ab729088e
Expected: 0000000040070000000000000000000000000000000000000000000000000000
Attempting to boot anyway...
entry 0x4037993c
I (soc_init): ESP Simple boot
I (soc_init): compile time Aug 14 2026 23:42:03
W (soc_init): Unicore bootloader
I (soc_init): chip revision: v0.2
I (flash_init): Boot SPI Speed : 80MHz
I (flash_init): SPI Mode       : DIO
I (flash_init): SPI Flash Size : 8MB
I (boot): DRAM  : lma=00000020h vma=3fc90710h size=03158h ( 12632)
I (boot): IRAM  : lma=00003180h vma=40374000h size=0c6fch ( 50940)
I (boot): RTC_DATA      : lma=0000f884h vma=50000000h size=00024h (    36)
I (boot): IROM  : lma=00010000h vma=42000000h size=0a130h ( 41264)
I (boot): DROM  : lma=00020000h vma=3c010000h size=03204h ( 12804)
I (boot): libc heap size 292 kB.
I (cache): Instruction cache: size 16KB, 8Ways, cache line size 32Byte
I (spi_flash): detected chip: boya
I (spi_flash): flash io: dio
W (spi_flash): Detected size(16384k) larger than the size in the binary image header(8192k). Using the size in the binary image header.
*** Booting Zephyr OS build v4.4.0-11807-g357467a011cd ***
[00:00:00.238,000] <inf> bringup: === Stethoscope hardware bring-up ===
[00:00:00.504,000] <inf> bringup: ---- peripheral probe: 7 of 8 connected (max 3 retries each) ----
[00:00:00.504,000] <inf> bringup: [ OK ] pushbutton + LED (GPIO16/17)  (attempt 1)
[00:00:00.510,000] <inf> bringup: [ OK ] SP3T switch      (GPIO18/21/38)  (attempt 1)
[00:00:00.519,000] <inf> bringup: [ OK ] potentiometer    (GPIO1, ADC1_CH0)  (attempt 1)
[00:00:00.527,000] <inf> bringup: [ OK ] backlight PWM    (GPIO8, LEDC ch0)  (attempt 1)
[00:00:00.536,000] <inf> bringup: [ OK ] display ILI9341  (SPI2, CS GPIO10)  (attempt 1)
[00:00:00.544,000] <inf> bringup: [ OK ] touch XPT2046    (SPI2, CS GPIO7)  (attempt 1)
[00:00:00.553,000] <inf> bringup: [ OK ] DAC PCM5102A     (I2S1)  (attempt 1)
[00:00:00.560,000] <wrn> bringup: [ -- ] mic INMP441      (I2S0)  not connected (err -61) - check BCLK/WS/SD and L/R to GND
[00:00:00.737,000] <inf> bringup: display colour -> red
[00:00:00.737,000] <wrn> bringup: audio loopback disabled: microphone missing
[00:00:00.739,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=114mV | backlight=3% | colour=red | touch=0@0,0 |
[00:00:01.252,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=167mV | backlight=5% | colour=red | touch=0@0,0 |
[00:00:01.754,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=171mV | backlight=5% | colour=red | touch=0@0,0 |
[00:00:02.257,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=167mV | backlight=5% | colour=red | touch=0@0,0 |
[00:00:02.760,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=155mV | backlight=4% | colour=red | touch=0@0,0 |
[00:00:03.262,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=147mV | backlight=4% | colour=red | touch=0@0,0 |
[00:00:03.765,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=147mV | backlight=4% | colour=red | touch=0@0,0 |
[00:00:04.267,000] <inf> bringup: btn=0 led=0 | sw=2 | poti=155mV | backlight=4% | colour=red | touch=0@0,0 |

```

**What I tried / assessment**

> Was SCK really tied to GND and XSMT to 3V3? Output measured (line level
> ≈ 2.1 V<sub>RMS</sub>) or only probed?
>
> Verdict: x PASS ☐ PARTIAL ☐ FAIL ☐ BLOCKED
>
> Message confirmed via logs.
>

---

## T09 — Audio loopback INMP441 → PCM5102A (requires T07 + T08)

**Goal:** the end-to-end audio path works — this is the core signal path of the
thesis.

**Wiring:** T07 and T08 wired at the same time, plus headphones/line input on the
DAC jack.

**Steps**

1. Both mic and DAC wired, reset.
2. Confirm the loopback thread started.
3. Tap / speak near the mic, watch `peak=` react, and listen on the DAC output.
4. Let it run ≥ 60 s and check that `errs=` stays constant.

**Expected log**

```
[ OK ] mic INMP441      (I2S0)  (attempt 1)
[ OK ] DAC PCM5102A     (I2S1)  (attempt 1)
[00:00:0x.xxx,000] <inf> bringup: audio loopback running (INMP441 -> PCM5102A)
...
audio blocks=812 errs=0 peak=91 |
audio blocks=1624 errs=0 peak=1043 |    <- while tapping the mic
```

Acceptance: `blocks=` rises steadily, `errs=` stays at (or near) 0, `peak=`
clearly tracks the input level, and the signal is audible without dropouts.

> Output is line level, not headphone drive — quiet headphones are expected and
> not a defect. A buffer/amplifier stage is still an open hardware item.

**Log output**

```text
(paste console output here)

```

**What I tried / assessment**

> `errs=` after 60 s: ______ · audible latency subjectively: ______ ·
> dropouts yes/no?
>
> Verdict: ☐ PASS ☐ PARTIAL ☐ FAIL ☐ BLOCKED x SKIPPED
>
>
>

---

## T10 — Full assembly, all components at once

**Goal:** no cross-interference — SPI, I2S, ADC, PWM and GPIO coexist, the power
budget holds, input response stays <=35 ms, and all thread/ISR stacks retain at
least 25% headroom.

**Wiring:** everything from T01–T09 connected simultaneously.

**Steps**

1. Build with `--pristine` and `-DEXTRA_CONF_FILE=qc.conf`, flash, reset, and
   read the evidence-qualified probe report. Do not interpret
   `controller-ready` or `transfer-accepted` as physical proof.
2. Exercise every input once (button, switch through all 3 positions, poti sweep,
   touch, tap the mic).
3. Let it run >=10 min while repeatedly redrawing and generating audio; capture
   the 10-second thread-analyzer reports, ISR stack, `input-latency-max`, audio
   counters and any brownout/reset.
4. Fail if a sentinel/analyzer warning occurs, any stack has <25% headroom,
   input latency exceeds 35 ms, audio stops, or the boot banner repeats.

**Expected log**

```
---- peripheral probe: 8 of 8 operational (max 4 attempts each) ----
[ OK ] pushbutton + LED (GPIO16/17) (controller-ready, attempt 1)
[ OK ] SP3T switch (GPIO18/21/38) (physical-response, attempt 1)
[ OK ] potentiometer (GPIO1, ADC1_CH0) (transfer-accepted, attempt 1)
[ OK ] backlight PWM (GPIO8, LEDC ch0) (controller-ready, attempt 1)
[ OK ] display ILI9341 (SPI2, CS GPIO10) (transfer-accepted, attempt 1)
[ OK ] touch XPT2046 (SPI2, CS GPIO7) (controller-ready, attempt 1)
[ OK ] mic INMP441 (I2S0) (physical-response, attempt 1)
[ OK ] DAC PCM5102A (I2S1) (transfer-accepted, attempt 1)
...
btn=0 led=1 | sw=2 | poti=1780mV | backlight=53% | colour=blue | touch=4@118,203 | audio blocks=812 errs=0 peak=91 |
```

No `Booting Zephyr OS` line may appear a second time — that would be a reset
(brownout).

**Log output**

```text
(paste console output here)

```

**What I tried / assessment**

> Any component that only fails in the full assembly? Power supply used
> (1 or 2 USB cables / external 5 V)?
>
> Verdict: ☐ PASS ☐ PARTIAL ☐ FAIL ☐ BLOCKED x SKIPPED
>
>
>

---

## Summary

One line per test, format `verdict — note`:

- T00 Boot + console — **PASS** — toolchain, flash and console work; probe report as specified.
- T01 Pushbutton + LED — **PASS** — LED toggles exactly once per press, visually confirmed. `btn=1` rarely appearing is the 500 ms sampling interval aliasing a short press, not a defect.
- T02 SP3T pos. 1 + 2 — **PARTIAL** — only `sw=1` and `sw=2` ever appear. Root cause: the fitted part is a **3PDT (3-pole, double-throw) = 2 positions**, so a third position is physically impossible. Wrong component, not a wiring or solder fault.
- T03 SP3T pos. 3 (GPIO38) — **SKIPPED** — untestable until a real 1P3T/SP3T switch is fitted. GPIO38 vs GPIO48 is therefore still unresolved.
- T04 Potentiometer — **PASS** — 0 mV … 3083 mV over full travel, monotonic, no jumps. 3083 mV is the expected `ADC_GAIN_1_4` ceiling.
- T05 Display + backlight — **PARTIAL** — panel shows the correct colour and the poti dims the backlight smoothly (no MOSFET fitted). Two defects observed: touch fires several events per tap, and the audio stream dies permanently at the first display redraw (see below).
- T06 Touch — **SKIPPED** as a standalone test, but exercised in T05: counter jumps 5→9→13→21→27 per tap, `x` saturates at 252 (outside `touchscreen-size-x = <240>`), `y` collapses to 0. Calibration in the overlay does not match this panel.
- T07 Mic INMP441 — **PASS** — `peak=` tracks real sound (81 … 32643), `errs=0` over 30 s with the documented pin map. The earlier `-EIO` / `-61` is closed.
- T08 DAC PCM5102A — **PASS (probe only)** — I2S1 accepts a block. This does **not** prove sound leaves the jack; I2S TX is write-only and passes with the module unplugged.
- T09 Audio loopback — **SKIPPED** — not run. This is the core signal path of the thesis and remains completely unverified.
- T10 Full assembly — **SKIPPED** — not run. Would currently fail on the T05 audio defect.

**Overall conclusion / follow-up actions**

> The session physically verified board boot, button/LED, ADC/potentiometer,
> visible display/backlight behavior and the I2S microphone with the documented
> pin map. It did not verify a third switch position, accurate touch coordinates,
> PCM5102A output, end-to-end audio, or simultaneous operation.
>
> Hardware:
>
> 1. **Wrong switch fitted.** A 3PDT has two positions. Replace with a genuine
>    1P3T (SP3T) slide/rotary switch, then re-run T02 and T03. Only after that
>    does the GPIO38-vs-GPIO48 question become meaningful.
> 2. **DAC output never verified acoustically.** `[ OK ]` on I2S1 is not
>    evidence of sound. Confirm SCK→GND and XSMT→3V3, then run T09 with
>    headphones/line-in on the jack. Biggest open risk in the whole build.
> 3. One unexplained reset in the T07 log — the boot banner restarts mid-line at
>    `[00:00:00.256,000] ESP-ROM:...`. If RST was not pressed this is a brownout
>    with the backlight at 93 % on a single USB feed. Watch for it in T10 and use
>    both USB-C cables.
>
> Firmware (blocks T09 and T10, no parts to replace):
>
> 4. **I2S RX dies permanently on the first display redraw.** In T05 `blocks=`
>    freezes at 1017 at `00:00:17` while `errs=` climbs by exactly 50 per status
>    line (= 100/s, matching the 10 ms retry). A full-screen fill is
>    240×320×2 = 150 kB at 10 MHz ≈ 120 ms of blocking, which overruns the RX
>    ring; the stream then sits in `I2S_STATE_ERROR` and `src/main.c` only counts
>    errors instead of recovering it. Fix: on error do
>    `i2s_trigger(DROP)` → `PREPARE` → `START`, and reduce/deprioritise the
>    display fill.
> 5. **Touch needs calibration and debouncing.** Correct
>    `min-x/max-x/min-y/max-y` for this panel and add a press/release edge filter
>    so one finger press produces one event.
>
> Recommended order: (1) swap switch → (4) fix I2S recovery → (2) run T09 →
> (5) calibrate touch, re-run T06 → then T10.

**Pin map changes made during testing** — transfer into
`boards/esp32s3_devkitc_procpu.overlay` and the README pin map. One line per
change, format `component: old pin → new pin (reason)`:

> None. All tests were run with the pin map as documented above; no overlay pin
> assignment was changed.
>
> Still open: SP3T throw 3 may have to move GPIO38 → GPIO48 (onboard WS2812 on
> DevKitC-1 v1.1) — cannot be decided until a real 1P3T switch is fitted.

---

## 19.08.2026 refactored-firmware evaluation

Source: Git commit `39a94db58d42147667e936b4d71734fce47274d0`
plus the uncommitted QC refactor. Zephyr revision
`357467a011cd2557a1a3f0b4be83d817c4addc9b`; SDK 1.0.1. The source compiled
pristinely for ESP32-S3 with both normal and QC configurations, and all seven
native_sim ztests passed. No board was attached, flashed or monitored during
this evaluation. These are the physical verdicts, mirrored exactly in the
`39a94db...+working-tree` JSON record:

- T00 — Verdict: BLOCKED — no flash or console capture.
- T01 — Verdict: BLOCKED — IRQ/debounce compiled; no button, LED or <=35 ms scope measurement.
- T02 — Verdict: BLOCKED — decoder simulated; no fitted switch exercised.
- T03 — Verdict: BLOCKED — no genuine 1P3T/SP3T part available.
- T04 — Verdict: BLOCKED — conversion boundaries simulated; no ADC/PWM hardware run.
- T05 — Verdict: BLOCKED — chunked redraw compiled; no panel/audio concurrency observation.
- T06 — Verdict: BLOCKED — event/color transitions simulated; calibration not measured.
- T07 — Verdict: BLOCKED — microphone input not captured.
- T08 — Verdict: BLOCKED — DAC output not measured electrically or acoustically.
- T09 — Verdict: BLOCKED — end-to-end loopback not run.
- T10 — Verdict: BLOCKED — simultaneous load, high-water marks and power stability not captured.

Do not replace these with the 14.08.2026 verdicts. Commit the final firmware,
flash that exact commit, execute T00–T10, retain logs/scope traces/analyzer
output, and add a new commit-keyed JSON session.
