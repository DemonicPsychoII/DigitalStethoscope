/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L2_COMMUNICATION
 * @{
 * @file
 * Implementation of the COMMUNICATION module: the Wi-Fi workflow thread.
 *
 * Workflow (architecture/COMMUNICATION/setup-state.puml, setup-flow.puml and
 * link-recovery.puml):
 * - Boot: join the stored network, 4 attempts, 5 s apart. Without a stored
 *   network, run setup. If all attempts fail, wait for a 2 s button hold.
 * - Setup: scan, then open the hotspot, the DHCP server and the page.
 *   - Connect: one join attempt. On success, save the network and show the
 *     result for 10 s. On failure, show the cause and scan again.
 *   - Rescan: scan again with the hotspot open.
 *   - Cancel, or 5 min without activity: show a notice, then close.
 *   - If a scan fails 4 times, setup closes with the cause.
 * - Idle: a 2 s hold runs setup. Every 2 min, check the link. If it is
 *   lost, join again (4 attempts) and run setup if all attempts fail.
 * - Listening: no Wi-Fi work, but a connected station stays connected.
 *   All waits run in 200 ms intervals, so a Start is seen quickly.
 *
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
#include "storage.h"
#include "wifi.h"

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

#define COMMUNICATION_THREAD_STACK_SIZE (4096) /**< Size of the communication thread stack. */
#define COMMUNICATION_THREAD_PRIORITY   (10)   /**< Priority of the communication thread. */

#define COMMUNICATION_STORED_CONNECT_ATTEMPTS     (4)      /**< Join attempts at boot and after a link loss. */
#define COMMUNICATION_PAGE_CONNECT_ATTEMPTS       (1)      /**< Join attempts for a Connect from the page. */
#define COMMUNICATION_SCAN_ATTEMPTS               (4)      /**< Scan attempts in total. */
#define COMMUNICATION_SAVE_ATTEMPTS               (2)      /**< Save attempts for the joined network. */
#define COMMUNICATION_RETRY_DELAY_S               (5)      /**< Delay after a failed attempt. */
#define COMMUNICATION_CONNECT_TIMEOUT_S           (15)     /**< Longest wait for one join. */
#define COMMUNICATION_SCAN_TIMEOUT_S              (10)     /**< Longest wait for one scan. */
#define COMMUNICATION_SETUP_INACTIVITY_TIMEOUT_S  (5 * 60) /**< Setup closes after this time without page activity. */
#define COMMUNICATION_RESULT_DISPLAY_S            (10)     /**< Time the page shows the join result. */
#define COMMUNICATION_CLOSE_NOTICE_DISPLAY_S      (2)      /**< Time the page shows the closing notice. */
#define COMMUNICATION_CONNECTION_CHECK_INTERVAL_S (2 * 60) /**< Link check interval in Idle. */
#define COMMUNICATION_EVENT_CHECK_INTERVAL_MS     (200)    /**< Wait interval; longest delay to see a Start. */

#define COMMUNICATION_NETWORK_RECORD "wifi/network" /**< Storage name of the joined network. */

#define COMMUNICATION_WORK_SCAN       BIT(0) /**< Scan started. */
#define COMMUNICATION_WORK_CONNECTION BIT(1) /**< Connect request pending. */
#define COMMUNICATION_WORK_PORTAL     BIT(2) /**< Setup page served. */
#define COMMUNICATION_WORK_DHCP       BIT(3) /**< DHCP server running. */
#define COMMUNICATION_WORK_HOTSPOT    BIT(4) /**< Hotspot open. */

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/** State of the communication thread, as seen by CONTROL. */
enum communication_state
{
    COMMUNICATION_STATE_RUNNING, /**< Boot, Idle or recovery. */
    COMMUNICATION_STATE_SETUP,   /**< Setup runs; a 2 s hold is ignored. */
    COMMUNICATION_STATE_STOPPED, /**< Wi-Fi work stopped for listening. */
    COMMUNICATION_STATE_OFFLINE, /**< Wi-Fi init failed; the thread has ended. */
};

/** Condition observed by the shared bounded wait. */
enum communication_wait_target
{
    COMMUNICATION_WAIT_CONTROL_EVENT, /**< Wait for a control event or the supplied timeout, then refresh the listening request. */
    COMMUNICATION_WAIT_DELAY,         /**< Wait for the full delay; Start ends it immediately when observed. */
    COMMUNICATION_WAIT_CONNECTION,    /**< Wait for a join result; completion, failure, deadline or Start ends it. */
    COMMUNICATION_WAIT_SCAN_LIST,     /**< Wait for the complete scan list; completion, failure, deadline or Start ends it. */
    COMMUNICATION_WAIT_WIFI_STOP,     /**< Wait for a stopped/offline acknowledgement of Start, or return pending at the deadline. */
};

/** How setup ended. */
enum communication_setup_result
{
    COMMUNICATION_SETUP_RUNNING,     /**< Setup still serves the page. */
    COMMUNICATION_SETUP_CONNECTED,   /**< Joined a network; the page showed the result. */
    COMMUNICATION_SETUP_CANCELLED,   /**< Cancel on the page or 5 min without activity. */
    COMMUNICATION_SETUP_FAILED,      /**< A scan failed; setup cannot continue. */
    COMMUNICATION_SETUP_INTERRUPTED, /**< Listening started. */
};

/** Wi-Fi work that must be stopped before listening. */
struct communication_work
{
    uint32_t bit;      /**< COMMUNICATION_WORK_* bit. */
    int (*stop)(void); /**< Stops the work; 0 on success. */
    const char *name;  /**< Name for the log. */
};

/***********************************************************************/
/* GLOBAL CONSTANTS                                                    */
/***********************************************************************/

/***********************************************************************/
/* LOCAL CONSTANTS                                                     */
/***********************************************************************/

/** Work in the order it is stopped: radio work first, then the setup services. */
static const struct communication_work communication_WorkList[] = {
    {COMMUNICATION_WORK_SCAN, wifi_cancelScan, "Scan"},
    {COMMUNICATION_WORK_CONNECTION, wifi_disconnect, "Connect request"},
    {COMMUNICATION_WORK_PORTAL, portal_stop, "Setup page"},
    {COMMUNICATION_WORK_DHCP, wifi_stopDHCPServer, "DHCP server"},
    {COMMUNICATION_WORK_HOTSPOT, wifi_stopHotspot, "Hotspot"},
};

/***********************************************************************/
/* GLOBAL VARIABLES                                                    */
/***********************************************************************/

/***********************************************************************/
/* LOCAL VARIABLES                                                     */
/***********************************************************************/

K_THREAD_STACK_DEFINE(communication_Stack, COMMUNICATION_THREAD_STACK_SIZE); /**< Communication stack. */
K_SEM_DEFINE(communication_ControlChanged, 0, 1);                            /**< Wakes the thread after an event. */

static struct k_thread communication_ThreadData; /**< Communication thread. */

/* Shared with CONTROL; protected by communication_ControlLock. */
static struct k_spinlock communication_ControlLock;  /**< Protects the variables below. */
static bool communication_ListeningIsRequested;      /**< CONTROL listens or is about to. */
static bool communication_SetupIsRequested;          /**< 2 s hold not yet handled. */
static enum communication_state communication_State; /**< State of the thread. */

/* Used by the communication thread only. */
static bool communication_ListeningIsActive;            /**< Copy of ListeningIsRequested from the last event check. */
static uint32_t communication_PendingWork;              /**< COMMUNICATION_WORK_* bits not yet stopped. */
static struct wifi_network communication_StoredNetwork; /**< Network for boot and recovery. */
static bool communication_StoredNetworkIsValid;         /**< StoredNetwork holds a network. */
static bool communication_CleanupFaultIsLatched;
static bool communication_BootJoinIsPending;
static int communication_BootAttemptsUsed;
static bool communication_RecoveryIsAllowed;                               /**< A connection was up and no recovery has failed since. */
static struct portal_request communication_PageRequest;                    /**< Last page request, with password. */
static struct wifi_scan_entry communication_ScanList[WIFI_SCAN_LIST_SIZE]; /**< Networks for the page. */
static size_t communication_ScanCount;                                     /**< Valid entries in ScanList. */

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
 * @brief Wait until the selected condition is met, Start interrupts it or the time is over.
 *
 * @param[in] target  Condition to wait for.
 * @param[in] timeout Longest wait.
 *
 * @return 0 when the condition is met, -ECANCELED if listening started,
 *         -ETIMEDOUT if a join or scan gave no result in time,
 *         -EAGAIN if Wi-Fi has not stopped in time, or a Wi-Fi error code.
 */
static int communication_waitForCondition(enum communication_wait_target target, k_timeout_t timeout);

/**
 * @brief Check the selected condition once.
 *
 * Join and scan checks wait up to one event check interval for the radio.
 *
 * @param[in] target   Condition to check.
 * @param[in] deadline End of the whole wait.
 *
 * @return 0 when the condition is met, -EAGAIN while it is pending, or the error that ended it.
 */
static int communication_checkWaitTarget(enum communication_wait_target target, k_timepoint_t deadline);

/**
 * @brief Pause before the next check of the selected condition.
 *
 * @param[in] target   Condition that is waited for.
 * @param[in] deadline End of the whole wait.
 */
static void communication_pauseBeforeNextCheck(enum communication_wait_target target, k_timepoint_t deadline);

/** @brief Take over the listening request that CONTROL posted last. */
static void communication_updateListeningState(void);

/**
 * @brief Tell whether a 2 s hold waits for setup.
 *
 * @return True if setup is requested.
 */
static bool communication_isSetupRequested(void);

/**
 * @brief Set the state of the thread.
 *
 * @param[in] state New state.
 */
static void communication_setState(enum communication_state state);

/**
 * @brief Stop all pending Wi-Fi work; a connected station stays connected.
 *
 * Each pending stop is tried once; a failed stop latches a restart-required fault.
 *
 * @return True when audio may be released. This is also true after a latched
 *         cleanup fault (REQ-13 Wi-Fi-only exception), while services may still be
 *         pending; it does not assert radio shutdown.
 */
static bool communication_stopWiFiWork(void);

/**
 * @brief Run an attempt function up to @p attempts times, COMMUNICATION_RETRY_DELAY_S apart.
 *
 * @param[in] tryOnce  One attempt; returns 0 on success.
 * @param[in] network  Argument for @p tryOnce.
 * @param[in] attempts Number of attempts in total.
 * @param[in] workBit  Work of the attempt; no retry while it is still pending.
 * @param[in] name     Name for the log.
 *
 * @return 0 on success, -ECANCELED if listening started, or the last error code.
 */
static int communication_retry(int (*tryOnce)(const struct wifi_network *network), const struct wifi_network *network, int attempts, uint32_t workBit, const char *name);

/**
 * @brief Send one connect request and wait until online.
 *
 * @param[in] network Network to join.
 *
 * @return 0 when online, -ECANCELED if listening started, or an error code.
 */
static int communication_tryConnect(const struct wifi_network *network);

/**
 * @brief Run one scan and wait for its list.
 *
 * @param[in] network Unused; the signature matches communication_retry().
 *
 * @return 0 on success, -ECANCELED if listening started, or an error code.
 */
static int communication_tryScan(const struct wifi_network *network);

/**
 * @brief Connect to a network, with COMMUNICATION_RETRY_DELAY_S between failed attempts.
 *
 * @param[in] network  Network to join.
 * @param[in] attempts Number of attempts in total.
 *
 * @return 0 when online, -ECANCELED if listening started, or the last error code.
 */
static int communication_connectToNetwork(const struct wifi_network *network, int attempts);

/**
 * @brief Scan into communication_ScanList and publish the list for the page.
 *
 * If all attempts fail, the previous list stays.
 *
 * @return 0 on success, -ECANCELED if listening started, or the last error code.
 */
static int communication_scanNetworks(void);

/**
 * @brief Run the whole setup: scan, open the page, serve it, close it.
 */
static void communication_runSetup(void);

/**
 * @brief Start one setup service, unless listening has started.
 *
 * @param[in] workBit Work bit of the service.
 * @param[in] start   Starts the service; 0 on success.
 *
 * @return 0 on success, -ECANCELED if listening started, or the error code of @p start.
 */
static int communication_startService(uint32_t workBit, int (*start)(void));

/**
 * @brief Start the hotspot, the DHCP server and the page.
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
 * @brief Drop page requests sent while a join ran.
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
        communication_SetupIsRequested = false;
        break;

    case COMMUNICATION_EVENT_LISTENING_STOPPED:
        communication_ListeningIsRequested = false;
        break;

    case COMMUNICATION_EVENT_SETUP_REQUESTED:
        if(!communication_ListeningIsRequested && (communication_State != COMMUNICATION_STATE_SETUP))
        {
            communication_SetupIsRequested = true;
        }

        break;

    default:
        result = -EINVAL; /**< Invalid argument or unsupported input. */
        break;
    }

    /* A new Start or Stop needs a new confirmation from the thread. */
    if((result == 0) && (event != COMMUNICATION_EVENT_SETUP_REQUESTED) && (communication_State == COMMUNICATION_STATE_STOPPED))
    {
        communication_State = COMMUNICATION_STATE_RUNNING;
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
    return communication_waitForCondition(COMMUNICATION_WAIT_WIFI_STOP, timeout);
}

/***********************************************************************/
/* LOCAL FUNCTIONS                                                     */
/***********************************************************************/

static void communication_thread(void *arg1, void *arg2, void *arg3)
{
    ARG_UNUSED(arg1);
    ARG_UNUSED(arg2);
    ARG_UNUSED(arg3);

    /* On failure the stored network cannot be read either, so setup opens. */
    (void)storage_init();

    int result = wifi_init();

    if(result != 0)
    {
        /* Audio works without Wi-Fi, so control must not wait for this thread. */
        LOG_ERR("Wi-Fi init failed (%d); device stays offline", result);
        communication_setState(COMMUNICATION_STATE_OFFLINE);
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
    int result = storage_read(COMMUNICATION_NETWORK_RECORD, &communication_StoredNetwork, sizeof(communication_StoredNetwork));

    if((result == 0) && !wifi_isValidNetwork(&communication_StoredNetwork))
    {
        /* A damaged record must not reach the connect request. */
        (void)memset(&communication_StoredNetwork, 0, sizeof(communication_StoredNetwork));

        result = -EINVAL; /**< Invalid argument or unsupported input. */
    }

    if(result != 0)
    {
        (void)memset(&communication_StoredNetwork, 0, sizeof(communication_StoredNetwork));
        communication_StoredNetworkIsValid = false;

        if(result != -ENOENT) /**< Requested record or network was not found. */
        {
            LOG_ERR("Stored Wi-Fi network load failed (%d)", result);
        }

        LOG_INF("No stored Wi-Fi network; opening setup");
        communication_runSetup();
    }
    else
    {
        communication_StoredNetworkIsValid = true;

        LOG_INF("Connecting to \"%s\"", communication_StoredNetwork.name);

        communication_BootJoinIsPending = true;
        communication_BootAttemptsUsed = 0;
        result = communication_connectToNetwork(&communication_StoredNetwork, COMMUNICATION_STORED_CONNECT_ATTEMPTS);
        communication_BootJoinIsPending = (result == -ECANCELED); /**< Start interrupted the network workflow. */

        if(result == 0)
        {
            LOG_INF("Wi-Fi connected");
        }
        else if(result == -ECANCELED) /**< Start interrupted the network workflow. */
        {
            communication_RecoveryIsAllowed = false;
        }
        else
        {
            LOG_ERR("JOIN_FAILURE (%d); hold the button 2 s for setup", result);
        }
    }
}

static void communication_runIdleCycle(void)
{
    (void)communication_waitForCondition(COMMUNICATION_WAIT_CONTROL_EVENT, K_NO_WAIT);

    bool isStopped = communication_stopWiFiWork();

    if(communication_ListeningIsActive)
    {
        k_spinlock_key_t key = k_spin_lock(&communication_ControlLock);

        if((isStopped && communication_ListeningIsRequested))
        {
            communication_State = COMMUNICATION_STATE_STOPPED;
        }
        else
        {
            communication_State = COMMUNICATION_STATE_RUNNING;
        }

        k_spin_unlock(&communication_ControlLock, key);

        if(isStopped)
        {
            (void)communication_waitForCondition(COMMUNICATION_WAIT_CONTROL_EVENT, K_FOREVER);
        }
        else
        {
            (void)communication_waitForCondition(COMMUNICATION_WAIT_CONTROL_EVENT, K_MSEC(COMMUNICATION_EVENT_CHECK_INTERVAL_MS));
        }

        if(isStopped && !communication_ListeningIsActive)
        {
            /* Back in Idle: continue a recovery that listening interrupted. */
            communication_recoverConnection();
        }
    }
    else if(communication_CleanupFaultIsLatched)
    {
        (void)communication_waitForCondition(COMMUNICATION_WAIT_CONTROL_EVENT, K_FOREVER);
    }
    else if(communication_isSetupRequested())
    {
        communication_runSetup();
    }
    else if(communication_BootJoinIsPending)
    {
        communication_recoverConnection();
    }
    else
    {
        (void)communication_waitForCondition(COMMUNICATION_WAIT_CONTROL_EVENT, K_SECONDS(COMMUNICATION_CONNECTION_CHECK_INTERVAL_S));

        if(!communication_ListeningIsActive)
        {
            communication_recoverConnection();
        }
    }
}

static void communication_recoverConnection(void)
{
    if(communication_CleanupFaultIsLatched)
    {
        return;
    }

    /* Resume interrupted boot attempts only while Idle and without a setup request. */
    if(communication_BootJoinIsPending && !communication_ListeningIsActive && !communication_isSetupRequested())
    {
        (void)communication_waitForCondition(COMMUNICATION_WAIT_DELAY, K_SECONDS(COMMUNICATION_RETRY_DELAY_S));
        int remainingAttempts = COMMUNICATION_STORED_CONNECT_ATTEMPTS - communication_BootAttemptsUsed;
        int result;
        if(communication_ListeningIsActive)
        {
            result = -ECANCELED; /**< Start interrupted the network workflow. */
        }
        else
        {
            result = communication_connectToNetwork(&communication_StoredNetwork, remainingAttempts);
        }
        communication_BootJoinIsPending = (result == -ECANCELED); /**< Start interrupted the network workflow. */
        if((result != 0) && (result != -ECANCELED))               /**< Start interrupted the network workflow. */
        {
            communication_RecoveryIsAllowed = false;
            LOG_ERR("JOIN_FAILURE (%d); hold the button 2 s for setup", result);
        }
        return;
    }

    /* Reconnect only an eligible stored station whose link has been lost. */
    if(!communication_isSetupRequested() && communication_RecoveryIsAllowed && communication_StoredNetworkIsValid && !wifi_isConnected())
    {
        LOG_WRN("Wi-Fi link lost; reconnecting");

        int result = communication_connectToNetwork(&communication_StoredNetwork, COMMUNICATION_STORED_CONNECT_ATTEMPTS);

        if(result == 0)
        {
            LOG_INF("Wi-Fi reconnected");
        }
        else if(result != -ECANCELED) /**< Start interrupted the network workflow. */
        {
            LOG_ERR("RECONNECT_FAILURE (%d); opening setup", result);

            communication_RecoveryIsAllowed = false;

            communication_runSetup();
        }
        else
        {
            /* Listening started; RecoveryIsAllowed stays set, so Idle tries again. */
        }
    }
}

static int communication_waitForCondition(enum communication_wait_target target, k_timeout_t timeout)
{
    k_timepoint_t deadline = sys_timepoint_calc(timeout);
    int result = 0;
    bool isWaiting = true;

    while(isWaiting)
    {
        result = communication_checkWaitTarget(target, deadline);
        isWaiting = (result == -EAGAIN) && !sys_timepoint_expired(deadline); /**< Condition still pending and time left. */
        if(isWaiting)
        {
            communication_pauseBeforeNextCheck(target, deadline);
        }
    }

    bool isRadioWait = (target == COMMUNICATION_WAIT_CONNECTION) || (target == COMMUNICATION_WAIT_SCAN_LIST); /**< Join or scan result from the radio. */
    if(isRadioWait && (result == -EAGAIN))
    {
        result = -ETIMEDOUT; /**< No radio result arrived before the deadline. */
    }

    return result;
}

static int communication_checkWaitTarget(enum communication_wait_target target, k_timepoint_t deadline)
{
    int result = -EAGAIN;                                                                                                                                  /**< Condition is still pending. */
    bool isStoppedByStart = (target == COMMUNICATION_WAIT_DELAY) || (target == COMMUNICATION_WAIT_CONNECTION) || (target == COMMUNICATION_WAIT_SCAN_LIST); /**< Start ends this wait early. */

    if(isStoppedByStart)
    {
        (void)k_sem_take(&communication_ControlChanged, K_NO_WAIT);
        communication_updateListeningState();
    }

    if(isStoppedByStart && communication_ListeningIsActive)
    {
        result = -ECANCELED; /**< Start takes priority over the wait. */
    }
    else
    {
        switch(target)
        {
        case COMMUNICATION_WAIT_CONTROL_EVENT:
            (void)k_sem_take(&communication_ControlChanged, sys_timepoint_timeout(deadline));
            communication_updateListeningState();
            result = 0;
            break;
        case COMMUNICATION_WAIT_DELAY:
            if(sys_timepoint_expired(deadline))
            {
                result = 0;
            }
            break;
        case COMMUNICATION_WAIT_CONNECTION:
            result = wifi_waitForConnection(K_MSEC(COMMUNICATION_EVENT_CHECK_INTERVAL_MS));
            break;
        case COMMUNICATION_WAIT_SCAN_LIST:
            result = wifi_waitForScanResult(communication_ScanList, WIFI_SCAN_LIST_SIZE, K_MSEC(COMMUNICATION_EVENT_CHECK_INTERVAL_MS));
            if(result >= 0)
            {
                communication_ScanCount = (size_t)result;
                result = 0;
            }
            break;
        case COMMUNICATION_WAIT_WIFI_STOP:
        {
            k_spinlock_key_t key = k_spin_lock(&communication_ControlLock);
            bool isStopped = communication_ListeningIsRequested &&
                             ((communication_State == COMMUNICATION_STATE_STOPPED) ||
                              (communication_State == COMMUNICATION_STATE_OFFLINE)); /**< Start has a stopped or offline network acknowledgement. */
            k_spin_unlock(&communication_ControlLock, key);
            if(isStopped)
            {
                result = 0;
            }
            break;
        }
        default:
            result = -EINVAL; /**< Wait target is invalid. */
            break;
        }
    }

    return result;
}

static void communication_pauseBeforeNextCheck(enum communication_wait_target target, k_timepoint_t deadline)
{
    k_timeout_t remaining = sys_timepoint_timeout(deadline);

    if(target == COMMUNICATION_WAIT_DELAY)
    {
        /* Every control event wakes the delay, so a Start is seen at once. */
        (void)k_sem_take(&communication_ControlChanged, remaining);
    }
    else if(target == COMMUNICATION_WAIT_WIFI_STOP)
    {
        if(K_TIMEOUT_EQ(remaining, K_FOREVER) || (remaining.ticks > K_MSEC(COMMUNICATION_EVENT_CHECK_INTERVAL_MS).ticks))
        {
            remaining = K_MSEC(COMMUNICATION_EVENT_CHECK_INTERVAL_MS);
        }
        (void)k_sleep(remaining);
    }
    else
    {
        /* Join and scan checks already waited for the radio. */
    }
}

static void communication_updateListeningState(void)
{
    k_spinlock_key_t key = k_spin_lock(&communication_ControlLock);
    communication_ListeningIsActive = communication_ListeningIsRequested;
    k_spin_unlock(&communication_ControlLock, key);
}

static bool communication_isSetupRequested(void)
{
    k_spinlock_key_t key = k_spin_lock(&communication_ControlLock);
    bool isRequested = communication_SetupIsRequested;

    k_spin_unlock(&communication_ControlLock, key);

    return isRequested;
}

static void communication_setState(enum communication_state state)
{
    k_spinlock_key_t key = k_spin_lock(&communication_ControlLock);

    communication_State = state;

    if(state == COMMUNICATION_STATE_SETUP)
    {
        /* Setup opens now, so a hold before this point is handled. */
        communication_SetupIsRequested = false;
    }

    k_spin_unlock(&communication_ControlLock, key);
}

static bool communication_stopWiFiWork(void)
{
    if(communication_CleanupFaultIsLatched)
    {
        return true;
    }

    for(size_t index = 0U; index < ARRAY_SIZE(communication_WorkList); index++)
    {
        const struct communication_work *work = &communication_WorkList[index];
        if((communication_PendingWork & work->bit) != 0U)
        {
            int result = work->stop();
            if(result == 0)
            {
                communication_PendingWork &= ~work->bit;
            }
        }
    }
    if(communication_PendingWork != 0U)
    {
        communication_CleanupFaultIsLatched = true;
        communication_RecoveryIsAllowed = false;
        communication_BootJoinIsPending = false;
        LOG_ERR("WIFI_CLEANUP_FAILURE; pending services 0x%x, network disabled until restart", communication_PendingWork);
    }
    /* REQ-13 permits audio after a latched Wi-Fi-only fault, without claiming radio shutdown. */
    return true;
}

static int communication_retry(int (*tryOnce)(const struct wifi_network *network), const struct wifi_network *network, int attempts, uint32_t workBit, const char *name)
{
    int result = -ETIMEDOUT; /**< Operation exceeded its wait deadline. */
    int attempt = 0;
    bool isRetryDue = attempts > 0;

    while(isRetryDue)
    {
        (void)communication_waitForCondition(COMMUNICATION_WAIT_CONTROL_EVENT, K_NO_WAIT);

        if(communication_ListeningIsActive)
        {
            result = -ECANCELED; /**< Start interrupted the network workflow. */
        }
        else
        {
            attempt++;
            /* Resume interrupted boot attempts only while Idle and without a setup request. */
            if(communication_BootJoinIsPending && (tryOnce == communication_tryConnect))
            {
                communication_BootAttemptsUsed++;
            }
            result = tryOnce(network);
        }

        if((result != 0) && (result != -ECANCELED)) /**< Start interrupted the network workflow. */
        {
            LOG_WRN("%s attempt %d/%d failed (%d)", name, attempt, attempts, result);
        }

        /* Do not start again while the driver may still work on the last attempt. */
        isRetryDue = (result != 0) && (result != -ECANCELED) && ((communication_PendingWork & workBit) == 0U) && (attempt < attempts); /**< Start interrupted the network workflow. */

        if(isRetryDue)
        {
            (void)communication_waitForCondition(COMMUNICATION_WAIT_DELAY, K_SECONDS(COMMUNICATION_RETRY_DELAY_S));

            if(communication_ListeningIsActive)
            {
                result = -ECANCELED; /**< Start interrupted the network workflow. */
                isRetryDue = false;
            }
        }
    }

    return result;
}

static int communication_tryConnect(const struct wifi_network *network)
{
    int result = wifi_connect(network);

    if(result == 0)
    {
        communication_PendingWork |= COMMUNICATION_WORK_CONNECTION;
        result = communication_waitForCondition(COMMUNICATION_WAIT_CONNECTION, K_SECONDS(COMMUNICATION_CONNECT_TIMEOUT_S));

        int cleanup = 0;

        if(result != 0)
        {
            cleanup = wifi_disconnect();
        }

        if(cleanup == 0)
        {
            communication_PendingWork &= ~COMMUNICATION_WORK_CONNECTION;
        }
        else
        {
            result = cleanup;
        }
    }

    return result;
}

static int communication_tryScan(const struct wifi_network *network)
{
    ARG_UNUSED(network);

    int result = wifi_startScan();

    if(result == 0)
    {
        communication_PendingWork |= COMMUNICATION_WORK_SCAN;
        result = communication_waitForCondition(COMMUNICATION_WAIT_SCAN_LIST, K_SECONDS(COMMUNICATION_SCAN_TIMEOUT_S));

        int cleanup = 0;

        /* Only an interrupted or timed-out scan can still run in the driver. */
        if((result == -ECANCELED) || (result == -ETIMEDOUT)) /**< Operation was cancelled; Operation exceeded its wait deadline. */
        {
            cleanup = wifi_cancelScan();
        }

        if(cleanup == 0)
        {
            communication_PendingWork &= ~COMMUNICATION_WORK_SCAN;
        }
        else
        {
            result = cleanup;
        }
    }

    return result;
}

static int communication_connectToNetwork(const struct wifi_network *network, int attempts)
{
    int result = communication_retry(communication_tryConnect, network, attempts, COMMUNICATION_WORK_CONNECTION, "Connect");

    if(result == 0)
    {
        char address[WIFI_ADDRESS_SIZE];

        communication_RecoveryIsAllowed = true;

        if(wifi_getAddress(address, sizeof(address)) == 0)
        {
            LOG_INF("Wi-Fi address %s", address);
        }
    }

    return result;
}

static int communication_scanNetworks(void)
{
    int result = communication_retry(communication_tryScan, NULL, COMMUNICATION_SCAN_ATTEMPTS, COMMUNICATION_WORK_SCAN, "Scan");

    if(result == 0)
    {
        portal_setNetworks(communication_ScanList, communication_ScanCount);
    }

    return result;
}

static void communication_runSetup(void)
{
    communication_BootJoinIsPending = false;
    communication_setState(COMMUNICATION_STATE_SETUP);
    LOG_INF("Wi-Fi setup: scanning");

    /* Scan before the hotspot opens, so the list is ready when the phone joins. */
    int result = communication_scanNetworks();

    if((result != 0) && (result != -ECANCELED)) /**< Start interrupted the network workflow. */
    {
        LOG_ERR("SCAN_FAILURE (%d); hold the button 2 s to retry", result);
    }

    if(result == 0)
    {
        result = communication_openSetup();
    }

    if(result == 0)
    {
        int error = 0;
        enum communication_setup_result outcome = communication_servePage(&error);

        communication_closeSetup(outcome, error);
    }
    else
    {
        portal_setStatus(PORTAL_STATUS_CLOSING, result);
    }

    /* Also stops services that started before a failure. */
    (void)communication_stopWiFiWork();

    communication_setState(COMMUNICATION_STATE_RUNNING);
}

static int communication_startService(uint32_t workBit, int (*start)(void))
{
    int result = -ECANCELED; /**< Start interrupted the network workflow. */

    (void)communication_waitForCondition(COMMUNICATION_WAIT_CONTROL_EVENT, K_NO_WAIT);

    if(!communication_ListeningIsActive)
    {
        /* Set before the start, so a partly started service is stopped too. */
        communication_PendingWork |= workBit;
        result = start();
    }

    return result;
}

static int communication_openSetup(void)
{
    portal_setStatus(PORTAL_STATUS_SELECTING, 0);

    int result = communication_startService(COMMUNICATION_WORK_HOTSPOT, wifi_startHotspot);

    if(result == 0)
    {
        result = communication_startService(COMMUNICATION_WORK_DHCP, wifi_startDHCPServer);
    }

    if(result == 0)
    {
        result = communication_startService(COMMUNICATION_WORK_PORTAL, portal_start);
    }

    if(result == 0)
    {
        LOG_INF("Wi-Fi setup open: join the hotspot and open http://%s", WIFI_HOTSPOT_ADDRESS);
    }
    else if(result != -ECANCELED) /**< Start interrupted the network workflow. */
    {
        LOG_ERR("HOTSPOT_START_FAILURE (%d); hold the button 2 s to retry", result);
    }
    else
    {
        /* Listening started. */
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
        (void)communication_waitForCondition(COMMUNICATION_WAIT_CONTROL_EVENT, K_NO_WAIT);

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

            /* Restart the timer after the request is done, so it does not run during a join or scan. */
            idleDeadline = sys_timepoint_calc(K_SECONDS(COMMUNICATION_SETUP_INACTIVITY_TIMEOUT_S));
        }
        else
        {
            /* No request in this interval. */
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
        /* Only restarts the inactivity timer. */
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

        if((result != 0) && (result != -ECANCELED)) /**< Start interrupted the network workflow. */
        {
            /* Update the list; the page keeps showing the cause of the failed join. */
            result = communication_scanNetworks();
        }

        break;

    default:
        break;
    }

    if(result == -ECANCELED) /**< Start interrupted the network workflow. */
    {
        outcome = COMMUNICATION_SETUP_INTERRUPTED;
    }

    if((result != 0) && (result != -ECANCELED)) /**< Start interrupted the network workflow. */
    {
        /* Only a failed scan gets here; setup cannot continue without a list. */
        *error = result;
        outcome = COMMUNICATION_SETUP_FAILED;
    }

    return outcome;
}

static int communication_handleConnectRequest(void)
{
    struct wifi_network *network = &communication_PageRequest.network;

    if(!wifi_isValidNetwork(network))
    {
        portal_setStatus(PORTAL_STATUS_CONNECT_FAILED, -EINVAL); /**< Invalid argument or unsupported input. */
        (void)memset(network->password, 0, sizeof(network->password));
        return -EINVAL; /**< Invalid argument or unsupported input. */
    }

    LOG_INF("Wi-Fi setup: joining \"%s\"", network->name);
    portal_setStatus(PORTAL_STATUS_CONNECTING, 0);

    /* The hotspot stays open, so the phone can follow the status during the join. */
    int result = communication_connectToNetwork(network, COMMUNICATION_PAGE_CONNECT_ATTEMPTS);

    if(result == 0)
    {
        communication_saveNetwork(network);
    }
    else
    {
        communication_discardPageRequests();

        if(result != -ECANCELED) /**< Start interrupted the network workflow. */
        {
            LOG_WRN("Wi-Fi setup: join failed (%d)", result);
            portal_setStatus(PORTAL_STATUS_CONNECT_FAILED, result);
        }
    }

    (void)memset(network->password, 0, sizeof(network->password));

    if(result == 0)
    {
        /* Let the page show the result. Requests stay unread meanwhile. */
        (void)communication_waitForCondition(COMMUNICATION_WAIT_DELAY, K_SECONDS(COMMUNICATION_RESULT_DISPLAY_S));
    }

    return result;
}

static void communication_saveNetwork(const struct wifi_network *network)
{
    int result = 0;
    int attempt = 0;
    char address[WIFI_ADDRESS_SIZE];

    /* A flash write is short, so it finishes even if listening starts. */
    do
    {
        attempt++;
        result = storage_write(COMMUNICATION_NETWORK_RECORD, network, sizeof(*network));

        if(result != 0)
        {
            LOG_WRN("Save attempt %d/%d failed (%d)", attempt, COMMUNICATION_SAVE_ATTEMPTS, result);
        }
    } while((result != 0) && (attempt < COMMUNICATION_SAVE_ATTEMPTS));

    /* The user needs the address to find the device on the clinic network. */
    (void)wifi_getAddress(address, sizeof(address));
    portal_setAddress(address);

    if(result == 0)
    {
        LOG_INF("Wi-Fi setup: joined and saved");
        portal_setStatus(PORTAL_STATUS_CONNECTED, 0);
    }
    else
    {
        /* The connection stays; flash keeps the previous record. */
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

    portal_setStatus(PORTAL_STATUS_CLOSING, error);

    /* Joined results have already been displayed; Start must not add a notice delay. */
    if((outcome == COMMUNICATION_SETUP_CANCELLED) || (outcome == COMMUNICATION_SETUP_FAILED))
    {
        (void)communication_waitForCondition(COMMUNICATION_WAIT_DELAY, K_SECONDS(COMMUNICATION_CLOSE_NOTICE_DISPLAY_S));
    }

    (void)communication_stopWiFiWork();

    LOG_INF("Wi-Fi setup closed (%d)", outcome);
}

/** @} */
