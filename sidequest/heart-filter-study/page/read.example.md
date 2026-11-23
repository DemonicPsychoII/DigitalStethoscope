---
title: Which filter should the stethoscope use? (example)
subtitle: A worked example that exercises every directive of the page generator, with synthetic data.
date: 23 November 2026
status: Interim
watermark: Example read generated from page/read.example.md with synthetic data; not a study result.
---

::summary
- The **band-pass filter 25–150 Hz** gives the smallest heart-rate error in this *synthetic* example [1].
- At full volume the device overloads the output for the unfiltered signal; a fixed gain per filter avoids that.
- Listen below: switch filters while the sample plays to hear the difference.
::end

## Why this matters

A digital stethoscope picks up heart sounds, but also breathing, skin rubbing and mains hum. A
filter decides what the listener hears and what the heart-rate estimator sees [1, 2].

::term{name="band-pass filter"}
A filter that lets through only a range of pitches, here roughly the low hum of the heart
(25 to 150 vibrations per second), and removes deeper rumble and higher hiss.
::end

::term{name="clipping"} When a signal is louder than the output can represent, its peaks are cut off flat. This sounds harsh and distorts the heart sounds. ::end

## Method

We compared three candidate filters on two recordings. Each candidate ran in a model of the
device chain: filter, then volume, then the output converter. See the table and figure below.

::table-csv{src="page/example-data/filter-results.csv" columns="label,mean_absolute_error_bpm,detection_rate,latency_ms" headers="Filter,Mean error (BPM),Beats detected,Delay (ms)" rows="6" caption="Heart-rate error per filter (synthetic numbers). The highlighted row is the recommendation." highlight="identifier=butterworth_hp2_25_lp2_150"}

The same table with two decimals everywhere:

::table-csv{src="page/example-data/filter-results.csv" columns="identifier,mean_absolute_error_bpm" headers="Filter,Mean error (BPM)" rows="3" precision="2"}

::figure{src="page/example-data/figures/example-filter-response.png" alt="Magnitude response of three filters between 5 Hz and 2 kHz" caption="How strongly each filter passes each pitch. Tap or click the figure to enlarge it." width="wide"}

A plain Markdown table also works and scrolls on its own on narrow screens:

| Recording | Heart rate (BPM) | Length (s) | Note |
| --- | ---: | ---: | --- |
| resting | 68 | 5.0 | quiet, regular |
| after-exercise | 112 | 5.0 | louder heartbeats that overload the output at full volume |

## Listen and compare

::audio-compare{excerpt="resting" variants="device,madeup,matched" title="Resting heart, three filters" note="Use headphones. Start playback, then tap another filter: it continues at the same moment."}

::audio-compare{excerpt="after-exercise" title="After exercise" note="Here the unfiltered signal overloads the output at full volume (see the clipped counts)." explain-matched="All three filters at the same loudness: listen for the character of the heart sounds."}

## Results

::callout{kind="finding"}
The band-pass filter reduced the mean heart-rate error from 9.8 to 1.9 BPM in this example [2].
::end

::callout{kind="limitation"}
These numbers come from **synthetic** signals. They only demonstrate the page layout.
::end

::callout{kind="decision"}
The volume path stays unchanged; a fixed gain per filter is applied before it.
::end

::callout{kind="open"}
Is the 4 ms delay of the band-pass filter acceptable for the beat indicator light?
::end

::raw-html
<p class="raw-html-example">This paragraph was passed through as <em>raw HTML</em>.</p>
::end

## Glossary

::glossary

## Sources

::sources
[1] A. Author and B. Author, "An example article about heart sounds," *Example Journal*, vol. 1, pp. 1–10, 2024. https://example.org/heart-sounds
[2] Own measurement (synthetic example), page/example-data/filter-results.csv, 23 November 2026.
::end
