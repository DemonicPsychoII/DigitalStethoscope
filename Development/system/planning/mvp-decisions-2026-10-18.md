# Wi-Fi and portal — decision log, 18 October 2026

> **Superseded in part (19 October 2026):** current Wi-Fi setup, recovery and feedback
> follow the [19 October resolutions](mvp-decisions-2026-10-19.md). Earlier text below
> is historical where it conflicts; unrelated delivery decisions remain separate.

Owner: Nico. Scope: ESP32-S3 Wi-Fi setup and recovery. This records project decisions,
not implemented or hardware-verified behaviour. This save adds only the decision log;
it does not change firmware or synchronize the older repository documents.

## Sources and precedence

- Nico, *Wi-Fi and portal workflow discussion and decisions*, T3 Code project
  conversation, 18 October 2026,
  [conversation](t3-thread://v1/d5e44f69-2ecc-4a3e-917b-31a7b084c12b),
  recorded/accessed 18 October 2026. Primary source: the owner's messages in this conversation.
- Earlier context: Nico's pasted extract from thread
  `1919c5ef-d887-4a12-ad4c-0de034a7e889`, “Zephyr Wi-Fi Communication Interfaces”.
  The original thread was not independently retrieved. Later answers below take precedence.
- Project records: [15 October](mvp-decisions-2026-10-15.md),
  [16 October](mvp-decisions-2026-10-16.md), and
  [detailed design](../design/interfaces-and-behavior.md).
- Visual snapshot: [Pages revision 11](https://homelab-server.tail15fafc.ts.net:8092/p/stethoscope-wifi-workflows/v/11/),
  accessed 18 October 2026. The page shows current behaviour without a decision history.

For Wi-Fi setup, this record supersedes conflicting older statements about a
password-protected hotspot, station Wi-Fi being down throughout Portal, saving before
a verified join, rejecting Start throughout setup, and registration within the Wi-Fi
setup phase. Older documents have not been rewritten by this save. Server delivery
contracts outside the Wi-Fi/portal scope remain separate.

## Confirmed decisions

1. **Entry:** setup runs at boot or in Idle. Read stored credentials first. Without
   credentials, open setup automatically. A button hold of at least **2 s in Idle**
   opens setup, including when already connected and after a prior workflow exit.
2. **Boot join:** use one initial attempt plus three retries: **four attempts total**.
   Wait **5 s after each failure before the next attempt**; no extra delay follows
   the last failure. Confirm the intended network and address assignment. Exhaustion
   shows the error and waits for a 2 s hold in Idle; no automatic portal after 30 s.
3. **Setup order:** open the access point (AP), scan/cache networks, then serve the
   portal. Keep the station interface usable while the AP is open.
4. **Page:** one HTML document with changing views. Hide the password field for an
   open network; show it for a protected network. Keep Connect for either type.
   Back/Cancel in the password or connect form returns to network selection.
5. **Connect request:** queue the request; the browser polls status. Switch to the
   selected network and wait for its assigned address. An old station connection
   does not count as a successful new join. Keep AP/portal available through joining
   and result display.
6. **Scan:** explicit Rescan and implicit rescan after a failed portal join. Publish
   the new cache after **scan-finished**, not a fixed delay. Retry a failed scan with
   **four attempts total**. Exhaustion shows an error; a 2 s hold in Idle retries setup.
7. **Portal join failure:** one submitted join attempt, then show the connection
   error, rescan and return to selection. Do not apply the boot retry budget here.
   Failed input does not replace valid saved credentials.
8. **Settings:** `wifi_readSettings()` and `wifi_storeSettings()` belong in L1.
   Save only after the selected network has joined and received an address. Retry
   saving once: **two save attempts total**. If both fail, **stay connected with
   unsaved credentials and show the save error**. Do not claim saved success or
   destroy the previous valid settings.
9. **Success:** show the success result for **10 s**, then stop AP and portal server.
   Keep the station connected. End the setup workflow, not device operation.
10. **Cancellation:** setup-level Cancel closes AP/page; form-level Cancel returns
    to selection. **No user cancel after Connect submission**, through joining,
    saving and automatic closure. A controller request to start listening is a
    separate interruption and still takes priority.
11. **Inactivity:** close after **5 min without user activity**. Selection, password
    input and Rescan count; status polling does not. Pause the timer during actions
    such as scanning, joining and saving. A closing page tells the user about AP teardown.
12. **Exit cleanup:** keep an established station connection. If a running join has
    already returned success when teardown takes effect, retain it too. Otherwise
    cease Wi-Fi activity, cancel attempts, close AP and stop resource-consuming services.
13. **Listening priority:** before listening/measurement starts, terminate attempts
    and AP/portal activity. Keep an already established station connection. Setup
    and recovery must not interfere with listening. Defer active link recovery
    during listening until Idle.
14. **Link loss:** **four attempts total**, **5 s between failures**. After exhaustion,
    **open setup automatically** when Idle permits it; no button press is needed.
15. **AP-start failure:** show the error; manually retry with a **2 s hold in Idle**.
    This does not use the automatic scan/join retry budget.
16. **Software-detected setup failure:** if an error prevents setup from continuing,
    show/log it, stop setup, release its resources and continue offline. Recoverable
    errors use the selected paths. A later 2 s hold in Idle can retry. A fixed list
    of error codes is not required to settle this design rule.
17. **Phone access:** the hotspot has **no password**. A QR (quick response) code
    opens the ESP32 portal address after the phone joins the hotspot. **Manual
    reconnection to the AP is accepted**; automatic phone recovery is not required.
18. **Lights:** retain the repository light design. On-board RGB (red, green, blue)
    never shows red: Idle is dim steady green; portal is magenta blinking at 0.5 Hz;
    listening is steady blue; measuring is cyan blinking at 1 Hz before 15 s and
    steady afterwards; startup is steady white; analysing/sending is white breathing.
    The separate red button light blinks at 2 Hz on error; serial output gives the
    cause. Short press in Idle acknowledges it. No numeric blink-code scheme.
    Green Idle is not proof of a healthy Wi-Fi link.
19. **Phase boundary:** time synchronization, secure server transport and Device
    registration are deferred to the FHIR (Fast Healthcare Interoperability Resources)
    phase, outside the current Wi-Fi/portal implementation.
20. **Presentation:** separate Overview, State diagram and Flow diagram tabs. Keep
    diagrams simple, state boxes with titles only, one SCANNING state for scans and
    rescans, and one ERROR state whose recovery depends on the cause. Replace WAITING
    with an exit node. The parent controller handles later 2 s holds; exit does not
    shut down the device. The snapshot has six behaviour states: SCANNING, PORTAL,
    CONNECTING, ERROR, CLOSING and CONNECTED. The page shows no decision history.

### Retry summary

| Operation | Total attempts | After exhaustion |
|---|---:|---|
| Saved-network boot join | 4 | Error; manual 2 s hold in Idle |
| Link-loss recovery | 4 | Error; automatic setup in Idle |
| Scan | 4 | Error; manual 2 s hold in Idle |
| Portal-submitted join | 1 | Error; automatic rescan and selection |
| Save after join | 2 | Save error; connected with unsaved credentials |
| AP start | 1 per manual request | Manual retry, or offline if setup cannot continue |

Four attempts includes the initial attempt. These budgets are separate from HTTP
(Hypertext Transfer Protocol) delivery retries.

## Snapshot conventions and implementation follow-through

These details make the published snapshot consistent. They are derived constraints
or implementation conventions, not separately quoted owner answers:

- Apply the normalized **5 s retry gap to scans** too.
- Show a save-warning result for **10 s**, using the same result-exit sequence as success.
- Deliver the closing notice before stopping the server; the browser retains it
  after shutdown. The current snapshot adds no extra 10 s Cancel/timeout delay.
- Retain the magenta portal indication during joining; no separate connecting pattern was selected.
- Serialize teardown and join completion; reject late events after cancellation.
- Finish an in-flight atomic settings write safely before acknowledging teardown.
  The audio-start handshake and its timing need implementation and target verification.

## Discussion summary

This is a curated summary, not a verbatim conversation export.

- The pasted earlier discussion covered event bits versus message queues, blocking
  joins that wait for an address, L1/L2 boundaries, AP/station coexistence, stale
  scans, cancellation, link loss, settings and lights. It did not fix a complete
  C interface or an error-code enumeration.
- Earlier variants included multiple portal pages, a 30 s boot-error display followed
  by automatic setup, breathing/pulsing connection lights, a protected hotspot and
  automatic phone recovery. The confirmed rules above replace these variants.
- Nico clarified “Initial attempt + 3 retries” and selected “Open setup automatically”
  after exhausted link recovery. Boot exhaustion requires manual entry.
- The twelve-question discussion then settled saving failure, AP/scan recovery,
  cancellation levels, retention of a successful link, user inactivity, action pauses,
  closure, listening priority, hotspot access and manual phone reconnection.
- Nico's final software-error clarification was: “if we realise software-side that
  somethign's not right we handle that error”. This settled offline fallback without
  requiring a complete error list before implementation.
- Nico requested a current-only page, matching state/flow behaviour, and simple
  diagrams. Revision 11 uses six states, one rescan loop and matching shared rules.
- The latest instruction limits this save to the decision log on the local Wi-Fi
  implementation feature branch; no pull request or merge is part of this save.

## Evidence and remaining work

The page diagrams were rendered and tabs/downloads checked. This is not firmware or
hardware evidence. Join timeouts, cache capacity, queue limits, specific error codes
and supported network-security types beyond the open/password views were not fixed.
Audio/radio interference, teardown timing, phone behaviour and settings-write handling
still need implementation and target evidence.

Older repository design, requirements and diagrams still need a separate synchronization
change. This log is the current Wi-Fi/portal reference; saving it does not make every
older repository view consistent with it.

Recorded by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
