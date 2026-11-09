# Server profile naming — 5 November 2026

Nico decided on 5 November 2026 in T3 Code (conversation link not recorded) to rename the separately
flashed image that carries the one server's HTTPS base URL, its certificate as the only trust anchor and
the server keep-alive. Until then it was called the provisioning image. That name collided with Wi-Fi
provisioning through the serial shell and the hotspot page. This is a project decision, not a measurement.

## Decision

1. The image, its partition, the host tool and the flash command use the name **server profile**:
   server profile image, server profile partition (`server_profile_partition`),
   `tools/server-profile/server_profile.py`, `flash-server-profile.ps1` and `erase-flash.ps1 -ServerProfile`.
   The deployment files moved to `coding/server-profiles/`; each one is still a deployment file.
2. The on-flash format stays unchanged, because devices are already flashed: magic `STPV`, version 1,
   field layout and the fixed start `0xF00000`. Parameter, requirement and verification tags (P28-*,
   REQ-*, VT-*) stay unchanged.
3. Wi-Fi provisioning keeps its name. Dated decision records, presentations, PR titles and tickets keep
   the earlier name.

## Applied in

- [Server profile architecture](../architecture/system/server-profile.md) and
  [server profile design](../design/STORAGE/server-profile.md)
- [STORAGE flash layout](../design/STORAGE/interfaces-and-behavior.md#flash-layout) and
  [TLS trust inputs](../design/COMMUNICATION/secure-transport.md#trust-and-server-profile-inputs)
- [Server profiles](../coding/server-profiles/README.md), firmware and tools in [`coding/`](../coding/app/README.md)
