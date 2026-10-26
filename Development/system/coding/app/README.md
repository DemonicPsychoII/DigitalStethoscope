# Thesis firmware — layer structure

This is the Zephyr/ESP32-S3 thesis application. The [archived bring-up firmware](../../../../preThesis/06-bringup-zephyr/README.md) remains separate pre-thesis material.

The table maps the application folders. L1 holds thin hardware adapters
over Zephyr drivers and pure C libraries; L2 orchestrates them. [Detailed design](../../design/system/interfaces-and-behavior.md#static-dependency-and-module-map)
maps its logical components to these folders.

`L2_COMMUNICATION` implements the [Wi-Fi contract](../../design/WIFI/interfaces-and-behavior.md).
`L1_PORTAL` declares the [portal contract](../../design/PORTAL/interfaces-and-behavior.md);
COMMUNICATION consumes its requests and publishes its state.

| Folder | Contents | May depend on |
|---|---|---|
| `L2_application/L2_CONTROL/` | Single writer of mode state; grants the network lease | L1, `common` |
| `L2_application/L2_AUDIO/` | Audio path and BPM worker, driven by control commands | L1, `common` |
| `L2_application/L2_COMMUNICATION/` | Builds via FHIR, sends via WIFI under the lease; Device registration; hotspot Wi-Fi setup page | L1, `common` |
| `L2_application/L2_SHELL/` | Shell commands and read-back through CONTROL | L2_CONTROL, `common` |
| `L1_services/` adapters | `L1_I2S` (mic RX, DAC TX), `L1_WIFI`, `L1_PORTAL` (Wi-Fi setup page), `L1_STORAGE` (settings records in flash), `L1_PHYSICALINTERFACE` (buttons, LEDs) | Zephyr, `common` |
| `L1_services/` libraries | `L1_FILTER`, `L1_BPM` (envelope, autocorrelation, aggregation), `L1_FHIR` (serialization); pure C | `common` |
| `L0_platform/` | Empty: Zephyr drivers and the board overlay | — |
| `MONITOR/` | Runtime supervision | All layers, read-only |
| `common/` | Shared audio/event/result types | Nothing |

Display/UI, touch, SD storage and replay (WSOLA) are optional and not part of the skeleton yet (TICKET-206, TICKET-202).

## Building the application

This directory is a standalone Zephyr application. `common/main.c` returns to the idle
thread; most component `.c` / `.h` files reserve places for implementation.
`L1_WIFI` wraps the Wi-Fi driver and storage persists its settings.
`L2_COMMUNICATION` implements the Wi-Fi workflow; the HTTP adapter remains unavailable.
`common/types.h` reserves the shared data types.
The board overlay and `prj.conf` set the fitted N16R8 module (16 MB flash,
8 MB octal PSRAM; GPIO33–37 stay reserved). The serial shell and deferred logging
are enabled. The application has not yet been tested on the board.
No audio processing, SD storage, UI or monitoring is active.

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
Application commands in `L2_SHELL` are not implemented yet. Logs use the shell
backend with deferred processing. Command history is disabled because future
provisioning commands can contain credentials; raw memory access is disabled.

`prj.conf` selects values for options already defined by Zephyr and its modules.
The application `Kconfig` includes `Kconfig.zephyr` as its configuration entry point.
No application-specific options are defined yet. A local Kconfig is optional until
the application needs its own options.

### Manual build

Provision the pinned toolchain once with
[`setup-toolchain.ps1`](../tools/setup-toolchain.ps1), then build from PowerShell:

```powershell
Development/system/coding/tools/build-firmware.ps1             # this app -> build-app/
Development/system/coding/tools/build-firmware.ps1 -Profile debug   # debug build -> build-app-debug/
Development/system/coding/tools/build-firmware.ps1 -Pristine   # clean rebuild
Development/system/coding/tools/build-firmware.ps1 -Target bringup   # evaluation firmware -> build-eval/
```

The `release` profile (default) builds `prj.conf` alone, the same configuration as CI.
The `debug` profile merges [`debug.conf`](debug.conf): optimization for GDB, Zephyr
thread information for OpenOCD, DBG logs from boot, assertions, stack sentinels and
execution cycles in `kernel thread list`. Each profile has its own build directory,
so switching does not rebuild everything. The debug profile exists only for this app.

The script uses the board pinned in `toolchain.json` and leaves the shell environment
unchanged. It only builds; it never flashes or publishes. Without PowerShell, activate
the pinned Zephyr environment and run from the repository root:

```sh
west build --pristine=always -b esp32s3_devkitc/esp32s3/procpu Development/system/coding/app -d build-app
```

CI runs the same application build with
`python Development/system/testing/ci/run_ci.py build --application`.

### Manual flash

Connect the board with a USB data cable and find its COM port in Device Manager.
Close any serial monitor, then flash the existing build from PowerShell:

```powershell
Development/system/coding/tools/flash-firmware.ps1 5   # app firmware -> COM5
Development/system/coding/tools/flash-firmware.ps1 5 -Profile debug   # build-app-debug -> COM5
Development/system/coding/tools/flash-firmware.ps1 5 -WhatIf   # show the action only
Development/system/coding/tools/flash-firmware.ps1 5 -Target bringup
```

The positional number selects the COM port. The script uses the pinned toolchain
and does not rebuild. `-BuildDir` selects an existing custom build directory;
relative paths resolve from the caller's current directory. Flashing replaces the
firmware on the selected device. If connection fails, hold BOOT, press and release
RESET, release BOOT, check the port again and retry.

For local PowerShell shortcuts, add aliases to your profile using absolute paths
to `build-firmware.ps1` and `flash-firmware.ps1`, for example `stetho-build` and
`stetho-flash`. Arguments pass through: `stetho-build -Target app -Pristine` and
`stetho-flash 5`.

### Debugging with GDB

The ESP32-S3 has a built-in USB JTAG unit on GPIO19/20, the DevKitC "USB" connector.
No external probe is necessary; the external JTAG pins are not free (GPIO39 is the
speed switch). Connect both the "UART" connector (console, flashing) and the "USB"
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

`run_ci.py build` and `run_ci.py build --application` both compile this application to `build-ci-app`, retain build evidence and stage the single application profile. Daily/dispatch and `firmware`-label publication use that profile. The archived bring-up firmware has local build instructions and no CI.

## Layer rules

Calls go downward; upward notifications use events/message queues. Zephyr owns
drivers, DMA and interrupts. L1 libraries include no Zephyr headers; each caller owns
its own filter instance, so listening and BPM analysis filters stay independent.
Only L2_CONTROL writes mode state; SHELL commands go through it. L2_COMMUNICATION is
the only path to a WIFI send (no pre-send assignment check since 15 October), while
MON observes it. Start on one core and measure before adding another.

[Detailed design](../../design/system/interfaces-and-behavior.md) defines contracts and
ownership. [Product scope](../../spec/product-scope.md) and the
risk/readiness register qualify
class B/SOUP intentions and monitoring controls; classification and hazards require
substantiation.

## Wi-Fi workflow verification

Planned: CONTROL posts `COMMUNICATION_EVENT_LISTENING_STARTED` and waits for
`communication_waitForWiFiStop()` before it starts audio. These names are not yet in
the code or the design. The design requires the acknowledgement to follow L1 confirmation
of scan and connect cancellation and of portal, DHCP and AP shutdown, and a new Start
invalidates the previous acknowledgement. The communication thread stops scans, connect
requests and the setup services, but preserves an established station association.

Cleanup tries each pending stop once. If all stops succeed, audio is released normally.
If any stop fails, the thread latches WIFI_CLEANUP_FAILURE, disables further Wi-Fi work
until restart and releases audio under the REQ-13 Wi-Fi-only exception. It does not
claim confirmed radio shutdown.

The thread uses a candidate 200 ms check interval for Start events. That interval is not
a bound on teardown latency: the time until audio can start also includes the atomic
settings write and the driver shutdown, which are not yet measured.
CONTROL does not call this interface yet.

No application test suite is included yet. The separate test stage will generate communication scenarios from the [Wi-Fi design](../../design/WIFI/interfaces-and-behavior.md) and [portal design](../../design/PORTAL/interfaces-and-behavior.md). CI skips application host execution while that suite is absent; the result reporter remains available for the test stage. Verification case VT-14 remains uncovered. Target timing and CONTROL integration are also pending.

## Coding conventions

`.clang-format` in this folder sets the layout (Allman braces, 4 spaces, `if(x)`,
`for(;;)` for the one intended endless loop); CI checks it. It has no column limit,
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

Names are written out, without abbreviations; units use their symbols as suffix
(`_MS`, `_S`, for example `COMMUNICATION_RETRY_DELAY_S`); protocol names such as DHCP or SSID
stay and keep their capitals inside camelCase, for example `wifi_startDHCPServer()`
and `communication_waitForWiFiStop()`. Every function has one `return` at its end and loops end through their
condition (MISRA C:2012 Rules 15.4 and 15.5; no `continue`, MISRA C:2004 Rule 14.5).
Every `if … else if` chain ends with `else` (Rule 15.7), and unused return values are
cast to `void` (Rule 17.7). Doxygen comments use one short `@return` line.
