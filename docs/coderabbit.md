# CodeRabbit reviews

Nico confirmed free OSS review access for DigitalStethoscope on 26 October 2026.
The repository uses manual review requests rather than relying on automatic PR
opening or push triggers. Keep the GitHub App installed and leave optional
usage-based reviews and paid agent services disabled.

[.coderabbit.yaml](../.coderabbit.yaml) applies different review guidance to:

- Embedded code under `Development/system/coding/`.
- Test and evidence material under `Development/system/testing/`.
- Academic planning and Markdown under `preThesis/`.
- LaTeX thesis sources (`*.tex`) and bibliography files (`*.bib`), wherever stored.
- Requirements under `Development/system/requirements/`.

If the final thesis uses Markdown outside `preThesis/`, add its directory to
`reviews.path_instructions` when that layout is established. Review the text
sources; PDF and Word files are excluded by CodeRabbit by default. Builds and
human inspection verify the rendered thesis.

## Daily workflow

CodeRabbit is the primary independent reviewer for DigitalStethoscope. Keep the
existing GlobalAgentContext `rules/git.md` and `review` skill process as the
fallback: use a separate agent session if CodeRabbit is unavailable, rate-limited,
fails, or remains stuck across two watcher updates at least 15 minutes apart.
Request a missing review once with `@coderabbitai review`, then use the app's
PR watcher. Record why fallback was needed. A fallback verdict must approve the
current head and address any material CodeRabbit findings already posted; it cannot
override unresolved findings, required CI, or owner questions. Do not enable
paid reviews or Agent usage to work around limits.

1. Open a focused, ready-for-review PR into `integration`. Check for an active
   or completed review of the current head; otherwise comment `@coderabbitai review`
   once. Do not duplicate a running review. Use the app's PR watcher.
2. Read the feedback. Fix material issues and explain false positives or
   declined optional suggestions in their original review threads.
3. Batch fixes before pushing. A push invalidates the previous head's verdict;
   request review of the new head once when ready. Do not assume an automatic
   incremental review will start.
4. Resolve dispositioned threads and wait for required repository checks.
   The existing gate recognizes CodeRabbit's native approval of the current
   head; a summary or progress check does not count as approval.

`request_changes_workflow` allows CodeRabbit to issue a native approval once
its review is complete, comments are resolved, and its pre-merge checks are
clear. It does not merge PRs or waive CI, conversation resolution, or the
existing review gate.

Author-issued approval commands are disabled with `allow_author_approval: false`;
the PR author cannot turn a manual bot command into the independent approval
trusted by the gate.

Free OSS reviews still have rate limits. Comment `@coderabbitai rate limit`
to check availability; wait rather than enabling paid continuation. Disable or
pause unnecessary review triggers if repeated pushes consume the allowance.
A green CodeRabbit status saying "Review rate limited" is not a completed review
or an approval. Use the separate-session fallback above when throttled.

For academic work, require evidence for claims and never accept invented
references or measurements. CodeRabbit feedback supplements source verification,
supervisor review, and hardware validation.

## First verification

After installation, use one small code PR and one small writing PR to confirm
that each receives useful feedback under the appropriate instructions. Verify
the bot's review and configuration status, not merely that an app is installed.
A schema-valid configuration does not prove the quality of the live reviews.

- [Free OSS offer](https://www.coderabbit.ai/oss)
- [Path instructions](https://docs.coderabbit.ai/configuration/path-instructions)
- [Review commands](https://docs.coderabbit.ai/reference/review-commands)

Updated by GPT-6.1-Sol on behalf of Nico running in codex.
