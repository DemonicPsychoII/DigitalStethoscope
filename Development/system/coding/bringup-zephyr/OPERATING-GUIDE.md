# Evaluation controls and serial shell

## Functions and controls

- 16 kHz, stereo 32-bit I2S; microphone left channel is duplicated to DAC L/R.
  128-frame blocks (8 ms), two silent TX priming blocks (16 ms), DMA in internal SRAM.
- Listening filters: Raw, initial Murmur candidate (40–800 Hz), initial BPM
  candidate (25–150 Hz). Second-order Butterworth HP + LP sections; 20 ms
  exponential crossfades. **These cutoffs are engineering candidates**, pending
  literature justification and evaluation, not established optimal filters.
- Independent analysis filter, 8-second rectified-envelope autocorrelation window,
  one update per second, provisional 30–200 BPM range and quality gating.
  The quality percentage is a periodicity score, not clinical confidence.
- Potentiometer: volume, 0–8× gain with a squared control curve, smoothing and
  saturation. Start at minimum. Brightness is a separate setting.
- Filter switch: positions 1/2/3 select Raw/Murmur/BPM. Touch or serial selection
  remains active until the next physical switch transition.
- Speed switch: positions 1/2/3 select 1.00×/0.75×/0.50× replay, with the same
  last-transition-wins rule. With no switch fitted all contacts read open and
  touch/serial stay in control.
- SD card: mounted read/write at `/SD:` when a FAT/exFAT card is inserted before
  boot. There is no card-detect line; after inserting later use `fs mount fat /SD:`.
  The firmware never formats a card. Browse with `fs ls /SD:`.
- Button: begin a volatile clip, or stop capture/replay and return to live.
  LED indicates active capture/replay. Default clip capacity: **5 seconds**.
- Touch dashboard: filter/speed, capture/replay, live/heart-lung, point/brightness.
  Positions are also selectable through the serial shell, independently of touch
  calibration. `point` is an operator-entered index 1–5 on screen, not an inferred
  anatomical location; record its anatomical meaning in each evaluation run.
- Replay: bounded recorded clip at 1× / 0.75× / 0.5× using waveform-similarity
  overlap-add (WSOLA), preserving pitch approximately. Ends at live playback.
  BPM always uses newly captured samples at the original sampling rate.
- Lung mode: live Raw listening, no BPM or replay, FHIR send refused.
- Diagnostics mode retains button/LED, potentiometer/backlight and colour tests.
- Sources: microphone, low-level 440 Hz tone, synthetic two-sound heartbeat,
  or a volatile host-uploaded PCM fixture. Test sources cannot be sent as FHIR.
- Display, audio and optional network work run in separate threads. Input
  events never wait for a full-screen redraw. Failed GPIO event delivery retries
  the latest stable state instead of losing synchronization permanently.

## Serial shell

```text
stetho status
stetho set filter 0
stetho set analysis 2
stetho set speed 75
stetho capture
stetho replay
stetho live
stetho restart
stetho set heart 0
stetho set heart 1
stetho set point 0
stetho set brightness 80
stetho set diagnostics 1
stetho color 3
stetho set diagnostics 0
```

`filter` and `analysis`: 0 Raw, 1 Murmur, 2 BPM. `speed`: 100, 75, 50.
`point`: 0–4. `volume`/`brightness`: 0–100. `heart`/`diagnostics`/`pot`: 0 or 1.
To control volume by shell, first issue `stetho set pot 0`; restore `pot 1`
afterward. Pot volume is otherwise sampled every 100 ms.

```text
stetho set pot 0
stetho set volume 10
stetho set source 1
stetho set source 2
stetho set bpm 72
stetho set source 0
```

Sources: 0 microphone, 1 low-level tone, 2 synthetic heart, 3 uploaded fixture.
Generated signals enter the **same** filtering, BPM and output path as the mic.
A failed microphone probe does not prevent DAC test-source operation.
A source/analysis/mode/reference-rate change resets BPM acquisition and cancels
active capture/replay. Filter and volume changes are smoothed. Clip capture stores
filtered audio before volume. Replaying a clip uses its recorded filter; changing
the live filter does not reprocess that clip. Capture a new clip for comparison.
At slow speed incoming live samples continue serving BPM but do not accumulate
an unbounded playback queue. Stop/restart interrupts the current clip operation.

`stetho status` returns one JSON object suitable for host collection: levels in
parts per million of digital full scale, clipping totals, processing maximum,
8 ms deadline misses, RX/TX/allocation failures, slab usage, recovery totals,
BPM validity/quality, clip status and network result. Slab usage is **not** an exact
hardware FIFO depth. RX/TX error counters include driver-reported stream failures;
the Zephyr API does not distinguish every physical underrun/overrun cause.
Counters are cumulative since boot. Processing time excludes blocking I/O;
measure end-to-end acoustic/electrical latency separately.

See [hardware](HARDWARE.md), [network setup](NETWORK.md) and the
[evaluation protocol](EVAL-GUIDE.md) for setup and acceptance testing.

Updated by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
