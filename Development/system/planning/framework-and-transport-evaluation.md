# Framework and transport evaluation — 2026-10-07 feedback

## Recommendation for the next discussion

Retain Zephyr for the MVP unless the remaining on-target audio/network checks
expose a concrete blocker. ESP-IDF is Espressif's native framework and offers
vendor examples and APIs directly; Zephyr offers the kernel, portable device
APIs, networking and existing project integration. Zephyr's Espressif HAL module
uses vendor support, but this does **not** make arbitrary ESP-IDF application
components drop-in Zephyr libraries. A framework migration would also require
reworking device configuration, synchronization, networking and verification.

Use HTTPS for BPM/FHIR delivery. The evaluation already contains verified TLS;
switching to HTTP would remove transport confidentiality and server authentication
without addressing the remaining application-level delivery verification work.
Do not transmit patient-linked results over an unprotected HTTP connection.

This is a source-backed feasibility assessment, not a fresh hardware qualification
or a measured development-time estimate. Homelab research could not be accessed
(SSH public-key authentication failed); official documentation and repository
evidence were inspected directly instead.

## ESP32-S3 and component support

The project pins Zephyr `357467a011cd2557a1a3f0b4be83d817c4addc9b`, the
`esp32s3_devkitc/esp32s3/procpu` board and an Xtensa ESP32-S3 toolchain in
[toolchain.json](../testing/ci/toolchain.json). Documentation for `latest` describes
upstream capabilities; the pinned build, overlay and target tests determine what
works here. Optional peripherals are beyond the MVP even where evaluation code
already supports them.

| Component / capability | Existing integration | Evidence and remaining work |
|---|---|---|
| ESP32-S3 N16R8 | Zephyr board, Espressif HAL, external RAM configuration | Existing build records; validate timing and RAM use on the exact release image. |
| INMP441 | ESP32 I2S RX + DMA; application normalizes 24-bit samples in 32-bit slots | No dedicated microphone driver is needed for this fixed-format I2S source. Historical T07 physical response passed; repeat on the current image. |
| PCM5102A | ESP32 I2S TX; fixed-function DAC configured through wiring | No register-control driver is needed for the wired operating mode. Successful TX alone does not prove analog/headphone output; T08/T09 remain physical verification work. |
| Buttons, switches, LED | Zephyr GPIO; application debounce and switch decoding | Existing adapters. Fitted switch/contact coverage still needs the protocol's physical checks. |
| Potentiometer | Zephyr ADC | Existing adapter and historical physical sweep; confirm calibration/volume behavior on current image. |
| ILI9341 display (optional) | `ilitek,ili9341`, MIPI DBI over SPI | Existing upstream driver and overlay; redraw interference with audio must be checked. |
| XPT2046 touch (optional) | `xptek,xpt2046`, Zephyr input subsystem | Existing driver and callback integration; coordinates and event behavior need acceptance testing. |
| SD card (optional) | `zephyr,sdhc-spi-slot`, `zephyr,sdmmc-disk`, disk access + FatFs | Existing mount probe. Mounting is not a complete fixture-streaming implementation; test shared-SPI contention and removal/error paths. |
| Backlight (optional) | Zephyr PWM | Existing adapter; tied to optional display. |
| Headphone amplifier | External analog stage | No software driver assumed; select/verify gain, output limits and load behavior. |
| Wi-Fi + HTTP/HTTPS client | Zephyr Wi-Fi, DHCP, DNS, BSD-style sockets, TLS via Mbed TLS | Existing optional network configuration and FHIR sender. Requires target AP/DNS/time/certificate/server tests. The device is a client, not an embedded web server. |

See the maintained [overlay](../coding/bringup-zephyr/boards/esp32s3_devkitc_procpu.overlay),
[configuration](../coding/bringup-zephyr/prj.conf),
[hardware evidence](../coding/bringup-zephyr/evidence/hardware-results.json) and
[test protocol](../coding/bringup-zephyr/TEST-PROTOCOL.md). Historical passes are
keyed to older firmware and must not be presented as current-head acceptance.

## Integrating external libraries

| Library kind | Expected effort | Conditions / likely porting work |
|---|---|---|
| Pure C algorithm library | Low when dependencies are small | Add sources/includes using CMake; cross-compile for Xtensa, check libc/math calls, allocation, licensing and bounded execution. The project's pure-C DSP and FHIR serialization already demonstrate this approach. |
| Portable C++ library | Low to moderate for a restricted dependency set | Enable `CONFIG_CPP`; choose the required C++ standard/library implementation. Check STL, exceptions/RTTI, heap use, startup and toolchain support. Zephyr's minimal C++ support is not a full desktop standard library. Keep C interfaces at application boundaries where useful. |
| Library using POSIX, files, sockets or threads | Moderate; dependency-specific | Audit each API against enabled Zephyr support. Adapt thread/synchronization, clock, filesystem and socket assumptions; desktop API availability is not guaranteed. |
| ESP-IDF or Arduino component | Potentially high | Vendor/Arduino initialization, FreeRTOS APIs, event loops, peripheral ownership and build-system dependencies need adapters or replacement. Availability in those ecosystems is not evidence of Zephyr compatibility. |

For any candidate, first make a small pinned-version cross-build and host test,
then measure target RAM/stack and worst-case runtime. Do not promise "no porting"
based only on the library being written in C or C++. Zephyr modules can package
external code with CMake/Kconfig metadata; a small library can simply be linked
into `app`. Avoid introducing a second owner for peripherals already used by Zephyr.

## HTTP versus HTTPS effort

HTTPS carries the same HTTP request/response semantics inside TLS. Wi-Fi, DHCP,
DNS, request serialization, response parsing, timeouts and FHIR acknowledgement/
readback verification are needed for both. HTTPS adds the following work:

| Area | HTTP | HTTPS addition / current project state |
|---|---|---|
| Connection | TCP socket | `IPPROTO_TLS_1_2` socket; existing sender requires peer verification, a CA security tag and hostname verification. |
| Trust | No transport server authentication | Provision trusted CA, use a matching DNS name and plan certificate/CA renewal. Existing CMake can embed a configured CA file. |
| Time | Needed for result timestamps | Correct time also enables certificate validity checks. Existing SNTP integration needs startup and failure validation; ordinary SNTP itself is not authenticated. |
| Resources | TCP and application buffers | TLS heap, handshake CPU/latency, stack and record buffers. `network.conf` currently sets a 65,536-byte TLS heap, 4,096-byte incoming and 2,048-byte outgoing records, and one TLS context; these are configuration values, not measured peak usage. |
| Server compatibility | HTTP endpoint | Match TLS versions, enabled cipher suites, chain and record sizes. Current config enables two ECDHE/AES-128-GCM TLS 1.2 suites; test the actual FHIR server. |
| Verification | Network failures and HTTP errors | Also reject unknown CA, wrong hostname, expired/not-yet-valid certificates; test missing clock/trust, handshake timeout, reconnection and memory pressure. Never fall back silently to HTTP or disable verification. |

Incremental implementation effort is smaller here than in a blank project because
[stetho_network.c](../coding/bringup-zephyr/src/stetho_network.c) and
[network.conf](../coding/bringup-zephyr/network.conf) already implement the TLS path.
The largest remaining uncertainty is provisioning and on-target interoperability,
not the existence of S3 HTTPS support. Network work stays outside live listening;
measure handshake resource use and recovery before accepting that separation.
TLS protects transport; server authorization and correct patient/result association
remain application responsibilities. The current sender's success logging must not
be confused with the proposed acknowledgement-plus-matching-readback contract.

## Preparation checklist

- Present the component table with historical evidence and current verification gaps.
- Demonstrate a pinned network-enabled build; with owner-authorized target access,
  exercise Wi-Fi, DNS, SNTP, valid TLS, certificate rejection and FHIR delivery/readback.
- Record flash, RAM, TLS peak heap/stack and handshake duration on the S3.
- Choose an actual external library only if needed, then demonstrate its dependency
  audit and minimal C/C++ integration rather than promising generic compatibility.
- Show correctly rendered component/deployment-style views and activity workflows;
  label display, touch, SD storage and slower replay as optional beyond the MVP.

## Official sources

- [ESP32-S3 DevKitC Zephyr support](https://docs.zephyrproject.org/latest/boards/espressif/esp32s3_devkitc/doc/index.html)
- [Zephyr sockets and secure sockets](https://docs.zephyrproject.org/latest/connectivity/networking/api/sockets.html)
- [Zephyr C++ support](https://docs.zephyrproject.org/latest/develop/languages/cpp/index.html)
- [Zephyr external modules](https://docs.zephyrproject.org/latest/develop/modules.html)
- [ESP-IDF ESP32-S3 programming guide](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/)
- [Pinned Zephyr source](https://github.com/zephyrproject-rtos/zephyr/tree/357467a011cd2557a1a3f0b4be83d817c4addc9b)
- [PlantUML component syntax](https://plantuml.com/component-diagram) and [activity syntax](https://plantuml.com/activity-diagram-beta)

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
