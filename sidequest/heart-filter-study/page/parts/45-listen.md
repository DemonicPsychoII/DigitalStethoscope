### Listen and compare

Use headphones: in Nico's recordings almost all energy lies below 150 Hz, which small loudspeakers of phones and laptops reproduce poorly (general experience, no source checked). Each player holds the same stretch of sound through nine candidates: the eight of the first version and, new in this version, the recommended BPM filter 40–150 Hz. Tap a row to switch while it plays. "Hide names" gives a blind comparison. The loudness on a computer is not the loudness of the device; compare the candidates with each other. A 20-millisecond fade at the start and end of each sample is not part of the device.

**Nico's recordings** (10 seconds each, through the real chest-piece, tube and microphone):

::audio-compare{excerpt="resting" variants="madeup,device,matched" title="At rest" note="Clean recording, about 80 beats per minute."}

::audio-compare{excerpt="elevated-clean" variants="madeup,device,matched" title="After exercise, no overload" note="About 100 beats per minute."}

::audio-compare{excerpt="elevated-overload" variants="madeup,device,matched" title="After exercise, repeated overload on the beats" note="The microphone path is overloaded on many beats here. Listen for which candidates make the distortion more or less noticeable."}

::audio-compare{excerpt="movement-artefact" variants="madeup,device,matched" title="At rest, with a movement" note="Contains a movement of the chest-piece: the case for \"too much other sound\"."}

**Public recordings with murmurs** (8 seconds each, from the murmur collection [17], passed through the model of our device input at rest level and then through the same simulated device; offered with the fixed boosts and at equal loudness only, without the version "as the device plays it today"). They are from children of about 1.1 m height and were chosen by a fixed rule before listening: the clearest example of its group, at the place on the chest where the murmur is heard best. These are not recordings made with our device: they are brighter than ours and contain nothing above 2 kHz. With the fixed boosts, some candidates overload the output on the two murmur samples (values cut off at full scale, out of 128,000 per sample, loud / soft murmur: 100–800 Hz gentle 71 / 46, 100–800 Hz steep 292 / 193, 150–800 Hz steep 804 / 693, above 80 Hz only 7 / 9, 60–800 Hz very steep 0 / 10; none in the sample without a murmur and none in the "same loudness" versions). This is the overload warning from the murmur results made audible. Each murmur sample starts with the filter switched on at its first value, so the first fraction of a second can sound different from the rest.

::audio-compare{excerpt="murmur-loud" variants="madeup,matched" explain-madeup="Each candidate with the fixed boost found safe on Nico's five recordings. On this public recording some boosted candidates overload the output (see the note above)." title="Loud murmur (grade III or more)" note="A harsh, high-pitched murmur that fills the whole stretch between the first and the second heart sound. Listen for which candidates keep the murmur clear; harshness in the boosted candidates can come from the overload described above and not from the filter (compare with the same-loudness versions)."}

::audio-compare{excerpt="murmur-soft" variants="madeup,matched" explain-madeup="Each candidate with the fixed boost found safe on Nico's five recordings. On this public recording some boosted candidates overload the output (see the note above)." title="Soft murmur (grade I)" note="The clearest grade I example in the collection, so easier to hear than a typical soft murmur."}

::audio-compare{excerpt="no-murmur-child" variants="madeup,matched" explain-madeup="Each candidate with the fixed boost found safe on Nico's five recordings. No candidate overloads the output on this sample (the highest peak stays 0.2 dB below full scale)." title="No murmur, child of similar size" note="For comparison: the same place on the chest as the loud murmur, without a murmur."}

::callout{kind="open"}
**The listening filter is not decided.** It is Nico's judgement by ear. A reasonable first candidate to check is still "100–800 Hz, gentle" with a fixed boost of 5.9 dB: on Nico's recordings it is 1.1 to 1.5 dB louder than Raw by two of the three estimates and 6.5 LU quieter by the third, and on the public murmur recordings it is in the top group for telling murmur from no murmur, with or without the boost. The 4.1 dB by which the murmur comes out stronger than Raw there is the boost itself, and with that boost the output overloads on 99.8 % of the modelled public recordings. The filter weakens sound at 50 Hz to about a quarter (−12.3 dB; with the boost, about half, −6.4 dB). Compare it against "40–800 Hz" and "above 80 Hz only" for whether it sounds too thin. If the planned 40–800 Hz filter sounds best, it cannot be boosted. The boost of 5.9 dB is safe on Nico's five recordings only.
::end
