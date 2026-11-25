# Feedback parameters

P12 and P22 apply to the [status and error catalogue](catalogue.md#status-and-error-catalogue).

| ID | Parameter | Value | Basis | Owners |
| --- | --- | --- | --- | --- |
| P12 | Fault response / recovery | Wi-Fi-only faults preserve audio; audio faults halt at once and block every input until restart; other halting faults during listening latch silently until manual Stop; clear and restart follow the feedback catalogue | [Status and error catalogue](catalogue.md#status-and-error-catalogue) | MONITOR, L2_AUDIO, L2_CONTROL |
| P22 | Feedback timing and brightness | Codes/flashes: 2 Hz, 250 ms on/off (50 % on); 2 s group pause, at most 6 blinks per context; long flash 1 s; hold acknowledgement 4 Hz, 125 ms on/off; slow blink 0.5 Hz, 1 s on/off; breathing 3 s; input-rejected dimming by at least 50 % for 250 ms; Idle dim 20 %; startup lamp test at least 1 s. Brightness: every pattern must be seen at 1 m and the error state at 4 m, at 100–1500 lx ambient light, inside a 30° viewing cone | Rates from IEC 60073 (normal 1.4–2.8 Hz, slow 0.4–0.8 Hz, pulse:pause about 1:1); visibility from IEC 60601-1-8 6.3.2.2. See [LED indication standards](led-indication-standards.md). | L1_PHYSICALINTERFACE, L2_CONTROL |
