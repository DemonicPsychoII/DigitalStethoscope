# Time, TLS and FHIR review — 2 November 2026

Andreas Summerer reviewed the architecture and design of SNTP time synchronization, TLS 1.3 transport
and FHIR delivery with Nico on 2 November 2026, 10:30–11:30. The basis was the presentation
*Digital Stethoscope · Uhrzeit, TLS 1.3 und FHIR*, version 9, built from the open design stack
([#99](https://github.com/DemonicPsychoII/DigitalStethoscope/pull/99),
[#100](https://github.com/DemonicPsychoII/DigitalStethoscope/pull/100),
[#101](https://github.com/DemonicPsychoII/DigitalStethoscope/pull/101)). Nico recorded the review notes,
then classified and resolved them in the [T3 conversation](t3-thread://v1/d5e44f69-2ecc-4a3e-917b-31a7b084c12b)
on the same day. These are project decisions, not measurements or standards conformity.

## Review notes

1. A measurement lasting more than 1 h makes the time invalid; show a TLS error instead of the time-synchronization error.
2. Calculate how long the internal ESP32 clock stays within tolerance of the NTP time.
3. Hotspot name with the whole MAC address.
4. One server, one URL, one address; every server change needs a new configuration.
5. Examination context: requests wait in Idle; the device cannot choose between requests, so the newest request is the active one.
6. Run SNTP directly before the TLS ClientHello.
7. Flash map.
8. Separate the certificate from the firmware, so a certificate change needs no firmware update.
9. Outlook: keep results that are otherwise lost.
10. Where do the time values come from? Typical time plus safety factor.
11. Four attempts.

## Decisions

1. **SNTP inside every TLS setup.** Each TLS connection setup, both the Idle preparation and a delivery
   reconnect, runs one SNTP exchange immediately before the ClientHello. SNTP shares the setup deadline.
   Reusing an open verified connection sends no ClientHello and needs no SNTP. The separate Idle refresh
   schedule (15 min refresh, 1 h expiry) is removed.
2. **One-hour mapping limit.** The UTC measurement end is derived from a clock anchor at most 1 h away
   from the measurement end, in monotonic time. If the anchor at Stop qualifies, the end is frozen at Stop.
   Otherwise, for example after listening for more than 1 h, the end is frozen from the SNTP anchor of the
   delivery connection setup, before the first request. A result without a qualifying anchor is not sent.
3. **One server error.** `TIME_SYNCHRONIZATION_FAILURE` is removed. A failed SNTP exchange is a failed
   secure connection setup and latches `SERVER_CONNECTION_FAILURE`, also when a result cannot be sent
   for lack of a qualifying anchor. The serial log keeps the precise cause. `SERVER_CONNECTION_FAILURE` takes the freed blue code, one blink; no code was implemented yet, so no enumerator value changes.
4. **Drift calculation instead of an experiment.** The worst-case clock drift is calculated from the
   datasheet crystal tolerance; see [drift calculation](#drift-calculation). It justifies the one-hour limit.
5. **Hotspot name.** The hotspot is called `Stetho-AABBCCDDEEFF`, with all six station MAC bytes in
   upper-case hexadecimal. The FHIR Device identifier uses the same hexadecimal digits.
6. **One server per device.** The device talks to exactly one HTTPS FHIR base URL. It offers no runtime
   server selection or server entry in the portal.
7. **Provisioning image.** Base URL, server certificate and the server keep-alive value are delivered together in a separate
   provisioning image, written to its own flash partition by a separate flash command. A firmware update
   leaves it unchanged; a server or certificate change rewrites only the provisioning image. This replaces
   the build-time embedding of #100 and refines note 4.
8. **Flash layout.** The [STORAGE design](../design/STORAGE/interfaces-and-behavior.md#flash-layout) defines the partition layout including the provisioning partition.
9. **Newest examination request wins.** A new pending request replaces an older pending one. A request
   that arrives while a session context is frozen stays pending for the next examination.
10. **Timing derivation.** Every timing parameter is derived from a measured typical duration and a stated
    safety factor. Until those measurements exist ([TICKET-213](https://nfrie.atlassian.net/browse/TICKET-213)),
    the current values are provisional project decisions.
11. **Four attempts.** P13 keeps four attempts in total. When the ten-second deadline admits only two
    attempts, no extra rule applies.
12. **Outlook only.** Keeping otherwise lost results is a thesis outlook item. The MVP keeps REQ-10:
    terminal failure discards the result.

## Drift calculation

The ESP32-S3-WROOM-1 datasheet shows the in-module crystal as 40 MHz ± 10 ppm in its module
schematic [1]. On the ESP32-S3, Zephyr's kernel time uses the Xtensa CPU cycle counter (CCOUNT), and
the CPU clock comes from the PLL referenced to that 40 MHz crystal [2]. The relative error of the kernel time is
therefore the crystal's relative error. Worst case without a new SNTP exchange:

| Time since the anchor | Maximum drift (10 ppm × t) |
| --- | --- |
| 1 min | 0.6 ms |
| 10 min | 6 ms |
| 1 h | 36 ms |
| 24 h | 864 ms |

The total error of a measurement end is the SNTP exchange uncertainty that Zephyr estimates, plus this
drift over the distance to the anchor. With the one-hour limit the drift share stays at or below 36 ms.
TLS certificate validity is not the binding limit: the device compares its clock with `notBefore` and
`notAfter` of the certificate, a window of months to years. The local HAPI certificate is valid from
17 June 2025 to 25 September 2027 ([TLS design](../design/COMMUNICATION/secure-transport.md#investigation-basis-and-limitations)).
At 10 ppm, one day of error needs about 270 years; only an unset clock fails this check.

Limitations: the datasheet labels the tolerance without stating whether it covers temperature range
and ageing. The calculation assumes the device does not sleep, because a sleep phase would run on
another clock source. Reference measurements remain with
[TICKET-209](https://nfrie.atlassian.net/browse/TICKET-209).

## Applied in

- [SNTP design](../design/COMMUNICATION/time-synchronization.md), [TLS design](../design/COMMUNICATION/secure-transport.md),
  [server communication](../design/COMMUNICATION/server-communication.md) and [COMMUNICATION parameters](../design/COMMUNICATION/parameters.md)
- [STORAGE flash layout](../design/STORAGE/interfaces-and-behavior.md#flash-layout), [feedback catalogue](../design/FEEDBACK/catalogue.md),
  [shared design](../design/system/interfaces-and-behavior.md) and [parameters](../design/system/parameters.md)
- Hotspot name in [`wifi.c`](../coding/app/L1_services/L1_WIFI/wifi.c)

Follow-ups outside this record: the SNTP implementation on `feature/time-synchronization` still uses the
removed Idle refresh and `TIME_SYNCHRONIZATION_FAILURE`; the provisioning partition, image tool and
reader need implementation.

## Sources

[1] Espressif Systems, *ESP32-S3-WROOM-1 & ESP32-S3-WROOM-1U Datasheet*, version 1.8, 2 March 2026,
section 8 *Module Schematics*, <https://documentation.espressif.com/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf>,
accessed 2 November 2026.

[2] The Zephyr Project, Xtensa system timer and ESP32-S3 devicetree, Zephyr source revision
`357467a011cd2557a1a3f0b4be83d817c4addc9b`:
[Kconfig.xtensa](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/drivers/timer/Kconfig.xtensa)
enables the CCOUNT-based system timer by default on Xtensa, and
[esp32s3_common.dtsi](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/dts/xtensa/espressif/esp32s3/esp32s3_common.dtsi)
sets a 240 MHz CPU clock from the PLL with a 40 MHz crystal, accessed 2 November 2026.
