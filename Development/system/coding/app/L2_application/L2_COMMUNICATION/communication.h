/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @defgroup L2COMMUNICATION COMMUNICATION
 * @{
 * @file
 * L2 delivery: builds messages via FHIR, sends via WIFI under the
 * lease.
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
 * Does not block, so it can also be called from an interrupt. CONTROL is the
 * sole producer. Start and Stop update the requested state under a spinlock;
 * coalesced wakeups do not drop that state. A Start invalidates any earlier
 * stopped acknowledgement. Setup holds during listening or setup are ignored.
 *
 * @param[in] event Event to send.
 *
 * @return 0 on success, -EINVAL for an unknown event.
 */
int communication_postEvent(enum communication_event event);

/**
 * @brief Wait until Wi-Fi work has stopped after COMMUNICATION_EVENT_LISTENING_STARTED.
 *
 * Control posts LISTENING_STARTED and calls this before audio starts.
 * CONTROL must not post Stop or another Start concurrently with this wait.
 * The station association stays. Failed driver cancellation or teardown
 * withholds success; CONTROL must keep audio stopped on timeout.
 * Wait slicing is not a guarantee of total shutdown latency.
 *
 * @param[in] timeout Maximum time to wait.
 *
 * @return 0 when Wi-Fi work has stopped, -EAGAIN if not within @p timeout.
 */
int communication_waitForWiFiStop(k_timeout_t timeout);

#endif /* L2_COMMUNICATION_H */

/** @} */
