/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L1_PHYSICALINTERFACE
 * @{
 * @file
 * Light patterns of the status and error catalogue, one table row per code.
 * Private to L1_PHYSICALINTERFACE; pure C without driver access.
 */

#ifndef L1_PHYSICALINTERFACE_INDICATION_H
#define L1_PHYSICALINTERFACE_INDICATION_H

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include <stdbool.h>
#include <stdint.h>

#include "feedback.h"

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

#define PHYSICALINTERFACE_FULL_BRIGHTNESS_PERCENT     100
#define PHYSICALINTERFACE_IDLE_DIM_BRIGHTNESS_PERCENT 20 /**< P22 Idle dim candidate. */
#define PHYSICALINTERFACE_REJECTION_DIM_PERCENT       50 /**< Catalogue: input rejected dims by at least 50 %. */

#define PHYSICALINTERFACE_SLOW_BLINK_HALF_PERIOD_MILLISECONDS  1000 /**< P22 slow blink: 0.5 Hz, 1 s on/off. */
#define PHYSICALINTERFACE_BREATHING_PERIOD_MILLISECONDS        3000 /**< P22 breathing: 3 s. */
#define PHYSICALINTERFACE_QUICK_FLASH_HALF_PERIOD_MILLISECONDS 250  /**< P22 flashes: 2 Hz, 250 ms on/off. */
#define PHYSICALINTERFACE_QUICK_FLASH_COUNT                    3
#define PHYSICALINTERFACE_REJECTION_DIM_MILLISECONDS           250 /**< P22 input-rejected dimming: 250 ms. */

#define PHYSICALINTERFACE_CODE_BLINK_HALF_PERIOD_MILLISECONDS 250  /**< P22 codes: 2 Hz, 250 ms on/off. */
#define PHYSICALINTERFACE_CODE_GROUP_PAUSE_MILLISECONDS       2000 /**< P22: dark time between the last blink of a group and the first of the next. */
#define PHYSICALINTERFACE_CODE_MAXIMUM_BLINKS                 6    /**< P22: at most 6 blinks per context. */
#define PHYSICALINTERFACE_LONG_FLASH_MILLISECONDS             1000 /**< P22 long flash: 1 s. */

/** Nico, 16 November 2026: an accepted hold blinks at 4 Hz, so it does not read as a 2 Hz error code. */
#define PHYSICALINTERFACE_HOLD_BLINK_HALF_PERIOD_MILLISECONDS 125

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/** Context colour of the RGB status light. */
enum physicalinterface_colour
{
    PHYSICALINTERFACE_COLOUR_OFF,
    PHYSICALINTERFACE_COLOUR_BLUE,   /**< FHIR. */
    PHYSICALINTERFACE_COLOUR_CYAN,   /**< Audio. */
    PHYSICALINTERFACE_COLOUR_GREEN,  /**< Idle. */
    PHYSICALINTERFACE_COLOUR_VIOLET, /**< Wi-Fi. */
    PHYSICALINTERFACE_COLOUR_WHITE,  /**< Device. */
};

/** Light pattern of the RGB status light. */
enum physicalinterface_pattern
{
    PHYSICALINTERFACE_PATTERN_NO_CHANGE, /**< Keep the current indication. */
    PHYSICALINTERFACE_PATTERN_OFF,
    PHYSICALINTERFACE_PATTERN_STEADY,
    PHYSICALINTERFACE_PATTERN_STEADY_DIM,
    PHYSICALINTERFACE_PATTERN_BLINK_SLOW,
    PHYSICALINTERFACE_PATTERN_BREATHING_SLOW,
    PHYSICALINTERFACE_PATTERN_THREE_QUICK_FLASHES, /**< Runs once, then the light stays off. */
    PHYSICALINTERFACE_PATTERN_DIM_ONCE,            /**< Dims the current indication once; keeps its colour and pattern. */
};

/** Light pattern of the red button light. */
enum physicalinterface_button_light_pattern
{
    PHYSICALINTERFACE_BUTTON_LIGHT_NO_CHANGE, /**< Keep the current red indication. */
    PHYSICALINTERFACE_BUTTON_LIGHT_OFF,
    PHYSICALINTERFACE_BUTTON_LIGHT_STEADY,          /**< Lamp test. */
    PHYSICALINTERFACE_BUTTON_LIGHT_BLINK_CODE,      /**< "N blinks, pause", repeated until another row replaces it. */
    PHYSICALINTERFACE_BUTTON_LIGHT_LONG_FLASH_ONCE, /**< One long flash over the current indication, then the next row. */
    PHYSICALINTERFACE_BUTTON_LIGHT_HOLD_BLINK,      /**< Fast blink over the current indication until the button is released. */
};

/** Both light columns of one catalogue row. */
struct physicalinterface_indication_row
{
    enum physicalinterface_colour colour;
    enum physicalinterface_pattern statusLightPattern;
    enum physicalinterface_button_light_pattern buttonLightPattern;
    uint8_t blinkCount; /**< Blinks per group for PHYSICALINTERFACE_BUTTON_LIGHT_BLINK_CODE, otherwise 0. */
};

/** Indication state of both lights. */
struct physicalinterface_indication
{
    enum feedback_code shownCode;        /**< Row that both lights show. */
    int64_t shownSinceMilliseconds;      /**< Uptime at which the row started. */
    enum feedback_code pendingCode;      /**< Row that replaces the shown row when the long flash ends. */
    bool hasPendingCode;                 /**< A row waits for the end of the long flash. */
    bool isLongFlashActive;              /**< The red light shows the long flash. */
    int64_t longFlashEndMilliseconds;    /**< Uptime at which the long flash ends. */
    int64_t rejectionDimEndMilliseconds; /**< Uptime at which the input-rejected dimming ends. */
    bool isButtonPressed;                /**< The button is down: the red light shows the press instead of its row. */
    bool isHoldBlinkActive;              /**< The press shown is an accepted hold: fast blink instead of steady. */
    int64_t holdBlinkSinceMilliseconds;  /**< Uptime at which the hold blink started. */
};

/** What both lights show at one time. */
struct physicalinterface_indication_output
{
    enum physicalinterface_colour colour;
    uint32_t statusLightBrightnessPercent; /**< 0 to 100. */
    bool isButtonLightOn;
    bool isAnimated; /**< True while a later time can change the output without a new row. */
};

/***********************************************************************/
/* GLOBAL FUNCTION PROTOTYPES                                          */
/***********************************************************************/

/**
 * @brief Tell whether a value is a code of the catalogue enumeration.
 *
 * @param[in] code Value to check.
 *
 * @return True for FEEDBACK_NONE up to the last code before FEEDBACK_CODE_COUNT.
 */
bool physicalinterface_isFeedbackCode(enum feedback_code code);

/**
 * @brief Light columns of one catalogue row.
 *
 * @param[in] code Catalogue code; must pass physicalinterface_isFeedbackCode().
 *
 * @return Row of the code.
 */
const struct physicalinterface_indication_row *physicalinterface_getIndicationRow(enum feedback_code code);

/**
 * @brief Reset the indication: both lights off.
 *
 * @param[out] indication Indication state.
 */
void physicalinterface_resetIndication(struct physicalinterface_indication *indication);

/**
 * @brief Apply a catalogue code at a time.
 *
 * A row replaces the shown row on both lights; while a long flash runs it waits
 * for the end of the flash. The three overlay codes keep the shown row.
 *
 * @param[in,out] indication Indication state.
 * @param[in] code Catalogue code; must pass physicalinterface_isFeedbackCode().
 * @param[in] nowMilliseconds Uptime; must not decrease between calls.
 */
void physicalinterface_applyIndication(struct physicalinterface_indication *indication, enum feedback_code code, int64_t nowMilliseconds);

/**
 * @brief Tell the indication whether the button is down.
 *
 * While the button is down the red light shows the press instead of its row.
 *
 * @param[in,out] indication Indication state.
 * @param[in] isPressed True while the debounced button is down.
 */
void physicalinterface_setIndicationButtonPressed(struct physicalinterface_indication *indication, bool isPressed);

/**
 * @brief Compute what both lights show at a time.
 *
 * Starts a waiting row once the long flash has ended.
 *
 * @param[in,out] indication Indication state.
 * @param[in] nowMilliseconds Uptime; must not decrease between calls.
 *
 * @return Colour, brightness, red light level and whether the output is animated.
 */
struct physicalinterface_indication_output physicalinterface_renderIndication(struct physicalinterface_indication *indication, int64_t nowMilliseconds);

#endif /* L1_PHYSICALINTERFACE_INDICATION_H */

/** @} */
