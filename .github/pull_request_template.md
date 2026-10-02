<!-- Agent PRs: replace the next line's placeholders (harness, model id, your session id). -->
<!-- agent-author harness=<claude-code|codex> model=<id> session=<id> -->

## Summary

<!-- What changes and why, in a few sentences. Link the issue/plan if there is one. -->

## Risk & rollback

<!-- agent-gate blocks the merge until all three are answered concretely. -->
- **What could break:**
- **How verified:**
- **How to revert:**

## Verification checklist

- [ ] Smallest relevant checks run locally (tests / type-check / lint / build) — commands and results above
- [ ] CI green on the head commit
- [ ] Self-reviewed the full diff (`gh pr diff`), no debug leftovers, secrets, or unrelated changes
- [ ] A separate reviewer session (different model family preferred) posted an `agent-review` verdict for the head SHA
- [ ] All review threads resolved; findings fixed or answered
- [ ] Deploy / host-install steps (if any) listed under "How to revert"
