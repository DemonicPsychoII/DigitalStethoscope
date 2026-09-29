# Quality-control evaluator

This directory compares the DigitalStethoscope Zephyr bring-up application with
engineering controls demonstrated by the THA Embedded Systems 2 course material.
The comparison is deliberately platform-neutral: STM32-specific implementation
details are not demanded from the ESP32-S3 target.

Run from the repository root:

```powershell
python tools/qc/qc_eval.py
```

Outputs:

- `artifacts/qc/QC-EVALUATION.md`: ignored live scorecard and actions
- `artifacts/qc/qc-eval-results.json`: ignored live CI/audit result

Defaults are repository-relative regardless of the current directory. `--repo`,
`--tha` and `--output-dir` remain available as explicit overrides. The
[2026-09-24 reports](../../verification-validation/reports/qc/2026-09-24) are
byte-preserved historical snapshots, not outputs to regenerate or current CI input.

Institutional source files are not copied into CI. The evaluator validates the
committed [traceability manifest](../../verification-validation/fixtures/qc/tha-baseline-traceability.json)
revision and SHA-256 records. When a
local THA checkout is present, its three referenced files must match those
hashes; CI uses the immutable metadata without exposing the source material.

The standalone evaluator exits `0` only at 100/100 with every control at
`PASS`; otherwise it exits `1`. CI enforces that outcome as part of the required
quality check. The repeatability control requires a detailed
manual protocol, recorded verdicts, and successful pristine ESP32-S3 build
evidence. These source heuristics and compilation evidence cannot replace
on-target timing or electrical/audio evidence.

The integrated stethoscope upgrade also has behavioral DSP/FHIR tests in
[host tests](../../software/evaluation/firmware/tests/host) and a physical acceptance matrix in
[EVAL-GUIDE.md](../../software/evaluation/firmware/EVAL-GUIDE.md). CI runs those host tests and builds the
offline, QC, and combined network/QC/optional-switch profiles. The engineering
score above is separate from functional evaluation; it does not imply a complete
stethoscope has passed the hardware matrix. Upgrade build/source hashes and
host-test results are recorded in the historical
[integrated build evidence](../../software/evaluation/firmware/evidence/integrated-build-results.json).
