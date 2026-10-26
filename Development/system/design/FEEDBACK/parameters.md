# Feedback parameters

P22 applies to the status/error catalogue. These are design choices and unverified standards working assumptions, not a conformity claim.

| ID | Parameter | Value / candidate | Verification status | Owners |
| --- | --- | --- | --- | --- |
| P22 | Feedback timing and brightness | Codes/flashes: 2 Hz, 250 ms on/off (50 % on); 2 s group pause, at most 6 blinks per context; long flash 1 s; slow blink 0.5 Hz, 1 s on/off; breathing 3 s; input-rejected dimming by at least 50 % for 250 ms; Idle dim candidate 20 %; startup lamp test at least 1 s. Brightness: every pattern must be seen at 1 m and the error state at 4 m, at 100–1500 lx ambient light, inside a 30° viewing cone | Rates from IEC 60073 (normal 1.4–2.8 Hz, slow 0.4–0.8 Hz, pulse:pause about 1:1); visibility from IEC 60601-1-8 6.3.2.2. See [LED indication standards](led-indication-standards.md). Documented deviations; no conformity claim. Specific error-code and priority identification at 1 m is outside automated MVP verification; one-time manual final system acceptance is required by the P22 manual procedure (`testing/system/P22-final-legibility.md`, named by `testing/ci/test_manual_test_records.py`), which is not yet in the repo. Pattern visibility remains separate; primary IEC clauses/applicability unverified | INP,UI |
