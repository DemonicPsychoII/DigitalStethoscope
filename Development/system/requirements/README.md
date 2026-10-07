# Requirements — component allocation

[Use cases](use-cases.md) → [system requirements](system-requirements.md) → component requirements → [planned verification](../testing/specification-verification.md). [Parameter register](parameters.md) contains open numeric/design choices. [Traceability CSV](traceability.csv) indexes every component requirement.

| Component | Scope |
|---|---|
| [HW](components/hw.md) | Hardware integration |
| [INP](components/inp.md) | Physical and touch input adapters |
| [CTL](components/ctl.md) | Application controller |
| [AUD](components/aud.md) | Audio source and block transport |
| [LIS](components/lis.md) | Listening DSP and output |
| [REC](components/rec.md) | Volatile clip capture and replay |
| [BPM](components/bpm.md) | Heart-rate analysis and session aggregation |
| [STO](components/sto.md) | Fixture storage and prefetch |
| [UI](components/ui.md) | Display, LED and shell surface |
| [NET](components/net.md) | FHIR/TLS delivery |
| [MON](components/mon.md) | Monitoring and evidence |

Requirement IDs remain stable when edited; retired IDs must be recorded rather than reused. All requirements are drafts. The CSV is an index, not a second copy of requirement text. Source IDs are defined in the product scope; test IDs describe future evidence, not passed tests.

Updated by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
