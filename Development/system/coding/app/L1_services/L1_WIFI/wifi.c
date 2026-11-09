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
#include "wifi_dns.h"

#include <esp_wifi.h>

#include <ctype.h>
#include <errno.h>
#include <string.h>
#include <time.h>

#include <zephyr/logging/log.h>
#include <zephyr/net/dhcpv4_server.h>
#include <zephyr/net/net_event.h>
#include <zephyr/net/net_if.h>
#include <zephyr/net/net_ip.h>
#include <zephyr/net/net_mgmt.h>
#include <zephyr/net/sntp.h>
#include <zephyr/net/socket.h>
#include <zephyr/net/wifi_mgmt.h>
#include <zephyr/sys/clock.h>
#include <zephyr/sys/printk.h>
#include <zephyr/sys/timeutil.h>

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

#define WIFI_EVENT_DISCONNECTED BIT(3) /**< Wait for terminal disconnect confirmation; confirmation or the caller's deadline ends the wait. */

#define WIFI_EVENT_CONNECTED BIT(0) /**< Wait for association and IPv4; readiness, join failure or the caller's deadline ends the wait. */
#define WIFI_EVENT_FAILED    BIT(1) /**< Wait for a join failure, including disconnect before IPv4; failure, readiness or the caller's deadline ends the wait. */
#define WIFI_EVENT_SCAN_DONE BIT(2) /**< Wait for scan completion or cancellation acknowledgement; SCAN_DONE or the caller's deadline ends the wait. */

#define WIFI_EVENT_TIME_SYNCHRONIZED    BIT(4) /**< Wake time synchronization waiters; the protected state holds the terminal result. */
#define WIFI_EVENT_TIME_SERVER_RESOLVED BIT(5) /**< Wake the time synchronization worker; only DNS has ended, not the synchronization. */

#define WIFI_TIME_SYNCHRONIZATION_STACK_SIZE (2048) /**< Stack of the time synchronization work queue; proposed value pending target measurement. */
#define WIFI_TIME_SYNCHRONIZATION_PRIORITY   (10)   /**< Same preemptive priority as the communication thread that waits for it. */

#define WIFI_TIME_SYNCHRONIZATION_CANCEL_TIMEOUT_MS    (1000)  /**< P23 per-service stop bound. */
#define WIFI_TIME_SYNCHRONIZATION_OPERATION_TIMEOUT_MS (10000) /**< Ends an operation nobody cancels; the caller's setup deadline (P26: 10 s at most) normally ends it first. */
#define WIFI_TIME_SYNCHRONIZATION_POLL_INTERVAL_MS     (100)   /**< Longest worker wait between cancellation checks, well inside the stop bound. */
#define WIFI_SNTP_PORT                                 (123)   /**< P25-SERVER: SNTP over UDP/123. */

#define WIFI_SNTP_HEADER_SIZE          (2)  /**< Leap indicator, version and mode byte, then the stratum byte (RFC 4330 section 4). */
#define WIFI_SNTP_LEAP_INDICATOR_SHIFT (6)  /**< The leap indicator occupies the two most significant bits of the first byte. */
#define WIFI_SNTP_LEAP_INDICATOR_ALARM (3)  /**< Alarm condition: the server clock is not synchronized. */
#define WIFI_SNTP_STRATUM_MINIMUM      (1)  /**< Stratum 0 is kiss-o'-death or unspecified. */
#define WIFI_SNTP_STRATUM_MAXIMUM      (15) /**< Strata 16 to 255 are reserved. */

#define WIFI_SCAN_CANCEL_TIMEOUT_MS (1000) /**< Longest wait for a running scan to end. */

/* Zephyr link-layer and network-layer events use separate callback masks. */
#define WIFI_LINK_LAYER_EVENTS    (NET_EVENT_WIFI_CONNECT_RESULT | NET_EVENT_WIFI_DISCONNECT_RESULT | NET_EVENT_WIFI_SCAN_RESULT | NET_EVENT_WIFI_SCAN_DONE)
#define WIFI_NETWORK_LAYER_EVENTS (NET_EVENT_IPV4_ADDR_ADD | NET_EVENT_IPV4_ADDR_DEL)

#define WIFI_HOTSPOT_NETMASK    "255.255.255.0"                 /**< Hotspot subnet. */
#define WIFI_HOTSPOT_POOL_START (10)                            /**< Last address byte of the first DHCP lease. */
#define WIFI_HOTSPOT_NAME_SIZE  (sizeof("Stetho-XXXXXXXXXXXX")) /**< Hotspot name with all six MAC bytes. */

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/** Lifecycle of the single time synchronization operation. */
enum wifi_time_synchronization_state
{
    WIFI_TIME_SYNCHRONIZATION_IDLE,       /**< Nothing started since boot. */
    WIFI_TIME_SYNCHRONIZATION_PENDING,    /**< Started; no terminal result yet. */
    WIFI_TIME_SYNCHRONIZATION_CANCELLING, /**< Cancellation requested; resources not yet quiescent. */
    WIFI_TIME_SYNCHRONIZATION_COMPLETED,  /**< Terminal result stored; Wait returns it repeatedly. */
};

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

K_EVENT_DEFINE(wifi_Events);                  /**< WIFI_EVENT_* bits shared with the waiting thread. */
K_MUTEX_DEFINE(wifi_TimeSynchronizationLock); /**< Protects the time synchronization state, result and sample. */

static enum wifi_time_synchronization_state wifi_TimeSynchronizationState;
static int wifi_TimeSynchronizationResult;                    /**< Terminal error code; 0 means the sample is valid. */
static struct normalised_time wifi_TimeSynchronizationSample; /**< Valid only when the result is 0. */
static uint32_t wifi_TimeSynchronizationGeneration;           /**< Identifies the accepted operation, so late callbacks of an older one can be ignored. */
static const char *wifi_TimeServerHostname;                   /**< Borrowed from the caller until terminal completion or successful cancellation. */
/**
 * @brief Tell whether an operation is still the pending one.
 * @param[in] generation Operation to check.
 * @return True while it is current and not cancelled; call with wifi_TimeSynchronizationLock held.
 */
static bool wifi_isTimeSynchronizationCurrent(uint32_t generation);

static struct wifi_dns_lookup wifi_TimeServerLookup = {
    .lock = &wifi_TimeSynchronizationLock,
    .events = &wifi_Events,
    .resolvedEvent = WIFI_EVENT_TIME_SERVER_RESOLVED,
    .isCurrent = wifi_isTimeSynchronizationCurrent,
}; /**< Time server lookup; its fields are protected by wifi_TimeSynchronizationLock. */
static bool wifi_TimeSynchronizationIsClaimed; /**< The worker owns the current operation's resources; protected by the lock. */

/* Owned by the time synchronization worker; no other thread touches them. */
static struct sntp_ctx wifi_TimeSynchronizationContext;
static bool wifi_TimeSynchronizationSocketIsOpen; /**< wifi_TimeSynchronizationContext owns an open socket. */

K_THREAD_STACK_DEFINE(wifi_TimeSynchronizationStack, WIFI_TIME_SYNCHRONIZATION_STACK_SIZE);
static struct k_work_q wifi_TimeSynchronizationQueue; /**< Runs the network exchange outside the caller's thread. */
static struct k_work wifi_TimeSynchronizationWork;

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

/** Roll back a partially started hotspot immediately; L2 retains responsibility for failed stops. */
static void wifi_rollbackHotspot(void);

/**
 * @brief Normalize one received SNTP result without applying the clock.
 * @param[in] nativeTime Native result with SNTP uncertainty enabled.
 * @param[out] sample Normalized sample; unchanged on failure.
 * @return 0 on success, or a negative error code.
 */
static int wifi_normalizeTimeSample(const struct sntp_time *nativeTime, struct normalised_time *sample);

/**
 * @brief Run one accepted time synchronization on the dedicated work queue.
 * @param[in] work Work item of the time synchronization queue.
 */
static void wifi_runTimeSynchronization(struct k_work *work);

/**
 * @brief Tell whether the worker may continue an operation.
 * @param[in] generation Operation the worker runs.
 * @return True while that operation is current and not cancelled.
 */
static bool wifi_isTimeSynchronizationAdmitted(uint32_t generation);

/**
 * @brief Resolve one operation's time server without applying time.
 * @param[in] generation Owning operation generation.
 * @param[in] deadline End of the operation.
 * @param[out] address Owned IPv4 address copy; written only on success.
 * @return 0 on success, or a negative error code.
 */
static int wifi_resolveTimeServer(uint32_t generation, k_timepoint_t deadline, struct net_sockaddr_in *address);

/**
 * @brief Exchange one SNTP request with the resolved server.
 * @param[in] generation Owning operation generation.
 * @param[in] deadline End of the operation.
 * @param[in] address Resolved IPv4 server address.
 * @param[out] sample Normalized sample; written only on success.
 * @return 0 on success, or a negative error code.
 */
static int wifi_exchangeTimeSample(uint32_t generation, k_timepoint_t deadline, const struct net_sockaddr_in *address, struct normalised_time *sample);

/**
 * @brief Wait one poll interval for the SNTP response and parse it only from a synchronized server.
 * @param[out] nativeTime Native result; written only on success.
 * @return 0 on success, -ETIMEDOUT if nothing arrived, -EPROTO for a server that is not
 *         synchronized, or another negative error code.
 */
static int wifi_receiveTimeResponse(struct sntp_time *nativeTime);

/**
 * @brief Release the DNS query and SNTP socket the worker owns.
 * @return 0 only when the resources are released and no DNS callback can run, or a negative error code.
 */
static int wifi_releaseTimeSynchronizationResources(void);

/**
 * @brief Publish a quiescent operation's terminal result.
 * @param[in] generation Owning operation generation.
 * @param[in] result Terminal result code; replaced by -ECANCELED once cancellation was requested.
 * @param[in] sample Successful sample; NULL on failure.
 */
static void wifi_publishTimeSynchronizationResult(uint32_t generation, int result, const struct normalised_time *sample);

/***********************************************************************/
/* MACROS                                                              */
/***********************************************************************/

LOG_MODULE_REGISTER(wifi, LOG_LEVEL_INF);

/***********************************************************************/
/* GLOBAL FUNCTIONS                                                    */
/***********************************************************************/

/** Wait for the event mask selected by the owning operation. */
static uint32_t wifi_waitForEvents(uint32_t eventMask, k_timeout_t timeout)
{
    return k_event_wait(&wifi_Events, eventMask, false, timeout);
}

int wifi_init(void)
{
    int result = 0;

    wifi_StationInterface = net_if_get_wifi_sta();
    wifi_HotspotInterface = net_if_get_wifi_sap();

    if(wifi_StationInterface == NULL)
    {
        LOG_ERR("No Wi-Fi station interface");

        result = -ENODEV; /**< Required device interface is unavailable. */
    }
    else
    {
        net_mgmt_init_event_callback(&wifi_LinkLayerCallback, wifi_handleEvent, WIFI_LINK_LAYER_EVENTS);
        net_mgmt_add_event_callback(&wifi_LinkLayerCallback);
        net_mgmt_init_event_callback(&wifi_NetworkLayerCallback, wifi_handleEvent, WIFI_NETWORK_LAYER_EVENTS);
        net_mgmt_add_event_callback(&wifi_NetworkLayerCallback);

        const struct k_work_queue_config queueConfiguration = {
            .name = "wifi_time_synchronization",
        };
        k_work_init(&wifi_TimeSynchronizationWork, wifi_runTimeSynchronization);
        k_work_queue_start(&wifi_TimeSynchronizationQueue,
                           wifi_TimeSynchronizationStack,
                           K_THREAD_STACK_SIZEOF(wifi_TimeSynchronizationStack),
                           WIFI_TIME_SYNCHRONIZATION_PRIORITY,
                           &queueConfiguration);
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
    /* Allow an open network or a passphrase within the supported size range. */
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
    int result = -EINVAL; /**< Invalid argument or unsupported input. */

    if(wifi_isValidNetwork(network))
    {
        size_t passwordLength = strlen(network->password);
        struct wifi_connect_req_params parameters = {
            .ssid = (const uint8_t *)network->name,
            .ssid_length = (uint8_t)strlen(network->name),
            .psk = (const uint8_t *)network->password,
            .psk_length = (uint8_t)passwordLength,
            .security = WIFI_SECURITY_TYPE_NONE,
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

        (void)k_event_clear(&wifi_Events, (WIFI_EVENT_CONNECTED | WIFI_EVENT_FAILED));
        atomic_set(&wifi_ConnectionIsRequested, 1);
        atomic_set(&wifi_StationIsActive, 1);

        if(passwordLength != 0U)
        {
            parameters.security = WIFI_SECURITY_TYPE_PSK;
        }

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
    int result = -EAGAIN; /**< Operation is still pending; try again. */
    uint32_t events = wifi_waitForEvents((WIFI_EVENT_CONNECTED | WIFI_EVENT_FAILED), timeout);

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
    (void)k_event_clear(&wifi_Events, (WIFI_EVENT_CONNECTED | WIFI_EVENT_FAILED));
    int result = 0;
    if(atomic_get(&wifi_StationIsActive) != 0)
    {
        (void)k_event_clear(&wifi_Events, WIFI_EVENT_DISCONNECTED);
        atomic_set(&wifi_DisconnectIsPending, 1);
        result = net_mgmt(NET_REQUEST_WIFI_DISCONNECT, wifi_StationInterface, NULL, 0);
        if(result == 0)
        {
            if(wifi_waitForEvents(WIFI_EVENT_DISCONNECTED, K_MSEC(1000)) == 0U)
            {
                result = -ETIMEDOUT; /**< Operation exceeded its wait deadline. */
            }
        }
        else if(result == -EALREADY) /**< Requested state is already active. */
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
                result = -EIO; /**< Input/output operation failed. */
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
        return -EINVAL; /**< Invalid argument or unsupported input. */
    }

    int result = -ENOTCONN; /**< Station has no usable connection. */
    const struct net_in_addr *address;
    if(wifi_isConnected())
    {
        address = net_if_ipv4_get_global_addr(wifi_StationInterface, NET_ADDR_PREFERRED);
    }
    else
    {
        address = NULL;
    }

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
            result = -ENOSPC; /**< Destination has insufficient space. */
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
        return -EBUSY; /**< Service is busy with another operation. */
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
    if(isRunning && (wifi_waitForEvents(WIFI_EVENT_SCAN_DONE, K_MSEC(WIFI_SCAN_CANCEL_TIMEOUT_MS)) == 0U))
    {
        LOG_ERR("Scan did not stop within %d ms", WIFI_SCAN_CANCEL_TIMEOUT_MS);

        result = -ETIMEDOUT; /**< Operation exceeded its wait deadline. */
    }

    return result;
}

int wifi_waitForScanResult(struct wifi_scan_entry *list, size_t listSize, k_timeout_t timeout)
{
    int result = -EAGAIN; /**< Operation is still pending; try again. */

    if(wifi_waitForEvents(WIFI_EVENT_SCAN_DONE, timeout) != 0U)
    {
        k_spinlock_key_t key = k_spin_lock(&wifi_ScanLock);
        size_t count = MIN(wifi_ScanCount, listSize);
        bool isAccepted = wifi_ScanResultsAreAccepted;

        (void)memcpy(list, wifi_ScanList, count * sizeof(list[0]));

        k_spin_unlock(&wifi_ScanLock, key);

        if(isAccepted)
        {
            LOG_INF("Scan found %u networks", (unsigned int)count);

            result = (int)count;
        }
        else
        {
            /* Cancelled scan: the list is incomplete. */
            result = -ECANCELED; /**< Operation was cancelled. */
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
        result = -ENODEV; /**< Required device interface is unavailable. */
    }
    /* Both hotspot address and netmask must parse before configuring the interface. */
    else if((net_addr_pton(NET_AF_INET, WIFI_HOTSPOT_ADDRESS, &address) != 0) || (net_addr_pton(NET_AF_INET, WIFI_HOTSPOT_NETMASK, &netmask) != 0))
    {
        result = -EINVAL; /**< Invalid argument or unsupported input. */
    }
    else
    {
        /* A second setup in the same boot finds the address already present. */
        if(net_if_ipv4_addr_lookup(&address, NULL) == NULL)
        {
            if(net_if_ipv4_addr_add(wifi_HotspotInterface, &address, NET_ADDR_MANUAL, 0) == NULL)
            {
                result = -ENOMEM; /**< Required memory or network address slot is unavailable. */
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

        /* The full MAC tells devices apart and matches the label used for the FHIR Device identity. */
        (void)snprintk(name, sizeof(name), "Stetho-%02X%02X%02X%02X%02X%02X", hardwareAddress[0], hardwareAddress[1], hardwareAddress[2], hardwareAddress[3], hardwareAddress[4], hardwareAddress[5]);

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
                result = -EIO; /**< Input/output operation failed. */
            }
            else
            {
                hotspotConfiguration.ap.max_connection = 1;
                if(esp_wifi_set_config(WIFI_IF_AP, &hotspotConfiguration) != ESP_OK)
                {
                    result = -EIO; /**< Input/output operation failed. */
                }
            }
            (void)memset(&hotspotConfiguration, 0, sizeof(hotspotConfiguration));
        }
        if(result == 0)
        {
            LOG_INF("Hotspot \"%s\" open at %s", name, WIFI_HOTSPOT_ADDRESS);
        }
        else
        {
            wifi_rollbackHotspot();
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

        if(result == -EALREADY) /**< Requested state is already active. */
        {
            result = 0;
        }
    }

    return result;
}

int wifi_startDHCPServer(void)
{
    int result = -ENODEV; /**< Required device interface is unavailable. */
    struct net_in_addr poolStart;

    /* Start DHCP only with an available hotspot and a valid pool address. */
    if((wifi_HotspotInterface != NULL) && (net_addr_pton(NET_AF_INET, WIFI_HOTSPOT_ADDRESS, &poolStart) == 0))
    {
        poolStart.s4_addr[3] = WIFI_HOTSPOT_POOL_START;

        result = net_dhcpv4_server_start(wifi_HotspotInterface, &poolStart);

        if(result == -EALREADY) /**< Requested state is already active. */
        {
            result = 0;
        }
        else if(result != 0)
        {
            wifi_rollbackHotspot();
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

        if(result == -ENOENT) /**< Requested record or network was not found. */
        {
            /* Not running. */
            result = 0;
        }
    }

    return result;
}

int wifi_startTimeSynchronization(const char *ntpServer)
{
    int result = 0;

    if((ntpServer == NULL) || (ntpServer[0] == '\0'))
    {
        return -EINVAL; /**< Invalid argument or unsupported input. */
    }

    (void)k_mutex_lock(&wifi_TimeSynchronizationLock, K_FOREVER);

    /* COMPLETED is only reached after the worker released everything, so a CANCELLING operation keeps Start blocked. */
    if((wifi_TimeSynchronizationState == WIFI_TIME_SYNCHRONIZATION_PENDING) ||
       (wifi_TimeSynchronizationState == WIFI_TIME_SYNCHRONIZATION_CANCELLING))
    {
        result = -EBUSY; /**< Service is busy with another operation. */
    }
    else
    {
        /* Submitting before changing any state leaves the previous record intact if the queue rejects the work.
         * The worker cannot observe the half-updated state because it takes this mutex first. */
        const int submissionResult = k_work_submit_to_queue(&wifi_TimeSynchronizationQueue, &wifi_TimeSynchronizationWork);

        if(submissionResult < 0)
        {
            result = submissionResult;
        }
        else
        {
            wifi_TimeSynchronizationGeneration++;
            wifi_TimeServerHostname = ntpServer;
            wifi_TimeSynchronizationIsClaimed = false;
            wifi_TimeSynchronizationState = WIFI_TIME_SYNCHRONIZATION_PENDING;
            (void)k_event_clear(&wifi_Events, WIFI_EVENT_TIME_SYNCHRONIZED);
        }
    }

    (void)k_mutex_unlock(&wifi_TimeSynchronizationLock);

    return result;
}

int wifi_waitForTimeSynchronization(struct normalised_time *time, k_timeout_t timeout)
{
    if(time == NULL)
    {
        return -EINVAL; /**< Invalid argument or unsupported input. */
    }

    const k_timepoint_t deadline = sys_timepoint_calc(timeout);

    if(k_mutex_lock(&wifi_TimeSynchronizationLock, sys_timepoint_timeout(deadline)) != 0)
    {
        return -EAGAIN; /**< State was busy for this call's whole interval. */
    }
    const enum wifi_time_synchronization_state stateBeforeWait = wifi_TimeSynchronizationState;
    const uint32_t awaitedGeneration = wifi_TimeSynchronizationGeneration;
    (void)k_mutex_unlock(&wifi_TimeSynchronizationLock);

    if(stateBeforeWait == WIFI_TIME_SYNCHRONIZATION_IDLE)
    {
        return -EINVAL; /**< No operation to wait for. */
    }

    if(stateBeforeWait != WIFI_TIME_SYNCHRONIZATION_COMPLETED)
    {
        /* The event only wakes this call; the protected state decides the result. */
        (void)wifi_waitForEvents(WIFI_EVENT_TIME_SYNCHRONIZED, sys_timepoint_timeout(deadline));
    }

    if(k_mutex_lock(&wifi_TimeSynchronizationLock, sys_timepoint_timeout(deadline)) != 0)
    {
        return -EAGAIN; /**< State was busy for the rest of this call's interval. */
    }

    int result = -EAGAIN; /**< Still pending after this call's interval. */
    if(wifi_TimeSynchronizationGeneration != awaitedGeneration)
    {
        result = -ECANCELED; /**< A newer Start replaced the awaited operation and its result. */
    }
    else if(wifi_TimeSynchronizationState == WIFI_TIME_SYNCHRONIZATION_COMPLETED)
    {
        result = wifi_TimeSynchronizationResult;
        if(result == 0)
        {
            *time = wifi_TimeSynchronizationSample;
        }
    }
    (void)k_mutex_unlock(&wifi_TimeSynchronizationLock);

    return result;
}

int wifi_cancelTimeSynchronization(void)
{
    const k_timepoint_t deadline = sys_timepoint_calc(K_MSEC(WIFI_TIME_SYNCHRONIZATION_CANCEL_TIMEOUT_MS));

    if(k_mutex_lock(&wifi_TimeSynchronizationLock, sys_timepoint_timeout(deadline)) != 0)
    {
        return -ETIMEDOUT; /**< Release could not be confirmed within the stop bound. */
    }

    const uint32_t generation = wifi_TimeSynchronizationGeneration;
    bool isWithdrawnBeforeWorker = false;

    if(wifi_TimeSynchronizationState == WIFI_TIME_SYNCHRONIZATION_PENDING)
    {
        wifi_TimeSynchronizationState = WIFI_TIME_SYNCHRONIZATION_CANCELLING;
        /* Without a claim the worker owns nothing yet, and a handler that runs later sees CANCELLING or COMPLETED and exits.
         * k_work_cancel() is not used: on a running handler it makes the next submission fail with -EBUSY. */
        isWithdrawnBeforeWorker = !wifi_TimeSynchronizationIsClaimed;
    }
    const bool isWorkerReleasing = (wifi_TimeSynchronizationState == WIFI_TIME_SYNCHRONIZATION_CANCELLING) && !isWithdrawnBeforeWorker;

    (void)k_mutex_unlock(&wifi_TimeSynchronizationLock);

    if(isWithdrawnBeforeWorker)
    {
        wifi_publishTimeSynchronizationResult(generation, -ECANCELED, NULL);
    }
    else if(isWorkerReleasing)
    {
        /* The worker notices CANCELLING within one poll interval, releases its resources and then publishes. */
        (void)wifi_waitForEvents(WIFI_EVENT_TIME_SYNCHRONIZED, sys_timepoint_timeout(deadline));
    }

    if(k_mutex_lock(&wifi_TimeSynchronizationLock, sys_timepoint_timeout(deadline)) != 0)
    {
        return -ETIMEDOUT; /**< Release could not be confirmed within the stop bound. */
    }

    int result = 0;
    if(wifi_TimeSynchronizationState == WIFI_TIME_SYNCHRONIZATION_CANCELLING)
    {
        /* Not released yet: Start stays blocked and the hostname stays borrowed; a later Cancel may confirm release. */
        result = -ETIMEDOUT; /**< Release could not be confirmed within the stop bound. */
    }
    (void)k_mutex_unlock(&wifi_TimeSynchronizationLock);

    return result;
}

int wifi_applyTimeSynchronization(const struct normalised_time *time, struct applied_time_anchor *anchor)
{
    if((time == NULL) || (anchor == NULL) || (time->utc_fraction_nanoseconds >= NSEC_PER_SEC))
    {
        return -EINVAL; /**< Invalid argument or unsupported input. */
    }

    const uint64_t maximumUTCSeconds = (uint64_t)SYS_TIME_T_MAX;
    if(time->utc_seconds > maximumUTCSeconds)
    {
        return -ERANGE; /**< UTC is not representable as Zephyr real time. */
    }

    const uint64_t appliedMonotonicMicroseconds = k_ticks_to_us_floor64((uint64_t)k_uptime_ticks());
    if(time->receive_monotonic_microseconds > appliedMonotonicMicroseconds)
    {
        return -EINVAL; /**< Receive timestamp lies in the future. */
    }

    const uint64_t elapsedMicroseconds = appliedMonotonicMicroseconds - time->receive_monotonic_microseconds;
    uint64_t elapsedSeconds = elapsedMicroseconds / USEC_PER_SEC;
    uint32_t advancedFractionNanoseconds = time->utc_fraction_nanoseconds + (uint32_t)((elapsedMicroseconds % USEC_PER_SEC) * NSEC_PER_USEC);

    if(advancedFractionNanoseconds >= NSEC_PER_SEC)
    {
        advancedFractionNanoseconds -= NSEC_PER_SEC;
        elapsedSeconds++;
    }

    if(elapsedSeconds > (maximumUTCSeconds - time->utc_seconds))
    {
        return -ERANGE; /**< Advanced UTC is not representable as Zephyr real time. */
    }

    const struct applied_time_anchor appliedAnchor = {
        .utc_seconds = (time->utc_seconds + elapsedSeconds),
        .utc_fraction_nanoseconds = advancedFractionNanoseconds,
        .applied_monotonic_microseconds = appliedMonotonicMicroseconds,
        .estimated_uncertainty_microseconds = time->estimated_uncertainty_microseconds,
    };

    const struct timespec realTime = {
        .tv_sec = (time_t)appliedAnchor.utc_seconds,
        .tv_nsec = (long)appliedAnchor.utc_fraction_nanoseconds,
    };

    int result = sys_clock_settime(SYS_CLOCK_REALTIME, &realTime);
    if(result == 0)
    {
        *anchor = appliedAnchor;
    }

    return result;
}

/***********************************************************************/
/* LOCAL FUNCTIONS                                                     */
/***********************************************************************/

static void wifi_runTimeSynchronization(struct k_work *work)
{
    ARG_UNUSED(work);

    (void)k_mutex_lock(&wifi_TimeSynchronizationLock, K_FOREVER);
    const uint32_t generation = wifi_TimeSynchronizationGeneration;
    /* A handler left queued by an earlier submission must not take over an operation that another handler runs or that Cancel withdrew. */
    const bool isClaimed = (wifi_TimeSynchronizationState == WIFI_TIME_SYNCHRONIZATION_PENDING) && !wifi_TimeSynchronizationIsClaimed;
    if(isClaimed)
    {
        wifi_TimeSynchronizationIsClaimed = true;
    }
    (void)k_mutex_unlock(&wifi_TimeSynchronizationLock);

    if(!isClaimed)
    {
        return;
    }

    const k_timepoint_t deadline = sys_timepoint_calc(K_MSEC(WIFI_TIME_SYNCHRONIZATION_OPERATION_TIMEOUT_MS));
    struct net_sockaddr_in address = {0};
    struct normalised_time sample = {0};

    int result = wifi_resolveTimeServer(generation, deadline, &address);
    if(result == 0)
    {
        result = wifi_exchangeTimeSample(generation, deadline, &address, &sample);
    }

    const int releaseResult = wifi_releaseTimeSynchronizationResources();
    if(releaseResult != 0)
    {
        /* Without proven release the operation never completes: Start stays blocked and Cancel reports the fault. */
        LOG_ERR("Time synchronization release failed (%d)", releaseResult);
    }
    else
    {
        wifi_publishTimeSynchronizationResult(generation, result, (result == 0) ? &sample : NULL);
    }
}

static bool wifi_isTimeSynchronizationCurrent(uint32_t generation)
{
    return (generation == wifi_TimeSynchronizationGeneration) && (wifi_TimeSynchronizationState == WIFI_TIME_SYNCHRONIZATION_PENDING);
}

static bool wifi_isTimeSynchronizationAdmitted(uint32_t generation)
{
    (void)k_mutex_lock(&wifi_TimeSynchronizationLock, K_FOREVER);
    const bool isAdmitted = wifi_isTimeSynchronizationCurrent(generation);
    (void)k_mutex_unlock(&wifi_TimeSynchronizationLock);

    return isAdmitted;
}

static int wifi_resolveTimeServer(uint32_t generation, k_timepoint_t deadline, struct net_sockaddr_in *address)
{
    (void)k_mutex_lock(&wifi_TimeSynchronizationLock, K_FOREVER);
    const char *hostname = wifi_TimeServerHostname;
    (void)k_mutex_unlock(&wifi_TimeSynchronizationLock);

    return wifi_resolveIpv4(&wifi_TimeServerLookup,
                            hostname,
                            generation,
                            deadline,
                            WIFI_TIME_SYNCHRONIZATION_OPERATION_TIMEOUT_MS,
                            WIFI_TIME_SYNCHRONIZATION_POLL_INTERVAL_MS,
                            address);
}

static int wifi_exchangeTimeSample(uint32_t generation, k_timepoint_t deadline, const struct net_sockaddr_in *address, struct normalised_time *sample)
{
    struct net_sockaddr_in serverAddress = *address;
    serverAddress.sin_port = net_htons(WIFI_SNTP_PORT);

    if(!wifi_isTimeSynchronizationAdmitted(generation))
    {
        return -ECANCELED; /**< Cancellation ended the operation before the socket was opened. */
    }

    int result = sntp_init(&wifi_TimeSynchronizationContext, (const struct net_sockaddr *)&serverAddress, sizeof(serverAddress));
    if(result != 0)
    {
        return result;
    }
    wifi_TimeSynchronizationSocketIsOpen = true;

    /* Bounds the single send, which otherwise waits for a network buffer without limit. */
    const struct zsock_timeval sendTimeout = {
        .tv_sec = 0,
        .tv_usec = (WIFI_TIME_SYNCHRONIZATION_POLL_INTERVAL_MS * USEC_PER_MSEC),
    };
    if(zsock_setsockopt(wifi_TimeSynchronizationContext.sock.fd, ZSOCK_SOL_SOCKET, ZSOCK_SO_SNDTIMEO, &sendTimeout, sizeof(sendTimeout)) != 0)
    {
        return -errno;
    }

    struct sntp_time nativeTime = {0};
    /* sntp_query() sends the operation's only request; every later wait only receives.
     * Its zero receive timeout leaves the response to wifi_receiveTimeResponse(), which checks the server state first. */
    result = sntp_query(&wifi_TimeSynchronizationContext, 0, &nativeTime);
    if(result == 0)
    {
        result = -EPROTO; /**< A response that arrived before the server state check was parsed unchecked. */
    }
    while((result == -ETIMEDOUT) && !sys_timepoint_expired(deadline) && wifi_isTimeSynchronizationAdmitted(generation))
    {
        result = wifi_receiveTimeResponse(&nativeTime);
    }

    if(result == 0)
    {
        /* Normalized right away, so the monotonic receive time is taken as close to reception as possible. */
        result = wifi_normalizeTimeSample(&nativeTime, sample);
    }

    return result;
}

static int wifi_receiveTimeResponse(struct sntp_time *nativeTime)
{
    const int socket = wifi_TimeSynchronizationContext.sock.fd;
    struct zsock_pollfd descriptor = {.fd = socket, .events = ZSOCK_POLLIN};

    const int ready = zsock_poll(&descriptor, 1, WIFI_TIME_SYNCHRONIZATION_POLL_INTERVAL_MS);
    if(ready < 0)
    {
        return -errno;
    }
    if(ready == 0)
    {
        return -ETIMEDOUT; /**< No response within this poll interval. */
    }

    /* The pinned Zephyr parser rejects only stratum 0 and returns neither field, so the queued datagram is inspected first. */
    uint8_t header[WIFI_SNTP_HEADER_SIZE] = {0};
    const ssize_t received = zsock_recv(socket, header, sizeof(header), ZSOCK_MSG_PEEK);
    if(received < 0)
    {
        return -errno;
    }
    if(received == (ssize_t)sizeof(header))
    {
        const uint8_t leapIndicator = (header[0] >> WIFI_SNTP_LEAP_INDICATOR_SHIFT);
        const uint8_t stratum = header[1];

        if((leapIndicator == WIFI_SNTP_LEAP_INDICATOR_ALARM) || (stratum < WIFI_SNTP_STRATUM_MINIMUM) || (stratum > WIFI_SNTP_STRATUM_MAXIMUM))
        {
            /* The exchange ends here; closing the socket discards the datagram. */
            return -EPROTO; /**< Server clock is not synchronized. */
        }
    }

    /* A shorter datagram is left to the parser, which rejects its size. */
    return sntp_recv_response(&wifi_TimeSynchronizationContext, 0, nativeTime);
}

static int wifi_releaseTimeSynchronizationResources(void)
{
    int result = 0;

    if(wifi_TimeSynchronizationSocketIsOpen)
    {
        sntp_close(&wifi_TimeSynchronizationContext);
        wifi_TimeSynchronizationSocketIsOpen = false;
    }

    const int lookupResult = wifi_releaseLookup(&wifi_TimeServerLookup);
    if(lookupResult != 0)
    {
        result = lookupResult;
    }

    return result;
}

static void wifi_publishTimeSynchronizationResult(uint32_t generation, int result, const struct normalised_time *sample)
{
    (void)k_mutex_lock(&wifi_TimeSynchronizationLock, K_FOREVER);

    const bool isUnfinished = (wifi_TimeSynchronizationState == WIFI_TIME_SYNCHRONIZATION_PENDING) ||
                              (wifi_TimeSynchronizationState == WIFI_TIME_SYNCHRONIZATION_CANCELLING);

    if((generation == wifi_TimeSynchronizationGeneration) && isUnfinished)
    {
        if(wifi_TimeSynchronizationState == WIFI_TIME_SYNCHRONIZATION_CANCELLING)
        {
            /* Cancellation wins over a sample that arrived meanwhile. */
            result = -ECANCELED;
        }

        wifi_TimeSynchronizationResult = result;
        if(result == 0)
        {
            wifi_TimeSynchronizationSample = *sample;
        }
        wifi_TimeServerHostname = NULL;
        wifi_TimeSynchronizationState = WIFI_TIME_SYNCHRONIZATION_COMPLETED;
        /* Stays set until the next accepted Start, so repeated Wait calls return at once. */
        (void)k_event_post(&wifi_Events, WIFI_EVENT_TIME_SYNCHRONIZED);
    }

    (void)k_mutex_unlock(&wifi_TimeSynchronizationLock);
}

static int wifi_normalizeTimeSample(const struct sntp_time *nativeTime, struct normalised_time *sample)
{
    int result = 0;

    if((nativeTime == NULL) || (sample == NULL))
    {
        result = -EINVAL; /**< Invalid argument or unsupported input. */
    }
    else
    {
        const uint64_t kernelMonotonicMicroseconds = k_ticks_to_us_floor64((uint64_t)k_uptime_ticks());

        if(nativeTime->fraction >= USEC_PER_SEC)
        {
            result = -EINVAL; /**< Invalid argument or unsupported input. */
        }
        else
        {
            struct normalised_time normalizedSample = {
                .utc_seconds = nativeTime->seconds,
                .utc_fraction_nanoseconds = (nativeTime->fraction * NSEC_PER_USEC),
                .receive_monotonic_microseconds = kernelMonotonicMicroseconds,
                .estimated_uncertainty_microseconds = nativeTime->uncertainty_us};

            *sample = normalizedSample;
        }
    }

    return result;
}

static void wifi_rollbackHotspot(void)
{
    int result = wifi_stopDHCPServer();
    if(result != 0)
    {
        LOG_ERR("Hotspot DHCP rollback failed (%d)", result);
    }

    result = wifi_stopHotspot();
    if(result != 0)
    {
        LOG_ERR("Hotspot rollback failed (%d)", result);
    }
}

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
            /* A successful requested join becomes online only after an IPv4 address exists. */
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
            bool joinHasFailed = (atomic_get(&wifi_ConnectionIsRequested) != 0) &&
                                 (atomic_get(&wifi_DisconnectIsPending) == 0) &&
                                 (k_event_test(&wifi_Events, WIFI_EVENT_CONNECTED) == 0U); /**< An unsolicited disconnect ended the join before IPv4 readiness. */
            atomic_set(&wifi_StationIsActive, 0);
            atomic_set(&wifi_ConnectionIsRequested, 0);
            /* Disconnect status carries a reason, including USER_REQUEST (2). */
            (void)k_event_post(&wifi_Events, WIFI_EVENT_DISCONNECTED);
            (void)k_event_clear(&wifi_Events, WIFI_EVENT_CONNECTED);
            if(joinHasFailed)
            {
                atomic_set(&wifi_FailureCause, -ENOTCONN); /**< Station disconnected before the requested join obtained IPv4. */
                (void)k_event_post(&wifi_Events, WIFI_EVENT_FAILED);
            }
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
    int cause = -ECONNREFUSED; /**< Connection was refused. */

    switch(status)
    {
    case WIFI_STATUS_CONN_WRONG_PASSWORD:
        cause = -EACCES; /**< Credentials or access were rejected. */
        break;

    case WIFI_STATUS_CONN_AP_NOT_FOUND:
        cause = -ENOENT; /**< Requested record or network was not found. */
        break;

    case WIFI_STATUS_CONN_TIMEOUT:
        cause = -ETIMEDOUT; /**< Operation exceeded its wait deadline. */
        break;

    default:
        break;
    }

    return cause;
}

static void wifi_addScanResult(const struct wifi_scan_result *result)
{
    /* Hidden networks have no name to show; enterprise and WEP need more than a password. */
    /* Keep only named networks with supported lengths and security. */
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
            size_t destination;
            if(wifi_ScanCount < WIFI_SCAN_LIST_SIZE)
            {
                destination = wifi_ScanCount;
            }
            else
            {
                destination = weakestIndex;
            }
            /* Fill unused scan slots, then replace only a weaker entry. */
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
