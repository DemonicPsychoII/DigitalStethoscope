# Use cases and device workflows

**Status: draft.** Preconditions are guards, not assumptions the implementation may ignore. All IDs are stable. Derived UI commands below require review (D02 in readiness plan).

Playback, measurement and delivery have independent state. “Record audio” in S02 is separated into a volatile replay clip and a measurement session; they may run in parallel, with separate IDs.

## UC-01 — Power up and assess readiness

- **Actors and trigger:** Operator; power-on or explicit recovery
- **Preconditions:** Fitted carrier and approved power/amplifier setup.
- **Postconditions:** Output starts silent; capabilities and degraded/fault status are visible.
- **Normal flow:** Initialize platform and memory; prime DAC with silence; check audio, controls and optional devices; publish Ready/Idle; await explicit listening command.
- **Alternatives/errors:** Essential microphone/DAC failure → muted Fault. Display/touch/SD/network failure → degraded capability, never falsely marked physically verified.

## UC-02 — Listen and change parameters

- **Actors and trigger:** Operator; start, filter/speed/volume/mode/point events
- **Preconditions:** Audio ready; network lease released.
- **Postconditions:** Live listening uses selected filter at 1×; controller/UI agree on effective settings.
- **Normal flow:** Start live; normalize microphone blocks; independently fan out analysis; apply listening filter, smoothed volume and saturation; handle stable control events at block boundaries.
- **Alternatives/errors:** Slow speed in Live selects future replay speed, not unbounded live slowdown. Lung forces Raw/1×. Invalid switch contact keeps last valid setting; stop mutes output.

## UC-03 — Capture a clip and replay slowly

- **Actors and trigger:** Operator; button or capture command
- **Preconditions:** Heart mode, microphone, active live audio, free bounded clip RAM.
- **Postconditions:** One raw volatile clip is replayed at selected speed then returns to live.
- **Normal flow:** Assign clip ID; turn activity LED on; capture raw before filtering/gain while live continues; at configured capacity finalize clip; replay through selected filter and pitch-preserving speed stage; end returns live.
- **Alternatives/errors:** Button during capture/replay cancels and returns live. Stop ends audio. Mode/source change discards stale clip. Allocation failure rejects capture without interrupting live.

## UC-04 — Evaluate using identical test recordings

- **Actors and trigger:** Researcher; fixture selection/upload
- **Preconditions:** Licensed fixture; declared format/sample rate; evaluation mode.
- **Postconditions:** Reproducible filter comparison with source/configuration recorded; no patient FHIR request.
- **Normal flow:** Validate fixture; prefetch bounded blocks; select fixture with explicit test indication; run the same DSP on device or host; compare each filter against identical input and reference interval.
- **Alternatives/errors:** Missing SD, EOF, truncated/unsupported file or prefetch underrun → stop fixture and report, no fabricated samples or silent change to microphone provenance.

## UC-05 — Determine one heart-rate result

- **Actors and trigger:** Operator; explicit start-measurement event
- **Preconditions:** Heart + microphone; active audio; patient/context captured; analysis parameters approved for evaluation.
- **Postconditions:** One completed valid/invalid immutable result, or an explicitly cancelled session.
- **Normal flow:** Assign session ID; freeze patient, point and analysis configuration; analyze original-rate windows independently of listening; aggregate accepted estimates over configured duration; freeze interval, quality, coverage and provenance.
- **Alternatives/errors:** Poor quality/clipping/gaps prevent accepted windows. Cancel/context change/audio fault discards incomplete session. Invalid coverage produces invalid result and no send. Do not count S1/S2 as two beats.

## UC-06 — Deliver or retry a completed result

- **Actors and trigger:** Operator and FHIR/time services; result eligible, stop listening, explicit retry
- **Preconditions:** Valid completed microphone result; Idle; patient/server/auth/time/trust configured.
- **Postconditions:** One initial attempt per result; verified delivery or visible failed/unverified outcome.
- **Normal flow:** Wait without stopping listening; operator stops; controller grants network lease; create R4 Observation; validate TLS/name/time; PUT stable ID; parse response; read back matching content; release lease.
- **Alternatives/errors:** No config, invalid time or source → no request. Timeout/4xx/5xx/readback failure remains visible. Explicit retry retains ID, interval, patient and value. Start listening cancels/drains network before audio restarts.

## UC-07 — Operate in lung mode

- **Actors and trigger:** Operator; select Lung
- **Preconditions:** Audio ready.
- **Postconditions:** Raw live at 1×; no BPM, clip replay or FHIR.
- **Normal flow:** Controller cancels active clip/measurement; invalidates heart estimate; forces Raw and 1×; displays Lung; keeps volume and point controls available.
- **Alternatives/errors:** BPM/replay/send commands rejected with reason. Previously completed heart result is retained only as historical context and cannot be sent while in Lung.

## UC-08 — Cancel, stop or recover from faults

- **Actors and trigger:** Operator or MON; cancel/stop/failure
- **Preconditions:** Any active operation or muted Fault.
- **Postconditions:** Buffers and jobs have a documented outcome; essential failure stays muted until recovery succeeds.
- **Normal flow:** Cancel clip or measurement independently; stop cancels active operations and mutes; MON reports essential fault; controller releases resources; explicit recovery reinitializes boundedly and returns Idle.
- **Alternatives/errors:** UI or SD failure preserves microphone listening. Resource/analysis overflow resets analysis validity. Recovery failure remains Fault; no endless retry or old result relabelled as new.

## UC-09 — Configure and inspect the prototype

- **Actors and trigger:** Operator/researcher; setup or diagnostics
- **Preconditions:** Idle for network/time configuration; authorized physical/serial access.
- **Postconditions:** Validated configuration and capability/measurement evidence available without secrets in logs.
- **Normal flow:** Calibrate touch and volume; assign patient and named listening point; set server/trust/auth/time; inspect build/carrier/config IDs, timing/resource/error counters; select approved research parameters.
- **Alternatives/errors:** Reject invalid values atomically. Configuration changes cannot mutate a frozen result. Diagnostic test sources stay visibly marked and excluded from patient delivery.

## Control workflow proposal

The physical button starts clip capture from Live and cancels capture/replay on the next press. Separate touch/shell commands provide Start listening, Stop, Start measurement, Cancel measurement, Send/retry and Recovery. No undocumented long-press behavior is assumed. Mode/source/patient/point changes during acquisition cancel that measurement to avoid mixing contexts. A valid completed result can wait in Pending while listening continues. Entering Idle permits an initial send only if delivery prerequisites are met; failed delivery never loops automatically.

Physical switches, touch and shell use last stable transition wins for filter/speed. An unchanged physical switch does not overwrite a newer touch/shell choice every polling cycle. Display shows effective settings and pending replay speed, not simply contact positions.

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
