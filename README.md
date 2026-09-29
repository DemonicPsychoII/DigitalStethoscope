# Digital Stethoscope

Bachelor's thesis repository: technical definition, physical implementation,
evaluation firmware, verification, research and thesis material. The ESP32-S3
application is evaluation software, not a released medical product.

## Start Here

- Firmware and wiring: [evaluation firmware](software/evaluation/firmware/README.md).
- Evaluation and evidence: [verification and validation](verification-validation/README.md).
- Thesis baseline: [submission brief](thesis/brief/Aufgabenbeschreibung-Abgabe.md).
- Development checks and prerequisites: [contributing](CONTRIBUTING.md).
- Maintained file register and historical inventory: [repository map](REPO-MAP.md).
- Agent routing and boundaries: [AGENTS.md](AGENTS.md).

## Scope Map

| Scope | Ownership and current material |
|---|---|
| `engineering/requirements`, `architecture`, `design` | Working technical definition, not thesis prose. No standalone documents yet; current evaluation requirements are in the [evaluation guide](software/evaluation/firmware/EVAL-GUIDE.md). |
| `engineering/decisions`, `risks` | [Open decisions](engineering/decisions/open-questions.md) and [contradictions](engineering/decisions/widersprueche.md). No separate risk register yet. |
| `hardware/electronics` | Board design, native CAD and deliberate releases. Current BOM/wiring notes remain in [assembly](hardware/assembly/hardware.md); no CAD project exists yet. Future real boards use `hardware/electronics/<board>/altium/` and sibling `releases/<rev>/`. |
| `hardware/mechanics`, `assembly` | Chestpiece/enclosure/mechanical implementation and assembly records. [Assembly notes](hardware/assembly/hardware.md) exist; no mechanical design yet. |
| `software/product` | [Future product status](software/product/README.md), with no implemented product deployment. |
| `software/evaluation/firmware`, `host` | [Intact Zephyr application](software/evaluation/firmware/README.md) and [host-tool navigation](software/evaluation/host/README.md). Tools/tests/evidence remain colocated with firmware. |
| `verification-validation/plans`, `fixtures`, `evidence`, `reports` | [System verification and validation](verification-validation/README.md), including traceability fixtures and dated QC reports. Software tests stay with their components. |
| `research/literature`, `investigations` | [Twelve paired investigations and prompt catalog](research/investigations/runs.json). No separate literature collection yet. |
| `thesis/brief`, `manuscript`, `figures`, `formal` | [Submission brief](thesis/brief/Aufgabenbeschreibung-Abgabe.md), internal/general drafts and preserved PDF. Manuscript, figures and formal-submission records are not populated yet. |
| `project/planning`, `meetings` | Intended schedule and coordination records; no maintained records yet. |
| `tools/ci`, `toolchain`, `qc` | [CI contract](tools/ci/CI-QUALITY-GATES.md), environment scripts and [QC evaluator](tools/qc/README.md). |

Unpopulated scopes are intentional destinations, not empty marker directories.
Evaluation code is not automatically promoted into product software. Hardware
acceptance, scientific claims and software test results remain separate.

## Local State and History

Installed dependencies and old builds under `Development/` remain local and ignored;
they are not maintained source and must not be recursively moved or deleted.
Historical app evidence, research payloads, the submission PDF and dated QC reports
retain their original contents, including old paths. New QC runs write ignored
`artifacts/qc/`, not the historical reports.
