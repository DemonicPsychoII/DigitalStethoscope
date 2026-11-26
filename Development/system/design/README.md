# Detailed design

| Area | Contracts |
| --- | --- |
| [Cross-module design](cross-module.md) | Data contracts between modules, queues between modules, state entry and exit, failure contract, pin assignment, design constraints and the parameters P10, P11 and P15. |
| [AUDIO](AUDIO/README.md) | I2S service boundary, block loop, Start/Stop order, sizing, stream faults, filter signal flow, BPM coverage and audio parameters. |
| [WIFI](WIFI/README.md) | Radio and address operations. |
| [STORAGE](STORAGE/README.md) | Named complete-record persistence. |
| [COMMUNICATION](COMMUNICATION/README.md) | Setup orchestration, retry, recovery and listening priority; delivery identity, clock mapping, registration and secure transport. |
| [PORTAL](PORTAL/README.md) | Page behavior, HTTP endpoints, status format and page parameters. |
| [FEEDBACK](FEEDBACK/README.md) | LED/error catalogue, fault response (P12), feedback timing and brightness parameters (P22) and LED indication standards. |

## Parameters

Each parameter is defined once, in the design of the module that defines its value. Owners are the firmware modules in the [module map](../architecture/system/firmware-structure.md#static-dependency-and-module-map).

| Parameters | Defined in |
| --- | --- |
| P01, P02, P03, P05, P06, P07, P08, P09, P17, P20 | [AUDIO](AUDIO/parameters.md) |
| P10, P11, P15 | [Cross-module design](cross-module.md#parameters) |
| P12, P22 | [FEEDBACK](FEEDBACK/parameters.md) |
| P13, P18, P19, P21-COMMUNICATION, P23 | [L2_COMMUNICATION](COMMUNICATION/parameters.md) |
| P25 | [SNTP](COMMUNICATION/time-synchronization.md#parameters) |
| P26 | [TLS](COMMUNICATION/secure-transport.md#parameters) |
| P27 | [Server communication](COMMUNICATION/server-communication.md#parameters) |
| P21-PORTAL, P24, P24-HTTP | [L1_PORTAL](PORTAL/parameters.md) |
| P21-WIFI, P23-WIFI | [L1_WIFI](WIFI/parameters.md) |
| P28 | [L1_STORAGE server profile](STORAGE/server-profile.md#parameters) |
