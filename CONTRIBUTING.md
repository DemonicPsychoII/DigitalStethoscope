# Contributing

Read the [scope map](README.md#scope-map) and [CI contract](tools/ci/CI-QUALITY-GATES.md).
Use a pre-existing Python 3.12+ environment with the unchanged
[CI lock](tools/ci/requirements-ci.txt) and
[host lock](software/evaluation/firmware/tools/requirements.txt) satisfied.
Host tests require GCC and OpenSSL; static C checks require clang-format in CI.
Provisioning or installing missing dependencies requires separate authorization.

## Existing Windows Environment

From the repository root, activate an already installed workspace:

```powershell
& ./tools/toolchain/zephyr-env.ps1
```

Both [activation](tools/toolchain/zephyr-env.ps1) and
[setup](tools/toolchain/setup-toolchain.ps1) choose `-WorkspacePath`, then
`STETHO_ZEPHYR_WORKSPACE`, then the existing
`Development/system/coding/tools/zephyrproject` fallback. Explicit or environment
paths must name an existing directory; relative paths are repository-relative.
Invalid settings fail without fallback. Activation validates inputs before
changing PATH, ZEPHYR_BASE or ZEPHYR_SDK_INSTALL_DIR. It never provisions.

Setup is a separate, networked provisioning operation, not an activation command.
Do not move installed virtual environments, SDKs or caches. A future external
workspace needs an explicit path and authorization to recreate it from pins.

## Separate Gates

From the repository root, `python` means the selected environment's interpreter:

```powershell
python -m pytest -q tools/ci/tests/test_repository_layout.py
python tools/ci/run_ci.py static
python tools/ci/run_ci.py qc
python -m pytest -q software/evaluation/firmware/tests/host
python tools/ci/run_ci.py build
```

Run each gate separately and stop on failure. `run_ci.py all` runs only static,
build and QC, in that order. It does not include either pytest or native execution.
The static runner scans the Git index; before staging, explicitly syntax-check new
destination files and compare the migration ledger rather than treating it as full
untracked-file coverage. Do not stage merely to run checks or relax the 5 MiB rule.

Infrastructure tests report unavailable Windows PowerShell coverage as skipped.
Navigation parsing uses `markdown-it-py` when already available in the Zephyr test
environment; absent parser coverage is skipped, not passed. The migration parity
test uses the local preserved W1 snapshot and skips when that snapshot is absent.
Neither case changes the pinned dependency locks.

Host HTTPS tests use loopback fixtures, not a real FHIR endpoint. No flash, serial,
device network or research-runner commands are part of these gates.

## Native Logic on Linux

In an existing pinned CI-style Linux workspace:

```sh
export ZEPHYR_BASE="$PWD/.ci-workspace/zephyr"
export PATH="$PWD/.ci-workspace/.venv/bin:$PATH"
west build --pristine=always -b native_sim/native/64 software/evaluation/firmware/tests/logic -d build-logic
build-logic/zephyr/zephyr.exe
```

Require actual suite execution, not compilation alone. Windows host tests are
not a replacement for this Linux gate. [Linux setup](tools/toolchain/setup_zephyr.sh)
retains the disposable `.ci-workspace` contract; do not run it without provisioning
approval. Firmware builds use the pinned ESP32-S3 target and three profiles from
the CI runner, with ignored output and no upload.

## Evidence and Prose

Current QC output is ignored under `artifacts/qc/`; the dated reports are historical.
Use [verification guidance](verification-validation/README.md) for physical/study
records. Host/build success is not hardware or clinical acceptance. Prose-only
work needs reference/traceability checks, not unrelated firmware builds.

The root [AGENTS.md](AGENTS.md) is the only canonical agent policy. VS Code's
Copilot/Local support is documented under
[custom instructions](https://code.visualstudio.com/docs/copilot/customization/custom-instructions).
For the Local agent, `chat.useAgentsMdFile` controls loading; confirm discovery in
Agent Customizations and References. No shared settings or duplicate policy is supplied.