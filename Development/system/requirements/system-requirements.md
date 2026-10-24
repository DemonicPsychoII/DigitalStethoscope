# System requirements (MVP)

The current baseline names the decisions behind this table;
the decision log records each change. Every requirement is checked by Nico on
the finished device with available equipment: headphones, phone, laptop, the HAPI web page, a pulse oximeter or
smartwatch and test-tone audio. The later design stage defines how the device achieves
these outcomes and selects internal parameters. Flows are shown in the [use-case diagrams](use-cases.md).

Registration and certificate tests remain later FHIR acceptance, not Wi-Fi setup prerequisites.

Methods: **T** test (measured), **D** demonstration (shown working).

| ID | Requirement | How it is tested | Method | Pass |
|---|---|---|---|---|
| REQ-01 | After power-on the device stays silent until Start is pressed. | Power on with volume at maximum and headphones on. | D | Silence until Start. |
| REQ-02 | After Start the operator hears heart sounds. | Chestpiece on own chest, Raw filter, press Start. | D | Heartbeat audible within 2 s of Start. |
| REQ-03 | The 3-position switch selects the Raw, Murmur or BPM listening filter. | Play 100 Hz, 400 Hz and 2 kHz tones from a laptop through an earbud held on the chestpiece diaphragm, at one fixed laptop volume and device volume for all positions. First confirm each tone is clearly audible in Raw; Raw is the reference. Tones follow the bands chosen in the filter study; these fit the current candidates (Murmur 40â€“800 Hz, BPM 25â€“150 Hz). | D | Compared with Raw: Murmur keeps 100 Hz and 400 Hz, 2 kHz clearly quieter. BPM keeps 100 Hz, 400 Hz and 2 kHz clearly quieter. |
| REQ-04 | The potentiometer sets the volume from silent to maximum. | Turn through the full range while listening. | D | Silent at minimum; loudest output at the maximum endpoint; no crackling throughout the sweep. |
| REQ-05 | Listening has no noticeable delay. | Tap the chestpiece and listen. | D | Tap heard together with the touch; no echo or lag noticeable. |
| REQ-06 | A heart session of at least 15 s gives a heart rate. | 10 sessions of 30 s and 3 sessions stopped at the 15 s boundary on own chest, pulse oximeter or smartwatch at the same time; use signals meeting the validity criteria. | T | Each result within Â±5 BPM or Â±10 % of the reference. |
| REQ-07 | Stopping before 15 s gives no result. | Stop after 10 s and again at 14.9 s; record timing uncertainty and ensure the upper bound remains below 15 s. | T | Nothing sent to the server; nothing in the serial log as a result. |
| REQ-08 | A poor signal gives an error instead of a number. | Chestpiece in open air or rubbed during the session. | T | Error on the server and on the device (LED and serial log); no BPM value. |
| REQ-09 | With the configured server available, a valid result reaches the FHIR server linked to this device; unavailable or failed delivery follows REQ-10. Patient linking is server-side, outside the system boundary; the device never sends a patient. | External test-setup precondition: configure HAPI server-side enrichment of Observation.subject from Device.patient (deployment-specific enrichment, not assumed default HAPI behavior). Run without a patient link, then link a synthetic patient to Device.patient, restart and repeat; inspect outgoing requests and the HAPI page. | T | Both Observations reference this device's Device, with a value meeting REQ-06 and the measurement-end timestamp, within 10 s of Stop; outgoing Observations omit subject in both runs; HAPI enriches only the second stored Observation with the linked patient. |
| REQ-10 | A failed delivery is retried up to 3 times within the overall deadline, then the device shows an error. Terminal failure discards the result; it is not retained for later delivery. | Stop the HAPI container before or during sending; repeat with the server restarted during the retries; then commit the first write, drop its receipt and let the device retry. After a terminal error, restore the server and inspect requests/HAPI until the next deliberately started measurement to check that the failed result is not resent. | T | At most 4 attempts within 10 s; error shown if all fail, with no later retry of that measurement after server recovery; in the committed-write/lost-receipt case exactly one Observation exists and every attempt uses the same conditional-create identity. |
| REQ-11 | Selected open networks need no password; protected networks require valid credentials. Secure server transport checks the server certificate. | Test an open network, wrong/correct protected-network password, then certificates with an untrusted issuer, wrong server name and expired validity in separate FHIR-phase runs. | T | Open/correct joins work; wrong credentials fail; invalid server certificate prevents sending. |
| REQ-12 | Without credentials or after a 2 s hold in Idle, the device provides an open hotspot portal to select Wi-Fi. Saved credentials survive restart. | Join hotspot without a password; use QR portal URL; select open/protected networks; verify address before saving, restart and rejoin; inject save failure. | T | Selected network joins; saved credentials persist; failed saving shows an error while retaining the connection and old valid settings. |
| REQ-13 | Faults follow the current feedback catalogue; Wi-Fi-only faults preserve working audio. Restart-required faults mute and block Start until restart. | Inject a Wi-Fi-only fault during listening, then Stop and press Start while offline; separately inject a microphone fault, press Start before restart, test short press, then restart after restoring the microphone. | T | Wi-Fi fault does not interrupt audio and offline Start works after Stop; microphone fault mutes, Start remains blocked before restart, short press does not restore it, restart/checks restore operation. |
| REQ-14 | Errors show the catalogue context colour and counted red code; short-press-clearable errors can be acknowledged without implicit Start/retry. | Inject Wi-Fi join, credential-save and delivery failures; compare code/context, acknowledge with a short press and separately request Start or setup (VT-09). | T | Correct code and serial cause; acknowledgement follows catalogue; no implicit Start or manual retry. |
| REQ-15 | The device keeps its server registration across restarts. | Record the server ID returned by first registration and its persisted value; restart three times, inspect reuse of that same ID and run a session after each restart (VT-15). | T | One Device for this device on the HAPI page; all Observations reference it. |

## Open acceptance inputs

Project decisions still needed: REQ-06 signal-validity criteria and the reference-selection rule must be frozen before selecting the ten sessions; VT-06 cannot pass with operator-selected exclusions. REQ-09 requires a clock reference, synchronization evidence and an allowed measurement-end timestamp skew; the 10 s delivery budget is not that skew. These remain unresolved FHIR/BPM design inputs (D06/D08), not invented acceptance limits.

## Retired requirements

SR-01â€¦SR-12 and the component requirements AUD, BPM, CTL, HW, INP, LIS, MON, NET, REC, STO and UI were retired on
14 October 2026 by project scope decision. Decision identification: Nico, *MVP scope decisions*, DigitalStethoscope project record, 14 October 2026, `Development/system/planning/mvp-decisions-2026-10-14.md` (Records stage). Their IDs are not reused. Internal constraints that remain relevant are inputs to the later design stage.
Optional requirements (replay, Lung, display, touch, SD, on-device test playback) are removed for now.
