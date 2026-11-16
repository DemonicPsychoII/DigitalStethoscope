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

#include <stdbool.h>

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/clock.h>

#include "audio.h"
#include "communication.h"
#include "feedback.h"
#include "physicalinterface.h"

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

#define CONTROL_LAMP_TEST_MINIMUM_MILLISECONDS 1000 /**< P22: startup lamp test at least 1 s. */
#define CONTROL_QUICK_FLASHES_MILLISECONDS     1500 /**< P22: three quick flashes at 2 Hz. */
#define CONTROL_WIFI_STOP_WAIT_MILLISECONDS    5000 /**< P23: Wi-Fi cleanup is capped at 5 s. */

#define CONTROL_THREAD_STACK_SIZE  (2048) /**< Proposed; measure under VT-02. */
#define CONTROL_THREAD_PRIORITY    (5)    /**< Below the audio thread, above COMMUNICATION. */
#define CONTROL_EVENT_QUEUE_LENGTH (16)   /**< P11: 16 control events. */

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/** Workflow state; only the control thread changes it after startup. */
enum control_state
{
    CONTROL_STATE_STARTUP,   /**< Until control_completeStartup(). */
    CONTROL_STATE_IDLE,      /**< Audio stopped; Wi-Fi work allowed. */
    CONTROL_STATE_STARTING,  /**< Start sent to AUDIO; waiting for its report. */
    CONTROL_STATE_LISTENING, /**< Microphone to DAC. */
    CONTROL_STATE_STOPPING,  /**< Stop sent to AUDIO; waiting for its report. */
    CONTROL_STATE_HALTED,    /**< Restart-required audio error latched; Start blocked. */
};

/** Input of the control thread. */
enum control_event_type
{
    CONTROL_EVENT_BUTTON_SHORT_PRESS,
    CONTROL_EVENT_BUTTON_LONG_PRESS,
    CONTROL_EVENT_AUDIO_STARTED,
    CONTROL_EVENT_AUDIO_STOPPED,
    CONTROL_EVENT_AUDIO_FAULT,
};

/** One entry of the control event queue. */
struct control_event
{
    enum control_event_type type;
    enum feedback_code fault; /**< Catalogue code for CONTROL_EVENT_AUDIO_FAULT, otherwise FEEDBACK_NONE. */
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

static k_timepoint_t control_lampTestEnd;
static struct k_spinlock control_indicationLock;                  /**< Protects the state and the Wi-Fi indication. */
static enum control_state control_currentState;                   /**< Also read by the Wi-Fi feedback handler on the communication thread. */
static enum feedback_code control_wifiIndication = FEEDBACK_NONE; /**< Wi-Fi status shown in Idle; NONE shows IDLE. */
static enum feedback_code control_audioFault = FEEDBACK_NONE;     /**< First latched audio error. */
static struct k_work_delayable control_quickFlashesEndWork;

K_THREAD_STACK_DEFINE(control_stack, CONTROL_THREAD_STACK_SIZE);
K_MSGQ_DEFINE(control_events, sizeof(struct control_event), CONTROL_EVENT_QUEUE_LENGTH, 4);

static struct k_thread control_threadData;

/***********************************************************************/
/* LOCAL FUNCTION PROTOTYPES                                           */
/***********************************************************************/

/**
 * @brief Queue a debounced Start/Stop button event for the control thread.
 *
 * @param[in] event Button event from PHYSICALINTERFACE.
 * @param[in] timestampMilliseconds Uptime at which PHYSICALINTERFACE recognized the event.
 */
static void control_handleButton(enum physicalinterface_button_event event, int64_t timestampMilliseconds);

/**
 * @brief Log a stable Raw/Murmur/BPM switch reading; selecting the filter is not implemented.
 *
 * @param[in] reading Switch reading from PHYSICALINTERFACE.
 */
static void control_handleListeningFilter(const struct physicalinterface_listening_filter_reading *reading);

/**
 * @brief Log a volume reading; applying the volume is not implemented.
 *
 * @param[in] reading Volume reading from PHYSICALINTERFACE.
 */
static void control_handleVolume(const struct physicalinterface_volume_reading *reading);

/**
 * @brief Queue a report of the audio thread for the control thread.
 *
 * @param[in] event Report from AUDIO.
 * @param[in] fault Catalogue code of the failed link for AUDIO_EVENT_FAULT.
 */
static void control_handleAudioEvent(enum audio_event event, enum feedback_code fault);

/**
 * @brief Queue an event without waiting; a full queue rejects it.
 *
 * @param[in] event Event to queue.
 */
static void control_postEvent(const struct control_event *event);

/**
 * @brief Take events from the queue and dispatch them in arrival order.
 *
 * @param[in] first Unused.
 * @param[in] second Unused.
 * @param[in] third Unused.
 */
static void control_thread(void *first, void *second, void *third);

/**
 * @brief Act on one event in the current state.
 *
 * After an audio error the device is halted: button events are dropped without an indication.
 *
 * @param[in] event Event from the queue.
 */
static void control_dispatch(const struct control_event *event);

/**
 * @brief Start in Idle, Stop while listening; otherwise reject.
 *
 * @param[in] state Current state.
 */
static void control_handleShortPress(enum control_state state);

/**
 * @brief Request Wi-Fi setup in Idle; otherwise reject.
 *
 * @param[in] state Current state.
 */
static void control_handleLongPress(enum control_state state);

/**
 * @brief Stop the Wi-Fi work, then send Start to AUDIO.
 *
 * Blocks the control thread until Wi-Fi work has stopped, at most the P23 cleanup cap.
 */
static void control_startListening(void);

/**
 * @brief Return to Idle, allow Wi-Fi work again and show the Idle indication.
 */
static void control_returnToIdle(void);

/**
 * @brief Read the workflow state.
 *
 * @return Current state.
 */
static enum control_state control_getState(void);

/**
 * @brief Change the workflow state.
 *
 * @param[in] state New state.
 */
static void control_setState(enum control_state state);

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

/***********************************************************************/
/* MACROS                                                              */
/***********************************************************************/

LOG_MODULE_REGISTER(control, LOG_LEVEL_INF);

/***********************************************************************/
/* GLOBAL FUNCTIONS                                                    */
/***********************************************************************/

void control_init(void)
{
    control_lampTestEnd = sys_timepoint_calc(K_MSEC(CONTROL_LAMP_TEST_MINIMUM_MILLISECONDS));
    k_work_init_delayable(&control_quickFlashesEndWork, control_endQuickFlashes);

    const struct physicalinterface_input_handlers inputHandlers = {
        .button = control_handleButton,
        .listeningFilter = control_handleListeningFilter,
        .volume = control_handleVolume,
    };

    if(physicalinterface_init(&inputHandlers) != 0)
    {
        LOG_WRN("Continuing with incomplete physical interface");
    }

    physicalinterface_showStatusLight(FEEDBACK_STARTUP_RUNNING);
    communication_setFeedbackHandler(control_handleWiFiFeedback);

    control_audioFault = audio_init(control_handleAudioEvent);

    (void)k_thread_create(&control_threadData,
                          control_stack,
                          K_THREAD_STACK_SIZEOF(control_stack),
                          control_thread,
                          NULL,
                          NULL,
                          NULL,
                          CONTROL_THREAD_PRIORITY,
                          0,
                          K_FOREVER);

    (void)k_thread_name_set(&control_threadData, "control");
    k_thread_start(&control_threadData);
}

void control_completeStartup(void)
{
    (void)k_sleep(sys_timepoint_timeout(control_lampTestEnd));

    if(control_audioFault == FEEDBACK_NONE)
    {
        control_setState(CONTROL_STATE_IDLE);
        control_showIdleIndication();
    }
    else
    {
        LOG_ERR("Audio initialization failed; Start is blocked until restart");
        control_setState(CONTROL_STATE_HALTED);
        physicalinterface_showStatusLight(control_audioFault);
    }
}

/***********************************************************************/
/* LOCAL FUNCTIONS                                                     */
/***********************************************************************/

static void control_handleButton(enum physicalinterface_button_event event, int64_t timestampMilliseconds)
{
    ARG_UNUSED(timestampMilliseconds);

    struct control_event controlEvent = {
        .type = (event == PHYSICALINTERFACE_BUTTON_LONG_PRESS) ? CONTROL_EVENT_BUTTON_LONG_PRESS : CONTROL_EVENT_BUTTON_SHORT_PRESS,
        .fault = FEEDBACK_NONE,
    };

    control_postEvent(&controlEvent);
}

static void control_handleAudioEvent(enum audio_event event, enum feedback_code fault)
{
    struct control_event controlEvent = {
        .type = CONTROL_EVENT_AUDIO_FAULT,
        .fault = fault,
    };

    if(event == AUDIO_EVENT_STARTED)
    {
        controlEvent.type = CONTROL_EVENT_AUDIO_STARTED;
    }
    else if(event == AUDIO_EVENT_STOPPED)
    {
        controlEvent.type = CONTROL_EVENT_AUDIO_STOPPED;
    }
    else
    {
        controlEvent.type = CONTROL_EVENT_AUDIO_FAULT;
    }

    control_postEvent(&controlEvent);
}

static void control_postEvent(const struct control_event *event)
{
    if(k_msgq_put(&control_events, event, K_NO_WAIT) != 0)
    {
        LOG_ERR("Control event %d lost: queue full", event->type);
        physicalinterface_showStatusLight(FEEDBACK_INPUT_REJECTED);
    }
}

static void control_thread(void *first, void *second, void *third)
{
    ARG_UNUSED(first);
    ARG_UNUSED(second);
    ARG_UNUSED(third);

    for(;;)
    {
        struct control_event event;

        (void)k_msgq_get(&control_events, &event, K_FOREVER);
        control_dispatch(&event);
    }
}

static void control_dispatch(const struct control_event *event)
{
    enum control_state state = control_getState();

    switch(event->type)
    {
    case CONTROL_EVENT_BUTTON_SHORT_PRESS:
        if(state != CONTROL_STATE_HALTED)
        {
            control_handleShortPress(state);
        }

        break;

    case CONTROL_EVENT_BUTTON_LONG_PRESS:
        if(state != CONTROL_STATE_HALTED)
        {
            control_handleLongPress(state);
        }

        break;

    case CONTROL_EVENT_AUDIO_STARTED:
        if(state == CONTROL_STATE_STARTING)
        {
            LOG_INF("Listening");
            control_setState(CONTROL_STATE_LISTENING);
            physicalinterface_showStatusLight(FEEDBACK_LISTENING);
        }

        break;

    case CONTROL_EVENT_AUDIO_STOPPED:
        if(state == CONTROL_STATE_STOPPING)
        {
            LOG_INF("Listening stopped");
            control_returnToIdle();
        }

        break;

    case CONTROL_EVENT_AUDIO_FAULT:
        /* The first latched error stays shown; Wi-Fi work stays stopped until the restart. */
        if(state != CONTROL_STATE_HALTED)
        {
            LOG_ERR("Audio fault, catalogue code %d; restart required", event->fault);
            control_audioFault = event->fault;
            control_setState(CONTROL_STATE_HALTED);
            physicalinterface_showStatusLight(event->fault);
        }

        break;

    default:
        break;
    }
}

static void control_handleShortPress(enum control_state state)
{
    switch(state)
    {
    case CONTROL_STATE_IDLE:
        control_startListening();
        break;

    case CONTROL_STATE_LISTENING:
        if(audio_postCommand(AUDIO_COMMAND_STOP) == 0)
        {
            control_setState(CONTROL_STATE_STOPPING);
        }
        else
        {
            LOG_ERR("AUDIO did not accept Stop");
        }

        break;

    default:
        LOG_INF("Button press in state %d rejected", state);
        physicalinterface_showStatusLight(FEEDBACK_INPUT_REJECTED);
        break;
    }
}

static void control_handleLongPress(enum control_state state)
{
    if(state != CONTROL_STATE_IDLE)
    {
        LOG_INF("Button hold outside Idle rejected");
        physicalinterface_showStatusLight(FEEDBACK_INPUT_REJECTED);
    }
    else
    {
        LOG_INF("Button hold in Idle: requesting Wi-Fi setup");

        if(communication_postEvent(COMMUNICATION_EVENT_SETUP_REQUESTED) != 0)
        {
            LOG_WRN("Wi-Fi setup request was not accepted");
        }
    }
}

static void control_startListening(void)
{
    control_setState(CONTROL_STATE_STARTING);
    (void)k_work_cancel_delayable(&control_quickFlashesEndWork);
    (void)communication_postEvent(COMMUNICATION_EVENT_LISTENING_STARTED);

    if(communication_waitForWiFiStop(K_MSEC(CONTROL_WIFI_STOP_WAIT_MILLISECONDS)) != 0)
    {
        LOG_WRN("Wi-Fi work did not stop in time; audio stays stopped");
        control_returnToIdle();
        physicalinterface_showStatusLight(FEEDBACK_INPUT_REJECTED);
    }
    else if(audio_postCommand(AUDIO_COMMAND_START) != 0)
    {
        LOG_ERR("AUDIO did not accept Start");
        control_returnToIdle();
        physicalinterface_showStatusLight(FEEDBACK_INPUT_REJECTED);
    }
    else
    {
        LOG_INF("Start sent to AUDIO");
    }
}

static void control_returnToIdle(void)
{
    control_setState(CONTROL_STATE_IDLE);
    (void)communication_postEvent(COMMUNICATION_EVENT_LISTENING_STOPPED);
    control_showIdleIndication();
}

static enum control_state control_getState(void)
{
    k_spinlock_key_t key = k_spin_lock(&control_indicationLock);
    enum control_state state = control_currentState;
    k_spin_unlock(&control_indicationLock, key);

    return state;
}

static void control_setState(enum control_state state)
{
    k_spinlock_key_t key = k_spin_lock(&control_indicationLock);
    control_currentState = state;
    k_spin_unlock(&control_indicationLock, key);
}

static void control_handleListeningFilter(const struct physicalinterface_listening_filter_reading *reading)
{
    static const char *const filterNames[] = {
        [PHYSICALINTERFACE_LISTENING_FILTER_RAW] = "Raw",
        [PHYSICALINTERFACE_LISTENING_FILTER_MURMUR] = "Murmur",
        [PHYSICALINTERFACE_LISTENING_FILTER_BPM] = "BPM",
    };

    if(reading->status == PHYSICALINTERFACE_INPUT_VALID)
    {
        LOG_INF("Listening filter switch: %s", filterNames[reading->filter]);
    }
    else
    {
        LOG_WRN("Listening filter switch has no valid position");
    }
}

static void control_handleVolume(const struct physicalinterface_volume_reading *reading)
{
    if(reading->status == PHYSICALINTERFACE_INPUT_VALID)
    {
        LOG_DBG("Volume: %u %%", reading->percent);
    }
    else if(reading->status == PHYSICALINTERFACE_INPUT_ABSENT)
    {
        LOG_INF("Volume potentiometer absent");
    }
    else
    {
        LOG_WRN("Volume potentiometer reading failed");
    }
}

static void control_handleWiFiFeedback(enum feedback_code code)
{
    if(code == FEEDBACK_WIFI_CLEANUP_FAILURE)
    {
        LOG_ERR("WIFI_CLEANUP_FAILURE reported; Wi-Fi disabled until restart");
    }

    bool isQuickFlash = (code == FEEDBACK_WIFI_CONNECTED);
    enum feedback_code wifiIndication = ((code == FEEDBACK_WIFI_CONNECTING) || (code == FEEDBACK_PORTAL_OPEN)) ? code : FEEDBACK_NONE;

    k_spinlock_key_t key = k_spin_lock(&control_indicationLock);
    control_wifiIndication = wifiIndication;
    bool isIdle = (control_currentState == CONTROL_STATE_IDLE);
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

    if(control_getState() == CONTROL_STATE_IDLE)
    {
        control_showIdleIndication();
    }
}

static void control_showIdleIndication(void)
{
    k_spinlock_key_t key = k_spin_lock(&control_indicationLock);
    enum feedback_code wifiIndication = control_wifiIndication;
    k_spin_unlock(&control_indicationLock, key);

    physicalinterface_showStatusLight((wifiIndication == FEEDBACK_NONE) ? FEEDBACK_IDLE : wifiIndication);
}

/** @} */
