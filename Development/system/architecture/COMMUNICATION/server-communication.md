# FHIR and server communication architecture

## Basis and scope

This Architecture-stage proposal refines the [system software allocation](../system/software-components.puml) for REQ-07/08/09/10/11/13/15. The [current decision baseline](../../planning/README.md#current-baseline) identifies accepted decisions; the [shared delivery design](../../design/system/interfaces-and-behavior.md#delivery-clock-and-configuration) records existing contracts. This page allocates responsibilities and dependencies without defining new message fields, protocol flows or firmware interfaces.

The patient rule is accepted: reuse only a patient reference supplied with a server-requested examination; otherwise omit it. The external examination-request adapter remains unspecified. Its existence as an architectural boundary does not approve polling, a push channel, a Device.patient lookup, or remote Start/Stop behavior. The additional allocation below is proposed, not accepted implementation behavior.

## Responsibilities and dependencies

| Owner | Responsibility | Boundary |
| --- | --- | --- |
| External examination workflow | Request an examination and optionally supply its patient reference. | Outside the device; protocol, authorization and availability semantics remain open. |
| Examination-request adapter, logical boundary within COMMUNICATION | Translate the eventual external protocol into examination context for CONTROL. | No selected protocol, new firmware module or independent worker is implied. |
| L2_CONTROL | Own admitted examination/session context and freeze it with the completed measurement; grant the network lease and consume delivery outcomes. | External requests do not directly mutate measurement state or bypass listening admission. |
| L2_AUDIO | Produce the completed valid/invalid measurement and interval under CONTROL's context. | No server calls or patient lookup. |
| L2_COMMUNICATION | Coordinate registration readiness, persistence, message construction, delivery and bounded retries. | Reuse the frozen context/body/identity across attempts; report outcomes rather than mutate controller state. |
| L1_FHIR | Pure-C serialization of the agreed FHIR messages from supplied context. | No sockets, patient selection, clock synchronization or persistence. |
| L1_WIFI | Execute secure transport and return operation outcomes. | No FHIR workflow or application retries. |
| L1_STORAGE | Persist/retrieve the named server registration record under the future agreed contract. | Not a persistent measurement queue; not a patient directory. |
| External FHIR server | Hold Device and Observation resources and return application receipts. | Separate from the examination-request protocol, even if one deployment hosts both. |

Dependencies run from CONTROL's frozen job to COMMUNICATION, then to FHIR serialization, WIFI transport and STORAGE operations. Transport depends on approved clock/trust preparation. A receipt returns through COMMUNICATION to CONTROL. Examination context enters through the adapter boundary and CONTROL admission before being frozen for the corresponding result. No lower service owns the complete workflow.

## Registration and message ownership

Registration and result delivery are distinct responsibilities. COMMUNICATION coordinates first registration and persistence of the server-assigned Device identifier, then reuses it after restart under REQ-15. Recovery from a server-side deletion, registration committed before a lost receipt, or persistence failure must be resolved in Design; this proposal does not claim duplicate-free registration is already specified.

FHIR message construction has three concerns: Device registration, a valid completed measurement Observation, and the error report required for invalid BPM. Their concrete schemas/profile claims, coding and parsing contracts belong to Design. In particular, REQ-08's error report remains an unresolved contract; the device must not manufacture a numeric result for an invalid measurement.

The device neither selects nor adds a patient identifier. Only the examination-supplied reference may enter the matching result; absence means omission. A Device.patient lookup is not an approved substitute. Design must settle context admission, correlation, lifetime and replacement/cancellation semantics before implementation. Logs must not expose patient context.

## Delivery boundary

Retain the agreed immutable completed result, measurement-end timestamp and conditional-create identity across retries. COMMUNICATION owns the bounded delivery job and interprets the existing success receipt; FHIR serialization and transport remain subordinate operations. The conditional-create basis is HL7 FHIR R4 [1]; the project's receipt, no-readback and retry policies are recorded in the shared design.

Terminal delivery failure follows REQ-10: discard the result without a later retry queue. No automatic reassignment or identity regeneration occurs. Missing prerequisites are reported through the existing failure boundary rather than silently extending delivery or redefining Wi-Fi setup success.

Active preparation, external-request communication and delivery require CONTROL's network lease outside listening. The examination adapter's eventual protocol must fit that boundary; it cannot introduce always-active polling or push handling during listening without revisiting the architecture. Operator Start/Stop semantics remain unchanged by this proposal.

## Verification allocation and open inputs

| Scenario | Trace | Expected outcome |
| --- | --- | --- |
| Registration and three restarts | REQ-15; VT-15 | Persisted Device identity is reused; results reference it. |
| Examination with/without supplied patient reference | REQ-09; VT-07 | Only the matching supplied reference is passed through; otherwise subject is absent. Adapter fixture awaits Design. |
| Write committed but receipt lost | REQ-09/REQ-10; VT-07 | Identical conditional-create identity/body on retry; one Observation. |
| Short session or invalid BPM | REQ-07/REQ-08; VT-06/VT-07 | Short session sends nothing; invalid measurement sends no numeric result and uses the separately agreed error contract. |
| Terminal failure and later recovery | REQ-10/REQ-13; VT-07/VT-09 | Visible failure, released job, no delayed resend. |
| Network work while listening and private context | REQ-11/REQ-13; VT-08/VT-11 | Lease prevents active jobs; no secrets/patient data in logs. |

These are architecture expectations, not generated tests or execution evidence. The [catalogue](../../testing/specification-verification.md) retains pending VT-07/08/15 coverage. Detailed design must settle the examination adapter contract, registration recovery/persistence, authorization, local message/profile mapping, error report, point coding and precision, clock acceptance and timestamp skew (TICKET-180/181/209). No unsupported profile-conformance claim is made.

## Sources and project decisions

[1] Health Level Seven International, *FHIR Release 4 (v4.0.1): RESTful API, Conditional create*, FHIR specification, 2019, <https://hl7.org/fhir/R4/http.html#ccreate>. Source verification/access recorded 23 October 2026 in the [source register](../../../../thesis-material/quellen.md#hl7_fhir_r4_conditional_create_2019); no new access claimed.

[2] Nico, *MVP decisions — Wi-Fi setup, registration and delivery*, DigitalStethoscope project record, 15 October 2026, [record](../../planning/mvp-decisions-2026-10-15.md); *MVP decisions — LED indication, single error type and patient pass-through*, 16 October 2026, with patient handling clarified 27 October 2026, [record and original conversation citation](../../planning/mvp-decisions-2026-10-16.md). Apply their [current-baseline precedence](../../planning/README.md#current-baseline), not superseded patient proposals. Requirements and shared design basis: repository revision `81c7b1a45f5b0ef45c939098e5a693773c8abb90`, 2026. These are project decisions, not evidence of implementation or target acceptance.
