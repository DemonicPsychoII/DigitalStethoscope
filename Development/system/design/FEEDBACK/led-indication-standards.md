# Standards research for LED indication

The [status and error catalogue](catalogue.md#status-and-error-catalogue) and
[P22](parameters.md) draw their colour, flash-rate and priority rules from IEC 60601-1, IEC 60073
and IEC 60601-1-8. All clause summaries below come from the secondary sources and standard previews
listed under [Sources](#sources).

Primary standard identification: International Electrotechnical Commission, *Medical electrical equipment — Part 1-8: General requirements for basic safety and essential performance — Collateral standard: General requirements, tests and guidance for alarm systems in medical electrical equipment and medical electrical systems*, IEC 60601-1-8:2006+AMD1:2012+AMD2:2020 CSV, edition 2.2, IEC, 2020. Publication record: <https://webstore.iec.ch/en/publication/67388> (accessed 2026-10-24).

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
- Applies to ME (medical electrical) equipment under IEC 60601-1.

### IEC 60073: coding principles for indicators

- Two flash rates: **slow flashing f1 = 0.4–0.8 Hz**, **normal flashing f2 = 1.4–2.8 Hz**. If only one
  rate is used, it shall be f2. [S4] [S5]
- Ratio f1:f2 constant per application, at least 1:2.5 and at most 1:5; **1:4 recommended**, for example
  0.5 Hz and 2 Hz. [S4]
- Pulse:pause about 1:1 recommended; limits 2:1 for f1 and 1:2 for f2. [S4]
- Industrial practice: 0.5 Hz / 2 Hz [S6]; 1.75 Hz [S7]; 1.4 Hz [S8].
- IEC 60073 defines no rate above 2.8 Hz.

### IEC 60601-1-8: alarm systems

- IEC 60601-1 7.8.1 points to IEC 60601-1-8 for the colour, flash rate and duty cycle of alarm indicator
  lights. [S3]
- Visual alarm signals are in clause 6.3.2.2; the values are in **Table 2 "Characteristics of alarm
  indicator lights"** (consolidated edition 2.2: 2006 + AMD1:2012 + AMD2:2020; Table 202 in the 2003 first edition). [S12] [S13]
- Table 2 values: **high priority red, 1.4–2.8 Hz; medium priority yellow, 0.4–0.8 Hz; low priority cyan
  or yellow, constant.** [S9] [S10]
- Duty cycle: Table 2 specifies a duty-cycle requirement for flashing [S3] [S13]. P22 uses 2 Hz with
  250 ms on and 250 ms off (50 % duty cycle).
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
- This device has the same function (chestpiece on the patient, heart-rate result for diagnosis). Its indication follows the IEC 60601-1 colour rules and the IEC 60601-1-8 priority rules that apply to ME equipment.
- Visual indication treats errors as technical alarm conditions under IEC 60601-1-8, with an assigned
  priority per condition.

### Alarm priorities (IEC 60601-1-8 Table 1)

- Table 1 "Determination of alarm conditions and assignment of priorities" assigns the priority from the
  potential harm if the operator does not respond and from how fast that harm can occur. The priority
  definitions: high = immediate operator response required, medium = prompt operator response required.
  [S11] [S16]
- Priority assignment for this device. The device does not continuously monitor or treat; the
  clinician is present during use and can switch to another stethoscope:
  - Audio-path faults (audio worker stall, microphone, DAC, control input): the clinician can misjudge or
    miss heart sounds at once, which can delay a finding (reversible) with prompt onset: **Medium**.
  - All other errors (startup, settings, reset, measurement, Wi-Fi, FHIR): the device or the record is not
    available; the clinician sees it before relying on it; the effect is delayed or minor: **Low**.
  - Statuses are information signals, not alarm signals.
- Simultaneous errors: the LEDs show only the highest-priority error. IEC 60601-1-8 permits this only as an
  intelligent alarm system that suppresses lower-priority signals [S12]. Between errors of the same
  priority the catalogue shows the first latched error; the standard asks for each one to be indicated.
- **Deviation from Table 2.** Table 2 assigns yellow at 0.4–0.8 Hz to medium priority and steady
  cyan or yellow to low priority [S9] [S10]. Because this hardware uses a single red button LED and
  no yellow on the RGB LED, the catalogue indicates every error with the red button LED at 2 Hz.

### Blink codes

- The cited sources name no standard for numeric blink codes. The counting limits (at most 6 blinks,
  2 s pause) are specific to this design and stay inside the IEC 60073 f2 rate.

## Influence on the design

Context-to-colour mappings (including blue for FHIR and white for device settings) are specific to this design; IEC 60601-1 defines only red, yellow and green.

| Design rule (catalogue / P22) | Basis | Source |
|---|---|---|
| Green only for Idle; "Input rejected" dims the current colour | Green = ready for use; green as warning is a controversial mapping | IEC 60601-1 7.8.1 [S1] [S2] |
| No red, yellow or orange on the RGB LED; red only on the button LED for errors | Red = warning, yellow = caution; orange can read as yellow | IEC 60601-1 7.8.1 [S1] |
| FHIR context is blue | "Delivery received" (success) must not look like caution | IEC 60601-1 7.8.1 [S1] |
| Context-change and settings errors use white | Red RGB reserved for warning | IEC 60601-1 7.8.1 [S1] |
| Blink code next to the context colour | Colour alone should not carry important information | IEC 60601-1 7.8.1 rationale, IEC 60073 [S3] |
| Blink codes and quick flashes at 2 Hz, 250 ms on / 250 ms off | Normal flashing f2, pulse:pause 1:1; 2 Hz also lies in the high-priority alarm band | IEC 60073 [S4]; IEC 60601-1-8 [S9] |
| Measuring < 15 s: slow blink 0.5 Hz | 1 Hz is in neither band; 0.5 Hz / 2 Hz is the recommended 1:4 pair | IEC 60073 [S4] |
| Error codes and status patterns blink at or below 2.8 Hz. The hold acknowledgement is a status overlay at 4 Hz | A blink above f2 (2.8 Hz) is hard to count. The 4 Hz overlay carries no count and does not read as a 2 Hz error code | IEC 60073 [S4] |
| Status patterns (steady, slow blink, breathing) differ from the 2 Hz red error blink | Information signals must differ from alarm signals | IEC 60601-1-8 Amd 1 [S11] |
| Breathing 3 s period, Idle dim 20 %, 2 s code pause, ≤ 6 blinks | Specific to this design | — |
| Errors halt operation, except the Wi-Fi-only exception; only clearable errors can resume | The error needs the operator to act, so red ("immediate response") fits; Wi-Fi-only errors preserve working audio | IEC 60601-1 7.8.1 [S1] |
| Priority column: Medium for audio-path faults, Low for all other errors, Information for statuses | Harm and onset per Table 1 | IEC 60601-1-8 Table 1 [S11] [S16]; ME assessment [S14] [S15] |
| Only the highest-priority error is shown | Intelligent alarm system may suppress lower-priority signals | IEC 60601-1-8 6.3.2.2 [S12] |
| Equal priority shows the first latched | First-latched tie handling (deviation from IEC 60601-1-8) | — |
| Red 2 Hz for all errors, no yellow (deviation from IEC 60601-1-8 Table 2) | This catalogue uses red; Table 2 would need yellow/cyan for medium/low | IEC 60601-1-8 Table 2 [S9] [S10] |
| Input-rejected dimming by at least 50 % | Must be clearly seen at 1 m | IEC 60601-1-8 6.3.2.2 test conditions [S12]; design choice |
| Visibility at 1 m / 4 m, 100–1500 lx, 30° cone (P22) | Test conditions for visual signals | IEC 60601-1-8 6.3.2.2 [S12] |
| RGB LED keeps the context colour during an error; blink code identifies the condition | At 1 m the specific alarm condition must be identifiable | IEC 60601-1-8 6.3.2.2 [S12] |
| Violet (Wi-Fi) and blue (FHIR) status patterns kept as they are | Errors stay distinct through the blink code; status colours carry no alarm information; workflow order also tells them apart (Sending follows Analysing) | IEC 60601-1 7.8.1 rationale [S3]; design choice |

## Sources

Secondary sources and standard previews (accessed 2026-10-19).

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
