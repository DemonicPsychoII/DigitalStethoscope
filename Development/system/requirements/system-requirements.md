# System requirements (MVP)

The [current baseline](../planning/README.md#current-baseline) names the decisions behind this table;
the [decision log](../planning/README.md#decision-log) records each change. Every requirement is checked by Nico on
the finished device with available equipment: headphones, phone, laptop, the HAPI web page, a pulse oximeter or
smartwatch and test-tone audio. How the device achieves it is design ([detailed design](../design/interfaces-and-behavior.md),
[design parameters](../design/parameters.md)). Flows are shown in the [use-case diagrams](use-cases.md).

Registration and certificate tests remain later FHIR acceptance, not Wi-Fi setup prerequisites.

Methods: **T** test (measured), **D** demonstration (shown working).

| ID | Requirement | How it is tested | Method | Pass |
|---|---|---|---|---|
| REQ-01 | After power-on the device stays silent until Start is pressed. | Power on with volume at maximum and headphones on. | D | Silence until Start. |
| REQ-02 | After Start the operator hears heart sounds. | Chestpiece on own chest, Raw filter, press Start. | D | Heartbeat audible within 2 s of Start. |
| REQ-03 | The 3-position switch selects the Raw, Murmur or BPM listening filter. | Play 100 Hz, 400 Hz and 2 kHz tones from a laptop through an earbud held on the chestpiece diaphragm, at one fixed laptop volume and device volume for all positions. First confirm each tone is clearly audible in Raw; Raw is the reference. Tones follow the bands chosen in the filter study; these fit the current candidates (Murmur 40–800 Hz, BPM 25–150 Hz). | D | Compared with Raw: Murmur keeps 100 Hz and 400 Hz, 2 kHz clearly quieter. BPM keeps 100 Hz, 400 Hz and 2 kHz clearly quieter. |
| REQ-04 | The potentiometer sets the volume from silent to maximum. | Turn through the full range while listening. | D | Silent at minimum, no crackling. |
| REQ-05 | Listening has no noticeable delay. | Tap the chestpiece and listen. | D | Tap heard together with the touch; no echo or lag noticeable. |
| REQ-06 | A heart session of at least 15 s gives a heart rate. | 10 sessions of 30 s on own chest, pulse oximeter or smartwatch at the same time. | T | Each result within ±5 BPM or ±10 % of the reference. |
| REQ-07 | Stopping before 15 s gives no result. | Stop after 10 s. | T | Nothing sent to the server; nothing in the serial log as a result. |
| REQ-08 | A poor signal gives an error instead of a number. | Chestpiece in open air or rubbed during the session. | T | Error on the server and on the device (LED and serial log); no BPM value. |
| REQ-09 | A valid result reaches the FHIR server, linked to this device, and to its patient if the server has linked one. | Run a session without a server-side patient link, then link a synthetic patient to the Device on the server, restart and run a second session; open the HAPI web page. | T | Both Observations reference this device's Device, with correct value and time, within 10 s of Stop; only the second one references the linked patient. |
| REQ-10 | A failed delivery is retried up to 3 times, then the device shows an error. | Stop the HAPI container before or during sending; repeat with the server restarted during the retries. | T | At most 4 attempts within 10 s; error shown if all fail; never a duplicate Observation. |
| REQ-11 | Selected open networks need no password; protected networks require valid credentials. Secure server transport checks the server certificate. | Test an open network, wrong/correct protected-network password, then a different server certificate in the FHIR phase. | T | Open/correct joins work; wrong credentials fail; invalid server certificate prevents sending. |
| REQ-12 | Without credentials or after a 2 s hold in Idle, the device provides an open hotspot portal to select Wi-Fi. Saved credentials survive restart. | Join hotspot without a password; use QR portal URL; select open/protected networks; verify address before saving, restart and rejoin; inject save failure. | T | Selected network joins; saved credentials persist; failed saving shows an error while retaining the connection and old valid settings. |
| REQ-13 | Faults follow the current feedback catalogue; Wi-Fi-only faults preserve working audio. Restart-required faults mute and block Start until restart. | Inject a Wi-Fi-only fault during listening, then a microphone fault; test short press and restart after restoring the microphone. | T | Wi-Fi fault does not interrupt audio; microphone fault mutes, short press does not restore it, restart/checks restore operation. |
| REQ-14 | Errors show the catalogue context colour and counted red code; short-press-clearable errors can be acknowledged without implicit Start/retry. | Inject Wi-Fi join, credential-save and delivery failures; compare code/context, acknowledge and separately request Start or setup. | T | Correct code and serial cause; acknowledgement follows catalogue; no implicit Start or manual retry. |
| REQ-15 | The device keeps its server registration across restarts. | Run a session, restart the device three times, run a session after each restart. | T | One Device for this device on the HAPI page; all Observations reference it. |

## Retired requirements

SR-01…SR-12 and the component requirements AUD, BPM, CTL, HW, INP, LIS, MON, NET, REC, STO and UI were retired on
14 October 2026. Their IDs are not reused. Content that is still valid moved to [detailed design](../design/interfaces-and-behavior.md#design-constraints).
Optional requirements (replay, Lung, display, touch, SD, on-device test playback) are removed for now.

Updated by Claude-Opus-5.5 on behalf of Nico running in T3 Code through Claude Code.
