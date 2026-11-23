## Do the two data sources agree?

| Question | Own recordings (first part) | Public recordings (this version) | Verdict |
|---|---|---|---|
| Is a BPM filter needed at all? | Yes: without a filter 16 gross errors in 255 windows | Yes: no filter is the worst choice (33.5 against 26.6 BPM) | Agree |
| 40–150 Hz or the planned 25–150 Hz? | 40 Hz as a precaution; rested on one window | 40 Hz better by 4.4 BPM (3.3 to 5.5), against an ECG | Agree; now supported |
| Best lower edge? | 30 to 80 Hz equal; steep 60 Hz worst | Error falls up to 80 Hz; steep 60 Hz best | Differ |
| Does the filter design or the upper edge matter? | Not measurably on clean windows | A steeper filter helps a little (about 3.5 BPM) | Differ slightly |
| Is the counting method of the first part good? | 0.30 BPM, no gross error | Good sitting still (2.7 BPM), fails during exercise (26.6 BPM overall) | Differ |
| Ranking of the counting variants | final method > 8 Hz variant > half-rate check alone | half-rate check alone > 8 Hz variant > final method | Reversed |
| Was the sound-derived reference sound? | Could not be checked | 99.7 % within 2 BPM of the ECG where it called a window clean | Confirmed |
| Planned listening filter 40–800 Hz | No room for a boost; slightly quieter than no filter | Weakest listening candidate for murmurs | Agree |
| First listening candidate 100–800 Hz with boost | Louder by two of three estimates | In the top group for murmur level and for telling murmurs apart | Agree |
| Order of candidates by estimated loudness | By A-weighting and by the hearing curve | Same order (agreement 0.98 on a scale from −1 to 1) | Agree |
| Order by broadcast loudness | Every filter quieter than no filter | Reversed (−0.93): boosted filters louder | Differ |
| Does the upper edge matter for listening? | Hardly | Yes: a higher upper edge keeps more murmur level | Differ |
| Are the fixed boosts safe? | Safe on the five recordings by construction | Overload on 97 to 100 % of the modelled public recordings | Differ |

*The main questions answered with each data source.*

Why they differ, where they do:

- **Heart rates and regularity.** The public recordings contain far more windows above 90 BPM (about three quarters) with very regular beats, which is exactly where the first part's counting method picks a wrong multiple. Nico's five recordings did not trigger it. This is a weakness of the method that five recordings could not reveal, not a difference between the people.
- **Tone balance.** The public recordings carry much more sound above 100 Hz and much less below 20 Hz than Nico's recordings. A higher or steeper lower edge therefore still leaves plenty of heart sound in the public recordings, while in Nico's recordings it cuts into the little there is. The same explains why the broadcast loudness measure, which counts low tones fully, reverses its order, and why the upper edge matters in the public recordings and not in Nico's.
- **Disturbances.** The gross errors of the first part came from a movement and an unsteady start, both strong below 20 Hz. The public recordings contain little below 20 Hz, so they do not test this; they test regular beats at high rates and exercise noise instead.
- **Peaks.** The public recordings are more peaky than Nico's (their loudest moments stand further above their average), so a loudness setting that matches the heart sounds makes them overload sooner.

::callout{kind="finding"}
**The recommended filters hold; the method around them changes.** Both data sources support the BPM filter 40–150 Hz over the planned 25–150 Hz, and both support a listening filter with a lower edge near 100 Hz and a fixed boost over the planned 40–800 Hz. What the public recordings change is the counting method (its choice of the peak must be replaced), the confidence in fixed boosts (they need a safety margin or a limiter, not a value found on five recordings), and the upper edge of the listening filter (800 Hz costs murmur level; 1 to 2 kHz is worth a listen).
::end
