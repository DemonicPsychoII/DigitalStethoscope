# Verification allocation of the design pages

Each table lists the scenarios that verify one design page, with the requirements and verification
cases they trace to and the expected result. The host tests name these sections as their basis.

## Time synchronization

Design page: [design/COMMUNICATION/time-synchronization.md](../design/COMMUNICATION/time-synchronization.md).

| Scenario | Trace | Expected result |
| --- | --- | --- |
| Boot and successful exchange | [REQ-09](../requirements/system-requirements.md#req-09)/[REQ-11](../requirements/system-requirements.md#req-11); VT-07/08 | No persisted ready clock; the first TLS setup applies the UTC/monotonic anchor before its ClientHello. |
| DNS failure, blocked UDP, rejected response (including leap indicator 3 or stratum outside 1–15) | [REQ-09](../requirements/system-requirements.md#req-09)/[REQ-13](../requirements/system-requirements.md#req-13); VT-08/09 | The containing connection setup fails within its deadline and follows P26 or P13 recovery; `SERVER_CONNECTION_FAILURE` without blocking listening. |
| Start during DNS/wait/completion race | [REQ-02](../requirements/system-requirements.md#req-02)/[REQ-13](../requirements/system-requirements.md#req-13); VT-08/09 | Quiesce before audio; stale completion cannot apply time; cancellation raises no time-sync error. |
| Mapping limit and long Idle period | [REQ-09](../requirements/system-requirements.md#req-09)/[REQ-10](../requirements/system-requirements.md#req-10)/[REQ-13](../requirements/system-requirements.md#req-13); VT-07/08/09 | A qualifying anchor at job admission freezes the end there; otherwise the first delivery setup anchor freezes it; no qualifying anchor sends nothing and latches `SERVER_CONNECTION_FAILURE`. |
| Correction and frozen measurement | [REQ-09](../requirements/system-requirements.md#req-09)/[REQ-10](../requirements/system-requirements.md#req-10); VT-07 | Monotonic duration and frozen UTC/identity stay unchanged across retries and later exchanges; no delayed resend. |
| Native units, unset time, subsecond carry | [REQ-09](../requirements/system-requirements.md#req-09)/[REQ-11](../requirements/system-requirements.md#req-11); VT-07/08 | Consistent UTC conversion and independently sampled monotonic anchor. |
| Cleanup fault | [REQ-13](../requirements/system-requirements.md#req-13)/[REQ-14](../requirements/system-requirements.md#req-14); VT-08/09/11 | Failed cancellation latches `WIFI_CLEANUP_FAILURE`, disables network work and releases audio without reporting quiescence. |

## Secure transport

Design page: [design/COMMUNICATION/secure-transport.md](../design/COMMUNICATION/secure-transport.md).

| Scenario | Trace | Expected result |
| --- | --- | --- |
| Server profile image and endpoint mismatch | [REQ-11](../requirements/system-requirements.md#req-11); VT-08 | Missing/corrupt image leaves transport unavailable with a configuration cause; a firmware update keeps the image; wrong SAN, untrusted or expired peer never becomes ready. |
| TLS version and server-only handshake | [REQ-11](../requirements/system-requirements.md#req-11); VT-07/08 | TLS 1.3 succeeds with matching trust; older-only peer/client-certificate requirement fails without fallback. |
| DNS/TCP/TLS stall and repeated recovery | [REQ-11](../requirements/system-requirements.md#req-11)/[REQ-13](../requirements/system-requirements.md#req-13)/[REQ-14](../requirements/system-requirements.md#req-14); VT-08/09/11 | Ten-second preparation deadline, 60-second gaps, no indication storm; standalone listening works. |
| Start/cancellation race and cleanup failure | [REQ-02](../requirements/system-requirements.md#req-02)/[REQ-13](../requirements/system-requirements.md#req-13); VT-08/09 | Quiesce before audio; stale completions ignored; failed cleanup uses restart policy. |
| Retained connection, idle closure and delivery reconnect | [REQ-09](../requirements/system-requirements.md#req-09)/[REQ-10](../requirements/system-requirements.md#req-10)/[REQ-11](../requirements/system-requirements.md#req-11); VT-07/08 | Reuse when eligible; a closed or over-age socket is replaced without consuming an attempt; reconnect stays within P13 and keeps the frozen result; no delayed send. Target timing and connection survival follow [TICKET-213](https://nfrie.atlassian.net/browse/TICKET-213). |
| SNTP before handshake, validity boundary and correction | [REQ-09](../requirements/system-requirements.md#req-09)/[REQ-11](../requirements/system-requirements.md#req-11); VT-07/08 | Every setup applies a fresh clock before its ClientHello, the first TLS handshake message; no request on an invalidated context; a new setup is required. |
| Listening and dormant transport | [REQ-02](../requirements/system-requirements.md#req-02)/[REQ-13](../requirements/system-requirements.md#req-13); VT-08/09 | No application network jobs/heartbeats; target evidence checks audio interference. |
| HAPI Device and Observation authorization | [REQ-10](../requirements/system-requirements.md#req-10)/[REQ-11](../requirements/system-requirements.md#req-11); VT-07 | Future integration verifies registration/upload permissions separately from metadata/TLS success. |

## Server communication

Design page: [design/COMMUNICATION/server-communication.md](../design/COMMUNICATION/server-communication.md).

| Scenario | Trace | Expected result |
| --- | --- | --- |
| Initial creation, lost receipt, one/multiple matches | [REQ-09](../requirements/system-requirements.md#req-09)/[REQ-11](../requirements/system-requirements.md#req-11)/[REQ-15](../requirements/system-requirements.md#req-15); VT-07/08/15 | One stable conditional identity; validated server id; 412 never falls back to unconditional creation |
| Flash failure, restart and corrupt/mismatched record | [REQ-09](../requirements/system-requirements.md#req-09)/[REQ-13](../requirements/system-requirements.md#req-13)/[REQ-15](../requirements/system-requirements.md#req-15); VT-08/11/15 | Not ready until committed; safe recovery with the same physical identity; old committed data preserved on failure |
| Wi-Fi change, server change and missing Device | [REQ-09](../requirements/system-requirements.md#req-09)/[REQ-11](../requirements/system-requirements.md#req-11)/[REQ-12](../requirements/system-requirements.md#req-12)/[REQ-15](../requirements/system-requirements.md#req-15); VT-07/08/15 | Network changes preserve registration; server binding changes reconcile while Idle; frozen result never relabelled |
| Local Start, request replacement, duplication and context changes | [REQ-02](../requirements/system-requirements.md#req-02)/[REQ-09](../requirements/system-requirements.md#req-09)/[REQ-13](../requirements/system-requirements.md#req-13); VT-07/08/09 | Local authority; the newest pending request wins; a request during a frozen session waits for the next examination; immutable subject; no next-session patient reuse after cancellation/failure |
| JSON fields, escaping, precision and overflow | [REQ-09](../requirements/system-requirements.md#req-09)/[REQ-10](../requirements/system-requirements.md#req-10)/[REQ-11](../requirements/system-requirements.md#req-11); VT-07/08 | Valid bounded base-FHIR representation; patient absent when unsupplied; no unverified profile claim |
| Early Stop and poor signal | [REQ-07](../requirements/system-requirements.md#req-07)/[REQ-08](../requirements/system-requirements.md#req-08); VT-07/09 | Early Stop sends nothing; poor signal uses an Observation with `dataAbsentReason=error`, no `valueQuantity`, and the frozen context |
| Reconnect, uncertain receipt and terminal failure | [REQ-09](../requirements/system-requirements.md#req-09)/[REQ-10](../requirements/system-requirements.md#req-10); VT-07/08 | P13 bounds; identical retries; receipt only on 201/200; visible terminal loss without delayed queue |
| Persistent registration across three restarts | [REQ-15](../requirements/system-requirements.md#req-15); VT-15 | First registration stores the server id; each of three restarts reuses that same id without a new Device, and a session after each restart references it; the HAPI page shows one Device for this device |
| Target identity, flash interruption and listening | [REQ-02](../requirements/system-requirements.md#req-02)/[REQ-13](../requirements/system-requirements.md#req-13)/[REQ-15](../requirements/system-requirements.md#req-15); VT-08/09/11/15 | Stable factory identity, demonstrated persistence/cancellation bounds and no active network jobs during audio |

## Server profile

Design page: [design/STORAGE/server-profile.md](../design/STORAGE/server-profile.md).

| Scenario | Trace | Expected result |
| --- | --- | --- |
| Valid deployment file | [REQ-09](../requirements/system-requirements.md#req-09)/[REQ-11](../requirements/system-requirements.md#req-11); VT-08 | `check` passes; the image bytes match the field table and the firmware reader accepts them. |
| Each violated file rule | [REQ-11](../requirements/system-requirements.md#req-11); VT-08 | Rejected with key and rule; no image written. |
| Certificate not self-issued, without matching Subject Alternative Name, or with a DNS entry for an IPv4 host | [REQ-11](../requirements/system-requirements.md#req-11); VT-08 | Rejected by the tool; an image forced onto a device yields an invalid configuration at boot (missing or wrong-type Subject Alternative Name) or, for a certificate that is not self-issued, an expected handshake failure that L1_WIFI work still has to demonstrate ([TLS trust inputs](../design/STORAGE/../COMMUNICATION/secure-transport.md#trust-and-server-profile-inputs)). |
| Certificate with a Key Usage extension that omits `digitalSignature`, or with an Extended Key Usage extension that omits both `serverAuth` and `anyExtendedKeyUsage` | [REQ-11](../requirements/system-requirements.md#req-11); VT-08 | Rejected by the tool; an image forced onto a device is accepted at boot and fails verification at the handshake. |
| Certificate expired or not yet valid | [REQ-11](../requirements/system-requirements.md#req-11); VT-08 | Rejected by the tool on the PC's date; on the device a valid image is accepted at boot and the setup fails its validity check after time synchronization, without a handshake. |
| Private key or other PEM label in the file | VT-11 | Rejected; nothing written. |
| Image larger than the server profile area, or build without the partition node | [REQ-11](../requirements/system-requirements.md#req-11); VT-08 | Rejected before writing. |
| Flash command on a device | [REQ-11](../requirements/system-requirements.md#req-11)/[REQ-12](../requirements/system-requirements.md#req-12); VT-08 | Only the server profile range changes; saved network and firmware remain. |
| Missing or corrupted image at boot | [REQ-11](../requirements/system-requirements.md#req-11)/[REQ-13](../requirements/system-requirements.md#req-13); VT-08/VT-09 | Secure transport unavailable with a configuration cause; Wi-Fi and offline listening unaffected. |
| CRC-valid image with a server keep-alive of 0 to 5 seconds at boot | [REQ-11](../requirements/system-requirements.md#req-11)/[REQ-13](../requirements/system-requirements.md#req-13); VT-08/VT-09 | Invalid configuration; no secure connection attempt; Wi-Fi and offline listening unaffected. |
