# Wi-Fi architecture

## Device-independent connection model

A station discovers nearby access points by scanning, selects a network and supplies credentials when its security requires them. Association/authentication establishes the link; the station must then obtain an IP address before IP application traffic can start. Link establishment alone is not address readiness. Failure at either boundary returns a cause for recovery policy. Previously stored credentials can replace interactive selection; scanning may be performed by the driver as part of association. This general model is supported by [1].

SoftAP provisioning uses a temporary access point hosted by the device so another station can deliver the target network's credentials. The pattern fixes neither the provisioning transport nor its authentication and security; an open hotspot is not inherent in it [2].

## Mapping to this device

L1_WIFI owns scan, station association and address readiness, disconnect, and setup-hotspot and address-service operations. It reports operation outcomes; it neither decides retries nor owns the browser page. L2_COMMUNICATION supplies setup and recovery policy under L2_CONTROL's Idle network lease. L1_PORTAL owns the setup page and HTTP requests, and L1_STORAGE owns named persistence.

| View | Editable source | Preview |
| --- | --- | --- |
| General station connection | [station-connection.puml](station-connection.puml) | [SVG](rendered/station_connection.svg) |

The [L2_COMMUNICATION setup workflow](../COMMUNICATION/README.md) maps the general model onto this device. [L1_PORTAL](../PORTAL/README.md) defines the page boundary.

The [secure transport boundary](../COMMUNICATION/secure-transport.md) refines the system allocation of TLS operations to L1_WIFI, separately from the station and provisioning interfaces.

## Sources

[1] Espressif Systems, *Wi-Fi Driver — ESP32-S3*, ESP-IDF Programming Guide v5.4.2, sections “ESP32-S3 Wi-Fi Scan”, “Wi-Fi Station General Scenario” and “IP_EVENT_STA_GOT_IP”, https://docs.espressif.com/projects/esp-idf/en/v5.4.2/esp32s3/api-guides/wifi.html (accessed 24 October 2026).

[2] Espressif Systems, *Wi-Fi Provisioning*, ESP-IDF Programming Guide v5.4.2, section “Provisioning Manager”, https://docs.espressif.com/projects/esp-idf/en/v5.4.2/esp32s3/api-reference/provisioning/wifi_provisioning.html (accessed 24 October 2026).
