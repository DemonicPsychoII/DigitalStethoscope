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

#include <stdint.h>

#include <zephyr/kernel.h>

#include "feedback.h"

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/** Kind of a finalized result that is delivered. */
enum communication_delivery_kind
{
    COMMUNICATION_DELIVERY_HEART_RATE,  /**< Valid BPM value. */
    COMMUNICATION_DELIVERY_POOR_SIGNAL, /**< Invalid BPM: error report without a value (REQ-08). */
};

/** One finalized result; copied and frozen on admission. */
struct communication_delivery
{
    uint64_t measurementEndMonotonicMicroseconds; /**< Kernel timestamp of the end of the aggregate interval. */
    enum communication_delivery_kind kind;        /**< Value or error report. */
    uint32_t heartRateScaled;                     /**< BPM times 10^heartRateDecimalPlaces; heart rate only. */
    uint8_t heartRateDecimalPlaces;               /**< Declared precision, 0 to 9; heart rate only. */
};

/** Outcome of the latest delivery job. */
enum communication_delivery_outcome
{
    COMMUNICATION_DELIVERY_NONE,      /**< No job admitted since boot. */
    COMMUNICATION_DELIVERY_PENDING,   /**< The job runs under P13. */
    COMMUNICATION_DELIVERY_DELIVERED, /**< 201 or 200 receipt. */
    COMMUNICATION_DELIVERY_FAILED,    /**< DELIVERY_FAILURE: terminal outcome or exhausted attempts or deadline. */
    COMMUNICATION_DELIVERY_NO_CLOCK,  /**< SERVER_CONNECTION_FAILURE: no qualifying clock anchor by the deadline. */
};

/**
 * @brief Receives Wi-Fi workflow feedback on the communication thread.
 *
 * Statuses and errors use catalogue codes; FEEDBACK_NONE means the Wi-Fi
 * workflow has no status to show any more.
 *
 * @param[in] code Catalogue code of the Wi-Fi workflow.
 */
typedef void (*communication_feedback_handler)(enum feedback_code code);

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
 * @brief Register the receiver of Wi-Fi workflow feedback.
 *
 * Call before communication_init(), so the boot join is reported too.
 * Without a handler, no feedback is reported.
 *
 * @param[in] handler Feedback receiver; only CONTROL registers one.
 */
void communication_setFeedbackHandler(communication_feedback_handler handler);

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
 * On timeout, CONTROL keeps audio stopped. After a latched Wi-Fi cleanup fault this
 * returns 0 while services may still be pending: audio is released under REQ-13,
 * and radio shutdown is not asserted.
 *
 * @param[in] timeout Maximum time to wait.
 *
 * @return 0 when Wi-Fi work has stopped, -EAGAIN if not within @p timeout.
 */
int communication_waitForWiFiStop(k_timeout_t timeout);

/**
 * @brief Admit one finalized result for delivery under P13, without waiting.
 *
 * CONTROL calls this once after finalization, after LISTENING_STOPPED, and treats
 * the job as running until communication_getDeliveryOutcome() reports a final
 * outcome. Prerequisites are checked once, at this call, without waiting.
 *
 * @param[in] delivery Result; copied.
 * @param[in] deadline P13: Stop plus 10 s, for all attempts, cancellation and release.
 *
 * @return 0 if admitted; -ENOENT when Wi-Fi is not configured (nothing is sent and
 *         nothing retained, no error); -ENODEV when a delivery prerequisite fails
 *         (no saved Device registration or no valid server profile):
 *         DELIVERY_NOT_POSSIBLE; -EBUSY while a job runs; -EINVAL for an invalid result.
 */
int communication_submitDelivery(const struct communication_delivery *delivery, k_timepoint_t deadline);

/**
 * @brief Report the outcome of the latest delivery job.
 *
 * @return The outcome; PENDING until the job ends.
 */
enum communication_delivery_outcome communication_getDeliveryOutcome(void);

#endif /* L2_COMMUNICATION_H */

/** @} */
