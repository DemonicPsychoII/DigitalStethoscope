# Time synchronization architecture

## Basis and scope

This Architecture-stage proposal refines the existing [system allocation](../system/software-components.puml) and [delivery/clock boundary](../../design/system/interfaces-and-behavior.md#delivery-clock-and-configuration). Its requirements basis is REQ-09, REQ-11 and REQ-13. It defines responsibilities and dependencies; clock interfaces, synchronization timing, accuracy and freshness belong to detailed design.

The existing allocation places time operations in L1_WIFI and orchestration in L2_COMMUNICATION. The additional responsibilities below are proposed, not an accepted implementation baseline. The [current decision baseline](../../planning/README.md#current-baseline) identifies accepted project decisions.

## Responsibilities and dependencies

| Owner | Responsibility | Boundary |
| --- | --- | --- |
| L2_CONTROL | Admit active synchronization under the exclusive network lease; supply measurement timing context and consume readiness/failure outcomes. | Listening admission remains independent of server readiness. |
| L2_COMMUNICATION | Coordinate synchronization and evaluate clock readiness against the eventual approved policy; make readiness available to delivery preparation. | No hidden background synchronization or retry policy in lower services. |
| L1_WIFI | Perform one requested SNTP exchange through Zephyr and return the time information or failure. | Obtaining a time value does not establish that it is trusted. |
| Measurement owner, L2_AUDIO with L2_CONTROL | Preserve the measurement interval in the sample/monotonic time domain and its approved UTC mapping. | A later synchronization must not silently relabel a frozen result. |
| TLS transport and L1_FHIR | Consume approved clock information for their respective certificate-checking and timestamp responsibilities. | Neither chooses a time server nor starts synchronization. |

Dependency direction: CONTROL grants the lease to COMMUNICATION; COMMUNICATION requests time operations from WIFI; WIFI uses Zephyr networking to reach the external time server. Measurement mapping and TLS readiness depend on the clock policy rather than on station association alone. This is a project allocation, not a new independently scheduled component.

Active exchanges remain outside live listening. Offline listening remains available when time preparation fails. Wi-Fi setup succeeds on its own address/persistence criteria; SNTP success is not an added setup prerequisite. Existing [network lease rules](../../design/system/interfaces-and-behavior.md#delivery-clock-and-configuration) continue to apply.

## Proposed trust boundary and open decisions

Propose a configured SNTP server on a trusted project network. Acceptance of that trust assumption remains open: unauthenticated SNTP does not authenticate the source [1]. Synchronization success alone must not be represented as authenticated time.

Detailed design must resolve the reference clock, synchronization evidence, allowed measurement-end timestamp skew, clock freshness and invalidation, and the mapping across clock corrections before/after a measurement. It must also define when preparation occurs without extending the delivery budget or creating network work during listening. TICKET-180 and TICKET-209 remain open. This proposal sets no new numeric acceptance limit and makes no claim of target accuracy.

## Verification allocation

These scenarios allocate future verification; they do not add a generated test batch or claim execution.

| Scenario | Trace | Expected outcome |
| --- | --- | --- |
| No clock, failed exchange or unapproved mapping | REQ-09/REQ-11; VT-07/VT-08 | No delivery with an invented measurement timestamp or bypassed certificate checks; readiness failure is reported. |
| Synchronization requested while listening | REQ-02/REQ-13; VT-08/VT-09 | No active time exchange; working offline audio remains available. |
| Clock correction around a completed measurement | REQ-09/REQ-10; VT-07 | Measurement interval and frozen delivery identity remain unchanged; mapping eligibility follows the agreed design. |
| Reference comparison on target | REQ-09; VT-07 | Evidence identifies the reference, firmware revision and measured skew; acceptance waits for the approved limits. |

The [verification catalogue](../../testing/specification-verification.md) retains pending TLS/time and timestamp acceptance coverage.

## Sources

[1] David L. Mills, *Simple Network Time Protocol (SNTP) Version 4 for IPv4, IPv6 and OSI*, IETF RFC 4330, January 2006, section 9, DOI: 10.17487/RFC4330, <https://www.rfc-editor.org/rfc/rfc4330#section-9>. Source verification/access recorded 24 October 2026 in the [source register](../../../../thesis-material/quellen.md#ietf_sntp_4330_2006); no new access claimed.
