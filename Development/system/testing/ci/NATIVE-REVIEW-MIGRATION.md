# Native approval migration and rollback

Native approval migration is deferred because fallback reviews currently use the PR author's GitHub account. Separate agent sessions can satisfy the legacy review policy, but GitHub does not accept an author's approval of their own PR. Migration therefore needs a separate reviewer App or account.

Until that identity exists and both probes below pass, `agent-gate` remains required and `CI_NATIVE_REVIEW` remains unset. This guide does not authorize credential creation or paid reviews for the migration.

The migration helper previews changes by default. Applying them requires an authorized administrator login. Existing rules, check identities and bypass actors are preserved; credentials remain outside the repository.

Run the helper from the checkout root. Its first apply saves `artifacts/ci/native-review-before-<owner>_<repo>-<ruleset>.json` inside the checkout. Copy that snapshot to an external location before continuing with the migration. Keep the external copy for rollback.

Migration has three stages:

1. **Add native protection.** The custom `agent-gate` remains required during the transition.

   ```sh
   python Development/system/testing/ci/native_review.py prepare \
     --repo DemonicPsychoII/DigitalStethoscope --ruleset 21015545
   # Inspect the JSON, then repeat with --apply.
   ```

   The added protection requires one approving review and resolved conversations. Pushes dismiss stale approvals. CodeRabbit must issue an approving review; a comment or progress check does not satisfy this rule.

2. **Verify both reviewer identities.** Two probe PRs demonstrate approval by CodeRabbit and by the separate fallback reviewer. Each probe needs `reviewDecision=APPROVED` and the tested reviewer's approval of its current head. The helper rejects other approving reviewers, including retained older approvals, so each probe tests one identity. Comment-only verdicts cannot satisfy native approval.

3. **Retire the custom check.** This stage follows successful verification of both probes.

   ```sh
   python Development/system/testing/ci/native_review.py finish \
     --repo DemonicPsychoII/DigitalStethoscope --ruleset 21015545 \
     --coderabbit-pr CR_PROBE_NUMBER --fallback-pr FALLBACK_PROBE_NUMBER \
     --fallback-login SEPARATE_REVIEWER_LOGIN
   # Inspect the JSON and probes, then repeat with --apply.
   ```

   The helper removes only `agent-gate` from required statuses, then sets `CI_NATIVE_REVIEW=true` to stop custom gate and review-signal jobs.

   Native reviews do not enforce session markers, owner-question markers or a CodeRabbit-only reviewer identity. PRs with unanswered owner questions remain draft with auto-merge disabled. Reverts also require approval in native mode.

Rollback removes `CI_NATIVE_REVIEW` to re-enable gate jobs, restores the saved ruleset's writable fields (`name`, `target`, `enforcement`, `conditions`, `rules` and optional `bypass_actors`), and dispatches `agent-gate.yml` for open PRs. Protection remains active throughout the transition.


[Return to verification operations](OPERATIONS.md).
