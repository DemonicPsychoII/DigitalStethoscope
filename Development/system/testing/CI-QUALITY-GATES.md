# Mandatory CI quality gates

GitHub Actions is used because `origin` is GitHub and the repository had no
other CI configuration. Pull requests into `integration` report two stable checks:

- `Zephyr / Firmware Build`
- `Quality / Static Checks`

The workflow pins Zephyr commit `357467a011cd2557a1a3f0b4be83d817c4addc9b`,
Zephyr SDK `1.0.1`, west `1.5.0`, the runner image, Python, and third-party
actions. Static checks and QC run on every PR, including documentation-only
changes, so changes to `.clang-format` and the QC traceability manifest are
always validated. The firmware job runs only when the workflow, bring-up tree,
or CI scripts change; otherwise GitHub reports it as skipped, which satisfies
its required-check rule. Change detection compares the current base and head
trees, includes deletions and both sides of renames, and fails on Git errors.
Regardless of paths, the firmware job also runs for same-repository PRs labelled
`firmware` (when the label is added and on every later push), the daily
03:17 UTC `schedule` run on `integration`, and manual *Run workflow* dispatches
on any branch; these publish their images (see below). Other label events skip
both jobs under distinct check names, so they neither cancel a real run nor
replace a required check's result. There are no push runs. Only Python package
caching remains; firmware builds are pristine with a 30-minute timeout.
Repository contents are read-only and no secrets
are used, so fork pull requests receive no privileged credentials.

## Local parity

Activate the pinned Zephyr virtual environment created by
`Development/system/coding/tools/setup-toolchain.ps1`, set `ZEPHYR_BASE`, then
run from the repository root:

```powershell
py "Development/system/testing/ci/run_ci.py" all
```

The Python entry point preserves paths containing spaces and parentheses and
returns non-zero on the first failed gate. Zephyr
4.4's Windows Kconfig generator itself cannot configure a firmware build from a
path containing parentheses; for the firmware stage, use a checkout path without
parentheses (a drive mapping alone is insufficient because Python canonicalizes
the path). Linux CI is unaffected and provisions the same pinned revision with
`setup_zephyr.sh`; Windows developers use the existing PowerShell provisioner.
CI treats all compiler warnings under Zephyr's default policy as
diagnostics; warnings promoted by Zephyr/Kconfig itself fail. A blanket `-Werror`
is intentionally not enabled because warnings in pinned upstream modules would
make the gate unreliable. Application-owned warnings should be fixed before
merge and may be promoted selectively as the code is modularized.

## Artifacts and reporting

Publishing builds (above) upload one artifact, `firmware-build-<attempt>`, kept
for three days: each profile's `zephyr.bin` under a descriptive name plus a
`manifest.json` (channel, commit, merged tree for PRs, UTC build time, board,
per-file profile, boot-banner version and SHA-256). The homelab's firmware sync
downloads it, checks it against GitHub's run record, and publishes it to
Personal Cloud: the build guest never holds a cloud credential. Each PR and
`integration` keep only their newest build; a PR's builds are deleted when it
is closed or merged, and an unchanged `integration` HEAD is not republished.
Fork builds never upload. Otherwise build output and RAM/ROM reports appear in
the job log; firmware evidence files remain available when running locally. The static
job generates a QC scorecard and records its score in the run summary; a `HOLD`
result fails the quality check.
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
validation remains a separate manual release gate using `TEST-PROTOCOL.md`.
Before release, retain the firmware commit, board revision/serial, operator,
date, filled PASS/FAIL/BLOCKED verdicts, electrical checks, audio observations,
and instrument evidence. Hardware-in-the-loop may become a separate protected
scheduled/manual gate only after a controlled runner and real board are available.

## Integrated evaluation coverage (2026-09-24)

The static job additionally installs the fully pinned
`bringup-zephyr/tools/requirements.txt` with `--require-hashes` and runs
`tests/host` against the portable DSP/FHIR implementation, evaluation CLI and a
local HTTPS readback fixture. The firmware job also performs pristine QC and
combined network/QC/second-switch builds, then builds and runs `tests/logic` on
`native_sim/native/64`, including bounded audio-start recovery regressions.
These builds do not connect to Wi-Fi or send FHIR data. CA/server credentials
are absent from CI and the latest local build evidence. Physical acceptance
remains in `bringup-zephyr/EVAL-GUIDE.md`.
