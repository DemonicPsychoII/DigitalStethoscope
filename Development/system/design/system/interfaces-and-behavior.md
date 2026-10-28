# Interface contracts and detailed design

These contracts define module ownership, data hand-offs and failure behavior. Proposed numeric values and open representation or sizing choices remain identified as such. Host execution uses injected data at the same service boundaries as target adapters.

## Static dependency and module map

This design assigns each module to a layer and defines its inputs, outputs and
ownership below. Zephyr supplies the drivers; there is no second project driver stack.
Implementations must follow these contracts and name the design they implement.

- **L0 is Zephyr:** drivers, DMA, interrupts and the devicetree overlay. No project code.
- **L1 adapters** call Zephyr driver APIs directly: `L1_I2S` (microphone RX and DAC TX),
  `L1_WIFI` (station, scan, hotspot and DHCP), `L1_PORTAL` (HTTP server of the Wi-Fi setup page; [contract](../PORTAL/interfaces-and-behavior.md)),
  `L1_STORAGE` (named records in flash through Zephyr settings),
  `L1_PHYSICALINTERFACE` (buttons, switches, potentiometer, LEDs).
- **L1 libraries** are pure C with no RTOS, filesystem, UI or network includes: `L1_FILTER`,
  `L1_BPM`, `L1_FHIR`. They hold no shared state; each caller owns its instances.
- **L2 orchestrates:** `L2_CONTROL`, `L2_AUDIO`, `L2_COMMUNICATION`, `L2_SHELL`. Only CONTROL
  writes mode state. The other L2 modules receive commands or snapshots from CONTROL and report
  back through events; SHELL reaches services only through CONTROL. The setup page is the
  exception: COMMUNICATION owns the setup workflow and reads the page requests itself, while
  CONTROL sends it the 2 s hold and listening start/stop.

Calls go downward; worker completion and health notifications are events to the controller, not
direct writes into application state. MON observes bounded counters/events; it must not become an
unrestricted caller of every API.

The components below are logical responsibilities, not folders; the module column shows where each one is realized.
REC, STO and the display are optional and not part of the MVP (TICKET-202, TICKET-206).

| Component | Module | Owns / writes | Inputs | Outputs / proposed operations |
|---|---|---|---|---|
| INP | `L1_PHYSICALINTERFACE`; events to `L2_CONTROL` | debounce/contact/calibration state | ISR notice, GPIO/ADC/touch samples | `publish_control(event)`; stable-state reconciliation |
| CTL | `L2_CONTROL` | settings, workflow state, generation, point | control/completion/health events | `dispatch(event)`, `snapshot()`, session-tagged commands, network lease |
| AUD | `L2_AUDIO` over `L1_I2S` | DMA pool, source generation, transport progress | mic/fixture blocks, source/stop commands | normalized `AudioBlock`, capture/analysis fan-out, TX submission |
| LIS | `L2_AUDIO` with `L1_FILTER` | listening coefficients and filter/ramp history | block, command snapshot | saturating mono output, levels/clipping |
| BPM | `L2_AUDIO` worker with `L1_FILTER`, `L1_BPM` | analysis window, estimates, coverage, aggregation | original-rate blocks, session configuration | validity updates and immutable `MeasurementResult` |
| UI | shell in `L2_SHELL`; LEDs via `L1_PHYSICALINTERFACE` | redraw progress/display model/shell state | `StateSnapshot` | bounded SPI redraw, LED state, control requests |
| NET | `L2_COMMUNICATION` with `L1_FHIR`, `L1_WIFI` | frozen job, connection, outcome | result/config + Idle lease | serialized Observation, outcome, lease-release acknowledgement |
| MON | `MONITOR` | anomaly counters, health evidence | worker checkpoints/counters | fault events, evidence snapshots |

Touch acquisition, calibration and physical input normalization belong to INP. UI renders the
snapshot; there is no Display-thread-to-Input-thread dependency. Shell commands and decoded
operator actions reach the controller through the same typed control-event contract. Exact
worker placement and ISR wake-up primitives remain proposed implementation choices.

## Data contracts

| Contract | Required fields and invariants |
|---|---|
| `AudioBlock` | pool handle, source ID/generation, sequence, first sample index, sample rate, frame count (≤128), representation/valid bits, discontinuity flag, readonly mono sample payload. Microphone is signed 24-bit normalized into int32; alignment convention remains to be fixed. Timestamp derives from sample count, not worker arrival. |
| `ControlEvent` | event ID/type, origin (physical/touch/shell/worker), monotonic timestamp, typed value, generation where relevant. Controller serializes accepted order; equal timestamps use queue arrival order. Invalid fields are rejected before mutation. |
| `AudioCommand` | unique command ID, controller generation, desired settings, action/session ID. Audio acknowledges applied block boundary or explicit rejection; stale generations are discarded. |
| `StateSnapshot` | snapshot revision, effective and requested settings, source/provenance, playback/measurement/delivery states, active IDs, capabilities, BPM validity/time, clip progress, pending replay speed, error/outcome counters. Read as a coherent copy; UI never edits it. |
| `Clip` | ID/generation, source, raw format/rate, allocated capacity and valid length, capture sample interval, evaluation metadata. Ownership REC; immutable after finalization until discarded. Never patient-persisted. |
| `MeasurementResult` | result/session ID, source/generation, valid flag/reason, BPM value and declared precision, quality definition/value, coverage, first/last sample index, measurement monotonic interval and UTC mapping, frozen Device id/point/config/filter IDs, completion status. Invalid results carry no sendable numeric value. |
| `NetworkJob` | stable Observation identifier (Device id plus measurement end time), immutable result/payload, frozen endpoint/profile/auth-config reference, attempt count (up to 4: 1 attempt + 3 retries, all within 10 s), lease ID. Secrets stay outside evidence. Result device/time/value never resnapshotted from live state. |
| `HealthEvent` | component, error class, time/generation, severity, evidence level and counter reference. Hardware physical proof references explicit test evidence. |

## Ownership, memory and queues

DMA allocations stay in internal DMA-capable SRAM. AUD owns RX/TX transport; pool handles never
escape without defined lifetime. Preferred draft fan-out: copy normalized analysis blocks into a
fixed analysis pool (4 blocks candidate) so a stalled BPM worker cannot pin RX buffers. REC copies
raw samples into its bounded PSRAM clip; LIS consumes the current transport block synchronously.
A ref-counted shared pool is an alternative only if its no-starvation behavior is proven.

DSP state is worker-local. Settings/snapshots are bounded copies made under a short lock or message
hand-off; no lock spans I2S wait, SPI, file access, TLS or rendering. `k_msgq` carries bounded values
or handles, not audio payloads of unbounded length. Use nonblocking enqueue on the audio path.
Analysis overflow marks a gap and resets its window; display coalesces to latest snapshot; input
queue overflow reconciles stable values but rejects/report transient actions. A full network slot
returns Busy without overwriting a job; a terminal failure retains only redacted outcome metadata, with no retry queue. The completed measurement is lost after that visible failure; server recovery does not resend it. This is the bounded failure outcome of REQ-10, separate from REQ-09's available-server success path.

Candidate memory accounting:

- 128 stereo 32-bit frames = 1,024 bytes per transport block; 4 RX + 4 TX = 8,192 bytes
  before DMA descriptors, alignment and driver overhead.
- A mono int32 analysis block is 512 bytes; four payloads = 2,048 bytes plus handles/metadata.
- 5 s raw int32 mono at 16 kHz = 320,000 bytes; 30 s = 1,920,000 bytes. Allocate separate
  fixture/clip regions only when their simultaneous use and budgets are justified.
- Full 240×320 RGB565 frame = 153,600 bytes. At 10 MHz raw transfer lower bound is 122.88 ms;
  avoid full-frame transfers in any latency-critical path. SPI arbitration includes touch and SD.
- Reserve measured stacks, heap/TLS, coefficients, analysis windows and driver overhead before
  treating 8 MB PSRAM as available. No clinical safety assertion follows from spare memory.

## State entry/process/exit

| Region / state | Entry | Process | Exit / cancellation |
|---|---|---|---|
| Playback Boot | zero gain, capability checks, silent TX prime | bounded adapter initialization | Idle on essential readiness; Fault otherwise |
| Idle | mute; no active transport/listening operation | allow configuration and network lease | Start is Busy during analysis and sending; otherwise start only after lease released |
| Live | reset source-dependent state on source generation change | 128-frame normalized fan-out; selected listening filter; gain/saturation; TX | stop/fault mute; capture keeps live path |
| Capture | allocate/claim bounded clip and ID; LED active | copy raw prefilter/pregain; normal live listening continues | full → Replay; cancel → Live; stop/fault → Idle/Fault, incomplete clip invalid |
| Replay | freeze valid clip; initialize speed stage; LED active | raw clip → filter → WSOLA → gain/saturation; fresh mic still feeds analysis | end/cancel → Live; release clip cursor; stop/fault mutes |
| Measurement Acquiring | freeze context/config/ID and clear aggregation | original-rate windows; independent filter; valid estimates | Stop <15 s cancels; Stop ≥15 s → Finalizing; identity change rejected; an Error with audio muted invalidates the session |
| Finalizing | stop accepting windows for that interval | aggregate and union valid temporal coverage | freeze valid/invalid result once; late blocks cannot mutate result |
| Delivery decision (end of Analysing) | after the valid/invalid latch, check Wi-Fi configuration and, only when Wi-Fi is configured, the delivery prerequisites (Device id, clock, trust and endpoint) once after finalization; no waiting | Wi-Fi unconfigured: no send or Wi-Fi error; result not retained. Delivery prerequisites fail: latch DELIVERY_NOT_POSSIBLE and release Busy at once. Delivery prerequisites pass: grant the one job to Sending for a valid BPM, or to ReportingError for an invalid BPM (validated error report, no numeric value) |
| Sending | acquire exclusive Idle lease; snapshot payload | bounded connect/TLS/conditional POST, receipt | outcome event + release lease; Start is Busy, never queued; terminal failure latches DELIVERY_FAILURE and releases Busy |
| Error, audio affected | mute and invalidate active acquisition; block Start | expose latched cause on the red LED and serial log | use the catalogue clear rule; restart-required faults remain halted until restart |

Changing Heart/Lung, source or point during a session leaves the frozen context unchanged and raises SESSION_CONTEXT_CHANGE with the catalogue halt/restart rule. Outside a session the controller may accept configuration changes and reset source-dependent histories. Generation checks reject stale completions. Separate acknowledgement clears the indication of an Error that the catalogue allows to clear, without starting, retrying or changing an active workflow. A halted Error follows the catalogue clear rule; a short press cannot clear a restart-required fault.

A completed result does not wait for delivery prerequisites. When Wi-Fi is configured and they fail after finalization, CONTROL releases Busy at once and latches DELIVERY_NOT_POSSIBLE; the result is not retained. When Wi-Fi is configured and they hold, the single job is granted to Sending, CONTROL rejects Start before acquisition with Busy, and it does not queue Start or a second result. Admission resumes only after delivery succeeds or terminates with DELIVERY_FAILURE and the network lease is released; the normal error-clear rules still apply to these latches. This preserves the one-slot/no-retry-queue contract and the bounded delivery outcomes of REQ-09/REQ-10: success confirms the result, failure visibly loses it. A later measurement needs a fresh Start; the lost result cannot be reconstructed or retried.

## DSP and measurement design

Draft listening candidates: second-order Butterworth high/low sections (Murmur 40–800 Hz;
BPM emphasis 25–150 Hz), with Raw unity and a 20 ms exponential crossfade. Preserve state for
continuously evaluated paths; clear histories on source reset. These are engineering candidates,
not established optimum bands. Measure response and transients before approving coefficients.
Normalize signed microphone values once; saturate only at output conversion, with clipping
counters. Raw replay precision policy must be settled before reusing the bring-up int16 clip API.

Draft BPM: independent band filter → rectified envelope/downsampled representation → whole-cycle
autocorrelation or an equivalent method → range/harmonic/quality checks → periodic update. An 8 s
window at 100 Hz envelope rate is 800 samples; a 3 s window at 30 BPM contains only 1.5 cycles
and needs justification. Candidate update 1 s and session 30 s are open. Define a quality score
mathematically and validate it; it is not probability of clinical correctness. Aggregate using a
proposed median of accepted BPM estimates; coverage is the union of accepted window intervals
clipped to session bounds, not number_of_windows × window_length. Warm-up treatment, temporal
weighting, minimum windows and thresholds remain open (TICKET-192). No window includes missing blocks.

Replay candidate is WSOLA with bounded overlap/search buffers. Output length should equal
`ceil(valid_clip_frames / speed)` under a rounding policy that remains to be fixed, with final partial blocks
padded only for transport. Measure pitch and artifacts on heart sounds, not just sine waves.
Speed changes during replay require a continuity rule; draft restarts the speed
stage at the current source cursor without pretending the duration was constant-speed.

## Delivery, clock and configuration

A completed measurement has separate identity from a replay clip. The project identifier
system is `urn:stethoscope:measurement`. Its value is `<device-id>:<measurement-end-UTC>`:
the persisted server Device id, a colon, and the immutable interval end formatted as
`YYYY-MM-DDTHH:mm:ss.SSSZ`. Freeze both before the first attempt; do not regenerate
the end time or identity on retry. One device must not finalize two measurements with
the same end timestamp. Send `POST /Observation`, `Content-Type: application/fhir+json`,
with `identifier: [{"system":"urn:stethoscope:measurement","value":"<value>"}]` in the body
and, for the example value below, `If-None-Exist: identifier=urn%3Astethoscope%3Ameasurement|device-42%3A2026-10-23T12%3A00%3A00.000Z`.
Percent-encode each search value using UTF-8 URI query encoding before constructing
the header; the separator `|` separates system and value. For example the logical value
`device-42:2026-10-23T12:00:00.000Z` is encoded as
`device-42%3A2026-10-23T12%3A00%3A00.000Z` (the system is
`urn%3Astethoscope%3Ameasurement`). Never update an Observation.
The server assigns the resource ID. `201` (created) or `200` (one existing match)
confirms success. Uncertain transport responses, including a lost receipt after a
committed write, must retry with the identical body and conditional-create identity
under P13 while an attempt and time budget remain. P13 classifies retryable and
terminal outcomes. A visible delivery failure releases the job only on a terminal
outcome or exhausted attempt/deadline budget; there is no unconditional-create fallback.
FHIR conditional-create semantics: Health Level Seven International, FHIR R4
v4.0.1, HTTP, Conditional create, 2019,
<https://hl7.org/fhir/R4/http.html#ccreate> (accessed 2026-10-23).

The device never selects or adds a patient ID. It serializes Observation.subject only from the patient reference supplied with a server-requested examination, and otherwise omits subject. The server-request mechanism remains an open integration design input; a Device.patient lookup is not an approved substitute. One delivery job is granted after finalization when Wi-Fi is configured and delivery prerequisites hold; with configured Wi-Fi but failed prerequisites, latch DELIVERY_NOT_POSSIBLE at once. P13 bounds its attempts.

Map sample/monotonic measurement interval to UTC from an approved clock anchor. Use measurement
time, not send time; clock loss/skew makes the result ineligible until its mapping is resolved,
not rewritten. FHIR `effectiveDateTime` carries the end of the aggregate interval. This is a project representation choice. The interval stays in the local result. Preserve the Device id, point (approved coding or
evaluation-only metadata), value, interval and analysis settings in the immutable local result.
The local profile/metadata mapping, validation of `effectiveDateTime` against `effectivePeriod`, and decimal precision remain open (TICKET-181).

NET verifies CA/name/time and checks bounded status/body parsing. `201 Created` or `200` (existing conditional create) is the receipt and marks the result Sent; there is no readback.
An uncertain response is retried within the same bounded job; a single matching identifier returns the existing resource; multiple matches fail with 412. Configuration/auth errors and server failures remain visible after the last attempt.
SNTP is a clock synchronization mechanism, not inherently authenticated trusted time; approve the
local network/clock trust assumptions; that decision remains open (TICKET-180, TICKET-209). David L. Mills, *Simple Network Time Protocol (SNTP) Version 4 for IPv4, IPv6 and OSI*, IETF RFC 4330, January 2006, §9, DOI: 10.17487/RFC4330, <https://www.rfc-editor.org/rfc/rfc4330#section-9> (accessed 2026-10-24), describes unauthenticated SNTP security limitations. Credentials are private deployment configuration.

Active network work and live listening use an exclusive controller lease. Retain an
established station association during listening; do not run setup/reconnect/delivery jobs.
Start during Wi-Fi setup requests safe teardown before audio; stop audio before granting network;
Start during analysis or sending is rejected Busy, with no cancellation or queued start. A fresh Start after release primes/starts audio.
If release cannot be proven, remain stopped and show the reason. Radio/driver background behavior
must be measured; disabling application jobs alone is not proof of interference isolation.

[Wi-Fi setup and recovery](../COMMUNICATION/interfaces-and-behavior.md#wi-fi-setup-and-recovery) and [portal behavior](../PORTAL/interfaces-and-behavior.md) define the communication-specific contracts.

## Failure contract

Service operations return Accepted / Rejected(reason) / Busy for commands and emit one terminal
outcome per accepted action ID. Essential audio faults mute; optional display/touch/SD failure
degrades capability. Analysis gaps invalidate analysis, not all listening. No component formats SD
or persists captured patient audio. No old result is relabelled with a new ID. Error indication and recovery follow the current [catalogue](../FEEDBACK/catalogue.md#status-and-error-catalogue), including its Wi-Fi-only audio exception and restart rules. Watchdog
detection thresholds and diagnostic cost are open; a bounded request is preferable to an implicit retry loop.

## MVP session baseline

Raw capture/REC/replay is optional; BPM retains bounded streaming analysis state and window estimates. Session identity changes are never applied and follow SESSION_CONTEXT_CHANGE halt/restart handling in the current catalogue. Invalid BPM sends no numeric value and uses a separately validated error-report contract. Current session state transitions are in [the state diagram](../../architecture/system/mvp-session-state.puml).

## LED indication and error handling

CONTROL selects feedback under the architectural fault-containment rules. The dedicated FEEDBACK design defines the status/error catalogue, acknowledgement, priorities and P22 indication values.

## Later FHIR phase

Time synchronization, secure server transport and Device registration are later FHIR
work, not Wi-Fi setup completion conditions. The device does not select patients;
it only reuses a patient reference supplied with a server-requested examination; otherwise it sends no patient reference. Existing persistent registration
and delivery requirements remain for that later phase (TICKET-180, TICKET-181, TICKET-194, TICKET-197).

## Design constraints

The following constraints guide implementation.
They are checked by design review and developer tests, not by the [system requirements](../../requirements/system-requirements.md).
Values are in [design parameters](parameters.md). Optional parts (replay, Lung, display, touch, SD) are not listed; see TICKET-202, TICKET-203 and TICKET-206.

| Area | Constraint |
|---|---|
| Hardware | ESP32-S3 N16R8, INMP441 on I2S0, PCM5102A on I2S1, maintained carrier pin map, potentiometer on ADC1. The device ends at the DAC line output; the amplifier is outside the project scope. Document chestpiece coupling and the microphone low-frequency limit. |
| Audio | Convert INMP441 signed 24-bit left-channel data into normalized mono blocks with sequence numbers. DMA buffers in internal RAM, TX primed with silence, mono duplicated to both DAC channels. Listening continues when analysis cannot accept a block; the gap invalidates the affected BPM window. On microphone/DAC failure: silence, cancel the session, Error with audio muted; restore the cause and restart as required by the catalogue. |
| Input | Debounced, timestamped events, one per stable transition. Interrupt handlers only signal deferred work. Volume clamped to 0–100 %. On potentiometer ADC failure or an invalid switch position: safe value, then CONTROL_INPUT_FAILURE (restart). A long press (≥2 s) is a distinct event and suppresses the ordinary press. |
| Controller | Only writer of mode, filter and workflow state; others send events and read snapshots. Context changes during a session are rejected with SESSION_CONTEXT_CHANGE halt/restart handling. Active network work only at boot/Idle; Start cancels Wi-Fi setup safely; Start during analysis or sending is Busy. Start/Stop and acknowledgement are separate. Portal only from Idle. |
| Listening | Raw, Murmur and BPM listening filters; Raw applies no band filter. Output saturates before integer conversion. Listening filter and volume never change the analysis input. DSP core in pure C without Zephyr headers or heap use per block. |
| BPM | BPM analysis gets audio before the volume control. Which filter it uses (own analysis filter or a listening filter) is decided by the filter study (TICKET-189). Whole-cycle periodicity, not single S1/S2 peaks. Invalid windows carry a reason; an old BPM is never reused. Aggregation counts overlapping windows once and freezes value, interval and settings. Cancel discards the aggregation. No fixed numeric quality threshold. |
| Network | Connection, time sync, TLS and HTTP only under the Idle lease. FHIR R4 Observation (LOINC 8867-4, UCUM /min, `effectiveDateTime` = interval end), conditional create with `device` reference, `subject` copied only from a server-requested examination with a supplied patient reference, otherwise omitted, up to 3 retries, `201`/`200` as receipt, no readback. HTTPS verifies chain, hostname and validity against the lab CA; no plain-HTTP fallback. Credentials stay out of source and logs. Wi-Fi credentials and the server-assigned Device id persist in the flash settings partition; Device registration creates the server resource once and reuses its stored id after restart. |
| Indication | RGB LED shows the context colour and status pattern; during an error it keeps the colour of the context where the error occurred. The red button LED shows the blink code of the highest-priority error (see [status and error catalogue](../FEEDBACK/catalogue.md#status-and-error-catalogue)). The catalogue is one append-only `FEEDBACK_` enum. Errors also go to the serial log, written by the component that detects them. Hotspot: open AP, setup at boot/Idle only, inactivity timeout, bounded clients; no credentials in logs. |
| Monitoring | Count stalls, dropped blocks, deadline misses, clipping, analysis gaps and queue saturation. Report stack/heap watermarks. A stalled required worker raises an Error with audio muted. Initialization alone never counts as verified operation. |

## Firmware layer structure

L2 owns orchestration; L1 remains thin. `L2_COMMUNICATION` is the only path to a send: it has `L1_FHIR` serialize the frozen `MeasurementResult` and passes the payload to `L1_WIFI` under the CONTROL lease. It never selects or adds a patient ID; only an examination-supplied reference may be reused. The server-request mechanism remains an open integration design input. MON observes delivery. Test recordings are handled like patient data. `L2_AUDIO` owns the real-time audio thread and executes `AudioCommand`s; CONTROL remains the single writer of mode state.
