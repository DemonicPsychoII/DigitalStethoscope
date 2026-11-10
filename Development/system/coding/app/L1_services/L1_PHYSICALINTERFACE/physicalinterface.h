/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @defgroup L1_PHYSICALINTERFACE PHYSICALINTERFACE
 * @{
 * @file
 * L1 adapter for buttons and LEDs over the Zephyr GPIO/ADC drivers.
 */

#ifndef L1_PHYSICALINTERFACE_H
#define L1_PHYSICALINTERFACE_H

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include "feedback.h"

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/** Debounced Start/Stop button event. */
enum physicalinterface_button_event
{
    PHYSICALINTERFACE_BUTTON_SHORT_PRESS, /**< Released before the long-press time. */
    PHYSICALINTERFACE_BUTTON_LONG_PRESS,  /**< Held for the long-press time; the release that follows is not a short press. */
};

/**
 * @brief Receives button events on the system work queue.
 *
 * @param[in] event Debounced button event.
 */
typedef void (*physicalinterface_button_handler)(enum physicalinterface_button_event event);

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
 * @brief Initialize the RGB status light, switch it off, and start the Start/Stop button input.
 *
 * Each part works without the other: a failed status light does not stop the
 * button, and the other way round.
 *
 * @param[in] buttonHandler Receives the button events; must not be NULL.
 *
 * @return 0 on success, -ENODEV if a driver is not ready, or the GPIO error of the button setup.
 */
int physicalinterface_init(physicalinterface_button_handler buttonHandler);

/**
 * @brief Show the RGB part of a catalogue row on the status light.
 *
 * The light takes the row's context colour and pattern. Error rows show
 * their context colour steady. FEEDBACK_INPUT_REJECTED dims the current
 * indication to half brightness for 250 ms without replacing it. Rows without
 * an RGB change, such as FEEDBACK_ERROR_ACKNOWLEDGED, leave the current
 * indication unchanged.
 * Does not block; the pattern runs on the system work queue.
 *
 * @param[in] code Catalogue code to show; FEEDBACK_NONE switches the light off.
 */
void physicalinterface_showStatusLight(enum feedback_code code);

#endif /* L1_PHYSICALINTERFACE_H */

/** @} */
