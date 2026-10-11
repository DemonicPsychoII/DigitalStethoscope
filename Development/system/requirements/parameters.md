# Parameter and acceptance register

Current owner decisions and numeric proposals: [11 October MVP decisions](../planning/mvp-decisions-2026-10-11.md). Older source snapshots and evaluation behavior remain historical evidence.

Open values are review candidates, not approved acceptance thresholds. Requirements that depend on them can guide interfaces but their final acceptance is blocked until the values are agreed. Keep parameter IDs in implementation configuration and evidence.

| ID | Parameter | Value / candidate | Status and basis | Owners |
|---|---|---|---|---|
| P01 | Sample rate / block | 16,000 Hz / 128 frames; 8 ms | Board baseline S03/S04/S07 | AUD |
| P02 | Execution budget | ≤4 ms critical-path execution per block with 2× planning margin; deadline 8 ms | Board target; needs measured load evidence | AUD,LIS,MON |
| P03 | Live latency | <30 ms target; <10 ms stretch goal | S03/S06 target; DAC filter delay included | AUD,LIS |
| P04 | Optional clip format / duration | Proposed raw signed 32-bit mono, 5 s; 320,000 bytes | Open: S03 proposal differs from filtered 16-bit bring-up | REC |
| P05 | BPM window / update / session | Proposed 8 s / 1 s / recommended 30 s; Stop <15 s cancels | 11 October proposal; manual Stop ≥15 s finalizes only if validity criteria pass | BPM |
| P06 | BPM range / error | Candidate 30–200 BPM; max(5 BPM, 10% reference) absolute error | 11 October proposal: MAE ≤5 BPM and ≥95% valid sessions within tolerance; no clinical conformity claim | BPM |
| P07 | BPM validity / coverage | Proposed calibrated quality gate, ≥3 valid windows and ≥80% union temporal coverage | Quality threshold derived on development corpus only; session availability ≥95% clean held-out runs proposed | BPM |
| P08 | Filter parameters | Candidate Murmur 40–800 Hz; BPM 25–150 Hz; 2nd-order HP + LP | Open: literature derivation/evaluation required; S07 candidates | LIS,BPM |
| P09 | Transition smoothing | Candidate 20 ms exponential crossfade / gain smoothing | Open: perceptual/transient bounds require evaluation | LIS |
| P10 | Input / UI response | Candidate debounce 30 ms; effective setting ≤100 ms; status ≤500 ms | Derived open budgets; shared SPI must be bounded | INP,CTL,UI |
| P11 | Queue / pool capacities | Candidate 16 control events, 4 analysis blocks, 1 pending network job; 4 RX + 4 TX DMA blocks | Derived open sizing; measure resource pressure | AUD,CTL,NET |
| P12 | Fault response / recovery | Proposed mute within 1 audio block after detection; DA latched until full restart | Restart-only DA recovery confirmed 11 October; detection/mute budget proposed | MON,AUD |
| P13 | Network timeout / handoff | Candidate 10 s connect/TLS; 10 s request/readback; ≤1 s cancellation/lease release | Open: platform cancellation behavior must be proven | NET,CTL |
| P14 | Replay fidelity | Candidate duration error ≤1 output block; pitch change <1% on tones | Open: WSOLA transient and perceptual acceptance corpus needed | REC |
| P15 | Resource margin | 16 MB flash / 8 MB PSRAM; DMA internal; candidate ≥25% free measured stack/internal-heap headroom | Board capacity, derived open margin; no inherited ≤80% flash rule | MON |
| P16 | Amplifier / acoustic output | External amplifier required; gain/model and maximum output level TBD | Open hardware design and target measurement | HW |
| P17 | Fixture format | Candidate mono PCM WAV 16/32-bit at 16 kHz; reject unsupported rates (no implicit resampling) | Derived open scope; signed alignment explicitly specified | STO |
| P18 | Patient / point / FHIR / time | FHIR R4; local HAPI; patient reference; named point list; approved clock source and skew | Partly board-fixed; deployment/profile/clock choices open | CTL,NET |
| P19 | Network exclusion | No Wi-Fi connection/time-sync/TLS/HTTP work in Live/Capture/Replay or active measurement | Saved S04 decision; lease mechanism derived | NET,CTL |
| P20 | Startup mode | Proposed Ready/Idle at zero gain; explicit Start listening | Open: S03 also shows ready/live; agree UI transition | CTL,AUD |

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
