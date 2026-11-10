# Status light pin and placeholder volume — 10 November 2026

Nico decided on 10 November 2026 in T3 Code (conversation link not recorded) how the first fitted
evaluation carrier is used. These are project decisions, not measurements.

Board state reported by Nico: the evaluation PCB from the `DigitalStethoscope_Eval` Altium project
(commit `a8f23a2`, production package of 13 October 2026) is assembled with J3 (INMP441 microphone),
J4 (PCM5102A DAC socket), J6 (illuminated button) and J8 (Raw/Murmur/BPM switch). J7 (volume
potentiometer) is not fitted, and the SD card is not used. The DevKitC-1 revision was not known
when the decision was made.

Bench observation on 10 November 2026 (Nico, local build of the TICKET-187 changes on commit
`5705ac4`, which is `integration` `50de562` plus a CI-only change): the status light lit on GPIO48, so the fitted DevKit is v1.0.
The DevKit was not yet soldered to the carrier, so carrier inputs such as J8 were not connected.

## Decision

1. **Status light on GPIO48.** The RGB status light is driven on GPIO48, its position on DevKitC-1
   v1.0, whichever revision is fitted. The carrier's SD card chip select on GPIO48 is not used.
   GPIO38 is not driven, so it stays the BPM contact of the filter switch. If the light stays dark,
   the DevKit is v1.1 and the pin is revisited. This replaces the earlier precondition to confirm
   the DevKit revision before enabling the RGB LED driver.
2. **Fixed volume until J7 is fitted.** Until the potentiometer is fitted, the audio path uses a
   fixed volume of 100 % as a placeholder that the potentiometer replaces. REQ-04 and the volume
   part of TICKET-187 stay unverified until then.

## Applied in

- [Feedback catalogue](../design/FEEDBACK/catalogue.md) and the
  [electrical interface baseline](../spec/product-scope.md#electrical-interface-baseline)
- [Architecture view notes](../architecture/system/VIEW-NOTES.md) and the application board overlay
  in [`coding/app/boards/`](../coding/app/README.md)
