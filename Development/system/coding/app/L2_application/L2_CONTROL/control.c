/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L2_CONTROL
 * @{
 * @file
 * Implementation of the CONTROL module.
 */

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include "control.h"

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/clock.h>

#include "communication.h"
#include "feedback.h"
#include "physicalinterface.h"

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

#define CONTROL_LAMP_TEST_MINIMUM_MILLISECONDS 1000 /**< P22: startup lamp test at least 1 s. */
#define CONTROL_QUICK_FLASHES_MILLISECONDS     1500 /**< P22: three quick flashes at 2 Hz. */

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

static k_timepoint_t control_lampTestEnd;
static struct k_spinlock control_indicationLock;
static bool control_isIdle;                                       /**< Startup has ended. */
static enum feedback_code control_wifiIndication = FEEDBACK_NONE; /**< Wi-Fi status shown in Idle; NONE shows IDLE. */
static struct k_work_delayable control_quickFlashesEndWork;

/***********************************************************************/
/* LOCAL FUNCTION PROTOTYPES                                           */
/***********************************************************************/

/**
 * @brief Act on a debounced Start/Stop button event.
 *
 * @param[in] event Button event from PHYSICALINTERFACE.
 */
static void control_handleButton(enum physicalinterface_button_event event);

/**
 * @brief Show a Wi-Fi workflow status from COMMUNICATION while Idle.
 *
 * @param[in] code Catalogue code from COMMUNICATION.
 */
static void control_handleWiFiFeedback(enum feedback_code code);

/**
 * @brief Show the Idle indication again after the quick flashes.
 *
 * @param[in] work Quick-flashes end work item.
 */
static void control_endQuickFlashes(struct k_work *work);

/**
 * @brief Show the current Wi-Fi status, or IDLE if there is none.
 */
static void control_showIdleIndication(void);

LOG_MODULE_REGISTER(control, LOG_LEVEL_INF);

/***********************************************************************/
/* GLOBAL FUNCTIONS                                                    */
/***********************************************************************/

void control_init(void)
{
    control_lampTestEnd = sys_timepoint_calc(K_MSEC(CONTROL_LAMP_TEST_MINIMUM_MILLISECONDS));
    k_work_init_delayable(&control_quickFlashesEndWork, control_endQuickFlashes);

    if(physicalinterface_init(control_handleButton) != 0)
    {
        LOG_WRN("Continuing with incomplete physical interface");
    }

    physicalinterface_showStatusLight(FEEDBACK_STARTUP_RUNNING);
    communication_setFeedbackHandler(control_handleWiFiFeedback);
}

void control_completeStartup(void)
{
    (void)k_sleep(sys_timepoint_timeout(control_lampTestEnd));

    k_spinlock_key_t key = k_spin_lock(&control_indicationLock);
    control_isIdle = true;
    k_spin_unlock(&control_indicationLock, key);

    control_showIdleIndication();
}

/***********************************************************************/
/* LOCAL FUNCTIONS                                                     */
/***********************************************************************/

static void control_handleButton(enum physicalinterface_button_event event)
{
    switch(event)
    {
    case PHYSICALINTERFACE_BUTTON_LONG_PRESS:
    {
        k_spinlock_key_t key = k_spin_lock(&control_indicationLock);
        bool isIdle = control_isIdle;
        k_spin_unlock(&control_indicationLock, key);

        if(!isIdle)
        {
            LOG_INF("Button hold outside Idle ignored");
            break;
        }

        LOG_INF("Button hold in Idle: requesting Wi-Fi setup");

        if(communication_postEvent(COMMUNICATION_EVENT_SETUP_REQUESTED) != 0)
        {
            LOG_WRN("Wi-Fi setup request was not accepted");
        }
        break;
    }

    default:
        break;
    }
}

static void control_handleWiFiFeedback(enum feedback_code code)
{
    bool isQuickFlash = (code == FEEDBACK_WIFI_CONNECTED);
    enum feedback_code wifiIndication = ((code == FEEDBACK_WIFI_CONNECTING) || (code == FEEDBACK_PORTAL_OPEN)) ? code : FEEDBACK_NONE;

    k_spinlock_key_t key = k_spin_lock(&control_indicationLock);
    control_wifiIndication = wifiIndication;
    bool isIdle = control_isIdle;
    k_spin_unlock(&control_indicationLock, key);

    if(!isIdle)
    {
        return;
    }

    if(isQuickFlash)
    {
        physicalinterface_showStatusLight(FEEDBACK_WIFI_CONNECTED);
        (void)k_work_reschedule(&control_quickFlashesEndWork, K_MSEC(CONTROL_QUICK_FLASHES_MILLISECONDS));
        return;
    }

    (void)k_work_cancel_delayable(&control_quickFlashesEndWork);
    control_showIdleIndication();
}

static void control_endQuickFlashes(struct k_work *work)
{
    ARG_UNUSED(work);

    control_showIdleIndication();
}

static void control_showIdleIndication(void)
{
    k_spinlock_key_t key = k_spin_lock(&control_indicationLock);
    enum feedback_code wifiIndication = control_wifiIndication;
    k_spin_unlock(&control_indicationLock, key);

    physicalinterface_showStatusLight((wifiIndication == FEEDBACK_NONE) ? FEEDBACK_IDLE : wifiIndication);
}

/** @} */
