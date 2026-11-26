# L1_WIFI interfaces and behavior

`L2_COMMUNICATION` owns setup, retries and sequencing. `L1_WIFI` owns individual radio and address operations defined in the [service boundary](#service-boundary) below. The page, HTTP server and typed request and status contract belong to [`L1_PORTAL`](../PORTAL/interfaces-and-behavior.md).

## Service boundary

The [SNTP time-synchronization design](../COMMUNICATION/time-synchronization.md) defines a cancellable DNS lookup and SNTP (Simple Network Time Protocol) exchange, normalization of its result and application of the time to the device clock.

| Interface | Inputs | Outputs and ownership |
| --- | --- | --- |
| `wifi_init()` | One initialization call before other operations | Registers driver callbacks. |
| `wifi_connect()` | Validated network | 0 accepts one join request; negative error rejects it. This call does not wait for the selected network's address. |
| `wifi_waitForConnection(timeout)` | Maximum wait interval | 0 only after the selected network has IPv4; `-EAGAIN` while pending; negative failure otherwise. An unsolicited disconnect before IPv4 ends the join immediately with `-ENOTCONN`; intentional cancellation and later established-link loss are separate. |
| `wifi_startScan()` | One scan request | 0 accepts the scan; negative error rejects it. No list is returned by this call. |
| `wifi_waitForScanResult(list, capacity, timeout)` | Caller-owned list, entry capacity and maximum wait interval | Nonnegative entry count only after scan-finished; `-EAGAIN` while pending; negative failure/cancellation otherwise. No partial list publication. |
| `wifi_cancelScan()`, `wifi_disconnect()` | Cancel active scan or connection | Bounded completion; no new connect starts until a disconnect completion event or confirmed already-disconnected state is established within the 1 s disconnect-confirmation deadline. `wifi_isConnected()` alone does not confirm cancellation of an in-progress join. No new scan starts until the scan-finished result (`wifi_waitForScanResult()`, including cancellation) arrives. Timeout is failure. |
| `wifi_isValidNetwork()` | Nullable stored or submitted network | Reject NULL, unterminated/empty name and invalid passphrase length (8–63 bytes, or exactly 64 hexadecimal key digits; empty for an open network); no mutation. |
| `wifi_startHotspot()`, `wifi_stopHotspot()`, `wifi_startDHCPServer()`, `wifi_stopDHCPServer()` | Start and stop requests from `L2_COMMUNICATION` | Individual service outcomes; HTTP page serving remains in `L1_PORTAL`. |
| `wifi_getAddress()`, `wifi_isConnected()` | Address buffer or link query | Current station address or connection state. |

A new radio request or cancellation rejects late results of the prior request. Each wait returns its result to `L2_COMMUNICATION`; callbacks do not change controller state. The [firmware structure](../../architecture/system/firmware-structure.md) defines mode ownership, and the [feedback design](../FEEDBACK/README.md) the indication; [Wi-Fi parameters](parameters.md) define operation limits; [L2_COMMUNICATION](../COMMUNICATION/interfaces-and-behavior.md) defines sequencing and retries.

## Secure server operations

Secure server operations follow the [TLS service contracts](../COMMUNICATION/secure-transport.md). `L1_WIFI` owns DNS, TCP and TLS resources and mandatory verification. `L2_COMMUNICATION` owns deadlines and retry scheduling. These operations require `L2_CONTROL`'s network lease and quiescent cancellation before audio.

## Physical device identity

`wifi_getDeviceIdentifier()` returns the full-MAC-derived physical identifier defined by [server communication](../COMMUNICATION/server-communication.md#physical-identity-and-server-binding), or an error cause. It reads the stable factory station MAC address rather than a short suffix or a runtime-overridden address. This local operation neither connects to a network nor registers a Device.

## Network record

`wifi_network` is the network name and password record shared with `L1_STORAGE` and `L2_COMMUNICATION`. It contains `char name[33]` followed by `char password[65]`, giving a complete persisted record of 98 bytes with no security-type field, version prefix or additional serialized metadata.

`name` holds 1–32 non-NUL SSID bytes followed by a NUL terminator. `password` holds an empty string for an open network, 8–63 passphrase bytes, or 64 ASCII hexadecimal key digits, followed by a NUL terminator. Each string must terminate within its array. Byte sequences are preserved without text normalization; lengths are byte counts, not Unicode character counts. Bytes after each terminator remain part of the fixed-size record but are not string content. `wifi_isValidNetwork()` checks this representation without mutation. Security-type eligibility is established by the supported-network scan/join path; this record alone cannot distinguish WPA2 from an unsupported secured network.

## Supported networks

`L1_WIFI` lists and accepts open networks and WPA2-PSK networks. It filters other security types instead of mapping them onto a supported type. Each operation is bounded and returns its cause to the caller. Persistence belongs to `L1_STORAGE`; retries and listening interruption belong to `L2_COMMUNICATION`.

## Failure boundaries and bounded results

On hotspot enable or configuration failure, `L1_WIFI` immediately attempts DHCP shutdown and hotspot disable before returning the original cause. DHCP startup failure rolls back the same partial setup. Failed rollback attempts remain subject to `L2_COMMUNICATION`'s bounded cleanup policy.

The scan cache retains the strongest 16 distinct supported SSIDs; a stronger duplicate updates its entry. Additional weaker networks are omitted. The completed cache has no signal-strength ordering. A smaller caller buffer receives the leading subset up to its capacity, and the returned count reports copied entries without an overflow flag. `L2_COMMUNICATION` supplies the full 16-entry capacity.
