# COMMUNICATION detailed design

[Setup workflow](interfaces-and-behavior.md) defines orchestration, retries, recovery, persistence sequencing, cancellation and listening priority. [Parameters](parameters.md) bound these operations. L1_WIFI owns radio operations; L1_STORAGE owns the record interface; L1_PORTAL owns HTTP and page behavior.

[SNTP synchronization](time-synchronization.md) defines the Simple Network Time Protocol (SNTP) exchange that opens every TLS connection setup, its service contracts, its uncertainty, the computed limit on how far a clock setting may lie from a measurement end, and cancellation. Wi-Fi setup succeeds without it, but each exchange needs the station's network address and a reachable time server (DNS and UDP port 123).

[TLS preparation](secure-transport.md) defines the endpoint and trust inputs from the server profile, TLS 1.3 verification, connection reuse, cancellation, recovery and the delivery-budget boundary. Each connection setup starts with the SNTP exchange above.

[Server communication](server-communication.md) defines persistent conditional Device registration, bounded FHIR message construction, request-context consumption and connection reuse. It compares ways for an external system to deliver examination requests to the device and leaves that choice open. It depends on the SNTP and TLS designs above.

## How Wi-Fi setup works

1. At boot, read the stored network and join it. If all boot attempts fail, the device shows an error and waits in Idle; it does not open setup on its own.
2. If no stored network can be read, or after a 2 s button hold in Idle, scan for nearby networks, open the hotspot and serve the setup page with the found networks listed.
3. The operator selects a network, enters its password if it needs one, and submits. The device joins that network and, once it has an address, saves the SSID and password in its persistent settings, retrying once. If saving fails, it keeps the old stored network and shows a save warning instead of success.
4. After showing the result or save warning for 10 s, the device closes the hotspot and stays connected to the network, even if the new network was not saved.

The [state diagram](../../architecture/COMMUNICATION/setup-state.puml), [setup flow](../../architecture/COMMUNICATION/setup-flow.puml) and [recovery flow](../../architecture/COMMUNICATION/link-recovery.puml) show these steps. The [setup workflow](interfaces-and-behavior.md) holds the detailed rules: retries, recovery, cancellation and listening priority.

## How server preparation and delivery work

1. At boot, L1_STORAGE reads and validates the [server profile image](../STORAGE/server-profile.md#device-behavior) once. It holds the one server's HTTPS endpoint, its keep-alive timeout and its public certificate. L2_COMMUNICATION also reads the saved [Device registration record](server-communication.md#registration-record). A missing or invalid image leaves secure transport unavailable; Wi-Fi setup and offline listening keep working.
2. In Idle, after the device has joined a network and has an address, L2_COMMUNICATION prepares a secure connection to the server. Every connection setup starts with one [SNTP exchange](time-synchronization.md#flow-and-scheduling) that sets the device clock directly before the TLS handshake. The device then [verifies the server certificate](secure-transport.md#trust-and-server-profile-inputs) against the certificate in the server profile, the endpoint name or address and the freshly set clock. Preparation, including the SNTP exchange, has ten seconds.
3. With a verified connection and no saved registration for this server, the device [registers itself](server-communication.md#registration-flow-and-recovery) with a conditional `POST /Device` that carries its physical identifier. It saves the server-assigned Device id in flash before it counts as registered.
4. During listening, the device starts no network work of its own: no application requests, no connection setup and no SNTP exchange. A retained connection stays open, and its effect on audio is still to be checked on the target. When a measurement Stop produces a result, CONTROL finalizes it and submits it as one delivery job. COMMUNICATION then sends it as a FHIR Observation with a conditional `POST /Observation`, [within one ten-second delivery deadline from Stop](secure-transport.md#delivery-budget-boundary). It reuses the verified connection if it is still eligible; otherwise it reconnects, again starting with an SNTP exchange. Connection setup starts at job submission, not at Stop. Start during sending cancels the job and the result is lost.
5. Server communication failures never block offline listening. A result that was not delivered is not queued for later sending.

| Situation | Outcome |
| --- | --- |
| Failed connection setup during Idle preparation | `SERVER_CONNECTION_FAILURE`; next try after 60 seconds |
| Failed connection setup during delivery | Retried within the delivery deadline under [P13](../system/parameters.md) |
| Terminal delivery outcome (for example a rejected certificate), attempts or deadline used up | `DELIVERY_FAILURE` |
| Result still without a qualifying clock setting at the deadline | `SERVER_CONNECTION_FAILURE` instead, because no request could carry its UTC measurement end |
| Failed registration | `DEVICE_REGISTRATION_FAILURE`; next try after 60 seconds, the gap doubling after each further failure, up to 4 failed attempts |
| Wi-Fi configured, delivery prerequisites missing | `DELIVERY_NOT_POSSIBLE` |
| Wi-Fi not configured | Result discarded without a delivery error |

The [COMMUNICATION lifecycle](../../architecture/COMMUNICATION/communication-lifecycle.puml) ([SVG](../../architecture/COMMUNICATION/rendered/communication_lifecycle.svg)) shows these steps from Wi-Fi join to delivery.

The [feedback catalogue](../FEEDBACK/catalogue.md) defines how the status light shows these failures. The detail pages hold the deadlines, retry counts and cancellation rules.
