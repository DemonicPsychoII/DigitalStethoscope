# Microphone capture tool

Temporary firmware and PC script that record raw INMP441 audio from the DigitalStethoscope Eval carrier. It is not
part of the application; flashing it replaces the application firmware until that is flashed back.

## What it does

- I2S0 receive on GPIO4 (clock), GPIO5 (word select), GPIO6 (data): 16 kHz, two 32-bit slots, left slot used,
  24-bit samples (`word >> 8`).
- Format `I2S_FMT_DATA_FORMAT_LEFT_JUSTIFIED | I2S_FMT_FRAME_CLK_INV`. With the standard I2S format every sample
  arrives one bit too far left; see the main [README](../README.md).
- **Headphones:** I2S1 transmit to the PCM5102A on GPIO40/41/42, the raw microphone signal on both channels with
  no gain and no filter, as in the application. Off after start.
- **Record:** 15 s mono 24-bit into PSRAM, then sent over UART0, one clip at a time. The button LED is lit from the
  start of a clip until it has reached the PC (about 23 s); a press during that time is ignored.
- **Carrier button (J6):** the first press turns the headphones on, every further press records one clip.
- **Stream:** the same samples live over UART0.
- UART0 runs at 921600 baud (CH343 bridge, COM4). Log and shell are off because the line carries binary frames.

Frame, little-endian: `"STHA"`, kind (1 stream, 2 recording, 3 recording end), flags (bit 0: an I2S receive error
happened during the recording), sample count (u16), sequence (u32), first sample index (u32), samples as 3-byte
signed integers, CRC-32 (IEEE) of header and samples. Commands are single bytes: `l` headphones on, `r` record, `s` stream,
`x` stop everything including the headphones, `?` status line.

## Use

Both PowerShell scripts take the toolchain from the main DigitalStethoscope checkout at `C:\SVN\DigitalStethoscope`
(`Development\system\coding\tools\firmware-common.ps1`). Nothing else may hold COM4 while flashing or recording.

```powershell
pwsh -File build_capture.ps1                                   # builds into .\build
pwsh -File flash_image.ps1 -BuildDirectory (Resolve-Path build)
uv run capture.py record --button --name 11-first 12-second    # one name per clip: press once for the
                                                               # headphones, then once per clip
uv run capture.py record --listen --name 14-my-recording       # started from the PC, headphones on
uv run capture.py stream --seconds 5 --gain 0                  # live stream to a file, no playback
pwsh -File flash_image.ps1 -BuildDirectory <application build directory>   # put the application back
```

Each recording gives `<name>-raw.wav` (24 bit, as delivered), `<name>-listen.wav` (DC removed, normalised, 16 bit)
and `<name>.png` (waveform, spectrogram, spectrum) in `recordings\`.

## Analysis scripts

Run with `uv run --with numpy --with scipy --with matplotlib python analysis\<script> ...`.

| Script | Purpose |
|---|---|
| `analyse_recording.py` | Clipping, level per second, energy per band |
| `wrap_check.py` | Bit statistics and wrap-around test for the one-bit shift |
| `reconstruct_recording.py` | Undo shift and wrap-around of a shifted recording; picture |
| `find_clicks.py` | Locate clicks and relate them to the microphone limit |
| `click_remedies.py` | Click rate by signal level; band-pass and zeroing compared |
| `band_levels.py` | Level per frequency band for parts of recordings |
| `highpass_listen.py` | High-pass a raw recording into a listening file |
| `evaluate_filters.py` | Filter candidates on raw recordings: spectra picture, table of numbers, listening files |
| `inspect_flat_stretches.py` | Stretches in which the microphone delivers an almost constant value |
| `inspect_jumps.py` | Size, direction, spacing and decay of the fast jumps; picture |
| `inspect_muted_ramps.py` | Share of time in noise-free ramps after the limit, and their time constant |
| `inspect_jump_block_alignment.py` | Whether the jumps sit on I2S block boundaries (lost-block test) |
| `compare_room_noise_clips.py` | Level per frequency band of several recordings side by side |

`record_with_room_noise.py <clip name>` plays the same seeded pink noise on the PC's default output and records one
clip started from the PC; `record_with_room_noise.py test` only plays 3 s of it.
| `analyse_clock_csv.py` | Periods, duty cycle, levels and gaps of a Rigol CSV export of a clock; picture |

`log_device.py <minutes>` records the application UART log with PC timestamps into `device-log-<date-time>.txt` and
turns on the debug log of the audio and I2S modules first; it lists error and warning lines at the end.
