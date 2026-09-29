# Repository Guidance

## Route the Task

Start at [README.md](README.md) and the relevant component, not the whole tree.
[REPO-MAP.md](REPO-MAP.md) is the maintained register; [CONTRIBUTING.md](CONTRIBUTING.md)
defines executable checks and prerequisites.

- Firmware, pins, controls: [app README](software/evaluation/firmware/README.md), then the relevant `src`, `include`, `boards` and colocated tests.
- Capture/analysis: [host navigation](software/evaluation/host/README.md). Host tools remain inside the evaluation app.
- Requirements/design/decisions/risks: `engineering/`; consult the [decision register](engineering/decisions/open-questions.md) and [evaluation requirements](software/evaluation/firmware/EVAL-GUIDE.md).
- Electronics/mechanics/assembly: [hardware notes](hardware/assembly/hardware.md) and the authoritative app overlay. Do not fabricate CAD projects or promote old wiring claims.
- System verification/studies: [verification navigation](verification-validation/README.md). Keep evidence, reports and plans distinct.
- Research/thesis/planning: `research/`, `thesis/`, `project/`. Preserve paired investigation records; the research runner performs external requests and is not a test.
- CI/QC/toolchain: [CI contract](tools/ci/CI-QUALITY-GATES.md), [QC contract](tools/qc/README.md), `tools/toolchain/`.

## Search and Ownership

Use `git ls-files` first, scoped to the owning component; reconcile relevant
untracked additions separately. Do not infer maintained coverage from a filesystem
search. Exclude `.git/`, installed Zephyr modules/SDKs/blobs, `.venv/`, `.ci-workspace/`,
`build/`, `build-*/`, caches, `artifacts/` and the historical inventory CSV from
default reads. Old ignored trees under `Development/` are not source.

Keep app-local tools/tests/evidence together. Product software is status-only;
do not infer implemented layers from deleted legacy placeholders. Never edit
generated code or dependencies. Preserve user edits and coordinate one writer per
file; check staged, unstaged and untracked state before changes.

## Evidence and Permissions

Run the smallest applicable checks from CONTRIBUTING; distinguish proposed,
calculated, compiled, host-tested and hardware-observed results. `run_ci.py all`
does not run host pytest or native logic execution. Missing tools block checks;
they do not authorize installation or weakening gates.

Do not rewrite historical app evidence/TEST-PROTOCOL, research MD/JSON/logs, the PDF,
dated QC snapshots or the inventory to make old claims current. New QC output is
ignored under `artifacts/qc/`.

Obtain separate explicit approval for provisioning/downloads, environment cleanup,
hardware flashing/serial/device-network operations, research execution, external
writes, staging/commits, each push, and branch/worktree changes. Issue trackers and
PRs are read-only unless a specific write is authorized. Do not expose credentials.

This is the sole repository-wide agent policy; do not duplicate it in a global
Copilot instruction file or add shared editor settings implicitly.