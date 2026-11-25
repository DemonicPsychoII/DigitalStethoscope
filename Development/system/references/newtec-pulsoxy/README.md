# PulsOxy reference code of NewTec GmbH

This code is by and belongs to NewTec GmbH.

Copyright 2026 NewTec GmbH.

The files are taken unchanged from the PulsOxy project of NewTec GmbH, revision
`e38b98fc8b881af01e23a8f4935567e73d00de28`. They keep their paths in that project.

| File | Content |
|---|---|
| [`lib/FhirService/src/FhirService.h`](lib/FhirService/src/FhirService.h), [`FhirService.cpp`](lib/FhirService/src/FhirService.cpp) | FHIR server communication over HTTP |
| [`lib/FhirService/src/FhirResourceFactory.h`](lib/FhirService/src/FhirResourceFactory.h), [`FhirResourceFactory.cpp`](lib/FhirService/src/FhirResourceFactory.cpp) | Construction of the FHIR resources as JSON |
| [`lib/App_PulsOxy/src/InitState.h`](lib/App_PulsOxy/src/InitState.h), [`InitState.cpp`](lib/App_PulsOxy/src/InitState.cpp) | Initialization: Wi-Fi connection and registration at the FHIR server |
| [`lib/App_PulsOxy/src/MeasuringState.h`](lib/App_PulsOxy/src/MeasuringState.h), [`MeasuringState.cpp`](lib/App_PulsOxy/src/MeasuringState.cpp) | Measurement and sending of the Observations |

The digital stethoscope does not build or link this code. Two design pages refer to it:
[secure transport](../../design/COMMUNICATION/secure-transport.md) for the trust configuration and
[server communication](../../design/COMMUNICATION/server-communication.md) for the structure of the
FHIR resources.
