# NET — FHIR/TLS delivery

Current owner decisions and numeric proposals: [11 October MVP decisions](../../planning/mvp-decisions-2026-10-11.md). Older source snapshots and evaluation behavior remain historical evidence.

**Status: current owner behavior decisions with proposed numeric acceptance.** “Source-backed” identifies origin, not formal approval. Acceptance with open parameters remains conditional. Interface names are proposed contracts, not existing APIs.

## NET-001

The network worker shall perform connection, time sync, TLS and HTTP work only under an Idle network lease, with no settings/audio lock held over I/O.

- **Derivation:** UC-06,UC-09 → SR-06; sources S04.
- **Status:** Source-backed + derived lease.
- **Parameters:** P19.
- **Verification:** VT-08.
- **Acceptance:** Lease/state trace for connect/send/retry/start races; no concurrent Live/Capture/Replay/measurement.

## NET-002

The production network worker shall reject incomplete, cancelled, Lung-mode, synthetic or fixture results and invalid numeric BPM. Invalid completed microphone measurements may use a separately validated error-report job with no numeric BPM. Configured patient/server/time/trust prerequisites apply to both paths. Diagnostic synthetic-patient transport tests require an explicit isolated harness, not a production guard bypass.

- **Derivation:** UC-06 → SR-06,SR-08; sources S03,S04.
- **Status:** Source-backed.
- **Parameters:** P18.
- **Verification:** VT-07.
- **Acceptance:** Negative matrix emits zero numeric-BPM requests for invalid results and zero production requests for cancelled/test/Lung sources; separately validate invalid-result error reporting. Provenance checked again in worker, not only UI.

## NET-003

FHIR serialization shall encode a final R4 heart-rate Observation with LOINC 8867-4, vital-signs category, UCUM /min, frozen subject/value and effective measurement interval/time.

- **Derivation:** UC-06 → SR-06; sources S03.
- **Status:** Source-backed.
- **Parameters:** P18.
- **Verification:** VT-07.
- **Acceptance:** FHIR validator and parsed JSON assertions; decimal precision and interval/time mapping agreed; do not use send time as measurement time.

## NET-004

The MVP delivery service shall schedule at most one attempt per completed result/error job with a stable Observation ID and frozen payload; failed/unverified delivery is terminal and has no automatic or manual retry queue.

- **Derivation:** UC-06 → SR-06; sources S02,S03.
- **Status:** Source-backed + derived idempotent PUT.
- **Parameters:** —.
- **Verification:** VT-07,VT-08.
- **Acceptance:** Timeout after server commit remains Unverified; no retry or new resource is created. Retain redacted outcome evidence, not a sendable failed payload; no mutable patient/value.

## NET-005

HTTPS shall verify certificate chain, server hostname and validity time against approved trust configuration and shall refuse insecure/plain-HTTP fallback.

- **Derivation:** UC-06 → SR-06; sources S03,S06.
- **Status:** Source-backed.
- **Parameters:** P18.
- **Verification:** VT-08.
- **Acceptance:** Wrong CA/name/expired certificate/untrusted clock are rejected; no verification-disable path.

## NET-006

Delivery shall distinguish request accepted from matching server readback, preserve visible failed/unverified outcomes, and bound all connection/request/cancellation waits.

- **Derivation:** UC-06 → SR-06,SR-09; sources S03.
- **Status:** Source-backed.
- **Parameters:** P13.
- **Verification:** VT-07,VT-08.
- **Acceptance:** 2xx/4xx/5xx/partial response/timeout/readback mismatch tests; Sent only after matched stored content.

## NET-007

Network configuration shall keep credentials outside source/evidence/logs, validate lengths/encoding atomically, and freeze the patient/result context before queuing a job.

- **Derivation:** UC-06,UC-09 → SR-06,SR-10; sources S03,S06.
- **Status:** Derived privacy constraint.
- **Parameters:** P18.
- **Verification:** VT-08,VT-11.
- **Acceptance:** Malformed fields rejected; redacted diagnostic output; frozen result unchanged by later config edits.

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
