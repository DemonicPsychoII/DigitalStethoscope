# Evaluation firmware build and flash

Archived pre-thesis material. This firmware has no continuous integration (CI).

Install the shared pinned tools with
`python Development/system/testing/ci/setup_zephyr.py` from the repository root.
Activate that Zephyr environment, then use the local commands below. The shared
CI build and publication entry points now build only the application firmware.
Archived bring-up builds stay local and are not published by CI.

### Toolchain and commands

The Zephyr, SDK and west pins live in toolchain.json;
the Zephyr west manifest fixes the hal_espressif revision
(`3d4d922a4d2994f844790ec031a584ec71240485` at the current Zephyr pin). See `Development/system/testing/ci/setup_zephyr.sh`
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

Hardware flashing, serial and device-network operations require owner authorization.
Review the [hardware guide](HARDWARE.md) before connecting the assembly.
