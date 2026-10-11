# System requirements

**Status: source-backed draft.** Exact numeric acceptance is supplied by the linked component requirements and [parameter register](parameters.md). Source backing does not constitute approval.

| ID | Use cases | Sources | Requirement | Verification |
|---|---|---|---|---|
| SR-01 | UC-01,UC-08 | S03,S04 | The system shall initialize output at zero gain and silence, report capabilities, and prevent listening when essential audio is unavailable. | VT-01,VT-09 |
| SR-02 | UC-02 | S03,S04 | The system shall provide continuous original-rate live audio with selectable Raw/Murmur/BPM listening filters, smoothed volume and bounded latency/resources. | VT-02,VT-03 |
| SR-03 | UC-02,UC-09 | S03,S04 | The system shall serialize operator commands through one state owner and expose the effective state consistently across physical, touch and shell controls. | VT-04 |
| SR-04 | UC-03 | S03 | The system shall capture a bounded volatile raw clip in heart mode, replay it at 1×/0.75×/0.5× with approximate pitch preservation, and return to live on completion or cancellation. | VT-05 |
| SR-05 | UC-05 | S03,S04 | The system shall derive heart-rate results from an independent original-rate analysis path, reject invalid windows, and freeze one result per completed session including context and validity. | VT-06 |
| SR-06 | UC-06 | S02,S03,S04 | The system shall attempt one initial delivery of each eligible completed microphone result using FHIR R4 over verified TLS only while listening is stopped, and permit explicit retries with the same identity. | VT-07,VT-08 |
| SR-07 | UC-07 | S03,S05 | The system shall restrict lung mode to Raw live listening at 1× and reject BPM, clip replay and health-data sending. | VT-04,VT-06,VT-07 |
| SR-08 | UC-04 | S03,S04,S05 | The system shall run identical licensed test recordings through the same DSP on host/device and preserve test provenance so no synthetic or fixture result becomes a patient transmission. | VT-10,VT-07 |
| SR-09 | UC-01,UC-08 | S03,S04 | The system shall isolate optional-component failures, mute essential audio faults, cancel stale operations and report bounded recovery outcomes. | VT-01,VT-09 |
| SR-10 | UC-09 | S03,S04 | The system shall retain build/configuration, timing/resource and anomaly evidence sufficient to reproduce evaluation without exposing credentials or claiming unperformed physical verification. | VT-11 |
| SR-11 | UC-04,UC-09 | S01,S03,S07 | The system shall use the selected hardware interfaces and serialized shared SPI bus with bounded fixture/display transfers and no filesystem operation in the audio deadline path. | VT-12,VT-13 |

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
