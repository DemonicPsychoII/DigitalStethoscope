# CI tooling

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
| `benchmark_build.py` | Controlled build timing and comparison. |
| `test_*.py` | Regression coverage for tooling, publication and QC failures. |

Run the tooling suite from the repository root:

```powershell
python -m unittest discover -s Development/system/testing/ci -p 'test_*.py'
```

Updated by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
