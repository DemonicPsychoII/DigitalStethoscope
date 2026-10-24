/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L1_WIFI
 * @{
 * @file
 * Implementation of the WIFI module.
 *
 * Each function does one step; L2_COMMUNICATION decides the order, the
 * attempts and the delays (see architecture/WIFI/wifi-flow.puml). The driver
 * reports its results as net_mgmt events. The event handler only records
 * them, and the wait functions hand them to the caller.
 *
 * Station and hotspot run at the same time, as in the Zephyr sample
 * samples/net/wifi/apsta_mode.
 */

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include "wifi.h"

#include <esp_wifi.h>

#include <ctype.h>
#include <errno.h>
#include <string.h>

#include <zephyr/logging/log.h>
#include <zephyr/net/dhcpv4_server.h>
#include <zephyr/net/net_event.h>
#include <zephyr/net/net_if.h>
#include <zephyr/net/net_ip.h>
#include <zephyr/net/net_mgmt.h>
#include <zephyr/net/wifi_mgmt.h>
#include <zephyr/sys/printk.h>

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

#define WIFI_EVENT_DISCONNECTED BIT(3)

#define WIFI_EVENT_CONNECTED BIT(0) /**< Station associated and IPv4 address assigned. */
#define WIFI_EVENT_FAILED    BIT(1) /**< Access point rejected the connect request. */
#define WIFI_EVENT_SCAN_DONE BIT(2) /**< Scan finished; results are complete. */

#define WIFI_SCAN_CANCEL_TIMEOUT_MS (1000) /**< Longest wait for a running scan to end. */

/* Zephyr link-layer and network-layer events use separate callback masks. */
#define WIFI_LINK_LAYER_EVENTS    (NET_EVENT_WIFI_CONNECT_RESULT | NET_EVENT_WIFI_DISCONNECT_RESULT | NET_EVENT_WIFI_SCAN_RESULT | NET_EVENT_WIFI_SCAN_DONE)
#define WIFI_NETWORK_LAYER_EVENTS (NET_EVENT_IPV4_ADDR_ADD | NET_EVENT_IPV4_ADDR_DEL)

#define WIFI_HOTSPOT_NETMASK    "255.255.255.0"         /**< Hotspot subnet. */
#define WIFI_HOTSPOT_POOL_START (10)                    /**< Last address byte of the first DHCP lease. */
#define WIFI_HOTSPOT_NAME_SIZE  (sizeof("Stetho-XXXX")) /**< Hotspot name with the last two MAC bytes. */

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

static struct net_if *wifi_StationInterface;                      /**< Joins the clinic network. */
static struct net_if *wifi_HotspotInterface;                      /**< Serves the setup hotspot; NULL without AP support. */
static struct net_mgmt_event_callback wifi_LinkLayerCallback;     /**< Connect, disconnect and scan events. */
static struct net_mgmt_event_callback wifi_NetworkLayerCallback;  /**< IPv4 address events. */
static atomic_t wifi_FailureCause;                                /**< Error code of the last rejected connect request. */
static struct wifi_scan_entry wifi_ScanList[WIFI_SCAN_LIST_SIZE]; /**< Written by the event handler during a scan. */
static int wifi_ScanSignalStrength[WIFI_SCAN_LIST_SIZE];
static size_t wifi_ScanCount;            /**< Valid entries in wifi_ScanList. */
static struct k_spinlock wifi_ScanLock;  /**< Protects the scan list and the scan flags. */
static bool wifi_ScanIsRunning;          /**< The driver scans until NET_EVENT_WIFI_SCAN_DONE. */
static bool wifi_ScanResultsAreAccepted; /**< Results belong to the scan the caller waits for. */
static atomic_t wifi_DisconnectIsPending;
static atomic_t wifi_StationIsActive;       /**< A station join is pending or the station is associated. */
static atomic_t wifi_ConnectionIsRequested; /**< Connect and IPv4 events belong to a request of this module. */

K_EVENT_DEFINE(wifi_Events); /**< WIFI_EVENT_* bits shared with the waiting thread. */

/***********************************************************************/
/* LOCAL FUNCTION PROTOTYPES                                           */
/***********************************************************************/

/**
 * @brief Handle Wi-Fi and IPv4 events of the station interface.
 *
 * Runs in the net_mgmt event thread and only updates shared state, so the
 * waiting thread decides what happens next.
 *
 * @param[in] callback Callback that received the event.
 * @param[in] event    Event code.
 * @param[in] iface    Interface that raised the event.
 */
static void wifi_handleEvent(struct net_mgmt_event_callback *callback, uint64_t event, struct net_if *iface);

/**
 * @brief Translate the status of a failed connect result into an error code.
 *
 * @param[in] status Status from NET_EVENT_WIFI_CONNECT_RESULT.
 *
 * @return -EACCES, -ENOENT, -ETIMEDOUT or -ECONNREFUSED.
 */
static int wifi_mapFailure(int status);

/**
 * @brief Add one scan result to the list of the running scan.
 *
 * @param[in] result Result reported by the driver.
 */
static void wifi_addScanResult(const struct wifi_scan_result *result);

/**
 * @brief Tell whether a security type works with a password alone.
 *
 * @param[in] security Security type of a scan result.
 *
 * @return True for open and personal (passphrase) networks.
 */
static bool wifi_isSupportedSecurity(enum wifi_security_type security);

/***********************************************************************/
/* MACROS                                                              */
/***********************************************************************/

LOG_MODULE_REGISTER(wifi, LOG_LEVEL_INF);

/***********************************************************************/
/* GLOBAL FUNCTIONS                                                    */
/***********************************************************************/

int wifi_init(void)
{
    int result = 0;

    wifi_StationInterface = net_if_get_wifi_sta();
    wifi_HotspotInterface = net_if_get_wifi_sap();

    if(wifi_StationInterface == NULL)
    {
        LOG_ERR("No Wi-Fi station interface");

        result = -ENODEV;
    }
    else
    {
        net_mgmt_init_event_callback(&wifi_LinkLayerCallback, wifi_handleEvent, WIFI_LINK_LAYER_EVENTS);
        net_mgmt_add_event_callback(&wifi_LinkLayerCallback);
        net_mgmt_init_event_callback(&wifi_NetworkLayerCallback, wifi_handleEvent, WIFI_NETWORK_LAYER_EVENTS);
        net_mgmt_add_event_callback(&wifi_NetworkLayerCallback);
    }

    return result;
}

bool wifi_isValidNetwork(const struct wifi_network *network)
{
    if(network == NULL)
    {
        return false;
    }

    size_t nameLength = strnlen(network->name, sizeof(network->name));
    size_t passwordLength = strnlen(network->password, sizeof(network->password));

    /* strnlen() equal to the buffer size means the terminator is missing. */
    bool isNameValid = (nameLength != 0U) && (nameLength < sizeof(network->name));
    bool isPasswordValid = (passwordLength == 0U) || ((passwordLength >= WIFI_PSK_MIN_LEN) && (passwordLength < sizeof(network->password)));

    if(passwordLength == WIFI_PSK_MAX_LEN)
    {
        for(size_t index = 0U; index < passwordLength; index++)
        {
            isPasswordValid = isPasswordValid && (isxdigit((unsigned char)network->password[index]) != 0);
        }
    }
    return isNameValid && isPasswordValid;
}

int wifi_connect(const struct wifi_network *network)
{
    int result = -EINVAL;

    if(wifi_isValidNetwork(network))
    {
        size_t passwordLength = strlen(network->password);
        struct wifi_connect_req_params parameters = {
            .ssid = (const uint8_t *)network->name,
            .ssid_length = (uint8_t)strlen(network->name),
            .psk = (const uint8_t *)network->password,
            .psk_length = (uint8_t)passwordLength,
            .security = (passwordLength != 0U) ? WIFI_SECURITY_TYPE_PSK : WIFI_SECURITY_TYPE_NONE,
            .band = WIFI_FREQ_BAND_2_4_GHZ, /* The ESP32-S3 radio has no 5 GHz band. */
            .channel = WIFI_CHANNEL_ANY,
            .mfp = WIFI_MFP_OPTIONAL,
            .timeout = SYS_FOREVER_MS,
        };

        /* Driver events carry no request identity. Drain the old disconnect before rearming. */
        result = wifi_disconnect();
        if(result != 0)
        {
            return result;
        }

        (void)k_event_clear(&wifi_Events, WIFI_EVENT_CONNECTED | WIFI_EVENT_FAILED);
        atomic_set(&wifi_ConnectionIsRequested, 1);
        atomic_set(&wifi_StationIsActive, 1);

        result = net_mgmt(NET_REQUEST_WIFI_CONNECT, wifi_StationInterface, &parameters, sizeof(parameters));

        if(result != 0)
        {
            atomic_set(&wifi_ConnectionIsRequested, 0);
            atomic_set(&wifi_StationIsActive, 0);
            LOG_ERR("Connect request failed (%d)", result);
        }
    }

    return result;
}

int wifi_waitForConnection(k_timeout_t timeout)
{
    int result = -EAGAIN;
    uint32_t events = k_event_wait(&wifi_Events, WIFI_EVENT_CONNECTED | WIFI_EVENT_FAILED, false, timeout);

    if((events & WIFI_EVENT_CONNECTED) != 0U)
    {
        result = 0;
    }
    else if((events & WIFI_EVENT_FAILED) != 0U)
    {
        result = (int)atomic_get(&wifi_FailureCause);
    }
    else
    {
        /* Still pending. */
    }

    return result;
}

int wifi_disconnect(void)
{
    atomic_set(&wifi_ConnectionIsRequested, 0);
    (void)k_event_clear(&wifi_Events, WIFI_EVENT_CONNECTED | WIFI_EVENT_FAILED);
    int result = 0;
    if(atomic_get(&wifi_StationIsActive) != 0)
    {
        (void)k_event_clear(&wifi_Events, WIFI_EVENT_DISCONNECTED);
        atomic_set(&wifi_DisconnectIsPending, 1);
        result = net_mgmt(NET_REQUEST_WIFI_DISCONNECT, wifi_StationInterface, NULL, 0);
        if(result == 0)
        {
            if(k_event_wait(&wifi_Events, WIFI_EVENT_DISCONNECTED, false, K_MSEC(1000)) == 0U)
            {
                result = -ETIMEDOUT;
            }
        }
        else if(result == -EALREADY)
        {
            atomic_set(&wifi_StationIsActive, 0);
            result = 0;
        }
    }
    atomic_set(&wifi_DisconnectIsPending, 0);

    if(result == 0)
    {
        /* The pinned DHCP client can retain its address when stopped while rebinding. */
        const struct net_in_addr *address = net_if_ipv4_get_global_addr(wifi_StationInterface, NET_ADDR_PREFERRED);
        while((address != NULL) && (result == 0))
        {
            struct net_in_addr previousAddress = *address;
            if(!net_if_ipv4_addr_rm(wifi_StationInterface, &previousAddress))
            {
                result = -EIO;
            }
            address = net_if_ipv4_get_global_addr(wifi_StationInterface, NET_ADDR_PREFERRED);
        }
    }

    return result;
}

bool wifi_isConnected(void)
{
    return k_event_test(&wifi_Events, WIFI_EVENT_CONNECTED) != 0U;
}

int wifi_getAddress(char *text, size_t size)
{
    if((text == NULL) || (size == 0U))
    {
        return -EINVAL;
    }

    int result = -ENOTCONN;
    const struct net_in_addr *address = wifi_isConnected() ? net_if_ipv4_get_global_addr(wifi_StationInterface, NET_ADDR_PREFERRED) : NULL;

    text[0] = '\0';

    if(address != NULL)
    {
        if(net_addr_ntop(NET_AF_INET, address, text, size) != NULL)
        {
            result = 0;
        }
        else
        {
            text[0] = '\0';
            result = -ENOSPC;
        }
    }

    return result;
}

int wifi_startScan(void)
{
    k_spinlock_key_t key = k_spin_lock(&wifi_ScanLock);

    if(wifi_ScanIsRunning)
    {
        k_spin_unlock(&wifi_ScanLock, key);
        return -EBUSY;
    }

    (void)k_event_clear(&wifi_Events, WIFI_EVENT_SCAN_DONE);
    wifi_ScanCount = 0;
    wifi_ScanIsRunning = true;
    wifi_ScanResultsAreAccepted = true;

    k_spin_unlock(&wifi_ScanLock, key);

    int result = net_mgmt(NET_REQUEST_WIFI_SCAN, wifi_StationInterface, NULL, 0);

    if(result != 0)
    {
        key = k_spin_lock(&wifi_ScanLock);
        wifi_ScanIsRunning = false;
        wifi_ScanResultsAreAccepted = false;

        k_spin_unlock(&wifi_ScanLock, key);
        LOG_ERR("Scan request failed (%d)", result);
    }

    return result;
}

int wifi_cancelScan(void)
{
    int result = 0;
    k_spinlock_key_t key = k_spin_lock(&wifi_ScanLock);
    bool isRunning = wifi_ScanIsRunning;

    /* Results that arrive from now on are dropped. */
    wifi_ScanResultsAreAccepted = false;

    k_spin_unlock(&wifi_ScanLock, key);

    /* The ESP32 driver cannot abort a scan, so wait for its end. */
    if(isRunning && (k_event_wait(&wifi_Events, WIFI_EVENT_SCAN_DONE, false, K_MSEC(WIFI_SCAN_CANCEL_TIMEOUT_MS)) == 0U))
    {
        LOG_ERR("Scan did not stop within %d ms", WIFI_SCAN_CANCEL_TIMEOUT_MS);

        result = -ETIMEDOUT;
    }

    return result;
}

int wifi_waitForScanResult(struct wifi_scan_entry *list, size_t listSize, k_timeout_t timeout)
{
    int result = -EAGAIN;

    if(k_event_wait(&wifi_Events, WIFI_EVENT_SCAN_DONE, false, timeout) != 0U)
    {
        k_spinlock_key_t key = k_spin_lock(&wifi_ScanLock);
        size_t count = MIN(wifi_ScanCount, listSize);
        bool isAccepted = wifi_ScanResultsAreAccepted;

        (void)memcpy(list, wifi_ScanList, count * sizeof(list[0]));

        wifi_ScanResultsAreAccepted = false;

        k_spin_unlock(&wifi_ScanLock, key);

        if(isAccepted)
        {
            LOG_INF("Scan found %u networks", (unsigned int)count);

            result = (int)count;
        }
        else
        {
            /* Cancelled scan: the list is incomplete. */
            result = -ECANCELED;
        }
    }

    return result;
}

int wifi_startHotspot(void)
{
    int result = 0;
    struct net_in_addr address;
    struct net_in_addr netmask;

    if(wifi_HotspotInterface == NULL)
    {
        result = -ENODEV;
    }
    else if((net_addr_pton(NET_AF_INET, WIFI_HOTSPOT_ADDRESS, &address) != 0) || (net_addr_pton(NET_AF_INET, WIFI_HOTSPOT_NETMASK, &netmask) != 0))
    {
        result = -EINVAL;
    }
    else
    {
        /* A second setup in the same boot finds the address already present. */
        if(net_if_ipv4_addr_lookup(&address, NULL) == NULL)
        {
            if(net_if_ipv4_addr_add(wifi_HotspotInterface, &address, NET_ADDR_MANUAL, 0) == NULL)
            {
                result = -ENOMEM;
            }
            else
            {
                (void)net_if_ipv4_set_netmask_by_addr(wifi_HotspotInterface, &address, &netmask);
                net_if_ipv4_set_gw(wifi_HotspotInterface, &address);
            }
        }
    }

    if(result == 0)
    {
        const uint8_t *hardwareAddress = net_if_get_link_addr(wifi_StationInterface)->addr;
        char name[WIFI_HOTSPOT_NAME_SIZE];

        /* The MAC bytes tell several devices in one room apart. */
        (void)snprintk(name, sizeof(name), "Stetho-%02X%02X", hardwareAddress[4], hardwareAddress[5]);

        struct wifi_connect_req_params parameters = {
            .ssid = (const uint8_t *)name,
            .ssid_length = (uint8_t)strlen(name),
            .security = WIFI_SECURITY_TYPE_NONE, /* The phone joins without a password. */
            .band = WIFI_FREQ_BAND_2_4_GHZ,
            .channel = WIFI_CHANNEL_ANY,
        };

        result = net_mgmt(NET_REQUEST_WIFI_AP_ENABLE, wifi_HotspotInterface, &parameters, sizeof(parameters));

        if(result == 0)
        {
            /* The pinned ESP32 driver hardcodes five clients and lacks AP_CONFIG_PARAM. */
            wifi_config_t hotspotConfiguration;
            if(esp_wifi_get_config(WIFI_IF_AP, &hotspotConfiguration) != ESP_OK)
            {
                result = -EIO;
            }
            else
            {
                hotspotConfiguration.ap.max_connection = 1;
                if(esp_wifi_set_config(WIFI_IF_AP, &hotspotConfiguration) != ESP_OK)
                {
                    result = -EIO;
                }
            }
            (void)memset(&hotspotConfiguration, 0, sizeof(hotspotConfiguration));
        }
        if(result == 0)
        {
            LOG_INF("Hotspot \"%s\" open at %s", name, WIFI_HOTSPOT_ADDRESS);
        }
    }

    return result;
}

int wifi_stopHotspot(void)
{
    int result = 0;

    if(wifi_HotspotInterface != NULL)
    {
        result = net_mgmt(NET_REQUEST_WIFI_AP_DISABLE, wifi_HotspotInterface, NULL, 0);

        if(result == -EALREADY)
        {
            result = 0;
        }
    }

    return result;
}

int wifi_startDHCPServer(void)
{
    int result = -ENODEV;
    struct net_in_addr poolStart;

    if((wifi_HotspotInterface != NULL) && (net_addr_pton(NET_AF_INET, WIFI_HOTSPOT_ADDRESS, &poolStart) == 0))
    {
        poolStart.s4_addr[3] = WIFI_HOTSPOT_POOL_START;

        result = net_dhcpv4_server_start(wifi_HotspotInterface, &poolStart);

        if(result == -EALREADY)
        {
            result = 0;
        }
    }

    return result;
}

int wifi_stopDHCPServer(void)
{
    int result = 0;

    if(wifi_HotspotInterface != NULL)
    {
        result = net_dhcpv4_server_stop(wifi_HotspotInterface);

        if(result == -ENOENT)
        {
            /* Not running. */
            result = 0;
        }
    }

    return result;
}

/***********************************************************************/
/* LOCAL FUNCTIONS                                                     */
/***********************************************************************/

static void wifi_handleEvent(struct net_mgmt_event_callback *callback, uint64_t event, struct net_if *iface)
{
    /* The hotspot interface also reports IPv4 events; only the station counts. */
    if(iface == wifi_StationInterface)
    {
        switch(event)
        {
        case NET_EVENT_WIFI_CONNECT_RESULT:
        {
            const struct wifi_status *status = callback->info;

            if((status->status != 0) && (atomic_get(&wifi_DisconnectIsPending) != 0))
            {
                /* ESP32 reports cancellation before association as a failed connect. */
                atomic_set(&wifi_StationIsActive, 0);
                (void)k_event_post(&wifi_Events, WIFI_EVENT_DISCONNECTED);
            }
            else if((status->status == 0) && (atomic_get(&wifi_ConnectionIsRequested) != 0) &&
                    (net_if_ipv4_get_global_addr(wifi_StationInterface, NET_ADDR_PREFERRED) != NULL))
            {
                (void)k_event_post(&wifi_Events, WIFI_EVENT_CONNECTED);
            }
            else if((status->status != 0) && (atomic_get(&wifi_ConnectionIsRequested) != 0))
            {
                LOG_WRN("Connect rejected (%d)", status->status);
                atomic_set(&wifi_StationIsActive, 0);
                atomic_set(&wifi_ConnectionIsRequested, 0);
                atomic_set(&wifi_FailureCause, wifi_mapFailure(status->status));
                (void)k_event_post(&wifi_Events, WIFI_EVENT_FAILED);
            }

            break;
        }

        case NET_EVENT_WIFI_DISCONNECT_RESULT:
        {
            atomic_set(&wifi_StationIsActive, 0);
            atomic_set(&wifi_ConnectionIsRequested, 0);
            /* Disconnect status carries a reason, including USER_REQUEST (2). */
            (void)k_event_post(&wifi_Events, WIFI_EVENT_DISCONNECTED);
            (void)k_event_clear(&wifi_Events, WIFI_EVENT_CONNECTED);
            break;
        }

        case NET_EVENT_IPV4_ADDR_DEL:
            (void)k_event_clear(&wifi_Events, WIFI_EVENT_CONNECTED);
            break;

        case NET_EVENT_WIFI_SCAN_RESULT:
            wifi_addScanResult(callback->info);
            break;

        case NET_EVENT_WIFI_SCAN_DONE:
        {
            k_spinlock_key_t key = k_spin_lock(&wifi_ScanLock);

            wifi_ScanIsRunning = false;

            (void)k_event_post(&wifi_Events, WIFI_EVENT_SCAN_DONE);
            k_spin_unlock(&wifi_ScanLock, key);
            break;
        }

        case NET_EVENT_IPV4_ADDR_ADD:
            /* Online only with an address. After wifi_disconnect() the address
             * belongs to a cancelled request. */
            if(atomic_get(&wifi_ConnectionIsRequested) != 0)
            {
                (void)k_event_post(&wifi_Events, WIFI_EVENT_CONNECTED);
            }

            break;

        default:
            break;
        }
    }
}

static int wifi_mapFailure(int status)
{
    int cause = -ECONNREFUSED;

    switch(status)
    {
    case WIFI_STATUS_CONN_WRONG_PASSWORD:
        cause = -EACCES;
        break;

    case WIFI_STATUS_CONN_AP_NOT_FOUND:
        cause = -ENOENT;
        break;

    case WIFI_STATUS_CONN_TIMEOUT:
        cause = -ETIMEDOUT;
        break;

    default:
        break;
    }

    return cause;
}

static void wifi_addScanResult(const struct wifi_scan_result *result)
{
    /* Hidden networks have no name to show; enterprise and WEP need more than a password. */
    if((result->ssid_length != 0U) && (result->ssid_length <= WIFI_SSID_MAX_LEN) && wifi_isSupportedSecurity(result->security))
    {
        struct wifi_scan_entry entry = {.needsPassword = (result->security != WIFI_SECURITY_TYPE_NONE)};
        bool isListed = false;

        (void)memcpy(entry.name, result->ssid, result->ssid_length);

        k_spinlock_key_t key = k_spin_lock(&wifi_ScanLock);

        /* Drop results of a cancelled scan. */
        isListed = !wifi_ScanResultsAreAccepted;

        size_t weakestIndex = 0U;
        for(size_t index = 0; (index < wifi_ScanCount) && !isListed; index++)
        {
            isListed = (strcmp(wifi_ScanList[index].name, entry.name) == 0);
            if(isListed && (result->rssi > wifi_ScanSignalStrength[index]))
            {
                wifi_ScanList[index] = entry;
                wifi_ScanSignalStrength[index] = result->rssi;
            }
            if(wifi_ScanSignalStrength[index] < wifi_ScanSignalStrength[weakestIndex])
            {
                weakestIndex = index;
            }
        }
        if(!isListed)
        {
            size_t destination = wifi_ScanCount < WIFI_SCAN_LIST_SIZE ? wifi_ScanCount : weakestIndex;
            if((wifi_ScanCount < WIFI_SCAN_LIST_SIZE) || (result->rssi > wifi_ScanSignalStrength[destination]))
            {
                wifi_ScanList[destination] = entry;
                wifi_ScanSignalStrength[destination] = result->rssi;
                if(wifi_ScanCount < WIFI_SCAN_LIST_SIZE)
                {
                    wifi_ScanCount++;
                }
            }
        }

        k_spin_unlock(&wifi_ScanLock, key);
    }
}

static bool wifi_isSupportedSecurity(enum wifi_security_type security)
{
    bool isSupported = false;

    switch(security)
    {
    case WIFI_SECURITY_TYPE_NONE:
    case WIFI_SECURITY_TYPE_PSK:
        isSupported = true;
        break;

    default:
        break;
    }

    return isSupported;
}

/** @} */
