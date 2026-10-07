# CI selection and prepared environments

[Detailed CI operations](OPERATIONS.md) covers the workflow diagram, selected suites,
retained evidence, minutes savings and staged native approval migration.

[CI quality gates](../CI-QUALITY-GATES.md) documents required contexts,
triggers, suite selection, publication and local commands.
[AGENTS.md](../../../../AGENTS.md) defines review and merge policy;
CodeRabbit progress alone is not approval.

## Prepared environments

Static jobs reuse `/opt/stethoscope-ci` only when Python 3.12.10, installed
packages and both hash-locked requirement files match the preparation manifest.
Otherwise normal Python setup and pinned installation run.

Firmware jobs validate `/opt/zephyr-workspace` against checkout pins, actual
Zephyr/module revisions, package versions, compiler and Espressif blob hashes.
A complete match skips setup; missing/changed state falls back to canonical
setup. Firmware profiles and native simulation still build pristine, without
compiler caching.

See HomelabServer's `scripts/ci-runner/STETHOSCOPE.md` for image preparation and
rollback. Bases are read-only and guests disposable; this creates no persistent
writable runner or public-fork authorization. Measure real prepared-image runs
before claiming a timing improvement.

Updated by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
