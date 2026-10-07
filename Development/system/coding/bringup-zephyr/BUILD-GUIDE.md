# Evaluation firmware build and flash

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
a build of every push (`PR #N`, newest only, deleted when the PR closes). *Run workflow*
builds any branch; dispatching `integration` also publishes it. Daily changed
`integration` builds are published too (newest only). See
[CI quality gates](../../testing/CI-QUALITY-GATES.md).

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

Hardware flashing, serial and device-network operations require owner authorization.
Review the [hardware guide](HARDWARE.md) before connecting the assembly.

Updated by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
