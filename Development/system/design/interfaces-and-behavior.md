# Interface contracts and detailed design

**Status: proposed design derived from S03/S04.** Data structures and operation names specify
semantics, not final C declarations. Agree open representation/sizing before coding. The diagrams
allocate ownership; these contracts make hand-offs testable. Components consume injected data
in host tests and adapters on target. No implementation or firmware migration is included.

## Static dependency and module map

Proposed thesis folder: `coding/thesis-zephyr/` (name open D11), with `application/` (controller,
dashboard), `services/` (audio, input, storage, measurement, delivery, pure-C `dsp/` algorithms),
`platform/` (thin Zephyr adapters), `monitoring/`, `include/` and `tests/`. Keep `bringup-zephyr/` as evaluation
evidence. Do not reuse the unused custom HAL skeleton as a second driver stack.

Application depends on service contracts; services own the pure-C DSP algorithms and depend on
platform contracts; adapters depend on Zephyr. DSP is part of Services, not a fourth layer,
and has no RTOS/filesystem/UI/network includes. Worker completion and
health notifications are events to the controller, not direct writes into application state.
MON observes bounded counters/events; it must not become an unrestricted caller of every API.

| Component | Owns / writes | Inputs | Outputs / proposed operations |
|---|---|---|---|
| INP | debounce/contact/calibration state | ISR notice, GPIO/ADC/touch samples | `publish_control(event)`; stable-state reconciliation |
| CTL | settings, workflow state, generation, patient/point | control/completion/health events | `dispatch(event)`, `snapshot()`, session-tagged commands, network lease |
| AUD | DMA pool, source generation, transport progress | mic/fixture blocks, source/stop commands | normalized `AudioBlock`, capture/analysis fan-out, TX submission |
| LIS | listening coefficients and filter/ramp history | block, command snapshot | saturating mono output, levels/clipping |
| REC | clip buffer, valid length, replay cursor/WSOLA history | raw capture blocks, capture/replay/cancel | clip metadata, replay blocks, completion event |
| BPM | analysis window, estimates, coverage, aggregation | original-rate blocks, session configuration | validity updates and immutable `MeasurementResult` |
| STO | file handle, prefetch pool, fixture metadata | select/read/cancel fixture | validated normalized blocks; EOF/error |
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
| `NetworkJob` | stable Observation ID, immutable result/payload, frozen endpoint/profile/auth-config reference, attempt type/count, lease ID. Secrets stay outside evidence. Result patient/time/value never resnapshotted from live state on retry. |
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
returns Busy and retains the completed result visibly; it does not silently overwrite a result.

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
| Measurement Acquiring | freeze context/config/ID and clear aggregation | original-rate windows; independent filter; valid estimates | duration → Finalizing; context/cancel/fault discards session |
| Finalizing | stop accepting windows for that interval | aggregate and union valid temporal coverage | freeze valid/invalid result once; late blocks cannot mutate result |
| Delivery Pending | retain completed result and unsent identity | wait for Idle/prerequisites; do not force stop | grant job once; full slot leaves visible Pending |
| Sending | acquire exclusive Idle lease; snapshot payload | bounded connect/TLS/PUT/readback | outcome event + release lease; start request cancels/drains first |
| Fault | mute and invalidate active acquisition | expose cause, bounded explicit recovery | reinitialize to Boot; no automatic unbounded restart |

Changing Heart/Lung or source cancels relevant capture/measurement, resets filter/analysis context
and rejects stale completions. Patient/point changes cancel an acquiring measurement but cannot
modify a completed result. Analysis coefficient changes during a session require cancel/restart
rather than aggregating across undocumented configurations. Playback filter changes are allowed.

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
plus session counter and keep the resulting FHIR resource ID stable for all attempts. Use PUT
`/Observation/{id}` only after confirming the server permits update/create; do not switch to POST
silently. One initial attempt may be queued automatically when a valid result and Idle/config
prerequisites coincide; explicit retry is required after failure. Eligibility in Lung is denied.

Map sample/monotonic measurement interval to UTC from an approved clock anchor. Use measurement
time, not send time; clock loss/skew makes the result ineligible until its mapping is resolved,
not rewritten. FHIR `effectivePeriod` is proposed for the aggregate interval (D08), versus existing
bring-up `effectiveDateTime` of a rolling estimate. Preserve subject, point (approved coding or
evaluation-only metadata), value, interval and analysis settings in the immutable local result.
The local profile/metadata mapping and decimal precision require agreement.

NET verifies CA/name/time, checks bounded status/body parsing, and GETs the resource to compare
ID/subject/code/unit/value/interval. Accepted without successful readback = Unverified, not Sent.
An explicit retry after an uncertain response uses identical ID/payload to avoid duplicate logical
observations. Configuration/auth errors and server failures remain visible; no automatic retry loop.
SNTP is a clock synchronization mechanism, not inherently authenticated trusted time; approve the
local network/clock trust assumptions. Credentials are private deployment configuration.

Network and live listening use an exclusive controller lease. Stop audio before granting network;
a start request first cancels/drains network, then waits for release, then primes/starts audio.
If release cannot be proven, remain stopped and show the reason. Radio/driver background behavior
must be measured; disabling application jobs alone is not proof of interference isolation.

## Failure contract

Service operations return Accepted / Rejected(reason) / Busy for commands and emit one terminal
outcome per accepted action ID. Essential audio faults mute; optional display/touch/SD failure
degrades capability. Analysis gaps invalidate analysis, not all listening. No component formats SD
or persists captured patient audio. No old result is relabelled with a new ID. Recovery, watchdog
thresholds and diagnostic cost are open; a bounded request is preferable to an implicit retry loop.

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
