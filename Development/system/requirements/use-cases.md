# Use cases and device workflows

**Status: draft.** Preconditions are guards, not assumptions the implementation may ignore. All IDs are stable. Derived UI commands below require review (D02 in readiness plan).

Playback, measurement and delivery have independent state. “Record audio” in S02 is separated into a volatile replay clip and a measurement session; they may run in parallel, with separate IDs.

## UC-01 — Power up and assess readiness

- **Actors and trigger:** Operator; power-on or full restart after Device Alarm
- **Preconditions:** Fitted carrier and approved power/amplifier setup.
- **Postconditions:** Output starts silent; capabilities and degraded/fault status are visible.
- **Normal flow:** Initialize platform and memory; prime DAC with silence; check audio, controls and optional devices; publish Ready/Idle; await explicit listening command.
- **Alternatives/errors:** Essential microphone/DAC startup failure → muted, latched Device Alarm; recovery requires a full device restart and successful startup checks. Display/touch/SD/network failure → degraded capability, never falsely marked physically verified.

## UC-02 — Listen and change parameters

- **Actors and trigger:** Operator; start, filter/speed/volume/mode/point events
- **Preconditions:** Audio ready; network lease released.
- **Postconditions:** Live listening uses selected filter at 1×; controller/UI agree on effective settings.
- **Normal flow:** Start live; normalize microphone blocks; independently fan out analysis; apply listening filter, smoothed volume and saturation; handle stable control events at block boundaries.
- **Alternatives/errors:** Slow speed in Live selects future replay speed, not unbounded live slowdown. Lung forces Raw/1×. Invalid switch contact keeps last valid setting; stop mutes output.

## UC-03 — Capture a clip and replay slowly (optional)

- **Actors and trigger:** Operator; button or capture command
- **Preconditions:** Heart mode, microphone, active live audio, free bounded clip RAM.
- **Postconditions:** One raw volatile clip is replayed at selected speed then returns to live.
- **Normal flow:** Assign clip ID; turn activity LED on; capture raw before filtering/gain while live continues; at configured capacity finalize clip; replay through selected filter and pitch-preserving speed stage; end returns live.
- **Alternatives/errors:** Button during capture/replay cancels and returns live. Stop ends audio. Clip/replay is optional; session mode/source changes are rejected. Allocation failure rejects capture without interrupting live.

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
- **Alternatives/errors:** Poor quality/clipping/gaps prevent accepted windows. Stop before 15 s cancels. Context changes are rejected with a normal fault and preserve the session. Essential audio fault latches DA. Invalid coverage produces no numeric BPM; a separately validated error report may be sent after listening stops. Do not count S1/S2 as two beats.

## UC-06 — Deliver a completed result or invalid-result error

- **Actors and trigger:** Operator and FHIR/time services; completed result, Stop listening.
- **Preconditions:** Idle, frozen completed microphone-session context, configured patient/server/time/trust. Lung/test/cancelled paths are excluded from production sending.
- **Postconditions:** One attempt; verified delivery or terminal failed/unverified outcome.
- **Normal flow:** Grant exclusive network lease; serialize numeric R4 Observation for valid BPM or separately validated missing-value/error representation for invalid BPM; verify TLS/name/time; PUT stable ID; read back matching content; release lease.
- **Alternatives/errors:** Unconfigured Wi-Fi causes no send/error. Configured connection failure permits offline listening and latches a manually cleared normal fault. Timeout/4xx/5xx/readback failure aborts without retry queue. Start during analysis/sending is Busy with activity indication and cannot cancel or queue a new session. Timeout after server commit remains Unverified.

## UC-07 — Operate in lung mode

- **Actors and trigger:** Operator; select Lung
- **Preconditions:** Audio ready.
- **Postconditions:** Raw live at 1×; no BPM, clip replay or FHIR.
- **Normal flow:** Controller accepts mode changes only outside a session; invalidates heart estimate; forces Raw and 1×; displays Lung; keeps volume available; context remains fixed during a session.
- **Alternatives/errors:** BPM/replay/send commands rejected with reason. Previously completed heart result is retained only as historical context and cannot be sent while in Lung.

## UC-08 — Cancel, stop or recover from faults

- **Actors and trigger:** Operator or MON; cancel/stop/failure
- **Preconditions:** Any active operation or muted Fault.
- **Postconditions:** Buffers and jobs have a documented outcome; essential failure stays muted until recovery succeeds.
- **Normal flow:** Cancel optional clip operations independently. Stop mutes listening; an active Heart measurement cancels without sending before 15 s and finalizes at or after 15 s subject to quality and coverage checks. Stop does not cancel analysis or sending; their Busy rule remains in force; MON reports essential fault; controller releases resources; Device Alarm stays muted/latched until full restart and startup checks succeed. Normal faults have a separate acknowledgement action.
- **Alternatives/errors:** UI or SD failure preserves microphone listening. Resource/analysis overflow resets analysis validity. Button acknowledgement cannot clear DA; no old result relabelled as new.

## UC-09 — Configure and inspect the prototype

- **Actors and trigger:** Operator/researcher; setup or diagnostics
- **Preconditions:** Idle for network/time configuration; authorized physical/serial access.
- **Postconditions:** Validated configuration and capability/measurement evidence available without secrets in logs.
- **Normal flow:** Calibrate touch and volume; assign patient and named listening point; set server/trust/auth/time; inspect build/carrier/config IDs, timing/resource/error counters; select approved research parameters.
- **Alternatives/errors:** Reject invalid values atomically. Configuration changes cannot mutate a frozen result. Diagnostic test sources stay visibly marked and excluded from patient delivery.

## Current MVP control workflow

See [11 October decisions](../planning/mvp-decisions-2026-10-11.md) for the confirmed Busy, acknowledgement, DA, context and cancellation transitions. Capture/replay and display/touch are optional; their historical proposal is not the MVP button mapping. Normal Start/Stop and separate acknowledgement remain distinct; no undocumented long press is assumed. Physical filter transitions and volume affect the listening path independently of frozen analysis settings.
