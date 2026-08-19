# Mandatory CI quality gates

GitHub Actions is used because `origin` is GitHub and the repository had no
other CI configuration. Pull requests and pushes to `main` and `integration`
run two stable checks:

- `Zephyr / Firmware Build`
- `Quality / Static Checks`

The workflow pins Zephyr commit `357467a011cd2557a1a3f0b4be83d817c4addc9b`,
Zephyr SDK `1.0.1`, west `1.5.0`, the runner image, Python, and third-party
actions. Caches are performance-only: every firmware build is pristine.
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

Firmware evidence (14 days): build log, `.config`, generated devicetree header,
ELF, BIN, map, RAM report, and ROM report. The static job also generates
a required QC scorecard (30 days); a `HOLD` result fails the quality check.
No serial captures, credentials, private
hardware evidence, or developer paths are collected.

## Branch protection (administrative step)

The remote currently exposes only `integration` (the default branch); despite a
stale local remote-tracking reference, the GitHub API reports no `main` branch.
In GitHub **Settings → Branches → Add branch protection rule**, create a rule for
`integration`, and create the same rule for `main` if/when that branch is created.
Enable “Require a pull request before merging”,
“Require status checks to pass”, “Require branches to be up to date”, select both
checks above, enable “Do not allow bypassing”, and apply the rule to
administrators if that matches project governance. Do not enable auto-merge.
The checks must complete at least once before GitHub offers them in the picker.

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
