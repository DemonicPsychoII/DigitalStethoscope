# Firmware structure and runtime ownership

The firmware consists of layered modules with defined ownership, a fixed set of threads and bounded hand-offs between them. Host execution uses injected data at the same service boundaries as target adapters.

## Static dependency and module map

Each module belongs to one layer with defined inputs, outputs and ownership. Zephyr supplies the hardware drivers. The [software components view](puml/software-components.puml) ([SVG](rendered/software_components.svg)) shows the modules and their dependencies.

- **L0 is Zephyr:** drivers, DMA, interrupts and the devicetree overlay. No project code.
- **L1 adapters** call Zephyr driver APIs directly: `L1_I2S` (microphone RX and DAC TX),
  `L1_WIFI` (station, scan, hotspot, DHCP, TLS transport and time synchronization), `L1_PORTAL` (HTTP server of the Wi-Fi setup page; [boundary](../PORTAL/README.md)),
  `L1_STORAGE` (named records in flash through Zephyr settings and the read-only server profile image),
  `L1_PHYSICALINTERFACE` (Start/Stop button, filter switch, potentiometer, lights).
- **L1 libraries** are pure C with no RTOS, filesystem, UI or network includes: `L1_FILTER`,
  `L1_BPM`, `L1_FHIR`. They hold no shared state; each caller owns its instances.
- **L2 orchestrates:** `L2_CONTROL`, `L2_AUDIO`, `L2_COMMUNICATION`, `L2_SHELL`. Only `L2_CONTROL`
  writes mode state. The other L2 modules receive commands or snapshots from `L2_CONTROL` and report
  back through events; `L2_SHELL` reaches services only through `L2_CONTROL`. `L2_SHELL` is a development
  aid on the serial port; the operator does not use it. The setup page is the
  exception: `L2_COMMUNICATION` owns the setup workflow and reads the page requests itself, while
  `L2_CONTROL` sends it the setup hold and listening start/stop.

Calls go downward; worker completion and health notifications are events sent to `L2_CONTROL`, not direct writes into application state. `MONITOR` observes bounded counters and events without calling arbitrary module APIs.

| Responsibility | Module | Owns / writes | Inputs | Outputs |
|---|---|---|---|---|
| Physical input | `L1_PHYSICALINTERFACE` | debounce and contact state | ISR notices, GPIO and ADC samples | typed control events to `L2_CONTROL`, stable-state reconciliation |
| Control | `L2_CONTROL` | settings, workflow state, generation counter for stale completions, measurement point | control, completion and health events | control dispatch, state snapshots, session-tagged commands, network lease |
| Audio transport | `L2_AUDIO` over `L1_I2S` | `L1_I2S`: RX and TX block pools; `L2_AUDIO`: source generation, transport progress | microphone blocks, start and stop commands | normalized audio blocks, analysis fan-out, TX submission |
| Listening | `L2_AUDIO` with `L1_FILTER` | listening filter instances and transition state | audio block, command snapshot | saturating mono output, levels and clipping |
| BPM analysis | `L2_AUDIO` BPM worker with `L1_FILTER`, `L1_BPM` | worker: session identity, gap detection; `L1_BPM` state: analysis window, estimates, coverage, aggregation | original-rate blocks and session markers | validity updates, cancellation or immutable measurement result |
| Indication | `L2_CONTROL`; LEDs via `L1_PHYSICALINTERFACE` | selected status or error; LED pattern state | workflow state and latched errors | feedback code to `L1_PHYSICALINTERFACE`, LED patterns |
| Shell | `L2_SHELL` | shell state | state snapshot | shell output, control requests |
| Network | `L2_COMMUNICATION` with `L1_FHIR`, `L1_WIFI`, `L1_PORTAL`, `L1_STORAGE` | frozen job, connection, outcome | result, configuration and Idle lease | serialized Observation, delivery outcome, lease-release acknowledgement |
| Monitoring | `MONITOR` | anomaly counters, health evidence | worker checkpoints and counters | fault events, evidence snapshots |

Physical input acquisition and normalization belong to `L1_PHYSICALINTERFACE`. `L2_SHELL` reads state snapshots and status indication receives feedback codes; neither depends directly on input acquisition. Shell commands and decoded operator actions reach `L2_CONTROL` through the same typed control-event contract.

## Firmware layer structure

L2 owns orchestration and L1 provides hardware and library adapters. `L2_COMMUNICATION` is the only path to server delivery: it uses `L1_FHIR` to serialize the frozen measurement result and passes the payload to `L1_WIFI` under the `L2_CONTROL` lease. It never selects or adds a patient ID; only an examination-supplied reference is reused. `MONITOR` observes delivery. `L2_AUDIO` owns the real-time audio thread and executes audio commands from `L2_CONTROL`, which is the single writer of mode state.

## Threads and hand-offs

The `L2_AUDIO` audio thread, `L2_CONTROL`, the `L2_AUDIO` BPM worker and `L2_COMMUNICATION` run on dedicated threads with decreasing priority in that order, and interrupt handlers signal deferred work rather than processing events in interrupt context. `L1_PHYSICALINTERFACE` handles input and lights as short, bounded work items on the Zephyr system work queue, which runs above the audio thread. The [threads view](puml/runtime-ownership.puml) ([SVG](rendered/runtime_ownership.svg)) shows the workers and their interactions.

Every hand-off between workers is bounded and has its own rule for a receiver that falls behind. Values are copied; handles point into a bounded pool.

| Hand-off | From | To | Carries | Receiver falls behind |
|---|---|---|---|---|
| Control events | `L1_PHYSICALINTERFACE` input, `L2_SHELL` | `L2_CONTROL` | values | stable values are reconciled; transient actions are rejected and reported |
| Audio command | `L2_CONTROL` | `L2_AUDIO` audio thread | values, including session begin and end | a full queue refuses the command; `L2_CONTROL` keeps its previous state |
| Analysis blocks | `L2_AUDIO` audio thread | `L2_AUDIO` BPM worker | copied payloads and handles, session begin and end markers in stream order | the gap is marked and the analysis window reset; a session marker is never dropped; listening continues |
| Results, completion and faults | `L2_AUDIO` audio thread and BPM worker | `L2_CONTROL` | values | posted without waiting; a BPM validity update may be dropped, a session outcome or fault is never dropped |
| State snapshot | `L2_CONTROL` | `L2_SHELL` | value copy | the latest snapshot wins |
| Listening and setup request | `L2_CONTROL` | `L2_COMMUNICATION` | values | the latest Start or Stop wins; the release is confirmed through a synchronized stopped state |
| Delivery job | `L2_CONTROL` | `L2_COMMUNICATION` | value copy | a job is admitted only while no other job is pending; a refused job is not queued |
| Wi-Fi feedback and delivery outcome | `L2_COMMUNICATION` | `L2_CONTROL` | values | Wi-Fi feedback without a free queue slot is dropped and logged; the delivery outcome stays readable as the latest value |
| Setup page requests | `L1_PORTAL` | `L2_COMMUNICATION` | values | a full queue refuses the request |

For the delivery job, a terminal failure retains only redacted outcome metadata with no retry queue. The completed measurement is discarded and server recovery does not resend it ([REQ-10](../../requirements/system-requirements.md#req-10)).

## Buffer ownership and blocking rules

`L1_I2S` owns the RX and TX block pools, `L2_AUDIO` borrows their blocks, and pool handles do not escape without a defined lifetime. Listening consumes the current transport block synchronously. BPM analysis receives copied blocks decoupled from the RX DMA pool so a stalled analysis worker cannot pin RX buffers. The [AUDIO architecture](../AUDIO/README.md) defines the block ownership of the audio path, and the [listening filter and BPM analysis architecture](../AUDIO/audio-processing.md) the two signal paths.

DSP state is worker-local. Settings and snapshots are bounded copies; no lock spans an I2S wait, an SPI transfer, a flash write or a TLS operation.
Queues carry bounded values or handles rather than unbounded audio payloads. The audio path never
waits when it enqueues.

## Listening and network lease

Active network work and live listening use an exclusive `L2_CONTROL` lease. An established station association stays active during listening, while setup, reconnect and delivery jobs do not run. Start during Wi-Fi setup requests safe teardown before audio, and `L2_CONTROL` stops audio before granting the network lease. Start during analysis is rejected Busy without cancellation or queuing. Start during sending cancels the delivery job. A fresh Start after release primes and starts audio.
If release cannot be confirmed, audio remains stopped and the device indicates the cause. As an exception under [REQ-13](../../requirements/system-requirements.md#req-13), after a failed network-service stop or a failed cancellation of the time synchronization `L2_COMMUNICATION` latches the Wi-Fi cleanup failure, disables network work until restart and releases audio.

Start cancels pending time synchronization before audio, and time or server-connection failures preserve offline listening. The [COMMUNICATION architecture](../COMMUNICATION/README.md) defines the setup workflow and its teardown, and the [feedback ground rules](feedback-principles.md) define fault containment.
