# MVP decisions — Wi-Fi setup, registration and delivery, 15 October 2026

Team discussion on 15 October, given by Nico in T3 Code. These decisions supersede the patient-assignment parts of the
[12 October decisions](mvp-decisions-2026-10-12.md) and the related parts of the [13 October](mvp-decisions-2026-10-13.md)
and [14 October](mvp-decisions-2026-10-14.md) records. Everything else from 14 October stands, including the retry rule.
The [sequence diagram](../architecture/patient-assignment-workflow.puml) shows the complete flow.
This records decisions, not implemented firmware behavior.

## Confirmed decisions

1. **Boot without Wi-Fi configuration.** The device must start and allow offline listening without stored credentials.
2. **Wi-Fi setup page.** Without stored credentials, the device opens a hotspot (access point) with a page.
   The operator selects the network from a scan list and enters the password.
3. **Persistent credentials.** The device saves SSID and password in a flash section (Zephyr settings partition),
   so they survive restarts.
4. **Persistent Device registration.** The device registers itself on the server once and saves the returned
   device-id in flash. After a restart it reuses that id, so the server does not get a new Device per restart.
5. **No patient selection on the device.** The device does not load, show, store or check patient data.
   The server provides a separate workflow that links a Device and its recent Observations to a patient.
   That workflow is outside the stethoscope MVP.
6. **Minimal measure and delivery.** Start/Stop stay. No network traffic during a measurement. After Stop the device
   sends the Observation and accepts the server receipt (`201 Created`, or `200` for an existing conditional create).
   No pre-send check, no readback, no assignment guard.

## Resulting behavior

- **Observation:** `POST /Observation` with `If-None-Exist` on the device/boot/session identifier, `device = Device/{id}`,
  no `subject`, LOINC 8867-4, UCUM `/min`, `effectiveDateTime` = end of the measurement interval (unchanged from D08).
- **Retry:** unchanged from 14 October: up to 3 retries (4 attempts) within 10 s, then a normal send fault.
  Conditional create prevents duplicates.
- **Registration:** `POST /Device` with the hardware serial as identifier and no patient. The server assigns the id.
  A stored id is reused without a server call.
- **Reopen setup:** the 12 October gesture stays: a long press of at least 2 s in Idle opens the setup page again,
  for example after a wrong password. A failed join gives Idle with a normal Wi-Fi fault; offline listening stays available.
- **Hotspot security:** WPA2 with a per-device passphrase outside source code, Idle only, with a timeout.
  The Wi-Fi password is write-only on the page and never logged.

## Requirement changes

- REQ-09: the result reaches the server linked to this device (was: the assigned patient).
- REQ-12: the hotspot page sets up Wi-Fi; credentials survive a restart (was: patient selection).
- REQ-15 (new): the device keeps its server registration across restarts.
- VT-07 and VT-14 follow; see [verification](../testing/specification-verification.md).

## Superseded

- 12 October: `Device.patient` as assignment store, the patient list query, patient selection on the phone,
  `If-Match` PATCH, assignment readback, the frozen assignment, the pre-send and post-readback Device checks,
  the Unverified state from a Device version change, and the wrong-patient controls on the device.
- 12 October D08: the full-payload Observation readback. Create-only, `If-None-Exist`, `effectiveDateTime` and the
  ID rules stay.
- 12 October registration with a client-assigned `PUT /Device/stetho-…`: replaced by server-assigned id stored in flash.
- 13 October: the pre-send assignment check in `L2_COMMUNICATION`.
- 14 October: "patient assignment lifetime remains open" is no longer a device question.

## Open points

- Server workflow for the patient link (owner, tool, how "recent" data is found). Outside the MVP.
- Behavior when the stored device-id no longer exists on the server (for example after a server reset).
  HAPI rejects an Observation with an unknown Device reference. Proposal: check `GET /Device/{id}` at boot,
  re-register on 404/410 and save the new id.
- Whether to keep the full-payload readback as an optional diagnostic. Current decision: no.

Created by Claude-Opus-5.5 on behalf of Nico running in T3 Code through Claude Code.
