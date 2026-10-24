# MVP setup security risk acceptance

Nico accepted the residual setup-security risk on 24 October 2026 for the intended
research-prototype MVP deployment defined by the [product scope](../spec/product-scope.md).
This is an owner project decision, not a claim of clinical suitability or regulatory conformity.
This acceptance is a known MVP limitation, not an additional system requirement. REQ-12 remains unchanged.

| Exposure | Accepted residual risk |
| --- | --- |
| Plain HTTP on the open hotspot | The clinic Wi-Fi credentials are transmitted without transport confidentiality; a party in radio range can observe them. |
| Unauthenticated `/connect` and `/cancel` forms | A party in radio range can submit setup commands; one associated client and request validation do not authenticate the operator. |
| Unencrypted `wifi/network` flash record | An attacker with access to the stored flash data can recover the credentials. Erasing transient copies does not encrypt the persisted record. |

The owner will revisit this acceptance after the MVP. Planned mitigation work is
TICKET-198 (a per-device hotspot password)
and TICKET-199 (flash encryption).
These are post-MVP backlog items under epic
TICKET-98; the wider outlook is
TICKET-198 through TICKET-207. They are planned mitigations, not implemented controls.
Password protection also requires revisiting REQ-12 and the phone/QR setup flow.

Source: Nico (surname not supplied), *DigitalStethoscope replay stack: round-7 owner
answers*, personal communication, T3 Code, 24 October 2026, authoritative local brief
`C:/Users/nicop/scratch/ds-vmodel-stack/round7/BRIEF.md` (read 24 October 2026).
The exposure description is the accepted project threat model; likelihood and
quantitative risk reduction have not been established by measurement.

Recorded by GPT-6.1-Sol on behalf of Nico running in codex.
