# COMMUNICATION parameters

L2_COMMUNICATION workflow parameters are defined below. Radio operation limits are allocated in L1_WIFI, and HTTP and page limits are allocated in L1_PORTAL.

| ID | Parameter | Value | Owners |
| --- | --- | --- | --- |
| P19 | Network exclusion | No active setup, reconnect, time-sync, TLS or HTTP jobs during listening or measurement; existing station association is retained; Start cancels setup before audio | L2_COMMUNICATION, L2_CONTROL |
| P21-COMMUNICATION | Setup entry and inactivity | Boot without usable credentials or 2 s hold in Idle; 5 min inactivity; actions pause it, selection/input/Rescan reset it, status polling does not | L2_COMMUNICATION, L2_CONTROL |
| P23 | Wi-Fi retry / exit | Boot/reconnect/scan 4 attempts total, 5 s between failures; portal join 1; save 2; hotspot start manual; success/save warning 10 s, Cancel/timeout notice then teardown; connect budget 15 s, scan 10 s, link check 2 min, close notice 2 s, scan list 16, event-check interval 200 ms; cleanup: one stop try per pending service of the seven in [cleanup limits](#cleanup-limits-p23), each bounded to 1 s; at most five are pending together, so a cleanup pass takes at most 5 s; a delivery attempt reserves 1 s; on a failed stop, L2_COMMUNICATION latches WIFI_CLEANUP_FAILURE, disables network work until restart and releases audio under REQ-13; scan-cancel and disconnect-confirmation waits 1 s each; HTTP server-start readiness and stop confirmation 1 s each | L2_COMMUNICATION, L2_CONTROL |

P23 owns the retry, result-display, close-notice and cleanup limits. Its radio wait and cache limits are allocated to P23-WIFI, and its HTTP readiness and stop limits are allocated to P24.

## Cleanup limits (P23)

L2_COMMUNICATION tracks seven stoppable services and stops them in this order. Each stop is tried once per cleanup pass and bounded to 1 s.

| Group | Service | Stop |
| --- | --- | --- |
| Network work | Time synchronization (SNTP) | Cancel the exchange |
| Network work | Secure connection: TLS setup or HTTP exchange | Cancel, then close the connection |
| Setup | Scan | Cancel and wait for the scan end |
| Setup | Connect request | Disconnect and wait for the confirmation |
| Setup | Setup page (HTTP server) | Stop and wait for the confirmation |
| Setup | DHCP server | Stop |
| Setup | Hotspot | Stop |

Which services can be pending together follows from the single worker thread:

- **Network work.** Time synchronization and secure connection run one after the other inside one connection setup, so at most one of them is pending. Network work never overlaps setup: setup closes all its services before Idle preparation starts.
- **Setup.** Hotspot, DHCP server and setup page stay pending while the page is served, and the worker runs one scan or one join at a time. A connect request whose disconnect failed stays pending while setup rescans, so the largest set pending together is five.
- **Cleanup pass: at most 5 s** = 5 services × 1 s.
- **Delivery cleanup reserve: 1 s.** A delivery attempt has at most one service pending, so the P13 reserve of one stop bound per pending service is 1 s.

A failed stop latches WIFI_CLEANUP_FAILURE, disables network work until restart and releases audio under REQ-13.

## Retry conventions

L2_COMMUNICATION owns workflow retry scheduling. Attempt 1 is the first issued request. The gap before a retry starts when the failed attempt completes and is measured in monotonic time. Each retry policy defines its attempt deadline, its gap, its total attempt cap or ongoing-recovery behavior, and its terminal outcomes. Wi-Fi operations use the retry and limit values of P23 above, and delivery uses the timeout and retry values of [P13](../system/parameters.md). L1_WIFI, L1_PORTAL, L1_STORAGE and L1_FHIR add no workflow retries.

Attempt caps are fixed counts. P13 allows at most four delivery attempts in total; fewer attempts run when the global deadline expires first.

The [P25 SNTP parameters](time-synchronization.md#parameters) (Simple Network Time Protocol) place one time exchange directly before every ClientHello, the first message of a TLS handshake. The exchange runs inside the deadline of the connection setup that contains it. A measurement end is converted to UTC only from a clock anchor (the point at which the clock was last set) that lies at most 12.5 hours away. That limit is the 1 s maximum deviation minus a 100 ms uncertainty budget, divided by a 20 ppm drift budget derived from the crystal datasheet tolerance.

The [P26 TLS parameters](secure-transport.md#parameters) select TLS 1.3 only. They take one server endpoint and its public server certificate from the server profile image, which is flashed separately from the firmware. In Idle, one connection setup, including its SNTP exchange, has a ten-second deadline. After a failure, preparation retries 60 seconds later without a total attempt cap. Delivery reconnects use the P13 limits: three seconds for connection setup and one second for writing the request and receiving the receipt, within ten seconds from Stop in total. Delivery connection setup starts when L2_CONTROL submits the finalized job rather than at Stop. A retained connection is reused only while its idle time is below the device keep-alive timeout, which is set below the server's keep-alive timeout. The retry conventions above apply. A missing prerequisite, such as a missing station address, consumes no attempt.

The [P27 server parameters](server-communication.md#parameters) define the stable physical device identifier derived from the factory MAC address, the Device registration record bound to one server, and ten-second registration attempts. In Idle, a failed registration retries after 60 seconds. The retry gap doubles with each further failure, and after 4 failed attempts registration remains unavailable until restart. These preparation budgets are separate from the P13 delivery deadlines. The retry conventions above apply.
