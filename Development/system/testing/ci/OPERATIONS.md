# Verification operations

This is the execution guide for the [application development process](../../process/README.md). It defines the target test coverage, suite selection and evidence. The process document owns test generation, PR order, manual-test format and GitLab review.

Component test PRs add the suites. Concrete application checks are listed in verification cases.

## Current state and target

When present, the communication host suite runs production L2 (layer 2) with controlled L1 (layer 1) services and simulated time. Its expectations come from the identified design revision; at this head one known implementation defect is recorded as a strict expected failure in the host suite ([GitHub #131](https://github.com/DemonicPsychoII/DigitalStethoscope/issues/131)); it is not target evidence. Unit tests, real-service integration, device verification and acceptance remain pending; the case catalogue records the gaps.

When the application entry point is present, its later implementation stages provide the Wi-Fi service, portal and COMMUNICATION workflow; other components contain placeholders. CI then builds, publishes and reuses only the `application` profile; without that entry point the application suite is disabled. The bring-up firmware and its source-pattern QC are archived under `preThesis/06-bringup-zephyr` and have no CI. The pinned application toolchain and compiler cache remain active. External cloud importer compatibility and device results remain unverified.

Component routing for WIFI, PORTAL, STORAGE and COMMUNICATION selects the communication suite when its test folder exists; source folders match with or without their `L1_`/`L2_` prefix. Changes to the server profile tool or the host test requirements select it too. Shared system pages and requirements also select it. Other suites are added with their test PRs. Application delivery follows receipt-based case VT-07.

## Test levels

| Level | Test basis | What runs |
| --- | --- | --- |
| Unit tests (target for the application) | Detailed design and interfaces | Individual functions, libraries and service logic, including boundaries and specified failures. Host tests cover portable code; hardware-dependent units require device runs. |
| L2 deterministic simulation | Detailed design and interface contracts | Production L2 workflows with controlled L1 responses, simulated time and injected events. The cases check states, ordering, retries, cancellation and recovery. |
| Host integration and target integration | Architecture and interface contracts | Connected production components: L2 with implemented L1 services, interacting services, and wrappers with Zephyr drivers. Reports identify any remaining substitutes. |
| System verification (target) | Whole-system requirements | Complete operator flows and failure behavior. Automatable cases run in CI; physical behavior is checked on the device. |
| Final system acceptance (target) | User needs and product scope | Manual runs on the complete device, with evidence and human sign-off. |

CI means continuous integration. L2 simulation checks application behavior with substituted services. Integration tests use real L1 services. A simulated deadline checks time logic, while a device measurement checks physical timing.

## CI selection and results

```mermaid
flowchart LR
    Change[Changed files] --> Select[Affected suites]
    Select --> Host[Host tests]
    Host --> Build[Builds and integration]
    Build --> Evidence[Results and logs]
```

| Change | Implemented selection |
| --- | --- |
| Requirements, architecture or design | Document validation and available application host scenarios. |
| Application source or configuration | Application build and available application host scenarios. |
| Application host tests | Host scenarios and document validation, without a target build. |
| Build toolchain or quality workflow | Application build and affected tooling/host regressions. |
| Tooling-only edits | Tooling regressions; build input edits also select the application build. |
| Merge-gate source | Merge-gate regression tests. |
| Daily publication, integration dispatch or `firmware` label | Application build and available host scenarios, or daily reuse of an exact verified application artifact. |
| Integration push | Application build and available host scenarios; retain the verified application artifact. |
| Weekly or full dispatch | Every available suite and a pristine application build. |
| Archived bring-up firmware | No build, host tests, native tests, QC evaluation or publication. |

The [selector](firmware_changes.py) supplies every suite output. Static checks run on every active batch. An unchanged daily publication can skip the batch.

The host batch runs production unit/service tests, deterministic L2 scenarios and
real-service integration together. The integration executable links production
COMMUNICATION, WIFI, PORTAL and STORAGE; only Zephyr kernel/driver/network, HTTP
server and settings APIs are substituted. The substitute follows the pinned ESP
driver's scan completion and connected-versus-connecting disconnect behavior.
It cannot prove target scheduling, socket transport, flash power-failure behavior
or radio/audio interference. JUnit reports the level per scenario.

Coverage runs separately from ASan/UBSan so sanitizer-generated checks do not
inflate the branch denominator. Both executions must pass. GCC instruments production C with `--coverage -O0` when
`STETHO_COVERAGE_DIRECTORY` is set. `host_coverage.py` invokes the matching `gcov`
with JSON line/branch output and reports unit, L2 and integration totals separately
in `GITHUB_STEP_SUMMARY`. Raw counters, gcov JSON, per-source line/branch counts and
`coverage.md` remain in `artifacts/ci/host-coverage/` inside the static evidence
artifact. Missing selected levels or production counters fail collection. XFAIL
execution can cover a branch without verifying its behavior. There is no numeric
threshold: this baseline exposes gaps for review instead of choosing an arbitrary
percentage. Host compilers and commands remain in JUnit; firmware build selection
and the required firmware check remain in place.

`manual_test_records.py` validates completed JSON runs and reports the count in the
job summary. An empty run directory explicitly means execution and Nico's sign-off
are pending. The manual record format, reusable procedures and executed records
are test-stage artifacts; the validator and workflow belong to Process/CI.

Application host scenarios run within `Quality / Static Checks` only when `available_component_suites()` finds the suite in the checkout. The communication suite, when present, writes `artifacts/ci/application-host.xml`. The following reporter lists each scenario, VT ID (verification-test identifier) and result in the job summary. Missing, empty, unmapped, skipped or unsuccessful selected results fail the required check. Documented pytest expected failures are shown as XFAIL and remain known defects; they are accepted by result accounting. Strict unexpected passes fail pytest and result accounting. Result accounting also rejects missing selector outputs.

The required check names remain `Quality / Static Checks`, `Zephyr / Firmware Build` and `agent-gate`. Selected work must produce a result; missing outputs, failures and cancellations do not silently pass. Workflow-level path filters are avoided because even documentation-only PRs need required results. Protected branches need matching workflow triggers.

Static checks cover formatting, configuration parsing, workflow and shell validation, and local Markdown links and anchors. PlantUML envelope checks confirm start/end markers; rendered diagrams are checked separately. Supported application host tests also use ASan (AddressSanitizer) and UBSan (UndefinedBehaviorSanitizer) to detect memory errors and undefined behavior.

The portal page check executes JavaScript using Node 24.19.0 from
`.ci-validation-tools/node`. The existing `validation_tools.py` workflow step
installs the hash-pinned Linux x86-64 runtime alongside actionlint and ShellCheck;
an older prepared image downloads it using the checked-out pin. A missing or
unusable runtime fails CI. Windows local execution and its explicit skip/override
are described in the host run instructions.

## Execution environment

Static checks and builds run in disposable home-lab VMs (virtual machines). GitHub-hosted runners handle routing, result accounting and artifact promotion. Heavy work has no hosted fallback. Fork builds receive no privileged credentials. Hardware flashing, serial access and device-network operations require owner authorization.

The [quality workflow](../../../../.github/workflows/quality-gates.yml) runs for PRs into `integration`, integration pushes, scheduled verification and manual dispatch. Tool and board versions are defined by [toolchain.json](../../coding/tools/toolchain/toolchain.json), the workflow and the hash-locked dependency files. The pins and the workspace setup live with the production tools in [coding/tools/toolchain](../../coding/tools/toolchain/), so firmware builds without this folder; CI imports them through `toolchain_path.py`.

### Prepared environments

Static jobs validate `/opt/stethoscope-ci` against the required Python version, package state and dependency hashes. Firmware jobs validate `/opt/zephyr-workspace` against Zephyr/module revisions, compiler inputs and Espressif binary hashes. Missing or changed inputs trigger setup. `setup_zephyr.sh` removes the marker, runs the production `setup_zephyr.py` and records the marker with `prepared_env.py record zephyr` only after setup succeeds. The marker holds the pin values, not their location. Validators are checksum-checked before reuse or download.

Every build starts with a clean CMake build tree. Compiler outputs can be reused through the pinned 512 MiB ccache, separated by toolchain/cache versions. PRs read entries; successful integration verification saves them. Weekly and full verification disable compiler-cache reuse. Disposable guest writes are discarded; the base images remain read-only.

## Evidence and publication

A result identifies the production source, test source, toolchain and configuration. Each suite supplies machine-readable reports plus a readable coverage summary: behavior checked, expected outcome, actual outcome, substituted boundaries and pending device cases. A failed case retains its inputs and logs for diagnosis and retest.

Diagnostic artifacts are retained for 14 days; firmware artifacts for eight days. Review evidence is copied to its durable review record before expiry, as defined in the [GitLab review process](../../process/README.md#github-development-and-gitlab-human-review).

Application publication requires successful selected verification and the single `application` profile, built from `coding/app/prj.conf`. The manifest entry has `component=application`, the version and SHA-256 (secure hash algorithm 256) checksum. The same version is printed at boot. Configuration, ELF (Executable and Linkable Format), binary, map, generated device tree and RAM/ROM reports are retained under `artifacts/firmware/application/`.

Daily builds, dispatches of `integration` and the `firmware` label publish only this application. Labels do not start quality-gate runs, because a label-only run would become the newest run for the head and hide its required checks. Adding `firmware` re-runs the head's green verification run through the [firmware label workflow](../../../../.github/workflows/firmware-label.yml); a run still in progress reads the live label when it plans, or is re-run once it finishes green without publishing. Integration pushes retain `verified-firmware-<attempt>`. Exact-commit reuse accepts a successful same-repository integration run of this workflow, a clean matching manifest and exactly one application image with a valid checksum. Missing eligible artifacts trigger a build; corrupt selected artifacts fail publication. The bundle keeps the external artifact name `firmware-build-<attempt>`. Build guests hold no cloud credentials.

### External publication handoff

The homelab importer and Personal Cloud service are outside this repository. Their owner must check that they accept `profile=application`, `component=application` and `--profile application --parts 1`, replace the previous download only after the upload succeeds, and display the application image. Importer compatibility and an end-to-end download remain unverified here.

## Review findings

Critical and major review findings block delivery. Minor findings and nitpicks may remain open or be deferred. The merge gate exempts only explicitly classified CodeRabbit minor/nitpick findings from its configured immutable bot identity. Unknown severity, other unresolved reviewers' threads and unanswered owner questions still block. A current-head CodeRabbit changes request counts as a completed nonblocking review only when its structured summary and all associated findings account for minor/nitpick findings exclusively; missing, truncated, mixed or unrecognised evidence blocks. Native GitHub required approvals remain independent and cannot be replaced by this gate.

The independent agent review is the default. CodeRabbit reviews only high-impact PRs, next to the agent review: automatic reviews are off, so add the `coderabbit` label and request `@coderabbitai review` once. Never duplicate a running review or assume a fixed subscription quota. The gate waits for CodeRabbit only when the PR carries the `coderabbit` label or CodeRabbit has already reviewed it. CodeRabbit's approval, or its minor-only changes request, never replaces the agent verdict: the gate requires both, Dependabot PRs included.

The gate reads `agent-review` markers from PR comments and submitted review bodies. It carries an agent approval of an earlier commit forward only when no newer `changes` verdict exists, the approved commit is one of the PR's commits or a head it had before a force-push, and the PR's own diff against its current base is identical to the approved commit's, compared through the API. A carried approval did not see changes that arrived through the base. A missing, stale or requested review, and running required checks, report `pending`. A `changes` verdict on the head, a malformed newest marker, a self-review, unanswered owner questions and the scope guard report `failure`; the agent-verdict failures hold even when CodeRabbit approved or is still requested. The scope guard rejects agent PRs that change `.github/agent-gate/**` or `.github/workflows/**` without class `policy`, except a verified pure revert, such as the automatic `revert/<sha7>` PR.

## Failures and retests

The failing test, input and environment remain part of the evidence. Corrections rerun affected unit, L2 and integration suites. Interface changes also affect callers and services. Device retests identify the hardware and firmware configuration and retain the earlier failed record.

Post-merge recovery reruns failed jobs once. Only attempts 1 and 2 determine recovery: a green rerun reports recovery; the same recognized verification step failing twice proposes a revert. Setup, runner availability, upload and unclassified failures require inspection. Later manual reruns do not reopen the recovery decision. Revert PRs still pass the active protections.

## Setup and local checks

New component suites are added through their test PRs. Use the following commands for the implemented checks.

### Local CI entry point

`local_ci.py` runs the same stages as the quality gates from any checkout or worktree on Windows (Git Bash or PowerShell) and Linux. Every stage runs; the summary lists each result, duration and device, and the exit code is non-zero if any stage failed.

| Stage | Commands, as in `quality-gates.yml` | Native where |
| --- | --- | --- |
| `static` | `ci_evidence.py`, `validate_docs.py`, `manual_test_records.py`, `run_ci.py static` | every device; Windows skips actionlint and ShellCheck |
| `unit` | tooling and merge-gate `unittest` suites | every device |
| `host` | host scenarios with sanitizers and their results, then production coverage | Linux with GCC (or `CC`) |
| `build` | `run_ci.py build --application`, then the ELF path and identity | wherever the pinned toolchain is installed |

```bash
python Development/system/testing/ci/local_ci.py run static unit
python Development/system/testing/ci/local_ci.py run host build --detach
python Development/system/testing/ci/local_ci.py follow --timeout 540
```

- `--mode auto` (default) runs a stage natively when the device has its toolchain and otherwise on homelab-annex. `--mode native` and `--mode remote` force one side.
- Remote runs keep the annex awake in two ways. The stage runs under a block-mode sleep inhibitor (`sudo -n systemd-inhibit --what=sleep`, the annex job convention), held until the run's shell exits. Around it, the run keeps its own `annex-power` hold for `--keep-minutes` (default 60, at least 1) with `annex-power keep MINUTES --owner local-ci-<run-id>`, renews it at half its duration and ends it with `annex-power release --owner local-ci-<run-id>`. annex-power keeps one hold per owner and the annex stays awake while any hold lives, so a run never shortens or ends another caller's hold. `annex-power status` lists every owner's hold. They ship `HEAD` as a Git bundle plus every tracked and untracked, non-ignored file of the working tree to `~/stethoscope-local-ci/<run-id>` on the annex. The copy shows the same uncommitted changes. The stage runs there detached from the SSH session with `--mode native --provision`; the caller polls its progress log. Its `artifacts/` files are copied back over the local ones; a remote `build` first removes the local `artifacts/firmware` and `artifacts/firmware-release`, so an earlier build cannot pass for this one. Cleanup stops a still running remote run (TERM, up to 10 s, then KILL) and removes the scratch copy, also after a failure, Ctrl+C, SIGTERM or SIGHUP. A stage without a reported result counts as failed.
- `--detach` starts the run in the background, prints its run ID and `artifacts/local-ci/<run-id>/progress.log`, and returns. `follow [run-id]` streams new log output of the newest or named run and exits with the run's code; `--timeout` returns exit code 3 while the run continues, so each call stays within an agent's foreground limit. Exit code 2 means the detached process ended without a result, for example because it was killed; its log shows how far it got. `--from-start` replays the whole log.
- The `build` stage prints the firmware version from `artifacts/firmware-release/manifest.json`, then each ELF path with its SHA-256: the retained `artifacts/firmware/application/zephyr.elf` and, for native builds, `build-ci-app/zephyr/zephyr.elf`. After a remote build, the local `build-ci-app` holds an older build and is not listed. Only a passed build is described. The pinned Zephyr links with `--build-id=none`, so no GNU build ID is printed. Decode crashes with the ELF whose SHA-256 belongs to the flashed build.
- Output is UTF-8 on every console and written files use LF. Child Python processes run with `PYTHONUTF8=1`.

### Shared environments

The firmware toolchain workspace is resolved once for all checkouts and worktrees of the same pins:

1. `STETHOSCOPE_TOOLCHAIN_WORKSPACE`, when set;
2. the checkout's own `.ci-workspace`, when it exists (CI links the prepared image there);
3. a workspace recorded with the current `toolchain.json` pins: the shared per-user location, the main checkout's `.ci-workspace` or, on Linux, `/opt/zephyr-workspace`;
4. otherwise the shared location, which setup provisions: `%USERPROFILE%\.stethoscope-toolchain\<pin key>` on Windows and `~/.cache/stethoscope-toolchain/<pin key>` on Linux. The pin key is a hash of `toolchain.json`. The location is inside the user's own profile, so other local accounts cannot place tools in it. On Windows the SDK's deepest file is 179 characters below the SDK directory, so under `%LOCALAPPDATA%` it reaches the 260-character path limit. Directly in the profile it fits while the profile path has at most 26 characters (`C:\Users\` plus a 17-character name); otherwise set `STETHOSCOPE_TOOLCHAIN_WORKSPACE` to a shorter directory that only you can write.

A workspace is used natively only when west, CMake, Ninja, Zephyr and the SDK compiler exist and its record matches the current pins; otherwise `--provision` sets it up, or `--mode auto` runs the stage on the annex. `setup_zephyr.py` holds `.stethoscope-setup.lock` in the workspace for the whole setup, and `--if-needed` returns once the workspace is ready after the lock is taken, so concurrent runs wait for one setup. After a complete setup it records the pins and the SDK location in `.stethoscope-toolchain-pins.json`: `west sdk install` reuses an SDK of the pinned version that the CMake package registry already knows, even when it lies in another workspace. `run_ci.py`, the PowerShell firmware scripts and `local_ci.py` use the same resolution. To use the pinned west, CMake and Ninja interactively, dot-source `Development/Toolchain/zephyr-env.ps1` in PowerShell or source `Development/Toolchain/zephyr-env.sh` in Bash and Git Bash. Both set `ZEPHYR_BASE`, `ZEPHYR_SDK_INSTALL_DIR` and `ZEPHYR_TOOLCHAIN_VARIANT` and print the tool paths they found.

The static, unit and host stages share one virtual environment per requirement-file hash, created with the CI's Python minor version (3.12). The hashes in the requirement files cover only its wheels. When the running interpreter has another version, `local_ci.py` uses `uv python find 3.12.10`, or installs that version with uv first. Linux runs install the pinned validators and Node with `validation_tools.py` into a shared cache directory and reuse them without rewriting once their checksums verify. Creation and installation hold a lock next to each directory and re-check afterwards. These environments live in the user cache directory, not in `/tmp` or a worktree.

### Manual setup and individual checks

Setup uses Python 3.12+, Git and, on Windows, 7-Zip. Linux also needs venv support, xz/tar and the [Zephyr host prerequisites](https://docs.zephyrproject.org/latest/develop/getting_started/index.html). A checkout path without parentheses avoids the pinned Zephyr Windows Kconfig path limitation.

```powershell
winget install --id 7zip.7zip -e --silent
python Development/system/coding/tools/toolchain/setup_zephyr.py
```

The individual commands below use a Python with `requirements-ci.txt` installed. Static checks also need actionlint and ShellCheck from [validation_tools.json](validation_tools.json). `validation_tools.py` installs their pinned Linux x86-64 binaries; a local Windows run uses native tools when available and prints a skip message for missing validators. CI requires both validators on every run. Host tests need pytest, `cryptography` for the server profile tool cases and a C compiler selected through `CC` (GCC in CI). The workflow records their dependency setup.

| Check | Command from the repository root |
| --- | --- |
| Static checks | `python Development/system/testing/ci/run_ci.py static` |
| Documentation | `python -X utf8 Development/system/testing/ci/validate_docs.py` |
| Application L2 host tests | `python -m pytest -q Development/system/coding/app/tests/host` |
| Application build | `python Development/system/testing/ci/run_ci.py build --application` |
| Tooling regression tests | `python -m unittest discover -s Development/system/testing/ci -p 'test_*.py'` |
| Merge-gate regression tests | `python -m unittest discover -s .github/agent-gate` |

`run_ci.py all` executes static checks and the application build. `build` and `build --application` are equivalent: both compile the application with its release configuration to `build-ci-app`, retain build evidence, stage the single application image and identity manifest, and can publish locally when `cloud-publish` is installed. The manual `coding/tools/build-firmware.ps1` release build uses the same configuration. Available host scenarios, tooling and merge-gate tests have separate entry points. Install application host dependencies with `python -m pip install --require-hashes -r Development/system/testing/ci/requirements-host.txt` before running an available suite.

The [archived bring-up](../../../../preThesis/06-bringup-zephyr/README.md) retains its local build guide and optional QC (quality control) evaluator. Its checks depend on named bring-up modules, optional display/touch wiring, `qc.conf` and historical bring-up evidence. They do not define application quality gates.

## Tool reference

| Tool | Responsibility |
| --- | --- |
| `run_ci.py` | Check/build entry points. |
| `local_ci.py` | Local and homelab-annex execution of the CI stages. |
| `toolchain_path.py` | Makes the production `build_support.py` (paths, pins and firmware profiles) in `coding/tools/toolchain/` importable. |
| `setup_zephyr.sh` | CI workspace setup through the production `setup_zephyr.py`, which completes interrupted setup and reuses downloads; then records the prepared-environment marker. |
| `prepared_env.py`, `validation_tools.py`, `compiler_cache.py` | Validate and reuse prepared environments, validators and compiler cache. |
| `firmware_changes.py` | Select affected suites. |
| `ci_evidence.py`, `ci_results.py` | Record execution identity and account for results. |
| `daily_build.py`, `release_reuse.py`, `firmware_release.py` | Daily selection, verified-artifact reuse and publication manifests. |
| `firmware_label.py` | Re-run a green, unpublished PR head verification when the `firmware` label is added. |
| `application_host_results.py` | Per-scenario application JUnit summary and result validation. |
| `native_review.py`, `post_merge.py` | Native protection migration and post-merge failure confirmation. |
| `validate_docs.py` | Links, diagram renders, indexes, repeated facts, available thesis sources and VT references (reported separately when present). |
| `test_*.py` | Regression tests for this tooling. |

Optional infrastructure references are kept below so the application reading path ends with test execution and evidence.

<details>
<summary>Runner maintenance</summary>

Host image setup and rollback live in HomelabServer's `scripts/ci-runner/STETHOSCOPE.md`. [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions) describes hosted-runner accounting; home-lab runtime is separate.

</details>

[Native approval migration and rollback](NATIVE-REVIEW-MIGRATION.md) has a separate guide.
