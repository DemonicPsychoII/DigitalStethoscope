# Interface contracts and detailed design

**Status: proposed design derived from S03/S04.** Data structures and operation names specify
semantics, not final C declarations. Agree open representation/sizing before coding. The diagrams
allocate ownership; these contracts make hand-offs testable. Components consume injected data
in host tests and adapters on target. No implementation or firmware migration is included.

## Static dependency and module map

The thesis firmware lives in [`coding/app/`](../coding/app/README.md) (D11, decided 14 October); its README is the
authoritative folder and layer map. The [13 October decisions](../planning/mvp-decisions-2026-10-13.md) fix the layer
layout. The earlier capability-based split (`application/`, `services/`, `platform/` in `coding/thesis-zephyr/`) is
superseded. Keep `bringup-zephyr/` as evaluation evidence. Do not reuse the unused custom HAL skeleton as a second
driver stack.

- **L0 is Zephyr:** drivers, DMA, interrupts and the devicetree overlay. No project code.
- **L1 adapters** call Zephyr driver APIs directly: `L1_I2S` (microphone RX and DAC TX),
  `L1_WIFI` (Wi-Fi, TLS, time), `L1_PORTAL` (HTTP server of the Wi-Fi setup page),
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
REC, STO and the display are optional and not part of the MVP.

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
| `AudioBlock` | pool handle, source ID/generation, sequence, first sample index, sample rate, frame count (≤128), representation/valid bits, discontinuity flag, readonly mono sample payload. Microphone is signed 24-bit normalized into int32; alignment convention must be fixed by D03. Timestamp derives from sample count, not worker arrival. |
| `ControlEvent` | event ID/type, origin (physical/touch/shell/worker), monotonic timestamp, typed value, generation where relevant. Controller serializes accepted order; equal timestamps use queue arrival order. Invalid fields are rejected before mutation. |
| `AudioCommand` | unique command ID, controller generation, desired settings, action/session ID. Audio acknowledges applied block boundary or explicit rejection; stale generations are discarded. |
| `StateSnapshot` | snapshot revision, effective and requested settings, source/provenance, playback/measurement/delivery states, active IDs, capabilities, BPM validity/time, clip progress, pending replay speed, error/outcome counters. Read as a coherent copy; UI never edits it. |
| `Clip` | ID/generation, source, raw format/rate, allocated capacity and valid length, capture sample interval, evaluation metadata. Ownership REC; immutable after finalization until discarded. Never patient-persisted. |
| `MeasurementResult` | result/session ID, source/generation, valid flag/reason, BPM value and declared precision, quality definition/value, coverage, first/last sample index, measurement monotonic interval and UTC mapping, frozen Device id/point/config/filter IDs, completion status. Invalid results carry no sendable numeric value. |
| `NetworkJob` | stable Observation identifier (device, random boot ID, session counter), immutable result/payload, frozen endpoint/profile/auth-config reference, attempt count (up to 4: 1 attempt + 3 retries, all within 10 s), lease ID. Secrets stay outside evidence. Result patient/time/value never resnapshotted from live state. |
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
returns Busy without overwriting a job; a terminal failure retains only redacted outcome metadata, with no retry queue.

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
| Idle | mute; no active transport/listening operation | allow configuration and network lease | start only after lease released |
| Live | reset source-dependent state on source generation change | 128-frame normalized fan-out; selected listening filter; gain/saturation; TX | stop/fault mute; capture keeps live path |
| Capture | allocate/claim bounded clip and ID; LED active | copy raw prefilter/pregain; normal live listening continues | full → Replay; cancel → Live; stop/fault → Idle/Fault, incomplete clip invalid |
| Replay | freeze valid clip; initialize speed stage; LED active | raw clip → filter → WSOLA → gain/saturation; fresh mic still feeds analysis | end/cancel → Live; release clip cursor; stop/fault mutes |
| Measurement Acquiring | freeze context/config/ID and clear aggregation | original-rate windows; independent filter; valid estimates | Stop <15 s cancels; Stop ≥15 s → Finalizing; identity change rejected; an Error with audio muted invalidates the session |
| Finalizing | stop accepting windows for that interval | aggregate and union valid temporal coverage | freeze valid/invalid result once; late blocks cannot mutate result |
| Delivery Pending | retain completed result and unsent identity | wait for Idle/prerequisites; do not force stop | grant job once; full slot leaves visible Pending |
| Sending | acquire exclusive Idle lease; snapshot payload | bounded connect/TLS/conditional POST, receipt | outcome event + release lease; Start is Busy, never queued |
| Error, audio affected | mute and invalidate active acquisition; block Start | expose latched cause on the red LED and serial log | use the catalogue clear rule; restart-required faults remain halted until restart |

Changing Heart/Lung, source or point during a session leaves the frozen context unchanged and raises SESSION_CONTEXT_CHANGE with the catalogue halt/restart rule. Outside a session the controller may accept configuration changes and reset source-dependent histories. Generation checks reject stale completions. Separate acknowledgement clears the indication of an Error that the catalogue allows to clear, without starting, retrying or changing an active workflow. A halted Error follows the catalogue clear rule; a short press cannot clear a restart-required fault.

## DSP and measurement design

Draft listening candidates: second-order Butterworth high/low sections (Murmur 40–800 Hz;
BPM emphasis 25–150 Hz), with Raw unity and a 20 ms exponential crossfade. Preserve state for
continuously evaluated paths; clear histories on source reset. These are engineering candidates,
not established optimum bands. Measure response and transients before approving coefficients.
Normalize signed microphone values once; saturate only at output conversion, with clipping
counters. Raw replay precision policy must be settled before reusing the bring-up int16 clip API.

Draft BPM: independent band filter → rectified envelope/downsampled representation → whole-cycle
autocorrelation or agreed equivalent → range/harmonic/quality checks → periodic update. An 8 s
window at 100 Hz envelope rate is 800 samples; a 3 s window at 30 BPM contains only 1.5 cycles
and needs justification. Candidate update 1 s and session 30 s are open. Define a quality score
mathematically and validate it; it is not probability of clinical correctness. Aggregate using a
proposed median of accepted BPM estimates; coverage is the union of accepted window intervals
clipped to session bounds, not number_of_windows × window_length. Warm-up treatment, temporal
weighting, minimum windows and thresholds remain D04/D05. No window includes missing blocks.

Replay candidate is WSOLA with bounded overlap/search buffers. Output length should equal
`ceil(valid_clip_frames / speed)` under the agreed rounding policy, with final partial blocks
padded only for transport. Measure pitch and artifacts on heart sounds, not just sine waves.
Speed changes during replay require an agreed continuity rule (D03); draft restarts the speed
stage at the current source cursor without pretending the duration was constant-speed.

## Delivery, clock and configuration

A completed measurement has separate identity from a replay clip. Use a boot-unique identifier
plus session counter as the Observation `identifier` and create it with `POST` plus `If-None-Exist`
on that identifier; never update an Observation. The server assigns the resource ID (from `Location`).
A retry or collision returns the existing resource instead of overwriting it (D08, 12 October). One delivery job is queued automatically when a result and Idle/config
prerequisites coincide. A failed attempt is retried up to 3 times (4 attempts, about 2 s apart, all within 10 s); then the job ends with a visible error ([14 October](../planning/mvp-decisions-2026-10-14.md)).

Map sample/monotonic measurement interval to UTC from an approved clock anchor. Use measurement
time, not send time; clock loss/skew makes the result ineligible until its mapping is resolved,
not rewritten. FHIR `effectiveDateTime` carries the end of the aggregate interval (D08, 12 October):
`effectivePeriod` failed the R4 heart-rate profile in validation. The interval stays in the local result. Preserve the Device id, point (approved coding or
evaluation-only metadata), value, interval and analysis settings in the immutable local result.
The local profile/metadata mapping and decimal precision require agreement.

NET verifies CA/name/time and checks bounded status/body parsing. `201 Created` or `200` (existing conditional create) is the receipt and marks the result Sent; there is no readback ([15 October](../planning/mvp-decisions-2026-10-15.md)).
An uncertain response is retried within the same bounded job; conditional create returns the existing resource instead of a duplicate. Configuration/auth errors and server failures remain visible after the last attempt.
SNTP is a clock synchronization mechanism, not inherently authenticated trusted time; approve the
local network/clock trust assumptions. Credentials are private deployment configuration.

Active network work and live listening use an exclusive controller lease. Retain an
established station association during listening; do not run setup/reconnect/delivery jobs.
Start during Wi-Fi setup requests safe teardown before audio; stop audio before granting network;
Start during analysis/sending is rejected Busy, with no cancellation or queued start. A fresh Start after release primes/starts audio.
If release cannot be proven, remain stopped and show the reason. Radio/driver background behavior
must be measured; disabling application jobs alone is not proof of interference isolation.

## Failure contract

Service operations return Accepted / Rejected(reason) / Busy for commands and emit one terminal
outcome per accepted action ID. Essential audio faults mute; optional display/touch/SD failure
degrades capability. Analysis gaps invalidate analysis, not all listening. No component formats SD
or persists captured patient audio. No old result is relabelled with a new ID. Error indication and recovery follow the current [catalogue](#status-and-error-catalogue), including its Wi-Fi-only audio exception and restart rules. Watchdog
detection thresholds and diagnostic cost are open; a bounded request is preferable to an implicit retry loop.

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.

## MVP session baseline

[Owner decisions and numeric proposals](../planning/mvp-decisions-2026-10-11.md) supersede older clip/retry/recovery proposals here. Raw capture/REC/replay is optional; BPM retains bounded streaming analysis state and window estimates. Session identity changes are never applied and follow SESSION_CONTEXT_CHANGE halt/restart handling in the current catalogue. Invalid BPM sends no numeric value and uses a separately validated error-report contract. Current session state transitions are in [the state diagram](../architecture/mvp-session-state.puml).

## Wi-Fi setup and recovery — 19 October

The [18 October discussion](../planning/mvp-decisions-2026-10-18.md) and
[19 October resolutions](../planning/mvp-decisions-2026-10-19.md) define this project design.
The [state diagram](../architecture/wifi-state.puml),
[setup flow](../architecture/wifi-flow.puml) and
[recovery flow](../architecture/wifi-recovery.puml) share the rules below.

Read settings through L1. At boot, join a stored network with four attempts total,
5 s between failures. Exhaustion shows an error and waits for a 2 s hold in Idle.
Without credentials, or on a 2 s hold in Idle, scan/cache first, then open the AP
and serve one HTML document. Rescan explicitly or after a failed portal join;
keep AP/server open for these rescans and publish the cache only after scan-finished.
Scan has four attempts total, 5 s between failures. Exhausted scan or AP-start failure
permits a manual 2 s setup retry. Link loss has four reconnect attempts, 5 s apart;
exhaustion starts setup automatically in Idle. Defer all active recovery during listening.

The hotspot is open. The phone joins it manually, then a QR code opens the portal URL;
manual rejoin is accepted. Hide the password field for open selected networks. The
HTTP handler queues typed requests (Connect, Rescan, Cancel, activity) for
COMMUNICATION, which reads them with `portal_waitForRequest()`, outside controller/audio
threads; the browser polls status. One portal join attempt waits for the selected network's
address. A stale existing link is not a successful new join. On failure show the
cause, rescan and return to selection. On success use `wifi_storeSettings()` in L1;
retry saving once. Preserve the old valid record on failure. Show success or save
warning for 10 s, close AP/server and keep the station, including with unsaved credentials.
L1 also owns `wifi_readSettings()`; L2 owns workflow policy.

Form Back/Cancel returns to selection; setup Cancel closes setup. No user cancellation
is accepted after Connect submission through saving/automatic closure. Timeout is
five minutes without selection, password input or Rescan; polling does not reset it.
Pause during operations. Send the closing notice before teardown, with no extra 10 s
Cancel/timeout delay. Retain an established station; otherwise cancel attempts and
release Wi-Fi services. Software errors that prevent continuing setup log/show the
cause, clean up and return to offline operation. Later 2 s holds can retry.

A Start request during setup cancels active setup, waits for safe teardown and then
starts audio. Preserve an established station association. Serialize cancellation
against join completion, reject stale callbacks and finish an atomic settings write
safely. The planned implementation uses a spinlock-protected requested listening state
and a semaphore wakeup, so coalesced events cannot lose the final Start/Stop state.
CONTROL serializes its commands with the release wait. No acknowledgement is
valid until L1 confirms scan/connect cancellation and portal/DHCP/AP shutdown;
failed cleanup keeps audio stopped and is retried. A new Start invalidates the
previous acknowledgement. The 200 ms wait slice is a candidate event-check
interval, not a measured bound on total teardown or settings-write latency.
Setup/reconnect/delivery work is prohibited during listening; retained radio
association and background traffic still require interference measurements.

Time synchronization, secure server transport and Device registration are later FHIR
work, not Wi-Fi setup completion conditions. The device does not select patients;
it passes on only server-linked patient references. Existing persistent registration
and delivery requirements remain for that later phase.

<a id="led-indication-and-single-error-type--16-october"></a>

## LED indication and error handling — 19 October

The [19 October owner resolutions](../planning/mvp-decisions-2026-10-19.md) adopt
the catalogue below as the current project design. It replaces the earlier light table.
The RGB status light never shows red; the separate red button light shows error codes.
Serial logs retain the detailed cause. Timing is in [P22](parameters.md).
No hardware revision is planned: the GPIO14 filter-switch move is dropped and the pin map stays as it
is (19 October). On DevKitC-1 v1.1 the RGB LED data pin (GPIO38) is also the BPM switch contact, so
confirm the fitted board revision before the RGB LED driver is enabled.

### Status and error catalogue

This table is authoritative for feedback. It records project decisions, not standards
conformity or implemented firmware. Recovery and acknowledgement are separate.

- **One feedback catalogue.** Wi-Fi-only failures preserve working audio and permit
  offline Start. Recovery follows the Wi-Fi rules above and need not wait for error
  acknowledgement. Other errors stop the active workflow, mute/cancel active audio
  and block Start until the catalogue clear rule is met. Restart means reset/power cycle.
  Generic device settings failures are distinct from Wi-Fi credential-save failures.
- **RGB LED = context.** The colour shows the context in which a status or error occurs, not the module that
  detects it. CONTROL decides what can run, so each context has one colour: white = device (startup,
  settings, session input), green = Idle, cyan = audio, violet = Wi-Fi, blue = FHIR.
- **Standards basis.** Colours follow IEC 60601-1 7.8.1 (green only for Idle, no red, yellow or orange on
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
- **Sort order.** Sort rows by RGB colour, then by number of blinks ("off" first). "No change" rows are
  overlays on the current colour and come last.
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
- **Restart** means the reset button or a power off/on cycle.
- **Code naming.** `<SUBJECT>_<OUTCOME>` in upper case with underscores and no abbreviations, for example
  `SCAN_FAILURE`. Outcome words: no suffix, `RUNNING`, `OPEN` or `PENDING` for a normal status;
  `SUCCESSFUL`, `RECEIVED` or `VALID` for a positive result; `REJECTED`, `FAILURE`, `STALL` or `INVALID`.
  The C enumerator adds the prefix `FEEDBACK_` (for example `FEEDBACK_SCAN_FAILURE`) to keep the global
  namespace clean. The catalogue is one enum. After the first implementation, new codes are only appended,
  so existing values never change.
- **Logging is separate.** The component that detects the fault logs the details (sub-cause, HTTP status,
  failed check). The LED interface only receives the code. The `HealthEvent` error class uses the same
  enumerator.

The catalogue table is reviewed together with the Wi-Fi implementation.

## Design constraints

Former component requirements that stay valid as design decisions after the [14 October review](../planning/mvp-decisions-2026-10-14.md).
They are checked by design review and developer tests, not by the [system requirements](../requirements/system-requirements.md).
Values are in [design parameters](parameters.md). Optional parts (replay, Lung, display, touch, SD) are not listed.

| Area | Constraint |
|---|---|
| Hardware | ESP32-S3 N16R8, INMP441 on I2S0, PCM5102A on I2S1, maintained carrier pin map, potentiometer on ADC1. The device ends at the DAC line output; the amplifier is outside the project scope. Document chestpiece coupling and the microphone low-frequency limit. |
| Audio | Convert INMP441 signed 24-bit left-channel data into normalized mono blocks with sequence numbers. DMA buffers in internal RAM, TX primed with silence, mono duplicated to both DAC channels. Listening continues when analysis cannot accept a block; the gap invalidates the affected BPM window. On microphone/DAC failure: silence, cancel the session, Error with audio muted; restore the cause and restart as required by the catalogue. |
| Input | Debounced, timestamped events, one per stable transition. Interrupt handlers only signal deferred work. Volume clamped to 0–100 %. On potentiometer ADC failure or an invalid switch position: safe value, then CONTROL_INPUT_FAILURE (restart). A long press (≥2 s) is a distinct event and suppresses the ordinary press. |
| Controller | Only writer of mode, filter and workflow state; others send events and read snapshots. Context changes during a session are rejected with SESSION_CONTEXT_CHANGE halt/restart handling. Active network work only at boot/Idle; Start cancels Wi-Fi setup safely; Start during analysis or sending is Busy. Start/Stop and acknowledgement are separate. Portal only from Idle. |
| Listening | Raw, Murmur and BPM listening filters; Raw applies no band filter. Output saturates before integer conversion. Listening filter and volume never change the analysis input. DSP core in pure C without Zephyr headers or heap use per block. |
| BPM | BPM analysis gets audio before the volume control. Which filter it uses (own analysis filter or a listening filter) is decided by the filter study (TICKET-189). Whole-cycle periodicity, not single S1/S2 peaks. Invalid windows carry a reason; an old BPM is never reused. Aggregation counts overlapping windows once and freezes value, interval and settings. Cancel discards the aggregation. No fixed numeric quality threshold. |
| Network | Connection, time sync, TLS and HTTP only under the Idle lease. FHIR R4 Observation (LOINC 8867-4, UCUM /min, `effectiveDateTime` = interval end), conditional create with `device` reference, `subject` only when the server has linked a patient, up to 3 retries, `201`/`200` as receipt, no readback. HTTPS verifies chain, hostname and validity against the lab CA; no plain-HTTP fallback. Credentials stay out of source and logs. Wi-Fi credentials and the server-assigned Device id persist in the flash settings partition; Device registration follows the [15 October decisions](../planning/mvp-decisions-2026-10-15.md). |
| Indication | RGB LED shows the context colour and status pattern; during an error it keeps the colour of the context where the error occurred. The red button LED shows the blink code of the highest-priority error (see [status and error catalogue](#status-and-error-catalogue)). The catalogue is one append-only `FEEDBACK_` enum. Errors also go to the serial log, written by the component that detects them. Hotspot: open AP, setup at boot/Idle only, inactivity timeout, bounded clients; no credentials in logs. |
| Monitoring | Count stalls, dropped blocks, deadline misses, clipping, analysis gaps and queue saturation. Report stack/heap watermarks. A stalled required worker raises an Error with audio muted. Initialization alone never counts as verified operation. |

## Firmware layer structure — 13 October

[Owner decisions](../planning/mvp-decisions-2026-10-13.md) move orchestration into L2 and keep L1
thin. `L2_COMMUNICATION` is the only path to a send: it has `L1_FHIR` serialize the frozen
`MeasurementResult` and passes the payload to `L1_WIFI` under the CONTROL lease. The 13 October pre-send
assignment check was dropped on [15 October](../planning/mvp-decisions-2026-10-15.md); MON still observes delivery. The
[14 October decisions](../planning/mvp-decisions-2026-10-14.md) drop the separate test-source send rule:
test recordings are handled like patient data. `L2_AUDIO` owns the real-time audio thread and executes
`AudioCommand`s; CONTROL remains the single writer of mode state.

Updated by Claude-Opus-5.5 on behalf of Nico running in T3 Code through Claude Code.

Updated by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
