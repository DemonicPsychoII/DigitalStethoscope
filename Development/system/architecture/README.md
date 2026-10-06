# Architecture diagrams

Snapshot: 2026-10-06, integration commit `655f74a`. The local checkout used to
start this task was older, so the implementation diagrams use the fetched
integration revision. No firmware was changed.

- [System architecture](system-architecture.puml): current evaluation hardware,
  local interfaces and optional network endpoints.
- [Software layer architecture](software-architecture.puml): the agreed
  L2 Application / L1 Services / L0 Platform design, with an enclosing box for
  every layer. `MON`, shared contracts and host tests have separate boxes.
- [Current software implementation](software-implementation.puml): actual
  modules, execution contexts and key interactions, grouped in boxes without
  claiming the future layer boundaries are already enforced.

The layer design comes from
[PR #15](https://github.com/DemonicPsychoII/DigitalStethoscope/pull/15), specifically
`Development/system/coding/app/README.md` at commit `3d471dc789e42cee6773e4714fa7b5d15b212589`.
It is still an open design/structure PR at this snapshot. Current firmware stays
in `coding/bringup-zephyr`; the folder migration is separate work. The proposed
single-writer controller, upward message queues and dedicated MON module are
design rules, not assertions about the current evaluation implementation.

Implementation sources: `bringup-zephyr/CMakeLists.txt`, `src/`, `include/`,
`Kconfig`, `prj.conf`, `network.conf`, the board overlay and its README. In
particular, the current control module uses mutex-protected settings with
multiple callers, and audio, display and optional network have their own threads.
BPM and replay algorithms reside in `stetho_dsp.c`; volatile clips are owned by
the audio module. SD support currently mounts a filesystem rather than saving
those clips automatically.

The system diagram describes configured interfaces, not hardware acceptance.
Networking is optional and requires explicit configuration/connection. The
DAC is a line output and needs a suitable headphone amplifier. Speed-switch
and SD wiring are outside the existing wiring confirmation.

Open `.puml` files in a PlantUML-compatible editor, or render locally:

```sh
java -jar /path/to/plantuml.jar -tsvg Development/system/architecture/*.puml
```

Created by GPT-6.1-Sol on behalf of Nico running in codex.
