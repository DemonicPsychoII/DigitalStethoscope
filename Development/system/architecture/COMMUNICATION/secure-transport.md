# Secure transport architecture

## Basis and scope

Secure transport builds on the [software allocation](../system/puml/software-components.puml). REQ-09, REQ-10 and REQ-11 establish delivery, bounded failure handling and certificate verification.

L1_WIFI owns Wi-Fi, TLS and time operations, and L2_COMMUNICATION owns workflow policy. Station, provisioning and TLS operations use separate interfaces within L1_WIFI.

## Responsibilities and dependencies

| Owner | Responsibility | Boundary |
| --- | --- | --- |
| L2_CONTROL | Admit active network work outside listening and receive completion/release outcomes. | L1_WIFI, L1_FHIR and L1_STORAGE never mutate controller mode. |
| L2_COMMUNICATION | Coordinate preparation and delivery; own overall attempt policy and classify outcomes. | No hidden retries in L1_WIFI, L1_FHIR or L1_STORAGE. |
| L1_WIFI | Own DNS/socket/TLS operations through Zephyr, certificate verification, connection resources and cleanup. | Report outcomes; never serialize FHIR or select a patient. |
| Zephyr networking and TLS stack | Provide platform transport beneath L1_WIFI. | Secure transport reaches it only through L1_WIFI. |
| Clock preparation | Supply time for certificate-validity checking. | Time comes from unauthenticated SNTP. |
| Server profile and L1_STORAGE | Supply the configured endpoint and trust certificate; L1_STORAGE persists named records. | Endpoint and trust material are read-only at runtime and separate from portal settings. |
| L1_FHIR | Serialize application messages independently of networking. | No Zephyr headers, socket ownership or certificate policy. |

L2_CONTROL leases network activity to L2_COMMUNICATION. L2_COMMUNICATION composes L1_FHIR serialization and L1_WIFI transport operations. L1_WIFI depends on Zephyr transport and the server profile trust material. The remote HTTPS server sits outside the device boundary.

## Connection policy

Transport uses TLS 1.3 only, without fallback to older versions. L1_WIFI retains a verified connection for reuse to avoid repeated handshakes. Connection loss recovers by reconnecting within the delivery budget.

L2_COMMUNICATION prepares secure transport automatically while Idle. Each setup starts with one time synchronization directly before the TLS handshake and then proceeds to Device registration. L2_COMMUNICATION tracks network access, verified transport and Device registration separately. Verified transport holds only when the most recent handshake verified the server against the active server profile and the clock applied during that setup.

During listening, a verified connection stays dormant, without application requests, heartbeat messages or proactive reconnects. If it closes, reconnection waits until listening stops. L1_WIFI keeps ownership of the dormant connection. Lease release means that active network operations have ended; a retained connection may stay open. Connection reuse never authorizes active work without the lease.

Servers close idle connections, so delivery reconnects when a retained connection is no longer open. Connection reuse relies on a configured server keep-alive period paired with a shorter device keep-alive timeout.

## Security and lifecycle boundaries

L1_WIFI verifies the server certificate against the server profile trust material, including endpoint identity and validity. The device trusts the server's public certificate directly. Endpoint and certificate come from a server profile image written separately from the firmware, with no client certificate configured. Failed verification blocks sending without plain-HTTP fallback or verification bypass, and reports a terminal verification failure to L2_COMMUNICATION. A station address alone does not establish server readiness.

The local provisioning HTTP server is L1_PORTAL's separate responsibility. Successful Wi-Fi setup does not imply TLS readiness. Device registration, examination-context ingress and result delivery use the secure-server boundary.

Active connection work follows the exclusive network lease. L1_WIFI owns connection resources through cleanup, and L2_COMMUNICATION reports lease release only after active operations end. Network-only failure preserves working offline listening under REQ-13.

The device uses SNTP time without authenticating the time server. Transport verification authenticates the server; it does not authorize an examination request.

## Verification allocation

| Scenario | Trace | Expected outcome |
| --- | --- | --- |
| Untrusted issuer, wrong name, expired certificate or unavailable clock basis | REQ-11; VT-08 | Verification failure prevents sending; no insecure fallback. |
| Handshake failure or incomplete response | REQ-09/REQ-10; VT-07/VT-08 | L2_COMMUNICATION applies bounded outcome/retry policy; transport releases resources. |
| Active transport requested during listening | REQ-02/REQ-13; VT-08/VT-09 | No active transport work; offline listening remains available. |
| Retained connection closes during listening | REQ-02/REQ-10/REQ-13; VT-08/VT-09 | No proactive reconnect or application heartbeat; reconnect after listening within the delivery budget. |
| Reuse and retained-stack load | REQ-02/REQ-09/REQ-11; VT-02/VT-08 | Verified TLS 1.3 connection is reused when available without degrading audio output. |
| Logs and repeated failure cleanup | REQ-10/REQ-13; VT-08/VT-11 | No secrets or patient data in logs; bounded cleanup/release are observable. |
