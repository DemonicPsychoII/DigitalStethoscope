# Feedback ownership and fault containment

These are project architecture decisions derived from REQ-13 and the system error use case. They define responsibilities; the separate FEEDBACK detailed design assigns colours, code numbers, priorities, clear rules and timing. No standards conformity is asserted here.

CONTROL alone decides mode admission, fault containment and the indication to publish. L1_PHYSICALINTERFACE drives the RGB status light and separate red button error light. Detecting components report faults and retain redacted causes in the serial log; the LED driver does not decide recovery or run a workflow.

The RGB light identifies operational context; the red button light identifies an error within that context. An error retains its originating context. A coherent feedback snapshot prevents a context from being paired with another error's code. Logs retain every cause even when only the selected error is indicated.

Fault selection uses priority; equal priorities keep the first latched fault. Acknowledgement and retry are separate actions. Clearing an indication must never initiate a workflow or bypass a restart-required fault. Wi-Fi-only failures preserve working audio and permit offline operation under REQ-13; faults affecting essential audio mute/cancel acquisition and block Start until their clear rule is met. CONTROL coordinates the listening/network lease, including bounded Wi-Fi cleanup failure handling.

The shared feedback identifier is carried by fault events and consumed by the indication boundary. A single catalogue prevents detecting components and LED drivers from assigning conflicting meanings. Specific codes, patterns, enum representation and visibility acceptance conditions belong to detailed design and generated Tests.
