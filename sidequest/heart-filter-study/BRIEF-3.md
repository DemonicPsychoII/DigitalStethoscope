# Brief 3: one clean-up pass so the read reads like a paper

Nico likes version 3 of the read (https://homelab-server.tail15fafc.ts.net:8092/p/heart-filter-study/)
and wants **one editorial clean-up pass** before reading it in detail. Rules of `BRIEF.md` still apply
(plain language, sources, Hz/kHz axes, homelab dark theme, watermark, Opus 5.5 on high effort writes
any code via `delegate_task`, keep `STATE.md` current under a new section "Run 3").

## Time limit

Started 11:47 (+01:00) on 2026-11-23. **Hard stop 13:46**; wrap up from 13:31. If unfinished, leave
version 3 online unchanged and record the state in `STATE.md`.

## What to do

1. **Paper structure**, in this order: title, authors line (Nico, with the AI assistance stated),
   date; abstract (about 150–200 words, key numbers); 1 Introduction (question, why it matters for
   the device); 2 Device and audio chain (including the chain measurement section); 3 Data (Nico's
   recordings, public datasets); 4 Methods (chain model, filters, BPM estimator and counting method,
   listening metrics, statistics); 5 Results (BPM, listening, non-real-time BPM, agreement between the
   data sources); 6 Discussion (what it means, recommendations); 7 Limitations; 8 Conclusion and next
   steps; References; appendix for review history, reproducibility and file paths.
   Merge run 1 and run 2 into one coherent account: report the current state, not the history.
   Where run 2 replaced a run 1 result (for example the withdrawn counting method), state the
   current result and mention the earlier one only where it explains a decision.
2. **Numbered figures and tables** with captions, each referenced in the text; one consistent style.
   Fix the stale items: the shortlist table and the two run 1 figures that show eight candidates
   must include the 40–150 Hz filter, or say clearly what they show.
3. **Language:** tighten, remove repetition, keep it free of jargon; consistent terms throughout
   (one name per filter, per method, per data set); one number format.
4. **No new analysis and no changed numbers.** Every number must stay as in version 3 and in the
   result files. After editing, check every number in the new text against version 3 and the
   result files and record the check in `STATE.md`. Regenerating a figure for the fixes in step 2
   is allowed from the existing result files.
5. **Check before publishing:** one review by Claude Sonnet 5.5 (via `delegate_task`, high effort)
   comparing version 3 with the new text for changed meanings, lost limitations, changed numbers and
   broken figures or players. Fix its findings. No full council round.
6. **Publish as version 4** of the same page with `publish-page`; verify the hosted page (figures,
   players, phone width).

## Report back

Page URL and version, what changed in structure, the number check result, the review result, and
anything left open.
