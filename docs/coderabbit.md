# CodeRabbit reviews

CodeRabbit's free public-repository offer covers DigitalStethoscope. Install its
GitHub App for this repository at [CodeRabbit](https://app.coderabbit.ai), then
confirm OSS access in the correct account. Leave optional usage-based reviews and
paid agent services disabled to keep this workflow free. A trial banner alone
does not prove permanent free access.

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

1. Open a focused, ready-for-review PR into `integration`. Automatic reviews
   are enabled; draft PRs are excluded.
2. Read the feedback. Fix material issues and explain false positives or
   declined optional suggestions in their original review threads.
3. Batch fixes before pushing. CodeRabbit normally reviews new commits
   incrementally. If needed, comment `@coderabbitai review`.
4. Resolve dispositioned threads and wait for required repository checks.
   The existing gate recognizes CodeRabbit's native approval of the current
   head; a summary or progress check does not count as approval.

`request_changes_workflow` allows CodeRabbit to issue a native approval once
its review is complete, comments are resolved, and its pre-merge checks are
clear. It does not merge PRs or waive CI, conversation resolution, or the
existing review gate.

Free OSS reviews still have rate limits. Comment `@coderabbitai rate limit`
to check availability; wait rather than enabling paid continuation. Disable or
pause unnecessary review triggers if repeated pushes consume the allowance.

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

Configured by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
