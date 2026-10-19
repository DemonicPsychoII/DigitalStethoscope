# Standards research for LED indication

**Status: desk research, 19 October 2026.** This note records which standards were checked for the
[status and error catalogue](interfaces-and-behavior.md#status-and-error-catalogue), what they say and
where they changed the design. The standards themselves are paywalled. All statements come from the
secondary sources listed below, not from the standard texts. Check the cited clauses against the purchased
standards before any conformity claim. This note is not a compliance statement; see the
[product scope](../spec/product-scope.md) for the open applicability of standards.

## Question

Which colours, flash rates and patterns do the relevant standards require or recommend for the two LEDs
(RGB status LED, red button LED)?

## Findings

### IEC 60601-1, subclause 7.8.1: colours of indicator lights

- Table 2 gives fixed meanings: **red** = warning, immediate response by the operator required;
  **yellow** = caution, prompt response required; **green** = ready for use; **any other colour** = a
  meaning other than red, yellow or green. [S1]
- Since the 3rd edition (2005) the green and yellow meanings are mandatory ("shall"), not only
  recommended. [S2]
- The rationale refers to IEC 60073: colour alone should not convey important information; use a
  redundant means such as shape, location, sound or marking. [S3]
- Usability guidance (IEC 60601-1-6) names green as a warning indicator as an example of a
  "controversial mapping". [S2]
- Particular standards can replace Table 2 (example: IEC 60601-2-2 for HF surgical equipment). [S2]
- Applies only if the device is ME (medical electrical) equipment under IEC 60601-1. This is not decided.

### IEC 60073: coding principles for indicators

- Two flash rates: **slow flashing f1 = 0.4–0.8 Hz**, **normal flashing f2 = 1.4–2.8 Hz**. If only one
  rate is used, it shall be f2. [S4] [S5]
- Ratio f1:f2 constant per application, at least 1:2.5 and at most 1:5; **1:4 recommended**, for example
  0.5 Hz and 2 Hz. [S4]
- Pulse:pause about 1:1 recommended; limits 2:1 for f1 and 1:2 for f2. [S4]
- Industrial practice: 0.5 Hz / 2 Hz [S6]; 1.75 Hz [S7]; 1.4 Hz [S8].
- No rate above 2.8 Hz is defined. A proposed 4–5 Hz blink is outside the standard.

### IEC 60601-1-8: alarm systems

- IEC 60601-1 7.8.1 points to IEC 60601-1-8 for the colour, flash rate and duty cycle of alarm indicator
  lights. [S3]
- Visual alarm signals are in clause 6.3.2.2; the values are in **Table 2 "Characteristics of alarm
  indicator lights"** (edition 2006 + Amd 1:2012; Table 202 in the 2003 first edition). [S12] [S13]
- Table 2 values: **high priority red, 1.4–2.8 Hz; medium priority yellow, 0.4–0.8 Hz; low priority cyan
  or yellow, constant.** [S9] [S10]
- Duty cycle: Table 2 has a duty-cycle requirement [S3] [S13]. The value (20–60 % on for flashing) is
  **not confirmed** by any source found. The proposed 2 Hz, 250 ms on / 250 ms off (50 %) lies inside
  that range if the value is correct.
- From 4 m the priority of the highest alarm must be visible; from 1 m the specific alarm condition and
  its priority must be legible. [S12]
- Each alarm condition that occurs at the same time must be indicated visually, unless an intelligent
  alarm system suppresses lower-priority signals. [S12]
- Visual information signals shall be perceived as different from visual alarm signals at 1 m. [S11]
  [S12]
- Compliance test conditions: visual acuity 6/6, 30° viewing cone, 100–1500 lx. [S12]
- Applies only if the errors are technical alarm conditions of an alarm system. See the assessment below.

### Is the device ME equipment?

- Commercial electronic stethoscopes are treated as ME equipment under IEC 60601-1. The 3M Littmann 3200
  is a Type B device; its applied parts are the chestpiece with diaphragm and the binaural; it meets
  IEC 60601-1-2 (EMC). [S14] The Eko digital stethoscope (model E6) has a Type BF applied part, is used
  for diagnostic decision support and lists IEC 60601-1 and IEC 60601-1-2. [S15]
- This device has the same function (chestpiece on the patient, heart-rate result for diagnosis). As a
  product it would therefore be ME equipment with the chestpiece as applied part.
- The thesis MVP makes no conformity claim (see the product scope). **Working assumption (confirmed
  19 October):** design the indication as if the device were ME equipment, and treat errors as technical
  alarm conditions under IEC 60601-1-8 with a priority per condition.

### Alarm priorities (IEC 60601-1-8 Table 1)

- Table 1 "Determination of alarm conditions and assignment of priorities" assigns the priority from the
  potential harm if the operator does not respond and from how fast that harm can occur. The priority
  definitions: high = immediate operator response required, medium = prompt operator response required.
  [S11] [S16]
- The cell values below are from memory of the standard and are **not confirmed** by a source:

  | Harm if no response | Immediate onset | Prompt onset | Delayed onset |
  |---|---|---|---|
  | Death or irreversible injury | High | High | Medium |
  | Reversible injury | High | Medium | Low |
  | Minor discomfort or injury | Medium | Low | Low or none |

- Assessment for this device. The device does not monitor or treat; the clinician is present and can use
  another stethoscope. No condition can cause death or irreversible injury.
  - Audio-path faults (audio worker stall, microphone, DAC, control input): the clinician can misjudge or
    miss heart sounds at once, which can delay a finding (reversible) with prompt onset: **Medium**.
  - All other errors (startup, settings, reset, measurement, Wi-Fi, FHIR): the device or the record is not
    available; the clinician sees it before relying on it; the effect is delayed or minor: **Low**.
  - Statuses are information signals, not alarm signals.
- Simultaneous errors: the LEDs show only the highest-priority error. IEC 60601-1-8 permits this only as an
  intelligent alarm system that suppresses lower-priority signals [S12]. Between errors of the same
  priority the catalogue shows the first latched error; the standard asks for each one to be indicated.
- **Gap in the visual signal.** Table 2 gives medium priority as yellow, 0.4–0.8 Hz, and low priority as
  cyan or yellow, constant [S9] [S10]. The catalogue shows every error with the red button LED at 2 Hz,
  which is the high-priority signal. With the confirmed catalogue (no yellow on the RGB LED, one red button
  LED), full alignment with Table 2 is not possible. This is a documented deviation for the MVP, accepted by
  the owner on 19 October.

### Blink codes

- No standard for numeric blink codes was found. Counting limits (at most 6 blinks, 2 s pause) are a design
  choice, kept inside the IEC 60073 f2 rate.

## Influence on the design

| Design decision (catalogue / P22) | Basis | Source |
|---|---|---|
| Green only for Idle; "Input rejected" no longer green | Green = ready for use; green as warning is a controversial mapping | IEC 60601-1 7.8.1 [S1] [S2] |
| No red, yellow or orange on the RGB LED; red only on the button LED for errors | Red = warning, yellow = caution; orange can read as yellow | IEC 60601-1 7.8.1 [S1] |
| FHIR context changed from orange to blue | "Delivery received" (success) must not look like caution | IEC 60601-1 7.8.1 [S1] |
| Context change, settings errors moved from red to white | Red RGB reserved for warning | IEC 60601-1 7.8.1 [S1] |
| Blink code next to the context colour | Colour alone should not carry important information | IEC 60601-1 7.8.1 rationale, IEC 60073 [S3] |
| Blink codes and quick flashes at 2 Hz, 250 ms on / 250 ms off | Normal flashing f2, pulse:pause 1:1; 2 Hz also lies in the high-priority alarm band | IEC 60073 [S4]; IEC 60601-1-8 [S9] |
| Measuring < 15 s: slow blink 0.5 Hz instead of 1 Hz | 1 Hz is in neither band; 0.5 Hz / 2 Hz is the recommended 1:4 pair | IEC 60073 [S4] |
| Proposed 4–5 Hz blink rejected | Above f2 (2.8 Hz) and hard to count | IEC 60073 [S4] |
| Status patterns (steady, slow blink, breathing) differ from the 2 Hz red error blink | Information signals must differ from alarm signals | IEC 60601-1-8 Amd 1 [S11] |
| Breathing 3 s period, Idle dim 20 %, 2 s code pause, ≤ 6 blinks | No standard found; design choice | — |
| Errors halt operation, except the Wi-Fi-only exception; only clearable errors can resume | The error needs the operator to act, so red ("immediate response") fits; Wi-Fi-only errors keep working audio by the owner's decision | IEC 60601-1 7.8.1 [S1]; 19 October decision log |
| Priority column: Medium for audio-path faults, Low for all other errors, Information for statuses | Harm and onset per Table 1 | IEC 60601-1-8 Table 1 [S11] [S16]; ME assessment [S14] [S15] |
| Only the highest-priority error is shown; equal priority shows the first latched | Intelligent alarm system may suppress lower-priority signals | IEC 60601-1-8 6.3.2.2 [S12] |
| Red 2 Hz for all errors, no yellow (documented deviation) | Owner kept the catalogue; Table 2 would need yellow/cyan for medium/low | IEC 60601-1-8 Table 2 [S9] [S10] |
| Input-rejected dimming by at least 50 % | Must be clearly seen at 1 m | IEC 60601-1-8 6.3.2.2 test conditions [S12]; design choice |
| Visibility at 1 m / 4 m, 100–1500 lx, 30° cone (P22) | Test conditions for visual signals | IEC 60601-1-8 6.3.2.2 [S12] |
| RGB LED keeps the context colour during an error; blink code identifies the condition | At 1 m the specific alarm condition must be identifiable | IEC 60601-1-8 6.3.2.2 [S12] |
| Violet (Wi-Fi) and blue (FHIR) status patterns kept as they are | Errors stay distinct through the blink code; status colours carry no alarm information; workflow order also tells them apart (Sending follows Analysing) | IEC 60601-1 7.8.1 rationale [S3]; design choice |

## Open points

1. Read the IEC 60601-1-8 Table 1 cell values and the Table 2 duty-cycle value in the standard text.
   The 50 % on-time of P22 lies inside the usual 20–60 % range if that value is correct.
2. The red 2 Hz signal for medium- and low-priority errors and the equal-priority suppression are
   documented deviations from IEC 60601-1-8 (see "Alarm priorities").
3. Decided 19 October, not open: visibility on the device is assumed adequate; no reset-cause tests and no
   colour-vision checks are planned for the MVP.
5. Clause checks done on 19 October: IEC 60601-1 7.8.1 Table 2 [S1]; IEC 60073 clause 4.2.3 [S4] [S6];
   IEC 60601-1-8 6.3.2.2 and Table 2 [S12] [S13]. Only the duty-cycle value is still unconfirmed.

## Sources

All accessed 19 October 2026. Secondary sources and standard previews; the full standard texts were not
read.

- [S1] NKK Switches, "IEC 60601-1, Edition 3.1 (JIS T 0601-1:2017) compliant", Table 2 quoted:
  <https://www.nkkswitches.com/pdf/NKKMedTech%20Ref.pdf>
- [S2] Elsmar Cove forum, "Medical device warning lights colors" (P. Selvey):
  <https://elsmar.com/elsmarqualityforum/threads/medical-device-warning-lights-colors.63082/>
- [S3] MECA, "Alarm standards cross-reference" (2015):
  <https://60601-1.com/wp-content/uploads/2019/04/meca-alarm-standards-cross-reference-2015-04-01.pdf>
- [S4] PLCtalk forum, EN 60073 clause 4.2.3 quoted:
  <https://www.plctalk.net/forums/threads/e-stop-manual-reset-button.86446/page-2>
- [S5] IEEE P1621 draft standard for user interface elements (December 2002):
  <https://ea-controls.lbl.gov/1621/docs/1621dec1502.pdf>
- [S6] Rockwell Automation, document 140G-IN067 (LED signalling per IEC 60073):
  <https://literature.rockwellautomation.com/idc/groups/literature/documents/in/140g-in067_-mu-p.pdf>
- [S7] IDEC, LD6A signal tower datasheet:
  <https://us.idec.com/idec-us/en/USD/medias/LD6ASeries.pdf>
- [S8] Norstat, signalling catalogue 2019:
  <https://norstat.com/wp-content/uploads/2019/08/2019-Signaling-Catalog-Complete.pdf>
- [S9] JBTH article (received September 2023), table after NBR IEC 60601-1-8:2022:
  <https://jbth.com.br/index.php/JBTH/article/download/322/259/>
- [S10] Elsmar Cove forum, "Light indication":
  <https://elsmar.com/elsmarqualityforum/threads/light-indication.89977/>
- [S11] IEC 60601-1-8:2006/Amd 1:2012 preview (iTeh):
  <https://cdn.standards.iteh.ai/samples/59935/58e3f4a16b774421af85d948685a6ae9/IEC-60601-1-8-2006-Amd-1-2012.pdf>
- [S12] Har-El standards notes, IEC 60601-1-8 clause 6.3.2 "Visual alarm signals":
  <https://standards.har-el.com/Projects/181701/60601-1-8/html/6-3-2-Visual-Generation.htm>
- [S13] Elsmar Cove forum, "About the intelligent alarm system in IEC 60601-1-8" (Table 2 duty-cycle
  testing; Table 202 in the 2003 edition):
  <https://elsmar.com/elsmarqualityforum/threads/about-the-intelligent-alarm-system-in-iec60601-1-8-anaesthetic-systems.46779/>
- [S14] 3M, Littmann Electronic Stethoscope Model 3200 user manual:
  <https://multimedia.3m.com/mws/media/612830O/electronic-stethoscope.pdf>
- [S15] Eko Devices, Eko CORE Digital Attachment and Eko Digital Stethoscope Model E6 manual (FCC filing):
  <https://fcc.report/FCC-ID/2ANB3-E6/4527557.pdf>
- [S16] iTeh catalogue entry, EN 60601-1-8:2007 (priority definitions, Table 1):
  <https://standards.iteh.ai/catalog/standards/clc/d6083c2c-a4a2-4a0d-95dd-da54d0593012/en-60601-1-8-2007>

Created by Claude-Opus-5.5 on behalf of Nico running in T3 Code through Claude Code.
