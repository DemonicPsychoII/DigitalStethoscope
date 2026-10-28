# VT-14 production service integration

The batch compiles the real COMMUNICATION L2 workflow together with WIFI, PORTAL
and STORAGE L1 services. No L1 service function is replaced. The test harness
includes the production units to inspect state without adding firmware hooks;
kernel scheduling/time, Wi-Fi/net management, IPv4/DHCP, HTTP listener/callbacks and
settings APIs form the substituted Zephyr boundary. Each process starts fresh.

The shared `service_boundary.c` is also used by the L1 unit tests. Its station
states distinguish Idle, Connecting and Connected. Scan completion is asynchronous;
there is no fabricated scan-abort API. Disconnect while Connecting emits a failed
CONNECT_RESULT; disconnect after association emits DISCONNECT_RESULT. A settings
callback reads the whole record and save failures preserve the previous record.
Those rules follow the pinned source below. The scheduler wakes semaphores for
posted events and advances simulated time; locks do not provide real concurrency.

| Scenario | Observable contract |
| --- | --- |
| Stored boot | Real settings read joins once without opening setup or rewriting flash. |
| Open / WPA2-PSK form | Real scan filtering lists one supported strongest network; HTTP form reaches L2, address precedes real settings save and result closure keeps the station. |
| Save failure | Two failed real storage writes preserve the old record and keep the new station association after page closure. |
| Join failure | Driver wrong-password result reaches L2 and the portal; a completed rescan restores selection without saving. |
| Invalid form | Real portal validation returns 400 and no join/save is issued. |
| Start / Cancel | Typed portal/control input reaches L2 and closes the real services; Start releases audio. |
| Refresh exhaustion | Four failed refresh attempts close setup with Closing, preserving the established station and requiring a new setup hold. |

Production line/branch coverage and the JUnit scenario traces are retained by the
host CI job. No L2 case is marked XFAIL at this head. The address, Closing, cleanup and
record-erasure cases are ordinary passing cases, and these integration checks do
not change their status. Real HTTP sockets/routing, concurrent callbacks,
physical timing, flash atomicity across power loss and radio behavior require
the identified device procedures and Nico's signed run.

Boundary source: Zephyr Project contributors, *Zephyr RTOS source*, revision
`357467a011cd2557a1a3f0b4be83d817c4addc9b` (the project's pinned development
revision; release year/version otherwise unverified), Linux Foundation/Zephyr
Project, inspected 24 October 2026:

- [ESP32 driver](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/drivers/wifi/esp32/src/esp_wifi_drv.c), `scan_done_handler`, `esp_wifi_handle_sta_disconnect_event`, `esp32_wifi_disconnect`.
- [HTTP server API](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/include/zephyr/net/http/server.h), response headers and transaction callback lifecycle.
- [HTTP/1 router](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/subsys/net/lib/http/http_server_http1.c), resource-path and supported-method rejection. Host routing tests model this boundary and verify the production registrations; they do not execute the router.

Created by GPT-6.1-Sol on behalf of Nico running in codex.
