# Application firmware: layer structure

The application firmware runs on Zephyr on the ESP32-S3.

Layer 1 (`L1_services/`) holds thin hardware adapters
over Zephyr drivers and pure C libraries; layer 2 (`L2_application/`) orchestrates them. The [firmware structure](../../architecture/system/firmware-structure.md#static-dependency-and-module-map)
maps the logical components to the application folders.

`L1_WIFI` and `L2_COMMUNICATION` implement the [Wi-Fi contract](../../design/WIFI/interfaces-and-behavior.md).
`L1_PORTAL` implements the [portal contract](../../design/PORTAL/interfaces-and-behavior.md);
`L2_COMMUNICATION` consumes its requests and publishes its state.

| Folder | Contents | May depend on |
|---|---|---|
| `L2_application/L2_CONTROL/` | Single writer of mode state; grants the network lease | `L2_AUDIO`, `L2_COMMUNICATION`, L1, `common` |
| `L2_application/L2_AUDIO/` | Audio path, driven by control commands | L1, `common` |
| `L2_application/L2_COMMUNICATION/` | Builds via `L1_FHIR`, sends via `L1_WIFI` under the lease; Device registration; hotspot Wi-Fi setup page | L1, `common` |
| `L2_application/L2_SHELL/` | Application shell commands; contains no commands | `L2_CONTROL`, `common` |
| `L1_services/` adapters | `L1_I2S` (microphone RX, DAC TX), `L1_WIFI`, `L1_PORTAL` (Wi-Fi setup page), `L1_STORAGE` (settings records in flash), `L1_PHYSICALINTERFACE` (button, switch, potentiometer, status light, button light) | Zephyr, `common`; `L1_WIFI` also the Espressif HAL and mbedTLS; `L1_PORTAL` also `L1_WIFI` |
| `L1_services/` libraries | `L1_FHIR` (serialization); `L1_FILTER` and `L1_BPM`, which contain no logic; pure C | `common` |
| `L0_platform/` | Empty: Zephyr drivers and the board overlay | — |
| `MONITOR/` | Runtime supervision; contains no checks | All layers, read-only |
| `common/` | `main.c`, the catalogue codes (`feedback.h`) and `types.h`, which defines no type | Nothing |

## Building the application

This directory is a standalone Zephyr application. `common/main.c` initializes
`L2_CONTROL` and `L2_COMMUNICATION`, completes startup and returns. `L1_I2S` and
`L2_AUDIO` stream microphone audio to the DAC and apply the volume. `L1_PHYSICALINTERFACE`
handles the button, filter switch, volume potentiometer, status light and button light.
`L1_STORAGE` persists settings and reads the server profile. `L1_WIFI`, `L1_PORTAL`,
`L1_FHIR` and `L2_COMMUNICATION` handle Wi-Fi, the setup portal, Device registration and
FHIR delivery. `L1_FILTER`, `L1_BPM`, `L2_SHELL`, `MONITOR` and `common/types.h` contain
no logic. The board overlay and `prj.conf` configure the N16R8 module
(16 MB flash, 8 MB octal PSRAM; GPIO33–37 reserved), the serial shell and deferred
logging.

### Physical inputs

`L1_PHYSICALINTERFACE` reports debounced, timestamped input events to `L2_CONTROL` on the
system work queue ([input contract](../../design/cross-module.md#design-constraints)):

| Input | Pins | Acquisition | Event |
|---|---|---|---|
| Start/Stop button J6 | GPIO16 | Edge interrupt starts a 30 ms debounce ([P10](../../design/cross-module.md#parameters)) | Short press; long press after 2 s |
| Raw/Murmur/BPM switch J8 | GPIO18/21/38 | Polled every 10 ms, 30 ms debounce (P10) | First stable position, then one per stable transition |
| Volume potentiometer J7 | GPIO1, ADC1 channel 0 | Polled every 50 ms | First reading, then each change of status, of at least 2 %, or to 0 % or 100 % |

The switch is polled because Murmur and BPM leave all three pins high at rest. On the
fitted J8 switch, the common contact connects to the GPIO18 pad, so `L1_PHYSICALINTERFACE`
drives GPIO18 low to distinguish Murmur and BPM.
The volume is clamped to 0–100 %, with 100 % mapped to 3083 mV (P10).

A reading that cannot be used carries a status and a safe value. FAILED marks an ADC
or GPIO failure or a switch position that stays invalid for the debounce time; ABSENT
marks a potentiometer that is not fitted. The safe values are Raw and 0 %, so an unusable
input mutes the audio. The 30 ms debounce also applies to slow switch
slides: a pause of 30 ms or more between positions is reported FAILED; `L2_CONTROL` evaluates the
position at Start and while listening. J7 is fitted, so
`CONFIG_PHYSICALINTERFACE_VOLUME_POTENTIOMETER_FITTED` is on by default and the ADC is read; with
the option off, the ADC is not read and the volume is reported ABSENT once.

`L2_CONTROL` passes the volume to `L2_AUDIO`, which applies it as a linear gain of 0–100 % with
saturation to every block; a failed or absent reading gives 0 %.
The switch position selects no filter, and all three positions pass audio through unfiltered.
`L2_CONTROL` keeps the last stable switch reading and latches CONTROL_INPUT_FAILURE when there is no valid position at
Start, or none for at least 1 s while listening; a failed reading outside these cases
latches nothing, because slow slides report FAILED for a moment. A failed potentiometer
reading also latches CONTROL_INPUT_FAILURE.

### Indication and errors

`physicalinterface_showFeedback()` takes one catalogue code and drives both lights from
one table row: the RGB status light on GPIO48 and the red button light on GPIO17 (J6, active high through the 330 Ω series resistor R12). The red light is steady during the lamp test, repeats an error's
blink code ([P22](../../design/FEEDBACK/parameters.md): 250 ms on and off, 2 s pause) and gives one 1 s flash for
ERROR_ACKNOWLEDGED. `L2_CONTROL` decides which code is shown. It latches every catalogue error
in `control_error_policy.c`, shows the highest priority, then the first latched, and lists every
latched error on the serial log. With an error shown that clears by short press, the first
short press acknowledges it; restart errors ignore the press. Errors other than audio
errors that occur during startup or while listening are latched silently and shown after
the startup or after the manual Stop.
Wi-Fi errors from `L2_COMMUNICATION` pass through the control queue and permit Start.

While the button is down the red light is steady on instead of its code, and the code
resumes at the release. When `L2_CONTROL` accepts a 2 s hold in Idle, the red light blinks at
4 Hz until the release (`FEEDBACK_BUTTON_HOLD_ACKNOWLEDGED`), so the hold does not read as a
2 Hz error code; a hold outside Idle stays steady.

The decoding and debounce logic in `physicalinterface_input.c` has host tests in
`tests/host/l1_physicalinterface/`.

### Shell and configuration

The shell uses the board's `zephyr,shell-uart` (`uart0`, 115200 baud). Built-in
commands provide help, tab completion, device information and kernel diagnostics,
including thread lists and stack usage. Run `help`, `device list`,
`kernel version`, `kernel uptime`, `kernel thread list`, `kernel thread stacks`
or `log status`. The `log` commands can adjust runtime log filters within the
levels compiled into the firmware.

Log output passes two filters. The compile-time level of each module
(`LOG_MODULE_REGISTER(name, LOG_LEVEL_DBG)` or `CONFIG_<MODULE>_LOG_LEVEL`) decides
which calls exist in the firmware. The runtime filter then starts at
`CONFIG_LOG_RUNTIME_DEFAULT_LEVEL`, which is INF in the release profile. Thus `LOG_DBG`
output is hidden by default, even in a module registered at DBG. Run
`log enable dbg <module>` to show it; messages logged before that command are lost.
The debug profile starts the runtime filter at DBG.
`L2_SHELL` has no application commands. Logs use the shell
backend with deferred processing. Command history is disabled so credentials entered
on the shell are not retained. Raw memory access is disabled.

`prj.conf` selects values for options already defined by Zephyr and its modules.
The application `Kconfig` includes `Kconfig.zephyr` as its configuration entry point.
The application `Kconfig` defines one option,
`CONFIG_PHYSICALINTERFACE_VOLUME_POTENTIOMETER_FITTED` (default on), which tells `L1_PHYSICALINTERFACE` whether J7 is fitted.

### Manual build

Provision the pinned toolchain once with
[`setup-toolchain.ps1`](../tools/setup-toolchain.ps1), then build from PowerShell:

```powershell
Development/system/coding/tools/build-firmware.ps1             # this app -> build-app/
Development/system/coding/tools/build-firmware.ps1 -Profile debug   # debug build -> build-app-debug/
Development/system/coding/tools/build-firmware.ps1 -Pristine   # clean rebuild
```

The `release` profile (default) builds `prj.conf` alone.
The `debug` profile merges [`debug.conf`](debug.conf): optimization for GDB, Zephyr
thread information for OpenOCD, DBG logs from boot, assertions, stack sentinels and
execution cycles in `kernel thread list`. Each profile has its own build directory,
so switching does not rebuild everything. The debug profile exists only for this app.

The script uses the board pinned in [`toolchain.json`](../tools/toolchain/toolchain.json) and leaves the shell environment
unchanged. It only builds; it never flashes or publishes. Without PowerShell, activate
the pinned Zephyr environment and run from the repository root:

```sh
west build --pristine=always -b esp32s3_devkitc/esp32s3/procpu Development/system/coding/app -d build-app
```

### Software bill of materials

Generate the SPDX 2.3 SBOM of the release firmware from PowerShell:

```powershell
Development/system/coding/tools/build-sbom.ps1             # build-app/ -> build-app/spdx/
Development/system/coding/tools/build-sbom.ps1 -Pristine   # clean rebuild first
```

The script enables the CMake file-based API, builds the release app and runs
`west spdx --include-sdk`. `prj.conf` enables `CONFIG_BUILD_OUTPUT_META`, which
`west spdx` needs. The output has five documents: `app.spdx` for the application,
`zephyr.spdx` for Zephyr with its modules, `build.spdx` for the build, `modules-deps.spdx`
for the module dependencies and `sdk.spdx` for the Zephyr SDK.

`west spdx` leaves out the Espressif Wi-Fi and PHY binary libraries; their versions are
listed in `hal_espressif`'s `zephyr/module.yml`. On Windows the SBOM contains no application or SDK file entries, because the path check of `west spdx` mixes `/` and `\`. The Zephyr and
module packages carry their commit or release version; the application and SDK
packages carry none, so record the repository commit and SDK version (`toolchain.json`)
alongside the SBOM.

### Manual flash

Connect the board with a USB data cable and find its COM port in Device Manager.
Close any serial monitor, then flash the existing build from PowerShell:

```powershell
Development/system/coding/tools/flash-firmware.ps1 5   # app firmware -> COM5
Development/system/coding/tools/flash-firmware.ps1 5 -Profile debug   # build-app-debug -> COM5
Development/system/coding/tools/flash-firmware.ps1 5 -WhatIf   # show the action only
Development/system/coding/tools/flash-firmware.ps1 5 -Erase   # erase the whole chip, then flash
```

The positional number selects the COM port. The script uses the pinned toolchain
and does not rebuild. `-BuildDir` selects an existing custom build directory;
relative paths resolve from the caller's current directory. Flashing replaces the
firmware on the selected device. If connection fails, hold BOOT, press and release
RESET, release BOOT, check the port again and retry.

Without `-Erase`, flashing keeps the settings partition. `-Erase` erases the whole chip
first, including the saved settings with the Wi-Fi network and the server profile.

To erase only selected partitions instead of the whole chip, select any
combination of them:

```powershell
Development/system/coding/tools/erase-flash.ps1 5 -Settings   # saved settings incl. Wi-Fi -> COM5
Development/system/coding/tools/erase-flash.ps1 5 -Settings -ServerProfile -WhatIf
Development/system/coding/tools/erase-flash.ps1 5 -App   # application; reflash before it boots again
```

The offsets and sizes come from the devicetree of the existing `build-app` build, or
from `-BuildDir`. `-ServerProfile` erases the
[server profile](../server-profiles/README.md).

### Debugging with GDB

The ESP32-S3 has a built-in USB JTAG unit on GPIO19/20, the DevKitC "USB" connector.
No external probe is necessary; the external JTAG pins are not free (GPIO40–42 carry
the DAC I2S signals). Connect both the "UART" connector (console, flashing) and the "USB"
connector (JTAG). Install Espressif's OpenOCD once; the Zephyr SDK OpenOCD cannot
drive this JTAG unit:

```powershell
Development/system/coding/tools/setup-openocd.ps1
```

On Windows, the JTAG interface of the "USB JTAG/serial debug unit" needs the WinUSB
driver. If OpenOCD reports `could not find or open device`, install it with Espressif's
`idf-env driver install --espressif` or with Zadig on interface 2.

Flash the debug build, then start a session:

```powershell
Development/system/coding/tools/flash-firmware.ps1 4 -Profile debug
Development/system/coding/tools/debug-firmware.ps1                 # reset, stop at main
Development/system/coding/tools/debug-firmware.ps1 -Mode attach    # running firmware, no reset
Development/system/coding/tools/debug-firmware.ps1 -Mode server    # GDB server on :3333 for an IDE
```

`debug-firmware.ps1` does not flash; the board runner passes `--no-load`. Debug the
same build that runs on the target, or source lines are wrong. `-Mode attach`
bypasses `west attach`, because the board's GDB init resets the target. GDB lists
Zephyr threads with `info threads`. The chip has two hardware breakpoints and two
watchpoints. A halted CPU stops the I2S DMA, so use logs for audio timing faults.

### Crash decoding

A fatal exception prints a register dump on the console. Copy it, then run:

```powershell
Development/system/coding/tools/decode-crash.ps1                   # dump in clipboard, debug build
Development/system/coding/tools/decode-crash.ps1 -Path crash.txt -Profile release
```

The script resolves PC (faulting instruction) and A0 (caller) to source lines with
`addr2line`. The pinned Zephyr cannot link `CONFIG_XTENSA_ENABLE_BACKTRACE` for the
ESP32-S3 (`xthal_window_spill` is missing), so deeper frames need GDB.

## Layer rules

Calls go downward. Upward notifications use events and message queues. Zephyr owns
drivers, DMA and interrupts. The `L1_services/` libraries include no Zephyr headers.
Only `L2_CONTROL` writes mode state.
`L2_COMMUNICATION` is the only path to an `L1_WIFI` send.

The [firmware structure](../../architecture/system/firmware-structure.md) defines ownership, and the
[cross-module design](../../design/cross-module.md) defines the contracts between modules.

## Wi-Fi teardown before listening

`L2_CONTROL` posts `COMMUNICATION_EVENT_LISTENING_STARTED` and waits on
`communication_waitForWiFiStop()` before starting audio. On wait timeout, `L2_CONTROL`
keeps audio stopped. `L2_COMMUNICATION` acknowledges teardown after `L1_WIFI` and
`L1_PORTAL` confirm cancellation of scans and connect requests and shutdown of the
portal, DHCP server and hotspot. Each new Start invalidates the previous
acknowledgement. An established station association is preserved.

Cleanup tries each pending stop once. If all stops succeed, audio starts normally.
If any stop fails, the communication thread latches `WIFI_CLEANUP_FAILURE`, disables
further Wi-Fi work until restart and still permits audio to start.

While it waits, the communication thread checks for Start events every 200 ms. A settings
write in progress returns before the check, so the teardown latency also includes that write
and the driver shutdown.

## Coding conventions

`.clang-format` in this folder sets the layout (Allman braces, 4 spaces, `if(x)`,
`for(;;)` for the endless loop of each thread). It has no column limit,
so statements stay on one line. Only a call with more than 2 arguments may be split,
by hand, with one argument per line; clang-format keeps and aligns that layout.

Add one blank line after a completed braced block before the next statement.
Add one blank line before `if` statements and loops after preceding statements.
Keep `else`, `else if`, a do/while tail and enclosing closing braces attached.
Separate local variable declarations from executable statements with a blank line.
Separate variable assignments from standalone function calls with a blank line.
Keep related declarations, assignments or calls together in their own groups.

| Item | Rule | Example |
|---|---|---|
| Function | `module_camelCase`, verb first | `wifi_startScan()`, `communication_waitForCondition()` |
| Waiting function | starts with `waitFor` and names what it waits for | `wifi_waitForConnection()` |
| File-scope variable | `module_PascalCase` | `communication_ScanList` |
| Flag (`bool`) | states what is true when set | `communication_StoredNetworkIsValid` |
| Local variable, parameter, struct field | `camelCase` | `idleDeadline`, `listSize`, `needsPassword` |
| Macro, enum constant | `MODULE_UPPER_CASE` | `COMMUNICATION_STORED_CONNECT_ATTEMPTS` |
| Type | `module_snake_case` | `struct wifi_network` |

Names are written out without abbreviations. Unit suffixes use either full unit names
(`_MILLISECONDS`, `_MICROSECONDS`) or unit symbols (`_MS`, `_S`, for example
`COMMUNICATION_RETRY_DELAY_S`). Protocol names such as DHCP or SSID keep their
capitals inside camelCase, for example `wifi_startDHCPServer()` and
`communication_waitForWiFiStop()`. The rule for loops is to terminate
through their condition without `continue` (MISRA C:2012 Rule 15.4; MISRA C:2004
Rule 14.5); `wifi_secure_connection.c` has one `continue` and one `while(true)` loop that
ends by `return`. The rule for functions is one
`return` at the end (MISRA C:2012 Rule 15.5). `L1_FHIR`, `L1_I2S`, `L1_STORAGE`, `L2_AUDIO`
and `L2_CONTROL` follow it throughout. Functions with early returns exist in `wifi.c`,
`wifi_dns.c`, `wifi_secure_connection.c`, `portal.c`, `physicalinterface.c` and
`communication.c`. Every `if … else if` chain ends with `else` (Rule 15.7), and unused return
values are cast to `void` (Rule 17.7). A condition contains only named values, constants
and comparisons. A call, conversion or calculation is assigned to a named `const` variable
before the condition. Doxygen comments use one short `@return` line.
