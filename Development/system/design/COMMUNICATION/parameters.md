# COMMUNICATION parameters

Selected workflow values. Radio operation limits are allocated in WIFI; HTTP/page limits are allocated in PORTAL. Target timing and radio/audio interference require device evidence.

| ID | Parameter | Value / candidate | Verification status | Owners |
| --- | --- | --- | --- | --- |
| P19 | Network exclusion | No active setup/reconnect/time-sync/TLS/HTTP jobs during listening/measurement; retain existing station association; Start cancels setup before audio | Radio interference and safe teardown require target evidence | NET,CTL |
| P21-COMMUNICATION | Setup entry and inactivity (allocation of P21) | Boot without usable credentials or 2 s hold in Idle; 5 min inactivity; actions pause it, selection/input/Rescan reset it, status polling does not | Project workflow choice | COMMUNICATION,CONTROL |
| P23 | Wi-Fi retry / exit | Boot/reconnect/scan 4 attempts total, 5 s between failures; portal join 1; save 2; AP start manual; success/save warning 10 s, Cancel/timeout notice then teardown | Connect budget 15 s, scan 10 s, link check 2 min, close notice 2 s, scan list 16; cleanup: at most 3 stop passes, 1 s then 2 s backoff, each stop bounded to 1 s, total cap 18 s including 5 services; on exhaustion latch WIFI_CLEANUP_FAILURE, disable network work until restart, release audio under REQ-13; scan-cancel and disconnect-confirmation waits 1 s each; HTTP server-start readiness and stop confirmation 1 s each; 200 ms event-check intervals are not total teardown bounds; target verification remains open | COMMUNICATION,CONTROL |

P23 owns the retry, result-display, close-notice and cleanup budgets. Its radio wait/cache limits are allocated to P23-WIFI and HTTP readiness/stop limits to P24. A 200 ms event-check interval is not a total teardown latency guarantee.
