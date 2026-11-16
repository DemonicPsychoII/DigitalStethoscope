# System architecture

Shared views remain at system level. The [viewer](review.html) presents the product views;
[view notes](VIEW-NOTES.md) retain their scope, hardware naming and runtime assumptions.

| Diagram | Editable source | Preview |
|---|---|---|
| Architecture | [architecture-choice.puml](architecture-choice.puml) | [SVG](rendered/architecture_choice.svg) |
| System context | [system-context.puml](system-context.puml) | [SVG](rendered/system_context.svg) |
| System components | [system-components.puml](system-components.puml) | [SVG](rendered/system_components.svg) |
| Electrical interfaces | [electrical-interfaces.puml](electrical-interfaces.puml) | [SVG](rendered/electrical_interfaces.svg) |
| Software components | [software-components.puml](software-components.puml) | [SVG](rendered/software_components.svg) |
| Input ownership | [input-ownership.puml](input-ownership.puml) | [SVG](rendered/input_ownership.svg) |
| Threads | [runtime-ownership.puml](runtime-ownership.puml) | [SVG](rendered/runtime_ownership.svg) |
| Listening | [listening-workflow.puml](listening-workflow.puml) | [SVG](rendered/listening_workflow.svg) |
| MVP session / alarms | [mvp-session-state.puml](mvp-session-state.puml) | [SVG](rendered/mvp_session_state.svg) |
| BPM measurement | [measurement-workflow.puml](measurement-workflow.puml) | [SVG](rendered/measurement_workflow.svg) |
| Server profile | [server-profile.puml](server-profile.puml) | [SVG](rendered/server_profile.svg) |

Lung mode is optional beyond the MVP (TICKET-203); its paths are marked optional in the listening and MVP session views.

[Feedback ground rules](feedback-principles.md) define indication ownership and fault containment. The session view's error latch is refined in the [FEEDBACK fault-handling view](../../design/FEEDBACK/catalogue.md#fault-handling).

[Server profile](server-profile.md) allocates how a device receives its one server, endpoint and trusted certificate.

Original board snapshots remain immutable source material.
