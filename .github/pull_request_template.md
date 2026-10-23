<!-- Agent-managed PRs: fill the marker and Risk & rollback fields. Humans and other bots may omit these; untouched marker placeholders do not declare agent authorship. All PRs need independent automated review; pure agent reverts are verified separately. -->
<!-- agent-author harness=<claude-code|codex> model=<id> session=<id> class=<quick-fix|feature|policy|revert> -->

## Summary

<!-- Concrete problem and resulting behavior. -->

## V-model stage

<!-- Apply one matching label. For mixed work, list other stages below. Explain infrastructure-only exceptions. -->
- Stage: `v:architecture` / `v:design` / `v:l2` / `v:l1` / `v:tests`

## Basis

- Requirements and design revision: <!-- Full commit SHA and document links. -->
- Covered cases and requirements: <!-- VT-xx / REQ-xx; explain gaps. -->
- Agreed decisions: <!-- Links to the discussion or decision record. -->

<!-- For test PRs, fill the case list. The developer reviews this list; AI reviews test code. -->
| Scenario | Basis (VT / REQ / design link) | Expected result |
| --- | --- | --- |

- Developer case-list review: <!-- Link to agreement or findings; pending until reviewed. -->

## Risk & rollback

- **What could break:**
- **How verified:**
- **How to revert:**

## Owner decisions

<!-- Only real unanswered decisions belong here. No routine human approval is required. -->
- None.

## Verification checklist

- [ ] Relevant local checks passed; limitations recorded
- [ ] Full diff reviewed; no secrets or unrelated changes
- [ ] Current head independently approved by an agent or configured CodeRabbit
- [ ] Blocking findings addressed; all conversations have dispositions and are resolved
- [ ] Genuine owner questions answered
- [ ] Required CI enforced; follow any explicit owner manual-review hold
- [ ] Deployment and rollback steps recorded where needed
