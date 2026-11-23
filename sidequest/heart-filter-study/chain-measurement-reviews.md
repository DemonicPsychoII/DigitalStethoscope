# Chain measurement of 22 November 2026: setup, results and the two independent reviews

Condensed from the measurement thread by Claude Opus 5.5 on 23 November 2026. Full review texts are in
the T3 threads "Fable review: audio chain session" and "Neon review: audio chain session" (both
23 November 2026, read-only reviews; scratch scripts of the Fable review in `C:/tmp/review-scratch`).

## Setup (own measurement, 22 November 2026)

- Source: Beyerdynamic DT 770 PRO (250 Ω) on an LD Systems HPA 4 headphone amplifier, played from
  Talos (Realtek USB audio, WASAPI exclusive, Windows volume 80, HPA 4 channel 3 at about 180°),
  started over SSH while NGLegion recorded the board.
- Capture: the throwaway capture firmware (`Development/system/testing/AUDIO/chain-measurement/capture-firmware/`),
  raw INMP441 left slot, 16 kHz, 24 bit, read out at 921,600 baud. The same firmware recorded
  Nico's heart sounds on 23 November.
- Stimulus: exponential sine sweep 20 Hz to 8 kHz, 4 sweeps of 5 s, 3 s apart, Farina deconvolution,
  clock-drift correction (the ESP32 ran about 34 ppm fast), at −12 and −24 dBFS, 4 re-seats per setup.
- Setups: A = INMP441 under the ear cup; B = chest-piece membrane under the cup, INMP441 at the end
  of the tube; C = bell. membrane = B/A, bell = C/A. No reference microphone; coupling through air.
  Tube gap under the cushion unsealed; no leakage control.
- Code and README: `Development/system/testing/AUDIO/chain-measurement/` in the repository
  worktree; data and plots: `C:/Users/nicop/audio-chain-measurements/2026-11-22/` (`notes.md`,
  `analysis/`, `photos/`).

## Results that hold (both reviews agree)

- Processing verified: recomputation matched the CSVs within 0.0005 dB; a simulated known system was
  recovered within 0.1 dB from 20 Hz to 7.8 kHz; −12 and −24 dBFS agree within 0.2–0.4 dB (linear).
- Signal-to-noise at −12 dBFS about 27–68 dB from 25 Hz to about 6 kHz; −24 dBFS only as a linearity check.
- Tube resonance comb at about 261, 572, 940, 1313, 1705 Hz, identical within ±2 Hz for membrane and
  bell (consistent with a tube of about 44–45 cm; inference).
- Membrane vs bell (C/B, independent of setup A): nearly the same below 1 kHz in air; membrane
  +9 to +10 dB around 1.7–2.5 kHz; bell 3.5–13 dB above the membrane above 4.5 kHz.
- Steep drop of both sides above about 5 kHz is acoustic, not processing.

## What is not valid, and why

- **B/A and C/A below about 400 Hz:** setup A had its own dip of about 13 dB at 220 Hz from the ear
  cushion resting on the board edge; it vanishes with the cup lifted (Neon checked the placement
  runs). Dividing by A adds about 10–13 dB to the 250 Hz peak of both ratios.
- **B above about 5.5 kHz:** sound reaching the microphone through the air arrives 0.5–1 ms before
  the tube signal (Neon).
- **Seat spread:** bell seats 3 and 4 (and B seats 3 and 4) form a separate block after a 68-minute
  pause, about 2 dB lower broadband and up to 6 dB below 315 Hz; A was not repeated at the end.
- **Distortion figures** are noise-limited upper bounds only.
- Smaller processing points (spread band, unpaired linearity, magnitude averaging, resampling at
  exactly 8 kHz) change the −12 dBFS results by less than 0.1 dB between 25 Hz and 7.5 kHz.

## Planned second session (not done yet)

Rebuilt setup A without its own dip, A before and after each block, sealed tube, pinched-tube and
taped-face leakage controls, silent capture for a noise mask, sweep 10 Hz to 7.5 kHz, processing fixes.
