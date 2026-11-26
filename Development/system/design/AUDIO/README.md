# Audio detailed design

[Interfaces and behavior](interfaces-and-behavior.md) define the `L1_I2S` service boundary, the
`L2_AUDIO` block loop and states, stream configuration and rationale, sizing, Start and Stop order,
fault handling, filter signal flow and BPM coverage of the audio path. The views are PlantUML sources in [puml/](puml/), rendered to
[rendered/](rendered/) and embedded in the document. The
[AUDIO architecture](../../architecture/AUDIO/README.md) defines the responsibilities. The
[audio parameters](parameters.md) P01, P02 and P03 and the cross-module parameter
[P11](../cross-module.md#parameters) hold the values.
