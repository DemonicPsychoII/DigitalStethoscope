# System detailed design

[Interfaces and behavior](interfaces-and-behavior.md) and [parameters](parameters.md) define shared system contracts. Component designs allocate radio operations to WIFI, setup sequencing to COMMUNICATION, HTTP/page behavior to PORTAL, records to STORAGE and indication values to FEEDBACK.

[Implicit state machines](state-machines.md) gives the explicit statechart of every implicit state machine in the firmware and the setup page, with verdicts, protections to keep and the refactor plan (TICKET-224).
