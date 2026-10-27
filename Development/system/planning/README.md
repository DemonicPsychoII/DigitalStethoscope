# Planning and decisions

## Current baseline

This table is the single place that names the decision in force for each topic.
Other documents link here instead of naming the latest decision date.

| Topic | Current decision | Applied in |
|---|---|---|
| MVP scope and session behaviour | [11 October](mvp-decisions-2026-10-11.md), scope reduced on [14 October](mvp-decisions-2026-10-14.md) | [Product scope](../spec/product-scope.md), [detailed design](../design/system/interfaces-and-behavior.md#mvp-session-baseline) |
| System requirements | [14 October](mvp-decisions-2026-10-14.md), changed on [15 October](mvp-decisions-2026-10-15.md) and [16 October](mvp-decisions-2026-10-16.md) | [System requirements](../requirements/system-requirements.md) |
| Firmware layer structure | [13 October](mvp-decisions-2026-10-13.md) | [Application README](../coding/app/README.md), [detailed design](../design/system/interfaces-and-behavior.md#firmware-layer-structure) |
| FHIR delivery, Device and patient link | [12 October](mvp-decisions-2026-10-12.md) write contract, [15 October](mvp-decisions-2026-10-15.md) Device registration without readback, [16 October record with 27 October clarification](mvp-decisions-2026-10-16.md): reuse only the patient reference supplied with a server-requested examination, otherwise omit it | Applied in [detailed design](../design/system/interfaces-and-behavior.md#delivery-clock-and-configuration), [parameters](../design/system/parameters.md) and [REQ-09](../requirements/system-requirements.md). The server-request mechanism remains an open integration design input |
| Wi-Fi setup, portal and recovery | [19 October](mvp-decisions-2026-10-19.md); [18 October](mvp-decisions-2026-10-18.md) is the discussion record | [Detailed design](../design/COMMUNICATION/interfaces-and-behavior.md#wi-fi-setup-and-recovery), [Wi-Fi views](../architecture/README.md) |
| LED and error feedback | [19 October](mvp-decisions-2026-10-19.md) catalogue | [Detailed design](../design/FEEDBACK/catalogue.md), [LED standards](../design/FEEDBACK/led-indication-standards.md) |
| Schedule | [14 October](mvp-decisions-2026-10-14.md); Jira holds current dates | [Implementation timeline](mvp-implementation-timeline.md) |

## Decision log

| Date | Record | Content |
|---|---|---|
| 11 October | [mvp-decisions-2026-10-11.md](mvp-decisions-2026-10-11.md) | MVP scope, session behaviour, BPM acceptance and latency proposals |
| 12 October | [mvp-decisions-2026-10-12.md](mvp-decisions-2026-10-12.md) | Hotspot portal, patient assignment, FHIR write contract |
| 13 October | [mvp-decisions-2026-10-13.md](mvp-decisions-2026-10-13.md) | Firmware layer structure |
| 14 October | [mvp-decisions-2026-10-14.md](mvp-decisions-2026-10-14.md) | 14 device-testable requirements from REQ-01, scope, schedule |
| 15 October | [mvp-decisions-2026-10-15.md](mvp-decisions-2026-10-15.md) | No patient selection on the device, Device registration, no readback; REQ-09/REQ-12 changed, REQ-15 added |
| 16 October | [mvp-decisions-2026-10-16.md](mvp-decisions-2026-10-16.md) | LED indication, single error type, patient pass-through; REQ-09/REQ-13 changed |
| 18 October | [mvp-decisions-2026-10-18.md](mvp-decisions-2026-10-18.md) | Wi-Fi and portal discussion record |
| 19 October | [mvp-decisions-2026-10-19.md](mvp-decisions-2026-10-19.md) | Wi-Fi, portal and feedback resolutions |

## Recording a new decision

1. Add a dated `mvp-decisions-<date>.md` and a row in the decision log.
2. Update the current-baseline row for each affected topic.
3. Change the content of the documents in "Applied in". Do not add change notes,
   decision dates in headings or "current decision" banners there; the log and
   Git history keep that record.
4. Leave earlier decision records unchanged; their banner points here.

Other planning records: [implementation readiness](implementation-readiness.md),
[implementation timeline](mvp-implementation-timeline.md) and
[framework and transport evaluation](framework-and-transport-evaluation.md).


[MVP security risk acceptance and known limitation](security-risk-acceptance.md) records the owner decision and post-MVP TICKET-198/199 follow-up.
