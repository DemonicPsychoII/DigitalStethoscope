/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L1_PHYSICALINTERFACE
 * @{
 * @file
 * Implementation of the indication of the PHYSICALINTERFACE module.
 */

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include "physicalinterface_indication.h"

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

/***********************************************************************/
/* LOCAL CONSTANTS                                                     */
/***********************************************************************/

/** Both light columns of the status and error catalogue, indexed by code. */
/* clang-format off */
static const struct physicalinterface_indication_row physicalinterface_indicationRows[FEEDBACK_CODE_COUNT] = {
    [FEEDBACK_NONE]                        = {PHYSICALINTERFACE_COLOUR_OFF,    PHYSICALINTERFACE_PATTERN_OFF,                 PHYSICALINTERFACE_BUTTON_LIGHT_OFF,             0},
    [FEEDBACK_DELIVERY_SENDING]            = {PHYSICALINTERFACE_COLOUR_BLUE,   PHYSICALINTERFACE_PATTERN_BREATHING_SLOW,      PHYSICALINTERFACE_BUTTON_LIGHT_OFF,             0},
    [FEEDBACK_DELIVERY_PENDING]            = {PHYSICALINTERFACE_COLOUR_BLUE,   PHYSICALINTERFACE_PATTERN_BLINK_SLOW,          PHYSICALINTERFACE_BUTTON_LIGHT_OFF,             0},
    [FEEDBACK_DELIVERY_RECEIVED]           = {PHYSICALINTERFACE_COLOUR_BLUE,   PHYSICALINTERFACE_PATTERN_THREE_QUICK_FLASHES, PHYSICALINTERFACE_BUTTON_LIGHT_OFF,             0},
    [FEEDBACK_DELIVERY_FAILURE]            = {PHYSICALINTERFACE_COLOUR_BLUE,   PHYSICALINTERFACE_PATTERN_STEADY,              PHYSICALINTERFACE_BUTTON_LIGHT_BLINK_CODE,      3},
    [FEEDBACK_DELIVERY_NOT_POSSIBLE]       = {PHYSICALINTERFACE_COLOUR_BLUE,   PHYSICALINTERFACE_PATTERN_STEADY,              PHYSICALINTERFACE_BUTTON_LIGHT_BLINK_CODE,      4},
    [FEEDBACK_SERVER_CONNECTION_FAILURE]   = {PHYSICALINTERFACE_COLOUR_BLUE,   PHYSICALINTERFACE_PATTERN_STEADY,              PHYSICALINTERFACE_BUTTON_LIGHT_BLINK_CODE,      1},
    [FEEDBACK_DEVICE_REGISTRATION_FAILURE] = {PHYSICALINTERFACE_COLOUR_BLUE,   PHYSICALINTERFACE_PATTERN_STEADY,              PHYSICALINTERFACE_BUTTON_LIGHT_BLINK_CODE,      2},
    [FEEDBACK_LISTENING]                   = {PHYSICALINTERFACE_COLOUR_CYAN,   PHYSICALINTERFACE_PATTERN_STEADY,              PHYSICALINTERFACE_BUTTON_LIGHT_OFF,             0},
    [FEEDBACK_MEASUREMENT_RUNNING]         = {PHYSICALINTERFACE_COLOUR_CYAN,   PHYSICALINTERFACE_PATTERN_BLINK_SLOW,          PHYSICALINTERFACE_BUTTON_LIGHT_OFF,             0},
    [FEEDBACK_MEASUREMENT_MINIMUM_REACHED] = {PHYSICALINTERFACE_COLOUR_CYAN,   PHYSICALINTERFACE_PATTERN_STEADY,              PHYSICALINTERFACE_BUTTON_LIGHT_OFF,             0},
    [FEEDBACK_ANALYSIS_RUNNING]            = {PHYSICALINTERFACE_COLOUR_CYAN,   PHYSICALINTERFACE_PATTERN_BREATHING_SLOW,      PHYSICALINTERFACE_BUTTON_LIGHT_OFF,             0},
    [FEEDBACK_MICROPHONE_FAILURE]          = {PHYSICALINTERFACE_COLOUR_CYAN,   PHYSICALINTERFACE_PATTERN_STEADY,              PHYSICALINTERFACE_BUTTON_LIGHT_BLINK_CODE,      4},
    [FEEDBACK_AUDIO_WORKER_STALL]          = {PHYSICALINTERFACE_COLOUR_CYAN,   PHYSICALINTERFACE_PATTERN_STEADY,              PHYSICALINTERFACE_BUTTON_LIGHT_BLINK_CODE,      1},
    [FEEDBACK_AUDIO_OUTPUT_FAILURE]        = {PHYSICALINTERFACE_COLOUR_CYAN,   PHYSICALINTERFACE_PATTERN_STEADY,              PHYSICALINTERFACE_BUTTON_LIGHT_BLINK_CODE,      5},
    [FEEDBACK_HEART_RATE_WORKER_STALL]     = {PHYSICALINTERFACE_COLOUR_CYAN,   PHYSICALINTERFACE_PATTERN_STEADY,              PHYSICALINTERFACE_BUTTON_LIGHT_BLINK_CODE,      2},
    [FEEDBACK_MEASUREMENT_INVALID]         = {PHYSICALINTERFACE_COLOUR_CYAN,   PHYSICALINTERFACE_PATTERN_STEADY,              PHYSICALINTERFACE_BUTTON_LIGHT_BLINK_CODE,      3},
    [FEEDBACK_CONTROL_INPUT_FAILURE]       = {PHYSICALINTERFACE_COLOUR_CYAN,   PHYSICALINTERFACE_PATTERN_STEADY,              PHYSICALINTERFACE_BUTTON_LIGHT_BLINK_CODE,      6},
    [FEEDBACK_IDLE]                        = {PHYSICALINTERFACE_COLOUR_GREEN,  PHYSICALINTERFACE_PATTERN_STEADY_DIM,          PHYSICALINTERFACE_BUTTON_LIGHT_OFF,             0},
    [FEEDBACK_WIFI_CONNECTING]             = {PHYSICALINTERFACE_COLOUR_VIOLET, PHYSICALINTERFACE_PATTERN_BREATHING_SLOW,      PHYSICALINTERFACE_BUTTON_LIGHT_OFF,             0},
    [FEEDBACK_WIFI_CONNECTED]              = {PHYSICALINTERFACE_COLOUR_VIOLET, PHYSICALINTERFACE_PATTERN_THREE_QUICK_FLASHES, PHYSICALINTERFACE_BUTTON_LIGHT_OFF,             0},
    [FEEDBACK_PORTAL_OPEN]                 = {PHYSICALINTERFACE_COLOUR_VIOLET, PHYSICALINTERFACE_PATTERN_STEADY,              PHYSICALINTERFACE_BUTTON_LIGHT_OFF,             0},
    [FEEDBACK_JOIN_FAILURE]                = {PHYSICALINTERFACE_COLOUR_VIOLET, PHYSICALINTERFACE_PATTERN_STEADY,              PHYSICALINTERFACE_BUTTON_LIGHT_BLINK_CODE,      3},
    [FEEDBACK_RECONNECT_FAILURE]           = {PHYSICALINTERFACE_COLOUR_VIOLET, PHYSICALINTERFACE_PATTERN_STEADY,              PHYSICALINTERFACE_BUTTON_LIGHT_BLINK_CODE,      4},
    [FEEDBACK_SCAN_FAILURE]                = {PHYSICALINTERFACE_COLOUR_VIOLET, PHYSICALINTERFACE_PATTERN_STEADY,              PHYSICALINTERFACE_BUTTON_LIGHT_BLINK_CODE,      2},
    [FEEDBACK_HOTSPOT_START_FAILURE]       = {PHYSICALINTERFACE_COLOUR_VIOLET, PHYSICALINTERFACE_PATTERN_STEADY,              PHYSICALINTERFACE_BUTTON_LIGHT_BLINK_CODE,      5},
    [FEEDBACK_WIFI_SETTINGS_SAVE_FAILURE]  = {PHYSICALINTERFACE_COLOUR_VIOLET, PHYSICALINTERFACE_PATTERN_STEADY,              PHYSICALINTERFACE_BUTTON_LIGHT_BLINK_CODE,      1},
    [FEEDBACK_WIFI_CLEANUP_FAILURE]        = {PHYSICALINTERFACE_COLOUR_VIOLET, PHYSICALINTERFACE_PATTERN_STEADY,              PHYSICALINTERFACE_BUTTON_LIGHT_BLINK_CODE,      6},
    [FEEDBACK_STARTUP_RUNNING]             = {PHYSICALINTERFACE_COLOUR_WHITE,  PHYSICALINTERFACE_PATTERN_STEADY,              PHYSICALINTERFACE_BUTTON_LIGHT_STEADY,          0},
    [FEEDBACK_SETTINGS_READ_FAILURE]       = {PHYSICALINTERFACE_COLOUR_WHITE,  PHYSICALINTERFACE_PATTERN_STEADY,              PHYSICALINTERFACE_BUTTON_LIGHT_BLINK_CODE,      1},
    [FEEDBACK_SETTINGS_SAVE_FAILURE]       = {PHYSICALINTERFACE_COLOUR_WHITE,  PHYSICALINTERFACE_PATTERN_STEADY,              PHYSICALINTERFACE_BUTTON_LIGHT_BLINK_CODE,      4},
    [FEEDBACK_STARTUP_FAILURE]             = {PHYSICALINTERFACE_COLOUR_WHITE,  PHYSICALINTERFACE_PATTERN_STEADY,              PHYSICALINTERFACE_BUTTON_LIGHT_BLINK_CODE,      2},
    [FEEDBACK_RESET_UNEXPECTED]            = {PHYSICALINTERFACE_COLOUR_WHITE,  PHYSICALINTERFACE_PATTERN_STEADY,              PHYSICALINTERFACE_BUTTON_LIGHT_BLINK_CODE,      3},
    [FEEDBACK_SESSION_CONTEXT_CHANGE]      = {PHYSICALINTERFACE_COLOUR_WHITE,  PHYSICALINTERFACE_PATTERN_STEADY,              PHYSICALINTERFACE_BUTTON_LIGHT_BLINK_CODE,      5},
    [FEEDBACK_INPUT_REJECTED]              = {PHYSICALINTERFACE_COLOUR_OFF,    PHYSICALINTERFACE_PATTERN_DIM_ONCE,            PHYSICALINTERFACE_BUTTON_LIGHT_NO_CHANGE,       0},
    [FEEDBACK_ERROR_ACKNOWLEDGED]          = {PHYSICALINTERFACE_COLOUR_OFF,    PHYSICALINTERFACE_PATTERN_NO_CHANGE,           PHYSICALINTERFACE_BUTTON_LIGHT_LONG_FLASH_ONCE, 0},
    [FEEDBACK_BUTTON_HOLD_ACKNOWLEDGED]    = {PHYSICALINTERFACE_COLOUR_OFF,    PHYSICALINTERFACE_PATTERN_NO_CHANGE,           PHYSICALINTERFACE_BUTTON_LIGHT_HOLD_BLINK,      0},
};
/* clang-format on */

/***********************************************************************/
/* LOCAL FUNCTION PROTOTYPES                                           */
/***********************************************************************/

/**
 * @brief Brightness of an RGB pattern at a time since its start.
 *
 * @param[in] pattern Pattern to evaluate.
 * @param[in] elapsedMilliseconds Time since the pattern started.
 * @param[out] isAnimated True while later steps can still change the brightness.
 *
 * @return Brightness in percent.
 */
static uint32_t physicalinterface_getStatusLightBrightnessPercent(enum physicalinterface_pattern pattern, int64_t elapsedMilliseconds, bool *isAnimated);

/**
 * @brief Level of the red light pattern of a row at a time since its start.
 *
 * @param[in] row Row to evaluate.
 * @param[in] elapsedMilliseconds Time since the row started.
 * @param[out] isAnimated True while later steps can still change the level.
 *
 * @return True if the red light is on.
 */
static bool physicalinterface_isButtonLightOn(const struct physicalinterface_indication_row *row, int64_t elapsedMilliseconds, bool *isAnimated);

/***********************************************************************/
/* GLOBAL FUNCTIONS                                                    */
/***********************************************************************/

bool physicalinterface_isFeedbackCode(enum feedback_code code)
{
    return (((int)code >= (int)FEEDBACK_NONE) && ((int)code < (int)FEEDBACK_CODE_COUNT));
}

const struct physicalinterface_indication_row *physicalinterface_getIndicationRow(enum feedback_code code)
{
    return &physicalinterface_indicationRows[code];
}

void physicalinterface_resetIndication(struct physicalinterface_indication *indication)
{
    indication->shownCode = FEEDBACK_NONE;
    indication->shownSinceMilliseconds = 0;
    indication->pendingCode = FEEDBACK_NONE;
    indication->hasPendingCode = false;
    indication->isLongFlashActive = false;
    indication->longFlashEndMilliseconds = 0;
    indication->rejectionDimEndMilliseconds = 0;
    indication->isButtonPressed = false;
    indication->isHoldBlinkActive = false;
    indication->holdBlinkSinceMilliseconds = 0;
}

void physicalinterface_applyIndication(struct physicalinterface_indication *indication, enum feedback_code code, int64_t nowMilliseconds)
{
    const struct physicalinterface_indication_row *row = &physicalinterface_indicationRows[code];
    bool isLongFlashRunning = (indication->isLongFlashActive && (nowMilliseconds < indication->longFlashEndMilliseconds));

    if(row->statusLightPattern == PHYSICALINTERFACE_PATTERN_DIM_ONCE)
    {
        indication->rejectionDimEndMilliseconds = nowMilliseconds + PHYSICALINTERFACE_REJECTION_DIM_MILLISECONDS;
    }
    else if(row->buttonLightPattern == PHYSICALINTERFACE_BUTTON_LIGHT_HOLD_BLINK)
    {
        if(indication->isButtonPressed && !indication->isHoldBlinkActive)
        {
            indication->isHoldBlinkActive = true;
            indication->holdBlinkSinceMilliseconds = nowMilliseconds;
        }
    }
    else if(row->buttonLightPattern == PHYSICALINTERFACE_BUTTON_LIGHT_LONG_FLASH_ONCE)
    {
        indication->isLongFlashActive = true;
        indication->longFlashEndMilliseconds = nowMilliseconds + PHYSICALINTERFACE_LONG_FLASH_MILLISECONDS;
    }
    else if(isLongFlashRunning)
    {
        indication->pendingCode = code;
        indication->hasPendingCode = true;
    }
    else
    {
        indication->shownCode = code;
        indication->shownSinceMilliseconds = nowMilliseconds;
        indication->hasPendingCode = false;
        indication->isLongFlashActive = false;
    }
}

void physicalinterface_setIndicationButtonPressed(struct physicalinterface_indication *indication, bool isPressed)
{
    indication->isButtonPressed = isPressed;
    indication->isHoldBlinkActive = false;
}

struct physicalinterface_indication_output physicalinterface_renderIndication(struct physicalinterface_indication *indication, int64_t nowMilliseconds)
{
    struct physicalinterface_indication_output output = {0};
    bool isStatusLightAnimated = false;
    bool isButtonLightAnimated = false;

    if(indication->isLongFlashActive && (nowMilliseconds >= indication->longFlashEndMilliseconds))
    {
        indication->isLongFlashActive = false;

        if(indication->hasPendingCode)
        {
            indication->shownCode = indication->pendingCode;
            indication->shownSinceMilliseconds = indication->longFlashEndMilliseconds;
            indication->hasPendingCode = false;
        }
    }

    const struct physicalinterface_indication_row *row = &physicalinterface_indicationRows[indication->shownCode];
    int64_t elapsedMilliseconds = (nowMilliseconds - indication->shownSinceMilliseconds);

    output.colour = row->colour;
    output.statusLightBrightnessPercent = physicalinterface_getStatusLightBrightnessPercent(row->statusLightPattern, elapsedMilliseconds, &isStatusLightAnimated);

    if(nowMilliseconds < indication->rejectionDimEndMilliseconds)
    {
        output.statusLightBrightnessPercent = ((output.statusLightBrightnessPercent * PHYSICALINTERFACE_REJECTION_DIM_PERCENT) / PHYSICALINTERFACE_FULL_BRIGHTNESS_PERCENT);
        isStatusLightAnimated = true;
    }

    if(indication->isButtonPressed && indication->isHoldBlinkActive)
    {
        int64_t holdMilliseconds = (nowMilliseconds - indication->holdBlinkSinceMilliseconds);

        output.isButtonLightOn = (((holdMilliseconds / PHYSICALINTERFACE_HOLD_BLINK_HALF_PERIOD_MILLISECONDS) % 2) == 0);
        isButtonLightAnimated = true;
    }
    else if(indication->isButtonPressed)
    {
        output.isButtonLightOn = true;
    }
    else if(indication->isLongFlashActive)
    {
        output.isButtonLightOn = true;
        isButtonLightAnimated = true;
    }
    else
    {
        output.isButtonLightOn = physicalinterface_isButtonLightOn(row, elapsedMilliseconds, &isButtonLightAnimated);
    }

    output.isAnimated = (isStatusLightAnimated || isButtonLightAnimated);

    return output;
}

/***********************************************************************/
/* LOCAL FUNCTIONS                                                     */
/***********************************************************************/

static uint32_t physicalinterface_getStatusLightBrightnessPercent(enum physicalinterface_pattern pattern, int64_t elapsedMilliseconds, bool *isAnimated)
{
    uint32_t brightnessPercent = 0U;

    *isAnimated = false;

    switch(pattern)
    {
    case PHYSICALINTERFACE_PATTERN_STEADY:
        brightnessPercent = PHYSICALINTERFACE_FULL_BRIGHTNESS_PERCENT;
        break;

    case PHYSICALINTERFACE_PATTERN_STEADY_DIM:
        brightnessPercent = PHYSICALINTERFACE_IDLE_DIM_BRIGHTNESS_PERCENT;
        break;

    case PHYSICALINTERFACE_PATTERN_BLINK_SLOW:
    {
        int64_t phaseMilliseconds = (elapsedMilliseconds % (2 * PHYSICALINTERFACE_SLOW_BLINK_HALF_PERIOD_MILLISECONDS));

        *isAnimated = true;
        brightnessPercent = ((phaseMilliseconds < PHYSICALINTERFACE_SLOW_BLINK_HALF_PERIOD_MILLISECONDS) ? PHYSICALINTERFACE_FULL_BRIGHTNESS_PERCENT : 0U);
        break;
    }

    case PHYSICALINTERFACE_PATTERN_BREATHING_SLOW:
    {
        int64_t halfPeriodMilliseconds = (PHYSICALINTERFACE_BREATHING_PERIOD_MILLISECONDS / 2);
        int64_t phaseMilliseconds = (elapsedMilliseconds % PHYSICALINTERFACE_BREATHING_PERIOD_MILLISECONDS);
        int64_t distanceFromPeakMilliseconds = ((phaseMilliseconds < halfPeriodMilliseconds) ? phaseMilliseconds : (PHYSICALINTERFACE_BREATHING_PERIOD_MILLISECONDS - phaseMilliseconds));

        *isAnimated = true;
        brightnessPercent = (uint32_t)((distanceFromPeakMilliseconds * PHYSICALINTERFACE_FULL_BRIGHTNESS_PERCENT) / halfPeriodMilliseconds);
        break;
    }

    case PHYSICALINTERFACE_PATTERN_THREE_QUICK_FLASHES:
    {
        int64_t flashSequenceMilliseconds = (2 * PHYSICALINTERFACE_QUICK_FLASH_COUNT * PHYSICALINTERFACE_QUICK_FLASH_HALF_PERIOD_MILLISECONDS);

        if(elapsedMilliseconds < flashSequenceMilliseconds)
        {
            bool isFlashOn = (((elapsedMilliseconds / PHYSICALINTERFACE_QUICK_FLASH_HALF_PERIOD_MILLISECONDS) % 2) == 0);

            *isAnimated = true;
            brightnessPercent = (isFlashOn ? PHYSICALINTERFACE_FULL_BRIGHTNESS_PERCENT : 0U);
        }

        break;
    }

    case PHYSICALINTERFACE_PATTERN_OFF:
    case PHYSICALINTERFACE_PATTERN_NO_CHANGE:
    case PHYSICALINTERFACE_PATTERN_DIM_ONCE:
    default:
        brightnessPercent = 0U;
        break;
    }

    return brightnessPercent;
}

static bool physicalinterface_isButtonLightOn(const struct physicalinterface_indication_row *row, int64_t elapsedMilliseconds, bool *isAnimated)
{
    bool isOn = false;

    *isAnimated = false;

    if(row->buttonLightPattern == PHYSICALINTERFACE_BUTTON_LIGHT_STEADY)
    {
        isOn = true;
    }
    else if((row->buttonLightPattern == PHYSICALINTERFACE_BUTTON_LIGHT_BLINK_CODE) && (row->blinkCount > 0U))
    {
        int64_t blinkGroupMilliseconds = (((2 * (int64_t)row->blinkCount) - 1) * PHYSICALINTERFACE_CODE_BLINK_HALF_PERIOD_MILLISECONDS);
        int64_t phaseMilliseconds = (elapsedMilliseconds % (blinkGroupMilliseconds + PHYSICALINTERFACE_CODE_GROUP_PAUSE_MILLISECONDS));

        *isAnimated = true;
        isOn = ((phaseMilliseconds < blinkGroupMilliseconds) && (((phaseMilliseconds / PHYSICALINTERFACE_CODE_BLINK_HALF_PERIOD_MILLISECONDS) % 2) == 0));
    }
    else
    {
        isOn = false;
    }

    return isOn;
}

/** @} */
