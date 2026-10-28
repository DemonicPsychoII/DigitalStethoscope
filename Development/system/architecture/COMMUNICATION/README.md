# COMMUNICATION architecture

L2_COMMUNICATION owns the setup workflow and recovery policy under CONTROL's network lease. It composes WIFI radio/address operations, STORAGE persistence and PORTAL typed requests/status publication. CONTROL owns mode admission; listening requests trigger safe setup teardown before lease release. Lower services never change controller state. These are project allocations derived from REQ-11/REQ-12/REQ-13.

| View | Editable source | Preview |
| --- | --- | --- |
| Setup state machine | [setup-state.puml](setup-state.puml) | [SVG](rendered/setup_state.svg) |
| Provisioning flow | [setup-flow.puml](setup-flow.puml) | [SVG](rendered/setup_flow.svg) |
| Setup ownership sequence | [setup-sequence.puml](setup-sequence.puml) | [SVG](rendered/setup_sequence.svg) |
| Link recovery | [link-recovery.puml](link-recovery.puml) | [SVG](rendered/link_recovery.svg) |

The [diagram viewer](setup-workflows.html) presents these architecture views. The general station/provisioning model lives under [WIFI](../WIFI/README.md); the browser boundary under [PORTAL](../PORTAL/README.md). Retry counts, timing, status/error patterns and request fields belong to detailed design.

[Time synchronization](time-ownership.md) proposes SNTP ownership and the clock dependency for later server communication. Clock trust acceptance remains open.
