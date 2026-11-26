# FHIR and server communication architecture

## Basis and scope

Server communication refines the [system software allocation](../system/firmware-structure.md#static-dependency-and-module-map) for Device registration, examination context, FHIR serialization and result delivery under [REQ-02](../../requirements/system-requirements.md#req-02), [REQ-07](../../requirements/system-requirements.md#req-07), [REQ-08](../../requirements/system-requirements.md#req-08), [REQ-09](../../requirements/system-requirements.md#req-09), [REQ-10](../../requirements/system-requirements.md#req-10), [REQ-11](../../requirements/system-requirements.md#req-11), [REQ-13](../../requirements/system-requirements.md#req-13) and [REQ-15](../../requirements/system-requirements.md#req-15).

The device reuses a patient reference only when supplied with a server-requested examination, and omits it otherwise. Only the device starts measurements; the server cannot start an examination.

## Responsibilities and dependencies

| Owner | Responsibility | Boundary |
| --- | --- | --- |
| External examination workflow | Request an examination and optionally supply its patient reference. | Outside the device boundary. |
| Examination-request adapter (within L2_COMMUNICATION) | Translate external examination requests into examination context for L2_CONTROL. | Logical boundary inside L2_COMMUNICATION; does not start measurements. |
| L2_CONTROL | Own admitted examination/session context and freeze it with the completed measurement; grant the network lease and consume delivery outcomes. | External requests do not directly mutate measurement state or bypass listening admission. |
| L2_AUDIO | Produce the completed valid/invalid measurement and interval under L2_CONTROL's context. | No server calls or patient lookup. |
| L2_COMMUNICATION | Coordinate registration readiness, persistence, message construction, delivery and bounded retries. | Reuse the frozen context/body/identity across attempts; report outcomes rather than mutate controller state. |
| L1_FHIR | Pure-C serialization of the FHIR messages from supplied context. | No sockets, patient selection, clock synchronization or persistence. |
| L1_WIFI | Execute secure transport and return operation outcomes. | No FHIR workflow or application retries. |
| L1_STORAGE | Persist and retrieve the named server registration record. | Not a persistent measurement queue or patient directory. |
| External FHIR server | Hold Device and Observation resources and return application receipts. | Separate from the examination-request protocol. |

Dependencies run from L2_CONTROL's frozen job to L2_COMMUNICATION, and from L2_COMMUNICATION to L1_FHIR serialization, L1_WIFI transport and L1_STORAGE persistence. Transport depends on clock and trust preparation. A receipt returns through L2_COMMUNICATION to L2_CONTROL. Examination context enters through the adapter boundary and L2_CONTROL admission before being frozen into the measurement session. Neither L1_FHIR, L1_WIFI nor L1_STORAGE owns the complete workflow.

## Preparation and readiness flow

While Idle, L2_COMMUNICATION prepares verified transport automatically after joining the configured network. Each setup starts with one time synchronization directly before the TLS handshake and then proceeds to Device registration. L2_COMMUNICATION tracks network access, verified transport and Device registration independently. A retained TLS connection alone does not establish complete readiness. Time comes from unauthenticated SNTP, and transport uses TLS 1.3 only.

L2_COMMUNICATION reuses an available verified connection under the [connection policy](secure-transport.md#connection-policy). A lost connection is restored within the delivery budget once L2_CONTROL submits the finalized job after listening stops.

Standalone listening and measurement work without a server-requested examination. A deliverable valid result references this Device and omits the patient reference when none was supplied. External request authenticity and authorization sit at L2_COMMUNICATION's secure intake boundary, and L2_CONTROL owns context admission. When L2_CONTROL accepts a local measurement Start, it consumes any pending examination context and freezes it for the session without replacement. Server context never authorizes remote measurement start.

## Registration and message ownership

Registration and result delivery are distinct responsibilities. After verified transport preparation while Idle, L2_COMMUNICATION reuses a stored Device identifier or coordinates first registration and persistence of the server-assigned identifier under [REQ-15](../../requirements/system-requirements.md#req-15). Registration failure preserves offline listening. L2_COMMUNICATION owns recovery when registration, receipt handling or persistence fails.

FHIR message construction covers three message types: Device registration, a valid completed measurement Observation, and an error report for an invalid BPM measurement under [REQ-08](../../requirements/system-requirements.md#req-08). An invalid measurement produces an error report without a numeric BPM value.

The device never selects, looks up or adds a patient identifier. Only a patient reference supplied with the matching examination enters the result, and its absence means omission. Logs never expose patient context.

## Delivery boundary

L2_COMMUNICATION retains the immutable completed result, measurement-end timestamp and conditional-create identity across retries. L2_COMMUNICATION owns the bounded delivery job and evaluates the server receipt without readback, while L1_FHIR serialization and L1_WIFI transport are subordinate operations. Conditional create follows HL7 FHIR R4 [1].

The successful server receipt completes the device's delivery responsibility; later patient assignment and clinical processing remain outside it. Terminal delivery failure follows [REQ-10](../../requirements/system-requirements.md#req-10): the result is discarded without a later retry queue, including after connection/server recovery. Connection retention does not add background resend. A result keeps its identity. A missing prerequisite ends the delivery with a fault.

Active preparation, external-request communication and result delivery require L2_CONTROL's network lease outside listening. The examination-request adapter operates strictly within that lease boundary and performs no polling or push handling during listening.

## Verification allocation

| Scenario | Trace | Expected outcome |
| --- | --- | --- |
| Registration and three restarts | [REQ-15](../../requirements/system-requirements.md#req-15); VT-15 | Persisted Device identity is reused; results reference it. |
| Idle preparation and failed registration | [REQ-02](../../requirements/system-requirements.md#req-02)/[REQ-11](../../requirements/system-requirements.md#req-11)/[REQ-13](../../requirements/system-requirements.md#req-13)/[REQ-15](../../requirements/system-requirements.md#req-15); VT-08/VT-09/VT-15 | Ordered preparation with distinct readiness; registration failure leaves offline listening available. |
| Examination with/without supplied patient reference | [REQ-09](../../requirements/system-requirements.md#req-09); VT-07 | Only the matching supplied reference is passed through; otherwise subject is absent. |
| Write committed but receipt lost | [REQ-09](../../requirements/system-requirements.md#req-09)/[REQ-10](../../requirements/system-requirements.md#req-10); VT-07 | Identical conditional-create identity/body on retry; one Observation. |
| Short session or invalid BPM | [REQ-07](../../requirements/system-requirements.md#req-07)/[REQ-08](../../requirements/system-requirements.md#req-08); VT-06/VT-07 | Short session sends nothing; invalid measurement sends an error report with no numeric result. |
| Terminal failure and later recovery | [REQ-10](../../requirements/system-requirements.md#req-10)/[REQ-13](../../requirements/system-requirements.md#req-13); VT-07/VT-09 | Visible failure, released job, no delayed resend. |
| Network work while listening and private context | [REQ-11](../../requirements/system-requirements.md#req-11)/[REQ-13](../../requirements/system-requirements.md#req-13); VT-08/VT-11 | Lease prevents active jobs; no secrets/patient data in logs. |

## Sources

[1] Health Level Seven International, *FHIR Release 4 (v4.0.1): RESTful API, Conditional create*, FHIR specification, 2019, <https://hl7.org/fhir/R4/http.html#ccreate>. Accessed 23 October 2026.
