# SNTP synchronization and clock readiness

## Basis

This Design-stage contract refines [SNTP architecture PR #78](https://github.com/DemonicPsychoII/DigitalStethoscope/pull/78) at `1e5085aa96edbb49683a988af302b95e570019e2` and requirements/shared design at `3d989815b4cbded9bf64ec7c9934894f95cc68e5`. It covers REQ-02, REQ-09, REQ-10, REQ-11, REQ-13 and REQ-14; verification uses VT-07, VT-08, VT-09 and VT-11. No firmware or generated tests are included.

Nico accepted the source/trust assumption, Zephyr uncertainty estimate, shared certificate/measurement clock basis, monotonic durations and cancellation during the SNTP grilling rounds [1]. The design review of 2 November 2026 placed SNTP inside every TLS connection setup, replaced the Idle refresh schedule by a computed mapping limit and merged the time error into the server-connection error [4]. Agreement on those behaviors is distinct from approval of the proposed interfaces below or target verification.

## Ownership and proposed interfaces

CONTROL grants the exclusive network lease. COMMUNICATION owns deadlines, readiness and scheduling. WIFI owns DNS/SNTP resources, native-result normalization and platform clock access. Callbacks publish results; they do not apply the clock, change controller state or retry.

These proposed WIFI interfaces follow the existing command/wait style. Later pull requests for L2_COMMUNICATION and L1_WIFI implement them:

| Operation | Contract |
| --- | --- |
| `wifi_startTimeSynchronization` | Accept a hostname and at most one pending operation; return accepted, busy or a cause. Resolve IPv4 through the station's DNS configuration and issue one UDP/123 SNTP request. No resend, alternate-server loop or clock mutation. |
| `wifi_waitForTimeSynchronization` | Accept a caller wait interval and result destination; return pending, a normalized sample, or terminal failure. Completion means operation resources/callbacks are quiesced. Waiting does not issue another request. |
| `wifi_cancelTimeSynchronization` | Cancel DNS, detach/close the socket and quiesce callbacks. Idempotent when inactive; reuse the one-second per-service stop bound of the Wi-Fi cleanup limits in [P23](parameters.md). Return failure rather than falsely acknowledging release. |
| `wifi_applyTimeSynchronization` | Under the lease, advance a successful sample by elapsed monotonic time, set Zephyr real time and return the applied UTC/monotonic anchor. On failure publish no ready anchor. No network work or retry. |

A normalized sample contains Unix UTC seconds plus fractional nanoseconds, an independently sampled receive-time kernel monotonic timestamp in microseconds, and Zephyr's estimated uncertainty in microseconds. An applied anchor is the reference point for later time conversion: it contains the UTC time and kernel monotonic time at which the clock was applied, and the uncertainty estimate. The caller owns copied values; no native `sntp_time` fields cross this boundary. Keep microsecond uncertainty internally; round upward when displaying milliseconds.

Each accepted operation produces one terminal result. Cancellation invalidates its generation; late DNS/socket callbacks cannot publish a sample for a newer operation or access a released context. Do not replace an operation until completion/cancellation establishes quiescence.

## Flow and scheduling

1. Boot starts without a valid anchor. A persisted timestamp does not establish freshness; offline listening remains available.
2. Every TLS connection setup under the [TLS design](secure-transport.md) begins with one SNTP exchange, so that only the server DNS lookup and TCP connection lie between the applied clock and the ClientHello, the first message of the TLS handshake. This applies to the Idle preparation and every delivery reconnect. Reusing an open verified connection sends no ClientHello and runs no SNTP. There is no separate SNTP schedule, refresh timer or internet/HTTP probe.
3. The exchange shares the deadline of the connection setup that contains it: the ten-second Idle preparation of the [P26 TLS parameters](secure-transport.md#parameters), or the three-second connection-setup budget of a delivery attempt under the delivery timeout and retry parameter [P13](../system/parameters.md). DNS, request, response, normalization and clock application share the remaining budget; short waits never reset it. Cancellation cleanup has the separate P23 stop bound.
4. Accept only a current-generation result while holding the lease; apply the clock, then continue with the TCP connection and ClientHello. Clock-set failure, DNS failure, timeout or a rejected response fails that connection setup. Recovery follows the setup's owner: 60-second Idle recovery under P26, or P13 retries during delivery. No SNTP-specific retry, gap or attempt cap applies.

Start cancels DNS or exchange work before audio begins. Ignore a completion racing with Start unless it was accepted/applied before CONTROL withdrew the lease. Cancellation is not a failure.

A failed cancellation is a resource-release fault, not merely unavailable time. Follow the P23 Wi-Fi cleanup outcome under REQ-13: latch `WIFI_CLEANUP_FAILURE`, disable network work until restart and release audio. Record the failed operation and never claim quiescence. Later L1_WIFI implementation work must demonstrate cancellation bounds; a blocking helper or forced worker abort is not a substitute.

## Clock mapping and native behavior

Enable `CONFIG_SNTP_UNCERTAINTY` and retain Zephyr's estimate [2]. It estimates exchange/server uncertainty; it does not authenticate the source or independently bound subsequent clock drift and software latency. The [drift calculation](../../planning/mvp-decisions-2026-11-02.md#drift-calculation) derives that limit from the datasheet crystal tolerance of ±10 ppm with safety factor 2 and the 1 s maximum deviation below. It is a calculation, not a measured accuracy claim.

Set Zephyr's real-time software clock; no battery-backed RTC is assumed. Advance the receive-time estimate by elapsed kernel monotonic time before applying it. Keep the applied UTC/monotonic anchor and record the measurement end in monotonic time. Corrections occur outside listening and may step real time without changing duration or rewriting a frozen result.

Map the measurement end to UTC only from a qualifying anchor: the monotonic distance between anchor and measurement end is at most 12.5 hours. The limit is (1 s − 100 ms) / 20 ppm: 1 second maximum deviation, a 100 ms SNTP uncertainty budget (observed about 50 ms × safety factor 2) and 20 ppm drift (datasheet ±10 ppm × safety factor 2). An exchange that reports more than 100 ms uncertainty does not fit the budget and fails like any other exchange. The 1 second maximum deviation follows the Consistent Time profile of IHE (Integrating the Healthcare Enterprise), which requires a median error of less than one second and names SNTP sufficient for it [5]; FHIR, the HAPI FHIR server and TLS give no tighter limit. If the anchor held at Stop qualifies, freeze the UTC end at Stop. Otherwise, for example after a long Idle period without a new setup, freeze it from the anchor applied by the delivery connection setup, before the first request. The UTC end and measurement identity are frozen exactly once; retries, later exchanges and backward corrections never change them. The existing uniqueness rule remains mandatory; never invent a timestamp to avoid a collision.

A result without a qualifying anchor by the end of the P13 budget is not sent and latches `SERVER_CONNECTION_FAILURE`. No delayed delivery queue is introduced. A retained connection is reused for delivery only while the anchor of its handshake qualifies; otherwise delivery opens a new setup with a fresh exchange.

Pinned-source caveat [2]: the uncertainty-enabled parser assigns `fraction` as a microsecond remainder, unlike the binary fraction on the ordinary path. The header calls `uptime_us` uptime, but the implementation derives it from real-time/NTP-epoch timestamps. WIFI must normalize the pinned units and independently sample kernel monotonic time rather than cast these fields or treat native `uptime_us` as kernel uptime. Verify unset initial time, subsecond carry and conversion before L1_WIFI acceptance. Recheck these semantics on a Zephyr revision change. This PR contains no upstream patch.

Reject a response from an unsynchronized server before normalization: a leap indicator of 3 (alarm condition, clock not synchronized) or a stratum outside 1–15 (0 is kiss-o'-death or unspecified, 16–255 reserved) [3]. The pinned parser rejects only stratum 0 and returns neither field [2], so WIFI must check both on the received packet. A rejected response fails the containing connection setup like any other failed exchange; the reported uncertainty never overrides this check.

## Failure indication and acknowledgement

There is no separate time-synchronization error. A failed exchange is a failed secure connection setup and follows the [TLS failure indication](secure-transport.md#failure-indication): `SERVER_CONNECTION_FAILURE`, blue with 1 blink, with offline Start/listening preserved. The same code marks a result that cannot be sent for lack of a qualifying anchor. Diagnostics name the time cause, anchor age and estimate, never credentials or patient context. The running examination wins: no time work and no time indication occur during listening.

## Parameters

| ID | Value / meaning |
| --- | --- |
| P25-SERVER | `pool.ntp.org`, IPv4 DNS and SNTP over UDP/123 |
| P25-PLACEMENT | One exchange directly before every ClientHello; none for a reused connection; no separate schedule |
| P25-BUDGET | Shares the containing setup deadline (P26 Idle preparation or P13 connection setup); separate existing one-second per-service cancellation bound |
| P25-MAPPING | Anchor qualifies within 12.5 hours of the measurement end: (1 s − 100 ms) / 20 ppm |
| P25-UNCERTAINTY-BUDGET | 100 ms: observed about 50 ms (15 ms and 53 ms) × safety factor 2; a larger reported uncertainty fails the exchange |
| P25-MAXIMUM-DEVIATION | 1 s, after the IHE Consistent Time profile |
| P25-DRIFT | Datasheet ±10 ppm × safety factor 2 = 20 ppm |
| P25-UNCERTAINTY | Zephyr `CONFIG_SNTP_UNCERTAINTY`; microseconds internally; no measured accuracy guarantee |

## Limitations and verification

The initial source requires usable DNS and reachable public UDP/123; Wi-Fi alone does not supply time. A fallback to a local time server is deferred to [GitHub #85](https://github.com/DemonicPsychoII/DigitalStethoscope/issues/85) / [TICKET-212](https://nfrie.atlassian.net/browse/TICKET-212), local SNTP time on networks without internet access. Unauthenticated SNTP is accepted for this minimum viable product (MVP) [1,3]; no authenticated-time claim follows. [GitHub #88](https://github.com/DemonicPsychoII/DigitalStethoscope/issues/88) / TICKET-209, choosing the clock reference and timestamp accuracy, retains the reference-comparison and accuracy evidence.

| Scenario | Trace | Expected result |
| --- | --- | --- |
| Boot and successful exchange | REQ-09/11; VT-07/08 | No persisted ready clock; the first TLS setup applies the UTC/monotonic anchor before its ClientHello. |
| DNS failure, blocked UDP, rejected response (including leap indicator 3 or stratum outside 1–15) | REQ-09/13; VT-08/09 | The containing connection setup fails within its deadline and follows P26 or P13 recovery; `SERVER_CONNECTION_FAILURE` without blocking listening. |
| Start during DNS/wait/completion race | REQ-02/13; VT-08/09 | Quiesce before audio; stale completion cannot apply time; cancellation raises no time-sync error. |
| Mapping limit and long Idle period | REQ-09/10/13; VT-07/08/09 | A qualifying anchor freezes the end at Stop; otherwise the delivery setup anchor freezes it; no qualifying anchor sends nothing and latches `SERVER_CONNECTION_FAILURE`. |
| Correction and frozen measurement | REQ-09/10; VT-07 | Monotonic duration and frozen UTC/identity stay unchanged across retries and later exchanges; no delayed resend. |
| Native units, unset time, subsecond carry | REQ-09/11; VT-07/08 | Consistent UTC conversion and independently sampled monotonic anchor. |
| Cleanup fault | REQ-13/14; VT-08/09/11 | Failed cancellation latches `WIFI_CLEANUP_FAILURE`, disables network work and releases audio without reporting quiescence. |

These allocate future verification, not generated tests or execution. DNS/socket integration, target cancellation latency, drift/reference comparison and audio interference remain pending. Timestamp acceptance evidence is not replaced by a reported estimate.

## Sources

[1] Nico, *SNTP detailed-design decisions*, personal communication, T3 Code, 28 October 2026, [conversation](t3-thread://v2/d5e44f69-2ecc-4a3e-917b-31a7b084c12b/576e10df-527c-41cc-86cd-4e7c0ff0c290), accessed 28 October 2026. Numbered grilling answers establish source/trust, uncertainty, cancellation, timing and failure-indication choices; project decisions, not measurements.

[2] The Zephyr Project, *SNTP API, Kconfig, implementation and DNS resolver API*, Zephyr source repository revision `357467a011cd2557a1a3f0b4be83d817c4addc9b`, publication year unverified; [SNTP header](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/include/zephyr/net/sntp.h), [Kconfig](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/subsys/net/lib/sntp/Kconfig), [parser](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/subsys/net/lib/sntp/sntp.c), [helper](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/subsys/net/lib/sntp/sntp_simple.c), [DNS header](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/include/zephyr/net/dns_resolve.h), accessed 28 October 2026. The convenience helper resolves before its exchange timeout and resends internally; split DNS/SNTP APIs underpin the proposed cancellable adapter. Target behavior remains unverified.

[3] David L. Mills, *Simple Network Time Protocol (SNTP) Version 4 for IPv4, IPv6 and OSI*, IETF RFC 4330, January 2006, sections 4, 5 and 9, DOI: 10.17487/RFC4330, <https://www.rfc-editor.org/rfc/rfc4330#section-9>. Access recorded 24 October 2026 in the [source register](../../../../thesis-material/quellen.md#ietf_sntp_4330_2006); no new access claimed.

[4] Andreas Summerer and Nico, *Design review of time, TLS and FHIR*, review meeting, 2 November 2026, with Nico's resolutions in the [decision record](../../planning/mvp-decisions-2026-11-02.md), accessed 2 November 2026. Project decisions; the drift figure is a datasheet calculation, not a measurement.

[5] IHE International, *IHE IT Infrastructure (ITI) Technical Framework, Volume 1, section 7 Consistent Time (CT)* and *Volume 2, section 3.1.4.1.2 Maintain Time [ITI-1]*, Revision 20.0, Final Text, 4 August 2023, <https://profiles.ihe.net/ITI/TF/Volume1/ch-7.html> and <https://profiles.ihe.net/ITI/TF/Volume2/ITI-1.html>, accessed 2 November 2026. The profile states a median error; using 1 s as a worst-case bound is a project decision.
