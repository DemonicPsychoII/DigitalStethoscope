# PORTAL parameters

These parameters define the page and HTTP limits of `L1_PORTAL`. `L2_COMMUNICATION` owns the setup timer and radio workflow. `L1_WIFI` owns the hotspot and station operations.

| ID | Parameter | Value | Basis | Owners |
| --- | --- | --- | --- | --- |
| P21-PORTAL | Page entry and activity | Client device joins or rejoins the device hotspot manually; QR code opens http://192.168.4.1/; selection, input and Rescan signal activity; polling does not | – | L1_PORTAL |
| P24 | Portal request limits | Rescan allowed after failed join; Connect returns 409 until rescan completes and selection is ready; fixed hotspot address 192.168.4.1, HTTP port 80; Activity at most 1/s; status poll 1 s; request queue length 4; HTTP client inactivity 5 s; HTTP server stop confirmation 1 s | – | L1_PORTAL |
| P24-HTTP | Bounded HTTP buffers and connections (allocation of P24) | URL-encoded form body at most 320 bytes; request queue 4; HTTP clients 8, backlog 4; client buffer 1024 bytes; HTTP/1.1; server readiness and stop wait 1 s | – | L1_PORTAL |
