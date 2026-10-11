# Product scope and specification basis

## Goal and boundary

Develop an ESP32-S3 digital stethoscope research prototype: acquire the reused chestpiece's
INMP441 signal, provide selectable listening filters and headphone output, determine heart
rate from original-rate audio, replay a bounded recording more slowly, and send a completed
heart-rate result to a local FHIR server over validated TLS. Compare filter variants on identical
licensed recordings against a defined reference. Filter superiority is a research question,
not an assumed product property. Listening and measurement are independent workflows.

The device boundary includes chestpiece coupling, microphone, MCU, controls, display/touch,
removable fixture storage, DAC and external headphone amplifier. The listener, signal source,
evaluation computer, network/time services and FHIR server are external actors/services.

Lung mode provides Raw live listening at 1× only. It excludes BPM, replay and FHIR sending.
The prototype excludes diagnosis, ML classification, durable patient audio storage, enclosure
development and proof of clinical benefit or regulatory conformity. The latest submitted thesis
description excludes measurement of the acoustic transfer chain; older boards propose it.
SD files are licensed test inputs, not a new patient-recording persistence feature.

## Source register and precedence

| ID | Source | Use and limitation |
|---|---|---|
| S01 | System Architecture Digital Stethoscope; snapshot in `architecture/sources/` | Context, chosen parts, electrical interfaces; retains historical alternatives and open storage/audio-stream ideas. |
| S02 | Software-Architecture and Requirements; same snapshot folder | Original listening and BPM workflows; 3 s window and 15/30/? s aggregation are unresolved sketches. |
| S03 | Software Architecture — Parallel Audio and Complete Flows; same folder | Detailed working proposal, ownership, fault paths, timing and interface candidates. |
| S04 | Software Architecture — Options and Decision; same folder | Latest explicit architecture decisions; controller ownership, Zephyr, k_msgq, MON, single-core first, network outside live listening. |
| S05 | [Latest submission description](../../../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Abgabe.md) | Current thesis scope and 320 h overall estimate. |
| S06 | [Internal description](../../../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md) and [decision notes](../../../preThesis/02-entscheidungen/open-questions.md) | Prior parameter candidates and rationale; older ESP-IDF preference is superseded by S04. |
| S07 | [Evaluation README](../coding/bringup-zephyr/README.md) and [devicetree overlay](../coding/bringup-zephyr/boards/esp32s3_devkitc_procpu.overlay) | Wiring baseline and implemented evaluation behavior, not acceptance of thesis behavior. |
| S08 | SW-Basis teaching material: ZumoRobot and SWBasisDoc | Process example only: use-case derivation, agreement, interfaces, review and requirement-linked evidence. |

This draft uses S04 for resolved software decisions, S07 for concrete pin assignments, and S05
for current thesis scope. It preserves conflicts in [the decision register](../planning/implementation-readiness.md)
rather than treating every older board statement as a requirement. The saved decisions are the
drafting basis; remaining choices are open. Neither source
provenance nor a readable presentation constitutes approval of requirement thresholds or
release of an implementation baseline.

## Terminology

| Term | Meaning |
|---|---|
| Raw | No listening band filter; sample normalization, gain and output saturation still apply. |
| Listening filter | Operator-selected Raw / Murmur / BPM emphasis applied to audible output. |
| Analysis filter | Independently selected processing for BPM; never silently follows the listening switch. |
| Recording / clip | Bounded volatile raw audio for replay; not a completed BPM result. |
| Measurement session | Bounded original-rate interval aggregated into one frozen result with a unique identifier. |
| Ready | Essential audio capability initialized; physical operation still needs target evidence. |
| Idle / stopped | No live microphone listening or replay; output muted; eligible for network work. |
| Live | Microphone blocks routed to listening output at 1×. |
| Valid BPM | Estimator and coverage criteria met; neither clinical confidence nor diagnosis. |
| Source | Microphone, synthetic tone/heartbeat or licensed fixture; provenance follows all derived data. |
| Listening point | Operator-entered anatomical label; device does not infer location. |
| MON | Cross-cutting software monitoring and risk controls, not an additional architecture layer. |

IEC 62304 class B and Zephyr as SOUP are recorded architecture intentions from S04. Classification,
hazard analysis and the applicability of standards require separate substantiation; this package
is not a compliance certificate. Candidate risks and controls are listed in the readiness plan.

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
