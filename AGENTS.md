# AGENTS.md — DigitalStethoscope-B.Thesis

## Merge policy

- Work on a branch, open a PR into `integration`, and fill in `.github/pull_request_template.md`.
- **Agents merge their own PRs** once the required `agent-gate` status is green — no human label.
  It (`.github/workflows/agent-gate.yml`, logic in `.github/agent-gate/agent_gate.py`) requires: not
  draft; `<!-- agent-author harness=<claude-code|codex> model=<id> session=<id> -->` in the body; a
  filled `## Risk & rollback` (what could break / how verified / how to revert); the newest
  `<!-- agent-review verdict=approve sha=<head sha> reviewer=<harness>/<model> session=<id> -->`
  comment from a *different* session (prefer another model family) naming the current head; no
  unresolved threads; `Quality / Static Checks` and `Zephyr / Firmware Build` green. A push
  invalidates the review. Then, if you judge it unlikely to fail:
  `gh pr merge <n> --merge --match-head-commit <sha>`. Never `--admin`.
- Merging re-runs the gates on `integration`; if they fail, `post-merge-revert.yml` opens a
  `revert/<sha7>` PR and @-mentions the owner on the merged PR. Merge it through the gate (verified
  pure reverts skip the review), or re-run the failed job and close it if it was a flake. By hand:
  `bash .github/agent-gate/revert-last-merge.sh <pr|sha|last>`.
- Before pushing, run the smallest relevant checks: `python Development/system/testing/ci/run_ci.py
  static`, `python -m pytest -q Development/system/coding/bringup-zephyr/tests/host`, and for firmware
  changes `run_ci.py build`. Hardware flashing, serial and device-network operations still need the
  owner.
