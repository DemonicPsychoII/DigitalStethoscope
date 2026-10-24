# Wi-Fi interfaces and behavior

L2_COMMUNICATION owns setup, retries and sequencing. `L1_WIFI` owns individual radio and address operations defined in the [service boundary](#service-boundary) below. The page, HTTP server and typed request/status contract belong to PORTAL.

## Service boundary

| Interface | Inputs | Outputs and ownership |
| --- | --- | --- |
| `wifi_init()` | One initialization call before other operations | Registers driver callbacks. |
| `wifi_connect()` | Validated network | 0 accepts one join request; negative error rejects it. This call does not wait for the selected network's address. |
| `wifi_waitForConnection(timeout)` | Maximum wait interval | 0 only after the selected network has IPv4; `-EAGAIN` while pending; negative failure otherwise. An unsolicited disconnect before IPv4 ends the join immediately with `-ENOTCONN`; intentional cancellation and later established-link loss are separate. |
| `wifi_startScan()` | One scan request | 0 accepts the scan; negative error rejects it. No list is returned by this call. |
| `wifi_waitForScanResult(list, capacity, timeout)` | Caller-owned list, entry capacity and maximum wait interval | Nonnegative entry count only after scan-finished; `-EAGAIN` while pending; negative failure/cancellation otherwise. No partial list publication. |
| `wifi_cancelScan()`, `wifi_disconnect()` | Cancel active scan or connection | Bounded completion; no new connect until DISCONNECT_RESULT or confirmed already-disconnected state; no new scan until SCAN_DONE; timeout is failure. |
| `wifi_isValidNetwork()` | Nullable stored or submitted network | Reject NULL, unterminated/empty name and invalid passphrase length (8–63 bytes, or exactly 64 hexadecimal key digits; empty for an open network); no mutation. |
| Hotspot and DHCP functions | Start/stop requests from COMMUNICATION | Individual service outcomes; HTTP page serving remains in PORTAL. |
| `wifi_getAddress()`, `wifi_isConnected()` | Address buffer or link query | Current station address or connection state. |

A new radio request or cancellation rejects late results of the prior request. Each wait returns its result to COMMUNICATION; callbacks do not change controller state. [Shared system contracts](../system/interfaces-and-behavior.md) define mode ownership and feedback; [Wi-Fi parameters](parameters.md) define operation limits; COMMUNICATION defines sequencing and retries.


## Supported networks

List and accept open networks and WPA2-PSK. Filter other security types instead of mapping them onto a supported type. Bound each operation and return its cause to the caller. Persistence belongs to L1_STORAGE; retries and listening interruption belong to L2_COMMUNICATION.

## Failure boundaries and bounded results

AP enable or vendor configuration failure immediately attempts DHCP shutdown and AP disable before returning the original cause. DHCP startup failure rolls back the same partial setup. Failed rollback attempts remain subject to COMMUNICATION's bounded cleanup policy; returning an error does not assert physical shutdown.

The scan cache retains the strongest 16 distinct supported SSIDs; a stronger duplicate updates its entry. Additional weaker networks are omitted. The completed cache has no signal-strength ordering. A smaller caller buffer receives the leading subset up to its capacity; the count reports copied entries, without an overflow flag. COMMUNICATION supplies the full 16-entry capacity. These are project operation contracts; target driver and shutdown verification remain pending.
