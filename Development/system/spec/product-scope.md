# Product specification

## Purpose and intended use

The digital stethoscope is a research prototype of an electronic stethoscope on an ESP32-S3. An
operator places the chestpiece on a patient and listens to the heart sounds through headphones.
The device measures the heart rate during the examination and sends the result to a FHIR server
in the local network.

The operator is present during use. The device does not continuously monitor or treat a patient.

The product does not include:

- diagnosis,
- classification of sounds by machine learning,
- durable storage of patient audio,
- the development of an enclosure,
- proof of clinical benefit,
- proof of regulatory conformity,
- a claim that one listening filter is superior to another.

## Users and external systems

| Actor or system | Role |
|---|---|
| Operator | Operates the controls, listens through the headphones and reads the status lights. |
| Patient | Sound source at the chestpiece. |
| Phone browser | The operator uses it to select the Wi-Fi network and to enter its password. |
| FHIR server | Server in the local network. It registers the device and stores the heart-rate results. |
| Network and time services | Give the device its Wi-Fi connectivity and the time. |

## Product boundary and external interfaces

The device consists of:

- the reused chestpiece with the microphone coupling,
- the INMP441 microphone,
- the ESP32-S3 microcontroller,
- the Start/Stop button with its red light,
- the 3-position filter switch,
- the volume potentiometer,
- the RGB status light,
- the PCM5102A DAC (digital-to-analog converter) with its line output.

The device ends at the DAC line output. The headphone amplifier and the headphones are external.
The phone, the FHIR server, the network and time services and the test equipment, including the
evaluation computer, are external.

| Interface | Counterpart | Kind |
|---|---|---|
| Sound input | Patient | Sound through the chestpiece to the microphone |
| Audio output | External headphone amplifier | Analog line output of the DAC |
| Start/Stop | Operator | Push button |
| Filter selection | Operator | 3-position switch: Raw, Murmur, BPM |
| Volume | Operator | Potentiometer |
| Status indication | Operator | RGB status light |
| Error indication | Operator | Red light in the button |
| Wi-Fi setup | Phone browser | Open Wi-Fi hotspot of the device with a setup page |
| Result delivery | FHIR server | Wi-Fi and HTTPS; the device checks the server certificate |
| Time | Network time service | Time synchronization over Wi-Fi |
| Serial log | Connected computer | Text log with the cause of each error |

Inside the device the parts connect to the microcontroller through these interface kinds:

| Part | Direction at the ESP32-S3 | Interface kind |
|---|---|---|
| INMP441 microphone | Clock and word select out, samples in | I2S (Inter-IC Sound) |
| PCM5102A DAC | Clock, word select and samples out | I2S |
| Start/Stop button | Input | GPIO (general-purpose input/output) |
| Filter switch | Inputs | GPIO |
| Volume potentiometer | Input | ADC (analog-to-digital converter) |
| Red button light | Output | GPIO |
| RGB status light | Output | WS2812 data line |

## Functions

### Listening

The device is silent after power-on and starts listening when the operator presses Start
([REQ-01](../requirements/system-requirements.md#req-01)). While listening, the operator hears the
heart sounds from the chestpiece ([REQ-02](../requirements/system-requirements.md#req-02)) without
noticeable delay ([REQ-05](../requirements/system-requirements.md#req-05)). The switch selects one
of the listening filters Raw, Murmur and BPM
([REQ-03](../requirements/system-requirements.md#req-03)). The potentiometer sets the volume
([REQ-04](../requirements/system-requirements.md#req-04)).

### Heart-rate measurement

The device determines the heart rate from the microphone audio at its original sample rate. The
measurement always uses its own analysis filter. The selected listening filter and the volume do
not change it.

A session of at least 15 s whose signal meets the validity criteria gives one heart-rate result
([REQ-06](../requirements/system-requirements.md#req-06)). A session that the operator stops
before 15 s gives no result ([REQ-07](../requirements/system-requirements.md#req-07)). A poor
signal gives an error and no heart-rate value
([REQ-08](../requirements/system-requirements.md#req-08)).

### Result delivery

The device registers itself at the FHIR server and keeps this registration across restarts
([REQ-15](../requirements/system-requirements.md#req-15)). With the configured server available,
it sends each valid result to the server over TLS (Transport Layer Security) and checks the
server certificate ([REQ-09](../requirements/system-requirements.md#req-09),
[REQ-11](../requirements/system-requirements.md#req-11)). The result references the registered
device. The device does not select a patient. A
result carries a patient reference only when the server supplies one with a requested examination
([REQ-09](../requirements/system-requirements.md#req-09)). The device repeats a failed delivery a
limited number of times, then shows an error and discards the result
([REQ-10](../requirements/system-requirements.md#req-10)).

Network work waits until listening stops. A Start during a delivery cancels the delivery, and
the result is discarded.

### Wi-Fi setup

Without stored credentials, or after the operator holds the button for 2 s in Idle, the device
opens a Wi-Fi hotspot without a password and serves a setup page. The operator joins
the hotspot with a phone, selects the Wi-Fi network in the browser and enters the password of a
protected network. The device keeps the credentials across restarts
([REQ-12](../requirements/system-requirements.md#req-12),
[REQ-11](../requirements/system-requirements.md#req-11)).

### Fault indication

The RGB status light shows the operating context by its colour. The red button light shows an
error as a counted blink code. The serial log holds the cause
([REQ-14](../requirements/system-requirements.md#req-14)). A fault that concerns only Wi-Fi leaves
working audio untouched. An audio fault mutes the output at once and blocks every input until a
restart ([REQ-13](../requirements/system-requirements.md#req-13)).

## Functions outside the product

The product has one listening mode, Heart. It does not include:

- a display with its backlight,
- touch input,
- SD-card storage of test recordings,
- capture of an audio clip with slower replay, and the speed switch for it,
- Lung mode.

## Standards and regulatory position

The specification covers the functions and the technical behaviour of the device. It contains no
conformity assessment and no clinical evaluation.

Errors are treated as technical alarm conditions with a priority under IEC 60601-1-8 [1]. The
error indication deviates from Table 2 of that standard in colour and flash rate: every error
uses the red button light with a counted blink code at 2 Hz, whatever its priority.

[1] International Electrotechnical Commission, *Medical electrical equipment — Part 1-8: General
requirements for basic safety and essential performance — Collateral standard: General
requirements, tests and guidance for alarm systems in medical electrical equipment and medical
electrical systems*, IEC 60601-1-8:2006+AMD1:2012+AMD2:2020 CSV, edition 2.2, IEC, 2020.
Publication record: <https://webstore.iec.ch/en/publication/67388> (accessed 2026-10-24).

## Terminology

| Term | Meaning |
|---|---|
| Operator | Person who operates the device and listens. |
| Raw | Listening without a band filter. Sample normalization, gain and output saturation still apply. |
| Listening filter | Switch position that the operator selects for the audible output: Raw (no band filter), Murmur (filter estimated to be better for murmur detection) or BPM (the filter of the BPM analysis, so the operator hears what the analysis gets). |
| Analysis filter | The BPM filter. BPM analysis always applies it to its own input, which is taken before the volume control. It is independent of the listening switch. |
| Measurement session | Bounded interval of original-rate audio that is aggregated into one frozen result with a unique identifier. |
| Idle | The device does not listen. The output is muted. Network work is permitted. |
| Live | Microphone blocks are routed to the listening output. |
| Valid BPM | Heart-rate value that meets the estimator and coverage criteria. It carries no clinical confidence and no diagnosis. |
| Source | Origin of an audio signal: the microphone, a synthetic tone or heartbeat, or a licensed recording. Derived data keep the identity of their source. |
| Portal | Setup page that the device serves over its hotspot. |
| MONITOR | Software module for cross-cutting runtime supervision and risk controls. It observes across the layers and is no layer of its own. |
