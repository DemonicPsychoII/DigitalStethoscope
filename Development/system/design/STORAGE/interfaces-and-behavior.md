# STORAGE record interface

L1_STORAGE adapts Zephyr settings and the flash backend. Call `storage_init()` once before record access. Callers own their buffers; STORAGE neither joins networks nor chooses retries.

| Operation | Input | Outcome |
| --- | --- | --- |
| `storage_init()` | None | 0 after settings/backend initialization; negative error otherwise. |
| `storage_read(name, data, size)` | Named record, writable caller buffer, exact expected byte count | 0 and a complete record; `-ENOENT` if missing; `-EINVAL` for a stored-size mismatch; negative backend error otherwise. Never use output as credentials after failure. |
| `storage_write(name, data, size)` | Named complete record and readable caller buffer | 0 after a whole-record commit; negative error otherwise. The previous valid record must survive an unsuccessful write; this is a required outcome pending backend-mechanism confirmation and target verification, not an established guarantee. Power-loss behavior also needs target evidence. |

The `wifi/network` record contains the complete 98-byte `wifi_network` record defined by the [WIFI network-record contract](../WIFI/interfaces-and-behavior.md#network-record), including both fixed-size arrays. COMMUNICATION reads it at boot, validates it using `wifi_isValidNetwork()`, and commits only after the selected network has an address. It owns the save retry and requires preservation of the old record on failure, subject to that pending backend verification. STORAGE does not authenticate or encrypt this record. Keep names/passphrases out of logs; clear transient copies after use. The separate `fhir/device-registration` record follows the versioned, whole-record [registration contract](../COMMUNICATION/server-communication.md#registration-record). COMMUNICATION validates physical identity and server binding and publishes readiness only after successful commit. Failed registration-record access follows the registration-only failure policy; it does not make generic device settings faults harmless.

## Flash layout

The ESP32-S3-WROOM-1-N16R8 has 16 MB flash. The board devicetree includes Zephyr's 4 MB Espressif default table (`partitions_0x0_amp.dtsi` → `partitions_0x0_amp_4M.dtsi`), and the application overlay widens `flash0` to 16 MB [1]. The application boots with Espressif Simple Boot, without MCUboot: a single image is flashed at an SoC-defined offset, and OTA and slot management are unavailable [2]. Settings (ZMS) use `storage_partition`, because no `zephyr,settings-partition` is chosen [3].

| Offset | Size | Partition | Use |
| --- | --- | --- | --- |
| `0x000000` | 64 KiB | `boot_partition` (`mcuboot`) | Board default; no MCUboot |
| `0x010000` | 64 KiB | `sys_partition` | Board default |
| `0x020000` | 1344 KiB | `slot0_partition` (`image-0`) | Application code partition (`zephyr,code-partition`) |
| `0x170000` | 1344 KiB | `slot1_partition` (`image-1`) | Reserved by the board default; no OTA |
| `0x2C0000` | 448 KiB | `slot0_appcpu_partition` | Reserved by the board default |
| `0x330000` | 448 KiB | `slot1_appcpu_partition` | Reserved by the board default |
| `0x3A0000` | 32 KiB | `slot0_lpcore_partition` | Reserved by the board default |
| `0x3A8000` | 32 KiB | `slot1_lpcore_partition` | Reserved by the board default |
| `0x3B0000` | 192 KiB | `storage_partition` | Settings: `wifi/network`, `fhir/device-registration` |
| `0x3E0000` | 124 KiB | `scratch_partition` | Reserved by the board default |
| `0x3FF000` | 4 KiB | `coredump_partition` | Board default |
| `0x400000` | 64 KiB | `provisioning_partition` (proposed) | Provisioning image: server endpoint, keep-alive and certificate |

The remaining flash above `0x410000` stays unassigned. The application overlay adds `provisioning_partition`; the board default rows stay unchanged.

The provisioning image is the only source of the server endpoint and certificate ([TLS trust inputs](../COMMUNICATION/secure-transport.md#trust-and-provisioning-inputs)). A host tool builds it; a separate flash command writes it to `0x400000`. The firmware reads it through the flash map and never writes it. Proposed version 1 format, little-endian:

| Field | Size | Content |
| --- | --- | --- |
| Magic | 4 bytes | ASCII `STPV` |
| Version | 1 byte | `1` |
| Base URL length, base URL | 2 bytes + at most 256 bytes | Canonical HTTPS FHIR base URL as defined by the [server binding](../COMMUNICATION/server-communication.md#physical-identity-and-server-binding) |
| Server keep-alive | 4 bytes | Server idle timeout in seconds; the device subtracts 5 seconds |
| Certificate length, certificate | 2 bytes + at most 8192 bytes | PEM public server certificate |
| CRC-32 | 4 bytes | IEEE CRC-32 over all preceding bytes |

Erased flash, an unknown magic or version, an out-of-range length, a CRC mismatch or an unparsable certificate make the image invalid. The image keeps settings and provisioning apart: erasing settings never removes the server, and rewriting the server never touches Wi-Fi credentials or the registration record.

Own observation on 2 November 2026: flashing a test build (`feature/time-synchronization` at `b6cccb8` plus the full-MAC hotspot change) with `flash-firmware.ps1` wrote 671,744 bytes at `0x00000000`, and the device booted with Espressif Simple Boot. Only the image range was written. Target verification remains open: a read-back must show that the firmware flash command leaves `0x400000` untouched, a settings erase must leave it intact, and a corrupted image must be rejected at boot.

[1] The Zephyr Project, *ESP32-S3-DevKitC board devicetree and Espressif partition tables*, source revision `357467a011cd2557a1a3f0b4be83d817c4addc9b`, [esp32s3_devkitc_procpu.dts](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/boards/espressif/esp32s3_devkitc/esp32s3_devkitc_procpu.dts) and [partitions_0x0_amp_4M.dtsi](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/dts/vendor/espressif/partitions_0x0_amp_4M.dtsi), accessed 2 November 2026; project [board overlay](../../coding/app/boards/esp32s3_devkitc_procpu.overlay).

[2] The Zephyr Project, *Espressif SoC Kconfig, `ESP_SIMPLE_BOOT`*, source revision `357467a011cd2557a1a3f0b4be83d817c4addc9b`, [soc/espressif/common/Kconfig](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/soc/espressif/common/Kconfig), accessed 2 November 2026. Simple Boot is the default without MCUboot; the project [prj.conf](../../coding/app/prj.conf) enables no MCUboot.

[3] The Zephyr Project, *Settings ZMS backend*, source revision `357467a011cd2557a1a3f0b4be83d817c4addc9b`, [settings_zms.c](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/subsys/settings/src/settings_zms.c), lines 21–24, accessed 2 November 2026.
