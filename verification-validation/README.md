# Verification and Validation

This scope owns system-level plans, reference fixtures, physical/study evidence
and interpreted reports. Automated software tests stay with their components.

| Area | Current material and boundary |
|---|---|
| `plans/` | No standalone system plan yet. The app's [integrated evaluation guide](../software/evaluation/firmware/EVAL-GUIDE.md) supplies the current acceptance matrix. |
| `fixtures/` | [Immutable THA traceability metadata](fixtures/qc/tha-baseline-traceability.json). Institutional source is not copied into CI. |
| `evidence/` | No relocated physical/study records yet. App [historical evidence](../software/evaluation/firmware/evidence) and [TEST-PROTOCOL](../software/evaluation/firmware/TEST-PROTOCOL.md) remain intact and colocated. |
| `reports/` | Dated [2026-09-24 QC report](reports/qc/2026-09-24/QC-EVALUATION.md) and [JSON](reports/qc/2026-09-24/qc-eval-results.json), preserved snapshots rather than current runs. |

[QC execution](../tools/qc/README.md) writes new ignored `artifacts/qc/` output.
Do not overwrite dated reports. Old paths inside historical records identify the
original setup; they are not current commands or broken navigation to repair.

Keep planned, calculated, compiled, host-tested and hardware-observed claims
separate. Associate each new observation with its actual image/source, setup,
fixture, operator and date. A successful build or host suite cannot establish
physical timing, audio performance, clinical validity or human-study acceptance.
Hardware/study execution requires its own authorization and stopping criteria.