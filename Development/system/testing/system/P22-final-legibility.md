# P22 — one-time final indication and legibility acceptance

Proposed procedure, deferred pending resolution of the P22 verification conflict. The 19 October owner decision plans no MVP visibility checks; this draft does not add a required MVP acceptance step. See the [recorded conflict](../../design/FEEDBACK/parameters.md). If adopted later, execution and sign-off belong to Nico on the final assembled system baseline. Repeat affected observations if the indication hardware,
enclosure, brightness, timing or catalogue changes afterward. This is a project
acceptance check, not a standards-conformity claim.

Basis: [P22](../../design/FEEDBACK/parameters.md#feedback-parameters), the
[indication and error catalogue](../../design/FEEDBACK/catalogue.md)
and the [system acceptance case](../specification-verification.md#system-acceptance).
The distances and conditions below are the project's specified acceptance values;
primary IEC applicability and clause verification remain open (TICKET-210) in the
[source assessment](../../design/FEEDBACK/led-indication-standards.md).

## Device and software

Record device/board/indication assembly, firmware boot build ID and full SHA,
procedure SHA, configuration, operator, date, lux-meter identity, distances and
viewing geometry in an [executed-run record](../manual/README.md). Keep the
procedure and signed run together. No run has been executed by this procedure's author.

## Preconditions

- The complete device implements the final catalogue and permits each specified
  pattern and error to be induced safely. Record the actual injection method;
  if a state cannot be induced, mark its step blocked.
- A tape measure and lux meter establish 1 m and 4 m observer distances and
  100 lx and 1500 lx ambient illumination at the indicator. Record actual readings
  and deviations. Do not substitute camera visibility for Nico's observation.
- Set viewing directions on-axis and at the edge of the specified 30° cone.
  Record the actual geometry so an ambiguous cone interpretation is visible in
  the evidence. Use the intended final indicator placement and normal viewing conditions.
- Prepare a reference list of every normal, activity, Busy, rejected-input,
  success, warning and error pattern plus every error code, context and priority
  from the identified catalogue. No omitted or unimplemented catalogue entry passes.

## Execution

1. Record the powered device's build identity and perform the startup lamp test.
   Pass if it matches the run's firmware identity and the specified startup pattern
   is visible. Record observed duration and any dark or failed indicator.
2. At **1 m**, induce each pattern in the reference list at both ambient-light
   endpoints and each prepared viewing direction. Create one run step per
   pattern/condition. Pass if Nico sees that pattern and distinguishes its indicated
   operating state. Record the injected and perceived pattern, lux, direction,
   distance and observation. Pattern visibility alone does not pass code identification.
3. At **1 m**, induce each specific error code and priority in the catalogue in
   the same light/direction matrix. Keep the injected identity hidden until Nico
   states the code, context and priority from the indicator. Pass each observation
   only if the stated code, context and priority all match the injected catalogue entry.
   Record expected and identified values separately; a visible but unreadable code fails.
4. At **4 m**, repeat the error-state matrix. Pass each observation if Nico
   recognizes that an error is active. Record visibility separately from the
   one-metre code/priority result; correct code naming at 4 m is not required.
5. Compare every matrix observation with its own criterion. Mark missing,
   ambiguous or unperformed observations blocked or failed as appropriate.
   Link evidence and deviations; never infer a pass for one distance or condition
   from another.

## Completion

Overall pass requires all required observations to pass. Nico dates and signs the
run using the manual record format. A failure returns to the affected indication
design/implementation and is retested on an identified new baseline.

Created by GPT-6.1-Sol on behalf of Nico running in codex.
