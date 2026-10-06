# CI selection and prepared environments

Required contexts remain `Quality / Static Checks`, `Zephyr / Firmware Build` and
`agent-gate`. A short hosted job selects suites before requesting a disposable VM;
selection errors fail the required static check. Static repository analysis and QC
always run. Host DSP/FHIR, build-tooling and merge-gate tests run when their inputs
change. Documentation/agent-gate-only edits skip firmware; unknown firmware/toolchain
inputs and workflow changes select it. The existing daily unchanged-build guard now
runs before VM allocation. A firmware label or integration publication still forces builds.

Static jobs can reuse `/opt/stethoscope-ci` when Python 3.12.10, installed package state
and both hash-locked requirement files match their preparation manifest. Otherwise
setup-python and pinned dependency installation run normally.

Firmware jobs validate `/opt/zephyr-workspace` against checkout pins, actual Zephyr/module
revisions, package versions, compiler and Espressif blob hashes. A complete matching image
skips setup; missing or changed state falls back to canonical setup. Every firmware profile
and native simulation test still builds pristine. Compiler caching is not enabled here.

The host setup and rollback procedure is in HomelabServer's
`scripts/ci-runner/STETHOSCOPE.md`. Images are read-only bases for disposable guests;
this optimization does not create persistent writable runners or authorize public forks.
No timing improvement should be claimed before real prepared-image runs are measured.

CodeRabbit native approval is accepted for the current head from the configured immutable
bot identity. Its progress check alone is insufficient. Once it issues a decisive verdict, a blocking,
stale or dismissed review cannot be replaced with an agent marker. Independent agent review
remains available before CodeRabbit issues a decisive verdict, including comment-only defaults. Human-only approval is removed; material
findings and unresolved conversations still block. Optional suggestions may be acknowledged
or declined and resolved without another code/review cycle.

Updated by GPT-6.1-Sol on behalf of Nico running in codex.
