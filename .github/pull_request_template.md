<!-- Agent PRs: replace the next line's placeholders. class: quick-fix (small correction to existing behaviour, no open owner question) | feature | policy (both need explicit owner approval) | revert (generated pure reverts only). -->
<!-- agent-author harness=<claude-code|codex> model=<id> session=<id> class=<quick-fix|feature|policy|revert> -->

## Summary

<!-- What changes and why, in a few sentences. Link the issue/plan if there is one. -->

## Risk & rollback

<!-- agent-gate blocks the merge until all three are answered concretely. -->
- **What could break:**
- **How verified:**
- **How to revert:**

## Owner decisions

<!-- feature/policy: how the owner approved (the `approved` label, or an owner-approval comment quoting
     the chat answer). Questions for the owner: ask in chat with the PR link AND post an owner-question
     comment; the gate stays red until a matching owner-answer comment records the answer.
     Marker syntax: AGENTS.md, "Merge authorization". -->
- None needed (quick fix) / approved by the owner on <date>: "<quote>"

## Verification checklist

- [ ] Smallest relevant checks run locally (tests / type-check / lint / build) — commands and results above
- [ ] CI green on the head commit
- [ ] Self-reviewed the full diff (`gh pr diff`), no debug leftovers, secrets, or unrelated changes
- [ ] Another agent session (different provider/model preferred) posted an `agent-review` verdict for the head SHA
- [ ] Every owner question answered and recorded; feature/policy changes carry the owner's approval
- [ ] All review threads resolved; findings fixed or answered
- [ ] Hardware / flashing steps the owner must run (if any) listed under "How to revert"
