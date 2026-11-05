# COMMUNICATION detailed design

[Setup workflow](interfaces-and-behavior.md) defines orchestration, retries, recovery, persistence sequencing, cancellation and listening priority. [Parameters](parameters.md) bound these operations. L1_WIFI owns radio operations; L1_STORAGE owns the record interface; L1_PORTAL owns HTTP and page behavior.

[SNTP synchronization](time-synchronization.md) defines the exchange that opens every TLS setup, service contracts, uncertainty, the computed mapping limit and cancellation, independently of Wi-Fi setup success.

[TLS preparation](secure-transport.md) defines the endpoint and trust inputs from the server profile, TLS 1.3 verification, connection reuse, cancellation, recovery and the delivery-budget boundary. Each setup starts with the SNTP exchange above.

[Server communication](server-communication.md) defines persistent conditional Device registration, bounded FHIR message construction, request-context consumption and connection reuse. Its request-delivery comparison leaves the external adapter undecided; It depends on the SNTP and TLS designs above.
