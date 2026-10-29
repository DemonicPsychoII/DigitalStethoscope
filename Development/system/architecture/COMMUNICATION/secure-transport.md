# Secure transport architecture

## Basis and scope

This Architecture-stage proposal refines the [software allocation](../system/software-components.puml) and [server transport boundary](../../design/system/interfaces-and-behavior.md#delivery-clock-and-configuration). REQ-09, REQ-10 and REQ-11 establish delivery, bounded failure handling and certificate verification. The [current decisions](../../planning/README.md#current-baseline) identify the accepted basis; this refinement is proposed, not an accepted implementation contract.

Retain the system allocation of Wi-Fi, TLS and time operations to L1_WIFI and workflow policy to L2_COMMUNICATION. Existing WIFI production interfaces cover station/provisioning operations; TLS operations still require a separate Design-stage contract before implementation.

## Responsibilities and dependencies

| Owner | Responsibility | Boundary |
| --- | --- | --- |
| L2_CONTROL | Admit active network work outside listening and receive completion/release outcomes. | Lower services never mutate controller mode. |
| L2_COMMUNICATION | Coordinate preparation and delivery; own overall attempt policy and classify outcomes. | No hidden retries in lower services. |
| L1_WIFI | Own DNS/socket/TLS operations through Zephyr, certificate verification, connection resources and cleanup. | Report outcomes; never serialize FHIR or select a patient. |
| Zephyr networking and TLS stack | Provide platform transport beneath L1_WIFI. | Integration and target behavior remain unverified. |
| Clock preparation | Supply acceptable time for certificate-validity checking. | Accepted unauthenticated SNTP time is not authenticated time. |
| Deployment configuration and L1_STORAGE | Supply endpoint/trust material through the eventual configuration contract; STORAGE persists named records. | No new settings record, credential interface or portal field is defined here. |
| L1_FHIR | Serialize application messages independently of networking. | No Zephyr headers, socket ownership or certificate policy. |

Dependency direction: CONTROL leases network activity to COMMUNICATION; COMMUNICATION composes the serializer and WIFI operations; WIFI depends on Zephyr transport and deployment trust material. The remote HTTPS server remains outside the device boundary. This is a project allocation derived from the existing system design.

## Agreed connection lifecycle

Nico agreed the following direction during architecture grilling on 28 October 2026, recorded in [PR #80](https://github.com/DemonicPsychoII/DigitalStethoscope/pull/80). Prefer TLS 1.3, subject to verification of support in the pinned device stack and server. TLS detailed design on 29 October 2026 narrowed this to TLS 1.3 only, without fallback to older versions ([TLS Design PR #100](https://github.com/DemonicPsychoII/DigitalStethoscope/pull/100)). Retain and reuse a verified connection when available to reduce repeated connection setup. Connection reuse is an optimization, not a delivery prerequisite: connection loss is an expected recovery path within the existing delivery budget.

Prepare secure transport automatically while Idle after acceptable clock preparation, then proceed to registration readiness. COMMUNICATION tracks network access, acceptable clock, verified transport and Device registration separately; an open connection does not establish all prerequisites. Verified transport means the most recent handshake verified the server under the current configuration and clock; an open socket is only a reuse candidate.

During listening, retain an existing connection without application requests, heartbeat messages or proactive reconnects. If it closes, defer reconnection until listening stops. WIFI retains ownership of the dormant connection; lease release means active network operations have ended, not that every retained socket must close. Connection reuse never authorizes active work without the lease. Target verification must establish the audio/resource impact of retained connections and underlying stack activity; application inactivity alone proves no isolation.

Design must define retained-connection lifecycle, closure detection, cleanup and reconnect behavior. No indefinite connection lifetime or keepalive guarantee is assumed. Servers close idle connections (the local HAPI deployment after about 60 s by default), so reconnection at delivery is the expected path and reuse depends on a keep-alive period on both ends: the deployment configures a long server keep-alive and the device applies its own, shorter keep-alive timeout. Retention during listening is the initial approach; if target measurement under [TICKET-213](https://nfrie.atlassian.net/browse/TICKET-213) shows that the connection does not survive, close it at Start instead. TLS 1.3 compatibility and resource costs remain unverified.

## Security and lifecycle boundaries

Verify the server certificate against build-supplied trust material, together with endpoint identity and validity; these checks are mandatory. TLS detailed design replaced the earlier lab-CA assumption with direct trust of the server's public certificate, selected at build time; no client certificate is configured. Failed verification prevents sending the application request; neither plain-HTTP fallback nor a verification bypass is a recovery path. COMMUNICATION receives a terminal verification failure under the existing delivery policy. A station address alone does not establish server readiness.

The local provisioning HTTP server remains L1_PORTAL's separate responsibility. Successful setup does not imply TLS readiness. Registration, examination-context ingress and delivery use the secure-server boundary when their transport contracts are defined.

Active connection work follows the exclusive network lease. WIFI owns connection resources through cleanup; COMMUNICATION reports release only after active operations have ended. Network-only failure preserves working offline listening under REQ-13. Precise cancellation/close behavior belongs to Design.

## Detailed-design inputs and gaps

Define operation interfaces, endpoint/trust provisioning, credential handling, connection lifetime, resource budgets and failure mapping in Design. Retain existing delivery bounds; cipher selection, rotation and timeout values remain Design inputs. Unauthenticated SNTP time is accepted for the MVP ([SNTP Design PR #99](https://github.com/DemonicPsychoII/DigitalStethoscope/pull/99)); timestamp accuracy evidence remains open (TICKET-209). Server authentication/authorization and certificate deployment must be made concrete before service implementation. Transport verification does not settle examination-request authorization.

## Verification allocation

| Scenario | Trace | Expected outcome |
| --- | --- | --- |
| Untrusted issuer, wrong name, expired certificate or unavailable clock basis | REQ-11; VT-08 | Verification failure prevents sending; no insecure fallback. |
| Handshake failure or incomplete response | REQ-09/REQ-10; VT-07/VT-08 | COMMUNICATION applies bounded outcome/retry policy; transport releases resources. |
| Active transport requested during listening | REQ-02/REQ-13; VT-08/VT-09 | No active transport work; offline listening remains available. |
| Retained connection closes during listening | REQ-02/REQ-10/REQ-13; VT-08/VT-09 | No proactive reconnect or application heartbeat; reconnect after listening within the delivery budget. |
| Reuse and retained-stack load | REQ-02/REQ-09/REQ-11; VT-02/VT-08 | Reuse the verified connection when available; verify TLS 1.3 support and measure target audio/resource impact. |
| Logs and repeated failure cleanup | REQ-10/REQ-13; VT-08/VT-11 | No secrets or patient data in logs; bounded cleanup/release are observable. |

These allocate future verification, not test execution. [VT-08 coverage](../../testing/specification-verification.md) and target resource/interference evidence remain pending.

## Project basis

The rules above restate project policy rather than claim TLS implementation conformance: Nico, *MVP decisions — Wi-Fi setup, registration and delivery*, DigitalStethoscope project record, 15 October 2026, [record](../../planning/mvp-decisions-2026-10-15.md), as superseded by the [current baseline](../../planning/README.md#current-baseline); *System requirements (MVP)* and *System interfaces and behavior*, repository revision `81c7b1a45f5b0ef45c939098e5a693773c8abb90`, 2026, [requirements](../../requirements/system-requirements.md), [design](../../design/system/interfaces-and-behavior.md#delivery-clock-and-configuration). No target acceptance is claimed.
