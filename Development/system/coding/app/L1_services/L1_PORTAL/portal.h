/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @defgroup L1_PORTAL PORTAL
 * @{
 * @file
 * L1 adapter over the Zephyr HTTP server: the Wi-Fi setup page.
 *
 * The page sends requests (connect, rescan, cancel) and polls the status.
 * L2_COMMUNICATION takes the requests, does the Wi-Fi work and publishes
 * the network list and the status for the page.
 * Implements Development/system/design/PORTAL/interfaces-and-behavior.md.
 */

#ifndef L1_PORTAL_H
#define L1_PORTAL_H

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include <stddef.h>

#include <zephyr/kernel.h>

#include "wifi.h"

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/** Status shown on the page. */
enum portal_status
{
    PORTAL_STATUS_SCANNING,       /**< Scan in progress; the list is not ready. */
    PORTAL_STATUS_SELECTING,      /**< List ready; waiting for the user. */
    PORTAL_STATUS_CONNECTING,     /**< Connect request in progress. */
    PORTAL_STATUS_CONNECT_FAILED, /**< Last connect failed; the page shows the cause. */
    PORTAL_STATUS_CONNECTED,      /**< Connected and network saved. */
    PORTAL_STATUS_SAVE_FAILED,    /**< Connected, but the network could not be saved. */
    PORTAL_STATUS_CLOSING,        /**< Setup ends on every closure, including success and Start. */
};

/** Kind of request from the page. */
enum portal_request_type
{
    PORTAL_REQUEST_CONNECT,  /**< Join the network in portal_request.network. */
    PORTAL_REQUEST_RESCAN,   /**< Scan again and publish the new list. */
    PORTAL_REQUEST_CANCEL,   /**< End setup. */
    PORTAL_REQUEST_ACTIVITY, /**< User selected a network or typed; restarts the 5 min timer. */
};

/** Request from the page. */
struct portal_request
{
    enum portal_request_type type; /**< Kind of request. */
    struct wifi_network network;   /**< Network to join, for PORTAL_REQUEST_CONNECT only. */
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
 * @brief Start the HTTP server for the setup page.
 *
 * It listens on the hotspot address only, so call wifi_startHotspot() first.
 *
 * @return 0 on success, or a negative error code.
 */
int portal_start(void);

/**
 * @brief Stop the HTTP server and drop pending requests.
 *
 * Publish PORTAL_STATUS_CLOSING first, so the page can show it before
 * the server stops. After the call, no new request is queued, and unread
 * requests are erased because they can hold a password. On error, the
 * server can still be running.
 *
 * @return 0 only after confirmed socket shutdown or a previously confirmed idle state;
 *         a shutdown-in-progress result still requires bounded confirmation.
 */
int portal_stop(void);

/**
 * @brief Publish the networks shown on the page.
 *
 * @param[in] list  Networks from wifi_waitForScanResult().
 * @param[in] count Number of entries in @p list.
 */
void portal_setNetworks(const struct wifi_scan_entry *list, size_t count);

/**
 * @brief Publish the status shown on the page.
 *
 * @param[in] status New status.
 * @param[in] error  Cause for PORTAL_STATUS_CONNECT_FAILED or PORTAL_STATUS_CLOSING,
 *                   otherwise 0.
 */
void portal_setStatus(enum portal_status status, int error);

/**
 * @brief Publish the device address shown after a successful join.
 *
 * @param[in] address IPv4 address text from wifi_getAddress(), or "".
 */
void portal_setAddress(const char *address);

/**
 * @brief Wait for the next request from the page.
 *
 * Status polls of the page are not requests. The page sends
 * PORTAL_REQUEST_ACTIVITY at most once per second while the user selects
 * or types, so polls never keep setup open.
 *
 * @param[out] request Request. Clear request->network.password after use.
 * @param[in]  timeout Maximum time to wait.
 *
 * @return 0 if a request was received, -EAGAIN if none came within @p timeout.
 */
int portal_waitForRequest(struct portal_request *request, k_timeout_t timeout);

#endif /* L1_PORTAL_H */

/** @} */
