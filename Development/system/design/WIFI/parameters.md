# L1_WIFI operation parameters

These parameters define the `L1_WIFI` operation limits. Retry budgets belong to `L2_COMMUNICATION`, and page limits belong to `L1_PORTAL`.

| ID | Parameter | Value | Basis | Owners |
| --- | --- | --- | --- | --- |
| P23-WIFI | Radio and address operation limits (allocation of `L2_COMMUNICATION` [P23](../COMMUNICATION/parameters.md)) | Connect wait 15 s; scan wait 10 s; scan cancellation and disconnect confirmation 1 s each; scan cache holds the strongest 16 distinct supported SSIDs; overflow and caller truncation follow [bounded results](interfaces-and-behavior.md#failure-boundaries-and-bounded-results) | – | L2_COMMUNICATION, L1_WIFI |
| P21-WIFI | Hotspot radio configuration (shared setup configuration with `L1_PORTAL` P21-PORTAL) | Open hotspot; fixed IPv4 address 192.168.4.1/24 (netmask 255.255.255.0); DHCP pool 192.168.4.10 through 192.168.4.13; at most 1 associated client | [REQ-12](../../requirements/system-requirements.md#req-12); HTTP connections are separate | L1_WIFI |

The DHCP pool starts at host byte 10 and supplies four consecutive addresses; the Zephyr DHCPv4 server configures this count via `CONFIG_NET_DHCPV4_SERVER_ADDR_COUNT` (The Zephyr Project, *Zephyr DHCPv4 Kconfig*, source repository, revision `357467a011cd2557a1a3f0b4be83d817c4addc9b`, [Kconfig](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/subsys/net/lib/dhcpv4/Kconfig), accessed 24 October 2026). The one-associated-client limit is separate from the lease-pool size.

The 15 s connect and 10 s scan limits are total deadlines owned by `L2_COMMUNICATION`. It calls `wifi_waitForConnection` and `wifi_waitForScanResult` repeatedly with the event-check interval of 200 ms (P23) until the result arrives or the deadline passes. One `L1_WIFI` call waits at most the interval it is given; `L1_WIFI` neither clamps nor rejects that interval. Scan cancellation and disconnect confirmation are fixed `L1_WIFI` deadlines of 1 s each; when one expires, the call fails.
