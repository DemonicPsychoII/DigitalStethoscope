/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @defgroup L1_WIFI WIFI
 * @{
 * @file
 * L1 adapter over the Zephyr Wi-Fi driver: station and setup hotspot
 * with DHCP server.
 *
 * Every function does one step and returns its result. Attempt counts,
 * delays and the order of steps belong to L2_COMMUNICATION.
 * Implements Development/system/design/WIFI/interfaces-and-behavior.md.
 */

#ifndef L1_WIFI_H
#define L1_WIFI_H

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include <stdbool.h>
#include <stddef.h>

#include <zephyr/kernel.h>
#include <zephyr/net/wifi.h>

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

#define WIFI_HOTSPOT_ADDRESS "192.168.4.1"               /**< Device address in the setup hotspot; the page is served here. */
#define WIFI_SCAN_LIST_SIZE  (16)                        /**< Strongest distinct networks kept per scan. */
#define WIFI_ADDRESS_SIZE    (sizeof("255.255.255.255")) /**< Text of an IPv4 address with terminator. */

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/** Network name and password, as entered on the setup page. */
struct wifi_network
{
    char name[WIFI_SSID_MAX_LEN + 1];    /**< Network name, 1 to 32 characters. */
    char password[WIFI_PSK_MAX_LEN + 1]; /**< Password, 8 to 64 characters, or "" if open. */
};

/** One network returned by wifi_waitForScanResult(). */
struct wifi_scan_entry
{
    char name[WIFI_SSID_MAX_LEN + 1]; /**< Network name. */
    bool needsPassword;               /**< True if the network needs a password. */
};

/***********************************************************************/
/* GLOBAL CONSTANTS                                                    */
/***********************************************************************/

/***********************************************************************/
/* GLOBAL VARIABLES                                                    */
/***********************************************************************/

/***********************************************************************/
/* GLOBAL FUNCTION PROTOTYPES                                          */
/***********************************************************************/

/**
 * @brief Initialize the Wi-Fi module.
 *
 * Register the Wi-Fi and IPv4 event callbacks. Call once, before any
 * other function of this module.
 *
 * @return 0 on success, or a negative error code.
 */
int wifi_init(void);

/**
 * @brief Check the lengths of a network name and password.
 *
 * @param[in] network Network to check.
 *
 * @return True if both fit the Wi-Fi limits; an empty password means an open network.
 */
bool wifi_isValidNetwork(const struct wifi_network *network);

/**
 * @brief Drain any old disconnect and send a new station connect request.
 *
 * Wait for the result with wifi_waitForConnection(). A new request or
 * wifi_disconnect() drops late events of an earlier request. Disconnect confirmation
 * is bounded to one second; a timeout rejects the new connect request.
 *
 * @param[in] network Network to join.
 *
 * @return 0 if the request was accepted, or a negative error code.
 */
int wifi_connect(const struct wifi_network *network);

/**
 * @brief Wait for the connect result, then for an IPv4 address.
 *
 * After -EAGAIN the request is still pending, so the caller can wait in
 * short slices and do other checks in between.
 *
 * @param[in] timeout Maximum time to wait in this call.
 *
 * @return 0 when online, -EAGAIN if still pending, or the cause of the failure.
 */
int wifi_waitForConnection(k_timeout_t timeout);

/**
 * @brief Disconnect the station and cancel a pending connect request.
 *
 * Late events of the cancelled request are ignored. On error, the driver
 * can still be connecting.
 *
 * @return 0 on success or if already disconnected, or a negative error code.
 */
int wifi_disconnect(void);

/**
 * @brief Report whether the station is connected with an IPv4 address.
 *
 * @return True if the station is connected with an IPv4 address.
 */
bool wifi_isConnected(void);

/**
 * @brief Write the IPv4 address of the station as text, for example "10.0.0.17".
 *
 * @param[out] text Address text; "" on error.
 * @param[in]  size Size of @p text, at least WIFI_ADDRESS_SIZE.
 *
 * @return 0 on success, -ENOTCONN if the station has no address, or -ENOSPC.
 */
int wifi_getAddress(char *text, size_t size);

/**
 * @brief Start a scan for networks and return at once.
 *
 * Collect the result with wifi_waitForScanResult(). A new scan drops late
 * results of an earlier one.
 *
 * @return 0 if the scan started, or a negative error code.
 */
int wifi_startScan(void);

/**
 * @brief Cancel a scan and wait until the driver has stopped it.
 *
 * Late scan results are ignored. A connected station stays connected.
 * On error, the driver can still be scanning.
 *
 * @return 0 when stopped or already idle, otherwise a negative error code.
 */
int wifi_cancelScan(void);

/**
 * @brief Wait for the scan to finish and copy the networks found.
 *
 * Hidden and enterprise (802.1X) networks are left out. Each network name
 * is listed once. After -EAGAIN the scan is still running, so the caller
 * can wait in short slices.
 *
 * @param[out] list      Found networks.
 * @param[in]  listSize Number of entries in @p list.
 * @param[in]  timeout   Maximum time to wait in this call.
 *
 * @return Number of networks written to @p list, -EAGAIN if still running, or an error code.
 */
int wifi_waitForScanResult(struct wifi_scan_entry *list, size_t listSize, k_timeout_t timeout);

/**
 * @brief Open the setup hotspot without a password.
 *
 * Give the hotspot interface its fixed IPv4 address and enable the
 * access point. The station stays usable, so wifi_startScan() and
 * wifi_connect() work while the hotspot is open.
 *
 * @return 0 on success, or a negative error code.
 */
int wifi_startHotspot(void);

/**
 * @brief Close the setup hotspot.
 *
 * On error, the hotspot can still be open.
 *
 * @return 0 on success or if already closed, or a negative error code.
 */
int wifi_stopHotspot(void);

/**
 * @brief Start the DHCP server that gives the phone an address on the hotspot.
 *
 * Call after wifi_startHotspot().
 *
 * @return 0 on success, or a negative error code.
 */
int wifi_startDHCPServer(void);

/**
 * @brief Stop the DHCP server of the hotspot.
 *
 * On error, the server can still be running.
 *
 * @return 0 on success or if already stopped, or a negative error code.
 */
int wifi_stopDHCPServer(void);

#endif /* L1_WIFI_H */

/** @} */
