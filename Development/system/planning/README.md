# Planning and decisions

## Current baseline

This table is the single place that names the decision in force for each topic.
Other documents link here instead of naming the latest decision date.

| Topic | Current decision | Applied in |
|---|---|---|
| MVP scope and session behaviour | [11 October](mvp-decisions-2026-10-11.md), scope reduced on [14 October](mvp-decisions-2026-10-14.md); [13 November](mvp-decisions-2026-11-13-delivery-and-filters.md): Start during sending cancels the delivery, filter roles | [Product scope](../spec/product-scope.md), [detailed design](../design/system/interfaces-and-behavior.md#mvp-session-baseline) |
| System requirements | [14 October](mvp-decisions-2026-10-14.md), changed on [15 October](mvp-decisions-2026-10-15.md) and [16 October](mvp-decisions-2026-10-16.md) | [System requirements](../requirements/system-requirements.md) |
| Firmware layer structure | [13 October](mvp-decisions-2026-10-13.md) | [Application README](../coding/app/README.md), [detailed design](../design/system/interfaces-and-behavior.md#firmware-layer-structure) |
| FHIR delivery, Device and patient link | [12 October](mvp-decisions-2026-10-12.md) write contract, [15 October](mvp-decisions-2026-10-15.md) Device registration without readback, [16 October record with 27 October clarification](mvp-decisions-2026-10-16.md): reuse only the patient reference supplied with a server-requested examination, otherwise omit it; [2 November](mvp-decisions-2026-11-02.md): one server from the server profile, newest pending examination request wins | Applied in [detailed design](../design/system/interfaces-and-behavior.md#delivery-clock-and-configuration), [server communication](../design/COMMUNICATION/server-communication.md), [parameters](../design/system/parameters.md) and [REQ-09](../requirements/system-requirements.md). The external request adapter remains an open integration design input |
| Time synchronization and secure transport | [2 November](mvp-decisions-2026-11-02.md): SNTP inside every TLS setup, computed 12.5 h mapping limit, separate image for URL and certificate; [5 November](mvp-decisions-2026-11-05.md): named server profile; [13 November](mvp-decisions-2026-11-13-delivery-and-filters.md): delivery setup at job submission, result freeze points, seven cleanup services | [SNTP design](../design/COMMUNICATION/time-synchronization.md), [TLS design](../design/COMMUNICATION/secure-transport.md), [flash layout](../design/STORAGE/interfaces-and-behavior.md#flash-layout), [server profile](../design/STORAGE/server-profile.md) |
| Wi-Fi setup, portal and recovery | [19 October](mvp-decisions-2026-10-19.md); [18 October](mvp-decisions-2026-10-18.md) is the discussion record; hotspot name [2 November](mvp-decisions-2026-11-02.md) | [Detailed design](../design/COMMUNICATION/interfaces-and-behavior.md#wi-fi-setup-and-recovery), [Wi-Fi views](../architecture/README.md) |
| LED and error feedback | [19 October](mvp-decisions-2026-10-19.md) catalogue; [2 November](mvp-decisions-2026-11-02.md) removes the time-synchronization error; [10 November](mvp-decisions-2026-11-10.md): status light on GPIO48, fixed volume until the potentiometer is fitted, rows grouped by subject with unchanged blink codes | [Detailed design](../design/FEEDBACK/catalogue.md), [LED standards](../design/FEEDBACK/led-indication-standards.md) |
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
| 2 November | [mvp-decisions-2026-11-02.md](mvp-decisions-2026-11-02.md) | Review of time, TLS and FHIR design: SNTP in TLS setup, drift calculation, provisioning image, flash layout, hotspot name, newest request wins |
| 5 November | [mvp-decisions-2026-11-05.md](mvp-decisions-2026-11-05.md) | Provisioning image renamed to server profile, apart from Wi-Fi provisioning; on-flash format unchanged |
| 10 November | [mvp-decisions-2026-11-10.md](mvp-decisions-2026-11-10.md) | First fitted evaluation carrier: RGB status light on GPIO48, fixed 100 % volume until J7 is fitted; catalogue rows grouped by subject, blink codes unchanged |
| 13 November | [mvp-decisions-2026-11-13-delivery-and-filters.md](mvp-decisions-2026-11-13-delivery-and-filters.md) | Start during sending cancels the delivery; delivery connection setup at job submission; seven cleanup services; result freeze points; filter roles; first short press acknowledges, errors during listening shown after Stop, audio errors halt all input |

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
