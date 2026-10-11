# Requirements — component allocation

[Use cases](use-cases.md) → [system requirements](system-requirements.md) → component requirements → [planned verification](../testing/specification-verification.md). [Parameter register](parameters.md) contains open numeric/design choices. [Traceability CSV](traceability.csv) indexes every component requirement.

| Component | Requirements | Scope |
|---|---|---|
| [HW](components/hw.md) | 4 | Hardware integration |
| [INP](components/inp.md) | 4 | Physical and touch input adapters |
| [CTL](components/ctl.md) | 6 | Application controller |
| [AUD](components/aud.md) | 6 | Audio source and block transport |
| [LIS](components/lis.md) | 5 | Listening DSP and output |
| [REC](components/rec.md) | 4 | Volatile clip capture and replay |
| [BPM](components/bpm.md) | 6 | Heart-rate analysis and session aggregation |
| [STO](components/sto.md) | 4 | Fixture storage and prefetch |
| [UI](components/ui.md) | 5 | Display, LED and shell surface |
| [NET](components/net.md) | 7 | FHIR/TLS delivery |
| [MON](components/mon.md) | 5 | Monitoring and evidence |

Requirement IDs remain stable when edited; retired IDs must be recorded rather than reused. All requirements are drafts. The CSV is an index, not a second copy of requirement text. Source IDs are defined in the product scope; test IDs describe future evidence, not passed tests.

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
