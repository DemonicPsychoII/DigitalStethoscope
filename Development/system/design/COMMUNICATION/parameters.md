# COMMUNICATION parameters

Selected workflow values. Radio operation limits are allocated in WIFI; HTTP/page limits are allocated in PORTAL. Target timing and radio/audio interference require device evidence.

| ID | Parameter | Value / candidate | Verification status | Owners |
| --- | --- | --- | --- | --- |
| P19 | Network exclusion | No active setup/reconnect/time-sync/TLS/HTTP jobs during listening/measurement; retain existing station association; Start cancels setup before audio | Radio interference and safe teardown require target evidence | NET,CTL |
| P21-COMMUNICATION | Setup entry and inactivity (allocation of P21) | Boot without usable credentials or 2 s hold in Idle; 5 min inactivity; actions pause it, selection/input/Rescan reset it, status polling does not | Project workflow choice | COMMUNICATION,CONTROL |
| P23 | Wi-Fi retry / exit | Boot/reconnect/scan 4 attempts total, 5 s between failures; portal join 1; save 2; AP start manual; success/save warning 10 s, Cancel/timeout notice then teardown; connect budget 15 s, scan 10 s, link check 2 min, close notice 2 s, scan list 16; cleanup: one stop try per pending service, each bounded to 1 s, total cap 5 s for 5 services; on a failed stop latch WIFI_CLEANUP_FAILURE, disable network work until restart, release audio under REQ-13; scan-cancel and disconnect-confirmation waits 1 s each; HTTP server-start readiness and stop confirmation 1 s each | 200 ms event-check intervals are not total teardown bounds; target verification remains open | COMMUNICATION,CONTROL |

P23 owns the retry, result-display, close-notice and cleanup limits. Its radio wait/cache limits are allocated to P23-WIFI and HTTP readiness/stop limits to P24. A 200 ms event-check interval is not a total teardown latency guarantee.

## Retry conventions

COMMUNICATION owns workflow retry scheduling. Attempt 1 is the initial issued request; retry gaps run from failure completion using monotonic time. Each policy specifies its attempt deadline, gap, total cap or ongoing-recovery behavior, and terminal outcomes. Shared conventions do not impose common numbers: retain P23 for Wi-Fi and P13 for delivery. Lower services do not add workflow retries.

[P25 SNTP parameters](time-synchronization.md#parameters) specify a five-second attempt, 60-second ongoing recovery while Idle, 15-minute refresh and one-hour expiry. These are owner-selected project settings, not Zephyr defaults or measured drift bounds.

[P26 TLS parameters](secure-transport.md#parameters) select TLS 1.3 only, a build-embedded public server certificate, ten-second Idle preparation and ongoing 60-second recovery gaps. Delivery reconnects use P13's three-second connection-setup and one-second write-and-receipt limits within ten seconds total; a device keep-alive timeout below the server's bounds connection reuse. The retry conventions above apply. Missing prerequisites consume no attempt. Timing values are project decisions pending target evidence.

[P27 server parameters](server-communication.md#parameters-and-outstanding-evidence) define stable physical identity, the server-bound registration record and ten-second registration attempts with 60-second Idle recovery gaps. These preparation budgets do not replace P13 delivery deadlines. The retry conventions above apply. Record and buffer limits are proposed design values pending target evidence.
