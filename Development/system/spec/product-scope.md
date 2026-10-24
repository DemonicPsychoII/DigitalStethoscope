# Product scope and specification basis

Current owner decisions: 14 October, 12 October and 11 October; newer records supersede older ones. Older source snapshots and evaluation behavior remain historical evidence.

## Goal and boundary

Develop an ESP32-S3 digital stethoscope research prototype: acquire the reused chestpiece's
INMP441 signal, provide selectable listening filters and headphone output, determine heart
rate from original-rate audio, and send a completed
heart-rate result to a local FHIR server over validated TLS. Compare filter variants on identical
licensed recordings against a defined reference. Filter superiority is a research question,
not an assumed product property. Listening and measurement are independent workflows.

The MVP device boundary includes chestpiece coupling, microphone, MCU, physical controls
and the DAC line output; the headphone amplifier is outside the project scope (14 October). Display, touch, SD-card fixture storage and bounded
capture / slower replay are optional extensions beyond the MVP, per the 2026-10-07 feedback.
Existing requirements and evaluation code for these features describe extension behavior;
their presence does not make them MVP acceptance criteria. The listener, signal source,
evaluation computer, network/time services and FHIR server are external actors/services.

The MVP is Heart only. Lung mode is optional and needs the display (14 October).
The prototype excludes diagnosis, ML classification, durable patient audio storage, enclosure
development and proof of clinical benefit or regulatory conformity. The latest submitted thesis
description excludes measurement of the acoustic transfer chain; older boards propose it.
SD files are licensed test inputs, not a new patient-recording persistence feature.

## Source register and precedence

| ID | Source | Use and limitation |
|---|---|---|
| S01 | System Architecture Digital Stethoscope; snapshot in `architecture/system/sources/` | Context, chosen parts, electrical interfaces; retains historical alternatives and open storage/audio-stream ideas. |
| S02 | Software-Architecture and Requirements; same snapshot folder | Original listening and BPM workflows; 3 s window and 15/30/? s aggregation are unresolved sketches. |
| S03 | Software Architecture — Parallel Audio and Complete Flows; same folder | Detailed working proposal, ownership, fault paths, timing and interface candidates. |
| S04 | Software Architecture — Options and Decision; same folder | Latest explicit architecture decisions; controller ownership, Zephyr, k_msgq, MON, single-core first, network outside live listening. |
| S05 | [Latest submission description](../../../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Abgabe.md) | Current thesis scope and 320 h overall estimate. |
| S06 | [Internal description](../../../preThesis/01-aufgabenbeschreibung/Aufgabenbeschreibung-Intern.md) and [decision notes](../../../preThesis/02-entscheidungen/open-questions.md) | Prior parameter candidates and rationale; older ESP-IDF preference is superseded by S04. |
| S07 | DemonicPsychoII (repository owner; individual file authorship unverified), DigitalStethoscope evaluation README and devicetree overlay, GitHub repository revision `1448340d265326e11b7a416960f35e0d2390cd6d`, 2026: [README](https://github.com/DemonicPsychoII/DigitalStethoscope/blob/1448340d265326e11b7a416960f35e0d2390cd6d/Development/system/coding/bringup-zephyr/README.md), [overlay](https://github.com/DemonicPsychoII/DigitalStethoscope/blob/1448340d265326e11b7a416960f35e0d2390cd6d/Development/system/coding/bringup-zephyr/boards/esp32s3_devkitc_procpu.overlay) (accessed 2026-10-23) | Historical pre-thesis evaluation material. Source for the proposed pin assignments below; not the application wiring definition or acceptance of thesis behavior. |
| S08 | SW-Basis teaching material: ZumoRobot and SWBasisDoc | Process example only: use-case derivation, agreement, interfaces, review and requirement-linked evidence. |

This draft uses S04 for resolved software decisions, the electrical baseline below for application pin assignments, and S05
for current thesis scope. It preserves conflicts in the decision register
rather than treating every older board statement as a requirement. The saved decisions are the
drafting basis; remaining choices are open. Neither source
provenance nor a readable presentation constitutes approval of requirement thresholds or
release of an implementation baseline.

## Electrical interface baseline

These are project assignments for the application, derived from the pre-thesis
evaluation material S07. They define planned wiring; they do not claim that the
application drivers or physical acceptance are complete.

| Interface | Direction at ESP32-S3 | Planned assignment |
|---|---|---|
| INMP441 audio | Clock/word-select output; sample input | I2S (Inter-IC Sound) controller `i2s0`: clock GPIO4, word select GPIO5, data GPIO6 |
| PCM5102A audio | Clock, word-select and sample output | Controller `i2s1`: clock GPIO40, word select GPIO41, data GPIO42; device boundary at DAC (digital-to-analog converter) line output |
| Start/Stop | GPIO (general-purpose input/output) input | GPIO16, active low with pull-up; button closes to ground |
| Raw/Murmur/BPM selection | GPIO inputs | GPIO18/21/38 respectively, active low with pull-ups; switch common to ground |
| Volume | ADC (analog-to-digital converter) input | GPIO1, ADC1 channel 0, potentiometer wiper |
| Button LED (light-emitting diode) | GPIO output | GPIO17, active high; retain current limiting |

Confirm the fitted carrier and DevKit revision before enabling peripherals. The
GPIO38/RGB-LED conflict remains an open board check; it is not resolved by this
assignment. Display, touch, SD storage, backlight and the speed switch are outside
this application baseline. The headphone amplifier remains external. The memory-only
application overlay is an implementation placeholder, not a wiring source.

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

Working assumption (19 October): the device is designed as if it were ME (medical electrical) equipment
under IEC 60601-1, with the chestpiece as applied part, as comparable electronic stethoscopes are. Errors
are treated as technical alarm conditions with priorities under IEC 60601-1-8. This is a project
decision that guides the later design stage. Applicability, sources and deviations need a separate
assessment; this assumption is not a conformity claim.
