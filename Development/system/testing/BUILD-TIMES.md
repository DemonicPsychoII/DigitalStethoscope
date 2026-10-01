# Evaluation firmware builds and build-time comparison

The same entry points work on Windows and Linux. They build the ESP32-S3
evaluation firmware; the host evaluation Python scripts do not need compilation.
Tool versions, board and module selection live in `ci/toolchain.json`.
The ignored `.ci-workspace` contains west, CMake, Ninja, Zephyr, its required
modules, Espressif blobs and the SDK's ESP32-S3 compiler. No shell activation is
needed. Setup downloads are outside the build timer.

## First setup on the Windows desktop

Install Python 3.12+ and Git, then run from the repository root in PowerShell:

```powershell
winget install --id 7zip.7zip -e --silent
python Development/system/testing/ci/setup_zephyr.py
```

The older `Development/system/coding/tools/setup-toolchain.ps1` is separate: it
still provisions its own legacy workspace and does not use these pins. Rerun
`setup_zephyr.py` to complete an interrupted install. It retains
existing sources and downloads; it does not delete the workspace. Legacy
workspaces in `Development/Toolchain/zephyrproject` or
`Development/system/coding/tools/zephyrproject` remain independent.

Linux requires Python 3.12+, Git, Python venv support, xz/tar and the host runtime
prerequisites from [Zephyr's getting-started guide](https://docs.zephyrproject.org/latest/develop/getting_started/index.html).
On the homelab use `python3` for the setup command.

## Repeat the same measurement on every device

```powershell
python Development/system/testing/ci/benchmark_build.py run --device desktop --jobs 4 --runs 3 --include-noop
```

Use `--device laptop` on this laptop. On the server:

```sh
cd ~/DigitalStethoscope-B.Thesis
.ci-workspace/.venv/bin/python Development/system/testing/ci/benchmark_build.py run --device homelab --jobs 4 --runs 3 --include-noop
```

The default `offline` profile is the evaluation image. `--profiles offline qc
network-qc-switch` also exercises stack diagnostics and the combined optional
network/switch image used by CI. All profiles have the same board and source
pins. Every run produces a fresh `zephyr.bin`. Benchmarks do not publish or flash.

Use four jobs for the direct comparison; the homelab has four logical CPUs.
Omit `--jobs` to use the local logical CPU count, or use `--jobs 1 4 16` to
measure scaling. Compare identical job counts separately. The default is one
excluded warm-up followed by three measured runs for each profile/job combination.
`--warmups 0 --runs 1` is useful for a build smoke check.

Each clean run measures pristine CMake configuration and the full compile/link
as separate phases. Total is their sum; metadata checks, downloads and copying
the binary are outside the timer. `--include-noop` also records a subsequent
unchanged build separately. This does **not** measure rebuilding after a source
edit. The compiler cache is disabled. The OS filesystem cache stays in place;
these are warm-filesystem clean builds, not cold-boot measurements. Keep power
mode and concurrent load consistent and record environmental differences.

## Results and comparison

Each invocation writes under `artifacts/build-times/DEVICE-UTC_TIMESTAMP/`:

- `results.json`: machine/OS/CPU, source hashes, commit/dirty status, exact
  compiler/tool versions, timings, exit codes, binary hashes and sizes.
- `results.csv`: one row per warm-up, clean build or no-op build.
- Per-phase logs and per-run firmware binaries.

Build trees remain in `build-benchmark/DEVICE-UTC_TIMESTAMP/PROFILE-jJOBS/` for
inspection or manual flashing. Failure stops the run and retains the logs and
result row; a failed build never counts as a successful timing sample.

Copy the `results.json` from each machine to the laptop, then run:

```powershell
python Development/system/testing/ci/benchmark_build.py compare path/to/laptop/results.json path/to/homelab/results.json path/to/desktop/results.json
```

The table reports median/min/max and sample count, excluding warm-ups and failed
builds. Different source hashes, compiler/tool pins, board or cache policies
produce separate input groups. Python version differences are reported as a
warning and remain in the raw reports. Source hashes normalize CRLF to LF so
Windows checkouts match Linux. Firmware binary hashes may differ because of
absolute build paths; compare the source inputs when establishing equal workloads.

`.ci-workspace`, `build-benchmark` and `artifacts` are ignored by Git. Keep the
result files when collecting thesis measurements. CI still runs its normal
quality checks and success-only homelab publication via `run_ci.py build`.
