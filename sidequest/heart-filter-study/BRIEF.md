# Brief: heart filter study (TICKET-189), first simulation

You lead this study on your own for Nico. Nico is not available; do not ask him questions. Where a
decision is open, choose the sensible option, record it in `STATE.md` with the reason, and carry on.

## Time limit and resumability (read first)

- Started: 2026-11-23 01:30 (+01:00). **Hard stop: 06:28 (+01:00).** The parent thread cancels
  you at that moment without warning.
- **At 05:58 at the latest, stop new work and wrap up:** bring `STATE.md` and `FINDINGS.md` up to
  date, and publish whatever result exists (marked as interim) if the page is not yet published.
- Keep the study resumable at every moment, not only at the end:
  - `STATE.md` (this folder) is the single source of truth: phase checklist with status, decisions
    with reasons, artifacts with paths, delegated tasks with their task IDs and status, open
    problems, and the exact next steps. Update it after every milestone and before every long run.
  - `FINDINGS.md`: results so far, each with its evidence (file, numbers) and its confidence.
  - Scripts are idempotent and cache intermediate results to files, so a rerun skips finished work.
  - A later session must be able to continue from `STATE.md` alone.
- Check the clock (`date`) regularly.

## Who does what

- **All software is written by Claude Opus 5.5 on high effort**, never by you: delegate every
  piece of code (simulation, filters, BPM estimator, evaluation, page build) with the T3
  `delegate_task` tool, `target: {providerInstanceId: "claudeAgent", model: "claude-opus-5-5",
  options: {effort: "high"}}`, `mode: "async"` or `"wait"` as fits. Give each delegate a
  self-contained brief (it gets no history) with paths, interfaces and acceptance checks. Run
  independent pieces in parallel. You may run scripts, read code and results, and review.
  Record every delegate's task ID in `STATE.md`.
- You plan, decide, review the delegates' work critically, interpret results and write the read.

## Goal

Choose the listening and BPM filters of the digital stethoscope by simulation, as close to the
real device as possible, and present the result as a scientific read on Pages.

Nico's decisions (23 November 2026), binding:

1. **Data:** Nico's own heart recordings in `recordings/` (see `README.md` for the table): rest-1,
   rest-2, elevated-1 (clean), elevated-2 and elevated-3 (overload on the heartbeats: the real
   chain reaches digital full scale at high post-exercise heart rates; keep them as realistic
   overload cases). Raw INMP441, 16 kHz, 24-bit, recorded through the real chest-piece (membrane
   side), tube and microphone with the capture firmware. The first ~2 s contain the microphone
   start-up transient; discard them.
2. **Listening filter ("Murmur" position, and Raw as reference):** the loudest audible result that
   is not distorted and does not carry too much other sound (judged subjectively by Nico). Prepare
   **listening samples** Nico can judge: the same excerpts through each shortlisted candidate,
   with the device's real gain staging and clipping at the output, plus Raw. Make them easy to play
   and compare (on the page and as WAV files).
3. **BPM filter:** the filter giving the **highest accuracy of an on-ESP32-S3 BPM estimate over an
   8 s rolling window held in PSRAM**. The estimator itself must be realistic for the ESP32-S3
   (memory, CPU at 16 kHz, fixed or float arithmetic as the firmware would use, causal processing,
   window update rate as the design says). The firmware design also feeds each listening filter
   into BPM detection (TICKET-189): test that too.
4. **Try all filter variants** worth trying: types (Butterworth, Bessel, Chebyshev, elliptic, FIR
   where affordable), orders, band edges, and simple non-linear steps if they help (for example
   envelope or clipping handling), within the device's real-time and memory limits.
5. **As close to the real device as possible:** take sample rate, block size, data format, filter
   placement, volume stage, DAC output and threads from the firmware and design documents.
6. **Everything lives in this folder** (`C:/Users/nicop/Desktop/heart-filter-study/`). Create
   subfolders as needed.

## Sources to read

Repository (read-only; do not commit, push, change it, or touch hardware/flash anything):
`C:/Users/nicop/.t3/worktrees/DigitalStethoscope/feature-audio-chain-swe-2447cecce9041295/`

- `AGENTS.md`: project rules, especially *Thesis sources* (every claim sourced or marked as a
  project decision or own measurement).
- Firmware: `Development/system/coding/app/` (L1_I2S, L2_AUDIO, `L1_services/L1_FILTER` is still
  empty), board config, Kconfig/prj files.
- Design: `Development/system/architecture/AUDIO/README.md`,
  `Development/system/design/AUDIO/interfaces-and-behavior.md`,
  `Development/system/design/system/interfaces-and-behavior.md` (BPM row),
  `Development/system/design/system/parameters.md` (P08 candidate bands: Murmur 40–800 Hz,
  BPM 25–150 Hz, 2nd-order HP + LP), `Development/system/design/system/shared-filter-signal-flow.puml`,
  `Development/system/planning/mvp-decisions-2026-11-13-delivery-and-filters.md`,
  `Development/system/requirements/system-requirements.md` (REQ-03 and the BPM requirements),
  `preThesis/06-bringup-zephyr/EVAL-GUIDE.md` (acceptance targets: live latency < 30 ms,
  BPM MAE ≤ 5 BPM with ≥ 90 % valid windows, ≥ 25 % stack headroom).
- Thesis material: `thesis-material/08-evaluation/01-fragen-kriterien.md`,
  `03-filtervergleich-statistik.md`, `04-bpm-validierung.md`, `06-akustische-kette.md`,
  `thesis-material/03-grundlagen-technisch/04-dsp-filter.md`, `thesis-material/quellen.md`.
- Acoustic chain measurement: `Development/system/testing/AUDIO/chain-measurement/` (README,
  `microphone_model.py`) and the session `C:/Users/nicop/audio-chain-measurements/2026-11-22/`
  (`notes.md`, `analysis/`). Two independent reviews found: B/A and C/A are **not valid below
  about 400 Hz** (setup A had its own 220 Hz dip from the cushion resting on the board edge) and B
  is contaminated above about 5.5 kHz; the membrane-vs-bell comparison C/B is the most reliable
  quantity; distortion figures are upper bounds only. Nico's recordings already contain the real
  chest-piece and microphone, so do not apply a chest-piece model to them.

## Known limitations to state, not hide

- One person, five recordings, one session; membrane side only.
- **No independent heart-rate reference** (no ECG, watch or oximeter). Derive reference beat times
  offline with the best non-causal method you can justify, cross-check them by more than one
  method, and state that this reference is weaker than ECG.
- Overload at high heart rates is a property of the real chain.
- Subjective listening judgement is Nico's and is still pending; the samples prepare it.

## The read on Pages

- Use the `publish-page` skill (`C:/Users/nicop/GlobalAgentContext/skills/universal/publish-page/SKILL.md`)
  to publish. Homelab dark theme, nice layout, readable on a phone.
- A scientific read **without jargon**: question, method, results, what it means, limitations,
  next steps. Explain every unavoidable technical term in plain words on first use. Clear figures
  with axes in Hz/kHz (log spacing, Hz/kHz labels, never "log"). Embedded listening samples.
- Back factual claims with sources; label own measurements with date and firmware; mark project
  decisions and unverified points as such.
- **Before publishing, have the read verified by the council** (`C:/Users/nicop/GlobalAgentContext/skills/universal/council/SKILL.md`):
  correctness of claims, numbers and method, and plainness of language. Fix
  every valid finding; record the council's verdict and what you changed in `STATE.md`. If time
  runs short, publish as interim with the open council points listed on the page.
- Below the content: `Published by Claude-Fable-5.2 on behalf of Nico running in T3 Code through Claude Code.`

## Report back

Final message: page URL, the recommended listening and BPM filters with their key numbers, the
council verdict, open points, and the path to `STATE.md`.
