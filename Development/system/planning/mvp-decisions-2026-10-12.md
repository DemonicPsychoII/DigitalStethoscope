# MVP decisions — patient assignment and device hotspot, 12 October 2026

Nico's answers in T3 thread `d5e44f69-2ecc-4a3e-917b-31a7b084c12b` extend the [11 October decisions](mvp-decisions-2026-10-11.md). They replace the 11 October treatment of the captive portal as an optional follow-up and the "client, not embedded web server" statement in the [framework evaluation](framework-and-transport-evaluation.md). Everything else from 11 October stands. This records decisions and proposals, not implemented firmware behavior. Numeric values are proposals.

The MVP has no display or touch. The operator therefore assigns the patient through a phone browser on a device hotspot; the FHIR server stores the assignment. The [patient-assignment sequence](../architecture/patient-assignment-workflow.puml) shows the complete flow.

## Confirmed decisions

- **Hotspot portal is MVP scope.** It provides patient selection and Wi-Fi setup. The serial shell remains a diagnostic fallback for both.
- **Gesture:** a long press of at least 2 s while Idle opens the hotspot. The long press is a documented, separate gesture; ordinary Start/Stop and normal-error acknowledgement keep their meaning. Outside Idle the long press is rejected and nothing changes.
- **No stored Wi-Fi credentials at boot:** startup checks complete and the device enters Idle as usual; Idle then enters Portal automatically with the Wi-Fi setup page, under the same Idle-only network lease as the long press. Saving credentials closes the hotspot and joins the hospital Wi-Fi; on success the device continues with time sync and Device registration (step 1), then returns to Idle. Patient assignment then uses the long press. On connection failure the device returns to Idle with a normal Wi-Fi fault; offline listening stays available and the long press reopens Portal. Credentials are entered in the portal and never echoed back.
- **The FHIR server holds the assignment.** The device registers its own `Device` resource; the selected patient is stored in R4 `Device.patient`. The KIS can also set or clear it, for example via curl or the HAPI web UI during the MVP.
- **Patient list loading:** the device loads the list on the hospital Wi-Fi immediately before switching to hotspot mode, then shows it with its load time. Hospital Wi-Fi is down while the hotspot is open.

## Proposed behavior

1. **Boot and registration.** Join the stored Wi-Fi (no credentials: Wi-Fi setup in Portal first, see above), synchronize time, then `GET /Device/{id}`. Not found (404, or 410 after a deletion) → `PUT /Device/{id}` without a patient. Found → adopt its `patient` as the local assignment; update only device metadata (for example firmware version) with `PATCH`. A blind `PUT` would erase an existing assignment. The ID is derived from a stable hardware identifier and contains a letter (`stetho-…`) because HAPI rejects client-assigned purely numeric IDs.
2. **Open portal (Idle only).** Long press → `GET /Patient?_has:Encounter:patient:status=in-progress&_elements=name,birthDate,identifier&_count=20` → leave hospital Wi-Fi → start WPA2 hotspot with timeout.
3. **Select.** The page lists name, birth date and patient ID only, plus the list load time. The operator confirms one patient explicitly. Nothing is assigned without confirmation.
4. **Assign.** Close the hotspot, rejoin hospital Wi-Fi, `PATCH /Device/{id}` with `patient` and `If-Match` on the version read before the hotspot opened (409 → no change, normal fault), then read back. Only a matching readback becomes the local assignment; failure leaves the device unassigned and latches a normal fault.
5. **Measure.** Start does no network work (network exclusion stays). The controller freezes the local assignment into the session. The serial log only states whether an assignment is present and its `Device` version, never the patient reference. No assignment → listening and measurement still work, but nothing is sent.
6. **Send.** Under the Idle network lease, NET re-reads `Device.patient` before creating the Observation. A different or cleared assignment means no send and a normal fault. Otherwise it creates the Observation as defined in the write contract below, with the frozen `subject` and `device`, then matching readback. The result is never relabelled: the subject stays the patient confirmed when the session started. FHIR offers no atomic condition across `Device` and `Observation`, so a KIS change between the check and the create is a residual race. To expose it, NET records the `Device` `meta.versionId` at the pre-send check and re-reads the Device after the Observation readback. Any version change marks the delivery Unverified with a normal fault for review instead of Sent; comparing the version, not only the patient reference, also catches an A→B→A reassignment. Every update, including metadata, changes the version, so a false Unverified is possible but a missed reassignment is not.

## FHIR write contract (D08) — decided 12 October after backend simulation

A simulated device run against the local HAPI server (synthetic data) showed that the server silently overwrites an Observation when a `PUT` reuses an ID with a different value, and ignores `If-None-Match: *`. The R4 vital-signs heart-rate profile also failed `$validate` with `effectivePeriod` (invariant vs-1) but passed with `effectiveDateTime`. Decisions:

- **Create, never update.** `POST /Observation` with `If-None-Exist: identifier=urn:stetho:observation|<device>-<boot>-<session>` and `Prefer: return=minimal`. The boot part comes from the hardware random number generator, so no counter has to survive a reboot. The server assigns the resource ID; NET reads it from `Location`. HAPI 8.12.0 sends `Location` and `Content-Location` on both 201 and the conditional-create 200, also with `return=minimal` (verified locally); FHIR R4 does not require it for the 200. Without either header, NET looks the resource up with `GET /Observation?identifier=<identifier>`: exactly one match is read back, zero or several matches end Unverified. A lost-response retry, or an identifier collision, returns the existing resource (200) instead of overwriting it; the full-payload readback then decides Sent or Unverified. This replaces the earlier stable-ID `PUT`.
- **Time:** `effectiveDateTime` is the end of the measurement interval (measurement time, never send time). Start and duration stay in the frozen local result and evidence, not in FHIR. A `component` or extension can be added later if a receiver needs the interval.
- **Readback:** for 201 and 200 alike, Sent requires the stored resource to match the frozen payload in identifier, `subject`, `device`, code, unit, value and `effectiveDateTime`. A 200 cannot distinguish a lost-response retry from an identifier collision; only this full match can. Any difference stays Unverified. Compare the value numerically, because the server normalizes decimals (`72.50` returns as `72.5`).
- **IDs:** client-assigned IDs (Device) are at most 64 characters of `A–Z a–z 0–9 - .` and not purely numeric, for example `stetho-a1b2c3d4e5f6`.
- **Patient list:** `_include=Encounter:subject` ignores `_elements` and returned complete patients including address and phone (27 KB for 20). The `_has` query above returns only name, birth date and identifier (16 KB for 20).

Server-side findings (certificate without subjectAltName, no authentication, no validation on write, LOINC not loaded) are backend tasks, not device behavior.

## Wrong-patient risk (not a completed ISO 14971 analysis)

Without a display, the operator cannot see the active patient on the device. Proposed controls: explicit confirmation on the phone with name and birth date; readback before the assignment is accepted; freeze at session start; assignment presence and Device version in the serial log; pre-send comparison with the server assignment; no assignment, no send. Stale lists are limited by loading immediately before the hotspot opens and showing the load time.

A remaining hazard is that the assignment persists: a measurement on the next patient goes to the previous one if nobody reassigns the device. Proposed control, **pending owner decision:** clear the assignment after a verified delivery, so every new patient needs a fresh selection. Alternative: a maximum assignment age.

## Security and privacy notes

The device now accepts inbound connections while the hotspot is open. Proposed controls: WPA2 with a per-device passphrase outside source code; hotspot only in Idle, with a timeout; minimal patient fields; no credentials or patient data in logs; Wi-Fi password write-only in the page. A portal login is still open. The hotspot passphrase provisioning method is still open.

## Open points

- Assignment lifetime after delivery (see risk above).
- Portal login beyond WPA2, and how the per-device hotspot passphrase is provisioned.
- `Device.patient` means "patient to whom the device is affixed" in R4. It is accepted for the MVP; `DeviceUseStatement` is the more precise alternative if the lab backend requires it.
- The lab server needs a seeded in-progress `Encounter` for the synthetic `Patient/stetho-test-01`.
- Zephyr on ESP32-S3: verify SoftAP, HTTP server and station/AP switching on target before relying on them. A captive-portal DNS redirect is optional; the page URL can be printed on the device label.

## Effort

The new [PORTAL task](mvp-implementation-timeline.md#portal--implement-hotspot-portal-and-patient-assignment) is estimated at 16 h. The plan was already full, so implementation now ends after the 18 November deadline; see the timeline for the shifted dates.

Created by Claude-Opus-5.5 on behalf of Nico running in T3 Code through Claude Code.
