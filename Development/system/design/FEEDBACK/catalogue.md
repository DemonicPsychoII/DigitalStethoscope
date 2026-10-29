# LED indication and error catalogue

The [architectural ground rules](../../architecture/system/feedback-principles.md) assign responsibility and fault containment. The following table and indication values are detailed design.



The RGB status light never shows red; the separate red button light shows error codes.
Serial logs retain the detailed cause. Timing is in [P22](parameters.md).
The pin map stays unchanged; there is no GPIO14 filter-switch move. The claimed GPIO38/BPM-contact conflict is an unsupported project wiring note: no dated carrier schematic or fitted-board evidence is available here. Confirm the board revision and carrier wiring before enabling the RGB LED driver; if either is unknown, leave that driver disabled pending owner-authorized inspection (TICKET-186, TICKET-187). This is a design precondition, not evidence that an implemented driver enforces it.

Vendor reference: Espressif Systems, *ESP32-S3-DevKitC-1 v1.1 User Guide*, ESP-Dev-Kits documentation, online revision not specified, <https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.1.html> (accessed 2026-10-24). It identifies the board RGB LED connection; it does not establish the project's carrier wiring.

## Status and error catalogue

This table is authoritative for feedback. It defines feedback behavior, not standards
conformity or implemented firmware. Recovery and acknowledgement are separate.

- **One feedback catalogue.** Wi-Fi-only failures, clock-only `TIME_SYNCHRONIZATION_FAILURE`, server-preparation `SERVER_CONNECTION_FAILURE` and registration-only `DEVICE_REGISTRATION_FAILURE` preserve working audio and permit
  offline Start. Recovery follows the [Wi-Fi rules](../COMMUNICATION/interfaces-and-behavior.md#wi-fi-setup-and-recovery) and need not wait for error
  acknowledgement. Other errors stop the active workflow, mute/cancel active audio
  and block Start until the catalogue clear rule is met. Restart means reset/power cycle.
  Generic device settings failures are distinct from Wi-Fi credential-save failures.
- **RGB LED = context.** The colour shows the context in which a status or error occurs, not the module that
  detects it. CONTROL decides what can run, so each context has one colour: white = device (startup,
  settings, session input), green = Idle, cyan = audio, violet = Wi-Fi, blue = FHIR.
- **Standards working assumptions.** Applicability and primary clauses remain unverified (TICKET-210). Project colour mappings are choices informed by secondary summaries of IEC 60601-1 7.8.1 (green only for Idle, no red, yellow or orange on
  the RGB LED). Flash rates follow IEC 60073: codes and quick flashes 2 Hz, slow blink 0.5 Hz. P22 defines
  pauses, breathing, dimming and visibility. Priorities follow the IEC 60601-1-8 approach. The research,
  sources and remaining gaps are in [LED indication standards](led-indication-standards.md). This design
  records the adopted design and its deviations; it is not a conformity claim.
- **Priority** (column): Medium for audio-path faults that can make the user misjudge heart sounds at
  once; Low for all other errors; Information for statuses. No error is High.
- **Red button LED = error code.** The red LED shows the error code as a number of blinks. The code is
  unique only together with the RGB colour, so the RGB LED stays on in the context colour during an error.
  Muting is an audio action and does not switch the RGB LED off.
- **Blink notation.** "N blinks, pause" repeats until the error is cleared. A pattern runs a limited number
  of times only when the table says so ("once").
- **Sort order.** Sort rows by RGB colour, then by number of blinks ("off" first). "No change" rows are overlays on the current colour and come last.
- **RGB behaviour** is the light pattern of the colour: steady, blink, breathing or flashes. Timing is in
  [design parameters](parameters.md) P22.
- **Statuses** end when the next status replaces them; the change of state is the visible clear.
- **More than one error.** The LEDs show only the error with the highest priority. If priorities are equal,
  they show the error that latched first. The serial log lists all errors.
- **Where the error occurred.** An error does not change the RGB context: it keeps the colour of the context in
  which the error occurred, so the user sees where it happened. The red LED shows the code.
- **Clear and retry are separate.** A short press only clears errors whose catalogue row permits acknowledgement. It does not repeat the failed
  workflow. A separate 2 s hold in Idle starts Wi-Fi setup again, even with a Wi-Fi error latched.
  Automatic reconnect/portal recovery remains automatic; acknowledgement is not its gate.
- **Time readiness.** [SNTP design](../COMMUNICATION/time-synchronization.md#failure-indication-and-acknowledgement) raises `TIME_SYNCHRONIZATION_FAILURE` on initial failed preparation or anchor expiry, not on a failed refresh while the old anchor is usable. Acknowledgement neither marks time valid nor triggers an attempt. Automatic clock recovery remains independent of acknowledgement; repeated failures in the same unavailable episode do not re-latch an acknowledged indication.
- **Server preparation.** [TLS failure handling](../COMMUNICATION/secure-transport.md#failure-indication) latches `SERVER_CONNECTION_FAILURE` after failed preparation. Acknowledgement clears only its indication; automatic recovery continues independently. Repeated failed retries in one unavailable episode do not re-latch after acknowledgement. Start cancellation alone raises no error. Delivery failures retain their separate catalogue behavior.
- **Device registration.** [Registration recovery](../COMMUNICATION/server-communication.md#registration-flow-and-recovery) covers request, response and registration-record failures. Standalone listening remains available. Acknowledgement clears only the indication; recovery is automatic, and repeated failures in the same unavailable episode do not re-latch an acknowledged indication. Start cancellation alone raises no registration error. Resource-release faults retain the existing cleanup/restart policy.
- **Restart** means the reset button or a power off/on cycle.
- **Code naming.** `<SUBJECT>_<OUTCOME>` in upper case with underscores and no abbreviations, for example
  `SCAN_FAILURE`. Outcome words: no suffix, `RUNNING`, `OPEN`, `PENDING`, `SENDING` or `CONNECTING` for a normal status;
  `SUCCESSFUL`, `RECEIVED`, `VALID`, `CONNECTED`, `ACKNOWLEDGED` or `MINIMUM_REACHED` for a positive result; `REJECTED`, `FAILURE`, `STALL`, `INVALID`, `UNEXPECTED`, `CHANGE` or `NOT_POSSIBLE` for a negative result.
  The C enumerator adds the prefix `FEEDBACK_` (for example `FEEDBACK_SCAN_FAILURE`) to keep the global
  namespace clean. The catalogue is one enum. After the first implementation, new codes are only appended,
  so existing values never change.
- **Logging is separate.** The component that detects the fault logs the details (sub-cause, HTTP status,
  failed check). The LED interface only receives the code. The `HealthEvent` error class uses the same
  enumerator.

| Kind   | Status / error                                               | Detected by       | Code                         | Priority    | RGB LED   | RGB behaviour                        | Red button LED         | Cleared by  |
|--------|--------------------------------------------------------------|-------------------|------------------------------|-------------|-----------|--------------------------------------|------------------------|-------------|
| Status | Sending                                                      | CONTROL           | DELIVERY_SENDING             | Information | blue      | breathing, slow                      | off                    |             |
| Status | Delivery pending                                             | CONTROL           | DELIVERY_PENDING             | Information | blue      | blink, slow                          | off                    |             |
| Status | Delivery received (201/200)                                  | COMMUNICATION     | DELIVERY_RECEIVED            | Information | blue      | 3 quick flashes                      | off                    |             |
| Error  | Time sync failed                                             | COMMUNICATION     | TIME_SYNCHRONIZATION_FAILURE | Low         | blue      | steady                               | 1 blink, pause         | Short press |
| Error  | Device registration failed                                   | COMMUNICATION     | DEVICE_REGISTRATION_FAILURE  | Low         | blue      | steady                               | 2 blinks, pause        | Short press |
| Error  | Terminal delivery failure, including first-attempt conditional-create rejection, or exhausted bounded retries                                  | COMMUNICATION     | DELIVERY_FAILURE             | Low         | blue      | steady                               | 3 blinks, pause        | Short press |
| Error  | Result cannot be sent (offline or no clock)                  | CONTROL           | DELIVERY_NOT_POSSIBLE        | Low         | blue      | steady                               | 4 blinks, pause        | Short press |
| Error  | Secure server preparation failed                            | COMMUNICATION     | SERVER_CONNECTION_FAILURE   | Low         | blue      | steady                               | 5 blinks, pause        | Short press |
| Status | Listening                                                    | CONTROL           | LISTENING                    | Information | cyan      | steady                               | off                    |             |
| Status | Measuring, < 15 s                                            | CONTROL           | MEASUREMENT_RUNNING          | Information | cyan      | blink, slow                          | off                    |             |
| Status | Measuring, ≥ 15 s                                            | CONTROL           | MEASUREMENT_MINIMUM_REACHED  | Information | cyan      | steady                               | off                    |             |
| Status | Analysing                                                    | CONTROL           | ANALYSIS_RUNNING             | Information | cyan      | breathing, slow                      | off                    |             |
| Error  | Audio worker stall                                           | MONITOR           | AUDIO_WORKER_STALL           | Medium      | cyan      | steady                               | 1 blink, pause         | Restart     |
| Error  | BPM worker stall                                             | MONITOR           | HEART_RATE_WORKER_STALL      | Low         | cyan      | steady                               | 2 blinks, pause        | Restart     |
| Error  | BPM result invalid                                           | AUDIO             | MEASUREMENT_INVALID          | Low         | cyan      | steady                               | 3 blinks, pause        | Short press |
| Error  | Microphone: no data or I2S RX error                          | AUDIO             | MICROPHONE_FAILURE           | Medium      | cyan      | steady                               | 4 blinks, pause        | Restart     |
| Error  | DAC: I2S TX error                                            | AUDIO             | AUDIO_OUTPUT_FAILURE         | Medium      | cyan      | steady                               | 5 blinks, pause        | Restart     |
| Error  | Control input failure (potentiometer ADC or switch position) | PHYSICALINTERFACE | CONTROL_INPUT_FAILURE        | Medium      | cyan      | steady                               | 6 blinks, pause        | Restart     |
| Status | Idle                                                         | CONTROL           | IDLE                         | Information | green     | steady, dim                          | off                    |             |
| Status | Portal / hotspot open                                        | CONTROL           | PORTAL_OPEN                  | Information | violet    | steady                               | off                    |             |
| Status | Wi-Fi scanning, connecting or reconnecting                   | COMMUNICATION     | WIFI_CONNECTING              | Information | violet    | breathing, slow                      | off                    |             |
| Status | Wi-Fi connected                                              | COMMUNICATION     | WIFI_CONNECTED               | Information | violet    | 3 quick flashes                      | off                    |             |
| Error  | Wi-Fi credentials save failed after 2 attempts               | COMMUNICATION     | WIFI_SETTINGS_SAVE_FAILURE   | Low         | violet    | steady                               | 1 blink, pause         | Short press |
| Error  | Wi-Fi scan: 4 attempts used                                  | COMMUNICATION     | SCAN_FAILURE                 | Low         | violet    | steady                               | 2 blinks, pause        | Short press |
| Error  | Wi-Fi boot join: 4 attempts used                             | COMMUNICATION     | JOIN_FAILURE                 | Low         | violet    | steady                               | 3 blinks, pause        | Short press |
| Error  | Wi-Fi link loss: 4 attempts used                             | COMMUNICATION     | RECONNECT_FAILURE            | Low         | violet    | steady                               | 4 blinks, pause        | Short press |
| Error  | Hotspot (AP) start failed                                    | COMMUNICATION     | HOTSPOT_START_FAILURE        | Low         | violet    | steady                               | 5 blinks, pause        | Short press |
| Error  | Wi-Fi cleanup stop failed                                    | COMMUNICATION     | WIFI_CLEANUP_FAILURE         | Low         | violet    | steady                               | 6 blinks, pause        | Restart     |
| Status | Boot / startup checks                                        | CONTROL           | STARTUP_RUNNING              | Information | white     | steady                               | on, steady (lamp test) |             |
| Error  | Settings read failed (flash)                                 | CONTROL           | SETTINGS_READ_FAILURE        | Low         | white     | steady                               | 1 blink, pause         | Restart     |
| Error  | Startup check failed                                         | CONTROL           | STARTUP_FAILURE              | Low         | white     | steady                               | 2 blinks, pause        | Restart     |
| Error  | Unexpected reset (watchdog, crash, brown-out)                | CONTROL           | RESET_UNEXPECTED             | Low         | white     | steady                               | 3 blinks, pause        | Short press |
| Error  | Settings save failed (flash)                                 | CONTROL           | SETTINGS_SAVE_FAILURE        | Low         | white     | steady                               | 4 blinks, pause        | Restart     |
| Error  | Context change during a session                              | CONTROL           | SESSION_CONTEXT_CHANGE       | Low         | white     | steady                               | 5 blinks, pause        | Restart     |
| Status | Input rejected                                               | CONTROL           | INPUT_REJECTED               | Information | no change | short dimming by at least 50 %, once | off                    |             |
| Status | Error acknowledged                                           | CONTROL           | ERROR_ACKNOWLEDGED           | Information | no change | no change                            | 1 long flash, once     |             |
