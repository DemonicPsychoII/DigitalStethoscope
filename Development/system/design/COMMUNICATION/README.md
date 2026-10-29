# COMMUNICATION detailed design

[Setup workflow](interfaces-and-behavior.md) defines orchestration, retries, recovery, persistence sequencing, cancellation and listening priority. [Parameters](parameters.md) bound these operations. L1_WIFI owns radio operations; L1_STORAGE owns the record interface; L1_PORTAL owns HTTP and page behavior.

[Server communication](server-communication.md) defines persistent conditional Device registration, bounded FHIR message construction, request-context consumption and connection reuse. Its request-delivery comparison leaves the external adapter undecided; SNTP and TLS remain separate design dependencies.
