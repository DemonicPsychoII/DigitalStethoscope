# Time, TLS and FHIR review — 2 November 2026

Andreas Summerer reviewed the architecture and design of SNTP time synchronization, TLS 1.3 transport
and FHIR delivery with Nico on 2 November 2026, 10:30–11:30. The basis was the presentation
*Digital Stethoscope · Uhrzeit, TLS 1.3 und FHIR*, version 9, built from the open design stack
([#99](https://github.com/DemonicPsychoII/DigitalStethoscope/pull/99),
[#100](https://github.com/DemonicPsychoII/DigitalStethoscope/pull/100),
[#101](https://github.com/DemonicPsychoII/DigitalStethoscope/pull/101)). Nico recorded the review notes,
then classified and resolved them in the [T3 conversation](t3-thread://v1/d5e44f69-2ecc-4a3e-917b-31a7b084c12b)
on the same day; a follow-up in the same conversation replaced the fixed one-hour limit by a computed
limit. These are project decisions, not measurements or standards conformity.

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
2. **Computed mapping limit.** The UTC measurement end is derived only from a clock anchor at most
   12.5 h away from it: (1 s − 100 ms) / 20 ppm. 1 s follows the IHE Consistent Time profile [3]; the
   SNTP uncertainty budget of 100 ms is the observed about 50 ms with safety factor 2, and 20 ppm is
   the datasheet tolerance with safety factor 2. An exchange reporting more than 100 ms fails. If the anchor at Stop qualifies, the end is frozen at Stop. Otherwise the end is
   frozen from the SNTP anchor of the delivery connection setup, before the first request. A result
   without a qualifying anchor is not sent. A retained connection is reused for delivery only while its
   handshake anchor still qualifies. This replaces the review's fixed one-hour rule.
3. **One server error.** `TIME_SYNCHRONIZATION_FAILURE` is removed. A failed SNTP exchange is a failed
   secure connection setup and latches `SERVER_CONNECTION_FAILURE`, also when a result cannot be sent
   for lack of a qualifying anchor. The serial log keeps the precise cause. `SERVER_CONNECTION_FAILURE` takes the freed blue code, one blink; no code was implemented yet, so no enumerator value changes.
4. **Drift calculation instead of an experiment.** The worst-case clock drift is calculated from the
   datasheet crystal tolerance; see [drift calculation](#drift-calculation). It sets the mapping limit.
5. **Hotspot name.** The hotspot is called `Stetho-AABBCCDDEEFF`, with all six station MAC bytes in
   upper-case hexadecimal. The FHIR Device identifier uses the same hexadecimal digits.
6. **One server per device.** The device talks to exactly one HTTPS FHIR base URL. It offers no runtime
   server selection or server entry in the portal.
7. **Provisioning image.** Base URL, server certificate and the server keep-alive value are delivered together in a separate
   provisioning image, written to its own flash partition by a separate flash command. A firmware update
   leaves it unchanged; a server or certificate change rewrites only the provisioning image. This replaces
   the build-time embedding of #100 and refines note 4. The image carries a CRC-32 against corruption;
   the MVP uses no signature.
8. **Flash layout.** The [STORAGE design](../design/STORAGE/interfaces-and-behavior.md#flash-layout) uses the whole 16 MB with only the
   partitions in use: the provisioning image in the last 2 MB, settings directly in front of it and the
   application in all remaining flash. Offsets follow from the sizes.
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

The total error of a measurement end is the SNTP exchange uncertainty that Zephyr estimates, plus the
drift over the distance to the anchor. With safety factor 2 the drift rate is 20 ppm, and with the 1 s
maximum deviation the usable distance is `(1 s − uncertainty) / 20 ppm`:

| SNTP uncertainty | Usable distance to the anchor |
| --- | --- |
| 15 ms (demo, 1 November 2026) | about 13.7 h |
| 53 ms (reported by Nico, 2 November 2026) | about 13.2 h |
| **100 ms (budget: about 50 ms × safety factor 2)** | **12.5 h, the design limit** |
| 500 ms | about 6.9 h |

**FHIR.** The limit protects the `effectiveDateTime` and the measurement identity. FHIR R4 asks for
clocks synchronized by NTP/SNTP without a maximum deviation [4]; neither the FHIR data types nor HAPI
document a tolerance. The IHE Consistent Time profile requires a median error of less than one second
and names SNTP sufficient for that [3]. Using 1 s as a worst-case bound is a project decision.

**TLS.** Certificate validity is not the binding limit: the device itself compares its clock with
`notBefore` and `notAfter` of the server certificate, a window of months to years; the server does not
check the device's time. The local HAPI certificate is valid from 17 June 2025 to 25 September 2027
([TLS design](../design/COMMUNICATION/secure-transport.md#investigation-basis-and-limitations)).
At 20 ppm, one day of error needs about 137 years; only an unset clock fails this check. Every TLS
setup applies a fresh SNTP time anyway.

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
- Delivery prerequisites in the [measurement workflow](../architecture/system/measurement-workflow.puml), [session state](../architecture/system/mvp-session-state.puml) and [architecture viewer](../architecture/system/review.html); architecture PRs [#78](https://github.com/DemonicPsychoII/DigitalStethoscope/pull/78), [#80](https://github.com/DemonicPsychoII/DigitalStethoscope/pull/80) and [#81](https://github.com/DemonicPsychoII/DigitalStethoscope/pull/81)

## Follow-ups

| Item | Tracking |
| --- | --- |
| Adapt the SNTP implementation on `feature/time-synchronization` (Idle refresh and `TIME_SYNCHRONIZATION_FAILURE` removed, SNTP before every ClientHello) | [TICKET-180](https://nfrie.atlassian.net/browse/TICKET-180), [#86](https://github.com/DemonicPsychoII/DigitalStethoscope/issues/86) |
| Provisioning partition, image tool and reader | [TICKET-214](https://nfrie.atlassian.net/browse/TICKET-214), [#105](https://github.com/DemonicPsychoII/DigitalStethoscope/issues/105) |
| Reference-clock comparison of the calculated drift | [TICKET-209](https://nfrie.atlassian.net/browse/TICKET-209), [#88](https://github.com/DemonicPsychoII/DigitalStethoscope/issues/88) |
| Timing values from measured typical duration and safety factor, including SNTP in the setup budget | [TICKET-213](https://nfrie.atlassian.net/browse/TICKET-213), [#102](https://github.com/DemonicPsychoII/DigitalStethoscope/issues/102) |
| Outlook: keep results after failed delivery for later sending | [TICKET-215](https://nfrie.atlassian.net/browse/TICKET-215), [#106](https://github.com/DemonicPsychoII/DigitalStethoscope/issues/106) |


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

[3] IHE International, *IHE IT Infrastructure (ITI) Technical Framework*, Revision 20.0, Final Text,
4 August 2023, Volume 1 section 7 *Consistent Time (CT)* and Volume 2 section 3.1.4.1.2 *Maintain Time [ITI-1]*,
<https://profiles.ihe.net/ITI/TF/Volume1/ch-7.html> and <https://profiles.ihe.net/ITI/TF/Volume2/ITI-1.html>,
accessed 2 November 2026.

[4] Health Level Seven International, *FHIR R4 Security*, version 4.0.1, 2019, section 6.1.0, time keeping,
<https://hl7.org/fhir/R4/security.html>, accessed 2 November 2026.
