# CodeRabbit reviews

Nico uses CodeRabbit Pro for this repository. Keep optional usage-based reviews and paid Agent services disabled. Review limits come from the active account; do not hard-code a free-tier quota.

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

1. Open a focused, ready-for-review PR into `integration`. Automatic reviews
   are enabled; draft PRs are excluded.
2. Read the feedback. Fix material issues and explain false positives or
   declined optional suggestions in their original review threads.
3. Batch fixes before pushing. CodeRabbit normally reviews new commits
   incrementally. Request `@coderabbitai review` only if automatic review did not trigger; never request another while one is running.
4. Address critical/major and unclassified findings, then wait for required repository checks. Minor findings and nitpicks may remain open or be deferred.
   The existing gate recognizes CodeRabbit's native approval of the current
   head or a fully accounted, explicitly minor/nitpick-only current-head changes request. A summary or progress check alone does not count as review.

`request_changes_workflow` allows CodeRabbit to issue a native approval once
its review is complete, comments are resolved, and its pre-merge checks are
clear. It does not merge PRs or waive CI, blocking conversation resolution, or the
existing review gate.

Author-issued approval commands are disabled with `allow_author_approval: false`;
the PR author cannot turn a manual bot command into the independent approval
trusted by the gate.

Rely on automatic reviews and batch related fixes before pushing. Do not enable paid continuation to work around limits.

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
