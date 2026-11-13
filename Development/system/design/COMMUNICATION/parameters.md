# COMMUNICATION parameters

Selected workflow values. Radio operation limits are allocated in WIFI; HTTP/page limits are allocated in PORTAL. Target timing and radio/audio interference require device evidence.

| ID | Parameter | Value / candidate | Verification status | Owners |
| --- | --- | --- | --- | --- |
| P19 | Network exclusion | No active setup/reconnect/time-sync/TLS/HTTP jobs during listening/measurement; retain existing station association; Start cancels setup before audio | Radio interference and safe teardown require target evidence | NET,CTL |
| P21-COMMUNICATION | Setup entry and inactivity (allocation of P21) | Boot without usable credentials or 2 s hold in Idle; 5 min inactivity; actions pause it, selection/input/Rescan reset it, status polling does not | Project workflow choice | COMMUNICATION,CONTROL |
| P23 | Wi-Fi retry / exit | Boot/reconnect/scan 4 attempts total, 5 s between failures; portal join 1; save 2; AP start manual; success/save warning 10 s, Cancel/timeout notice then teardown; connect budget 15 s, scan 10 s, link check 2 min, close notice 2 s, scan list 16; cleanup: one stop try per pending service of the seven in [cleanup limits](#cleanup-limits-p23), each bounded to 1 s; cleanup pass capped at 5 s (largest set pending together: 5); delivery cleanup reserve 1 s (at most one service pending during a delivery attempt); on a failed stop latch WIFI_CLEANUP_FAILURE, disable network work until restart, release audio under REQ-13; scan-cancel and disconnect-confirmation waits 1 s each; HTTP server-start readiness and stop confirmation 1 s each | 200 ms event-check intervals are not total teardown bounds; DHCP and hotspot stops have no explicit 1 s limit in code at 994ce24; target verification remains open | COMMUNICATION,CONTROL |

P23 owns the retry, result-display, close-notice and cleanup limits. Its radio wait/cache limits are allocated to P23-WIFI and HTTP readiness/stop limits to P24. A 200 ms event-check interval is not a total teardown latency guarantee.

## Cleanup limits (P23)

L2_COMMUNICATION tracks seven stoppable services (`COMMUNICATION_WORK_*` in `communication.c`, integration `994ce24`) and stops them in this order. Each stop is tried once per cleanup pass and bounded to 1 s.

| Group | Service | Stop | Stop bound in code at `994ce24` |
| --- | --- | --- | --- |
| Network work | Time synchronization (SNTP) | `wifi_cancelTimeSynchronization` | 1 s |
| Network work | Secure connection: TLS setup or HTTP exchange | `wifi_cancelSecureConnection`, then `wifi_closeSecureConnection` | 1 s for the cancel; the close sends one non-blocking `close_notify` |
| Setup | Scan | `wifi_cancelScan` | 1 s wait for scan end |
| Setup | Connect request | `wifi_disconnect` | 1 s wait for disconnect confirmation |
| Setup | Setup page (HTTP server) | `portal_stop` | 1 s wait for stop confirmation |
| Setup | DHCP server | `wifi_stopDHCPServer` | synchronous driver call, no explicit limit |
| Setup | Hotspot | `wifi_stopHotspot` | synchronous driver call, no explicit limit |

Which services can be pending together follows from the single worker thread:

- **Network work.** Time synchronization and secure connection run one after the other inside one connection setup, so at most one of them is pending. A failed cancellation latches WIFI_CLEANUP_FAILURE at once and ends all further network work. Network work never overlaps setup: setup closes all its services before Idle preparation starts.
- **Setup.** Hotspot, DHCP server and setup page stay pending while the page is served. The worker runs one scan or one join at a time. A connect request whose disconnect failed stays pending, and setup then rescans; so the largest set pending together is five: three setup services, the scan and the connect request.
- **Cleanup pass cap: 5 s** = 5 services × 1 s. The interrupted operation is first cancelled once in-line under its own 1 s bound. A scan or connect request whose in-line cancellation failed gets its one try in the cleanup pass. A failed network-work cancellation has already latched the fault, so the pass skips it.
- **Delivery cleanup reserve: 1 s.** A delivery attempt has at most one service pending, time synchronization or secure connection, so one stop bound suffices. This matches the fixed `COMMUNICATION_DELIVERY_CLEANUP_RESERVE_MS` of the code and the P13 reserve of one stop bound per pending service.

A failed stop latches WIFI_CLEANUP_FAILURE, disables network work until restart and releases audio under REQ-13 without claiming that the radio is off. The [network-to-audio handover](interfaces-and-behavior.md#listening-priority-and-safe-teardown) shows the sequence.

## Retry conventions

L2_COMMUNICATION owns workflow retry scheduling. Attempt 1 is the first request that is actually issued. The gap before a retry starts when the failed attempt has completed and is measured in monotonic time. Each retry policy states its attempt deadline, its gap, its total attempt cap or ongoing-recovery behavior, and its terminal outcomes. These shared conventions do not impose common numbers: Wi-Fi keeps the Wi-Fi retry and limit values of [P23](#communication-parameters), and delivery keeps the delivery timeout and retry values of [P13](../system/parameters.md). The L1 services, such as L1_WIFI, L1_PORTAL, L1_STORAGE and L1_FHIR, add no workflow retries of their own.

Every timing value is derived from a measured typical duration and a stated safety factor; the evidence records both. Until target measurements exist (planned in Jira [TICKET-213](https://nfrie.atlassian.net/browse/TICKET-213), measuring TLS reconnect timing and connection survival on the target), the current values are provisional project decisions. Attempt caps are fixed counts: P13 allows four delivery attempts in total. No extra rule applies when its deadline leaves time for only two of them.

The [P25 SNTP parameters](time-synchronization.md#parameters) (Simple Network Time Protocol) place one time exchange directly before every ClientHello, the first message of a TLS handshake. The exchange runs inside the deadline of the connection setup that contains it. A measurement end is converted to UTC only from a clock anchor, the point at which the clock was last set, that lies at most 12.5 hours away. That limit is the 1 s maximum deviation minus a 100 ms uncertainty budget, divided by a drift of 20 ppm. It rests on a datasheet drift calculation, not on a measured drift bound.

The [P26 TLS parameters](secure-transport.md#parameters) select TLS 1.3 only. They take one server endpoint and its public server certificate from the server profile image, which is flashed separately from the firmware. In Idle, one connection setup, including its SNTP exchange, may take ten seconds; after a failure, preparation is tried again 60 seconds later, without a total attempt cap. Delivery reconnects use the P13 limits instead: three seconds for connection setup and one second for writing the request and receiving the receipt, within ten seconds from Stop in total. Delivery connection setup starts when CONTROL submits the finalized job, not at Stop. A retained connection is reused only while its idle time is below the device keep-alive timeout, which is set below the server's keep-alive timeout. The retry conventions above apply. A missing prerequisite, such as a missing station address, uses up no attempt. The timing values are project decisions pending target evidence.

The [P27 server parameters](server-communication.md#parameters-and-outstanding-evidence) define the stable physical device identifier derived from the factory MAC address, the Device registration record bound to one server, and ten-second registration attempts. In Idle, a failed registration is tried again after 60 seconds; the gap doubles with each further failure, and after 4 failed attempts registration stays unavailable until restart. These preparation budgets do not replace the P13 delivery deadlines. The retry conventions above apply. Record and buffer limits are proposed design values pending target evidence.
