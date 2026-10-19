# Wi-Fi, portal and feedback alignment — 19 October 2026

Project decisions given by Nico in the [T3 conversation](t3-thread://v1/d5e44f69-2ecc-4a3e-917b-31a7b084c12b),
19 October 2026, recorded/accessed on that date. This is a project decision source,
not evidence of firmware implementation, measured performance or standards conformity.
The [18 October log](mvp-decisions-2026-10-18.md) remains the discussion record;
the amendments below take precedence where they differ.

## Owner resolutions

Nico accepted the conflict-resolution suggestions with these explicit directions:

- For initial scan/AP ordering: “do what makes the most sense here”.
- Retain functioning audio for Wi-Fi-only failures.
- Adopt numeric error blink codes and update the page and log together.
- The newest “Status and error catalogue — draft” table in
  `design/interfaces-and-behavior.md` applies.
- “otherwise continue with all of your suggestions”.

## Current rules and amendments

1. **Initial setup:** scan/cache first, then open the access point (AP) and serve
   the portal. This ordering is the implementation choice delegated above: it
   prepares the list before the phone joins. Do not claim an uninterrupted radio
   connection from this ordering. Explicit and join-failure rescans keep the AP open.
   Retry a failed scan four times total, 5 s between failures. Failure after the
   budget waits for a manual 2 s hold in Idle, which restarts setup from scanning.
2. **Open networks:** the device hotspot has no password. A QR code contains the
   portal address; the phone joins the hotspot first. The selected network may
   also be open; show its password field only when needed. Manual phone rejoin is accepted.
3. **Join and save:** keep the AP available during a portal join. Queue the request
   and poll status. Confirm the selected network and its address before storing
   credentials. Portal join: one attempt; failure shows the cause, rescans and returns
   to selection. Save: two attempts; failure retains the connection with unsaved
   credentials and the previous valid stored record. Show success or save warning
   for 10 s, then close AP/server and retain the station connection.
4. **Boot and recovery:** four join attempts total, 5 s after a failed attempt before
   the next. Boot exhaustion requires a 2 s hold in Idle; link-recovery exhaustion
   opens setup automatically in Idle. AP-start failure requires manual 2 s retry.
   Software errors that prevent continuing setup show/log their cause, release
   setup resources and permit offline operation. HTTP delivery retries remain separate.
5. **Cancel and timeout:** form Back returns to selection; setup Cancel ends setup.
   No user cancel after Connect submission through saving and automatic closure.
   Five minutes of inactivity counts selection, password input and Rescan, excludes
   polling and pauses during operations. Deliver the closing notice before teardown;
   Cancel/timeout adds no extra 10 s delay. Keep an established station; otherwise
   cancel attempts and release Wi-Fi services.
6. **Listening priority:** Start during setup requests safe teardown, then audio starts.
   Preserve an established station association; prohibit setup, reconnect and delivery
   work during listening. Defer link recovery until Idle. Association does not prove
   zero background traffic or absence of audio interference: target evidence is required.
   Serialize late join callbacks against cancellation and finish atomic settings writes safely.
7. **Feedback:** the current [catalogue](../design/interfaces-and-behavior.md#status-and-error-catalogue)
   supersedes the old light table and generic no-blink-code rule. RGB shows context:
   white device, green Idle, cyan audio, violet Wi-Fi, blue FHIR. The red button LED
   uses counted codes at 2 Hz with pauses; serial logs retain the detailed cause.
   Portal is steady violet; connecting/scanning/reconnecting breathes violet;
   connected gives three quick violet flashes, then the current controller status.
   Error acknowledgement and retry are separate; short press never starts setup.
8. **Wi-Fi-only exception:** Wi-Fi errors do not mute or cancel working audio and
   do not block offline Start. Workflow recovery may proceed without acknowledging
   the indication. A 2 s hold in Idle can retry even with a Wi-Fi error latched.
   Other faults follow the catalogue's halt/clear rule, including restart where stated.
9. **Credential-save feedback:** distinguish Wi-Fi credential save failure from
   generic device settings failure. Add `WIFI_SETTINGS_SAVE_FAILURE`, violet,
   two red blinks then pause; short press clears its indication. It retains the
   connection and does not require restart. Generic `SETTINGS_SAVE_FAILURE` remains
   a device-context failure with the catalogue's restart rule.
10. **Scope:** time synchronization, secure server transport and persistent Device
    registration belong to the later FHIR phase. Their eventual product requirements
    remain; they are not prerequisites for Wi-Fi/portal acceptance. Patient selection
    stays outside the device. Keep L1 credential read/store functions and L2 orchestration.

## Alignment and remaining evidence

Update current requirements, design, parameter rows, verification plans, workflow
sources and rendered views. Preserve earlier decision records with supersession
notices. The page remains a current snapshot without a decision history.

The adopted catalogue is a project design, not a claim that standards require these
particular colours, codes or recovery paths. Numeric operation timeouts, queue/cache
limits, supported security variants, teardown timing and radio/audio interference
still require implementation decisions or measurements. No hardware work is performed
by this documentation change. Work remains local on `feature/implement-wifi-service`;
no push, pull request or merge is requested.

## Documentation verification — 19 October 2026

- Changed PlantUML sources render successfully; shared Wi-Fi rule blocks match.
- Local Markdown paths resolve. Downloaded source content matches repository sources
  after line-ending normalization. Repository and published HTML snapshot match.
- Pages revision 12 was opened in the collaborative browser. Overview/State/Flow
  switching, three diagram images, six download links and the full feedback table
  were checked. Desktop and phone-width previews produced no console errors.
- Agent-gate unit tests: 90 passed. The broader static suite stopped because
  `actionlint` is missing. Host tests did not pass: missing local build executables
  (including `gcc`) caused fixture and evaluation-subprocess failures.
- No firmware changes or hardware tests. This evidence verifies documentation,
  not device behaviour. Page: https://homelab-server.tail15fafc.ts.net:8092/p/stethoscope-wifi-workflows/v/12/

Recorded by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
