/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L1_WIFI
 * @{
 * @file
 * Implementation of the WIFI module.
 *
 * References, in the order the features build on each other. The pinned
 * Zephyr is in .ci-workspace/zephyr; its samples match the API exactly,
 * while the web documentation can be newer.
 *
 * 1. Join a network and wait for an IPv4 address
 *    - Wi-Fi management API (connect, disconnect, scan, access point):
 *      https://docs.zephyrproject.org/latest/services/connectivity/networking/api/wifi.html
 *    - Network management events (CONNECT_RESULT, IPV4_ADDR_ADD, callbacks):
 *      https://docs.zephyrproject.org/latest/services/connectivity/networking/api/net_mgmt.html
 *    - Kernel events, to let a thread wait for the event handler:
 *      https://docs.zephyrproject.org/latest/kernel/services/synchronization/events.html
 *    - Small complete example (connect, events, DHCP):
 *      https://github.com/craigpeacock/Zephyr_WiFi
 *    - Try every step by hand first with the Wi-Fi shell
 *      (wifi scan / connect / status, net iface):
 *      https://docs.zephyrproject.org/latest/samples/net/wifi/shell/README.html
 *
 * 2. Open a hotspot for setup while the station stays usable
 *    - Access point and station at the same time, with a DHCP server:
 *      https://docs.zephyrproject.org/latest/samples/net/wifi/apsta_mode/README.html
 *      (code: .ci-workspace/zephyr/samples/net/wifi/apsta_mode/src/main.c)
 *    - DHCPv4 server API:
 *      https://docs.zephyrproject.org/latest/services/connectivity/networking/api/dhcpv4.html
 *
 * 3. Serve a setup page
 *    - HTTP server API (static and dynamic resources, linker section):
 *      https://docs.zephyrproject.org/latest/services/connectivity/networking/api/http_server.html
 *    - HTTP server sample:
 *      https://docs.zephyrproject.org/latest/samples/net/sockets/http_server/README.html
 *
 * 4. Keep the chosen network across reboots
 *    - Settings subsystem (settings_save_one, static handlers):
 *      https://docs.zephyrproject.org/latest/services/storage/settings/index.html
 *    - Zephyr Memory Storage, the flash backend for settings:
 *      https://docs.zephyrproject.org/latest/services/storage/zms/zms.html
 *
 * 5. ESP32-S3 specifics
 *    - Board (flash, PSRAM, Wi-Fi node in the devicetree):
 *      https://docs.zephyrproject.org/latest/boards/espressif/esp32s3_devkitc/doc/index.html
 *    - ESP32 Wi-Fi driver; its Kconfig lists AP/STA mode, buffer counts and
 *      the heap choice (ESP_WIFI_HEAP_SPIRAM):
 *      https://github.com/zephyrproject-rtos/zephyr/tree/main/drivers/wifi/esp32
 *    - Espressif Wi-Fi guide (buffers, AP/STA channel behavior):
 *      https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-guides/wifi.html
 *    - Espressif external RAM (PSRAM) guide:
 *      https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-guides/external-ram.html
 *    - Setting Kconfig values (prj.conf, extra .conf files):
 *      https://docs.zephyrproject.org/latest/build/kconfig/setting.html
 */

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include "wifi.h"

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/***********************************************************************/
/* GLOBAL CONSTANTS                                                    */
/***********************************************************************/

/***********************************************************************/
/* LOCAL CONSTANTS                                                     */
/***********************************************************************/

/***********************************************************************/
/* GLOBAL VARIABLES                                                    */
/***********************************************************************/

/***********************************************************************/
/* LOCAL VARIABLES                                                     */
/***********************************************************************/

/***********************************************************************/
/* LOCAL FUNCTION PROTOTYPES                                           */
/***********************************************************************/

/***********************************************************************/
/* GLOBAL FUNCTIONS                                                    */
/***********************************************************************/

int wifi_init(void)
{
    return 0;
}

/***********************************************************************/
/* LOCAL FUNCTIONS                                                     */
/***********************************************************************/

/** @} */
