# CI quality gates

The [quality workflow](../../../.github/workflows/quality-gates.yml) runs
for PRs into `integration`, pushes to `integration`, the daily 03:17 UTC
schedule and manual dispatches. Required contexts remain:

- `Quality / Static Checks`
- `Zephyr / Firmware Build`
- `agent-gate` (the separate merge/review policy gate)

Keep these names stable. Merge and review requirements are defined in
[AGENTS.md](../../../AGENTS.md), not by a QC score or this guide.

Keep the active branch-protection rules; native review migration remains staged. Avoid workflow-level path
filters: filtered workflows cannot report required contexts for docs-only PRs.
Add any new protected branch to the workflow trigger before requiring its checks.

## Selection and runners

See [detailed CI operations](ci/OPERATIONS.md) for the selection table, workflow
flow, schedules, artifact promotion and review migration. Native-test-only edits
run native tests without ESP32 profiles. Static/QC remain required; selected heavy
verification stays in a disposable homelab VM, with hosted final accounting.
The stable required check names above remain enforced. No hosted build fallback
or workflow-level path filter is introduced.

[toolchain.json](ci/toolchain.json) pins tools and source revisions.
[Prepared environments](ci/OPERATIONS.md#prepared-environments) can skip matching
setup; selected firmware profiles and native simulation still build pristine.
Fork builds receive no privileged credentials.

## Setup and local checks

Static checks also require actionlint 1.7.12 and ShellCheck 0.11.0 on PATH.
`ci/validation_tools.py` installs pinned Linux x86-64 binaries; use matching
native binaries on Windows or run static checks on Linux.

Install Python 3.12+ and Git. On Windows, also install 7-Zip:

```powershell
winget install --id 7zip.7zip -e --silent
python Development/system/testing/ci/setup_zephyr.py
.ci-workspace/.venv/Scripts/python.exe -m pip install --require-hashes -r Development/system/testing/ci/requirements-ci.txt
.ci-workspace/.venv/Scripts/python.exe Development/system/testing/ci/run_ci.py static
.ci-workspace/.venv/Scripts/python.exe Development/system/testing/ci/run_ci.py qc
```

For firmware compilation, run `run_ci.py build` with that same Python.
`run_ci.py all` runs static, build and QC; it does not run the independent
host, tooling, merge-gate or native simulation suites. A local build publishes
only after all firmware profiles succeed, if `cloud-publish` is installed.
Use [benchmark_build.py](BUILD-TIMES.md) for timing without publication or flashing.

`Development/system/coding/tools/setup-toolchain.ps1` delegates to the same
provisioner. Linux uses `python3` and `.ci-workspace/.venv/bin/python`; it also
requires venv support, xz/tar and
[Zephyr host prerequisites](https://docs.zephyrproject.org/latest/develop/getting_started/index.html).
CI's `setup_zephyr.sh` delegates to the shared Python provisioner. Rerunning
setup completes interrupted installations and retains sources/downloads.
Legacy toolchain locations remain independent.

`ci/toolchain.json` supplies the common tool, board and module pins. The
workflow pins Python and actions; requirements are installed with hashes.
Host tests additionally require a host C compiler and the pinned dependencies
in `bringup-zephyr/tools/requirements.txt`. CI uses GCC. Run separate suites:

```powershell
python -m unittest discover -s Development/system/testing/ci -p 'test_*.py'
python -m pytest -q Development/system/coding/bringup-zephyr/tests/host
python -m unittest discover -s .github/agent-gate
```

Commands fail on the first failed stage. Zephyr 4.4's Windows Kconfig generator
cannot configure firmware in paths containing parentheses; use a checkout
path without them. Compiler diagnostics follow Zephyr policy; no blanket
`-Werror` is added for upstream modules.

## Prepared environments

`ci/prepared_env.py` validates `/opt/stethoscope-ci` against Python 3.12.10,
installed package state and both hash-locked requirement files. Missing or
changed state falls back to pinned installation.

For `/opt/zephyr-workspace`, it verifies checkout tool pins, actual Zephyr and
module revisions, package versions, compiler and Espressif blob hashes.
Matching images skip setup; incomplete images use canonical provisioning.
Images are read-only bases for disposable guests, not persistent writable
runners. Every firmware profile and native test still builds pristine;
compiler caching is disabled. Host image preparation/rollback is documented
in HomelabServer's `scripts/ci-runner/STETHOSCOPE.md`. Timing improvements
require measured prepared-image runs.

## Reports, publication and hardware boundary

See [evidence and publication](ci/OPERATIONS.md#evidence-and-publication) for
14-day diagnostic retention and exact-commit daily artifact promotion.

QC writes its Markdown scorecard and JSON to ignored `artifacts/qc/` and
records the score in the run summary. HOLD fails the quality check. These
source heuristics are separate from functional evaluation and physical proof;
see the [testing index](README.md#source-level-qc).

Publishing builds upload `firmware-build-<attempt>` for three days, containing
each profile binary and a manifest with commit/merged-tree identity, UTC time,
board, profile, boot-banner version and SHA-256. The homelab firmware sync
validates the GitHub run before publishing to Personal Cloud; the build guest
holds no cloud credential. Publication occurs only after all selected firmware
and native tests succeed. Fork builds do not publish firmware release artifacts. Build and RAM/ROM logs
remain in CI; local firmware evidence is under ignored `artifacts/`.

ESP32-S3 builds prove compilation/linking and resource fit. Host DSP/FHIR and
native tests do not connect a physical device to Wi-Fi or a patient server.
Hardware acceptance remains in
[the integrated EVAL-GUIDE.md](../coding/bringup-zephyr/EVAL-GUIDE.md) and the
[planned verification procedures](specification-verification.md).
[TEST-PROTOCOL.md](../coding/bringup-zephyr/TEST-PROTOCOL.md) records historical
component observations; these do not establish acceptance of current firmware.
Retain firmware identity, board/wiring revision, operator/date, actual
PASS/FAIL/BLOCKED outcomes and instrument evidence. Flashing, serial and
device-network operations require owner authorization.

Updated by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
