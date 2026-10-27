---
name: stetho-dev
description: When Nico explicitly says "stetho dev" or "stetho-dev" to invoke this skill.
metadata:
  scope: project
---

# Stetho development

## Project scope

Use this skill only within the DigitalStethoscope repository.
Repository placement defines discovery scope; the metadata records intent.
Outside this project, stop without applying this workflow.

## Explicit invocation only

Stop here unless Nico explicitly invoked this skill for the current task by
saying "stetho dev", "stetho-dev" or "$stetho-dev". A prior explicit invocation
continues to apply while its task is active. Quoted examples, discussion of
the skill, relevant subject matter and references from other skills do not
count as invocation. If not invoked, do not follow the workflow below;
continue the user's task under the otherwise applicable instructions.

References below to other stetho skills are suggested handoffs, not permission
to activate them. Run another stetho skill only if Nico explicitly invoked
that skill too. Otherwise describe the useful next step without making its
invocation a prerequisite for completing already authorized work.

Read the repository AGENTS.md and Development/system/process/README.md.
Use paths below relative to the repository root. Read only the system and
component documents needed for the requested change.

## Establish the basis

Identify the component, intended behavior, affected REQ and VT identifiers,
and the requirements/design revisions. Distinguish an existing agreed design
from a proposal. Use recorded developer acceptance at an identified revision;
do not infer acceptance from a document merely existing or from AI review.
Ask Nico about consequential unresolved choices; continue independent work.

Requirements remain at system level. Architecture defines responsibilities,
boundaries and dependencies. Detailed design defines behavior, states, data,
parameters, interface contracts and failure handling. Shared decisions belong
at system level. Refine the relevant level without inventing extra documents.
Follow the repository source and citation rules for factual claims.

## Perform the scoped work

Keep each PR within its stage: Requirements, Architecture, Design, L2 or L1.
Use Process for development tooling and Records for project history or risk
acceptance. A small supporting documentation edit may accompany implementation.

Implement agreed interfaces and production L2 logic against substitute L1
services before the corresponding L1 services and driver wrappers. Reuse
completed work; this ordering does not require rebuilding existing layers.
Implement the production design without adding hooks solely for testing.

A necessary contract change gets a separate Design PR with the interface and
documentation adjustment. Dependent implementation merges wait for it. Trace
the change through callers, services, tests and any baseline already in review.
If behavior is unspecified, return that decision to design discussion.

Use stetho-verify for a new generated verification batch or changed test
expectations; those belong in a Tests PR. Keep existing tests running and
diagnose failures during development. Implementation may merge before the new
batch when existing required checks pass; GitLab implementation review waits
for its passing automated batch. Record pending device cases explicitly.

## Complete and deliver

Run the relevant checks from Development/system/testing/ci/OPERATIONS.md.
Record the stage, full basis commit hashes, affected REQ/VT identifiers and
links to real agreed decisions in the project PR template. Update affected
trace links and explicit gaps without maintaining a separate status document.

Use ship for authorized end-to-end delivery, or file-pr when asked only to
file a PR. Follow current repository and user review rules: CodeRabbit first,
current-head independent review, required CI and answered owner questions.
Minor findings may remain open under Nico's current instructions. Do not
reinterpret case-list agreement or manual sign-off as routine merge approval.

Use embedded-debugging for target faults and hardware-bring-up for a new or
revised board; retain the repository's owner-authorization boundary for flashing,
serial and device-network operations. Use excalidraw-communication when a design
discussion benefits from a board, homelab-research for substantial cited research,
and publish-plan when a browser-reviewable proposal helps. Use grilling when
Nico asks to challenge a decision. These skills support the current task;
they do not expand its scope.
