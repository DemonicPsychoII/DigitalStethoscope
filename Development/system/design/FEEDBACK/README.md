# Feedback detailed design

The [LED/error catalogue](catalogue.md), [P12 and P22 parameters](parameters.md) and [LED indication standards](led-indication-standards.md) define indication behaviour. The [fault-handling view](catalogue.md#fault-handling) separates recovery, indication and Start admission. Architectural fault-containment and ownership rules are in the [system architecture](../../architecture/system/feedback-principles.md).

## LED indication and error handling

`L2_CONTROL` selects status and error indications under the fault-containment rules; the [status and error catalogue](catalogue.md#status-and-error-catalogue) and [feedback parameters](parameters.md) define codes, acknowledgement, priorities and P22 timing values.
