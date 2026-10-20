# Thesis firmware — layer structure

This directory records the Zephyr/ESP32-S3 layer structure from the saved
architecture decision. The thesis firmware lives here (decided 14 October,
[D11](../../planning/implementation-readiness.md#decision-register)); the
[evaluation firmware](../bringup-zephyr/README.md) remains separate.

The table uses the existing skeleton folder names. L1 holds thin hardware adapters
over Zephyr drivers and pure C libraries; L2 orchestrates them, as decided on
[13 October](../../planning/mvp-decisions-2026-10-13.md). [Detailed design](../../design/interfaces-and-behavior.md#static-dependency-and-module-map)
maps its logical components to these folders.

| Folder | Contents | May depend on |
|---|---|---|
| `L2_application/L2_CONTROL/` | Single writer of mode state; grants the network lease | L1, `common` |
| `L2_application/L2_AUDIO/` | Audio path and BPM worker, driven by control commands | L1, `common` |
| `L2_application/L2_COMMUNICATION/` | Builds via FHIR, sends via WIFI under the lease; pre-send assignment check; hotspot portal | L1, `common` |
| `L2_application/L2_SHELL/` | Shell commands and read-back through CONTROL | L2_CONTROL, `common` |
| `L1_services/` adapters | `L1_I2S` (mic RX, DAC TX), `L1_WIFI`, `L1_PHYSICALINTERFACE` (buttons, LEDs) | Zephyr, `common` |
| `L1_services/` libraries | `L1_FILTER`, `L1_BPM` (envelope, autocorrelation, aggregation), `L1_FHIR` (serialization); pure C | `common` |
| `L0_platform/` | Empty: Zephyr drivers and the board overlay | — |
| `MONITOR/` | Runtime supervision | All layers, read-only |
| `common/` | Shared audio/event/result types | Nothing |
| `tests/host/` | Library tests on recorded WAVs | L1 libraries, `common` |

Display/UI, touch, SD storage and replay (WSOLA) are optional and not part of the skeleton yet.

## Building the skeleton

This directory is a standalone Zephyr application. `common/main.c` returns to the idle
thread; the component `.c` / `.h` files reserve places for implementation and
declare no APIs yet. `common/types.h` reserves the shared data types.
The board overlay and `prj.conf` set the fitted N16R8 module (16 MB flash,
8 MB octal PSRAM; GPIO33–37 stay reserved). The serial shell and deferred logging
are enabled; no audio processing, networking, storage, UI or monitoring is active.

### Shell and configuration

The shell uses the board's `zephyr,shell-uart` (`uart0`, 115200 baud). Built-in
commands provide help, tab completion, device information and kernel diagnostics,
including thread lists and stack usage. Run `help`, `device list`,
`kernel version`, `kernel uptime`, `kernel thread list`, `kernel thread stacks`
or `log status`. The `log` commands can adjust runtime log filters within the
levels compiled into the firmware.
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
Development/system/coding/tools/build-firmware.ps1 -Pristine   # clean rebuild
Development/system/coding/tools/build-firmware.ps1 -Target bringup   # evaluation firmware -> build-eval/
```

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

Without `--application`, `run_ci.py build` also compiles this skeleton to
`build-ci-app`, before building and packaging the bring-up firmware. The skeleton
is not packaged or published as the bring-up firmware. The pure C library placeholders
will gain host tests in `tests/host` when their behavior is implemented.

## Layer rules

Calls go downward; upward notifications use events/message queues. Zephyr owns
drivers, DMA and interrupts. L1 libraries include no Zephyr headers; each caller owns
its own filter instance, so listening and BPM analysis filters stay independent.
Only L2_CONTROL writes mode state; SHELL commands go through it. L2_COMMUNICATION is
the only path to a WIFI send and runs the pre-send assignment check, while
MON observes it. Start on one core and measure before adding another.

[Detailed design](../../design/interfaces-and-behavior.md) defines contracts and
ownership. [Product scope](../../spec/product-scope.md) and the
[risk/readiness register](../../planning/implementation-readiness.md) qualify
class B/SOUP intentions and monitoring controls; classification and hazards require
substantiation.

Updated by Claude-Opus-5.5 on behalf of Nico running in T3 Code through Claude Code.
