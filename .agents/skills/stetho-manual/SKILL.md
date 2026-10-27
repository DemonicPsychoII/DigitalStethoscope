---
name: stetho-manual
description: When Nico explicitly says "stetho manual" or "stetho-manual" to invoke this skill.
metadata:
  scope: project
---

# Stetho manual tests

## Project scope

Use this skill only within the DigitalStethoscope repository.
Repository placement defines discovery scope; the metadata records intent.
Outside this project, stop without applying this workflow.

## Explicit invocation only

Stop here unless Nico explicitly invoked this skill for the current task by
saying "stetho manual", "stetho-manual" or "$stetho-manual". A prior explicit invocation
continues to apply while its task is active. Quoted examples, discussion of
the skill, relevant subject matter and references from other skills do not
count as invocation. If not invoked, do not follow the workflow below;
continue the user's task under the otherwise applicable instructions.

References below to other stetho skills are suggested handoffs, not permission
to activate them. Run another stetho skill only if Nico explicitly invoked
that skill too. Otherwise describe the useful next step without making its
invocation a prerequisite for completing already authorized work.

Read AGENTS.md, the manual-test section of
Development/system/process/README.md, Development/system/testing/manual/README.md
and the relevant requirement/design and existing procedure. Paths are relative
to the repository root. Reuse the current procedure where suitable.

## Prepare a procedure

Derive observable pass criteria from an identified basis. If a criterion,
reference or setup input is unresolved, identify the missing decision rather
than inventing it. Keep system requirement verification separate from final
acceptance, which exercises the documented startup-to-FHIR user workflow.

Store reusable procedures under Development/system/testing/<COMPONENT>/ or
testing/system/. Each is one short Markdown or HTML document containing:

- Test ID, title and requirement/design links.
- One device/software/setup identity field.
- Required preconditions and equipment.
- Numbered actions with observable pass criteria in the action text; each
  step has Pass / Fail / Blocked / Not run and one note field.
- Overall outcome, date and the executor's name below the results.

Use publish-page if Nico requests a viewable procedure. Preserve a durable
local copy: Pages is a review surface, not the sole signed-record archive.

## Record execution faithfully

Prepare a run copy under testing/manual/runs/<date>-<test-id>-<device>.md or
.html. Identify device, firmware/build, full source and procedure commits,
setup and configuration. Leave unexecuted steps Not run and signature empty.
The developer executes and signs; do not enter the executor's name on their
behalf. Transcribe supplied observations without inventing execution or outcome.

Keep failures, blocked steps, deviations and evidence links visible. Overall
Pass requires all required steps to pass. A rerun retains the earlier failed
record and identifies its own firmware and setup. Keep secrets and patient data
out of evidence. Optional JSON validation checks only that export, not execution
or the signed Markdown/HTML record.

Preparing a procedure does not authorize flashing, serial or device-network
access. Use existing explicit owner authorization where it covers the action;
otherwise obtain it before device operations. Use embedded-debugging for faults
or hardware-bring-up for board checks rather than expanding this procedure.

Deliver procedure/test changes through stetho-verify and the requested global
delivery skill. Component runs accompany their matching GitLab reviews through
stetho-handoff. Signed FINAL-01 and SYS-P22 runs receive internal developer
review in a GitHub Tests PR. Report pending execution and signatures explicitly.
