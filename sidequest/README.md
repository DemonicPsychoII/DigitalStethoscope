# Side quests

Exploratory work outside the planned V-model artefacts: measurements, prototypes and studies that
fed decisions but are not requirements, design or verification evidence themselves. Each folder is
kept as it was produced, with its own README or findings; numbers there are evidence for the
statements in that folder only.

| Folder | What it holds | Tickets |
| --- | --- | --- |
| [DigitalStethoscope-mic-samples-2026-11-15](DigitalStethoscope-mic-samples-2026-11-15/) | 3D-printed microphone adapter v10 to v14, first chest and room recordings, the I2S bit clock measurement, capture tool, and the transcript of the supervisor meeting on 16 November 2026 | TICKET-185, TICKET-186 |
| [DigitalStethoscope-weight-test-2026-11-23](DigitalStethoscope-weight-test-2026-11-23/) | Static weight test on the chest piece, v10 sealed against v14 with vent; [findings](DigitalStethoscope-weight-test-2026-11-23/FINDINGS.md) on what a steady push does to the microphone | TICKET-186 |
| [heart-filter-study](heart-filter-study/) | Offline simulation of listening and BPM filters on own and public heart sound recordings; [findings](heart-filter-study/FINDINGS.md) | TICKET-189, TICKET-192 |

## Not in the repository

These parts stay outside the repository:

- `heart-filter-study/.venv`, `cache/`, `public-data/` and `listening-public/` (about 14 GB): the
  Python environment, intermediate results, downloaded public data sets and listening samples
  derived from them. The scripts in `heart-filter-study/src/` download and regenerate them.
- `heart-filter-study/page/publish*.json`: publishing records holding time-limited share links.
- The MT1 course material (`Stethoskop-Kursmaterial`): lecturers' material that its own README
  says not to publish or commit.
- macOS `__MACOSX` folders and `._*` resource files.
