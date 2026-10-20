/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @defgroup L1_WIFI WIFI
 * @{
 * @file
 * L1 adapter over the Zephyr Wi-Fi driver: station, setup hotspot with
 * DHCP server, and the stored network credentials.
 *
 * Every function does one step and returns its result. Attempt counts,
 * delays and the order of steps belong to L2_COMMUNICATION.
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

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/** Network name and password, as stored in flash and entered on the setup page. */
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
 * other function of this module. An initialization failure leaves no active work.
 *
 * @return 0 on success, or a negative error code.
 */
int wifi_init(void);

/**
 * @brief Read the stored network from flash.
 *
 * @param[out] network Stored network.
 *
 * @return 0 on success, -ENOENT if no network is stored, or a negative error code.
 */
int wifi_readSettings(struct wifi_network *network);

/**
 * @brief Store the network in flash.
 *
 * The previous record stays valid if the write fails.
 *
 * @param[in] network Network to store.
 *
 * @return 0 on success, or a negative error code.
 */
int wifi_storeSettings(const struct wifi_network *network);

/**
 * @brief Send a connect request for the station and return at once.
 *
 * Wait for the result with wifi_waitForConnection(). A new request or
 * wifi_disconnect() discards late results of an earlier request.
 *
 * @param[in] network Network to join.
 *
 * @return 0 if the request was accepted, or a negative error code.
 */
int wifi_connect(const struct wifi_network *network);

/**
 * @brief Wait for the connect result, then for an IPv4 address.
 *
 * The request stays pending after -EAGAIN, so the caller can wait in
 * short slices and check for other work in between.
 *
 * @param[in] timeout Maximum time to wait in this call.
 *
 * @return 0 when online, -EAGAIN if still pending, or an error code that names the cause.
 */
int wifi_waitForConnection(k_timeout_t timeout);

/**
 * @brief Disconnect the station and cancel a pending connect request.
 *
 * Success confirms completion, including rejection of late callbacks.
 * On error, the caller must not assume that connection work has stopped.
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
 * @brief Start a scan for networks and return at once.
 *
 * Collect the result with wifi_waitForScanResult(). A new scan discards late
 * results of an earlier one. A rejected start leaves no scan pending.
 *
 * @return 0 if the scan started, or a negative error code.
 */
int wifi_startScan(void);

/**
 * @brief Cancel a scan and wait until the driver has stopped its work.
 *
 * A zero result confirms completion and rejection of late scan callbacks.
 * Preserve an established station. On error, scanning may still be active.
 *
 * @return 0 when stopped or already idle, otherwise a negative error code.
 */
int wifi_cancelScan(void);

/**
 * @brief Wait for the scan to finish and copy the networks found.
 *
 * Hidden and enterprise (802.1X) networks are left out. Each network name
 * is listed once. The scan stays running after -EAGAIN, so the caller can
 * wait in short slices.
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
 * Success confirms shutdown. On error, the hotspot may still be active.
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
 * Success confirms shutdown. On error, the server may still be active.
 *
 * @return 0 on success or if already stopped, or a negative error code.
 */
int wifi_stopDHCPServer(void);

#endif /* L1_WIFI_H */

/** @} */
