/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @defgroup COMMON_FEEDBACK FEEDBACK
 * @{
 * @file
 * Status and error codes of the feedback catalogue
 * (design/FEEDBACK/catalogue.md). New codes are only appended.
 */

#ifndef COMMON_FEEDBACK_H
#define COMMON_FEEDBACK_H

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/** One row of the status and error catalogue. */
enum feedback_code
{
    FEEDBACK_NONE,                        /**< No indication: lights off. */
    FEEDBACK_DELIVERY_SENDING,            /**< Status: sending. */
    FEEDBACK_DELIVERY_PENDING,            /**< Status: delivery pending. */
    FEEDBACK_DELIVERY_RECEIVED,           /**< Status: delivery received (201/200). */
    FEEDBACK_SERVER_CONNECTION_FAILURE,   /**< Error: secure server connection or its time synchronization failed. */
    FEEDBACK_DEVICE_REGISTRATION_FAILURE, /**< Error: device registration failed. */
    FEEDBACK_DELIVERY_FAILURE,            /**< Error: terminal delivery failure or exhausted retries. */
    FEEDBACK_DELIVERY_NOT_POSSIBLE,       /**< Error: result cannot be sent. */
    FEEDBACK_LISTENING,                   /**< Status: listening. */
    FEEDBACK_MEASUREMENT_RUNNING,         /**< Status: measuring, less than 15 s. */
    FEEDBACK_MEASUREMENT_MINIMUM_REACHED, /**< Status: measuring, at least 15 s. */
    FEEDBACK_ANALYSIS_RUNNING,            /**< Status: analysing. */
    FEEDBACK_AUDIO_WORKER_STALL,          /**< Error: audio worker stall. */
    FEEDBACK_HEART_RATE_WORKER_STALL,     /**< Error: BPM worker stall. */
    FEEDBACK_MEASUREMENT_INVALID,         /**< Error: BPM result invalid. */
    FEEDBACK_MICROPHONE_FAILURE,          /**< Error: microphone delivers no data or I2S RX error. */
    FEEDBACK_AUDIO_OUTPUT_FAILURE,        /**< Error: DAC I2S TX error. */
    FEEDBACK_CONTROL_INPUT_FAILURE,       /**< Error: potentiometer ADC or switch position failure. */
    FEEDBACK_IDLE,                        /**< Status: Idle. */
    FEEDBACK_PORTAL_OPEN,                 /**< Status: portal and hotspot open. */
    FEEDBACK_WIFI_CONNECTING,             /**< Status: Wi-Fi scanning, connecting or reconnecting. */
    FEEDBACK_WIFI_CONNECTED,              /**< Status: Wi-Fi connected. */
    FEEDBACK_WIFI_SETTINGS_SAVE_FAILURE,  /**< Error: Wi-Fi credentials save failed after 2 attempts. */
    FEEDBACK_SCAN_FAILURE,                /**< Error: Wi-Fi scan used all attempts. */
    FEEDBACK_JOIN_FAILURE,                /**< Error: Wi-Fi boot join used all attempts. */
    FEEDBACK_RECONNECT_FAILURE,           /**< Error: Wi-Fi link loss used all attempts. */
    FEEDBACK_HOTSPOT_START_FAILURE,       /**< Error: hotspot start failed. */
    FEEDBACK_WIFI_CLEANUP_FAILURE,        /**< Error: Wi-Fi cleanup stop failed. */
    FEEDBACK_STARTUP_RUNNING,             /**< Status: boot and startup checks. */
    FEEDBACK_SETTINGS_READ_FAILURE,       /**< Error: settings read from flash failed. */
    FEEDBACK_STARTUP_FAILURE,             /**< Error: startup check failed. */
    FEEDBACK_RESET_UNEXPECTED,            /**< Error: unexpected reset (watchdog, crash, brown-out). */
    FEEDBACK_SETTINGS_SAVE_FAILURE,       /**< Error: settings save to flash failed. */
    FEEDBACK_SESSION_CONTEXT_CHANGE,      /**< Error: context change during a session. */
    FEEDBACK_INPUT_REJECTED,              /**< Status overlay: input rejected. */
    FEEDBACK_ERROR_ACKNOWLEDGED,          /**< Status overlay: error acknowledged. */
    FEEDBACK_CODE_COUNT,                  /**< Number of codes; not a code. */
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

#endif /* COMMON_FEEDBACK_H */

/** @} */
