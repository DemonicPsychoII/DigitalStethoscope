# Interface contracts and detailed design

**Status: proposed design derived from S03/S04.** Data structures and operation names specify
semantics, not final C declarations. Agree open representation/sizing before coding. The diagrams
allocate ownership; these contracts make hand-offs testable. Components consume injected data
in host tests and adapters on target. No implementation or firmware migration is included.

## Static dependency and module map

The thesis firmware lives in [`coding/app/`](../coding/app/README.md) (D11, decided 14 October); its README is the
authoritative folder and layer map. L1 holds thin hardware adapters over Zephyr drivers and pure-C libraries;
L2 orchestrates them. The earlier capability-based split (`application/`, `services/`, `platform/` in
`coding/thesis-zephyr/`) is superseded. Keep `bringup-zephyr/` as evaluation evidence.

The components below are logical responsibilities, not folders. They map to `coding/app/` as follows:
INP → `L1_PHYSICALINTERFACE` + `L2_CONTROL`; CTL → `L2_CONTROL`; AUD → `L1_I2S` + `L2_AUDIO`;
LIS → `L1_FILTER` + `L2_AUDIO`; BPM → `L1_BPM` + `L2_AUDIO`; NET → `L1_WIFI` + `L1_FHIR` + `L2_COMMUNICATION`;
UI → LEDs in `L1_PHYSICALINTERFACE`, shell in `L2_SHELL`; MON → `MONITOR`. REC, STO and the display are optional
and not part of the MVP. Pure-C libraries have no RTOS/filesystem/UI/network includes. Worker completion and
health notifications are events to the controller, not direct writes into application state.
MON observes bounded counters/events; it must not become an unrestricted caller of every API.

| Component | Owns / writes | Inputs | Outputs / proposed operations |
|---|---|---|---|
| INP | debounce/contact/calibration state | ISR notice, GPIO/ADC/touch samples | `publish_control(event)`; stable-state reconciliation |
| CTL | settings, workflow state, generation, patient/point | control/completion/health events | `dispatch(event)`, `snapshot()`, session-tagged commands, network lease |
| AUD | DMA pool, source generation, transport progress | mic/fixture blocks, source/stop commands | normalized `AudioBlock`, capture/analysis fan-out, TX submission |
| LIS | listening coefficients and filter/ramp history | block, command snapshot | saturating mono output, levels/clipping |
| BPM | analysis window, estimates, coverage, aggregation | original-rate blocks, session configuration | validity updates and immutable `MeasurementResult` |
| UI | redraw progress/display model/shell state | `StateSnapshot` | bounded SPI redraw, LED state, control requests |
| NET | frozen job, connection, outcome | result/config + Idle lease | serialized Observation, outcome, lease-release acknowledgement |
| MON | anomaly counters, health evidence | worker checkpoints/counters | fault events, evidence snapshots |

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
| `MeasurementResult` | result/session ID, source/generation, valid flag/reason, BPM value and declared precision, quality definition/value, coverage, first/last sample index, measurement monotonic interval and UTC mapping, frozen patient/point/config/filter IDs, completion status. Invalid results carry no sendable numeric value. |
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
| Measurement Acquiring | freeze context/config/ID and clear aggregation | original-rate windows; independent filter; valid estimates | Stop <15 s cancels; Stop ≥15 s → Finalizing; identity change rejected; DA invalidates session |
| Finalizing | stop accepting windows for that interval | aggregate and union valid temporal coverage | freeze valid/invalid result once; late blocks cannot mutate result |
| Delivery Pending | retain completed result and unsent identity | wait for Idle/prerequisites; do not force stop | grant job once; full slot leaves visible Pending |
| Sending | acquire exclusive Idle lease; snapshot payload | bounded connect/TLS/conditional POST/readback | outcome event + release lease; Start is Busy, never queued |
| Fault | mute and invalidate active acquisition | expose latched DA cause | full device restart to Boot only |

Changing Heart/Lung, source, patient or point during a session is rejected with a normal fault and leaves the frozen context unchanged. Outside a session the controller may accept configuration changes and reset source-dependent histories. Generation checks reject stale completions. Separate acknowledgement clears normal-fault indication without starting, retrying or changing an active workflow. Device Alarm remains latched until full restart.

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
`effectivePeriod` failed the R4 heart-rate profile in validation. The interval stays in the local result. Preserve subject, point (approved coding or
evaluation-only metadata), value, interval and analysis settings in the immutable local result.
The local profile/metadata mapping and decimal precision require agreement.

NET verifies CA/name/time, checks bounded status/body parsing, and GETs the resource to compare
identifier/subject/device/code/unit/value/`effectiveDateTime` (D08, 12 October). Accepted without successful readback = Unverified, not Sent.
An uncertain response is retried within the same bounded job; conditional create returns the existing resource instead of a duplicate. Configuration/auth errors and server failures remain visible after the last attempt.
SNTP is a clock synchronization mechanism, not inherently authenticated trusted time; approve the
local network/clock trust assumptions. Credentials are private deployment configuration.

Network and live listening use an exclusive controller lease. Stop audio before granting network;
Start during analysis/sending is rejected Busy, with no cancellation or queued start. A fresh Start after release primes/starts audio.
If release cannot be proven, remain stopped and show the reason. Radio/driver background behavior
must be measured; disabling application jobs alone is not proof of interference isolation.

## Failure contract

Service operations return Accepted / Rejected(reason) / Busy for commands and emit one terminal
outcome per accepted action ID. Essential audio faults mute; optional display/touch/SD failure
degrades capability. Analysis gaps invalidate analysis, not all listening. No component formats SD
or persists captured patient audio. No old result is relabelled with a new ID. DA requires complete restart; normal Wi-Fi indication clears manually only. Watchdog
detection thresholds and diagnostic cost are open; a bounded request is preferable to an implicit retry loop.

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.

## Current MVP baseline — 11 October

[Owner decisions and numeric proposals](../planning/mvp-decisions-2026-10-11.md) supersede older clip/retry/recovery proposals here. Raw capture/REC/replay is optional; BPM retains bounded streaming analysis state and window estimates. Session identity changes are rejected with normal fault, never applied. Invalid BPM sends no numeric value and uses a separately validated error-report contract. Current session state transitions are in [the state diagram](../architecture/mvp-session-state.puml).

## Patient assignment and hotspot portal — 12 October

[Owner decisions](../planning/mvp-decisions-2026-10-12.md) make the hotspot portal MVP scope; the [sequence diagram](../architecture/patient-assignment-workflow.puml) shows the flow. The FHIR server holds the assignment in `Device.patient`; CTL keeps a local copy that is set only from a matching readback. NET registers the Device at boot without erasing an assignment, loads the list before the hotspot opens and re-reads the assignment before each Observation create (see [Design constraints](#design-constraints)).

Portal is an Idle-only controller state with the exclusive network lease: station Wi-Fi is down, Start and session commands are rejected, and the state ends on confirmation, cancel or timeout. Start does no network work; the session freezes the local assignment. `MeasurementResult` and `NetworkJob` therefore carry the frozen patient reference and the Device ID; a missing local assignment makes the result ineligible for sending. The portal HTTP handler runs outside audio and controller threads and submits typed control events like the shell; it never writes state directly.

## Design constraints

Former component requirements that stay valid as design decisions after the [14 October review](../planning/mvp-decisions-2026-10-14.md).
They are checked by design review and developer tests, not by the [system requirements](../requirements/system-requirements.md).
Values are in [design parameters](parameters.md). Optional parts (replay, Lung, display, touch, SD) are not listed.

| Area | Constraint |
|---|---|
| Hardware | ESP32-S3 N16R8, INMP441 on I2S0, PCM5102A on I2S1, maintained carrier pin map, potentiometer on ADC1. The device ends at the DAC line output; the amplifier is outside the project scope. Document chestpiece coupling and the microphone low-frequency limit. |
| Audio | Convert INMP441 signed 24-bit left-channel data into normalized mono blocks with sequence numbers. DMA buffers in internal RAM, TX primed with silence, mono duplicated to both DAC channels. Listening continues when analysis cannot accept a block; the gap invalidates the affected BPM window. On microphone/DAC failure: silence, cancel the session, Device Alarm until restart. |
| Input | Debounced, timestamped events, one per stable transition. Interrupt handlers only signal deferred work. Volume clamped to 0–100 % with a safe value on ADC failure. A long press (≥2 s) is a distinct event and suppresses the ordinary press. |
| Controller | Only writer of mode, patient, filter and workflow state; others send events and read snapshots. Context changes during a session are rejected with a normal fault. Network work only in Idle; Start during analysis or sending is Busy. Start/Stop and acknowledgement are separate. Portal only from Idle. |
| Listening | Raw, Murmur and BPM listening filters; Raw applies no band filter. Output saturates before integer conversion. Listening filter and volume never change the analysis input. DSP core in pure C without Zephyr headers or heap use per block. |
| BPM | BPM analysis gets audio before the volume control. Which filter it uses (own analysis filter or a listening filter) is decided by the filter study (TICKET-189). Whole-cycle periodicity, not single S1/S2 peaks. Invalid windows carry a reason; an old BPM is never reused. Aggregation counts overlapping windows once and freezes value, interval, patient and settings. Cancel discards the aggregation. No fixed numeric quality threshold. |
| Network | Connection, time sync, TLS and HTTP only under the Idle lease. FHIR R4 Observation (LOINC 8867-4, UCUM /min, `effectiveDateTime` = interval end), conditional create with up to 3 retries, then matching readback. HTTPS verifies chain, hostname and validity against the lab CA; no plain-HTTP fallback. Credentials stay out of source and logs. Device registration and patient assignment follow the [12 October decisions](../planning/mvp-decisions-2026-10-12.md). |
| Indication | Activity LED on during measurement and pulsing while Busy; distinct pattern while the hotspot is open. Errors shown by LED pattern and serial log. Hotspot: WPA2 with a per-device passphrase outside source, Portal state only, timeout, bounded clients; no credentials or patient data in logs. |
| Monitoring | Count stalls, dropped blocks, deadline misses, clipping, analysis gaps and queue saturation. Report stack/heap watermarks. A stalled required worker raises a Device Alarm. Initialization alone never counts as verified operation. |

Updated by Claude-Opus-5.5 on behalf of Nico running in T3 Code through Claude Code.
