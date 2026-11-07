# STORAGE record interface

L1_STORAGE adapts Zephyr settings and the flash backend. Call `storage_init()` once before record access. Callers own their buffers; STORAGE neither joins networks nor chooses retries.

| Operation | Input | Outcome |
| --- | --- | --- |
| `storage_init()` | None | 0 after settings/backend initialization; negative error otherwise. |
| `storage_read(name, data, size)` | Named record, writable caller buffer, exact expected byte count | 0 and a complete record; `-ENOENT` if missing; `-EINVAL` for a stored-size mismatch; negative backend error otherwise. Never use output as credentials after failure. |
| `storage_write(name, data, size)` | Named complete record and readable caller buffer | 0 after a whole-record commit; negative error otherwise. The previous valid record must survive an unsuccessful write; this is a required outcome pending backend-mechanism confirmation and target verification, not an established guarantee. Power-loss behavior also needs target evidence. |

The `wifi/network` record contains the complete 98-byte `wifi_network` record defined by the [WIFI network-record contract](../WIFI/interfaces-and-behavior.md#network-record), including both fixed-size arrays. COMMUNICATION reads it at boot, validates it using `wifi_isValidNetwork()`, and commits only after the selected network has an address. It owns the save retry and requires preservation of the old record on failure, subject to that pending backend verification. STORAGE does not authenticate or encrypt this record. Keep names/passphrases out of logs; clear transient copies after use. The separate `fhir/device-registration` record follows the versioned, whole-record [registration contract](../COMMUNICATION/server-communication.md#registration-record). COMMUNICATION validates physical identity and server binding and publishes readiness only after successful commit. Failed registration-record access follows the registration-only failure policy; it does not make generic device settings faults harmless.

## Flash layout

The ESP32-S3-WROOM-1-N16R8 has 16 MB flash. The application overlay widens `flash0` to 16 MB, but the partitions still come from the board's 4 MB Espressif default table (`partitions_0x0_amp.dtsi` → `partitions_0x0_amp_4M.dtsi`) [1]. The application boots with Espressif Simple Boot, without MCUboot: a single image is flashed at an SoC-defined offset, and OTA and slot management are unavailable [2]; the build sets `CONFIG_FLASH_LOAD_OFFSET=0`. Settings (ZMS) use `storage_partition`, because no `zephyr,settings-partition` is chosen [3].

The project layout uses the whole 16 MB. Settings and the server profile each have a fixed start address; their sizes are independent [5]:

| Range | Size | Partition | Content |
| --- | --- | --- | --- |
| `0x000000`–`0xE7FFFF` | 14848 KiB (14.5 MB) | `slot0_partition` (`application`), `zephyr,code-partition` | Simple Boot image: header, loaded segments and flash-mapped code and data |
| `0xE80000`–`0xEAFFFF` | 192 KiB | `storage_partition` (`storage`) | Settings (ZMS): `wifi/network`, `fhir/device-registration` |
| `0xEB0000`–`0xEFFFFF` | 320 KiB | unassigned | Growth room for settings |
| `0xF00000`–`0xF2FFFF` | 192 KiB | `server_profile_partition` (`server-profile`) | Server profile image: server endpoint, keep-alive and certificate; read-only for the firmware |
| `0xF30000`–`0xFFFFFF` | 832 KiB | unassigned | Growth room for the server profile |

Neither start depends on the other partition's size. Settings can grow to 512 KiB without moving the server profile, and the server profile can grow to 1 MB without moving settings. The server profile start must never change between firmware versions, because an updated firmware must still find an image that was flashed earlier. Both starts are aligned to the 4 KiB erase sector and to 64 KiB. This placement is a project decision [5].

Worst-case sizing, calculated from source and not measured:

- **Settings.** About 0.6 KiB of live data. The ZMS backend stores each setting as a name entry, a data entry and a linked-list entry; every entry has a 16-byte allocation table entry, and values of at most 8 bytes, such as the linked-list node, sit inside it [3][4]. `wifi/network` (98 bytes) needs about 160 bytes, `fhir/device-registration` (343 bytes, [registration record](../COMMUNICATION/server-communication.md#registration-record)) about 416 bytes, and the list head and updates about 50 bytes. ZMS needs at least two sectors, because one sector stays empty for garbage collection [4].
- **Server profile.** The version 1 format below has at most 8,465 bytes, which fits in three 4 KiB sectors. The lab image built from `lab-hapi.toml` has 1,446 bytes: a 30-byte base URL and a 1,399-byte PEM certificate (calculated from the file at commit `3535a857aacc7a99d3db3ff61c6515514b1670d9`, 4 November 2026).
- **Flash geometry.** Erase sector 4 KiB, write block 4 bytes [4].

The board default's `boot`, `sys`, second image, second-core, low-power-core, scratch and core-dump partitions are not defined: Simple Boot needs no MCUboot, there is no OTA, only one core runs the application and no core dump is configured. The observed image of 2 November 2026 places loaded segments at `0x20`, `0x4F2C` and `0x15BAC` and flash-mapped code and data at `0x20000` and `0x90000`; about 656 KiB of the application partition are in use. The partition size only bounds the image; SoC mapping limits must be checked if the image grows far.

Moving settings from `0x3B0000` to `0xE80000` loses the stored Wi-Fi network and Device registration once. The device then opens Wi-Fi setup, and conditional registration recovers the same Device through its physical identifier. A full chip erase also removes the server profile image, which must then be flashed again.

### Build-system plan

1. **Layout.** A new `boards/flash-layout.dtsi`, included by the board overlay, defines two start addresses and two sizes (settings `0xE80000` and 192 KiB, server profile `0xF00000` and 192 KiB), deletes the board's partition node and defines `slot0_partition` from offset 0 up to the settings start, `storage_partition` and `server_profile_partition`. A build check fails if settings do not end before the server profile start or the server profile does not end within the 16 MB, and when the server profile start differs from `0xF00000`, because an image flashed for one layout must stay readable by every firmware version. The size may grow up to 1 MB; the image-fit assertion below keeps it large enough for the largest image. The board's `zephyr,code-partition` choice stays on `slot0_partition`; settings keep using `storage_partition`.
2. **Firmware reader.** L1_STORAGE reads the image through `flash_area_open(FIXED_PARTITION_ID(server_profile_partition))`, validates it once at boot and hands endpoint, keep-alive and certificate to COMMUNICATION. A build assertion checks that the maximum image fits the partition.
3. **Host tool.** `Development/system/coding/tools/server-profile/` builds the image from one [deployment file](server-profile.md#deployment-file), validates it, checks the certificate and appends the CRC-32. It reads the partition offset and size from the build's generated devicetree, so no offset is written twice.
4. **Flash command.** `flash-server-profile.ps1 <COM port> <deployment file>` builds that image and writes it to the server profile offset with the pinned esptool ([commands](server-profile.md#commands)). `flash-firmware.ps1` stays unchanged and writes only the firmware image.
5. **Verification.** Host tests cover the tool (format, limits, CRC) and the reader (valid, erased, corrupted, oversized images). On target: build and boot with the new table, read back the server profile partition after a firmware flash, reject a corrupted image, and keep the image across a settings-partition erase.

The server profile image is the only source of the server endpoint and certificate ([TLS trust inputs](../COMMUNICATION/secure-transport.md#trust-and-server-profile-inputs)). A host tool builds it; a separate flash command writes it to the server profile offset `0xF00000`. The firmware reads it through the flash map and never writes it. Proposed version 1 format, little-endian:

| Field | Size | Content |
| --- | --- | --- |
| Magic | 4 bytes | ASCII `STPV` |
| Version | 1 byte | `1` |
| Base URL length, base URL | 2 bytes + at most 256 bytes | Canonical HTTPS FHIR base URL as defined by the [server binding](../COMMUNICATION/server-communication.md#physical-identity-and-server-binding) |
| Server keep-alive | 4 bytes | Server idle timeout in seconds, 6 to 4,294,967,295; the device subtracts 5 seconds, and COMMUNICATION rejects a smaller value at boot as an invalid configuration |
| Certificate length, certificate | 2 bytes + at most 8192 bytes | PEM public server certificate |
| CRC-32 | 4 bytes | IEEE CRC-32 over all preceding bytes; detects corruption only. The MVP uses no signature. |

Erased flash, an unknown magic or version, an out-of-range length or a CRC mismatch make the image invalid; the reader checks only this structure. The content checks after it make the configuration invalid instead: WIFI rejects an unusable URL, an unparsable certificate or a missing matching Subject Alternative Name, and COMMUNICATION rejects a server keep-alive below 6 seconds, as the [server profile design](server-profile.md#device-behavior) lists. Either way secure transport stays unavailable. The image keeps settings and the server profile apart: erasing only the settings partition never removes the server, and rewriting the server never touches Wi-Fi credentials or the registration record. A whole-flash erase (`flash-firmware.ps1 -Erase`) removes the image too and requires flashing it again.

Own observation on 2 November 2026: flashing a test build (`feature/time-synchronization` at `b6cccb8` plus the full-MAC hotspot change) with `flash-firmware.ps1` wrote 671,744 bytes at `0x00000000`, and the device booted with Espressif Simple Boot. Only the image range was written. Target verification remains open under [TICKET-214](https://nfrie.atlassian.net/browse/TICKET-214), following the build-system plan above.

[1] The Zephyr Project, *ESP32-S3-DevKitC board devicetree and Espressif partition tables*, source revision `357467a011cd2557a1a3f0b4be83d817c4addc9b`, [esp32s3_devkitc_procpu.dts](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/boards/espressif/esp32s3_devkitc/esp32s3_devkitc_procpu.dts) and [partitions_0x0_amp_4M.dtsi](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/dts/vendor/espressif/partitions_0x0_amp_4M.dtsi), accessed 2 November 2026; project [board overlay](../../coding/app/boards/esp32s3_devkitc_procpu.overlay).

[2] The Zephyr Project, *Espressif SoC Kconfig, `ESP_SIMPLE_BOOT`*, source revision `357467a011cd2557a1a3f0b4be83d817c4addc9b`, [soc/espressif/common/Kconfig](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/soc/espressif/common/Kconfig), accessed 2 November 2026. Simple Boot is the default without MCUboot; the project [prj.conf](../../coding/app/prj.conf) enables no MCUboot.

[3] The Zephyr Project, *Settings ZMS backend*, source revision `357467a011cd2557a1a3f0b4be83d817c4addc9b`, [settings_zms.c](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/subsys/settings/src/settings_zms.c), lines 21–24, accessed 2 November 2026.

[4] The Zephyr Project, *ZMS allocation table entry, settings ZMS entries and ESP32-S3 flash geometry*, source revision `357467a011cd2557a1a3f0b4be83d817c4addc9b`: [zms_priv.h](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/subsys/kvss/zms/zms_priv.h) (`struct zms_ate`, 16 bytes with 8 bytes of inline data), [zms.c](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/subsys/kvss/zms/zms.c) (mount rejects fewer than two sectors), [settings_zms.c](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/subsys/settings/src/settings_zms.c) and [settings_zms.h](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/subsys/settings/include/settings/settings_zms.h) (name, data and 8-byte linked-list entries per setting), [esp32s3_common.dtsi](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/dts/xtensa/espressif/esp32s3/esp32s3_common.dtsi) (`flash0`: `erase-block-size = <4096>`, `write-block-size = <4>`), accessed 4 November 2026. [Source register](../../../../thesis-material/quellen.md#zephyr_zms_sizing_357467a).

[5] Nico, *Flash layout decision*, personal communication, T3 Code, 4 November 2026. [Source register](../../../../thesis-material/quellen.md#nico_flash_layout_decision_20261104). Project decision, not a measurement.
