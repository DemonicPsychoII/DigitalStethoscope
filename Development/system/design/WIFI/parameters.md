# Wi-Fi operation parameters

These are selected L1 operation limits; target measurements remain pending (TICKET-182). Controller retry budgets are in COMMUNICATION, page limits in PORTAL.

| ID | Parameter | Value / candidate | Verification status | Owners |
| --- | --- | --- | --- | --- |
| P23-WIFI | Radio and address operation limits (allocation of P23) | Connect wait 15 s; scan wait 10 s; scan cancellation and disconnect confirmation 1 s each; scan cache the strongest 16 distinct supported SSIDs; overflow and caller truncation follow [bounded results](interfaces-and-behavior.md#failure-boundaries-and-bounded-results) | Project limits; driver cancellation and address readiness need target evidence | WIFI |
| P21-WIFI | Hotspot radio configuration (allocation of P21) | Open hotspot; fixed IPv4 address 192.168.4.1/24 (netmask 255.255.255.0); DHCP pool 192.168.4.10 through 192.168.4.13; at most 1 associated client | Project choices; HTTP connections are separate | WIFI |

The DHCP pool starts at host byte 10; the pinned backend's `CONFIG_NET_DHCPV4_SERVER_ADDR_COUNT` default supplies four consecutive addresses. Source: The Zephyr Project, *Zephyr DHCPv4 Kconfig*, source repository, revision `357467a011cd2557a1a3f0b4be83d817c4addc9b`, publication year not verified, [Kconfig](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/subsys/net/lib/dhcpv4/Kconfig), accessed 24 October 2026. The one-associated-client limit is separate from the lease-pool size. These configuration choices do not establish target DHCP behavior.

The 15 s connect and 10 s scan limits are total deadlines owned by COMMUNICATION. It calls `wifi_waitForConnection` and `wifi_waitForScanResult` repeatedly with a short interval until the result arrives or the deadline passes. One L1 call waits at most the interval it is given; L1 neither clamps nor rejects that interval. Scan cancellation and disconnect confirmation are fixed L1 deadlines of 1 s each; when one expires, the call fails.
