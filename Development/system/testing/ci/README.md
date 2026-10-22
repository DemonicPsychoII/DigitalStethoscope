# CI tooling

[Detailed CI operations](OPERATIONS.md) covers the workflow, suite table, retained
evidence, minutes savings and staged native-review migration.

[CI-QUALITY-GATES.md](../CI-QUALITY-GATES.md) is the authoritative guide for
setup, check selection, prepared environments and publication. Merge and review
policy lives in the repository's [AGENTS.md](../../../../AGENTS.md).

| File | Responsibility |
|---|---|
| `run_ci.py` | Local/CI static, firmware and QC entry points. |
| `build_support.py` | Shared workspace paths, environment and firmware profiles. |
| `toolchain.json` | Toolchain, board and module pins. |
| `requirements-ci.txt` | Hash-locked static-check dependencies. |
| `setup_zephyr.py`, `setup_zephyr.sh` | Canonical provisioner and Linux compatibility entry point. |
| `prepared_env.py` | Validate prepared package, source, compiler and blob state. |
| `firmware_changes.py` | Select affected firmware, host, tooling and merge-gate suites. |
| `daily_build.py` | Skip unchanged successful daily integration builds. |
| `firmware_release.py` | Boot identity and release manifest/staging. |
| `validation_tools.py`, `compiler_cache.py` | Reuse prepared checksum-verified validators and compiler-cache binaries. |
| `benchmark_build.py` | Controlled build timing and comparison. |
| `ci_evidence.py` | Record the tested tree separately from the PR's advertised head. |
| `ci_results.py` | Required accounting; rejects failure, cancellation and missing selector output. |
| `native_tests.py` | Instrumented ztest logic with logs and a JUnit record. |
| `release_reuse.py` | Promote successful integration artifacts for the exact current commit. |
| `post_merge.py` | Post-merge failure confirmation; infrastructure failures never trigger a revert. |
| `native_review.py` | Staged native review protection and legacy gate retirement. |
| `validate_docs.py` | Documentation links, rendered diagrams, these indexes, repeated facts and the thesis kit. |
| `test_*.py` | Regression coverage for tooling, publication and QC failures. |

`validate_docs.py` fails when a script in this directory is missing from the table.

Run the tooling suite from the repository root:

```powershell
python -m unittest discover -s Development/system/testing/ci -p 'test_*.py'
```

Updated by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.

Updated by Claude-Opus-5.5 on behalf of Nico running in T3 Code through Claude Code.
