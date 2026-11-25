# COMMUNICATION setup workflow and recovery

L2_COMMUNICATION owns setup sequencing and retry policy under L2_CONTROL's network lease. It uses [L1_WIFI operations](../WIFI/interfaces-and-behavior.md), the [L1_STORAGE record interface](../STORAGE/interfaces-and-behavior.md) and the [L1_PORTAL request/status boundary](../PORTAL/interfaces-and-behavior.md).

## Wi-Fi setup and recovery

The [state diagram](../../architecture/COMMUNICATION/puml/setup-state.puml),
[setup flow](../../architecture/COMMUNICATION/puml/setup-flow.puml) and
[recovery flow](../../architecture/COMMUNICATION/puml/link-recovery.puml) share the rules below.

### Entry, scan and recovery

L1_WIFI lists only supported networks: open networks and WPA2-PSK. It filters out WPA1, WPA2-SHA256 and WPA3/SAE scan results rather than joining them with a mismatched security type. Its scan cache keeps the 16 strongest distinct supported SSIDs, matching the scan list limit of the [P23 Wi-Fi retry and limit parameters](parameters.md). L2_COMMUNICATION passes this list to the setup page.

L2_COMMUNICATION initializes L1_STORAGE with `storage_init()` before any boot record read. If initialization fails, L2_COMMUNICATION treats the record as unavailable and opens setup without joining from failed-read output. L2_COMMUNICATION reads settings through L1_STORAGE. At boot, L2_COMMUNICATION joins a stored network with four attempts in total, 5 s between failures. Exhausting these attempts shows an error and waits for a 2 s button hold in Idle. Without credentials, or on a 2 s hold in Idle, L2_COMMUNICATION scans and caches nearby networks first, then opens the hotspot and serves one HTML document. L2_COMMUNICATION rescans on an explicit request or after a failed portal join. It keeps the hotspot and HTTP server open during these rescans and publishes the cache only after the scan finishes. Scanning has four attempts in total, 5 s between failures. An exhausted scan or a hotspot-start failure permits a manual 2 s setup retry. Link loss triggers four reconnect attempts, 5 s apart. Exhausting link-loss reconnect attempts starts setup automatically in Idle. L2_COMMUNICATION defers all active recovery during listening.

The [L1_PORTAL interface](../PORTAL/interfaces-and-behavior.md) queues typed requests for L2_COMMUNICATION and publishes its status. The hotspot is open. The operator's phone, or any other device with Wi-Fi and a browser, joins it manually and opens the setup page without pairing with the stethoscope. Its name is `Stetho-AABBCCDDEEFF`, using all six station MAC bytes in upper-case hexadecimal so devices in one room stay distinguishable.

### Join, persistence and result closure

One portal join attempt waits for the selected network's address. A stale existing link does not count as a successful new join. On failure, L2_COMMUNICATION shows the cause, rescans and returns to network selection. On success, L2_COMMUNICATION saves the network under the `wifi/network` key in L1_STORAGE with `storage_write()` and retries saving once on failure. A failed save preserves the previous valid record. L2_COMMUNICATION shows the success status or save warning for 10 s together with the station IPv4 address from `wifi_getAddress()`. Before teardown on every setup exit, including result or save-warning completion and Start, L2_COMMUNICATION publishes the Closing status. Only Cancel, inactivity and scan failure add the 2 s closing-notice delay. L2_COMMUNICATION then closes the hotspot and HTTP server while keeping the station connection, including when credentials were not saved. At boot, L2_COMMUNICATION reads the `wifi/network` record with `storage_read()` and validates it with `wifi_isValidNetwork()`. L2_COMMUNICATION owns workflow policy.

### Cancellation and inactivity

The shared setup contract accepts form Back/Cancel only before Connect submission. Setup Cancel ends setup. Connect through save and automatic closure cannot be cancelled by the user. The inactivity timeout is 5 min; selection, password input and Rescan reset it, status polling does not, and operations pause it. L2_COMMUNICATION sends a 2 s closing notice before teardown; Cancel and timeout do not add the 10 s result display.

L2_COMMUNICATION retains an established station connection; otherwise it cancels active attempts and releases Wi-Fi services. Software errors that prevent continuing setup log and show the cause, clean up and return to offline operation. The user can start the Wi-Fi setup workflow again by holding the button for 2 s in Idle.

### Listening priority and safe teardown

![Network-to-audio handover sequence](rendered/network_audio_handover.svg)

*When may audio start after Start?* Source: [puml/network-audio-handover.puml](puml/network-audio-handover.puml). The [L2_COMMUNICATION lifecycle](../../architecture/COMMUNICATION/puml/communication-lifecycle.puml) ([SVG](../../architecture/COMMUNICATION/rendered/communication_lifecycle.svg)) places this handover between Idle network work and listening.

Cancellation is serialized against join completion. The stop bounds are the [P23 cleanup limits](parameters.md#cleanup-limits-p23). L2_COMMUNICATION checks for control events every 200 ms while waiting. Setup, reconnect and delivery work are prohibited during listening.

### Specified failures and interrupted boot

If the network list cannot be refreshed while the setup page is open, the device reports SCAN_FAILURE, shows Closing and ends setup. An existing Wi-Fi connection stays up. Setup restarts with a new 2 s button hold in Idle. The IPv4 address event confirms the join, so the network is saved before the address text is read for the page. If that text cannot be read, the join still counts and the page shows no address. An unreadable or invalid stored record is cleared from working memory, never used for a join, and opens initial setup; the flash content is preserved for diagnosis until a valid save. A `portal_start()` failure independently reports HOTSPOT_START_FAILURE with the HTTP cause, tears down any partially started services and waits for the manual setup hold.

Start interrupts a boot join by cancelling its active attempt. On return to Idle, L2_COMMUNICATION resumes the remaining boot attempts after the normal retry gap. The interrupted issued attempt counts toward the four-attempt boot budget; cancellation before issuing an attempt consumes none. Boot exhaustion remains JOIN_FAILURE with manual setup; it never becomes link-loss recovery or automatic setup.

An interrupted or timed-out scan or join is cancelled once when it ends. Cleanup then tries each stop that is still pending once, in the order of the [P23 cleanup limits](parameters.md#cleanup-limits-p23): time synchronization, secure connection, scan, connect request, setup page (HTTP), DHCP and hotspot. If all stops succeed, audio is released normally. If any stop fails, L2_COMMUNICATION latches `WIFI_CLEANUP_FAILURE` (cleared only by restart; indication follows the feedback catalogue), disables further Wi-Fi work until restart and releases audio under [REQ-13](../../requirements/system-requirements.md#req-13)'s Wi-Fi-only exception. L2_COMMUNICATION records the failed stop operations and reports the cleanup fault to L2_CONTROL through the feedback event boundary.
