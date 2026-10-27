# PORTAL parameters

Selected page and HTTP limits. COMMUNICATION owns the setup timer and radio workflow; WIFI owns the hotspot and station operations.

| ID | Parameter | Value / candidate | Verification status | Owners |
| --- | --- | --- | --- | --- |
| P21-PORTAL | Page entry and activity (allocation of P21) | Manual phone hotspot join/rejoin, QR opens http://192.168.4.1/; selection/input/Rescan signal activity; polling does not | Project choices; phone/QR behavior needs a device run | PORTAL |
| P24 | Portal request limits | Rescan allowed after failed join; Connect returns 409 until rescan completes and selection is ready; fixed hotspot 192.168.4.1, HTTP port 80, manual phone join/rejoin; Activity at most 1/s; status poll 1 s; request queue length 4; HTTP client inactivity 5 s; HTTP server stop confirmation 1 s | Project choices; target scheduling and stop-event timing remain unverified | PORTAL |
| P24-HTTP | Bounded HTTP buffers and connections (allocation of P24) | URL-encoded form body at most 320 bytes; request queue 4; HTTP clients 8, backlog 4; client buffer 1024 bytes; HTTP/1.1; server readiness/stop wait 1 s | Project limits; target scheduling needs evidence | PORTAL |
