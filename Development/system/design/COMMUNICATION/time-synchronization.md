# SNTP synchronization and clock readiness

## Basis

This Design-stage contract refines [SNTP architecture PR #78](https://github.com/DemonicPsychoII/DigitalStethoscope/pull/78) at `4c25ba2ea12d718541f2ec3f00653ea3bc2d5823` and requirements/shared design at `3d989815b4cbded9bf64ec7c9934894f95cc68e5`. It covers REQ-02, REQ-09, REQ-10, REQ-11, REQ-13 and REQ-14; verification uses VT-07, VT-08, VT-09 and VT-11. No firmware or generated tests are included.

Nico accepted the source/trust assumption, Zephyr uncertainty estimate, boot synchronization, shared certificate/measurement clock basis, monotonic durations, cancellation, timing values and failure behavior during the SNTP grilling rounds [1]. Agreement on those behaviors is distinct from approval of the proposed interfaces below or target verification.

## Ownership and proposed interfaces

CONTROL grants the exclusive network lease. COMMUNICATION owns deadlines, readiness and scheduling. WIFI owns DNS/SNTP resources, native-result normalization and platform clock access. Callbacks publish results; they do not apply the clock, change controller state or retry.

These proposed WIFI interfaces follow the existing command/wait style and belong to later L2/L1 PRs:

| Operation | Contract |
| --- | --- |
| `wifi_startTimeSynchronization` | Accept a hostname and at most one pending operation; return accepted, busy or a cause. Resolve IPv4 through the station's DNS configuration and issue one UDP/123 SNTP request. No resend, alternate-server loop or clock mutation. |
| `wifi_waitForTimeSynchronization` | Accept a caller wait interval and result destination; return pending, a normalized sample, or terminal failure. Completion means operation resources/callbacks are quiesced. Waiting does not issue another request. |
| `wifi_cancelTimeSynchronization` | Cancel DNS, detach/close the socket and quiesce callbacks. Idempotent when inactive; reuse P23's one-second per-service stop bound. Return failure rather than falsely acknowledging release. |
| `wifi_applyTimeSynchronization` | Under the lease, advance a successful sample by elapsed monotonic time, set Zephyr real time and return the applied UTC/monotonic anchor. On failure publish no ready anchor. No network work or retry. |

A normalized sample contains Unix UTC seconds plus fractional nanoseconds, an independently sampled receive-time kernel monotonic timestamp in microseconds, and Zephyr's estimated uncertainty in microseconds. An applied anchor contains the corresponding applied UTC/monotonic pair and estimate. The caller owns copied values; no native `sntp_time` fields cross this boundary. Keep microsecond uncertainty internally; round upward when displaying milliseconds.

Each accepted operation produces one terminal result. Cancellation invalidates its generation; late DNS/socket callbacks cannot publish a sample for a newer operation or access a released context. Do not replace an operation until completion/cancellation establishes quiescence.

## Flow and scheduling

1. Boot starts without a valid anchor. A persisted timestamp does not establish freshness; offline listening remains available.
2. After the selected station obtains an IPv4 address and CONTROL admits network work while Idle, request time directly from `pool.ntp.org`. No separate internet/HTTP probe is used.
3. Start one five-second monotonic attempt deadline before DNS submission. DNS, request, response, normalization and clock application share the remaining budget. Short waits never reset it. Failed submission counts as an issued attempt; absence of connectivity/lease does not. Cancellation cleanup has the separate P23 stop bound.
4. Accept only a current-generation result while holding the lease; apply the clock, then publish readiness. Clock-set failure is attempt failure. Successful application starts the refresh/expiry timers and enables later secure-server preparation; this page does not implement TLS or registration.
5. On failure, retain an unexpired previous anchor and schedule recovery no earlier than 60 seconds after failure completion. No total recovery-attempt cap applies. Missing connectivity and listening defer issuance without catch-up bursts.
6. Refresh becomes due 15 minutes after successful application. Defer its network work during listening. Expire readiness at one hour even when refresh is deferred/failing; failed attempts never extend anchor age. Expiry does not stop audio. A new successful application restarts both timers.

Start cancels DNS or exchange work before audio begins. Ignore a completion racing with Start unless it was accepted/applied before CONTROL withdrew the lease. Cancellation is not time-sync failure. An interrupted issued attempt observes the normal 60-second gap before reissuance while Idle; an already-running gap is not reset by listening transitions. Cancellation before issuance consumes no attempt.

A failed cancellation is a resource-release fault, not merely unavailable time: report the existing cleanup/failure outcome, never claim quiescence or admit overlapping audio/network work on unproven release. Later L1 work must demonstrate cancellation bounds; a blocking five-second helper or forced worker abort is not a substitute.

## Clock mapping and native behavior

Enable `CONFIG_SNTP_UNCERTAINTY` and retain Zephyr's estimate [2]. It estimates exchange/server uncertainty; it does not authenticate the source or independently bound subsequent clock drift and software latency. No arbitrary millisecond tolerance replaces it. Refresh/expiry values are project settings pending drift evidence, not measured accuracy claims.

Set Zephyr's real-time software clock; no battery-backed RTC is assumed. Advance the receive-time estimate by elapsed kernel monotonic time before applying it. Preserve the usable clock anchor with measurement timing data and derive measurement-end UTC from that anchor plus monotonic elapsed time. Corrections occur outside listening and may step real time without changing duration or rewriting a frozen result. Delivery retries retain the original timestamp/identity; the existing uniqueness rule remains mandatory, including after backward corrections. Never invent a timestamp to avoid a collision.

An expired anchor is insufficient for new server work. Do not remap a frozen result after resynchronization or wait beyond the delivery budget for a replacement. If its mapping or current prerequisites are ineligible at finalization, follow `DELIVERY_NOT_POSSIBLE`; no delayed delivery queue is introduced. This timing anchor is separate from the still-open examination-context attachment policy.

Pinned-source caveat [2]: the uncertainty-enabled parser assigns `fraction` as a microsecond remainder, unlike the binary fraction on the ordinary path. The header calls `uptime_us` uptime, but the implementation derives it from real-time/NTP-epoch timestamps. WIFI must normalize the pinned units and independently sample kernel monotonic time rather than cast these fields or treat native `uptime_us` as kernel uptime. Verify unset initial time, subsecond carry and conversion before L1 acceptance. Recheck these semantics on a Zephyr revision change. This PR contains no upstream patch.

## Failure indication and acknowledgement

Initial failed synchronization or anchor expiry with no usable anchor latches `TIME_SYNCHRONIZATION_FAILURE`, while preserving offline Start/listening. Failed refresh with an unexpired anchor records the cause and schedules recovery without a new operator error. Diagnostics contain cause, age and estimate, never credentials/patient context.

Acknowledgement clears the indication only: no clock-validity change or immediate retry. Automatic recovery proceeds independently. Follow the existing latched-error model: success restores readiness but does not itself acknowledge the indication. After acknowledgement while unavailable, do not re-latch on every scheduled failure; successful recovery followed by another loss starts a new failure episode. Start cancellation alone does not create one.

## Parameters

| ID | Value / meaning |
| --- | --- |
| P25-SERVER | `pool.ntp.org`, IPv4 DNS and SNTP over UDP/123 |
| P25-ATTEMPT | 5 seconds beginning before DNS; separate existing one-second per-service cancellation bound |
| P25-RETRY | 60 seconds after failed/interrupted issued attempt completes; ongoing recovery while Idle, no total attempt cap |
| P25-REFRESH | 15 minutes after successful application; active work deferred during listening |
| P25-EXPIRY | One hour after successful application; failure does not extend it |
| P25-UNCERTAINTY | Zephyr `CONFIG_SNTP_UNCERTAINTY`; microseconds internally; no measured accuracy/drift guarantee |

## Limitations and verification

The initial source requires usable DNS and reachable public UDP/123; Wi-Fi alone does not supply time. Local-server fallback is deferred to [GitHub #85](https://github.com/DemonicPsychoII/DigitalStethoscope/issues/85) / [TICKET-212](https://nfrie.atlassian.net/browse/TICKET-212). Unauthenticated SNTP is accepted for this MVP [1,3]; no authenticated-time claim follows. [GitHub #88](https://github.com/DemonicPsychoII/DigitalStethoscope/issues/88) / TICKET-209 retains reference-comparison and accuracy evidence.

| Scenario | Trace | Expected result |
| --- | --- | --- |
| Boot and successful exchange | REQ-09/11; VT-07/08 | No persisted ready clock; normalize uncertainty and apply UTC/monotonic anchor before readiness. |
| DNS failure, blocked UDP, rejected response | REQ-09/13; VT-08/09 | Bounded attempt and 60-second recovery; visible initial failure without blocking listening. |
| Start during DNS/wait/completion race | REQ-02/13; VT-08/09 | Quiesce before audio; stale completion cannot apply time; cancellation raises no time-sync error. |
| Refresh/expiry boundaries and failed refresh | REQ-09/13/14; VT-07/08/09 | Keep unexpired anchor, defer active work during listening, expire at one hour; acknowledgement changes neither readiness nor scheduling. |
| Correction and frozen measurement | REQ-09/10; VT-07 | Monotonic duration and frozen UTC/identity stay unchanged; no remapping or delayed resend. |
| Native units, unset time, subsecond carry | REQ-09/11; VT-07/08 | Consistent UTC conversion and independently sampled monotonic anchor. |
| Repeated failures, recovery and cleanup fault | REQ-13/14; VT-08/09/11 | No per-retry indication storm after acknowledgement; never report unproven release. |

These allocate future verification, not generated tests or execution. DNS/socket integration, target cancellation latency, drift/reference comparison and audio interference remain pending. Timestamp acceptance evidence is not replaced by a reported estimate.

## Sources

[1] Nico, *SNTP detailed-design decisions*, personal communication, T3 Code, 28 October 2026, [conversation](t3-thread://v1/d5e44f69-2ecc-4a3e-917b-31a7b084c12b), accessed 28 October 2026. Numbered grilling answers establish source/trust, uncertainty, cancellation, timing and failure-indication choices; project decisions, not measurements.

[2] The Zephyr Project, *SNTP API, Kconfig, implementation and DNS resolver API*, Zephyr source repository revision `357467a011cd2557a1a3f0b4be83d817c4addc9b`, publication year unverified; [SNTP header](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/include/zephyr/net/sntp.h), [Kconfig](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/subsys/net/lib/sntp/Kconfig), [parser](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/subsys/net/lib/sntp/sntp.c), [helper](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/subsys/net/lib/sntp/sntp_simple.c), [DNS header](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/include/zephyr/net/dns_resolve.h), accessed 28 October 2026. The convenience helper resolves before its exchange timeout and resends internally; split DNS/SNTP APIs underpin the proposed cancellable adapter. Target behavior remains unverified.

[3] David L. Mills, *Simple Network Time Protocol (SNTP) Version 4 for IPv4, IPv6 and OSI*, IETF RFC 4330, January 2006, section 9, DOI: 10.17487/RFC4330, <https://www.rfc-editor.org/rfc/rfc4330#section-9>. Access recorded 24 October 2026 in the [source register](../../../../thesis-material/quellen.md#ietf_sntp_4330_2006); no new access claimed.
