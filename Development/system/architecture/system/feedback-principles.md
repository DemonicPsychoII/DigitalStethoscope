# Feedback ownership and fault containment

L2_CONTROL alone decides mode admission, fault containment and the indication to publish. L1_PHYSICALINTERFACE drives the RGB status light and separate red button error light. Detecting components report faults and record redacted causes in the serial log. The LED driver never decides recovery or runs a workflow.

The RGB light identifies operational context; the red button light identifies an error within that context. An error retains its originating context. A coherent feedback snapshot prevents a context from being paired with another error's code. Logs retain every cause even when only the selected error is indicated.

Fault selection uses priority; equal priorities keep the first latched fault. Acknowledgement and retry are separate actions. Clearing an indication must never initiate a workflow or bypass a restart-required fault. Wi-Fi-only failures preserve working audio and permit offline operation under [REQ-13](../../requirements/system-requirements.md#req-13); faults affecting essential audio mute/cancel acquisition and block Start until their clear rule is met. L2_CONTROL coordinates the listening/network lease, including bounded Wi-Fi cleanup failure handling.

Fault events carry a shared feedback identifier to the indication boundary so detecting components and LED drivers use consistent meanings. Recovery, indication and admission operate as separate concerns. The [input-ownership view](VIEW-NOTES.md#input-ownership) shows where L1_PHYSICALINTERFACE contact handling ends and L2_CONTROL policy begins.
