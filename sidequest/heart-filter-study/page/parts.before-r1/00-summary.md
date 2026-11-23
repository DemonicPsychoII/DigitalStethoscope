---
title: Which filters should the digital stethoscope use?
subtitle: A simulation with five own heart recordings and two public collections (heart sounds with ECG, heart sounds with murmurs), for listening and for counting the heart rate (TICKET-189)
date: 23 November 2026
status: Second version, with public data; listening judgement pending
watermark: Published by Claude-Fable-5.2 on behalf of Nico running in T3 Code through Claude Code.
---

::summary
**What is new in this version.** The first version rested on five recordings of one person. This one adds two public collections: 29 hours of heart sounds from 22 young men with an ECG as an independent heart-rate reference, at rest and during exercise, and recordings of 873 patients, mostly children, with and without heart murmurs. They were passed through a model of our device's input. It also explains how the table measurement of 22 November fed into the study, and explores counting the heart rate on the stored 8 seconds as a whole.

**Heart rate: the filter recommendation holds, the counting method does not.** The recommended **40–150 Hz** filter beats the planned 25–150 Hz filter and no filter on the public recordings too, now against an ECG. But the counting method of the first version fails there during exercise: sitting still it is 2.7 beats per minute (BPM) off on average, over all recordings 26.6 BPM, because above about 90 BPM it often reports a third of the true rate. The cause was found (it picks the wrong one of several equally good repeat patterns) and an improved choice was built and tested on people it was not tuned on: it halves the error (28.4 to 13.1 BPM) and leaves the result on Nico's recordings unchanged, but is slightly worse at slow heart rates and still far from the target during exercise. Counting on the stored 8 seconds in non-real time is possible but brings no gain of its own.

**Listening: the first candidate is confirmed for murmurs.** The planned 40–800 Hz filter is the weakest listening candidate for murmurs. Filters with a lower edge of 80 to 150 Hz, played with the boost they make room for, make a murmur 3 to 8 dB stronger than without a filter (dB is a measure for ratios, explained below: +6 dB is twice as large) and let simple measures tell murmur from no murmur better. The first candidate named in the first version, **100–800 Hz with a boost of 5.9 dB**, is in that top group. The choice by ear is still Nico's; murmur samples are now among the listening samples.

**How far this carries.** The public recordings come from other sensors and other people, are much brighter than what our chain delivered on Nico's chest, and were only passed through a model of our device input. They test the filters and the counting method more widely; they do not show how our device sounds on those people.
::end
