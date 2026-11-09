# COMMUNICATION detailed design

[Setup workflow](interfaces-and-behavior.md) defines orchestration, retries, recovery, persistence sequencing, cancellation and listening priority. [Parameters](parameters.md) bound these operations. L1_WIFI owns radio operations; L1_STORAGE owns the record interface; L1_PORTAL owns HTTP and page behavior.

[SNTP synchronization](time-synchronization.md) defines the exchange that opens every TLS setup, service contracts, uncertainty, the computed mapping limit and cancellation, independently of Wi-Fi setup success.

[TLS preparation](secure-transport.md) defines the endpoint and trust inputs from the server profile, TLS 1.3 verification, connection reuse, cancellation, recovery and the delivery-budget boundary. Each setup starts with the SNTP exchange above.

[Server communication](server-communication.md) defines persistent conditional Device registration, bounded FHIR message construction, request-context consumption and connection reuse. Its request-delivery comparison leaves the external adapter undecided; It depends on the SNTP and TLS designs above.

## How Wi-Fi setup works

1. At boot, read the stored network and join it. If all boot attempts fail, the device shows an error and waits in Idle; it does not open setup on its own.
2. If no stored network can be read, or after a 2 s button hold in Idle, scan for nearby networks, open the hotspot and serve the setup page with the found networks listed.
3. The operator selects a network, enters its password if it needs one, and submits. The device joins that network and, once it has an address, saves the SSID and password in its persistent settings.
4. After showing the result for 10 s, the device closes the hotspot and stays connected to the network.

The [state diagram](../../architecture/COMMUNICATION/setup-state.puml), [setup flow](../../architecture/COMMUNICATION/setup-flow.puml) and [recovery flow](../../architecture/COMMUNICATION/link-recovery.puml) show these steps. The [setup workflow](interfaces-and-behavior.md) holds the detailed rules: retries, recovery, cancellation and listening priority.
