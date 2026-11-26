/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @defgroup L1_PHYSICALINTERFACE PHYSICALINTERFACE
 * @{
 * @file
 * Adapter for the Start/Stop button, the listening-filter switch, the volume potentiometer,
 * the RGB status light and the button light over the Zephyr GPIO, ADC and LED strip drivers.
 */

#ifndef L1_PHYSICALINTERFACE_H
#define L1_PHYSICALINTERFACE_H

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include <stdint.h>

#include "feedback.h"

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

/** Filter reported with a failed switch reading: Raw applies no band filter, so no sound is hidden. */
#define PHYSICALINTERFACE_SAFE_LISTENING_FILTER PHYSICALINTERFACE_LISTENING_FILTER_RAW

/** Volume reported with a failed or absent potentiometer reading: silent output. */
#define PHYSICALINTERFACE_SAFE_VOLUME_PERCENT 0

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/** Debounced Start/Stop button event. */
enum physicalinterface_button_event
{
    PHYSICALINTERFACE_BUTTON_SHORT_PRESS, /**< Released before the long-press time. */
    PHYSICALINTERFACE_BUTTON_LONG_PRESS,  /**< Held for the long-press time; the release that follows is not a short press. */
};

/** Position of the Raw/Murmur/BPM switch. */
enum physicalinterface_listening_filter
{
    PHYSICALINTERFACE_LISTENING_FILTER_RAW,
    PHYSICALINTERFACE_LISTENING_FILTER_MURMUR,
    PHYSICALINTERFACE_LISTENING_FILTER_BPM,
};

/** Whether an input reading can be used. */
enum physicalinterface_input_status
{
    PHYSICALINTERFACE_INPUT_VALID,  /**< The reading reflects the control. */
    PHYSICALINTERFACE_INPUT_FAILED, /**< ADC or GPIO failure, or no valid switch position; the reading carries the safe value. */
    PHYSICALINTERFACE_INPUT_ABSENT, /**< The control is not fitted (potentiometer only); the reading carries the safe value. */
};

/** Stable reading of the Raw/Murmur/BPM switch. */
struct physicalinterface_listening_filter_reading
{
    enum physicalinterface_listening_filter filter; /**< PHYSICALINTERFACE_SAFE_LISTENING_FILTER unless valid. */
    enum physicalinterface_input_status status;     /**< VALID or FAILED. */
    int64_t timestampMilliseconds;                  /**< Uptime at which the reading became stable. */
};

/** Reading of the volume potentiometer. */
struct physicalinterface_volume_reading
{
    uint8_t percent;                            /**< 0 to 100; PHYSICALINTERFACE_SAFE_VOLUME_PERCENT unless valid. */
    enum physicalinterface_input_status status; /**< VALID, FAILED, or ABSENT if the potentiometer is not fitted. */
    int64_t timestampMilliseconds;              /**< Uptime of the ADC reading. */
};

/**
 * @brief Receives button events on the system work queue.
 *
 * @param[in] event Debounced button event.
 * @param[in] timestampMilliseconds Uptime at which the press, release or hold was recognized.
 */
typedef void (*physicalinterface_button_handler)(enum physicalinterface_button_event event, int64_t timestampMilliseconds);

/**
 * @brief Receives the switch reading on the system work queue: the first stable
 *        reading after initialization, then one per stable transition.
 *
 * @param[in] reading New stable reading; valid only during the call.
 */
typedef void (*physicalinterface_listening_filter_handler)(const struct physicalinterface_listening_filter_reading *reading);

/**
 * @brief Receives the volume on the system work queue: the first reading after
 *        initialization, then each change of status, each change of at least
 *        2 %, and each reach of 0 % or 100 %.
 *
 * An absent potentiometer is reported once and then never again.
 *
 * @param[in] reading New reading; valid only during the call.
 */
typedef void (*physicalinterface_volume_handler)(const struct physicalinterface_volume_reading *reading);

/** Receivers of the input events; none may be NULL. */
struct physicalinterface_input_handlers
{
    physicalinterface_button_handler button;
    physicalinterface_listening_filter_handler listeningFilter;
    physicalinterface_volume_handler volume;
};

/***********************************************************************/
/* GLOBAL CONSTANTS                                                    */
/***********************************************************************/

/***********************************************************************/
/* GLOBAL VARIABLES                                                    */
/***********************************************************************/

/***********************************************************************/
/* GLOBAL FUNCTION PROTOTYPES                                          */
/***********************************************************************/

/**
 * @brief Initialize the RGB status light and the red button light, switch both
 *        off, and start the inputs: Start/Stop button, Raw/Murmur/BPM switch and
 *        volume potentiometer.
 *
 * Each part works without the others: a failed light does not stop the other
 * light or the inputs, and a failed input does not stop the other parts. A failed switch or
 * potentiometer is also reported to its handler as a FAILED reading. Without
 * CONFIG_PHYSICALINTERFACE_VOLUME_POTENTIOMETER_FITTED the ADC is not read and
 * the volume handler receives one ABSENT reading.
 *
 * @param[in] handlers Receivers of the input events; must not be NULL and is
 *                     copied, so it need not outlive the call.
 *
 * @return 0 on success, -ENODEV if a driver is not ready, or the first GPIO or ADC setup error.
 */
int physicalinterface_init(const struct physicalinterface_input_handlers *handlers);

/**
 * @brief Show a catalogue row on the RGB status light and the red button light.
 *
 * Does not block; the patterns run on the system work queue. While the button
 * is down the red light shows the press instead of its row.
 *
 * @param[in] code Catalogue code to show; FEEDBACK_NONE switches both lights off.
 */
void physicalinterface_showFeedback(enum feedback_code code);

#endif /* L1_PHYSICALINTERFACE_H */

/** @} */
