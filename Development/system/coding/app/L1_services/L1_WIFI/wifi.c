/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L1_WIFI
 * @{
 * @file
 * Implementation of the WIFI module: one Wi-Fi step per function.
 *
 * Role in the workflow (architecture/wifi-flow.puml): L2_COMMUNICATION
 * decides order, attempts and delays; this module does one step and
 * returns its result:
 * - Boot: wifi_readSettings(), then wifi_connect() and wifi_waitForConnection().
 * - Setup: wifi_startScan() and wifi_waitForScanResult(), wifi_startHotspot() and
 *   wifi_startDHCPServer(); after a join, wifi_storeSettings().
 * - Idle: wifi_isConnected() for the link check.
 * - Close: wifi_stopDHCPServer(), wifi_stopHotspot(), wifi_disconnect().
 * The wait functions return -EAGAIN while a request runs, so L2 can wait
 * in short slices and still react to Start. A new request discards late
 * results of an earlier one.
 *
 * Status: implemented, not yet tested on the board.
 *
 * Coding rules: one return per function (MISRA C:2012 Rule 15.5); unused
 * return values are cast to void (Rule 17.7).
 *
 * References, in the order the features build on each other:
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
 * 3. Serve a setup page: see portal.c.
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
 *    - ESP32 Wi-Fi driver; its Kconfig lists access point and station
 *      (AP/STA) mode, buffer counts and the heap choice
 *      (ESP_WIFI_HEAP_SPIRAM):
 *      https://github.com/zephyrproject-rtos/zephyr/tree/main/drivers/wifi/esp32
 *    - Espressif Wi-Fi guide (buffers, channel behavior in AP/STA mode):
 *      https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-guides/wifi.html
 *    - Espressif external RAM (PSRAM) guide:
 *      https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-guides/external-ram.html
 *    - Setting Kconfig values (prj.conf, extra .conf files):
 *      https://docs.zephyrproject.org/latest/build/kconfig/setting.html
 *
 * Where the headers for these APIs are (the pinned Zephyr tree matches the
 * build exactly; the web documentation can be newer):
 * - <zephyr/X> is .ci-workspace/zephyr/include/zephyr/X, for example
 *   <zephyr/net/wifi_mgmt.h> (connect, scan, access point, events),
 *   <zephyr/net/net_mgmt.h> (event callbacks), <zephyr/net/net_if.h>
 *   (interfaces, IPv4 address), <zephyr/net/dhcpv4_server.h> and
 *   <zephyr/settings/settings.h>.
 * - The samples named above are in .ci-workspace/zephyr/samples/.
 * - <errno.h>: the C library of the toolchain (picolibc) in
 *   .ci-workspace/zephyr-sdk-1.0.1/gnu/<target>/<target>/include/.
 * - Any other header: build-app/compile_commands.json lists every include
 *   path (-I) that the compiler searches, in order.
 */

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include "wifi.h"

#include <errno.h>
#include <string.h>

#include <zephyr/logging/log.h>
#include <zephyr/net/dhcpv4_server.h>
#include <zephyr/net/net_event.h>
#include <zephyr/net/net_if.h>
#include <zephyr/net/net_ip.h>
#include <zephyr/net/net_mgmt.h>
#include <zephyr/net/wifi_mgmt.h>
#include <zephyr/settings/settings.h>
#include <zephyr/sys/printk.h>

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

#define WIFI_EVENT_CONNECTED BIT(0) /**< Station associated and IPv4 address assigned. */
#define WIFI_EVENT_FAILED    BIT(1) /**< Access point rejected the connect request. */
#define WIFI_EVENT_SCAN_DONE BIT(2) /**< Scan finished; results are complete. */

#define WIFI_SCAN_CANCEL_TIMEOUT_MS (5000) /**< Candidate: longest driver scan after a cancel. */

/* Wi-Fi (L2) and IPv4 (L3) events belong to different layers, so each needs its own callback. */
#define WIFI_L2_EVENTS (NET_EVENT_WIFI_CONNECT_RESULT | NET_EVENT_WIFI_DISCONNECT_RESULT | NET_EVENT_WIFI_SCAN_RESULT | NET_EVENT_WIFI_SCAN_DONE)
#define WIFI_L3_EVENTS (NET_EVENT_IPV4_ADDR_ADD | NET_EVENT_IPV4_ADDR_DEL)

#define WIFI_SCAN_CAPACITY      (16)                    /**< Networks kept per scan; more are dropped. */
#define WIFI_HOTSPOT_NETMASK    "255.255.255.0"         /**< Hotspot subnet. */
#define WIFI_HOTSPOT_POOL_START (10)                    /**< Last address byte of the first DHCP lease. */
#define WIFI_HOTSPOT_NAME_SIZE  (sizeof("Stetho-XXXX")) /**< Hotspot name with the last two MAC bytes. */
#define WIFI_SETTINGS_SUBTREE   "wifi"                  /**< Settings subtree of this module. */
#define WIFI_SETTINGS_KEY       "network"               /**< Key of the stored struct wifi_network. */
#define WIFI_SETTINGS_NAME      "wifi/network"          /**< Full settings name of the stored network. */

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/** Result of wifi_readSettings(), filled by the settings callback. */
struct wifi_settings_read
{
    struct wifi_network *network; /**< Destination of the stored network. */
    int result;                   /**< 0 when read, -ENOENT until found, or an error code. */
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

static struct net_if *wifi_StationInterface;                     /**< Joins the clinic network. */
static struct net_if *wifi_HotspotInterface;                     /**< Serves the setup hotspot; NULL without AP support. */
static struct net_mgmt_event_callback wifi_L2Callback;           /**< Connect, disconnect and scan events. */
static struct net_mgmt_event_callback wifi_L3Callback;           /**< IPv4 address events. */
static atomic_t wifi_FailureCause;                               /**< Error code of the last rejected connect request. */
static struct wifi_scan_entry wifi_ScanList[WIFI_SCAN_CAPACITY]; /**< Written by the event handler during a scan. */
static size_t wifi_ScanCount;                                    /**< Valid entries in wifi_ScanList. */
static struct k_spinlock wifi_ScanLock;                          /**< Protects the scan list and the scan flags. */
static bool wifi_ScanIsRunning;                                  /**< The driver scans until NET_EVENT_WIFI_SCAN_DONE. */
static bool wifi_ScanResultsAreAccepted;                         /**< Results belong to the scan the caller waits for. */
static atomic_t wifi_ConnectionIsRequested;                      /**< Connect and IPv4 events belong to a request of this module. */

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

/**
 * @brief Copy the stored network into the read context.
 *
 * Parameters as settings_load_direct_cb.
 *
 * @return 0 to continue loading, as the settings subsystem expects.
 */
static int wifi_loadSetting(const char *key, size_t length, settings_read_cb read, void *readArgument, void *parameter);

/**
 * @brief Check the lengths of a network name and password.
 *
 * @param[in] network Network to check.
 *
 * @return True if both fit the Wi-Fi limits; an empty password means an open network.
 */
static bool wifi_isValidNetwork(const struct wifi_network *network);

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
        net_mgmt_init_event_callback(&wifi_L2Callback, wifi_handleEvent, WIFI_L2_EVENTS);
        net_mgmt_add_event_callback(&wifi_L2Callback);
        net_mgmt_init_event_callback(&wifi_L3Callback, wifi_handleEvent, WIFI_L3_EVENTS);
        net_mgmt_add_event_callback(&wifi_L3Callback);

        result = settings_subsys_init();

        if(result != 0)
        {
            /* Wi-Fi still works; only the stored network is unavailable. */
            LOG_ERR("Settings init failed (%d)", result);

            result = 0;
        }
    }

    return result;
}

int wifi_readSettings(struct wifi_network *network)
{
    struct wifi_settings_read read = {.network = network, .result = -ENOENT};

    int result = settings_load_subtree_direct(WIFI_SETTINGS_SUBTREE, wifi_loadSetting, &read);

    if(result == 0)
    {
        result = read.result;
    }

    if((result == 0) && !wifi_isValidNetwork(network))
    {
        /* A damaged record must not reach the connect request. */
        LOG_ERR("Stored network is invalid");
        (void)memset(network, 0, sizeof(*network));

        result = -EINVAL;
    }

    return result;
}

int wifi_storeSettings(const struct wifi_network *network)
{
    int result = -EINVAL;

    if(wifi_isValidNetwork(network))
    {
        /* One record for name and password: ZMS writes it as a whole, so a failed
         * write leaves the previous record valid. */
        result = settings_save_one(WIFI_SETTINGS_NAME, network, sizeof(*network));
    }

    return result;
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

        if(wifi_isConnected())
        {
            /* A join from the page replaces the current network; its IPv4 event must
             * not count as the result of the new request. */
            (void)wifi_disconnect();
        }

        (void)k_event_clear(&wifi_Events, WIFI_EVENT_CONNECTED | WIFI_EVENT_FAILED);
        atomic_set(&wifi_ConnectionIsRequested, 1);

        result = net_mgmt(NET_REQUEST_WIFI_CONNECT, wifi_StationInterface, &parameters, sizeof(parameters));

        if(result != 0)
        {
            /* A rejected request leaves nothing pending whose events could count later. */
            atomic_set(&wifi_ConnectionIsRequested, 0);
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
        /* Still pending: the caller decides whether to keep waiting. */
    }

    return result;
}

int wifi_disconnect(void)
{
    /* Rejected before the request, so no callback of the old attempt can count afterwards. */
    atomic_set(&wifi_ConnectionIsRequested, 0);

    /* The driver stops retrying in the background, so a later scan or connect finds it idle. */
    int result = net_mgmt(NET_REQUEST_WIFI_DISCONNECT, wifi_StationInterface, NULL, 0);

    (void)k_event_clear(&wifi_Events, WIFI_EVENT_CONNECTED | WIFI_EVENT_FAILED);

    if(result == -EALREADY)
    {
        /* No connection to end is not an error for the caller. */
        result = 0;
    }

    return result;
}

bool wifi_isConnected(void)
{
    return k_event_test(&wifi_Events, WIFI_EVENT_CONNECTED) != 0U;
}

int wifi_startScan(void)
{
    k_spinlock_key_t key = k_spin_lock(&wifi_ScanLock);

    /* Late results of an earlier scan must not mix into the new list. */
    wifi_ScanCount = 0;
    wifi_ScanIsRunning = true;
    wifi_ScanResultsAreAccepted = true;

    k_spin_unlock(&wifi_ScanLock, key);
    (void)k_event_clear(&wifi_Events, WIFI_EVENT_SCAN_DONE);

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

    /* The ESP32 driver cannot abort a scan, so completion means the scan has ended. */
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
            /* The scan was cancelled; its list is incomplete. */
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
        const uint8_t *mac = net_if_get_link_addr(wifi_StationInterface)->addr;
        char name[WIFI_HOTSPOT_NAME_SIZE];

        /* The MAC bytes tell several devices in one room apart. */
        (void)snprintk(name, sizeof(name), "Stetho-%02X%02X", mac[4], mac[5]);

        struct wifi_connect_req_params parameters = {
            .ssid = (const uint8_t *)name,
            .ssid_length = (uint8_t)strlen(name),
            .security = WIFI_SECURITY_TYPE_NONE, /* Open hotspot: Development/system/design/parameters.md, P21. */
            .band = WIFI_FREQ_BAND_2_4_GHZ,
            .channel = WIFI_CHANNEL_ANY,
        };

        result = net_mgmt(NET_REQUEST_WIFI_AP_ENABLE, wifi_HotspotInterface, &parameters, sizeof(parameters));

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
            /* A closed hotspot is not an error for the caller. */
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
            /* A stopped server is not an error for the caller. */
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

            if((status->status != 0) && (atomic_get(&wifi_ConnectionIsRequested) != 0))
            {
                LOG_WRN("Connect rejected (%d)", status->status);
                atomic_set(&wifi_FailureCause, wifi_mapFailure(status->status));
                (void)k_event_post(&wifi_Events, WIFI_EVENT_FAILED);
            }

            break;
        }

        case NET_EVENT_WIFI_DISCONNECT_RESULT:
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

            k_spin_unlock(&wifi_ScanLock, key);
            (void)k_event_post(&wifi_Events, WIFI_EVENT_SCAN_DONE);
            break;
        }

        case NET_EVENT_IPV4_ADDR_ADD:
            /* Online only with an address: association alone cannot reach the server.
             * An address after wifi_disconnect() belongs to a cancelled attempt. */
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

        /* A cancelled scan reports nothing more; a full list counts as listed. */
        isListed = !wifi_ScanResultsAreAccepted;

        /* Several access points can share one name; the page lists it once. */
        for(size_t index = 0; (index < wifi_ScanCount) && !isListed; index++)
        {
            isListed = (strcmp(wifi_ScanList[index].name, entry.name) == 0);
        }

        if(!isListed && (wifi_ScanCount < WIFI_SCAN_CAPACITY))
        {
            wifi_ScanList[wifi_ScanCount] = entry;
            wifi_ScanCount++;
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
    case WIFI_SECURITY_TYPE_PSK_SHA256:
    case WIFI_SECURITY_TYPE_WPA_PSK:
    case WIFI_SECURITY_TYPE_WPA_AUTO_PERSONAL:
    case WIFI_SECURITY_TYPE_SAE:
    case WIFI_SECURITY_TYPE_SAE_H2E:
    case WIFI_SECURITY_TYPE_SAE_AUTO:
        isSupported = true;
        break;

    default:
        break;
    }

    return isSupported;
}

static int wifi_loadSetting(const char *key, size_t length, settings_read_cb read, void *readArgument, void *parameter)
{
    struct wifi_settings_read *context = parameter;

    if((key != NULL) && (settings_name_steq(key, WIFI_SETTINGS_KEY, NULL) != 0))
    {
        if(length != sizeof(*context->network))
        {
            /* A record of another size comes from another layout and cannot be trusted. */
            context->result = -EINVAL;
        }
        else
        {
            ssize_t readLength = read(readArgument, context->network, sizeof(*context->network));

            context->result = (readLength == (ssize_t)sizeof(*context->network)) ? 0 : -EIO;
        }
    }

    return 0;
}

static bool wifi_isValidNetwork(const struct wifi_network *network)
{
    size_t nameLength = strnlen(network->name, sizeof(network->name));
    size_t passwordLength = strnlen(network->password, sizeof(network->password));

    /* strnlen() equal to the buffer size means the terminator is missing. */
    bool isNameValid = (nameLength != 0U) && (nameLength < sizeof(network->name));
    bool isPasswordValid = (passwordLength == 0U) || ((passwordLength >= WIFI_PSK_MIN_LEN) && (passwordLength < sizeof(network->password)));

    return isNameValid && isPasswordValid;
}

/** @} */
