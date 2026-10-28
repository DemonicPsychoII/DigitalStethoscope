# COMMUNICATION detailed design

[Setup workflow](interfaces-and-behavior.md) defines orchestration, retries, recovery, persistence sequencing, cancellation and listening priority. [Parameters](parameters.md) bound these operations. L1_WIFI owns radio operations; L1_STORAGE owns the record interface; L1_PORTAL owns HTTP and page behavior.

[SNTP synchronization](time-synchronization.md) defines clock readiness, service contracts, uncertainty, refresh, cancellation and recovery independently of Wi-Fi setup success.
