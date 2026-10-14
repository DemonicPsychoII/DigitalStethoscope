# MVP decisions — 14 October 2026 (TICKET-125)

Nico's review of the requirements and architecture in this T3 thread. These decisions supersede the
[11 October](mvp-decisions-2026-10-11.md) and [12 October](mvp-decisions-2026-10-12.md) records where they differ.

## Requirements

- **A requirement is valid only if Nico can test it on the device** with available equipment (headphones, phone,
  laptop, HAPI web page, pulse oximeter or smartwatch, test-tone audio) and gets a clear pass or fail.
  Statements only checkable by reading code are design decisions and live in [detailed design](../design/interfaces-and-behavior.md).
- [System requirements](../requirements/system-requirements.md) are replaced by REQ-01…REQ-14. SR-01…SR-12, all component
  requirements (AUD, BPM, CTL, HW, INP, LIS, MON, NET, REC, STO, UI) and the traceability CSV are retired.
- All optional requirements are removed for now: slowed replay, clip capture, Lung, display, touch, SD storage and
  on-device test playback. Optional ideas stay recorded in the [11 October decisions](mvp-decisions-2026-10-11.md).
- Numeric design values are internal [design parameters](../design/parameters.md), not requirements.
- Use cases are shown as [abstract flow diagrams](../requirements/use-cases.md) instead of lists.
- Test recordings are handled like real patient data. There is no separate "test data never sent" rule.
- The smoothed-volume requirement is removed.

## Behavior

- **Retry:** a failed delivery is retried up to 3 times (4 attempts), about 2 s apart, all within 10 s. Then the device
  shows an error. Conditional create (`If-None-Exist`) keeps retries from creating duplicates. This replaces the
  11 October "no retry" rule.
- **Invalid BPM:** the device sends an error to the server and shows the error on the device.
- **Error indication:** without a display, the device shows errors with LED patterns and the serial log.
- **Device Alarm** recovers only by restart. Normal faults are cleared with the button.
- **BPM reference:** pulse oximeter or smartwatch measured at the same time; pass within ±5 BPM or ±10 %.
  There is no fixed signal-quality threshold.
- **Security:** Wi-Fi with a password (WPA2) and HTTPS with the server certificate checked against the lab CA (self-signed).
  The server does not authenticate the device in the MVP.
- **Patient assignment lifetime** remains open.

## Scope

- Heart only. Lung is optional and needs the display.
- The device ends at the DAC line output. The amplifier is outside the digital-stethoscope scope.
- The corpus, reference recordings and resampling are decided during the Wi-Fi/FHIR phase.
- Filter bands are chosen after the device works. Filter work is research (which filters) plus code.
  The filter study also runs BPM detection on each listening filter to answer whether one filter can serve both.
- Latency: no two-channel recording setup is available. Latency is checked by ear (demonstration), not measured.
- The new firmware lives in [`coding/app/`](../coding/app/README.md) (closes D11).

## Schedule

- The newest Jira plan applies: TICKET-178…196 under TICKET-129, 271 h at 8 h per weekday, 16 October to 2 December.
- Patient assignment and Device registration were missing from that plan. They are added as one ticket of about 12 h.
  It uses Saturdays (Nico has some free in the next two weeks) and the slack before the carrier board arrives
  (around 25 October), which goes to Wi-Fi, FHIR and the hotspot page.
- Submission is **11 January 2027**. Writing and proofreading finish at least one week before (4 January),
  ideally two weeks before (28 December).
