/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L2_CONTROL
 * @{
 * @file
 * Implementation of the L2_CONTROL module.
 */

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include "control.h"
#include "control_error_policy.h"

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

#define CONTROL_LAMP_TEST_MINIMUM_MILLISECONDS     1000 /**< P22: startup lamp test at least 1 s. */
#define CONTROL_QUICK_FLASHES_MILLISECONDS         1500 /**< P22: three quick flashes at 2 Hz. */
#define CONTROL_ACKNOWLEDGEMENT_FLASH_MILLISECONDS 1000 /**< P22: long flash of 1 s after an acknowledgement. */
#define CONTROL_WIFI_STOP_WAIT_MILLISECONDS        5000 /**< P23: Wi-Fi cleanup is capped at 5 s. */

/** The control thread checks the input readings at least this often; within the P10 status budget of 500 ms. */
#define CONTROL_INPUT_CHECK_MILLISECONDS 100

/** No valid switch position for this long while listening is CONTROL_INPUT_FAILURE. */
#define CONTROL_SWITCH_FAILURE_MILLISECONDS 1000

/** Wait before the startup completion is posted again, if the queue had no free slot. */
#define CONTROL_STARTUP_RETRY_MILLISECONDS 10

#define CONTROL_THREAD_STACK_SIZE  (2048) /**< Stack size of the control thread. */
#define CONTROL_THREAD_PRIORITY    (5)    /**< Preemptive priority of the control thread. */
#define CONTROL_EVENT_QUEUE_LENGTH (16)   /**< P11: 16 control events. */

/** Queue slots that input events leave free: one stream reports started and then stopped or a fault, and a lost report would leave the state wrong. */
#define CONTROL_AUDIO_EVENT_RESERVE (2U)

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/** Workflow state; only the control thread changes it. */
enum control_state
{
    CONTROL_STATE_STARTUP,   /**< Until the lamp test has ended. */
    CONTROL_STATE_IDLE,      /**< Audio stopped; Wi-Fi work allowed. */
    CONTROL_STATE_STARTING,  /**< Start sent to L2_AUDIO; waiting for its report. */
    CONTROL_STATE_LISTENING, /**< Microphone to DAC. */
    CONTROL_STATE_STOPPING,  /**< Stop sent to L2_AUDIO; waiting for its report. */
    CONTROL_STATE_HALTED,    /**< Restart-required error in effect; every input is dropped. */
};

/** Input of the control thread. */
enum control_event_type
{
    CONTROL_EVENT_BUTTON_SHORT_PRESS,
    CONTROL_EVENT_BUTTON_LONG_PRESS,
    CONTROL_EVENT_AUDIO_STARTED,
    CONTROL_EVENT_AUDIO_STOPPED,
    CONTROL_EVENT_AUDIO_FAULT,
    CONTROL_EVENT_WIFI_FEEDBACK,
    CONTROL_EVENT_STARTUP_COMPLETED,
};

/** One entry of the control event queue. */
struct control_event
{
    enum control_event_type type;
    enum feedback_code code; /**< Catalogue code for CONTROL_EVENT_AUDIO_FAULT and CONTROL_EVENT_WIFI_FEEDBACK, otherwise FEEDBACK_NONE. */
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
static enum feedback_code control_initialAudioFault = FEEDBACK_NONE; /**< Set before the control thread starts; afterwards only read by it. */

/* Only the control thread uses these after control_init(). */
static enum control_state control_currentState;
static struct control_error_latch control_errorLatch;
static enum feedback_code control_wifiIndication = FEEDBACK_NONE; /**< Wi-Fi status shown in Idle; NONE shows IDLE. */
static bool control_isQuickFlashActive;                           /**< WIFI_CONNECTED is shown in Idle until control_quickFlashesEnd. */
static k_timepoint_t control_quickFlashesEnd;
static k_timepoint_t control_acknowledgementFlashEnd;            /**< Until then the next error is not shown yet, so a press must not acknowledge it. */
static enum feedback_code control_shownFeedback = FEEDBACK_NONE; /**< Last row passed to L1_PHYSICALINTERFACE, overlays excluded. */

static struct k_spinlock control_inputLock; /**< Protects the readings that the input handlers store on the system work queue. */
static struct physicalinterface_listening_filter_reading control_switchReading = {
    .filter = PHYSICALINTERFACE_SAFE_LISTENING_FILTER,
    .status = PHYSICALINTERFACE_INPUT_FAILED,
    .timestampMilliseconds = 0,
};
static bool control_isVolumeFailed;

K_MUTEX_DEFINE(control_inputEventLock); /**< Makes the free-slot check and the put of an input event one step. */

K_THREAD_STACK_DEFINE(control_stack, CONTROL_THREAD_STACK_SIZE);
K_MSGQ_DEFINE(control_events, sizeof(struct control_event), CONTROL_EVENT_QUEUE_LENGTH, 4);

static struct k_thread control_threadData;

/***********************************************************************/
/* LOCAL FUNCTION PROTOTYPES                                           */
/***********************************************************************/

/**
 * @brief Queue a debounced Start/Stop button event for the control thread.
 *
 * @param[in] event Button event from L1_PHYSICALINTERFACE.
 * @param[in] timestampMilliseconds Uptime at which L1_PHYSICALINTERFACE recognized the event.
 */
static void control_handleButton(enum physicalinterface_button_event event, int64_t timestampMilliseconds);

/**
 * @brief Keep the last stable Raw/Murmur/BPM switch reading for the control thread.
 *
 * All three positions pass audio through unfiltered; the position selects no filter.
 *
 * @param[in] reading Switch reading from L1_PHYSICALINTERFACE.
 */
static void control_handleListeningFilter(const struct physicalinterface_listening_filter_reading *reading);

/**
 * @brief Pass the volume to L2_AUDIO and keep a potentiometer failure for the control thread.
 *
 * @param[in] reading Volume reading from L1_PHYSICALINTERFACE.
 */
static void control_handleVolume(const struct physicalinterface_volume_reading *reading);

/**
 * @brief Queue a report of the audio thread for the control thread.
 *
 * @param[in] event Report from L2_AUDIO.
 * @param[in] fault Catalogue code of the failed link for AUDIO_EVENT_FAULT.
 */
static void control_handleAudioEvent(enum audio_event event, enum feedback_code fault);

/**
 * @brief Queue Wi-Fi workflow feedback of the communication thread for the control thread.
 *
 * @param[in] code Catalogue code from L2_COMMUNICATION.
 */
static void control_handleWiFiFeedback(enum feedback_code code);

/**
 * @brief Queue an input event without waiting, leaving CONTROL_AUDIO_EVENT_RESERVE slots free.
 *
 * @param[in] event Event to queue.
 *
 * @return True if the event was queued.
 */
static bool control_postInputEvent(const struct control_event *event);

/**
 * @brief Queue a report of L2_AUDIO without waiting; it may use the reserved slots.
 *
 * @param[in] event Event to queue.
 */
static void control_postEvent(const struct control_event *event);

/**
 * @brief Take events from the queue and dispatch them in arrival order; check the inputs and timers in between.
 *
 * @param[in] first Unused.
 * @param[in] second Unused.
 * @param[in] third Unused.
 */
static void control_thread(void *first, void *second, void *third);

/**
 * @brief Act on one event in the current state.
 *
 * @param[in] event Event from the queue.
 */
static void control_dispatch(const struct control_event *event);

/**
 * @brief Acknowledge the error shown, reject the press, drop it while halted, or pass it to the workflow.
 */
static void control_handleShortPress(void);

/**
 * @brief Start in Idle, Stop while listening; otherwise reject.
 */
static void control_handleWorkflowShortPress(void);

/**
 * @brief Request Wi-Fi setup in Idle; drop the hold while halted; otherwise reject.
 */
static void control_handleLongPress(void);

/**
 * @brief Check the switch, stop the Wi-Fi work, then send Start to L2_AUDIO.
 *
 * Without a valid switch position CONTROL_INPUT_FAILURE is latched and audio stays stopped.
 * Blocks the control thread until Wi-Fi work has stopped, at most the P23 cleanup cap.
 */
static void control_startListening(void);

/**
 * @brief Allow Wi-Fi work again after listening, then enter Idle.
 */
static void control_returnToIdle(void);

/**
 * @brief Enter Idle, or Halted if a latched error halts the device, and show the indication.
 */
static void control_enterIdle(void);

/**
 * @brief End the startup: latch a failed audio initialization and enter Idle.
 */
static void control_finishStartup(void);

/**
 * @brief Latch an error and apply its effect, unless it is already latched.
 *
 * @param[in] code Catalogue error.
 * @param[in] cause Short description for the serial log.
 */
static void control_raiseError(enum feedback_code code, const char *cause);

/**
 * @brief Halt the device if the latched errors require it now, then show the indication.
 */
static void control_applyErrorEffects(void);

/**
 * @brief List every latched error and the error shown on the serial log.
 */
static void control_logLatchedErrors(void);

/**
 * @brief Act on Wi-Fi workflow feedback: latch an error or keep the Wi-Fi status for Idle.
 *
 * @param[in] code Catalogue code from L2_COMMUNICATION.
 */
static void control_applyWiFiFeedback(enum feedback_code code);

/**
 * @brief Latch CONTROL_INPUT_FAILURE for a failed potentiometer or for a switch without a valid position while listening.
 */
static void control_checkInputs(void);

/**
 * @brief Show the Idle indication again once the quick flashes have ended.
 */
static void control_checkQuickFlashes(void);

/**
 * @brief Read the last stable switch reading.
 *
 * @return Copy of the reading.
 */
static struct physicalinterface_listening_filter_reading control_getSwitchReading(void);

/**
 * @brief Tell whether error indications wait: during startup and while audio is started.
 *
 * @return True in Startup, Starting, Listening and Stopping.
 */
static bool control_isIndicationDeferred(void);

/**
 * @brief Status of the current state.
 *
 * @return Catalogue status to show when no error is shown.
 */
static enum feedback_code control_getStatusFeedback(void);

/**
 * @brief Show the code that the latch and the state select, if it changed.
 */
static void control_updateIndication(void);

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
    control_resetErrorLatch(&control_errorLatch);

    const struct physicalinterface_input_handlers inputHandlers = {
        .button = control_handleButton,
        .listeningFilter = control_handleListeningFilter,
        .volume = control_handleVolume,
    };
    const int initializationResult = physicalinterface_init(&inputHandlers);

    if(initializationResult != 0)
    {
        LOG_WRN("Continuing with incomplete physical interface");
    }

    control_updateIndication();
    communication_setFeedbackHandler(control_handleWiFiFeedback);

    control_initialAudioFault = audio_init(control_handleAudioEvent);

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
    const struct control_event event = {
        .type = CONTROL_EVENT_STARTUP_COMPLETED,
        .code = FEEDBACK_NONE,
    };

    (void)k_sleep(sys_timepoint_timeout(control_lampTestEnd));

    bool isPosted = control_postInputEvent(&event);

    while(!isPosted)
    {
        (void)k_sleep(K_MSEC(CONTROL_STARTUP_RETRY_MILLISECONDS));

        isPosted = control_postInputEvent(&event);
    }
}

/***********************************************************************/
/* LOCAL FUNCTIONS                                                     */
/***********************************************************************/

static void control_handleButton(enum physicalinterface_button_event event, int64_t timestampMilliseconds)
{
    ARG_UNUSED(timestampMilliseconds);

    struct control_event controlEvent = {
        .type = ((event == PHYSICALINTERFACE_BUTTON_LONG_PRESS) ? CONTROL_EVENT_BUTTON_LONG_PRESS : CONTROL_EVENT_BUTTON_SHORT_PRESS),
        .code = FEEDBACK_NONE,
    };
    const bool isPosted = control_postInputEvent(&controlEvent);

    if(!isPosted)
    {
        LOG_WRN("Button event rejected: control queue full");
        physicalinterface_showFeedback(FEEDBACK_INPUT_REJECTED);
    }
}

static void control_handleListeningFilter(const struct physicalinterface_listening_filter_reading *reading)
{
    static const char *const filterNames[] = {
        [PHYSICALINTERFACE_LISTENING_FILTER_RAW] = "Raw",
        [PHYSICALINTERFACE_LISTENING_FILTER_MURMUR] = "Murmur",
        [PHYSICALINTERFACE_LISTENING_FILTER_BPM] = "BPM",
    };

    k_spinlock_key_t key = k_spin_lock(&control_inputLock);
    control_switchReading = *reading;
    k_spin_unlock(&control_inputLock, key);

    if(reading->status == PHYSICALINTERFACE_INPUT_VALID)
    {
        LOG_INF("Listening filter switch: %s; audio passes unfiltered", filterNames[reading->filter]);
    }
    else
    {
        LOG_WRN("Listening filter switch has no valid position");
    }
}

static void control_handleVolume(const struct physicalinterface_volume_reading *reading)
{
    uint8_t volumePercent = ((reading->status == PHYSICALINTERFACE_INPUT_VALID) ? reading->percent : PHYSICALINTERFACE_SAFE_VOLUME_PERCENT);

    audio_setVolume(volumePercent);

    k_spinlock_key_t key = k_spin_lock(&control_inputLock);
    control_isVolumeFailed = (control_isVolumeFailed || (reading->status == PHYSICALINTERFACE_INPUT_FAILED));
    k_spin_unlock(&control_inputLock, key);

    if(reading->status == PHYSICALINTERFACE_INPUT_VALID)
    {
        LOG_DBG("Volume: %u %%", volumePercent);
    }
    else if(reading->status == PHYSICALINTERFACE_INPUT_ABSENT)
    {
        LOG_INF("Volume potentiometer absent; volume %u %%", volumePercent);
    }
    else
    {
        LOG_WRN("Volume potentiometer reading failed; volume %u %%", volumePercent);
    }
}

static void control_handleAudioEvent(enum audio_event event, enum feedback_code fault)
{
    struct control_event controlEvent = {
        .type = CONTROL_EVENT_AUDIO_FAULT,
        .code = fault,
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

static void control_handleWiFiFeedback(enum feedback_code code)
{
    struct control_event controlEvent = {
        .type = CONTROL_EVENT_WIFI_FEEDBACK,
        .code = code,
    };
    const bool isPosted = control_postInputEvent(&controlEvent);

    if(!isPosted)
    {
        LOG_ERR("Wi-Fi feedback %d lost: control queue full", code);
    }
}

static bool control_postInputEvent(const struct control_event *event)
{
    bool isPosted = false;

    (void)k_mutex_lock(&control_inputEventLock, K_FOREVER);

    const uint32_t freeSlotCount = k_msgq_num_free_get(&control_events);

    if(freeSlotCount > CONTROL_AUDIO_EVENT_RESERVE)
    {
        isPosted = (k_msgq_put(&control_events, event, K_NO_WAIT) == 0);
    }

    (void)k_mutex_unlock(&control_inputEventLock);

    return isPosted;
}

static void control_postEvent(const struct control_event *event)
{
    const bool isQueued = (k_msgq_put(&control_events, event, K_NO_WAIT) == 0);

    if(!isQueued)
    {
        LOG_ERR("Control event %d lost: queue full", event->type);
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
        const bool isEventReceived = (k_msgq_get(&control_events, &event, K_MSEC(CONTROL_INPUT_CHECK_MILLISECONDS)) == 0);

        if(isEventReceived)
        {
            control_dispatch(&event);
        }

        control_checkInputs();
        control_checkQuickFlashes();
    }
}

static void control_dispatch(const struct control_event *event)
{
    switch(event->type)
    {
    case CONTROL_EVENT_BUTTON_SHORT_PRESS:
        control_handleShortPress();
        break;

    case CONTROL_EVENT_BUTTON_LONG_PRESS:
        control_handleLongPress();
        break;

    case CONTROL_EVENT_AUDIO_STARTED:
        if(control_currentState == CONTROL_STATE_STARTING)
        {
            LOG_INF("Listening");
            control_currentState = CONTROL_STATE_LISTENING;
            control_updateIndication();
        }

        break;

    case CONTROL_EVENT_AUDIO_STOPPED:
        if(control_currentState == CONTROL_STATE_STOPPING)
        {
            LOG_INF("Listening stopped");
            control_returnToIdle();
        }

        break;

    case CONTROL_EVENT_AUDIO_FAULT:
        control_raiseError(event->code, "Audio fault; restart required");
        break;

    case CONTROL_EVENT_WIFI_FEEDBACK:
        control_applyWiFiFeedback(event->code);
        break;

    case CONTROL_EVENT_STARTUP_COMPLETED:
        control_finishStartup();
        break;

    default:
        break;
    }
}

static void control_handleShortPress(void)
{
    enum feedback_code shownError = control_getShownError(&control_errorLatch);
    const enum control_press_action pressAction = control_decideShortPress(&control_errorLatch, control_isIndicationDeferred());
    bool isAcknowledgementFlashEnded = false;

    switch(pressAction)
    {
    case CONTROL_PRESS_ACKNOWLEDGE:
        isAcknowledgementFlashEnded = sys_timepoint_expired(control_acknowledgementFlashEnd);

        if(isAcknowledgementFlashEnded)
        {
            (void)control_acknowledgeShownError(&control_errorLatch);
            LOG_INF("Error %d acknowledged", shownError);
            control_logLatchedErrors();

            physicalinterface_showFeedback(FEEDBACK_ERROR_ACKNOWLEDGED);
            control_shownFeedback = FEEDBACK_ERROR_ACKNOWLEDGED;
            control_acknowledgementFlashEnd = sys_timepoint_calc(K_MSEC(CONTROL_ACKNOWLEDGEMENT_FLASH_MILLISECONDS));
            control_updateIndication();
        }
        else
        {
            LOG_INF("Button press dropped: error %d is not shown yet", shownError);
        }
        break;

    case CONTROL_PRESS_REJECT:
        LOG_INF("Start blocked until the latched errors are acknowledged");
        physicalinterface_showFeedback(FEEDBACK_INPUT_REJECTED);
        break;

    case CONTROL_PRESS_WORKFLOW:
        control_handleWorkflowShortPress();
        break;

    case CONTROL_PRESS_IGNORE:
    default:
        LOG_DBG("Button press dropped: halted until restart");
        break;
    }
}

static void control_handleWorkflowShortPress(void)
{
    bool isStopAccepted = false;

    switch(control_currentState)
    {
    case CONTROL_STATE_IDLE:
        control_startListening();
        break;

    case CONTROL_STATE_LISTENING:
        isStopAccepted = (audio_postCommand(AUDIO_COMMAND_STOP) == 0);

        if(isStopAccepted)
        {
            control_currentState = CONTROL_STATE_STOPPING;
        }
        else
        {
            LOG_ERR("AUDIO did not accept Stop");
        }

        break;

    default:
        LOG_INF("Button press in state %d rejected", control_currentState);
        physicalinterface_showFeedback(FEEDBACK_INPUT_REJECTED);
        break;
    }
}

static void control_handleLongPress(void)
{
    const enum control_press_action pressAction = control_decideLongPress(&control_errorLatch, control_isIndicationDeferred());

    if(pressAction == CONTROL_PRESS_IGNORE)
    {
        LOG_DBG("Button hold dropped: halted until restart");
    }
    else if(control_currentState != CONTROL_STATE_IDLE)
    {
        LOG_INF("Button hold outside Idle rejected");
        physicalinterface_showFeedback(FEEDBACK_INPUT_REJECTED);
    }
    else
    {
        LOG_INF("Button hold in Idle: requesting Wi-Fi setup");

        const bool isSetupRequestAccepted = (communication_postEvent(COMMUNICATION_EVENT_SETUP_REQUESTED) == 0);

        if(!isSetupRequestAccepted)
        {
            LOG_WRN("Wi-Fi setup request was not accepted");
        }
        else
        {
            physicalinterface_showFeedback(FEEDBACK_BUTTON_HOLD_ACKNOWLEDGED);
        }
    }
}

static void control_startListening(void)
{
    struct physicalinterface_listening_filter_reading switchReading = control_getSwitchReading();

    if(switchReading.status != PHYSICALINTERFACE_INPUT_VALID)
    {
        control_raiseError(FEEDBACK_CONTROL_INPUT_FAILURE, "No valid listening filter switch position at Start");
    }
    else
    {
        control_currentState = CONTROL_STATE_STARTING;
        control_isQuickFlashActive = false;
        (void)communication_postEvent(COMMUNICATION_EVENT_LISTENING_STARTED);

        const bool isWiFiStopped = (communication_waitForWiFiStop(K_MSEC(CONTROL_WIFI_STOP_WAIT_MILLISECONDS)) == 0);
        bool isStartAccepted = false;

        if(isWiFiStopped)
        {
            isStartAccepted = (audio_postCommand(AUDIO_COMMAND_START) == 0);
        }

        if(!isWiFiStopped)
        {
            LOG_WRN("Wi-Fi work did not stop in time; audio stays stopped");
            control_returnToIdle();
            physicalinterface_showFeedback(FEEDBACK_INPUT_REJECTED);
        }
        else if(!isStartAccepted)
        {
            LOG_ERR("AUDIO did not accept Start");
            control_returnToIdle();
            physicalinterface_showFeedback(FEEDBACK_INPUT_REJECTED);
        }
        else
        {
            LOG_INF("Start sent to AUDIO");
        }
    }
}

static void control_returnToIdle(void)
{
    (void)communication_postEvent(COMMUNICATION_EVENT_LISTENING_STOPPED);
    control_enterIdle();
}

static void control_enterIdle(void)
{
    const bool isHalted = control_isHalted(&control_errorLatch);

    if(isHalted)
    {
        if(control_currentState != CONTROL_STATE_HALTED)
        {
            LOG_ERR("Halted: every input is blocked until restart");
        }

        control_currentState = CONTROL_STATE_HALTED;
    }
    else
    {
        control_currentState = CONTROL_STATE_IDLE;
    }

    control_updateIndication();
}

static void control_finishStartup(void)
{
    if(control_initialAudioFault != FEEDBACK_NONE)
    {
        control_raiseError(control_initialAudioFault, "Audio initialization failed; restart required");
    }

    control_enterIdle();
}

static void control_raiseError(enum feedback_code code, const char *cause)
{
    const bool isNewlyLatched = control_latchError(&control_errorLatch, code);

    if(isNewlyLatched)
    {
        LOG_ERR("%s: error %d latched", cause, code);

        const bool isIndicationDeferred = control_isIndicationDeferred();

        if(isIndicationDeferred)
        {
            LOG_INF("Unless it is an audio error, it is shown after the startup or after audio has stopped");
        }

        control_logLatchedErrors();
        control_applyErrorEffects();
    }
}

static void control_applyErrorEffects(void)
{
    bool isAudioStarted = ((control_currentState == CONTROL_STATE_STARTING) || (control_currentState == CONTROL_STATE_LISTENING) || (control_currentState == CONTROL_STATE_STOPPING));
    const bool isHaltedAtOnce = control_hasAdmission(&control_errorLatch, CONTROL_ADMISSION_HALTED_AT_ONCE);
    const bool isIndicationDeferred = control_isIndicationDeferred();

    if(isHaltedAtOnce && (control_currentState != CONTROL_STATE_HALTED))
    {
        if(isAudioStarted)
        {
            /* L2_AUDIO stops itself on its own faults; this also mutes it for an audio error that another component detected. */
            (void)audio_postCommand(AUDIO_COMMAND_STOP);
        }

        LOG_ERR("Halted: every input is blocked until restart");
        control_currentState = CONTROL_STATE_HALTED;
    }
    else if(!isIndicationDeferred)
    {
        control_enterIdle();
    }
    else
    {
        /* The error takes effect when audio has stopped. */
    }

    control_updateIndication();
}

static void control_logLatchedErrors(void)
{
    for(uint32_t index = 0U; index < control_errorLatch.errorCount; index++)
    {
        LOG_INF("Latched error %u of %u: %d", index + 1U, control_errorLatch.errorCount, control_errorLatch.errors[index]);
    }

    LOG_INF("Error to show: %d", control_getShownError(&control_errorLatch));
}

static void control_applyWiFiFeedback(enum feedback_code code)
{
    const bool isError = control_isError(code);

    if(isError)
    {
        if(code == FEEDBACK_WIFI_CLEANUP_FAILURE)
        {
            LOG_ERR("WIFI_CLEANUP_FAILURE reported; Wi-Fi disabled until restart");
        }

        control_wifiIndication = FEEDBACK_NONE;
        control_isQuickFlashActive = false;
        control_raiseError(code, "Wi-Fi workflow error");
    }
    else if(code == FEEDBACK_WIFI_CONNECTED)
    {
        control_wifiIndication = FEEDBACK_NONE;
        control_isQuickFlashActive = true;
        control_quickFlashesEnd = sys_timepoint_calc(K_MSEC(CONTROL_QUICK_FLASHES_MILLISECONDS));
        control_updateIndication();
    }
    else
    {
        control_wifiIndication = (((code == FEEDBACK_WIFI_CONNECTING) || (code == FEEDBACK_PORTAL_OPEN)) ? code : FEEDBACK_NONE);
        control_isQuickFlashActive = false;
        control_updateIndication();
    }
}

static void control_checkInputs(void)
{
    k_spinlock_key_t key = k_spin_lock(&control_inputLock);
    struct physicalinterface_listening_filter_reading switchReading = control_switchReading;
    bool isVolumeFailed = control_isVolumeFailed;
    k_spin_unlock(&control_inputLock, key);

    bool isListening = ((control_currentState == CONTROL_STATE_STARTING) || (control_currentState == CONTROL_STATE_LISTENING));
    bool isSwitchFailureLong = ((switchReading.status != PHYSICALINTERFACE_INPUT_VALID) && ((k_uptime_get() - switchReading.timestampMilliseconds) >= CONTROL_SWITCH_FAILURE_MILLISECONDS));

    if(isVolumeFailed)
    {
        control_raiseError(FEEDBACK_CONTROL_INPUT_FAILURE, "Volume potentiometer failed");
    }

    if(isListening && isSwitchFailureLong)
    {
        control_raiseError(FEEDBACK_CONTROL_INPUT_FAILURE, "Listening filter switch without a valid position for 1 s while listening");
    }
}

static void control_checkQuickFlashes(void)
{
    bool isQuickFlashTimeOver = false;

    if(control_isQuickFlashActive)
    {
        isQuickFlashTimeOver = sys_timepoint_expired(control_quickFlashesEnd);
    }

    if(control_isQuickFlashActive && isQuickFlashTimeOver)
    {
        control_isQuickFlashActive = false;
        control_updateIndication();
    }
}

static struct physicalinterface_listening_filter_reading control_getSwitchReading(void)
{
    k_spinlock_key_t key = k_spin_lock(&control_inputLock);
    struct physicalinterface_listening_filter_reading reading = control_switchReading;
    k_spin_unlock(&control_inputLock, key);

    return reading;
}

static bool control_isIndicationDeferred(void)
{
    return ((control_currentState == CONTROL_STATE_STARTUP) || (control_currentState == CONTROL_STATE_STARTING) || (control_currentState == CONTROL_STATE_LISTENING) || (control_currentState == CONTROL_STATE_STOPPING));
}

static enum feedback_code control_getStatusFeedback(void)
{
    enum feedback_code status = FEEDBACK_IDLE;

    switch(control_currentState)
    {
    case CONTROL_STATE_STARTUP:
        status = FEEDBACK_STARTUP_RUNNING;
        break;

    case CONTROL_STATE_LISTENING:
    case CONTROL_STATE_STOPPING:
        status = FEEDBACK_LISTENING;
        break;

    case CONTROL_STATE_IDLE:
    case CONTROL_STATE_STARTING:
    case CONTROL_STATE_HALTED:
    default:
        if(control_isQuickFlashActive)
        {
            status = FEEDBACK_WIFI_CONNECTED;
        }
        else if(control_wifiIndication != FEEDBACK_NONE)
        {
            status = control_wifiIndication;
        }
        else
        {
            status = FEEDBACK_IDLE;
        }

        break;
    }

    return status;
}

static void control_updateIndication(void)
{
    enum feedback_code feedback = control_selectFeedback(&control_errorLatch, control_isIndicationDeferred(), control_getStatusFeedback());

    if(feedback != control_shownFeedback)
    {
        physicalinterface_showFeedback(feedback);
        control_shownFeedback = feedback;
    }
}

/** @} */
