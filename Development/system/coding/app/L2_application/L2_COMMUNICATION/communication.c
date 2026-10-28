/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L2_COMMUNICATION
 * @{
 * @file
 * Implementation of the COMMUNICATION module: the Wi-Fi workflow thread.
 *
 * Workflow, as drawn in architecture/wifi-flow.puml, wifi-state.puml and
 * wifi-recovery.puml (rules: planning/mvp-decisions-2026-10-19.md):
 * - Boot: read the stored network and join it, 4 attempts, 5 s apart.
 *   No network stored: run setup. All attempts failed: wait for a 2 s hold.
 * - Setup: scan (4 attempts), then open the hotspot, DHCP server and page.
 *   The page sends Connect, Rescan, Cancel and activity requests:
 *   - Connect: one join attempt; requests sent meanwhile are dropped.
 *     Joined: save (2 attempts), show the result 10 s, close the page.
 *     Failed: show the cause, rescan, return to the selection.
 *   - Rescan: scan again with the hotspot open.
 *   - Cancel or 5 min without activity: closing notice, then close.
 *   - A scan that fails 4 times shows its cause and closes setup.
 *   Closing keeps an established station, otherwise it disconnects.
 * - Idle: a 2 s hold runs setup. Every 2 min, check the link; if it is
 *   lost, join again (4 attempts) and run setup once if all fail.
 * - Listening: no Wi-Fi work; the station association stays. Every wait
 *   checks for Start in 200 ms wait slices. Driver cancellation, atomic
 *   settings writes and teardown must also finish before control may start
 *   audio. Their target latency is not yet measured.
 *
 * Wi-Fi errors never mute audio or block offline Start, so this module
 * only logs them for now (catalogue names, for example SCAN_FAILURE). The
 * LED report goes to control when control has an interface for it.
 *
 * References used for the implementation:
 * - Threads (k_thread_create, stacks, priorities):
 *   https://docs.zephyrproject.org/latest/kernel/services/threads/index.html
 * - Semaphores, to wake the worker after control changes its requested state:
 *   https://docs.zephyrproject.org/latest/kernel/services/synchronization/semaphores.html
 * - Timeouts and timepoints (sys_timepoint_calc, sys_timepoint_expired):
 *   https://docs.zephyrproject.org/latest/kernel/services/timing/clocks.html
 * - Logging (LOG_MODULE_REGISTER, LOG_INF, deferred mode):
 *   https://docs.zephyrproject.org/latest/services/logging/index.html
 * - Wi-Fi, DHCP, HTTP server and settings: see wifi.c and portal.c.
 *
 * Where the included headers are:
 * - <zephyr/...>: the pinned Zephyr tree, .ci-workspace/zephyr/include/zephyr/,
 *   for example <zephyr/kernel.h> is .ci-workspace/zephyr/include/zephyr/kernel.h.
 *   These files match the build exactly; the web documentation can be newer.
 * - <errno.h>, <string.h>: the C library of the toolchain (picolibc) in
 *   .ci-workspace/zephyr-sdk-1.0.1/gnu/<target>/<target>/include/.
 * - "wifi.h", "portal.h": the module folders that CMakeLists.txt lists in
 *   target_include_directories.
 * - Any other header: build-app/compile_commands.json lists every include
 *   path (-I) that the compiler searches, in order.
 */

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include "communication.h"

#include <errno.h>
#include <string.h>

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

#include "portal.h"
#include "wifi.h"

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

#define COMMUNICATION_THREAD_STACK_SIZE (4096) /**< Size of the communication thread stack. */
#define COMMUNICATION_THREAD_PRIORITY   (10)   /**< Priority of the communication thread. */

#define COMMUNICATION_STORED_CONNECT_ATTEMPTS     (4)                        /**< P23: boot and recovery. */
#define COMMUNICATION_PAGE_CONNECT_ATTEMPTS       (1)                        /**< P23: request from the page. */
#define COMMUNICATION_SCAN_ATTEMPTS               (4)                        /**< P23: scans in total. */
#define COMMUNICATION_SAVE_ATTEMPTS               (2)                        /**< P23: settings saves in total. */
#define COMMUNICATION_RETRY_DELAY_S               (5)                        /**< P23: after a failed attempt. */
#define COMMUNICATION_CONNECT_TIMEOUT_S           (15)                       /**< Candidate: until online. */
#define COMMUNICATION_SCAN_TIMEOUT_S              (10)                       /**< Candidate: one scan. */
#define COMMUNICATION_SETUP_INACTIVITY_TIMEOUT_S  (5 * 60)                   /**< P21: without page activity. */
#define COMMUNICATION_RESULT_DISPLAY_S            (10)                       /**< P23: success or save warning. */
#define COMMUNICATION_CLOSE_NOTICE_DISPLAY_S      (2)                        /**< Candidate: Cancel or timeout. */
#define COMMUNICATION_CONNECTION_CHECK_INTERVAL_S (2 * 60)                   /**< Candidate: in Idle only. */
#define COMMUNICATION_SCAN_LIST_SIZE              (16)                       /**< Candidate: networks on the page. */
#define COMMUNICATION_EVENT_CHECK_INTERVAL_MS     (200)                      /**< Longest delay to see a Start. */
K_THREAD_STACK_DEFINE(communication_Stack, COMMUNICATION_THREAD_STACK_SIZE); /**< Communication stack. */
K_SEM_DEFINE(communication_ControlChanged, 0, 1);                            /**< Wakeup; state is held under ControlLock. */

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

enum communication_setup_result
{
    COMMUNICATION_SETUP_RUNNING,     /**< Setup still serves the page. */
    COMMUNICATION_SETUP_CONNECTED,   /**< Joined a network; the page showed the result. */
    COMMUNICATION_SETUP_CANCELLED,   /**< Cancel on the page or 5 min without activity. */
    COMMUNICATION_SETUP_FAILED,      /**< A scan failed; setup cannot continue. */
    COMMUNICATION_SETUP_INTERRUPTED, /**< Listening started. */
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

static struct k_thread communication_ThreadData; /**< Communication thread. */

static struct wifi_network communication_StoredNetwork;                             /**< Network for boot and recovery. */
static bool communication_StoredNetworkIsValid;                                     /**< StoredNetwork holds a network. */
static struct portal_request communication_PageRequest;                             /**< Last page request, with password. */
static struct wifi_scan_entry communication_ScanList[COMMUNICATION_SCAN_LIST_SIZE]; /**< Networks for the page. */
static size_t communication_ScanCount;                                              /**< Valid entries in ScanList. */

/* Only CONTROL changes the requested state. Coalesced wakeups cannot lose a
 * Start/Stop transition's final state. A Start invalidates an old acknowledgement. */
static struct k_spinlock communication_ControlLock;
static bool communication_ListeningIsRequested;
static bool communication_SetupIsPending;
static bool communication_SetupIsActive;
static bool communication_WiFiIsStopped;
static bool communication_WiFiIsUnavailable;

/* Worker-owned resources remain pending until L1 confirms their release. */
static bool communication_ScanIsPending;
static bool communication_ConnectionIsPending;
static bool communication_PortalIsActive;
static bool communication_DHCPServerIsActive;
static bool communication_HotspotIsActive;

static bool communication_ListeningIsActive; /**< Control listens; no Wi-Fi work allowed during that time. */
static bool communication_SetupIsRequested;  /**< 2 s hold in Idle not yet handled. */
static bool communication_RecoveryIsAllowed; /**< A connection was up; no failed recovery since. */

/***********************************************************************/
/* LOCAL FUNCTION PROTOTYPES                                           */
/***********************************************************************/

/**
 * @brief Thread for handling communication tasks.
 *
 * @param[in] arg1 Unused parameter.
 * @param[in] arg2 Unused parameter.
 * @param[in] arg3 Unused parameter.
 */
static void communication_thread(void *arg1, void *arg2, void *arg3);

/**
 * @brief Load the stored network and connect, or run setup if none is stored.
 */
static void communication_connectAtBoot(void);

/**
 * @brief Run one Idle pass: setup on a 2 s hold, otherwise wait and check the link.
 */
static void communication_runIdleCycle(void);

/**
 * @brief Reconnect if the link was lost in Idle; run setup if all attempts fail.
 */
static void communication_recoverConnection(void);

/**
 * @brief Wait for events from control and handle them.
 *
 * Returns on a state-change wakeup or timeout and reads the latest control
 * state under a spinlock. K_NO_WAIT reads it without a delay. Fixed delays
 * use communication_waitForDelay(), so unrelated wakeups do not shorten them.
 *
 * Afterwards, communication_ListeningIsActive tells whether Wi-Fi work
 * must stop.
 *
 * @param[in] timeout Maximum time to wait.
 */
static void communication_waitForEvents(k_timeout_t timeout);

/** @brief Keep a fixed delay unless listening requests an early exit. */
static void communication_waitForDelay(k_timeout_t timeout);

/** @brief Release setup and pending radio work, retaining a connected station.
 * @return True only when every active resource has confirmed release.
 */
static bool communication_stopWiFiWork(void);

/**
 * @brief Wait in slices for the pending connect request.
 *
 * @return 0 when online, -ECANCELED if listening started, or the error code of the request.
 */
static int communication_waitForConnection(void);

/**
 * @brief Wait in slices for the running scan and store its list.
 *
 * @return 0 on success, -ECANCELED if listening started, or the error code of the scan.
 */
static int communication_waitForScanResult(void);

/**
 * @brief Connect to a network, with COMMUNICATION_RETRY_DELAY_S between failed attempts.
 *
 * Boot and recovery use COMMUNICATION_STORED_CONNECT_ATTEMPTS on the stored
 * network; a page request uses COMMUNICATION_PAGE_CONNECT_ATTEMPTS.
 *
 * @param[in] network  Network to join.
 * @param[in] attempts Number of attempts in total.
 *
 * @return 0 when online, -ECANCELED if listening started, or the last error code.
 */
static int communication_connectToNetwork(const struct wifi_network *network, int attempts);

/**
 * @brief Scan into communication_ScanList and publish it for the page.
 *
 * COMMUNICATION_SCAN_ATTEMPTS in total. The previous list stays if all
 * attempts fail. Publishing before the page starts is harmless.
 *
 * @return 0 on success, -ECANCELED if listening started, or the last error code.
 */
static int communication_scanNetworks(void);

/**
 * @brief Run the whole setup: scan, open the page, serve it, close it.
 */
static void communication_runSetup(void);

/**
 * @brief Start the hotspot, the DHCP server and the page; undo the started steps on failure.
 *
 * @return 0 on success, or the error code of the step that failed.
 */
static int communication_openSetup(void);

/**
 * @brief Serve requests from the page until setup ends.
 *
 * @param[out] error Cause when setup failed, otherwise 0.
 *
 * @return How setup ended.
 */
static enum communication_setup_result communication_servePage(int *error);

/**
 * @brief Handle the request in communication_PageRequest.
 *
 * @param[out] error Cause when setup failed, otherwise unchanged.
 *
 * @return COMMUNICATION_SETUP_RUNNING to keep serving, otherwise how setup ended.
 */
static enum communication_setup_result communication_handlePageRequest(int *error);

/**
 * @brief Connect to the network from the page request, then save it or show the cause.
 *
 * @return 0 if connected, -ECANCELED if listening started, or the error the page shows.
 */
static int communication_handleConnectRequest(void);

/**
 * @brief Save the joined network, COMMUNICATION_SAVE_ATTEMPTS in total, and keep it for reconnects.
 *
 * @param[in] network Joined network.
 */
static void communication_saveNetwork(const struct wifi_network *network);

/**
 * @brief Drop page requests sent while a join ran; user cancel is locked then.
 */
static void communication_discardPageRequests(void);

/**
 * @brief Close the page, the DHCP server and the hotspot.
 *
 * @param[in] outcome How setup ended; Cancel, timeout and failure show a notice first.
 * @param[in] error   Cause shown with the notice, or 0.
 */
static void communication_closeSetup(enum communication_setup_result outcome, int error);

/***********************************************************************/
/* MACROS                                                              */
/***********************************************************************/

LOG_MODULE_REGISTER(communication, LOG_LEVEL_INF);

/***********************************************************************/
/* GLOBAL FUNCTIONS                                                    */
/***********************************************************************/

void communication_init(void)
{
    (void)k_thread_create(&communication_ThreadData,
                          communication_Stack,
                          K_THREAD_STACK_SIZEOF(communication_Stack),
                          communication_thread,
                          NULL,
                          NULL,
                          NULL,
                          COMMUNICATION_THREAD_PRIORITY,
                          0,
                          K_FOREVER);

    (void)k_thread_name_set(&communication_ThreadData, "communication");
    k_thread_start(&communication_ThreadData);
}

int communication_postEvent(enum communication_event event)
{
    int result = 0;
    k_spinlock_key_t key = k_spin_lock(&communication_ControlLock);

    switch(event)
    {
    case COMMUNICATION_EVENT_LISTENING_STARTED:
        communication_ListeningIsRequested = true;
        communication_SetupIsPending = false;
        communication_WiFiIsStopped = false;
        break;

    case COMMUNICATION_EVENT_LISTENING_STOPPED:
        communication_ListeningIsRequested = false;
        communication_WiFiIsStopped = false;
        break;

    case COMMUNICATION_EVENT_SETUP_REQUESTED:
        if(!communication_ListeningIsRequested && !communication_SetupIsActive)
        {
            communication_SetupIsPending = true;
        }

        break;

    default:
        result = -EINVAL;
        break;
    }

    k_spin_unlock(&communication_ControlLock, key);

    if(result == 0)
    {
        k_sem_give(&communication_ControlChanged);
    }

    return result;
}

int communication_waitForWiFiStop(k_timeout_t timeout)
{
    k_timepoint_t deadline = sys_timepoint_calc(timeout);

    int result = -EAGAIN;
    bool waiting = true;

    while(waiting)
    {
        k_spinlock_key_t key = k_spin_lock(&communication_ControlLock);
        bool stopped = communication_ListeningIsRequested &&
                       (communication_WiFiIsStopped || communication_WiFiIsUnavailable);

        k_spin_unlock(&communication_ControlLock, key);

        if(stopped)
        {
            result = 0;
        }

        waiting = (result != 0) && !sys_timepoint_expired(deadline);

        if(waiting)
        {
            k_timeout_t remaining = sys_timepoint_timeout(deadline);
            k_timeout_t slice = K_MSEC(COMMUNICATION_EVENT_CHECK_INTERVAL_MS);

            if(!K_TIMEOUT_EQ(remaining, K_FOREVER) && (remaining.ticks < slice.ticks))
            {
                slice = remaining;
            }

            (void)k_sleep(slice);
        }
    }

    return result;
}

/***********************************************************************/
/* LOCAL FUNCTIONS                                                     */
/***********************************************************************/

static void communication_thread(void *arg1, void *arg2, void *arg3)
{
    ARG_UNUSED(arg1);
    ARG_UNUSED(arg2);
    ARG_UNUSED(arg3);

    int result = wifi_init();

    if(result != 0)
    {
        /* Audio works without Wi-Fi; the thread ends and control never waits for it. */
        LOG_ERR("Wi-Fi init failed (%d); device stays offline", result);

        k_spinlock_key_t key = k_spin_lock(&communication_ControlLock);

        communication_WiFiIsUnavailable = true;

        k_spin_unlock(&communication_ControlLock, key);
    }
    else
    {
        communication_connectAtBoot();

        for(;;)
        {
            communication_runIdleCycle();
        }
    }
}

static void communication_connectAtBoot(void)
{
    int result = wifi_readSettings(&communication_StoredNetwork);

    if(result != 0)
    {
        if(result != -ENOENT)
        {
            LOG_ERR("Wi-Fi settings load failed (%d)", result);
        }

        LOG_INF("No stored Wi-Fi network; opening setup");
        communication_runSetup();
    }
    else
    {
        communication_StoredNetworkIsValid = true;

        LOG_INF("Connecting to \"%s\"", communication_StoredNetwork.name);

        result = communication_connectToNetwork(&communication_StoredNetwork, COMMUNICATION_STORED_CONNECT_ATTEMPTS);

        if(result == 0)
        {
            LOG_INF("Wi-Fi connected");
        }
        else if(result == -ECANCELED)
        {
            /* Listening interrupted the attempts before they were used up, so recovery
             * in Idle is still permitted. */
            communication_RecoveryIsAllowed = true;
        }
        else
        {
            LOG_ERR("JOIN_FAILURE (%d); hold the button 2 s for setup", result);
        }
    }
}

static void communication_runIdleCycle(void)
{
    communication_waitForEvents(K_NO_WAIT);

    bool stopped = communication_stopWiFiWork();

    if(communication_ListeningIsActive)
    {
        k_spinlock_key_t key = k_spin_lock(&communication_ControlLock);

        communication_WiFiIsStopped = stopped && communication_ListeningIsRequested;

        k_spin_unlock(&communication_ControlLock, key);

        if(stopped)
        {
            communication_waitForEvents(K_FOREVER);
        }
        else
        {
            communication_waitForEvents(K_MSEC(COMMUNICATION_EVENT_CHECK_INTERVAL_MS));
        }

        if(stopped && !communication_ListeningIsActive)
        {
            /* Resume deferred recovery as soon as CONTROL returns to Idle. */
            communication_recoverConnection();
        }
    }
    else if(!stopped)
    {
        /* Do not start another operation or release audio after failed cleanup. */
        communication_waitForEvents(K_MSEC(COMMUNICATION_EVENT_CHECK_INTERVAL_MS));
    }
    else if(communication_SetupIsRequested)
    {
        communication_SetupIsRequested = false;

        communication_runSetup();
    }
    else
    {
        communication_waitForEvents(K_SECONDS(COMMUNICATION_CONNECTION_CHECK_INTERVAL_S));

        if(!communication_ListeningIsActive)
        {
            communication_recoverConnection();
        }
    }
}

static void communication_recoverConnection(void)
{
    if(!communication_SetupIsRequested && communication_RecoveryIsAllowed && communication_StoredNetworkIsValid && !wifi_isConnected())
    {
        LOG_WRN("Wi-Fi link lost; reconnecting");

        int result = communication_connectToNetwork(&communication_StoredNetwork, COMMUNICATION_STORED_CONNECT_ATTEMPTS);

        if(result == 0)
        {
            LOG_INF("Wi-Fi reconnected");
        }
        else if(result != -ECANCELED)
        {
            LOG_ERR("RECONNECT_FAILURE (%d); opening setup", result);

            communication_RecoveryIsAllowed = false;

            communication_runSetup();
        }
        else
        {
            /* Listening has priority (P19); RecoveryIsAllowed stays set, so Idle resumes
             * the recovery. */
        }
    }
}

static void communication_waitForEvents(k_timeout_t timeout)
{
    (void)k_sem_take(&communication_ControlChanged, timeout);

    k_spinlock_key_t key = k_spin_lock(&communication_ControlLock);

    communication_ListeningIsActive = communication_ListeningIsRequested;

    if(communication_SetupIsPending && !communication_SetupIsActive && !communication_ListeningIsActive)
    {
        communication_SetupIsRequested = true;
    }

    communication_SetupIsPending = false;

    if(communication_ListeningIsActive)
    {
        communication_SetupIsRequested = false;
    }

    k_spin_unlock(&communication_ControlLock, key);
}

static void communication_waitForDelay(k_timeout_t timeout)
{
    k_timepoint_t deadline = sys_timepoint_calc(timeout);

    communication_waitForEvents(K_NO_WAIT);

    while(!communication_ListeningIsActive && !sys_timepoint_expired(deadline))
    {
        communication_waitForEvents(sys_timepoint_timeout(deadline));
    }
}

static bool communication_stopWiFiWork(void)
{
    if(communication_ScanIsPending)
    {
        int result = wifi_cancelScan();

        communication_ScanIsPending = (result != 0);

        if(result != 0)
        {
            LOG_ERR("Scan cancellation failed (%d); audio release withheld", result);
        }
    }

    if(communication_ConnectionIsPending)
    {
        int result = wifi_disconnect();

        communication_ConnectionIsPending = (result != 0);

        if(result != 0)
        {
            LOG_ERR("Connect cancellation failed (%d); audio release withheld", result);
        }
    }

    if(communication_PortalIsActive)
    {
        int result = portal_stop();

        communication_PortalIsActive = (result != 0);

        if(result != 0)
        {
            LOG_ERR("Portal shutdown failed (%d); audio release withheld", result);
        }
    }

    if(communication_DHCPServerIsActive)
    {
        int result = wifi_stopDHCPServer();

        communication_DHCPServerIsActive = (result != 0);

        if(result != 0)
        {
            LOG_ERR("DHCP shutdown failed (%d); audio release withheld", result);
        }
    }

    if(communication_HotspotIsActive)
    {
        int result = wifi_stopHotspot();

        communication_HotspotIsActive = (result != 0);

        if(result != 0)
        {
            LOG_ERR("Hotspot shutdown failed (%d); audio release withheld", result);
        }
    }

    return !communication_ScanIsPending && !communication_ConnectionIsPending &&
           !communication_PortalIsActive && !communication_DHCPServerIsActive && !communication_HotspotIsActive;
}

static int communication_waitForConnection(void)
{
    k_timepoint_t deadline = sys_timepoint_calc(K_SECONDS(COMMUNICATION_CONNECT_TIMEOUT_S));
    int result = -EAGAIN;

    while((result == -EAGAIN) && !sys_timepoint_expired(deadline))
    {
        communication_waitForEvents(K_NO_WAIT);

        if(communication_ListeningIsActive)
        {
            result = -ECANCELED;
        }
        else
        {
            result = wifi_waitForConnection(K_MSEC(COMMUNICATION_EVENT_CHECK_INTERVAL_MS));
        }
    }

    if(result == -EAGAIN)
    {
        result = -ETIMEDOUT;
    }

    return result;
}

static int communication_waitForScanResult(void)
{
    k_timepoint_t deadline = sys_timepoint_calc(K_SECONDS(COMMUNICATION_SCAN_TIMEOUT_S));
    int result = -EAGAIN;

    while((result == -EAGAIN) && !sys_timepoint_expired(deadline))
    {
        communication_waitForEvents(K_NO_WAIT);

        if(communication_ListeningIsActive)
        {
            result = -ECANCELED;
        }
        else
        {
            result = wifi_waitForScanResult(communication_ScanList,
                                            COMMUNICATION_SCAN_LIST_SIZE,
                                            K_MSEC(COMMUNICATION_EVENT_CHECK_INTERVAL_MS));

            if(result >= 0)
            {
                communication_ScanCount = (size_t)result;
                result = 0;
            }
        }
    }

    if(result == -EAGAIN)
    {
        result = -ETIMEDOUT;
    }

    return result;
}

static int communication_connectToNetwork(const struct wifi_network *network, int attempts)
{
    int result = -ECANCELED;
    int attempt = 0;
    bool retry = true;

    while(retry)
    {
        attempt++;

        communication_waitForEvents(K_NO_WAIT);

        if(communication_ListeningIsActive)
        {
            result = -ECANCELED;
        }
        else
        {
            result = wifi_connect(network);

            if(result == 0)
            {
                communication_ConnectionIsPending = true;
                result = communication_waitForConnection();

                if(result == 0)
                {
                    communication_ConnectionIsPending = false;
                }
            }
        }

        if(result == 0)
        {
            communication_RecoveryIsAllowed = true;
        }
        else
        {
            if(communication_ConnectionIsPending)
            {
                int cleanup = wifi_disconnect();

                communication_ConnectionIsPending = (cleanup != 0);

                if(cleanup != 0)
                {
                    result = cleanup;
                }
            }

            if(result != -ECANCELED)
            {
                LOG_WRN("Connect attempt %d/%d failed (%d)", attempt, attempts, result);

                if((attempt < attempts) && !communication_ConnectionIsPending)
                {
                    communication_waitForDelay(K_SECONDS(COMMUNICATION_RETRY_DELAY_S));

                    if(communication_ListeningIsActive)
                    {
                        result = -ECANCELED;
                    }
                }
            }
        }

        retry = (result != 0) && (result != -ECANCELED) && !communication_ConnectionIsPending && (attempt < attempts);
    }

    return result;
}

static int communication_scanNetworks(void)
{
    int result = -ECANCELED;
    int attempt = 0;
    bool retry = true;

    while(retry)
    {
        attempt++;

        communication_waitForEvents(K_NO_WAIT);

        if(communication_ListeningIsActive)
        {
            result = -ECANCELED;
        }
        else
        {
            result = wifi_startScan();

            if(result == 0)
            {
                communication_ScanIsPending = true;
                result = communication_waitForScanResult();

                if((result != -ECANCELED) && (result != -ETIMEDOUT))
                {
                    communication_ScanIsPending = false;
                }
                else
                {
                    int cleanup = wifi_cancelScan();

                    communication_ScanIsPending = (cleanup != 0);

                    if(cleanup != 0)
                    {
                        result = cleanup;
                    }
                }
            }
        }

        if((result != 0) && (result != -ECANCELED))
        {
            LOG_WRN("Scan attempt %d/%d failed (%d)", attempt, COMMUNICATION_SCAN_ATTEMPTS, result);

            if((attempt < COMMUNICATION_SCAN_ATTEMPTS) && !communication_ScanIsPending)
            {
                communication_waitForDelay(K_SECONDS(COMMUNICATION_RETRY_DELAY_S));

                if(communication_ListeningIsActive)
                {
                    result = -ECANCELED;
                }
            }
        }

        retry = (result != 0) && (result != -ECANCELED) && !communication_ScanIsPending && (attempt < COMMUNICATION_SCAN_ATTEMPTS);
    }

    if(result == 0)
    {
        portal_setNetworks(communication_ScanList, communication_ScanCount);
    }

    return result;
}

static void communication_runSetup(void)
{
    k_spinlock_key_t key = k_spin_lock(&communication_ControlLock);

    communication_SetupIsActive = true;

    k_spin_unlock(&communication_ControlLock, key);
    LOG_INF("Wi-Fi setup: scanning");

    /* Scan before the hotspot opens, so the list is ready when the phone joins (item 1). */
    int result = communication_scanNetworks();

    if(result != 0)
    {
        if(result != -ECANCELED)
        {
            LOG_ERR("SCAN_FAILURE (%d); hold the button 2 s to retry", result);
        }
    }
    else if(communication_openSetup() == 0)
    {
        int error = 0;
        enum communication_setup_result outcome = communication_servePage(&error);

        communication_closeSetup(outcome, error);
    }
    else
    {
        /* Release even partially started services; failed cleanup remains pending. */
    }

    (void)communication_stopWiFiWork();

    key = k_spin_lock(&communication_ControlLock);
    communication_SetupIsActive = false;

    k_spin_unlock(&communication_ControlLock, key);
}

static int communication_openSetup(void)
{
    communication_waitForEvents(K_NO_WAIT);

    int result = -ECANCELED;

    if(!communication_ListeningIsActive)
    {
        communication_HotspotIsActive = true;
        result = wifi_startHotspot();
    }

    if(result != 0)
    {
        LOG_ERR("HOTSPOT_START_FAILURE (%d); hold the button 2 s to retry", result);
    }
    else
    {
        communication_waitForEvents(K_NO_WAIT);

        communication_DHCPServerIsActive = !communication_ListeningIsActive;

        if(communication_ListeningIsActive)
        {
            result = -ECANCELED;
        }
        else
        {
            result = wifi_startDHCPServer();
        }

        if(result != 0)
        {
            LOG_ERR("DHCP server start failed (%d); hold the button 2 s to retry", result);
            /* runSetup performs checked teardown. */
        }
        else
        {
            portal_setStatus(PORTAL_STATUS_SELECTING, 0);

            communication_waitForEvents(K_NO_WAIT);

            communication_PortalIsActive = !communication_ListeningIsActive;

            if(communication_ListeningIsActive)
            {
                result = -ECANCELED;
            }
            else
            {
                result = portal_start();
            }

            if(result != 0)
            {
                LOG_ERR("Setup page start failed (%d); hold the button 2 s to retry", result);
                /* runSetup performs checked teardown. */
            }
            else
            {
                LOG_INF("Wi-Fi setup open: join the hotspot and open http://192.168.4.1");
            }
        }
    }

    return result;
}

static enum communication_setup_result communication_servePage(int *error)
{
    k_timepoint_t idleDeadline = sys_timepoint_calc(K_SECONDS(COMMUNICATION_SETUP_INACTIVITY_TIMEOUT_S));
    enum communication_setup_result outcome = COMMUNICATION_SETUP_RUNNING;

    *error = 0;

    while(outcome == COMMUNICATION_SETUP_RUNNING)
    {
        /* A hold during setup has no meaning; setup is already open. */
        communication_SetupIsRequested = false;

        communication_waitForEvents(K_NO_WAIT);

        if(communication_ListeningIsActive)
        {
            outcome = COMMUNICATION_SETUP_INTERRUPTED;
        }
        else if(sys_timepoint_expired(idleDeadline))
        {
            LOG_INF("Wi-Fi setup: no activity for 5 min");

            outcome = COMMUNICATION_SETUP_CANCELLED;
        }
        else if(portal_waitForRequest(&communication_PageRequest, K_MSEC(COMMUNICATION_EVENT_CHECK_INTERVAL_MS)) == 0)
        {
            outcome = communication_handlePageRequest(error);

            /* Every request and the end of its work restart the timer, so it pauses
             * during operations (P21). */
            idleDeadline = sys_timepoint_calc(K_SECONDS(COMMUNICATION_SETUP_INACTIVITY_TIMEOUT_S));
        }
        else
        {
            /* Empty slices keep the Start and timeout checks running. */
        }
    }

    return outcome;
}

static enum communication_setup_result communication_handlePageRequest(int *error)
{
    enum communication_setup_result outcome = COMMUNICATION_SETUP_RUNNING;
    int result = 0;

    switch(communication_PageRequest.type)
    {
    case PORTAL_REQUEST_CANCEL:
        outcome = COMMUNICATION_SETUP_CANCELLED;
        break;

    case PORTAL_REQUEST_ACTIVITY:
        /* The page sends it while the user types, so setup stays open during input (P21). */
        break;

    case PORTAL_REQUEST_RESCAN:
        portal_setStatus(PORTAL_STATUS_SCANNING, 0);

        result = communication_scanNetworks();

        if(result == 0)
        {
            portal_setStatus(PORTAL_STATUS_SELECTING, 0);
        }

        break;

    case PORTAL_REQUEST_CONNECT:
        result = communication_handleConnectRequest();

        if(result == 0)
        {
            outcome = COMMUNICATION_SETUP_CONNECTED;
        }
        else if(result != -ECANCELED)
        {
            /* The page keeps showing the join cause while the list updates. */
            result = communication_scanNetworks();
        }
        else
        {
            /* No rescan: listening has priority (P19). */
        }

        break;

    default:
        break;
    }

    if(result == -ECANCELED)
    {
        outcome = COMMUNICATION_SETUP_INTERRUPTED;
    }
    else if(result != 0)
    {
        /* An exhausted scan ends setup with an error (wifi-flow.puml). */
        *error = result;
        outcome = COMMUNICATION_SETUP_FAILED;
    }
    else
    {
        /* Success needs no change: the request already set the outcome. */
    }

    return outcome;
}

static int communication_handleConnectRequest(void)
{
    struct wifi_network *network = &communication_PageRequest.network;

    LOG_INF("Wi-Fi setup: joining \"%s\"", network->name);
    portal_setStatus(PORTAL_STATUS_CONNECTING, 0);

    /* The hotspot stays open, so the phone keeps polling the status during the join
     * (item 3). */
    int result = communication_connectToNetwork(network, COMMUNICATION_PAGE_CONNECT_ATTEMPTS);

    if(result == 0)
    {
        communication_saveNetwork(network);
    }
    else
    {
        communication_discardPageRequests();

        if(result != -ECANCELED)
        {
            LOG_WRN("Wi-Fi setup: join failed (%d)", result);
            portal_setStatus(PORTAL_STATUS_CONNECT_FAILED, result);
        }
    }

    (void)memset(network->password, 0, sizeof(network->password));

    if(result == 0)
    {
        /* Start during the result display ends setup at once. Requests stay
         * unread until the page closes, so the user cannot cancel meanwhile. */
        communication_waitForDelay(K_SECONDS(COMMUNICATION_RESULT_DISPLAY_S));
    }

    return result;
}

static void communication_saveNetwork(const struct wifi_network *network)
{
    int result = 0;
    int attempt = 0;

    /* Settings writes finish even if listening starts meanwhile (item 6). */
    do
    {
        attempt++;
        result = wifi_storeSettings(network);

        if(result != 0)
        {
            LOG_WRN("Save attempt %d/%d failed (%d)", attempt, COMMUNICATION_SAVE_ATTEMPTS, result);
        }
    } while((result != 0) && (attempt < COMMUNICATION_SAVE_ATTEMPTS));

    if(result == 0)
    {
        LOG_INF("Wi-Fi setup: joined and saved");
        portal_setStatus(PORTAL_STATUS_CONNECTED, 0);
    }
    else
    {
        /* The connection stays; flash keeps the previous valid record (item 9). */
        LOG_ERR("WIFI_SETTINGS_SAVE_FAILURE (%d); network not saved", result);
        portal_setStatus(PORTAL_STATUS_SAVE_FAILED, result);
    }

    /* Reconnect to the joined network, also when it could not be saved. */
    communication_StoredNetwork = *network;
    communication_StoredNetworkIsValid = true;
    communication_RecoveryIsAllowed = true;
}

static void communication_discardPageRequests(void)
{
    while(portal_waitForRequest(&communication_PageRequest, K_NO_WAIT) == 0)
    {
        (void)memset(communication_PageRequest.network.password,
                     0,
                     sizeof(communication_PageRequest.network.password));
    }
}

static void communication_closeSetup(enum communication_setup_result outcome, int error)
{
    if(outcome == COMMUNICATION_SETUP_FAILED)
    {
        LOG_ERR("SCAN_FAILURE (%d); closing setup, hold the button 2 s to retry", error);
    }

    /* Start must not wait for a notice; a joined page already showed its result. */
    if((outcome == COMMUNICATION_SETUP_CANCELLED) || (outcome == COMMUNICATION_SETUP_FAILED))
    {
        portal_setStatus(PORTAL_STATUS_CLOSING, error);
        communication_waitForDelay(K_SECONDS(COMMUNICATION_CLOSE_NOTICE_DISPLAY_S));
    }

    (void)communication_stopWiFiWork();

    LOG_INF("Wi-Fi setup closed (%d)", outcome);
}

/** @} */
