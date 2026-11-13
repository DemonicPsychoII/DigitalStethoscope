# TLS preparation and connection reuse

## Basis and accepted decisions

This Design-stage contract refines [TLS architecture PR #80](https://github.com/DemonicPsychoII/DigitalStethoscope/pull/80) at `2142fbd5b635ec399775fd92d18c48e9bcb085e9` and requirements/shared design at `3d989815b4cbded9bf64ec7c9934894f95cc68e5`. It depends on [SNTP Design PR #99](https://github.com/DemonicPsychoII/DigitalStethoscope/pull/99) at `36ffb0ec45dab9a4cde7cf8882505fb7bf1415bc`. Covered requirements are REQ-02, REQ-09, REQ-10, REQ-11, REQ-13 and REQ-14; verification allocation is VT-07, VT-08, VT-09 and VT-11. No firmware, server configuration or generated tests change here.

Nico accepted TLS 1.3 only, server-only authentication, a separate public server certificate, connection reuse, bounded preparation and recovery, offline listening, delivery-budget interaction and clock invalidation in this conversation [1]. Connection keep-alive, reconnect timing and the connection-setup budget within the delivery timeout and retry parameter [P13](../system/parameters.md) were decided in a follow-up review on 29 October 2026 [7]. The design review of 2 November 2026 moved endpoint and certificate into a separate server profile image and placed one SNTP exchange inside every connection setup [8]. The service interfaces below are proposed refinements; agreement on behavior is not target acceptance.

## Trust and server profile inputs

Each device talks to exactly one server. Its HTTPS endpoint (hostname or IP, port and base path), the PEM public server certificate and the server keep-alive timeout travel together in a server profile image, separate from the firmware. A separate flash command writes that image to the server profile partition of the [flash layout](../STORAGE/interfaces-and-behavior.md#flash-layout); a firmware update leaves it unchanged. Boot validates the image once (format version, lengths, CRC-32 and certificate parsing). A missing or invalid image leaves secure transport unavailable with a configuration cause; there is no fallback endpoint or certificate. Never place the server private key or keystore in the image. Network or portal enrollment, a project CA, older TLS versions and plain-HTTP fallback are outside this version.

Whoever can flash the device can change its server; physical access is the trust assumption. The CRC detects corruption, not tampering.

Trust the selected self-signed server certificate directly. Require the configured endpoint identity, acceptable certificate validity against the prepared UTC clock and successful TLS peer verification. Do not fetch a certificate from an unverified connection and automatically trust it. DNS resolution changes the destination address, never the configured reference identity. Require a matching DNS or IP Subject Alternative Name (SAN); do not rely on legacy Common Name fallback [2,3]. Later L1_WIFI work must demonstrate that the pinned verifier enforces validity and identity even for the directly trusted certificate. If its handling of trust anchors, the certificates it trusts as the starting point of verification, omits these checks, L1_WIFI adds explicit checks. A server or certificate change rewrites the server profile image without a firmware update; no automatic rollover is claimed.

No client certificate or device private key is configured. TLS authenticates the server, not the device. FHIR Device registration is separate application state; successful TLS does not prove authorization to create Device or Observation resources. If the deployed server requires client authentication or other credentials, report the cause rather than weaken verification. Application authorization and registration behavior belong to the later FHIR Design PR.

TLS 1.3 permits application traffic after the handshake and does not require a new handshake for each request [2]. Retain the connection when possible, but treat remote/network idle closure as ordinary transport loss. No negotiated session-resumption or 0-RTT (zero round-trip early data) mechanism is required by this design; reconnect may use a full handshake.

## Ownership and proposed service contracts

CONTROL grants the exclusive network lease. COMMUNICATION owns preparation policy, monotonic deadlines, readiness, retry scheduling and failure episodes. WIFI owns the DNS/TCP/TLS context and verification at the Zephyr socket boundary. Later FHIR code uses the verified transport; it cannot select an insecure mode. This follows the architecture basis, not the class layout of the PulsOxy reference project [5].

| Proposed operation | Contract |
| --- | --- |
| `wifi_startSecureConnection` | Under the lease, accept the immutable endpoint/trust configuration and caller deadline; at most one operation/context. Start DNS, TCP and TLS 1.3 with mandatory peer verification. Return accepted, busy or a cause; no internal workflow retries. |
| `wifi_waitForSecureConnection` | Wait at most the caller interval. Return pending or one terminal result, with verified endpoint/configuration identity and peer-validity interval on success. Completion quiesces operation callbacks. Short waits never restart the deadline. |
| `wifi_cancelSecureConnection` | Cancel pending resolution/connect/handshake, close the pending context and quiesce callbacks. Idempotent when inactive; use the one-second per-service stop bound of the Wi-Fi cleanup limits in [P23](parameters.md). Do not acknowledge release without proof. |
| `wifi_closeSecureConnection` | Invalidate and close a retained context under the lease, with the same stop bound. No reconnect, HTTP request or workflow retry. |

Operation generations reject late results after cancellation, configuration change or prerequisite loss. A terminal result contains a bounded cause category (resolution, TCP, timeout, TLS version, trust/name/validity, local configuration or cleanup), not secrets or patient context. No new context may replace one whose release is unproven. The later interface, L2_COMMUNICATION and L1_WIFI stages must realize these contracts and demonstrate bounded cancellation; force-aborting a blocked worker is not proof of release.

Track station-address readiness, transport verification and Device registration independently. Transport verification means the most recent handshake verified the server under the current endpoint/trust configuration and the clock applied by the SNTP exchange of the same setup; it does not require an open socket. A retained socket is only a reuse candidate, not proof that the next request will succeed. Idle has no keepalive traffic and no reconnect loop: a connection closed by the server while Idle is replaced on the next use. Binding the connection to endpoint/trust configuration prevents reuse with another server. Registration persistence and invalidation remain for FHIR design.

## Preparation, listening and recovery

1. While Idle and holding the lease, require a station address and a valid server profile image. Boot has no retained connection. Missing prerequisites defer preparation without consuming an attempt or reporting a TLS handshake failure.
2. Start one monotonic ten-second deadline before the [SNTP exchange](time-synchronization.md#flow-and-scheduling) that opens every setup. SNTP, resolution, TCP setup, handshake and verification share that budget. Publish a verified connection only after every check succeeds. Cleanup has its separate P23 bound.
3. On failed preparation, mark transport unavailable, release resources and schedule another preparation attempt no earlier than 60 seconds after failure completion. Recovery continues without a total attempt cap while Idle and prerequisites permit. No catch-up bursts or hidden lower-level retries apply. Invalid certificate/configuration attempts remain unavailable and never trigger an insecure fallback.
4. Start preempts preparation: cancel and establish quiescence before audio. An interrupted issued attempt observes the same 60-second gap; cancellation before issuance consumes no attempt. Start cancellation alone is not an error. Failed cleanup follows the existing `WIFI_CLEANUP_FAILURE` restart policy, not ordinary TLS recovery.
5. During listening retain an already verified, dormant connection if possible. Issue no application requests, heartbeats, proactive reconnects or active liveness probes. Disable optional TCP keepalive probes. This is not a claim that retaining a Wi-Fi/TCP association eliminates driver or protocol traffic; target audio-interference verification remains necessary. If background TLS handling requires application work, defer it until the lease returns or invalidate the connection.
6. After listening, reuse the retained context only if endpoint/trust configuration and peer-validity checks still hold, for a delivery the clock anchor of its handshake still qualifies for the measurement end under the [mapping limit](time-synchronization.md#clock-mapping-and-native-behavior) and it has been idle for less than the device keep-alive timeout. Before the first request, poll the socket without blocking; a pending close (FIN, RST or `close_notify`) invalidates it without consuming an attempt. Closure/reset discovered on use still invalidates it.
7. Close a retained context whose idle time reaches the device keep-alive timeout: under the lease while Idle, as logical invalidation during listening. Set the device keep-alive timeout to the server keep-alive minus 5 seconds; the server profile image carries the server value as a deployment input. The local deployment of the HAPI FHIR server closed an idle TLS 1.3 connection after about 60 seconds with default settings [4]; the test deployment raises `server.tomcat.keep-alive-timeout` to 10 minutes and keeps the default as the comparison case.
8. Retention during listening is the initial approach. If target measurement under [TICKET-213](https://nfrie.atlassian.net/browse/TICKET-213), measuring TLS reconnect timing and connection survival on the target, shows that the connection does not survive, close it at Start before audio instead. Idle recovery uses the preparation policy; active delivery uses P13 below.

Before every new application request, check the retained peer's validity interval against the current clock. Configuration change, certificate expiry or a clock correction that makes validity fail immediately removes transport eligibility. During listening this is logical invalidation only; close under the lease afterward. A new setup, starting with its SNTP exchange, must verify the server before further requests. A clock correction that remains within the peer-validity interval does not itself require reconnection.

## Delivery budget boundary

Reconnection is the expected delivery path; reuse is an optimisation. P13 keeps one ten-second deadline from Stop, at most four attempts and two-second gaps after transient failure. Within an attempt, connection setup (SNTP, DNS, TCP, TLS and verification) has its own three-second limit and write plus receipt keep one second, both capped by the remaining global time. A failed connection setup counts as a failed attempt. Delivery connection setup starts when CONTROL submits the finalized job, not at Stop; the deadline still runs from Stop, so finalization time comes out of the same budget [9]. No setup is then wasted or cancelled when no job is granted (Stop before 15 s, Wi-Fi unconfigured or failed delivery prerequisites), and an eligible retained verified connection is reused without any setup. It never uses the ten-second Idle preparation allowance. A Start during Sending cancels the delivery job [9]: a connection setup or exchange in flight is cancelled, a retry gap ends at once and no further attempt starts. The job ends with `DELIVERY_FAILURE`, or with `SERVER_CONNECTION_FAILURE` when no qualifying clock anchor ever froze its UTC end, and the result is lost; a failed cancellation follows `WIFI_CLEANUP_FAILURE` under P23. The three-second and one-second values are provisional until TICKET-213 measures handshake and conditional-POST times on the target.

A usable retained connection is preferred but is not a mandatory delivery prerequisite: transport loss alone allows a bounded reconnect if the other delivery prerequisites hold. A missing or invalid server profile image follows `DELIVERY_NOT_POSSIBLE` before issuance. Certificate/name/validity failure discovered during an issued attempt is terminal `DELIVERY_FAILURE`; transient loss, including a failed SNTP exchange, follows P13 retry rules. A result that has no qualifying clock anchor when P13 ends latches `SERVER_CONNECTION_FAILURE` under the SNTP design. Delivery reconnects are governed by P13 rather than the Idle 60-second recovery gap. Frozen payload, identity and timestamp remain unchanged; no delayed queue is introduced. Registration eligibility remains the later FHIR design's responsibility.

## Failure indication

Failed TLS preparation latches `SERVER_CONNECTION_FAILURE`, preserving standalone listening. Acknowledgement clears only its indication: it neither creates transport readiness nor triggers a retry. Recovery continues independently. Success restores readiness but does not acknowledge an existing indication. Do not re-latch on every failed retry after acknowledgement in the same unavailable episode; successful recovery followed by a new preparation failure begins a new episode. Passive loss alone does not change transport verification; a subsequent failed reconnection or preparation raises the indication. A failed SNTP exchange is a failed preparation and raises this indication; the serial log names the time cause. There is no separate time-synchronization error. Issued delivery failures use the existing delivery indication.

## Parameters

| ID | Value / meaning |
| --- | --- |
| P26-VERSION | TLS 1.3 only; mandatory verification; no older TLS or HTTP fallback |
| P26-TRUST | One endpoint plus PEM public server certificate in the separate server profile image; no client certificate/key or network enrollment |
| P26-ATTEMPT | Ten seconds including SNTP/DNS/TCP/TLS/verification during Idle preparation; separate P23 one-second per-service cleanup bound |
| P26-RETRY | 60 seconds after failed/interrupted issued preparation completes; ongoing recovery while Idle |
| P26-REUSE | Retain a dormant verified context; no application heartbeat or proactive reconnect during listening; recheck time/configuration/peer validity, idle age and a non-blocking close poll before reuse; fall back to closing at Start if TICKET-213 shows the connection does not survive |
| P26-KEEPALIVE | Device keep-alive timeout = server keep-alive minus 5 seconds, server value from the server profile image; test deployment server keep-alive 10 minutes, default 60 seconds as comparison |
| P26-DELIVERY | P13 remains authoritative: per attempt three seconds connection setup including SNTP plus one second write and receipt, ten seconds total from Stop; connection setup starts at job submission; provisional until TICKET-213 |

## Investigation basis and limitations

Read-only investigation on 29 October 2026 observed Docker Desktop container `fhir_tls`, image tag `hapiproject/hapi:latest`, exposing local TCP/8443. A Python desktop client forced TLS 1.3, trusted the retrieved public certificate explicitly, configured no client certificate and received HTTP 200 from `GET /fhir/metadata` [4]. This proves that tested local read request only. It does not prove write authorization, device reachability, persistent-connection behavior or Zephyr interoperability. A follow-up desktop probe held an idle TLS 1.3 connection after one metadata request; the server closed it after about 60 seconds, consistent with Spring Boot's embedded Tomcat default keep-alive, as `hapi.application.yaml` sets no Tomcat timeout. The observed public certificate SHA-256 is `2bcec564243b27d9781e249794ccbeae83e88e1c2ccc6edba6db6b5eaa2cc2cd`. The container image content ID captured while documenting the investigation is `sha256:d4a0dc0bcde83fbbb855fc739aa952b376a31b27dca343c51e8607a1db6a8e35`; a registry manifest digest and complete versioned server configuration remain for integration evidence. The mutable image tag alone is not a reproducible server baseline.

The observed certificate has Common Name `localhost`, no SAN, and validity 17 June 2025 07:11:56 UTC through 25 September 2027 07:11:56 UTC [4]. The desktop probe's Common Name fallback is insufficient for this design. Replace the certificate with one covering the actual device-facing endpoint before device acceptance; the endpoint value and certificate artifact remain deployment inputs, not guessed here. No server change was made.

The PulsOxy reference project at `e38b98fc8b881af01e23a8f4935567e73d00de28` loads `Config::CERTIFICATE` and calls `setCACert()` when nonempty; its FHIR service supplies no client certificate/key or application authorization and creates a local HTTP client per operation with `end()` afterward [5]. It does not explicitly select TLS 1.3 or demonstrate persistent reuse. Its Arduino implementation is a reference for trust configuration, not proof of this Zephyr design or of the OAuth2 behavior described in its documentation.

The pinned Zephyr socket implementation has a TLS 1.3 protocol path [6]. Actual ESP32-S3 configuration, cipher compatibility, direct-certificate trust behavior, SAN enforcement, cancellation, heap use and delivery latency remain unverified. Public SNTP remains unauthenticated under the accepted SNTP assumption; certificate time checks do not turn that clock into an authenticated time source.

## Verification allocation

| Scenario | Trace | Expected result |
| --- | --- | --- |
| Server profile image and endpoint mismatch | REQ-11; VT-08 | Missing/corrupt image leaves transport unavailable with a configuration cause; a firmware update keeps the image; wrong SAN, untrusted or expired peer never becomes ready. |
| TLS version and server-only handshake | REQ-11; VT-07/08 | TLS 1.3 succeeds with matching trust; older-only peer/client-certificate requirement fails without fallback. |
| DNS/TCP/TLS stall and repeated recovery | REQ-11/13/14; VT-08/09/11 | Ten-second preparation deadline, 60-second gaps, no indication storm; standalone listening works. |
| Start/cancellation race and cleanup failure | REQ-02/13; VT-08/09 | Quiesce before audio; stale completions ignored; failed cleanup uses restart policy. |
| Retained connection, idle closure and delivery reconnect | REQ-09/10/11; VT-07/08 | Reuse when eligible; a closed or over-age socket is replaced without consuming an attempt; reconnect stays within P13 and keeps the frozen result; no delayed send. Target timing and connection survival follow [TICKET-213](https://nfrie.atlassian.net/browse/TICKET-213). |
| SNTP before handshake, validity boundary and correction | REQ-09/11; VT-07/08 | Every setup applies a fresh clock before its ClientHello, the first TLS handshake message; no request on an invalidated context; a new setup is required. |
| Listening and dormant transport | REQ-02/13; VT-08/09 | No application network jobs/heartbeats; target evidence checks audio interference. |
| HAPI Device and Observation authorization | REQ-10/11; VT-07 | Future integration verifies registration/upload permissions separately from metadata/TLS success. |

These are future verification expectations, not an executed or generated test batch. SNTP and TLS architecture/design dependencies remain separately reviewed; FHIR message fields, registration flow and external request adapter are outside this PR.

## Sources

[1] Nico, *TLS detailed-design decisions*, personal communication, T3 Code, 29 October 2026, [conversation](t3-thread://v2/d5e44f69-2ecc-4a3e-917b-31a7b084c12b/576e10df-527c-41cc-86cd-4e7c0ff0c290), accessed 29 October 2026. Project decisions, not measurements.

[2] Eric Rescorla, *The Transport Layer Security (TLS) Protocol Version 1.3*, IETF RFC 8446, August 2018, sections 2, 4.3.2, 4.4.2 and 4.6, DOI [10.17487/RFC8446](https://doi.org/10.17487/RFC8446), accessed 29 October 2026.

[3] Peter Saint-Andre and Rich Salz, *Service Identity in TLS*, IETF RFC 9525, November 2023, sections 4 and 6, DOI [10.17487/RFC9525](https://doi.org/10.17487/RFC9525), accessed 29 October 2026.

[4] GPT-6.1-Sol on behalf of Nico, *Local HAPI TLS investigation*, own desktop observations, 29 October 2026, recorded in this page and [conversation](t3-thread://v2/d5e44f69-2ecc-4a3e-917b-31a7b084c12b/576e10df-527c-41cc-86cd-4e7c0ff0c290). No device firmware revision: Python desktop probe only. Raw probe transcript is conversation evidence; the image content ID is recorded above, but no registry manifest digest was captured. Findings are limited to the observed instance.

[5] nt-medlink contributors (individual authors unverified), *PulsOxy FhirService implementation*, NewTec GitLab, revision `e38b98fc8b881af01e23a8f4935567e73d00de28`, publication year unverified, [source](https://gitlab.newtec.zz/newtec/student-projects/nt-medlink/ntmedlinkremdev/-/blob/e38b98fc8b881af01e23a8f4935567e73d00de28/lib/FhirService/src/FhirService.cpp), lines 55–83, 140–172 and 215–309, accessed 29 October 2026.

[6] Zephyr Project contributors, *TLS socket implementation*, Zephyr Project, revision `357467a011cd2557a1a3f0b4be83d817c4addc9b`, publication year unverified, [source](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/subsys/net/lib/sockets/sockets_tls.c), `NET_IPPROTO_TLS_1_3` branch, accessed 29 October 2026.

[7] Nico, *TLS keep-alive and reconnect decisions*, personal communication, T3 Code, 29 October 2026, [conversation](t3-thread://v2/d5e44f69-2ecc-4a3e-917b-31a7b084c12b/e4e74eaa-efe8-48c5-8071-2589f46555a2), accessed 29 October 2026. Project decisions, not measurements.

[8] Andreas Summerer and Nico, *Design review of time, TLS and FHIR*, review meeting, 2 November 2026, with Nico's resolutions in the [decision record](../../planning/mvp-decisions-2026-11-02.md), accessed 2 November 2026. Project decisions, not measurements.

[9] Nico, *Delivery start, Start during sending, cleanup services, result freeze points and filter roles*, personal communication, T3 Code, 13 November 2026, recorded in the [decision record](../../planning/mvp-decisions-2026-11-13-delivery-and-filters.md), accessed 13 November 2026. Project decisions, not measurements.
