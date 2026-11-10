# AGENTS.md — DigitalStethoscope

## Agent skills

Project skills live in `.agents/skills/`, where Codex discovers them. Claude Code reads only
`.claude/skills/`, which is not tracked. To expose the skills to Claude Code in a checkout, run
from its root on Windows `cmd /c "mkdir .claude & mklink /J .claude\skills .agents\skills"`, or on
Linux `mkdir -p .claude && ln -sfT ../.agents/skills .claude/skills`.

## Thesis sources

Applies to bachelor-thesis work: `thesis-material/`, `preThesis/`, requirements/design/planning
rationale under `Development/system/`, and weekly slides or reports that feed the thesis.

- Back every factual or technical claim with a verifiable source and a full citation: authors,
  title, venue/publisher or standard number, year/version, DOI/URL where available, and access
  date for web sources. Own measurements cite their evidence with date and firmware revision.
- Prefer peer-reviewed literature, primary standards and vendor documentation. Record sources in
  `thesis-material/quellen.bib` and `thesis-material/quellen.md`, following their existing format.
  Both files are generated: add new records to `thesis-material/_build/supplemental-sources.json`
  (or the other `_build/` inputs) and run `python thesis-material/_build/build.py`.
- If no adequate source exists, say so explicitly and mark the claim as unsupported or as a
  project decision; never present it as established.
- Never invent or approximate citations, metadata or page numbers; mark unverified fields as such.

## Merge policy

Heavy CI runs only in disposable VMs on the home-lab runner pool. Static/QC suites use
`homelab-stethoscope-static-<run-id>-<attempt>`; firmware uses
`homelab-zephyr-<run-id>-<attempt>`. No GitHub-hosted fallback or `ZEPHYR_RUNNER_LABELS` override.
Offline home-lab/fork jobs remain queued until the owner handles them; merge/approval accounting
workflows may remain hosted. Preserve required check names and existing gate policy.

- Work on a branch and open a PR into `integration` using `.github/pull_request_template.md`.
- **Merge authorization:** quick fixes, features and policy changes require independent automated
  review of the current head, required CI, answered owner questions and resolved critical/major or unclassified review threads; minor findings and nitpicks may remain open or be deferred.
  Human approval is not a prerequisite. Agents may apply a legacy `approved` label after review;
  never invent an owner quote. The required `agent-gate` status enforces this policy until native review migration is validated.
  Native mode requires one eligible GitHub approval and dismisses stale approvals; separate
  reviewer credentials are necessary when agents share the PR author identity.
  Legacy mode waives review only for a machine-verified pure revert; additional changes need review.
- Agent-managed PRs carry
  `<!-- agent-author harness=<claude-code|codex> model=<id> session=<id> class=<quick-fix|feature|policy|revert> -->`
  and concrete `## Risk & rollback` evidence. Human and other bot PRs without an agent-author
  declaration do not need agent metadata; untouched template placeholders are ignored. They still
  need current-head independent review, required CI, answered owner questions and resolved blocking or unclassified threads.
  Agents must declare their authorship even when using the owner's GitHub account. Another agent session records
  `<!-- agent-review verdict=<approve|changes> sha=<head sha> reviewer=<harness>/<model> session=<id> -->`
  in a PR comment or a submitted PR review body.
  Prefer a different provider/model. A push invalidates the verdict unless the gate carries the
  approval forward: only when no newer `changes` verdict exists, the approved commit belongs to the
  PR (one of its commits, or a head it had before a force-push), and the PR's own diff against its
  current base is unchanged, as after a base merge, update-branch or a stacked PR's new base.
  A carried approval did not see the changes that arrived through the base. Configured CodeRabbit
  native approval also counts when it approves the current head; a progress check alone does not.
- `agent-gate` reports `pending` while a review is missing, stale or requested, and while
  required checks run. `failure` means the author must act.
- **CI and gate changes:** keep changes to `.github/agent-gate/**` or `.github/workflows/**` in a
  separate PR of class `policy`. The gate fails an agent PR that changes these paths without class
  `policy`; it does not check what else the PR contains. Fix a failing check in the code under
  test, never by weakening the check, gate or workflow.
- **Reviewers:** the independent agent review is the default reviewer. CodeRabbit (confirmed free OSS
  access) reviews only high-impact PRs, next to the agent review. Automatic CodeRabbit reviews are
  off. On a high-impact PR, add the `coderabbit` label, check for an active or completed
  current-head review, then comment `@coderabbitai review` once and use the app's PR watcher.
  Do not request another review while one is running. The gate waits for CodeRabbit only when the
  PR carries the `coderabbit` label or CodeRabbit has already reviewed it.
  Batch fixes before pushing; a changed head needs a new independent verdict unless carried forward.
  If CodeRabbit is unavailable, rate-limited, fails, or remains stuck without completing a review
  across two watcher updates at least 15 minutes apart, use the existing GlobalAgentContext
  `rules/git.md` and `review` skill workflow with a separate agent session as the fallback.
  Record the reason using `<!-- review-fallback sha=<head> reason=<unavailable|rate-limited|failed|stuck> -->`
  in a trusted maintainer comment. Native mode needs a real GitHub review from a separate
  reviewer App/account; comment markers and labels cannot satisfy GitHub approval.
  Never enable paid usage to obtain a review.
  Fallback review must approve the current head and address any existing CodeRabbit blocking
  findings; it does not bypass CI, owner questions, or conversation resolution.
- Only material correctness, safety, security or verification findings block review. Nitpicks are
  optional: fix, acknowledge, decline or defer them; their conversations may remain open.
  Follow-up reviews focus on blocking fixes and regressions introduced by them.
- Genuine owner questions still require an answer: post `<!-- owner-question id=<short-id> -->`
  with the question, then `<!-- owner-answer id=<short-id> -->` with the real answer. Thread
  resolution alone is not an answer.
- Unless the owner explicitly requests a manual hold, once review and conversations are settled, enable
  `gh pr merge <n> --auto --merge
  --match-head-commit <sha>` while required CI finishes. Use the app's PR watcher; return on failure
  or new feedback instead of polling. Verify the merge and affected deployment afterward.
  Never use `--admin` or bypass required CI/review.
- **After a merge, a failed check is not yet a regression.** The gates re-run on `integration`.
  If they fail, `post-merge-revert.yml` re-runs the failed jobs once:
  - a green re-run is a flaky check: no revert, and the owner is told on the merged PR;
  - the same verification step failing on both attempts is a confirmed regression;
    setup, runner and upload failures remain infrastructure or unconfirmed failures. For a
    confirmed regression, the workflow opens a `revert/<sha7>` PR
    (class=revert) and @-mentions the owner.

  Runtime comes first. Red builds never publish firmware, so the last working firmware on
  Personal Cloud stays available without any merge. The revert only restores a green
  `integration`. Legacy mode can waive review for machine-verified pure reverts. Native mode requires
  approval for reverts too. Merge after the active protections pass, or land a
  corrective PR instead and close the revert. Never merge a revert for an unconfirmed failure.
  By hand: `bash .github/agent-gate/revert-last-merge.sh <pr|sha|last>...` (`--deploy` is not
  supported in this repository).
- Before pushing, run `python Development/system/testing/ci/run_ci.py static`, the relevant
  [local checks](Development/system/testing/ci/OPERATIONS.md#setup-and-local-checks), and
  for firmware changes `run_ci.py build`.
  Hardware flashing, serial and device-network operations still need the owner.

See [CI operations](Development/system/testing/ci/OPERATIONS.md) for suite selection, artifacts,
minutes savings. See [native review migration](Development/system/testing/ci/NATIVE-REVIEW-MIGRATION.md)
for the staged migration and rollback. Owner questions remain mandatory;
in native mode keep the PR draft and auto-merge disabled until real answers are recorded.

## Identifier naming

Identifiers introduced by this project are fully written out, without abbreviations. Names required by external interfaces are exempt. Source comments explain non-obvious reasons; they contain no test status, progress markers or agent notes.
