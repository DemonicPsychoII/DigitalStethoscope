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

Exit code `0` means the gate passed. Exit code `1` means one or more mandatory
controls are on hold. Static checks are heuristics; the hardware test protocol,
clean build, on-target timing, and electrical/audio measurements remain separate
release evidence.
