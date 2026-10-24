# MVP decisions — LED indication, single error type and patient pass-through, 16 October 2026

> **Superseded in part:** the [current baseline](README.md#current-baseline) names the
> decision in force for each topic. Text below is historical where it conflicts.

Decisions given by Nico in T3 Code on 16 October. They supersede the Device Alarm / normal fault split of the
[11 October decisions](mvp-decisions-2026-10-11.md) and item 5 ("no patient data on the device") of the
[15 October decisions](mvp-decisions-2026-10-15.md). Everything else from 15 October stands.
This records decisions, not implemented firmware behavior.

## Confirmed decisions

1. **Two LEDs.** The on-board RGB LED (WS2812) shows the workflow status; the red LED in the pushbutton shows
   errors. Red is never used on the RGB LED, so red always means "error, press the button". The serial log
   records every cause. The colour table is in the
   [detailed design](../design/FEEDBACK/catalogue.md).
2. **One error type.** Any detected fault latches an Error: the red LED blinks and the serial log records the
   cause. If audio is affected (microphone, DAC, stalled worker, failed startup check, potentiometer ADC), the
   device also mutes and blocks Start. A short press in Idle acknowledges the Error and runs the check again;
   if the cause is still present, the Error returns at once. No fault needs a restart any more.
3. **Patient only from the server.** The device never selects a patient. If the server workflow has already
   linked a patient to the Device, the device puts that reference into `Observation.subject`. If not, the
   Observation is sent without patient data; linking it later is the server's job.

## Proposals

- **Board pins.** The RGB LED data pin is GPIO48 on DevKitC-1 v1.0 and GPIO38 on v1.1, and GPIO38 is the BPM
  contact of the filter switch. Move that contact to GPIO14 (the former display DC pin, not a strapping pin),
  so both revisions work and one overlay line selects the LED pin. The fitted board revision is to be confirmed.
- **Reading the patient.** Read `Device.patient` with `GET /Device/{id}` after joining Wi-Fi at boot. This is the
  same request as the device-id check proposed on 15 October.

## Requirement changes

- REQ-09: the result also carries the patient when the server has linked one.
- REQ-13: a fault that affects audio mutes the device; a short press clears it only when the cause is gone
  (was: only a restart clears it).
- VT-01, VT-07 and VT-09 follow; see verification.

## Superseded

- 11 October: Device Alarm as a separate state that only a full restart clears, and restart-only recovery
  (parameter P12).
- 15 October item 5 and the related "no `subject`" rule: the device still never loads a patient list or
  selects a patient, but it passes on a patient that the server has linked.

## Open points

- Whether the device also reads `Device.patient` again before each send, so a link made after boot is used
  without a restart.
- Which fault classes count as "audio affected" in the startup check list.
