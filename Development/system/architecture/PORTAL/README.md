# PORTAL architecture

L1_PORTAL owns the HTTP server and page. It validates and queues typed Connect, Rescan, Cancel and Activity requests for L2_COMMUNICATION, and exposes its published status, network list, cause and station address. COMMUNICATION owns setup/retries and persistence sequencing; L1_WIFI owns radio/address operations. PORTAL never joins networks or saves credentials. These are project boundary decisions derived from REQ-12.

| View | Editable source | Preview |
| --- | --- | --- |
| Page/controller boundary sequence | [portal-boundary.puml](portal-boundary.puml) | [SVG](rendered/portal_boundary.svg) |

[COMMUNICATION](../COMMUNICATION/README.md) defines the setup workflow. Detailed design defines the page views, transitions, endpoint table, status format and parameter values.
