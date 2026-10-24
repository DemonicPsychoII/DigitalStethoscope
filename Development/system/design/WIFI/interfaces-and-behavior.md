# Wi-Fi interfaces and behavior

L2_COMMUNICATION owns setup, retries and sequencing. `L1_WIFI` owns individual radio and address operations defined in the [service boundary](#service-boundary) below. The page, HTTP server and typed request/status contract belong to PORTAL.

## Service boundary

| Interface | Inputs | Outputs and ownership |
| --- | --- | --- |
| `wifi_init()` | One initialization call before other operations | Registers driver callbacks. |
| `wifi_connect()`, `wifi_waitForConnection()` | Validated network; bounded wait slice | Request acceptance, pending `-EAGAIN`, selected-network address or failure. |
| `wifi_startScan()`, `wifi_waitForScanResult()` | Scan request and caller-owned bounded list | Scan-finished list; no partial list publication. |
| `wifi_cancelScan()`, `wifi_disconnect()` | Cancel active scan or connection | Bounded completion; no new connect until DISCONNECT_RESULT or confirmed already-disconnected state; no new scan until SCAN_DONE; timeout is failure. |
| `wifi_isValidNetwork()` | Nullable stored or submitted network | Reject NULL, unterminated/empty name and invalid passphrase length (8–63 bytes, or exactly 64 hexadecimal key digits; empty for an open network); no mutation. |
| Hotspot and DHCP functions | Start/stop requests from COMMUNICATION | Individual service outcomes; HTTP page serving remains in PORTAL. |
| `wifi_getAddress()`, `wifi_isConnected()` | Address buffer or link query | Current station address or connection state. |

A new radio request or cancellation rejects late results of the prior request. Each wait returns its result to COMMUNICATION; callbacks do not change controller state. [Shared system contracts](../system/interfaces-and-behavior.md) define mode ownership and feedback; [Wi-Fi parameters](parameters.md) define operation limits; COMMUNICATION defines sequencing and retries.


## Supported networks

List and accept open networks and WPA2-PSK. Filter other security types instead of mapping them onto a supported type. Bound each operation and return its cause to the caller. Persistence belongs to L1_STORAGE; retries and listening interruption belong to L2_COMMUNICATION.
