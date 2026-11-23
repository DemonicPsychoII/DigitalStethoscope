# Static weight test, 23 November 2026

Question from the supervisor meeting with Prof. Zeuke on 23 November 2026: does a steady push on
the chest piece build up a pressure in the closed air volume that drives the INMP441 to full scale,
or does only the change of pressure (placing, lifting, breathing, movement) overload it?

## Set-up

- Littmann Classic II chest piece, membrane side open, lying on the desk; tube to the printed
  microphone adapter on the ESP32-S3 evaluation carrier.
- Weight: a filled chewing-gum jar (Wrigley's Extra), put down on the chest piece by hand. Its mass
  was not weighed.
- Adapters:
  - **v10 sealed:** the old v10 adapter with its old seal and no vent hole.
  - **v14 vent open:** the printed v14 adapter with the 0.8 × 0.7 mm slot vent and the TPU seal.
    The slot could not be taped shut, so there is no sealed v14 take.
- Capture firmware of `Development/system/testing/AUDIO/chain-measurement/` with the
  `capture weight` command: 24 s raw capture, 16 kHz, 24 bit, with cues on the RGB status light:
  blue 0–1 s stay still, green 1–6 s put the weight down, red 6–16 s hands off, yellow 16–21 s
  lift, off 21–24 s. The firmware was built from integration b1c7fbb plus the uncommitted
  measurement tools; `run.json` records only b1c7fbb, because untracked files do not mark the
  revision as dirty.
- Takes (all by Nico, NGLegion, COM4): v10 sealed takes 1–3, one v10 take without weight
  (`v10-sealed-baseline`), v14 vent open takes 1–3. `short-cues-take-1` is a first attempt with
  2 s cue phases that were too short to follow; it is not evaluated.

## Results

Fractions of digital full scale. Phases as cued: placing 1–6.5 s, resting 7–16 s, lifting 16–21 s.
Raw numbers: [analysis/phases.txt](analysis/phases.txt) and
[analysis/overload-duration.txt](analysis/overload-duration.txt), produced by the two scripts in
[analysis/](analysis/).

| Take | Placing: samples at full scale | Resting: peak | Resting: samples at full scale | Lifting: samples at full scale |
| --- | --- | --- | --- | --- |
| v10 sealed 1 | 0.09 % | 0.13 | 0 % | 0.01 % |
| v10 sealed 2 | 0.26 % | 0.05 | 0 % | 0 % (peak 0.97) |
| v10 sealed 3 | 0.05 % | 0.04 | 0 % | 0.28 % |
| v14 vent open 1 | 0.21 % | 0.05 | 0 % | 0.01 % |
| v14 vent open 2 | 0.04 % | 0.17 | 0 % | 0 % (peak 1.00) |
| v14 vent open 3 | 0.07 % | 0.26 | 0 % | 0 % (peak 0.99) |

Without weight the signal stays at about 0.002 RMS. While the weight rests, it is 0.009–0.028 RMS,
mostly below 20 Hz; above 20 Hz it is 0.003–0.007 RMS against about 0.002 without weight.

Time the signal stays above half scale when lifting, and time until it falls below 0.05 afterwards:

| Adapter | Above half scale | Below 0.05 after |
| --- | --- | --- |
| v10 sealed, takes 1–3 | 190–760 ms | 320–450 ms |
| v14 vent open, takes 1–3 | 105–170 ms | 90–100 ms |

When placing, the overload lasts as long as the hand moves (0.65–2 s) and ends within 10–20 ms
after the last loud sample with both adapters.

## What this confirms and denies in our argument

| Statement | Verdict | Evidence |
| --- | --- | --- |
| A steady push builds up a pressure in the closed volume that keeps the microphone at full scale | **Denied** | No sample at full scale during 9 s of steady load in 6 of 6 takes, even with the sealed v10 |
| The overload comes from pressure changes: placing, lifting, and by extension breathing and movement | **Supported** | Every take reaches full scale while placing (6 of 6) and comes close or reaches it while lifting (6 of 6) |
| The microphone does not pass a static pressure, so the signal returns to zero under a steady load | **Supported, mechanism not measured** | While resting, the peak stays at 0.26 or below and most of the remaining level lies below 20 Hz; the cut-off frequency of the microphone was not measured here |
| The vent shortens the overload after a fast pressure release | **Indication only** | v14 vent open recovers 3–4 times faster after lifting than v10 sealed, but the adapters also differ in shape and seal, and there are 3 takes each |
| The vent prevents the overload when placing the chest piece | **Not shown** | Both adapters saturate for as long as the hand moves; the fractions overlap (0.04–0.26 %) |

Earlier observations that fit: on 16 November 2026 widening the vent from 0.5 to 0.8 mm brought
the drop-outs at rest and when slightly tilted to 0 % (recordings 11–16 in
[DigitalStethoscope-mic-samples-2026-11-15](../DigitalStethoscope-mic-samples-2026-11-15/)).
Breathing and tremor are slow pressure changes that a vent can leak away. The heart filter study
reached full scale on every heartbeat at high post-exercise heart rates
([heart-filter-study/README.md](../heart-filter-study/README.md)); these are pressure changes too,
and this test does not say whether a vent would help there.

## Limitations

- One weight of unknown mass; weigh the jar and add the mass before quoting a pressure.
- Placing and lifting by hand: the speed differs between takes, so the placing and lifting numbers
  compare the order of magnitude, not the adapters.
- Disturbances: the take without weight has a bump with peak 0.32 in 7–16 s; v10 take 2 peaks at
  0.40 and v14 take 3 reaches full scale (0.18 %) after the lift, 21–24 s. Neither falls into a
  resting window of a weighted take.
- The vent effect is confounded with the adapter: a v14 printed without the slot would separate
  them.
