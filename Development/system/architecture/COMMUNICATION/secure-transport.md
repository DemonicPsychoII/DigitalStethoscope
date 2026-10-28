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
| Clock preparation | Supply the approved time basis for certificate-validity checking. | Successful SNTP alone does not establish accepted clock trust. |
| Deployment configuration and L1_STORAGE | Supply endpoint/trust material through the eventual configuration contract; STORAGE persists named records. | No new settings record, credential interface or portal field is defined here. |
| L1_FHIR | Serialize application messages independently of networking. | No Zephyr headers, socket ownership or certificate policy. |

Dependency direction: CONTROL leases network activity to COMMUNICATION; COMMUNICATION composes the serializer and WIFI operations; WIFI depends on Zephyr transport and deployment trust material. The remote HTTPS server remains outside the device boundary. This is a project allocation derived from the existing system design.

## Security and lifecycle boundaries

Keep the existing CA, hostname and validity checks mandatory. Failed verification prevents sending the application request; neither plain-HTTP fallback nor a verification bypass is a recovery path. COMMUNICATION receives a terminal verification failure under the existing delivery policy. A station address alone does not establish server readiness.

The local provisioning HTTP server remains L1_PORTAL's separate responsibility. Successful setup does not imply TLS readiness. Registration, examination-context ingress and delivery use the secure-server boundary when their transport contracts are defined.

Active connection work follows the exclusive network lease. WIFI owns connection resources through cleanup; COMMUNICATION reports release only after active operations have ended. Network-only failure preserves working offline listening under REQ-13. Precise cancellation/close behavior belongs to Design.

## Detailed-design inputs and gaps

Define operation interfaces, endpoint/trust provisioning, credential handling, connection lifetime, resource budgets and failure mapping in Design. Retain existing delivery bounds; this architecture adds no TLS version, cipher list, rotation mechanism or timeout. Clock trust/freshness remain open (TICKET-180/TICKET-209). Server authentication/authorization and certificate deployment must be made concrete before service implementation. Transport verification does not settle examination-request authorization.

## Verification allocation

| Scenario | Trace | Expected outcome |
| --- | --- | --- |
| Untrusted issuer, wrong name, expired certificate or unavailable clock basis | REQ-11; VT-08 | Verification failure prevents sending; no insecure fallback. |
| Handshake failure or incomplete response | REQ-09/REQ-10; VT-07/VT-08 | COMMUNICATION applies bounded outcome/retry policy; transport releases resources. |
| Active transport requested during listening | REQ-02/REQ-13; VT-08/VT-09 | No active transport work; offline listening remains available. |
| Logs and repeated failure cleanup | REQ-10/REQ-13; VT-08/VT-11 | No secrets or patient data in logs; bounded cleanup/release are observable. |

These allocate future verification, not test execution. [VT-08 coverage](../../testing/specification-verification.md) and target resource/interference evidence remain pending.

## Project basis

The rules above restate project policy rather than claim TLS implementation conformance: Nico, *MVP decisions — Wi-Fi setup, registration and delivery*, DigitalStethoscope project record, 15 October 2026, [record](../../planning/mvp-decisions-2026-10-15.md), as superseded by the [current baseline](../../planning/README.md#current-baseline); *System requirements (MVP)* and *System interfaces and behavior*, repository revision `81c7b1a45f5b0ef45c939098e5a693773c8abb90`, 2026, [requirements](../../requirements/system-requirements.md), [design](../../design/system/interfaces-and-behavior.md#delivery-clock-and-configuration). No target acceptance is claimed.
