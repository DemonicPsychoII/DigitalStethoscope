# STORAGE record interface

L1_STORAGE adapts Zephyr settings and the flash backend. Call `storage_init()` once before record access. Callers own their buffers; STORAGE neither joins networks nor chooses retries.

| Operation | Input | Outcome |
| --- | --- | --- |
| `storage_init()` | None | 0 after settings/backend initialization; negative error otherwise. |
| `storage_read(name, data, size)` | Named record, writable caller buffer, exact expected byte count | 0 and a complete record; `-ENOENT` if missing; `-EINVAL` for a stored-size mismatch; negative backend error otherwise. Never use output as credentials after failure. |
| `storage_write(name, data, size)` | Named complete record and readable caller buffer | 0 after a whole-record commit; negative error otherwise. The previous valid record must survive an unsuccessful write. Power-loss behavior needs target evidence. |

The `wifi/network` record contains one complete network name/passphrase structure defined by the WIFI service interface. COMMUNICATION reads it at boot, validates it using `wifi_isValidNetwork()`, and commits only after the selected network has an address. It owns the save retry and retains the old record on failure. STORAGE does not authenticate or encrypt this record. Keep names/passphrases out of logs; clear transient copies after use. Device registration persistence belongs to the later system FHIR design.
