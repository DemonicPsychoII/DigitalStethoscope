# Quality-control evaluator

This directory compares the DigitalStethoscope Zephyr bring-up application with
engineering controls demonstrated by the THA Embedded Systems 2 course material.
The comparison is deliberately platform-neutral: STM32-specific implementation
details are not demanded from the ESP32-S3 target.

Run from the repository root:

```powershell
py Development/system/testing/qc_eval.py
```

Outputs:

- `QC-EVALUATION.md`: reviewable scorecard and actions
- `qc-eval-results.json`: machine-readable CI/audit result

Institutional source files are not copied into CI. The evaluator validates the
committed `tha-baseline-traceability.json` revision and SHA-256 records. When a
local THA checkout is present, its three referenced files must match those
hashes; CI uses the immutable metadata without exposing the source material.

The standalone evaluator exits `0` only at 100/100 with every control at
`PASS`; otherwise it exits `1`. CI enforces that outcome as part of the required
quality check. The repeatability control requires a detailed
manual protocol, recorded verdicts, and successful pristine ESP32-S3 build
evidence. These source heuristics and compilation evidence cannot replace
on-target timing or electrical/audio evidence.
