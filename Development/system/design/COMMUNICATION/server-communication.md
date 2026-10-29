# Device registration, FHIR messages and examination context

## Basis and accepted decisions

This Design-stage contract refines [server-communication Architecture PR #81](https://github.com/DemonicPsychoII/DigitalStethoscope/pull/81), revision `eb0a2db8be47a160981eab15f9b939ad3b649ec3`, and requirements/shared design at `3d989815b4cbded9bf64ec7c9934894f95cc68e5`. Dependencies are [SNTP Design #99](https://github.com/DemonicPsychoII/DigitalStethoscope/pull/99), revision `1a1e35350bb1cffc3bdb5346bc53020343f28ca8`, and [TLS Design #100](https://github.com/DemonicPsychoII/DigitalStethoscope/pull/100), revision `b17e3d2c1a1a0dc9a80fd1d44e6fa9f166cb00d1`. These dependencies remain separate PRs; no firmware, server configuration or generated test changes are included here.

Nico accepted persistent server-bound registration, conditional recovery, full-MAC-derived physical identity, registration readiness only after flash save, ten-second registration attempts with 60-second Idle recovery, and connection reuse. He accepted one pending examination request, consumption/context freezing at local Start, no automatic patient-context reuse after cancellation/failure, standalone measurements without subject, and adaptation of PulsOxy JSON without unverified profile declarations [1]. Proposed interface names, record encoding and buffer limits below refine these decisions; they are not measured target guarantees. This covers REQ-02, REQ-07, REQ-08, REQ-09, REQ-10, REQ-11, REQ-12, REQ-13 and REQ-14; verification allocation is VT-07, VT-08, VT-09 and VT-11.

## Responsibilities and proposed interfaces

| Owner | Responsibility |
| --- | --- |
| CONTROL | Grant/revoke the network lease; accept local Start; consume and freeze examination context; finalize results and admit one delivery job. A server request never starts audio. |
| COMMUNICATION | Prepare registration, bind/cache identity, own deadlines/retries and failure episodes, invoke serialization, and send the frozen job through the verified transport. |
| L1_FHIR | Pure C bounded serialization and response parsing. No Wi-Fi, clocks, settings access, automatic registration, retries or mutable global examination state. |
| L1_WIFI | Provide stable physical identity and the verified transport, DNS/TCP/TLS/HTTP resource lifecycle, bounded completion and cancellation. A new socket does not imply a new Device registration. |
| L1_STORAGE | Read/write the complete named registration record. No server policy or retry decisions. |
| External request adapter | Supply validated, device-addressed examination context and consumption acknowledgement. External protocol and hosting remain unspecified. |

Proposed `fhir_buildDeviceRegistration` and `fhir_buildObservation` accept immutable input, caller buffer/capacity and return success plus byte length or a cause. They perform no network work. `fhir_parseDeviceRegistration` accepts bounded status/headers/body and the expected server binding, returning a validated server Device id or a cause. Never return truncated JSON, silently truncate an identifier or fall back to an unconditional POST. The WIFI HTTP service accepts method, configured relative resource path, headers, frozen bytes and the caller deadline; waits do not reset deadlines or retry. Its cancellation contract must quiesce callbacks/resources before audio, under the separate P23 one-second per-service stop bound. Detailed signatures belong to the later interface/L2 PR.

## Physical identity and server binding

The current hotspot name is `Stetho-XXXX`, built from the station interface's last two MAC bytes [2]. Keep that short display name. For registration use `stetho-AABBCCDDEEFF`: all six factory station MAC bytes in uppercase hexadecimal, no separators, with the lowercase project prefix. Obtain the stable factory station identity independently of any runtime override/randomization; later L1 acceptance must prove that source on the pinned board/driver. A failed identity read makes registration unavailable; never substitute all zeros or the short hotspot suffix. This identifier is not an authentication credential.

Use `Device.identifier.system = urn:stethoscope:device` and the physical identifier as its value. Keep this distinct from HAPI's logical `Device.id` [3,4]. Bind the saved logical id to the complete configured HTTPS FHIR base URL, including base path. At build time lowercase scheme/host, make the port explicit and remove the trailing slash; reject userinfo, query and fragment. Use the same canonical string everywhere. Host/path aliases and a changed base URL require conditional registration for that binding; DNS destination changes, Wi-Fi/SSID/password changes, reconnects and certificate renewal alone do not. A one-slot record is sufficient: returning to a previous server conditionally recovers its resource instead of requiring a multi-server registry.

## Registration record

Use the existing whole-record storage interface with key `fhir/device-registration`. Proposed version 1 encoding is 343 bytes: one version byte with value 1, 257 bytes for the canonical base URL, 20 for the physical identifier, and 65 for the server Device id, in that order. Strings are NUL-terminated, zero-padded UTF-8/ASCII arrays; reject overflow, missing terminators, unsupported version, incorrect physical identity or malformed fields. Do not persist a native C struct with compiler-dependent padding. Server Device ids match FHIR R4 `id`: 1–64 ASCII letters, digits, hyphen or full stop [4]. No patient reference, request context, credentials or certificate is part of this record.

Boot reads and validates the record once. A matching record supplies cached registration readiness without a registration POST or mandatory readback per measurement. This is cached application state, not proof the server still holds the resource. A missing, malformed or mismatched record requires conditional registration; a backend read failure leaves registration unavailable and raises the registration failure cause. Saving a new record must preserve the prior committed record on unsuccessful write under the existing STORAGE contract; atomicity and power-loss behavior remain target evidence, not established guarantees.

## Registration flow and recovery

1. While Idle, require station address, acceptable clock and verified TLS under the separate designs. These are prerequisites, not registration substeps repeated for every message.
2. With no eligible saved registration, acquire CONTROL's network lease and start one monotonic ten-second attempt. Reuse verified TLS where possible. Any required transport recovery, conditional POST, response parsing and flash commit share the remaining attempt budget. Do not invoke an independent ten-second TLS preparation inside it.
3. Send `POST /Device`, `Content-Type: application/fhir+json`, `Prefer: return=representation`, and `If-None-Exist: identifier=urn%3Astethoscope%3Adevice|stetho-AABBCCDDEEFF` for the example identity. Body:

   ```json
   {"resourceType":"Device","identifier":[{"system":"urn:stethoscope:device","value":"stetho-AABBCCDDEEFF"}],"status":"active"}
   ```

   Do not assign a logical resource id in the create body, invent manufacturer/model data or create a Patient. FHIR conditional create returns 201 for a new resource, 200 for one existing match and 412 for multiple matches [5]. This reuses the Observation conditional-create pattern; it does not require a separate search-then-create race.
4. On 201/200, obtain a valid logical Device id from a Device representation or Location header referring to the expected server/base and Device resource. Require agreement if both supply an id; reject another resource type/origin, malformed/truncated responses or missing identity. Parse any history suffix as version metadata, not part of the logical id. Representation identifiers, when present, must include the requested physical identifier. Do not treat HTTP success alone as saved registration.
5. Commit the complete record before publishing registration readiness. If saving fails, retain only a candidate in memory and retry its save during recovery in the same boot. After restart or uncertain creation/receipt, repeat conditional creation using the same physical identifier. Never generate a new identity to escape an error. A new server binding does not become ready using the old server's id.
6. On failed/interrupted issued preparation, retry no earlier than 60 seconds after completion, indefinitely while Idle and prerequisites permit. Missing prerequisites consume no attempt. Start cancels network preparation before audio; a pending settings commit must complete under its remaining bound before release. Late generations cannot save or publish registration for another binding. Lower services add no workflow retries.

Ambiguous multiple matches, unsupported conditional creation, authentication/configuration failure and invalid trust never trigger unconditional creation. Latch `DEVICE_REGISTRATION_FAILURE`, retain bounded/redacted cause information, and use the normal 60-second preparation recovery without per-retry alerts after acknowledgement. Acknowledgement clears only the indication, not readiness or retry scheduling; success restores readiness but does not acknowledge an existing latch. Registration-only faults preserve standalone listening. Failure to prove resource release follows existing cleanup/restart rules.

If an authoritative read or server diagnostic specifically establishes that the saved Device is absent, invalidate cached readiness and conditionally register again while Idle. A generic 404 from an Observation endpoint does not establish that a referenced Device is missing. There is no per-message existence query, background existence polling or automatic inference that an accepted Observation proves referential integrity. How the deployed server detects/reports missing references remains an integration check. Never change a frozen result's Device id or resend a previously failed result after reconciliation.

## Examination request boundary

While Idle, the adapter may offer at most one validated pending examination with a stable request identity, target device/server binding, and optional supplied patient reference. Reject wrong-target/binding, malformed or oversized context; a second pending offer returns Busy without overwriting the first. Duplicate delivery of the same logical request must not create a new examination. CONTROL consumes the pending offer only on an accepted local measurement Start and copies its request identity and patient reference into the session. A rejected Start consumes nothing. No pending request means standalone measurement with no subject.

Consumption removes the pending offer immediately. Cancellation, poor signal, delivery failure and acknowledgement never automatically restore it or apply its patient context to another session. Active-session context is immutable. New external context cannot replace it or start a measurement. Apply existing session-context-change handling if an attempted active-session mutation occurs. Do not perform adapter receive/fetch/acknowledgement network work while listening; local consumption may queue an adapter acknowledgement for the next permitted network lease. A request received later cannot be retroactively attached to an already started measurement.

The adapter contract must prevent consumed-request redelivery from becoming a new request, including after reconnect/restart, without this PR prescribing server status fields, persistent cursors or an acknowledgement endpoint. A fresh explicit examination needs its own logical identity. Local pending/session context is not persisted by the registration record. Request cancellation/expiry, external validation rules and replay/acknowledgement durability must be specified with the selected adapter before implementing external examination reception; no exactly-once claim is made here.

## Observation construction and delivery

Adapt PulsOxy's useful resource structure in C, not its registration lifecycle, Arduino dependencies, Patient creation, current-send-time timestamp or unconditional subject/profile fields [6]. Use a bounded JSON writer with proper escaping, finite-number checks, locale-independent numeric formatting and checked lengths. Serialize once after finalization/admission and retain the identical byte sequence for all retries. Registration and Observation rendering are separate operations.

| Field | Valid heart-rate result |
| --- | --- |
| `resourceType`, `status` | `Observation`, `final` |
| `identifier` | Existing `urn:stethoscope:measurement` plus frozen `<server-device-id>:<measurement-end-UTC>`; retain the shared uniqueness rule |
| `category` | Coding system `http://terminology.hl7.org/CodeSystem/observation-category`, code `vital-signs` |
| `code` | Coding system `http://loinc.org`, code `8867-4` (heart rate), per the existing baseline [7] |
| `effectiveDateTime` | Frozen measurement-end UTC, formatted `YYYY-MM-DDTHH:mm:ss.SSSZ`; never sampled during serialization/retry |
| `device.reference` | `Device/<frozen-server-device-id>` |
| `subject.reference` | Exact validated patient reference supplied by the attached examination; omit the entire subject when absent. No Patient lookup, creation or replacement. |
| `valueQuantity` | Frozen valid BPM numeric value using the result's declared precision; `unit` and `code` are `/min`, `system` is `http://unitsofmeasure.org`. Never invent a rounding/precision policy here. |
| `meta.profile` | Omitted until a specific profile is validated, including patient-less measurements. A vital-signs category alone is not a profile-conformance claim. |

FHIR R4 Observation fields are defined in [8]. Keep interval, analysis configuration, request identity and measurement point in the immutable local result. Do not invent extension URLs, body-site codes or an Observation.basedOn reference for an unspecified external request type. Wire mapping of these optional metadata and final numeric precision remain identified design gaps; core registration/transport does not depend on inventing them.

Stop before 15 seconds sends nothing (REQ-07). Poor-signal reporting must satisfy REQ-08 without a numeric value. Proposed wire representation (owner acceptance still open): use the same Observation identity, code, time, device and optional subject, omit `valueQuantity`, and add `dataAbsentReason.coding = [{"system":"http://terminology.hl7.org/CodeSystem/data-absent-reason","code":"error"}]` [14]. Do not encode NaN, zero BPM or the string "error" as a numeric value. Use the same conditional delivery/receipt rules. This proposal is not silently accepted implementation behavior; REQ-08 remains blocked on that choice and subsequent validation.

Keep P13 unchanged: at most four conditional `POST /Observation` attempts, a one-second shared connect/TLS/write/receipt budget per attempt, two-second gaps, and one ten-second monotonic deadline from Stop including finalization and release. `If-None-Exist` uses the frozen measurement identifier; 201/200 is receipt. Retry transient/uncertain responses with identical bytes and identity; 412 and configuration/auth/certificate failures are terminal. No unconditional fallback, readback per measurement or delayed delivery queue applies. Delivery never creates a Device first: missing registration after finalization is immediately `DELIVERY_NOT_POSSIBLE` when Wi-Fi is configured.

Reuse the verified HTTP connection sequentially when eligible under TLS Design #100. Drain a bounded HTTP response completely before reuse or close the connection; never interpret leftover response bytes as the next response. Once a complete successful receipt is established, oversized optional response content need not revoke Sent: close instead of reusing it. Device-registration responses still require a validated id. Incomplete/malformed headers are not receipt. HTTP status/body limits and cancellation must be exercised before L1 acceptance.

## Request-delivery alternatives: Docker HAPI evaluation

These are alternatives, not selected implementations. Docker packaging does not provide an examination workflow. FHIR R4 Task/ServiceRequest model the work/request; the adapter still defines addressing, state, acknowledgement and patient extraction [9]. All candidates must recover pending requests after listening and must preserve local Start authority.

| Method | Fit with the observed HAPI Docker deployment | Evaluation |
| --- | --- | --- |
| Periodic FHIR searches, or history-based polling | Task and ServiceRequest count searches returned HTTP 200; capability statement advertises searchable resources [10] | Simplest candidate; ordinary HTTPS reuse, no inbound device listener or extra service. Poll intervals trade traffic for delay. Search/history cursors and deduplication still need design. |
| FHIR Subscription over WebSocket | HAPI 8.12.0 includes a WebSocket dispatcher [11]; this instance's enablement is unverified | Push candidate with outbound device connection. Needs subscription setup, separate WebSocket lifecycle, missed-request recovery and compatibility with listening pauses. REST uploads normally use another connection. |
| Subscription REST hook directly to device | Requires enabled subscription delivery and a callback address reachable from the container | Device hosts HTTP(S), with inbound reachability, credentials/trust and endpoint lifecycle. Poor fit for paused network processing during listening. |
| REST hook to a gateway, gateway to device | Requires an added service, which could run alongside HAPI in Docker Compose | Gateway can buffer notifications and adapt delivery. Adds service state, authentication and operations. |
| MQTT/AMQP or another broker via gateway | Requires a broker and a FHIR-to-device bridge; not established by running HAPI | Persistent outbound channel and buffering options, but more infrastructure and delivery semantics. Not the ordinary REST upload connection. |
| Long polling or Server-Sent Events via adapter | No such examination stream was verified on this HAPI instance; custom adapter/extension required | Avoids periodic empty searches but introduces a custom stream, timeouts and recovery. |
| FHIR messaging | Requires implemented message dispatch/receipt and workflow; resource storage alone is insufficient | Can express an exchange, but does not itself solve device reachability or transport. More integration than direct polling. |
| Email/SMS subscription channels | FHIR R4 lists them [12]; support/configuration in this instance is unverified | Poor direct device fit; needs a receiver/gateway and secure retrieval of request context. |

R5 topic-based subscriptions and their R4 backport change the subscription model, not the need for a delivery channel. The local configuration references `hl7.fhir.uv.subscriptions-backport.r4` version 1.1.0; this alone does not enable notification delivery [10]. Ordinary HTTP keep-alive does not let HAPI spontaneously send a new REST request down the upload connection. A WebSocket upgrade is a different application protocol, not simultaneous ordinary FHIR REST traffic on that same connection [11–13]. Keep polling and WebSocket as candidates; no adapter choice is accepted in this PR.

## Parameters and outstanding evidence

| ID | Proposed contract |
| --- | --- |
| P27-IDENTITY | Full factory station MAC, `stetho-` plus 12 uppercase hex digits; identifier system `urn:stethoscope:device` |
| P27-RECORD | `fhir/device-registration`, version 1, 343 bytes as specified above; canonical base URL at most 256 bytes, server id at most 64 bytes |
| P27-REGISTRATION | Ten seconds including conditional request, parsing and flash save; separate existing cleanup bound; recovery 60 seconds after failed/interrupted issued attempt, no total cap while Idle |
| P27-REQUEST | At most one pending request, consumed on accepted measurement Start; no automatic reapplication. External field bounds and durable replay rules remain adapter design inputs. |
| P27-BUFFERS | Proposed 2048-byte outgoing JSON capacity, 4096-byte registration-response body capacity and 4096-byte aggregate response-header capacity; reject overflow without truncation. Adapter bounds and target memory validation remain open. |
| P27-DELIVERY | Existing P13 deadlines, receipt, conditional identity, retry classifications and no delayed queue |

The read-only 29 October 2026 desktop probe reports HAPI FHIR Server 8.12.0, FHIR 4.0.1. Its metadata advertises conditional Device creation and identifier search; Task and ServiceRequest count searches returned HTTP 200 [10]. No Device/Observation was written, no Subscription was activated and no server configuration changed. Advertised capability is not proof of write authorization, actual duplicate handling, referential validation or end-to-end notifications. Capture server image/configuration identity and firmware revision with later integration evidence. TLS/certificate deployment prerequisites remain in #100.

| Scenario | Trace | Expected result |
| --- | --- | --- |
| Initial creation, lost receipt, one/multiple matches | REQ-09/11/12; VT-07/08 | One stable conditional identity; validated server id; 412 never falls back to unconditional creation |
| Flash failure, restart and corrupt/mismatched record | REQ-09/12/13; VT-08/11 | Not ready until committed; safe recovery with the same physical identity; old committed data preserved on failure |
| Wi-Fi change, server change and missing Device | REQ-09/11/12; VT-07/08 | Network changes preserve registration; server binding changes reconcile while Idle; frozen result never relabelled |
| Local Start, request duplication and context changes | REQ-02/09/13; VT-07/08/09 | Local authority, one consumed context, immutable subject; no next-session patient reuse after cancellation/failure |
| JSON fields, escaping, precision and overflow | REQ-09/10/11; VT-07/08 | Valid bounded base-FHIR representation; patient absent when unsupplied; no unverified profile claim |
| Early Stop and poor signal | REQ-07/08; VT-07/09 | Early Stop sends nothing; poor signal has no numeric value and requires the agreed error-report contract |
| Reconnect, uncertain receipt and terminal failure | REQ-09/10; VT-07/08 | P13 bounds; identical retries; receipt only on 201/200; visible terminal loss without delayed queue |
| Target identity, flash interruption and listening | REQ-02/12/13; VT-08/09/11 | Stable factory identity, demonstrated persistence/cancellation bounds and no active network jobs during audio |

This allocates future verification, not generated tests or target acceptance. The external adapter, request replay durability, optional metadata/profile mapping, numeric precision and deployed write/reference-validation behavior remain explicit gaps. Proposed record/buffer values require later implementation and evidence. Do not claim complete REQ-08 verification before its wire format and integration evidence exist.

## Sources

[1] Nico, *FHIR registration and examination-context design decisions*, personal communication, T3 Code, 29 October 2026, [conversation](t3-thread://v1/d5e44f69-2ecc-4a3e-917b-31a7b084c12b), accessed 29 October 2026. Project decisions, not target measurements.

[2] DigitalStethoscope contributors, *WIFI hotspot identity implementation*, project source, integration revision `3d989815b4cbded9bf64ec7c9934894f95cc68e5`, 2026, [wifi.c](../../coding/app/L1_services/L1_WIFI/wifi.c), lines 478–482, inspected 29 October 2026. This proves the source expression, not factory-MAC provenance on target.

[3] Health Level Seven International, *FHIR R4 Device*, version 4.0.1, 2019, <https://hl7.org/fhir/R4/device.html>, accessed 29 October 2026.

[4] Health Level Seven International, *FHIR R4 Data Types*, version 4.0.1, 2019, Identifier and id definitions, <https://hl7.org/fhir/R4/datatypes.html>, accessed 29 October 2026.

[5] Health Level Seven International, *FHIR R4 RESTful API*, version 4.0.1, 2019, Conditional create, <https://hl7.org/fhir/R4/http.html#ccreate>, accessed 29 October 2026.

[6] nt-medlink contributors (individual authors unverified), *PulsOxy InitState, MeasuringState and FhirResourceFactory*, NewTec GitLab, revision `e38b98fc8b881af01e23a8f4935567e73d00de28`, publication year unverified, [initialization](https://gitlab.newtec.zz/newtec/student-projects/nt-medlink/ntmedlinkremdev/-/blob/e38b98fc8b881af01e23a8f4935567e73d00de28/lib/App_PulsOxy/src/InitState.cpp), [sending](https://gitlab.newtec.zz/newtec/student-projects/nt-medlink/ntmedlinkremdev/-/blob/e38b98fc8b881af01e23a8f4935567e73d00de28/lib/App_PulsOxy/src/MeasuringState.cpp), [builder](https://gitlab.newtec.zz/newtec/student-projects/nt-medlink/ntmedlinkremdev/-/blob/e38b98fc8b881af01e23a8f4935567e73d00de28/lib/FhirService/src/FhirResourceFactory.cpp), accessed 29 October 2026. Initialization PUTs Patient/Device; measurement sends Observations without registration per message.

[7] Health Level Seven International, *FHIR R4 Vital Signs*, version 4.0.1, 2019, <https://hl7.org/fhir/R4/vitalsigns.html>, accessed 29 October 2026. Coding reference only; profile conformance is not claimed.

[8] Health Level Seven International, *FHIR R4 Observation*, version 4.0.1, 2019, <https://hl7.org/fhir/R4/observation.html>, accessed 29 October 2026.

[9] Health Level Seven International, *FHIR R4 Task* and *ServiceRequest*, version 4.0.1, 2019, <https://hl7.org/fhir/R4/task.html> and <https://hl7.org/fhir/R4/servicerequest.html>, accessed 29 October 2026.

[10] GPT-6.1-Sol on behalf of Nico, *Read-only HAPI FHIR capability and request-delivery investigation*, own desktop observations, 29 October 2026, recorded above and in the [conversation](t3-thread://v1/d5e44f69-2ecc-4a3e-917b-31a7b084c12b). Python desktop HTTPS probes, no device firmware revision. Capability and count-query results do not establish write/notification behavior.

[11] HAPI FHIR contributors, *WebsocketDispatcherConfig*, HAPI FHIR 8.12.0, 2026 (source copyright year), [source](https://github.com/hapifhir/hapi-fhir/blob/v8.12.0/hapi-fhir-jpaserver-subscription/src/main/java/ca/uhn/fhir/jpa/subscription/match/config/WebsocketDispatcherConfig.java), accessed 29 October 2026. Source capability, not deployment enablement.

[12] Health Level Seven International, *FHIR R4 Subscription*, version 4.0.1, 2019, <https://hl7.org/fhir/R4/subscription.html>, accessed 29 October 2026. Subscription channels and polling/history alternative.

[13] Ian Fette and Alexey Melnikov, *The WebSocket Protocol*, IETF RFC 6455, December 2011, sections 1.3 and 1.7, DOI [10.17487/RFC6455](https://doi.org/10.17487/RFC6455), accessed 29 October 2026.

[14] Health Level Seven International, *FHIR R4 DataAbsentReason code system*, version 4.0.1, 2019, <https://hl7.org/fhir/R4/codesystem-data-absent-reason.html>, accessed 29 October 2026. The selected use of `error` for poor-signal reporting is a project proposal, not prescribed by this source.
