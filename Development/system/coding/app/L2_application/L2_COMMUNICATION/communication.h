/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @defgroup L2_COMMUNICATION COMMUNICATION
 * @{
 * @file
 * L2 communication: Wi-Fi connection and setup. Later also builds the
 * messages via FHIR and sends them via WIFI.
 * Implements Development/system/design/WIFI/interfaces-and-behavior.md and
 * Development/system/design/PORTAL/interfaces-and-behavior.md.
 */

#ifndef L2_COMMUNICATION_H
#define L2_COMMUNICATION_H

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include <zephyr/kernel.h>

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/** Event from control to the communication thread. */
enum communication_event
{
    COMMUNICATION_EVENT_SETUP_REQUESTED,   /**< 2 s button hold: open Wi-Fi setup (Idle only). */
    COMMUNICATION_EVENT_LISTENING_STARTED, /**< Listening starts: end setup, no Wi-Fi work. */
    COMMUNICATION_EVENT_LISTENING_STOPPED, /**< Listening stopped: back in Idle. */
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
 * @brief Initialize the communication module.
 *
 * This includes the on-board WIFI module.
 */
void communication_init(void);

/**
 * @brief Send an event from control to the communication thread.
 *
 * Does not block, so it can also be called from an interrupt. Only CONTROL
 * sends events. A setup request during listening or setup is ignored.
 *
 * @param[in] event Event to send.
 *
 * @return 0 on success, -EINVAL for an unknown event.
 */
int communication_postEvent(enum communication_event event);

/**
 * @brief Wait until the Wi-Fi work has stopped after COMMUNICATION_EVENT_LISTENING_STARTED.
 *
 * CONTROL calls this after LISTENING_STARTED and before audio starts, and
 * sends no other event during the wait. A connected station stays connected.
 * On timeout, CONTROL keeps audio stopped.
 *
 * @param[in] timeout Maximum time to wait.
 *
 * @return 0 when Wi-Fi work has stopped, -EAGAIN if not within @p timeout.
 */
int communication_waitForWiFiStop(k_timeout_t timeout);

#endif /* L2_COMMUNICATION_H */

/** @} */
