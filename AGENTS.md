# AGENTS.md — DigitalStethoscope

## Merge policy

Heavy CI runs only in disposable VMs on the home-lab runner pool. Static/QC suites use
`homelab-stethoscope-static-<run-id>-<attempt>`; firmware uses
`homelab-zephyr-<run-id>-<attempt>`. No GitHub-hosted fallback or `ZEPHYR_RUNNER_LABELS` override.
Offline home-lab/fork jobs remain queued until the owner handles them; merge/approval accounting
workflows may remain hosted. Preserve required check names and existing gate policy.

- Work on a branch and open a PR into `integration` using `.github/pull_request_template.md`.
- **Merge authorization:** quick fixes, features and policy changes require independent automated
  review of the current head, required CI, answered owner questions and resolved review threads.
  Human approval is not a prerequisite. Agents may apply a legacy `approved` label after review;
  never invent an owner quote. The required `agent-gate` status enforces the migrated policy.
  A machine-verified pure revert requires CI but waives review; additional changes need normal review.
- The PR body carries
  `<!-- agent-author harness=<claude-code|codex> model=<id> session=<id> class=<quick-fix|feature|policy|revert> -->`
  and concrete `## Risk & rollback` evidence. Another agent session records
  `<!-- agent-review verdict=<approve|changes> sha=<head sha> reviewer=<harness>/<model> session=<id> -->`.
  Prefer a different provider/model; a push invalidates the verdict. Configured CodeRabbit native
  approval also counts when it approves the current head; a progress check alone does not.
- **Primary reviewer:** use CodeRabbit for independent PR review in this repository. If no review
  starts, request `@coderabbitai review` once and use the app's PR watcher while it runs.
  If CodeRabbit is unavailable, rate-limited, fails, or remains stuck without completing a review
  across two watcher updates at least 15 minutes apart, use the existing GlobalAgentContext
  `rules/git.md` and `review` skill workflow with a separate agent session as the fallback.
  Record the reason for fallback in the PR. Never enable paid usage to obtain a review.
  Fallback review must approve the current head and address any existing CodeRabbit blocking
  findings; it does not bypass CI, owner questions, or conversation resolution.
- Only material correctness, safety, security or verification findings block review. Nitpicks are
  optional: fix, acknowledge or decline them with a reason, then resolve the conversation.
  Follow-up reviews focus on blocking fixes and regressions introduced by them.
- Genuine owner questions still require an answer: post `<!-- owner-question id=<short-id> -->`
  with the question, then `<!-- owner-answer id=<short-id> -->` with the real answer. Thread
  resolution alone is not an answer.
- Once review and conversations are settled, enable `gh pr merge <n> --auto --merge
  --match-head-commit <sha>` while required CI finishes. Use the app's PR watcher; return on failure
  or new feedback instead of polling. Verify the merge and affected deployment afterward.
  Never use `--admin` or bypass required CI/review.
- **After a merge, a failed check is not yet a regression.** The gates re-run on `integration`.
  If they fail, `post-merge-revert.yml` re-runs the failed jobs once:
  - a green re-run is a flaky check: no revert, and the owner is told on the merged PR;
  - a failure on the re-run is a confirmed regression, and the workflow opens a `revert/<sha7>` PR
    (class=revert) and @-mentions the owner.

  Runtime comes first. Red builds never publish firmware, so the last working firmware on
  Personal Cloud stays available without any merge. The revert only restores a green
  `integration`. Merge it once agent-gate (pure-revert verification + checks) is green, or land a
  corrective PR instead and close the revert. Never merge a revert for an unconfirmed failure.
  By hand: `bash .github/agent-gate/revert-last-merge.sh <pr|sha|last>...` (`--deploy` is not
  supported in this repository).
- Before pushing, run the smallest relevant checks: `python Development/system/testing/ci/run_ci.py
  static`, `python -m pytest -q Development/system/coding/bringup-zephyr/tests/host`,
  `python -m unittest discover -s .github/agent-gate`, and for firmware changes `run_ci.py build`.
  Hardware flashing, serial and device-network operations still need the owner.
