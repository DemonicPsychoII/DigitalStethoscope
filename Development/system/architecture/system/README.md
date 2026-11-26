# System architecture

The [viewer](review.html) presents the system architecture views except Input ownership and Server profile, and [view notes](VIEW-NOTES.md)
document their scope, hardware naming and runtime assumptions.

| Diagram | Editable source | Preview |
|---|---|---|
| Architecture | [puml/architecture-choice.puml](puml/architecture-choice.puml) | [SVG](rendered/architecture_choice.svg) |
| System context | [puml/system-context.puml](puml/system-context.puml) | [SVG](rendered/system_context.svg) |
| System components | [puml/system-components.puml](puml/system-components.puml) | [SVG](rendered/system_components.svg) |
| Electrical interfaces | [puml/electrical-interfaces.puml](puml/electrical-interfaces.puml) | [SVG](rendered/electrical_interfaces.svg) |
| Software components | [puml/software-components.puml](puml/software-components.puml) | [SVG](rendered/software_components.svg) |
| Input ownership | [puml/input-ownership.puml](puml/input-ownership.puml) | [SVG](rendered/input_ownership.svg) |
| Threads | [puml/runtime-ownership.puml](puml/runtime-ownership.puml) | [SVG](rendered/runtime_ownership.svg) |
| Listening | [puml/listening-workflow.puml](puml/listening-workflow.puml) | [SVG](rendered/listening_workflow.svg) |
| Session and error transitions | [puml/session-state.puml](puml/session-state.puml) | [SVG](rendered/session_state.svg) |
| BPM measurement | [puml/measurement-workflow.puml](puml/measurement-workflow.puml) | [SVG](rendered/measurement_workflow.svg) |
| Server profile | [puml/server-profile.puml](puml/server-profile.puml) | [SVG](rendered/server_profile.svg) |

[Firmware structure and runtime ownership](firmware-structure.md) defines the layers and call directions, the ownership of each module, the threads, the hand-offs between them and the listening and network lease.

[Feedback ground rules](feedback-principles.md) define indication ownership and fault containment.

[Server profile](server-profile.md) defines how a device receives its server endpoint, keep-alive and trusted certificate.
