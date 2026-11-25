/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L2_CONTROL
 * @{
 * @file
 * Implementation of the error policy of the L2_CONTROL module.
 */

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include "control_error_policy.h"

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

/***********************************************************************/
/* LOCAL CONSTANTS                                                     */
/***********************************************************************/

/** L2_CONTROL columns of the status and error catalogue, indexed by code; rows not listed are statuses. */
/* clang-format off */
static const struct control_error_row control_errorRows[FEEDBACK_CODE_COUNT] = {
    [FEEDBACK_DELIVERY_FAILURE]            = {CONTROL_PRIORITY_LOW,    CONTROL_CLEAR_RULE_SHORT_PRESS, CONTROL_ADMISSION_START_BLOCKED},
    [FEEDBACK_DELIVERY_NOT_POSSIBLE]       = {CONTROL_PRIORITY_LOW,    CONTROL_CLEAR_RULE_SHORT_PRESS, CONTROL_ADMISSION_START_BLOCKED},
    [FEEDBACK_SERVER_CONNECTION_FAILURE]   = {CONTROL_PRIORITY_LOW,    CONTROL_CLEAR_RULE_SHORT_PRESS, CONTROL_ADMISSION_START_PERMITTED},
    [FEEDBACK_DEVICE_REGISTRATION_FAILURE] = {CONTROL_PRIORITY_LOW,    CONTROL_CLEAR_RULE_SHORT_PRESS, CONTROL_ADMISSION_START_PERMITTED},
    [FEEDBACK_MICROPHONE_FAILURE]          = {CONTROL_PRIORITY_MEDIUM, CONTROL_CLEAR_RULE_RESTART,     CONTROL_ADMISSION_HALTED_AT_ONCE},
    [FEEDBACK_AUDIO_WORKER_STALL]          = {CONTROL_PRIORITY_MEDIUM, CONTROL_CLEAR_RULE_RESTART,     CONTROL_ADMISSION_HALTED_AT_ONCE},
    [FEEDBACK_AUDIO_OUTPUT_FAILURE]        = {CONTROL_PRIORITY_MEDIUM, CONTROL_CLEAR_RULE_RESTART,     CONTROL_ADMISSION_HALTED_AT_ONCE},
    [FEEDBACK_HEART_RATE_WORKER_STALL]     = {CONTROL_PRIORITY_LOW,    CONTROL_CLEAR_RULE_RESTART,     CONTROL_ADMISSION_HALTED},
    [FEEDBACK_MEASUREMENT_INVALID]         = {CONTROL_PRIORITY_LOW,    CONTROL_CLEAR_RULE_SHORT_PRESS, CONTROL_ADMISSION_START_BLOCKED},
    [FEEDBACK_CONTROL_INPUT_FAILURE]       = {CONTROL_PRIORITY_MEDIUM, CONTROL_CLEAR_RULE_RESTART,     CONTROL_ADMISSION_HALTED},
    [FEEDBACK_JOIN_FAILURE]                = {CONTROL_PRIORITY_LOW,    CONTROL_CLEAR_RULE_SHORT_PRESS, CONTROL_ADMISSION_START_PERMITTED},
    [FEEDBACK_RECONNECT_FAILURE]           = {CONTROL_PRIORITY_LOW,    CONTROL_CLEAR_RULE_SHORT_PRESS, CONTROL_ADMISSION_START_PERMITTED},
    [FEEDBACK_SCAN_FAILURE]                = {CONTROL_PRIORITY_LOW,    CONTROL_CLEAR_RULE_SHORT_PRESS, CONTROL_ADMISSION_START_PERMITTED},
    [FEEDBACK_HOTSPOT_START_FAILURE]       = {CONTROL_PRIORITY_LOW,    CONTROL_CLEAR_RULE_SHORT_PRESS, CONTROL_ADMISSION_START_PERMITTED},
    [FEEDBACK_WIFI_SETTINGS_SAVE_FAILURE]  = {CONTROL_PRIORITY_LOW,    CONTROL_CLEAR_RULE_SHORT_PRESS, CONTROL_ADMISSION_START_PERMITTED},
    [FEEDBACK_WIFI_CLEANUP_FAILURE]        = {CONTROL_PRIORITY_LOW,    CONTROL_CLEAR_RULE_RESTART,     CONTROL_ADMISSION_START_PERMITTED},
    [FEEDBACK_SETTINGS_READ_FAILURE]       = {CONTROL_PRIORITY_LOW,    CONTROL_CLEAR_RULE_RESTART,     CONTROL_ADMISSION_HALTED},
    [FEEDBACK_SETTINGS_SAVE_FAILURE]       = {CONTROL_PRIORITY_LOW,    CONTROL_CLEAR_RULE_RESTART,     CONTROL_ADMISSION_HALTED},
    [FEEDBACK_STARTUP_FAILURE]             = {CONTROL_PRIORITY_LOW,    CONTROL_CLEAR_RULE_RESTART,     CONTROL_ADMISSION_HALTED},
    [FEEDBACK_RESET_UNEXPECTED]            = {CONTROL_PRIORITY_LOW,    CONTROL_CLEAR_RULE_SHORT_PRESS, CONTROL_ADMISSION_START_BLOCKED},
    [FEEDBACK_SESSION_CONTEXT_CHANGE]      = {CONTROL_PRIORITY_LOW,    CONTROL_CLEAR_RULE_RESTART,     CONTROL_ADMISSION_HALTED},
};
/* clang-format on */

/***********************************************************************/
/* LOCAL FUNCTION PROTOTYPES                                           */
/***********************************************************************/

/**
 * @brief Position of the error shown in the latch order.
 *
 * @param[in] latch Error latch with at least one error.
 *
 * @return Index into latch->errors.
 */
static uint32_t control_getShownErrorIndex(const struct control_error_latch *latch);

/***********************************************************************/
/* GLOBAL FUNCTIONS                                                    */
/***********************************************************************/

const struct control_error_row *control_getErrorRow(enum feedback_code code)
{
    return &control_errorRows[code];
}

bool control_isError(enum feedback_code code)
{
    bool isError = false;
    const int codeNumber = (int)code;
    const int lowestCodeNumber = (int)FEEDBACK_NONE;
    const int codeCount = (int)FEEDBACK_CODE_COUNT;

    if((codeNumber >= lowestCodeNumber) && (codeNumber < codeCount))
    {
        isError = (control_errorRows[code].priority != CONTROL_PRIORITY_INFORMATION);
    }

    return isError;
}

void control_resetErrorLatch(struct control_error_latch *latch)
{
    latch->errorCount = 0U;
}

bool control_latchError(struct control_error_latch *latch, enum feedback_code code)
{
    bool isLatched = false;

    for(uint32_t index = 0U; (index < latch->errorCount) && !isLatched; index++)
    {
        isLatched = (latch->errors[index] == code);
    }

    bool isNewlyLatched = (control_isError(code) && !isLatched && (latch->errorCount < (uint32_t)FEEDBACK_CODE_COUNT));

    if(isNewlyLatched)
    {
        latch->errors[latch->errorCount] = code;
        latch->errorCount++;
    }

    return isNewlyLatched;
}

enum feedback_code control_getShownError(const struct control_error_latch *latch)
{
    enum feedback_code shownError = FEEDBACK_NONE;

    if(latch->errorCount > 0U)
    {
        shownError = latch->errors[control_getShownErrorIndex(latch)];
    }

    return shownError;
}

bool control_acknowledgeShownError(struct control_error_latch *latch)
{
    bool isAcknowledged = false;

    if(latch->errorCount > 0U)
    {
        uint32_t shownIndex = control_getShownErrorIndex(latch);

        isAcknowledged = (control_errorRows[latch->errors[shownIndex]].clearRule == CONTROL_CLEAR_RULE_SHORT_PRESS);

        if(isAcknowledged)
        {
            const uint32_t lastErrorIndex = latch->errorCount - 1U;

            for(uint32_t index = shownIndex; index < lastErrorIndex; index++)
            {
                latch->errors[index] = latch->errors[index + 1U];
            }

            latch->errorCount--;
        }
    }

    return isAcknowledged;
}

bool control_hasAdmission(const struct control_error_latch *latch, enum control_admission admission)
{
    bool hasAdmission = false;

    for(uint32_t index = 0U; (index < latch->errorCount) && !hasAdmission; index++)
    {
        hasAdmission = (control_errorRows[latch->errors[index]].admission == admission);
    }

    return hasAdmission;
}

bool control_isHalted(const struct control_error_latch *latch)
{
    return (control_hasAdmission(latch, CONTROL_ADMISSION_HALTED) || control_hasAdmission(latch, CONTROL_ADMISSION_HALTED_AT_ONCE));
}

enum feedback_code control_selectFeedback(const struct control_error_latch *latch, bool isIndicationDeferred, enum feedback_code status)
{
    enum feedback_code shownError = control_getShownError(latch);
    enum feedback_code feedback = status;
    const bool isHaltedAtOnce = control_hasAdmission(latch, CONTROL_ADMISSION_HALTED_AT_ONCE);

    if(isHaltedAtOnce)
    {
        feedback = shownError;
    }
    else if(!isIndicationDeferred && (shownError != FEEDBACK_NONE))
    {
        feedback = shownError;
    }
    else
    {
        feedback = status;
    }

    return feedback;
}

enum control_press_action control_decideShortPress(const struct control_error_latch *latch, bool isIndicationDeferred)
{
    enum control_press_action action = CONTROL_PRESS_WORKFLOW;
    enum feedback_code shownError = control_getShownError(latch);
    const bool isHaltedAtOnce = control_hasAdmission(latch, CONTROL_ADMISSION_HALTED_AT_ONCE);
    const bool isHalted = control_isHalted(latch);
    const bool isStartBlocked = control_hasAdmission(latch, CONTROL_ADMISSION_START_BLOCKED);

    if(isHaltedAtOnce)
    {
        action = CONTROL_PRESS_IGNORE;
    }
    else if(isIndicationDeferred)
    {
        action = CONTROL_PRESS_WORKFLOW;
    }
    else if(isHalted)
    {
        action = CONTROL_PRESS_IGNORE;
    }
    else if((shownError != FEEDBACK_NONE) && (control_errorRows[shownError].clearRule == CONTROL_CLEAR_RULE_SHORT_PRESS))
    {
        action = CONTROL_PRESS_ACKNOWLEDGE;
    }
    else if(isStartBlocked)
    {
        action = CONTROL_PRESS_REJECT;
    }
    else
    {
        action = CONTROL_PRESS_WORKFLOW;
    }

    return action;
}

enum control_press_action control_decideLongPress(const struct control_error_latch *latch, bool isIndicationDeferred)
{
    enum control_press_action action = CONTROL_PRESS_WORKFLOW;
    const bool isHaltedAtOnce = control_hasAdmission(latch, CONTROL_ADMISSION_HALTED_AT_ONCE);
    const bool isHalted = control_isHalted(latch);

    if(isHaltedAtOnce)
    {
        action = CONTROL_PRESS_IGNORE;
    }
    else if(!isIndicationDeferred && isHalted)
    {
        action = CONTROL_PRESS_IGNORE;
    }
    else
    {
        action = CONTROL_PRESS_WORKFLOW;
    }

    return action;
}

/***********************************************************************/
/* LOCAL FUNCTIONS                                                     */
/***********************************************************************/

static uint32_t control_getShownErrorIndex(const struct control_error_latch *latch)
{
    uint32_t shownIndex = 0U;

    for(uint32_t index = 1U; index < latch->errorCount; index++)
    {
        if(control_errorRows[latch->errors[index]].priority > control_errorRows[latch->errors[shownIndex]].priority)
        {
            shownIndex = index;
        }
    }

    return shownIndex;
}

/** @} */
