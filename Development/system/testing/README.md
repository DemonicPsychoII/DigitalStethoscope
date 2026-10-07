# Testing and verification

This directory contains planned product verification, CI tooling and retained
documentation evidence. Behavioral DSP/FHIR tests live beside the firmware in
[`../coding/bringup-zephyr/tests/host`](../coding/bringup-zephyr/tests/host);
native simulation tests are in
[`../coding/bringup-zephyr/tests/logic`](../coding/bringup-zephyr/tests/logic).

- [Planned verification and acceptance](specification-verification.md): VT-01–VT-13,
  requirement traceability and the evidence record template. These procedures
  do not claim executed product acceptance.
- [CI quality gates](CI-QUALITY-GATES.md): setup, suite selection, prepared
  environments, required checks and publication boundaries.
- [Build-time measurements](BUILD-TIMES.md): reproducible timing and comparison.
- [CI tooling index](ci/README.md): scripts, pinned inputs and regression tests.
- [Documentation evidence](evidence/2026-10-06-draft-validation.md): historical
  validation of the architecture/requirements review package.
- [Physical evaluation guide](../coding/bringup-zephyr/EVAL-GUIDE.md) and
  [hardware protocol](../coding/bringup-zephyr/TEST-PROTOCOL.md): target acceptance
  and recorded hardware observations.

## Source-level QC

`qc_eval.py` compares engineering controls with the THA Embedded Systems 2
baseline. Run from the repository root:

```powershell
python Development/system/testing/qc_eval.py
```

The generated `QC-EVALUATION.md` and `qc-eval-results.json` are written to the
ignored `artifacts/qc/` directory. Use `--output-dir PATH` to retain a separate
dated evidence copy. Reports are reproducible output, not maintained source;
older committed reports remain available in Git history.

The evaluator checks source patterns across production `src/*.c` modules,
configuration options and historical evidence records. PASS requires every
source-level control and 100/100; otherwise it returns HOLD and exits nonzero.
It does not establish synchronization correctness, bounded target timing,
complete API error recovery or current hardware acceptance. Historical build
and protocol records are identified as such, not rerun by QC.

The committed `tha-baseline-traceability.json` pins the institutional revision
and three source hashes. A local THA checkout must match those hashes when
present; CI validates the metadata without copying institutional source files.

Updated by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
