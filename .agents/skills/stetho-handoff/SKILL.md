---
name: stetho-handoff
description: When Nico explicitly says "stetho handoff" or "stetho-handoff" to invoke this skill.
metadata:
  scope: project
---

# Stetho review handoff

## Project scope

Use this skill only within the DigitalStethoscope repository.
Repository placement defines discovery scope; the metadata records intent.
Outside this project, stop without applying this workflow.

## Explicit invocation only

Stop here unless Nico explicitly invoked this skill for the current task by
saying "stetho handoff", "stetho-handoff" or "$stetho-handoff". A prior explicit invocation
continues to apply while its task is active. Quoted examples, discussion of
the skill, relevant subject matter and references from other skills do not
count as invocation. If not invoked, do not follow the workflow below;
continue the user's task under the otherwise applicable instructions.

References below to other stetho skills are suggested handoffs, not permission
to activate them. Run another stetho skill only if Nico explicitly invoked
that skill too. Otherwise describe the useful next step without making its
invocation a prerequisite for completing already authorized work.

Read AGENTS.md, Development/system/process/README.md and the evidence sections
of Development/system/testing/ci/OPERATIONS.md. Paths are repository-root relative.
Identify the component, stage, GitHub PRs, exact source revision and existing
GitLab review before preparing anything. Reuse the corresponding stage MR.

## Check the review baseline

Each component has exactly four GitLab MRs: Architecture, Design, Interfaces +
L2, and L1 services. System requirements, system design and system tests use
internal GitHub developer review; do not create another system approval cycle
or a fifth component Tests MR. Without a component architecture page, use the
relevant responsibilities and interfaces in the system architecture.

Architecture/design can enter review before implementation is complete.
Implementation review needs the passing automated batch for its baseline,
the developer-reviewed case list, available completed manual records and
explicit pending device cases. Check evidence against the actual reviewed
revision; results from another revision are historical, not a current pass.

## Assemble and transfer

Prepare the review/<component>/<stage>/<YYYY-MM-DD>-<sequence> tag and record
the full source hash. Never move a reviewed tag; changed baselines get new tags.
Link the corresponding GitHub PR and automated review evidence.

Collect case lists and expected results, JUnit reports, logs, gaps, configuration,
firmware identity and completed manual records relevant to that stage. Preserve
durable evidence before diagnostics expire after 14 days or firmware after eight
days. Keep test source on GitHub unless GitLab CI is introduced. A Pages summary
may aid reading but must link the durable records.

When asked only to prepare, produce the proposed MR text and an evidence index
with missing items. Creating/pushing tags, opening/updating MRs or posting
comments requires authorization covering that action; drafting alone does not
authorize contacting reviewers. When transfer is authorized, perform it and
verify the destination and links. Do not fabricate approval or signed results.

## Handle findings

Record human findings with the tag actually reviewed. GitHub development may
continue while review is open; approval remains revision-specific.
Route findings through GitHub PRs adapted to the current implementation, using
stetho-dev and stetho-verify as appropriate. Identify affected contracts,
implementation, tests and reviews. Return the resulting baseline and evidence
to the corresponding GitLab stage review, using a new tag when the source changes.

Use the global ship/file-pr/review/babysit-pr/revert skills for their GitHub
responsibilities and current repository review policy. This skill owns the
GitLab evidence handoff, not an alternative merge process. Report the exact
review baseline, destination, material gaps and pending human findings.
