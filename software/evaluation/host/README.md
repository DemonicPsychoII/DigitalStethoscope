# Host Evaluation Tools

Host tooling remains colocated in the intact firmware application:

- [Evaluation CLI](../firmware/tools/evaluate.py) and [dependency lock](../firmware/tools/requirements.txt).
- [Host tests](../firmware/tests/host) and [evaluation guide](../firmware/EVAL-GUIDE.md).
- [Contributor checks](../../../CONTRIBUTING.md) for local tests and prerequisites.

Extraction into this scope is deferred. WAV evaluation is local; serial capture,
fixture upload and remote FHIR readback require separate operation approval.