# STORAGE record interface

L1_STORAGE adapts Zephyr settings and the flash backend. Call `storage_init()` once before record access. Callers own their buffers; STORAGE neither joins networks nor chooses retries.

| Operation | Input | Outcome |
| --- | --- | --- |
| `storage_init()` | None | 0 after settings/backend initialization; negative error otherwise. |
| `storage_read(name, data, size)` | Named record, writable caller buffer, exact expected byte count | 0 and a complete record; `-ENOENT` if missing; `-EINVAL` for a stored-size mismatch; negative backend error otherwise. Never use output as credentials after failure. |
| `storage_write(name, data, size)` | Named complete record and readable caller buffer | 0 after a whole-record commit; negative error otherwise. The previous valid record must survive an unsuccessful write; this is a required outcome pending backend-mechanism confirmation and target verification, not an established guarantee. Power-loss behavior also needs target evidence. |

The `wifi/network` record contains the complete 98-byte `wifi_network` record defined by the [WIFI network-record contract](../WIFI/interfaces-and-behavior.md#network-record), including both fixed-size arrays. COMMUNICATION reads it at boot, validates it using `wifi_isValidNetwork()`, and commits only after the selected network has an address. It owns the save retry and requires preservation of the old record on failure, subject to that pending backend verification. STORAGE does not authenticate or encrypt this record. Keep names/passphrases out of logs; clear transient copies after use. Device registration persistence belongs to the later system FHIR design.
