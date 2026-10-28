---
name: stetho-verify
description: When Nico explicitly says "stetho verify" or "stetho-verify" to invoke this skill.
metadata:
  scope: project
---

# Stetho verification

## Project scope

Use this skill only within the DigitalStethoscope repository.
Repository placement defines discovery scope; the metadata records intent.
Outside this project, stop without applying this workflow.

## Explicit invocation only

Stop here unless Nico explicitly invoked this skill for the current task by
saying "stetho verify", "stetho-verify" or "$stetho-verify". A prior explicit invocation
continues to apply while its task is active. Quoted examples, discussion of
the skill, relevant subject matter and references from other skills do not
count as invocation. If not invoked, do not follow the workflow below;
continue the user's task under the otherwise applicable instructions.

References below to other stetho skills are suggested handoffs, not permission
to activate them. Run another stetho skill only if Nico explicitly invoked
that skill too. Otherwise describe the useful next step without making its
invocation a prerequisite for completing already authorized work.

Read AGENTS.md, Development/system/process/README.md,
Development/system/testing/specification-verification.md and the relevant
parts of Development/system/testing/ci/OPERATIONS.md. Paths are repository-root
relative. Inspect the affected design, production code and existing harness.

## Derive the cases

Identify full requirements and design commit hashes and the implementation
revision under test. Derive expectations from the agreed documents, using
implementation details to drive the harness rather than define correctness.
Link every case to its REQ/VT identifier or specific design contract.

Cover normal operation, boundaries and specified failures, including timeout,
retry and cancellation where applicable. Missing expected behavior or an
unresolved acceptance input returns to design; do not invent a limit or oracle.
Preserve stable identifiers and document genuine coverage gaps.

Choose the appropriate observation boundary: unit, deterministic L2 simulation,
real-service integration, system verification or manual device execution.
Reuse the existing harness. For L2, run production logic with controlled L1
and kernel substitutes, fresh scenario state and explicit simulated time/events.
Report which services are real. Simulated deadlines do not establish physical
timing; controlled threads and locks do not establish target scheduling.

## Implement and run

Create executable tests, test-only substitutes and manual procedures in a
separate Tests PR. Use stetho-manual for device or human-observation cases.
Do not add production abstractions only to make tests convenient.
CI executes committed cases; it must not regenerate expectations on a push.

Run the relevant existing commands from OPERATIONS.md. Diagnose failures in
the implementation, test, substitute or specification before correcting them.
Do not weaken an expectation to obtain a pass. Route production/design fixes
to the appropriate stage. Report documented XFAILs as known defects, never as
verified behavior; leave physical cases pending until actually executed.

## Produce reviewable evidence

Include a readable list of scenarios, linked basis and expected results, how
to run them, and the remaining unverified behavior. Results identify production
and test revisions, toolchain/configuration, substitutions, actual outcomes
and diagnostic evidence. A reference to a VT identifier is not proof of coverage.

Nico reviews the case list and records agreement or findings before that list
and its results enter GitLab review evidence. AI reviews executable test source;
it cannot supply Nico's agreement. This does not introduce a human merge gate.

Use ship or file-pr for the requested delivery scope and current repository
review policy. Use stetho-handoff when preparing GitLab review evidence.
