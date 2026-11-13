# Delivery start, Start during sending, cleanup services, result freeze points and filter roles — 13 November 2026

Nico decided on 13 November 2026 in T3 Code
([conversation](t3-thread://v2/ebfb7799-1b91-4733-8204-77deebceece3/e7c027fb-ffa0-4ff4-bf3f-83155f894937))
how to resolve five findings of an audit that compared the architecture and design documents with the
firmware. These are project decisions, not measurements. The file name carries a topic because the
audio decisions of the same day have their own record.

## Decisions

1. **Start during Sending cancels the delivery.** The firmware already behaves this way and Nico accepted
   it. The job ends with DELIVERY_FAILURE, or with SERVER_CONNECTION_FAILURE when its UTC measurement end
   was never frozen, and the result is lost. Start during Analysing stays Busy. This replaces the Busy
   rejection during sending of the [11 October record](mvp-decisions-2026-10-11.md).
2. **Delivery connection setup starts at job submission.** Nico asked to settle the start point "based on
   code and what's smart". The design now follows the firmware: setup starts when CONTROL submits the
   finalized job, not at Stop in parallel with finalization. The ten-second deadline still runs from
   Stop. No setup is wasted or cancelled when no job is granted, and an eligible retained connection needs
   no setup. The cost is that finalization time is no longer used for connecting.
3. **Seven cleanup services.** The P23 cleanup covers the seven services the firmware stops: time
   synchronization, secure connection, scan, connect request, setup page, DHCP server and hotspot. At most
   five are pending together, so the five-second cleanup pass remains.
4. **Result freeze points.** A delivery freezes the server Device id at job admission. It freezes the UTC
   measurement end at admission when a qualifying clock anchor exists, otherwise once from the first
   delivery connection setup. The Observation is serialized once before the first request.
5. **Filter roles.** The BPM switch position lets the listener hear the filter that prepares the audio for
   automated BPM analysis. Murmur is a separate listening filter estimated to be better for murmur
   detection. BPM analysis always applies the BPM filter, whatever the switch position, and estimates BPM
   while the doctor listens with Raw, Murmur or BPM.

## Applied in

- [System design](../design/system/interfaces-and-behavior.md) and parameters P08 and P13 in the
  [system parameters](../design/system/parameters.md)
- [COMMUNICATION parameters](../design/COMMUNICATION/parameters.md#cleanup-limits-p23),
  [TLS design](../design/COMMUNICATION/secure-transport.md#delivery-budget-boundary) and
  [SNTP design](../design/COMMUNICATION/time-synchronization.md#clock-mapping-and-native-behavior)
- [Product scope](../spec/product-scope.md), VT-09 in the
  [verification catalogue](../testing/specification-verification.md) and the session and measurement views
  of the [system architecture](../architecture/system/README.md)
