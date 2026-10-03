# AGENTS.md — DigitalStethoscope

## Merge policy

- **Enforcement starts only after a post-merge step.** Until the owner (or an agent on the
  homelab host, from HomelabServer) runs
  `scripts/github/apply-merge-policy.sh --apply DigitalStethoscope`, the `integration` ruleset
  requires only `Quality / Static Checks` and `Zephyr / Firmware Build`. `agent-gate` is advisory
  until then, the `approved` label does not exist, and the auto-revert workflow cannot open PRs.
  Follow the policy below anyway: merge only when `agent-gate` is green.
- Work on a branch, open a PR into `integration`, and fill in `.github/pull_request_template.md`.
- **Merge authorization.** An agent may merge its own PR only when the `agent-gate` status
  (`.github/workflows/agent-gate.yml`, logic in `.github/agent-gate/agent_gate.py`) is green, and
  green means one of:
  - **quick fix**: a small correction to existing behaviour with no unresolved owner question.
    Needs independent review and required checks.
  - **feature / policy**: anything new, or any change to the gate, workflows, PR template or
    agent instructions. Needs the same, **plus explicit owner approval**. Passing CI and review
    alone never authorize it.
  - **pure revert**: a machine-verified exact inverse of merge(s). Merges once required checks
    pass, with no review. Any extra change makes it a fix that needs normal review.

  The PR body carries
  `<!-- agent-author harness=<claude-code|codex> model=<id> session=<id> class=<quick-fix|feature|policy|revert> -->`
  and a filled `## Risk & rollback` (what could break / how verified / how to revert). Evidence
  lives in PR comments, each marker on its own line:
  - review: another agent session checks task fit and correctness and posts
    `<!-- agent-review verdict=<approve|changes> sha=<head sha> reviewer=<harness>/<model> session=<id> -->`.
    Prefer a different provider/model; the same model in a separate session is acceptable when
    provider limits require it. A push invalidates the review.
  - owner approval: the owner applies the `approved` label (stronger: agents never add it). For
    an approval the owner gave in chat, record it verbatim:
    `<!-- owner-approval sha=<head sha|any> quote="<the owner's words>" -->`. Only record an
    answer to the specific question about this PR, never approval inferred from unrelated chat.
  - owner questions: ask in chat with the PR link and post `<!-- owner-question id=<short-id> -->`
    with the question in the PR. The gate stays red until `<!-- owner-answer id=<short-id> -->`
    with the answer is posted. Resolving a thread is not an answer.

  `Quality / Static Checks` and `Zephyr / Firmware Build` must be green (the firmware build is
  skipped, which counts as green, when no firmware input changed). All agents and the owner share
  one GitHub account, so class, session and owner-approval comments are honour-based. The label
  is the stronger signal. Then: `gh pr merge <n> --merge --match-head-commit <sha>`. Never
  `--admin`, and never add the `approved` label yourself.
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
