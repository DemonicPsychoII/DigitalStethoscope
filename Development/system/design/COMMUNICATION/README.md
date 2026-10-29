# COMMUNICATION detailed design

[Setup workflow](interfaces-and-behavior.md) defines orchestration, retries, recovery, persistence sequencing, cancellation and listening priority. [Parameters](parameters.md) bound these operations. L1_WIFI owns radio operations; L1_STORAGE owns the record interface; L1_PORTAL owns HTTP and page behavior.

[TLS preparation](secure-transport.md) defines build-time endpoint/trust inputs, TLS 1.3 verification, connection reuse, cancellation, recovery and the delivery-budget boundary. It depends on the separately proposed SNTP design in PR #99.
