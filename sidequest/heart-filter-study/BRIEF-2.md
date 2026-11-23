# Brief 2: heart filter study with public data

Continuation of the study in this folder. Read `BRIEF.md` (all its rules still apply unless changed
here), then `STATE.md` and `FINDINGS.md` from the first run, and reuse its code in `src/hfs/`,
`.venv/` and caches. Nico is not available; decide open points yourself and record them in
`STATE.md` with the reason.

## Time limit and resumability

- Started: 2026-11-23 09:20 (+01:00). **Hard stop: 14:19 (+01:00)**; the parent thread cancels you
  then without warning. **Wrap up from 13:49 at the latest.**
- Same resumability rules as `BRIEF.md`: add a new section "Run 2" to `STATE.md` (phases, decisions,
  delegates with task IDs, next steps) and to `FINDINGS.md`; keep them current after every
  milestone. Downloads must be resumable and verified (checksums where the source gives them).
- All software is written by Claude Opus 5.5 on high effort via `delegate_task`, as in `BRIEF.md`.

## Why

The first run used only Nico's five recordings: one person, no murmurs, and a heart-rate reference
taken from the same sound. Nico wants the evaluation extended with public data and compared with
our own analysed audio chain.

## Goal

1. **Public data.** Find, verify and download suitable open datasets (check licence, size, sample
   rate and annotation before downloading; store under `public-data/`, outside the repository;
   record exact versions and citations). Candidates to verify, not assumed facts:
   - a dataset with heart sounds **and simultaneous ECG**, ideally including exercise (for example
     EPHNOGRAM on PhysioNet), as an independent heart-rate reference for the BPM filter;
   - **CirCor DigiScope** (murmur labels and segmentation) for the listening filter: does a
     candidate keep murmurs audible and distinguishable;
   - others only if they add something these do not.
   Use a well-defined, justified subset if a full set is too large for the time; split by patient.
2. **Through our chain.** Run the public recordings through a model of our device chain that is as
   close to the real device as the evidence allows, and say exactly which parts are modelled from
   what:
   - resampling to 16 kHz, the INMP441 (datasheet model in
     `Development/system/testing/AUDIO/chain-measurement/microphone_model.py`; its unverified
     fields stay marked), the noise floor and the full-scale overload seen in Nico's recordings,
     the firmware's block processing, volume and output stage (reuse `src/hfs/`);
   - the chest-piece: the public recordings already contain their own stethoscope sensor, so our
     chest-piece cannot simply be added. From the chain measurement, only the membrane-vs-bell
     comparison (C/B) and the shape above about 400 Hz are usable (see `BRIEF.md`). Decide whether
     and how to include a chest-piece correction, run it as a variant at most, and justify it.
   - Calibrate the level and spectrum of the modelled chain against Nico's recordings (they are the
     real chain on a real chest), and report how close the modelled public data comes to them.
3. **Evaluate the same filters** as in run 1 (BPM filter + counting method together; listening
   candidates), now on the public data:
   - BPM: accuracy against the ECG reference, at rest and at high rates, using the same 8 s
     rolling-window ESP32-S3 estimator; also validate run 1's sound-derived reference method
     against ECG where both exist.
   - Listening: murmur audibility or distinguishability metrics fixed in advance (see
     `thesis-material/08-evaluation/03-filtervergleich-statistik.md`), paired comparison with
     Raw, paired tests with correction for multiple tests; add a few murmur excerpts to the
     listening samples if the upload size allows.
4. **Compare** public-data results with run 1 on Nico's recordings: do the rankings and the
   recommended filters hold? Where they differ, say why.
5. **Update the read on Pages** (same page, new version) to cover both data sources, same style and
   rules: plain language, Hz/kHz axes, sources cited, limitations stated. Fix the open points of
   run 1 where cheap (for example add the recommended 40–150 Hz BPM filter to the listening samples
   if the size allows; the two known code errors). Council verification before publishing, as in
   `BRIEF.md`.

## Report back

Page URL and version, the recommended filters and whether public data confirmed or changed them,
key numbers, council verdict, open points, path to `STATE.md`.

## Addition by Nico (23 November 2026, during run 2)

Add a section to the read: **how the first measurement setup (the chain measurement of 22 November
2026) fed into this study.** In plain language: what was measured and how (with a simple picture or
diagram of setups A, B and C if cheap), what came out, what this study took from it (for example the
capture firmware, the microphone model, the validity limits, the decision not to apply a chest-piece
correction, and in run 2 the chain model for the public data), what it did not take and why, and how
the planned second session would change that. Source: `chain-measurement-reviews.md` in this folder
(condensed setup, results and both reviews; replaces "the review texts were not inspected"), plus the
session folder and the repository README it points to. The section goes into the next page version and
through the council like the rest.

## Second addition by Nico (23 November 2026, during run 2): BPM does not have to be real time

The BPM estimate works on an 8 s rolling window held in PSRAM, so its analysis branch does not have
to be causal or sample-by-sample: it may process each buffered window as a whole. Explore this:

- **Zero-phase ("both ways") filtering** of each window (forward and backward, as `filtfilt` does):
  no phase delay or smearing of the heart sounds, doubled effective order; handle the window edges
  (padding or discarding the edge seconds) and compare against the causal filters of run 1.
- **The Springer approach:** Nico means the heart-sound segmentation of Springer, Tarassenko and
  Clifford (logistic-regression hidden semi-Markov model, IEEE Transactions on Biomedical
  Engineering, 2016), which filters forward-backward and derives several envelopes (homomorphic,
  Hilbert, power-spectral, wavelet) before estimating heart rate and segmenting S1/S2. Verify the
  citation and details from the original before relying on them; add the source to the read's
  references. Evaluate at least its pre-processing and heart-rate estimate (envelopes +
  autocorrelation) as a BPM method; the full segmentation only if time allows and it adds accuracy.
- **Device budget:** with one estimate per update step over 8 s of data, estimate the processor
  time per window on the ESP32-S3 (single-precision FPU, the audio thread has priority) and the
  PSRAM and internal RAM needed, including any decimation before the window analysis; state which
  variants fit and how often they could update.
- Evaluate on both data sources (Nico's recordings and the public set with ECG reference) with the
  same windows as the causal variants, and say in the read whether non-real-time processing beats the
  recommended causal 40–150 Hz filter and counting method, and at what cost. The listening path stays
  real time (latency below 30 ms); this addition concerns only BPM.
