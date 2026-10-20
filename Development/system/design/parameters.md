# Design parameters (internal)

**Internal design values, not requirements.** They are left to implementation and design ([14 October decisions](../planning/mvp-decisions-2026-10-14.md)); acceptance is defined only by the [system requirements](../requirements/system-requirements.md). Values are proposals until measured. Keep parameter IDs in implementation configuration and evidence. P04 (clip format), P14 (replay fidelity) and P16 (amplifier) were removed on 14 October 2026.

| ID | Parameter | Value / candidate | Status and basis | Owners |
|---|---|---|---|---|
| P01 | Sample rate / block | 16,000 Hz / 128 frames; 8 ms | Board baseline S03/S04/S07 | AUD |
| P02 | Execution budget | ≤4 ms critical-path execution per block with 2× planning margin; deadline 8 ms | Board target; needs measured load evidence | AUD,LIS,MON |
| P03 | Live latency | <30 ms design target; <10 ms stretch goal | Not measured: no two-channel setup; checked by ear (REQ-05) | AUD,LIS |
| P05 | BPM window / update / session | Proposed 8 s / 1 s / recommended 30 s; Stop <15 s cancels | 11 October proposal; manual Stop ≥15 s finalizes only if validity criteria pass | BPM |
| P06 | BPM range / error | Candidate 30–200 BPM; acceptance ±5 BPM or ±10 % against pulse oximeter/smartwatch (REQ-06) | Decided 14 October; recordings and reference for host tests decided during the Wi-Fi/FHIR phase; no clinical conformity claim | BPM |
| P07 | BPM validity / coverage | Proposed ≥3 valid windows and ≥80% union temporal coverage; no fixed numeric quality threshold | 14 October: quality threshold removed; window/coverage values are design proposals | BPM |
| P08 | Filter parameters | Candidate Murmur 40–800 Hz; BPM 25–150 Hz; 2nd-order HP + LP | Chosen after the device works (filter study TICKET-189, including listening filters as BPM input) | LIS,BPM |
| P09 | Transition smoothing | Candidate 20 ms exponential crossfade / gain smoothing | Open: perceptual/transient bounds require evaluation | LIS |
| P10 | Input / UI response | Candidate debounce 30 ms; effective setting ≤100 ms; status ≤500 ms | Derived open budgets; shared SPI must be bounded | INP,CTL,UI |
| P11 | Queue / pool capacities | Candidate 16 control events, 4 analysis blocks, 1 pending network job; 4 RX + 4 TX DMA blocks | Derived open sizing; measure resource pressure | AUD,CTL,NET |
| P12 | Fault response / recovery | Wi-Fi-only faults preserve audio; other faults halt; clear/restart per feedback catalogue | Decided 19 October; detection and mute latency still require measurement | MON,AUD,CTL |
| P13 | Delivery timeout / retry | HTTP delivery: 1 attempt + 3 retries about 2 s apart, all within 10 s; connect/TLS timeout and cancellation latency still unverified | Delivery retry decided 14 October; Wi-Fi budgets are separate in P23 | NET,CTL |
| P15 | Resource margin | 16 MB flash / 8 MB PSRAM; DMA internal; candidate ≥25% free measured stack/internal-heap headroom | Board capacity, derived open margin; no inherited ≤80% flash rule | MON |
| P17 | Test recording format | Host-side mono PCM WAV; resampling of 2–4 kHz datasets to be decided | Decided during the Wi-Fi/FHIR phase (14 October) | BPM |
| P18 | Device / FHIR / time | FHIR R4; local HAPI over HTTPS with lab CA; Observation references the server-assigned Device id (stored in flash), and the patient only when the server has linked one; `effectiveDateTime` = interval end; approved clock source and skew | Decided 12 October, Device/patient changed 15 and 16 October; clock skew open | CTL,NET |
| P19 | Network exclusion | No active setup/reconnect/time-sync/TLS/HTTP jobs during listening/measurement; retain existing station association; Start cancels setup before audio | Decided 19 October; radio interference and safe teardown require target evidence | NET,CTL |
| P20 | Startup mode | Idle at zero gain; explicit Start listening | Decided (REQ-01) | CTL,AUD |
| P21 | Hotspot Wi-Fi setup | Scan/cache then open AP + portal; open hotspot; 2 s hold in Idle; 5 min inactivity, paused during actions; selection/input/Rescan reset it, polling does not; candidate 1 client | Decided 18/19 October; client/cache capacity not fixed | INP,CTL,UI,NET |
| P22 | Feedback timing and brightness | Codes/flashes: 2 Hz, 250 ms on/off (50 % on); 2 s group pause, at most 6 blinks per context; long flash 1 s; slow blink 0.5 Hz, 1 s on/off; breathing 3 s; input-rejected dimming by at least 50 % for 250 ms; Idle dim candidate 20 %; startup lamp test at least 1 s. Brightness: every pattern must be seen at 1 m and the error state at 4 m, at 100–1500 lx ambient light, inside a 30° viewing cone | Adopted catalogue 19 October. Rates from IEC 60073 (normal 1.4–2.8 Hz, slow 0.4–0.8 Hz, pulse:pause about 1:1); visibility from the IEC 60601-1-8 6.3.2.2 test conditions; see [LED indication standards](led-indication-standards.md). Documented deviations; no conformity claim. Visibility assumed adequate; no device check planned | INP,UI |
| P23 | Wi-Fi retry / exit | Boot/reconnect/scan 4 attempts total, 5 s between failures; portal join 1; save 2; AP start manual; success/save warning 10 s, Cancel/timeout notice then teardown | Decided 18/19 October; candidate connect 15 s, scan 10 s, link check 2 min, close notice 2 s, scan list 16; 200 ms event-check slices are not total teardown bounds; target verification remains open | NET,CTL |

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.

Updated by Claude-Opus-5.5 on behalf of Nico running in T3 Code through Claude Code.
