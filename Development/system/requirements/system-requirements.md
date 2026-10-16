# System requirements (MVP)

Decided on 14 October 2026 ([decisions](../planning/mvp-decisions-2026-10-14.md)); REQ-09 and REQ-12 changed and REQ-15 added on 15 October ([decisions](../planning/mvp-decisions-2026-10-15.md)). Every requirement is checked by Nico on
the finished device with available equipment: headphones, phone, laptop, the HAPI web page, a pulse oximeter or
smartwatch and test-tone audio. How the device achieves it is design ([detailed design](../design/interfaces-and-behavior.md),
[design parameters](../design/parameters.md)). Flows are shown in the [use-case diagrams](use-cases.md).

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
| REQ-09 | A valid result reaches the FHIR server, linked to this device. | Run a session, then open the HAPI web page. | T | Observation referencing this device's Device, with correct value and time, within 10 s of Stop. |
| REQ-10 | A failed delivery is retried up to 3 times, then the device shows an error. | Stop the HAPI container before or during sending; repeat with the server restarted during the retries. | T | At most 4 attempts within 10 s; error shown if all fail; never a duplicate Observation. |
| REQ-11 | Wi-Fi needs a password and the server certificate is checked. | Use a wrong Wi-Fi password; point the device at a server with a different certificate. | T | No connection; nothing sent; error shown. |
| REQ-12 | Without stored Wi-Fi credentials, or after a long press (≥2 s) in Idle, the device opens a hotspot page to select the network and enter its password. | Erase the credentials and power on; connect a phone, enter the hotspot password, select the network and enter its password; restart the device. | T | The device joins the selected network, and joins it again after the restart without the page. |
| REQ-13 | A serious fault mutes the device until it is restarted. | Unplug the microphone while listening. | T | Muted plus alarm indication; only a restart clears it. |
| REQ-14 | A minor fault is shown and cleared with the button. | Stop the HAPI container, run a valid session and stop it so delivery fails; press the button, then press Start. | T | Error shown after the failed delivery; the button clears it; listening works after Start. |
| REQ-15 | The device keeps its server registration across restarts. | Run a session, restart the device three times, run a session after each restart. | T | One Device for this device on the HAPI page; all Observations reference it. |

## Retired requirements

SR-01…SR-12 and the component requirements AUD, BPM, CTL, HW, INP, LIS, MON, NET, REC, STO and UI were retired on
14 October 2026. Their IDs are not reused. Content that is still valid moved to [detailed design](../design/interfaces-and-behavior.md#design-constraints).
Optional requirements (replay, Lung, display, touch, SD, on-device test playback) are removed for now.

Updated by Claude-Opus-5.5 on behalf of Nico running in T3 Code through Claude Code.
