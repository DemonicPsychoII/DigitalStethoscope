# Time synchronization architecture

## Basis and scope

Time synchronization refines the [system allocation](../system/software-components.puml) under REQ-02, REQ-09, REQ-10, REQ-11 and REQ-13.

L1_WIFI performs the time operations and L2_COMMUNICATION orchestrates them.

## Responsibilities and dependencies

| Owner | Responsibility | Boundary |
| --- | --- | --- |
| L2_CONTROL | Admit active synchronization under the exclusive network lease; supply measurement timing context and consume readiness/failure outcomes. | Listening admission remains independent of server readiness. |
| L2_COMMUNICATION | Coordinate synchronization and evaluate clock readiness against the clock policy; make readiness available to delivery preparation. | No hidden background synchronization or retry policy in L1_WIFI or L1_FHIR. |
| L1_WIFI | Perform one requested SNTP exchange through Zephyr and return the time information or failure. | Obtaining a time value does not establish that it is trusted. |
| Measurement owner, L2_AUDIO with L2_CONTROL | Preserve the measurement interval in the sample/monotonic time domain and its UTC mapping. | A later synchronization must not silently relabel a frozen result. |
| TLS transport and L1_FHIR | Consume clock information for their respective certificate-checking and timestamp responsibilities. | Neither chooses a time server nor starts synchronization. |

L2_CONTROL grants the network lease to L2_COMMUNICATION. L2_COMMUNICATION requests time operations from L1_WIFI, and L1_WIFI uses Zephyr networking to reach the external time server. Measurement timestamp mapping and TLS readiness depend on the clock policy rather than on station association alone.

Active time exchanges occur only outside live listening under L2_CONTROL's exclusive network lease. Offline listening remains available when time preparation fails. Wi-Fi setup succeeds on its own address and persistence criteria, without requiring SNTP success.

## Preparation flow

After joining the configured network, L2_COMMUNICATION starts every secure transport setup with one time synchronization directly before the TLS handshake. A failed exchange fails that setup and blocks server readiness without affecting Wi-Fi setup completion or offline listening. Once transport is verified, Device registration proceeds while Idle so measurement Stop does not trigger full preparation from scratch.

L2_COMMUNICATION tracks network access, verified transport (including the time applied by its setup) and Device registration separately. A connected station or retained TLS connection alone does not establish delivery readiness. A measurement uses a clock anchor only when that anchor qualifies for the measurement end; synchronization success alone does not authenticate the time source.

## Trust boundary

The time source is an external SNTP server reached through the station's network. Time is obtained over unauthenticated SNTP, which does not authenticate the time server [1]. Synchronization success is never represented as authenticated time.

Time synchronization and clock-correction handling neither extend the delivery budget nor run during listening.

## Verification allocation

| Scenario | Trace | Expected outcome |
| --- | --- | --- |
| No clock, failed exchange or no qualifying clock anchor | REQ-09/REQ-11; VT-07/VT-08 | Delivery is blocked until a qualifying clock anchor exists; no invented measurement timestamp or bypassed certificate checks; readiness failure is reported. |
| Synchronization requested while listening | REQ-02/REQ-13; VT-08/VT-09 | No active time exchange; working offline audio remains available. |
| Clock correction around a completed measurement | REQ-09/REQ-10; VT-07 | Measurement interval and frozen delivery identity remain unchanged. |
| Reference comparison on target | REQ-09; VT-07 | Measured clock skew against the reference stays within the specified timestamp accuracy limit. |

## Sources

[1] David L. Mills, *Simple Network Time Protocol (SNTP) Version 4 for IPv4, IPv6 and OSI*, IETF RFC 4330, January 2006, section 11, DOI: 10.17487/RFC4330, <https://www.rfc-editor.org/rfc/rfc4330#section-11>. Accessed 24 October 2026.
