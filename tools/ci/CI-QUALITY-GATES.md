# Mandatory CI quality gates

GitHub Actions is used because `origin` is GitHub and the repository had no
other CI configuration. Pull requests into `integration` report two stable checks:

- `Zephyr / Firmware Build`
- `Quality / Static Checks`

The workflow pins Zephyr commit `357467a011cd2557a1a3f0b4be83d817c4addc9b`,
Zephyr SDK `1.0.1`, west `1.5.0`, the runner image, Python, and third-party
actions. Static checks and QC run on every PR, including documentation-only
changes, so changes to `.clang-format` and the QC traceability manifest are
always validated. The firmware job runs only when the workflow, evaluation firmware,
CI or toolchain scripts change; otherwise GitHub reports it as skipped, which satisfies
its required-check rule. Change detection compares the current base and head
trees, includes deletions and both sides of renames, and fails on Git errors.
There are no push, main-branch, or manual duplicate runs. Only Python package
caching remains; firmware builds are pristine with a 30-minute timeout.
Repository contents are read-only and no secrets
are used, so fork pull requests receive no privileged credentials.

## Local parity

Use an already installed pinned environment; see
[CONTRIBUTING](../../CONTRIBUTING.md) for workspace selection and prerequisites.
Run from the repository root with its selected interpreter:

```powershell
python tools/ci/run_ci.py all
```

`all` runs static, build and QC only. Host pytest, infrastructure regressions and
Linux native execution are separate gates documented in CONTRIBUTING. Change
detection retains legacy firmware/CI/toolchain prefixes during migration so
old-only deletions still trigger. New prefixes are `software/evaluation/firmware/`,
`tools/ci/` and `tools/toolchain/`.

The Python entry point preserves paths containing spaces and parentheses and
returns non-zero on the first failed gate. Zephyr
4.4's Windows Kconfig generator itself cannot configure a firmware build from a
path containing parentheses; for the firmware stage, use a checkout path without
parentheses (a drive mapping alone is insufficient because Python canonicalizes
the path). Linux CI is unaffected and provisions the same pinned revision with
[setup_zephyr.sh](../toolchain/setup_zephyr.sh); Windows developers use the
[PowerShell provisioner](../toolchain/setup-toolchain.ps1) only with separate
provisioning approval. Activation uses [zephyr-env.ps1](../toolchain/zephyr-env.ps1).
CI treats all compiler warnings under Zephyr's default policy as
diagnostics; warnings promoted by Zephyr/Kconfig itself fail. A blanket `-Werror`
is intentionally not enabled because warnings in pinned upstream modules would
make the gate unreliable. Application-owned warnings should be fixed before
merge and may be promoted selectively as the code is modularized.

## Artifacts and reporting

No artifacts are uploaded. Build output and RAM/ROM reports appear in the job
log; firmware evidence files remain available when running locally. The static
job generates a QC scorecard and records its score in the run summary; a `HOLD`
result fails the quality check. Live reports are ignored under `artifacts/qc/`;
[dated reports](../../verification-validation/reports/qc/2026-09-24) are historical
and are neither overwritten nor consumed as current results.
No serial captures, credentials, private
hardware evidence, or developer paths are collected.

## Branch protection (administrative step)

The existing `integration` protection requires both check names above and an
up-to-date branch. Keep those names stable. Do not use workflow-level path
filters: a filtered-out workflow cannot report a required check for docs-only
PRs. If CI is later required for another protected branch, add that branch to
the workflow trigger before requiring these checks there.

Equivalent GitHub CLI/API setup requires repository-administration authority;
it is deliberately not performed by the local validation script.

## Hardware boundary

An ESP32-S3 build proves compilation/linking and resource fit; it does not prove that a microphone,
DAC, display, touch controller, GPIO, ADC, PWM, or board wiring works. Physical
validation remains a separate manual release gate using the
[integrated evaluation guide](../../software/evaluation/firmware/EVAL-GUIDE.md).
[TEST-PROTOCOL.md](../../software/evaluation/firmware/TEST-PROTOCOL.md) retains historical verdicts.
Before release, retain the firmware commit, board revision/serial, operator,
date, filled PASS/FAIL/BLOCKED verdicts, electrical checks, audio observations,
and instrument evidence. Hardware-in-the-loop may become a separate protected
scheduled/manual gate only after a controlled runner and real board are available.

## Integrated evaluation coverage (2026-09-24)

The static job additionally installs the fully pinned
[host dependencies](../../software/evaluation/firmware/tools/requirements.txt) with `--require-hashes` and runs
`software/evaluation/firmware/tests/host` against the portable DSP/FHIR implementation, evaluation CLI and a
local HTTPS readback fixture. The firmware job also performs pristine QC and
combined network/QC/second-switch builds, then builds and runs `tests/logic` on
`native_sim/native/64`, including bounded audio-start recovery regressions.
These builds do not connect to Wi-Fi or send FHIR data. CA/server credentials
are absent from CI and the latest local build evidence. Physical acceptance
remains in the app evaluation guide. The static job also runs
`tools/ci/tests/test_repository_layout.py`; unavailable Windows or optional local
snapshot/parser checks are explicitly skipped, not reported as passed.
