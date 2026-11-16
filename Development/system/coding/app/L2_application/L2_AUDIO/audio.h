/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @defgroup L2_AUDIO AUDIO
 * @{
 * @file
 * L2 audio path and BPM worker, driven by control commands.
 * Implements Development/system/design/AUDIO/interfaces-and-behavior.md.
 */

#ifndef L2_AUDIO_H
#define L2_AUDIO_H

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

/** Command from CONTROL to the audio thread. */
enum audio_command
{
    AUDIO_COMMAND_START, /**< Start both links and the block loop; ignored while running. */
    AUDIO_COMMAND_STOP,  /**< Leave the block loop and stop both links; ignored while stopped. */
};

/** Report from the audio thread to CONTROL. */
enum audio_event
{
    AUDIO_EVENT_STARTED, /**< Both links run and the block loop has started. */
    AUDIO_EVENT_STOPPED, /**< Stopped after AUDIO_COMMAND_STOP; output silent. */
    AUDIO_EVENT_FAULT,   /**< A link failed; both links are stopped and need a device restart. */
};

/**
 * @brief Receives reports on the audio thread.
 *
 * Must not block.
 *
 * @param[in] event Report from the audio thread.
 * @param[in] fault FEEDBACK_MICROPHONE_FAILURE or FEEDBACK_AUDIO_OUTPUT_FAILURE for AUDIO_EVENT_FAULT, otherwise FEEDBACK_NONE.
 */
typedef void (*audio_event_handler)(enum audio_event event, enum feedback_code fault);

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
 * @brief Initialize both I2S links and start the audio thread, which waits for commands.
 *
 * No stream runs afterwards. Call once at boot.
 *
 * @param[in] eventHandler Receives the reports of the audio thread; must not be NULL.
 *
 * @return FEEDBACK_NONE, or the catalogue code of the link that failed.
 */
enum feedback_code audio_init(audio_event_handler eventHandler);

/**
 * @brief Send a command to the audio thread without waiting.
 *
 * Only CONTROL sends commands.
 *
 * @param[in] command Command to send.
 *
 * @return 0 on success, -ENOMSG if the command queue is full.
 */
int audio_postCommand(enum audio_command command);

#endif /* L2_AUDIO_H */

/** @} */
