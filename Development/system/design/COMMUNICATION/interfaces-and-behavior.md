# COMMUNICATION setup workflow and recovery

L2_COMMUNICATION owns setup sequencing and retry policy under CONTROL's network lease. It uses [WIFI operations](../WIFI/interfaces-and-behavior.md), the [STORAGE record interface](../STORAGE/interfaces-and-behavior.md) and the PORTAL request/status boundary.

## Wi-Fi setup and recovery

The [state diagram](../../architecture/COMMUNICATION/setup-state.puml),
[setup flow](../../architecture/COMMUNICATION/setup-flow.puml) and
[recovery flow](../../architecture/COMMUNICATION/link-recovery.puml) share the rules below.

### Entry, scan and recovery

Only supported networks are listed and offered: open networks and WPA2-PSK. WPA1, WPA2-SHA256 and WPA3/SAE scan results are filtered rather than joined with a mismatched security type; support for WPA3 and WPA2-SHA256 is TICKET-200. Keep the strongest distinct SSIDs within the P23 cache limit.

Initialize L1_STORAGE with `storage_init()` before any boot record read. If initialization fails, treat the record as unavailable and open setup; never join using failed-read output. Read settings through L1. At boot, join a stored network with four attempts total,
5 s between failures. Exhaustion shows an error and waits for a 2 s hold in Idle.
Without credentials, or on a 2 s hold in Idle, scan/cache first, then open the AP
and serve one HTML document. Rescan explicitly or after a failed portal join;
keep AP/server open for these rescans and publish the cache only after scan-finished.
Scan has four attempts total, 5 s between failures. Exhausted scan or AP-start failure
permits a manual 2 s setup retry. Link loss has four reconnect attempts, 5 s apart;
exhaustion starts setup automatically in Idle. Defer all active recovery during listening.

The portal interface queues typed requests for COMMUNICATION and publishes its status. The hotspot is open; the phone joins it manually before opening the page.

### Join, persistence and result closure

One portal join attempt waits for the selected network's
address. A stale existing link is not a successful new join. On failure show the
cause, rescan and return to selection. On success save the network as the
`wifi/network` record with `storage_write()` in `L1_STORAGE`; retry saving once.
Preserve the old valid record on failure. Show success or save warning, with the
station IPv4 address from `wifi_getAddress()`, for 10 s. Publish Closing before teardown on every setup exit, including result/save-warning completion and Start; only Cancel, inactivity and scan failure add the 2 s closing-notice delay. Then close AP/server and keep
the station, including with unsaved credentials. At boot L2 reads the record with
`storage_read()` and checks it with `wifi_isValidNetwork()`; L2 owns workflow policy.

### Cancellation and inactivity

The shared setup contract accepts form Back/Cancel only before Connect submission. Setup Cancel ends setup. Connect through save and automatic closure cannot be cancelled by the user. The inactivity timeout is 5 min; selection, password input and Rescan reset it, status polling does not, and operations pause it. Send a 2 s closing notice before teardown; Cancel and timeout do not add the 10 s result display.

Retain an established station; otherwise cancel attempts and
release Wi-Fi services. Software errors that prevent continuing setup log/show the
cause, clean up and return to offline operation. Later 2 s holds can retry.

### Listening priority and safe teardown

A Start request during setup cancels active setup, waits for safe teardown and then
starts audio. Preserve an established station association. Serialize cancellation
against join completion, reject stale callbacks and finish an atomic settings write
safely. Preserve the final requested Start/Stop state when commands coalesce.
CONTROL serializes its commands with the release wait. No acknowledgement is
valid until L1 confirms scan/connect cancellation and portal/DHCP/AP shutdown;
cleanup tries each pending stop once (see below); a latched Wi-Fi-only cleanup fault releases audio and prevents further Wi-Fi work until restart. This exception follows REQ-13; it does not assert that the radio is physically off. A new Start invalidates the
previous acknowledgement. The 200 ms wait interval is a candidate event-check
interval, not a measured bound on total teardown or settings-write latency.
Setup/reconnect/delivery work is prohibited during listening; retained radio
association and background traffic still require interference measurements.


### Specified failures and interrupted boot

If the network list cannot be refreshed while the setup page is open, the device
reports SCAN_FAILURE, shows Closing and ends setup. An existing Wi-Fi connection
stays up. Setup restarts with a new 2 s button hold in Idle. The IPv4 address event
confirms the join, so the network is saved before the address text is read for the page.
If that text cannot be read, the join still counts and the page shows no address.
An unreadable or invalid stored record is cleared from working memory, never used
for a join, and opens initial setup; preserve flash for diagnosis until a valid save.
`portal_start()` failure independently reports HOTSPOT_START_FAILURE with the HTTP
cause, tears down any partially started services and waits for the manual setup hold.

Start interrupts a boot join by cancelling its active attempt. On return to Idle,
resume the remaining boot attempts; the interrupted issued attempt counts toward
the four-attempt boot budget. Cancellation before issuing an attempt consumes none.
Wait the normal retry gap before resuming. Boot exhaustion remains JOIN_FAILURE
with manual setup; it never becomes link-loss recovery or automatic setup.

An interrupted or timed-out scan or join is cancelled once when it ends. Cleanup then
tries each stop that is still pending once: scan, join, HTTP, DHCP and hotspot.
If all stops succeed, audio is released normally. If any stop fails, latch
WIFI_CLEANUP_FAILURE (restart to clear; indication follows the feedback catalogue), disable further Wi-Fi
work until restart and release audio under REQ-13's Wi-Fi-only exception. Keep failed
operations recorded; do not claim confirmed radio shutdown. Report the cleanup fault to CONTROL through the feedback event boundary.
