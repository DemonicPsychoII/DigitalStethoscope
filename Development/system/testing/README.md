# Quality control and evaluation

The platform-neutral QC evaluator compares Zephyr bring-up engineering controls
with THA Embedded Systems 2 material. Run from the repository root:

```powershell
py Development/system/testing/qc_eval.py
```

It produces [QC-EVALUATION.md](QC-EVALUATION.md) and
[qc-eval-results.json](qc-eval-results.json), exiting `0` only at 100/100 with
every control `PASS`; otherwise `1`. CI enforces this result.

The [baseline manifest](tha-baseline-traceability.json) pins the institutional
revision and three SHA-256 records without copying source into CI. A local THA
checkout must match those hashes. Repeatability requires the manual protocol,
recorded verdicts and successful pristine ESP32-S3 build evidence.

- [Firmware setup and build benchmarks](BUILD-TIMES.md)
- [CI gates and local parity](CI-QUALITY-GATES.md)
- [Behavioral DSP/FHIR tests](../coding/bringup-zephyr/tests/host)
- [Physical acceptance protocol](../coding/bringup-zephyr/EVAL-GUIDE.md)
- [Integrated software evidence](../coding/bringup-zephyr/evidence/integrated-build-results.json)
- [Planned thesis verification](specification-verification.md)

QC scores and compilation are separate from functional acceptance: neither
establishes on-target timing, electrical/audio behavior or clinical validity.

Updated by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
