/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L2_AUDIO
 * @{
 * @file
 * Implementation of the AUDIO module.
 */

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include "audio.h"

#include <stdbool.h>
#include <stdint.h>

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

#include "i2s.h"

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

#define AUDIO_THREAD_STACK_SIZE (2048) /**< Proposed; measure under VT-02. */
#define AUDIO_THREAD_PRIORITY   (1)    /**< Highest application thread priority; the numeric value is measured under VT-02. */

#define AUDIO_COMMAND_QUEUE_LENGTH (4)

/** The INMP441 does not drive the 8 bits after the 24-bit sample. */
#define AUDIO_SAMPLE_MASK (0xFFFFFF00U)

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/***********************************************************************/
/* GLOBAL CONSTANTS                                                    */
/***********************************************************************/

/***********************************************************************/
/* LOCAL CONSTANTS                                                     */
/***********************************************************************/

/***********************************************************************/
/* GLOBAL VARIABLES                                                    */
/***********************************************************************/

/***********************************************************************/
/* LOCAL VARIABLES                                                     */
/***********************************************************************/

static audio_event_handler audio_EventHandler; /**< Set before the thread starts; only read afterwards. */

K_THREAD_STACK_DEFINE(audio_Stack, AUDIO_THREAD_STACK_SIZE);
K_MSGQ_DEFINE(audio_Commands, sizeof(enum audio_command), AUDIO_COMMAND_QUEUE_LENGTH, 4);

static struct k_thread audio_ThreadData;

/** Mono working buffer of the audio thread: left-aligned 24-bit samples with the low 8 bits cleared. */
static int32_t audio_MonoSamples[I2S_FRAMES_PER_BLOCK];

/***********************************************************************/
/* LOCAL FUNCTION PROTOTYPES                                           */
/***********************************************************************/

/**
 * @brief Wait for commands and run the block loop while started.
 *
 * @param[in] first Unused.
 * @param[in] second Unused.
 * @param[in] third Unused.
 */
static void audio_thread(void *first, void *second, void *third);

/**
 * @brief Start both links, run the block loop until Stop or a fault, then stop both links.
 */
static void audio_runStream(void);

/**
 * @brief Move one block from the microphone to the DAC: read, process, send.
 *
 * @return I2S_RESULT_OK, or the link that failed.
 */
static enum i2s_result audio_processBlock(void);

/**
 * @brief Check the command queue without waiting.
 *
 * @return True if Stop was requested.
 */
static bool audio_isStopRequested(void);

/**
 * @brief Catalogue code of a failed link.
 *
 * @param[in] result Result of an I2S operation.
 *
 * @return FEEDBACK_NONE for I2S_RESULT_OK, otherwise the code of the failed link.
 */
static enum feedback_code audio_getFaultCode(enum i2s_result result);

/***********************************************************************/
/* MACROS                                                              */
/***********************************************************************/

LOG_MODULE_REGISTER(audio, LOG_LEVEL_INF);

/***********************************************************************/
/* GLOBAL FUNCTIONS                                                    */
/***********************************************************************/

enum feedback_code audio_init(audio_event_handler eventHandler)
{
    audio_EventHandler = eventHandler;

    enum feedback_code result = audio_getFaultCode(i2s_initialize());

    (void)k_thread_create(&audio_ThreadData,
                          audio_Stack,
                          K_THREAD_STACK_SIZEOF(audio_Stack),
                          audio_thread,
                          NULL,
                          NULL,
                          NULL,
                          AUDIO_THREAD_PRIORITY,
                          0,
                          K_FOREVER);

    (void)k_thread_name_set(&audio_ThreadData, "audio");
    k_thread_start(&audio_ThreadData);

    return result;
}

int audio_postCommand(enum audio_command command)
{
    return k_msgq_put(&audio_Commands, &command, K_NO_WAIT);
}

/***********************************************************************/
/* LOCAL FUNCTIONS                                                     */
/***********************************************************************/

static void audio_thread(void *first, void *second, void *third)
{
    ARG_UNUSED(first);
    ARG_UNUSED(second);
    ARG_UNUSED(third);

    for(;;)
    {
        enum audio_command command = AUDIO_COMMAND_STOP;

        (void)k_msgq_get(&audio_Commands, &command, K_FOREVER);

        if(command == AUDIO_COMMAND_START)
        {
            audio_runStream();
        }
    }
}

static void audio_runStream(void)
{
    enum i2s_result result = i2s_start();
    bool isStopRequested = false;

    if(result == I2S_RESULT_OK)
    {
        audio_EventHandler(AUDIO_EVENT_STARTED, FEEDBACK_NONE);

        while((result == I2S_RESULT_OK) && !isStopRequested)
        {
            result = audio_processBlock();

            if(result == I2S_RESULT_OK)
            {
                isStopRequested = audio_isStopRequested();
            }
        }

        (void)i2s_stop();
    }

    if(result == I2S_RESULT_OK)
    {
        audio_EventHandler(AUDIO_EVENT_STOPPED, FEEDBACK_NONE);
    }
    else
    {
        audio_EventHandler(AUDIO_EVENT_FAULT, audio_getFaultCode(result));
    }
}

static enum i2s_result audio_processBlock(void)
{
    int32_t *receivedFrames = NULL;
    int32_t *transmitFrames = NULL;
    uint32_t frame = 0U;
    enum i2s_result result = i2s_receiveBlock(&receivedFrames);

    if(result == I2S_RESULT_OK)
    {
        for(frame = 0U; frame < I2S_FRAMES_PER_BLOCK; frame++)
        {
            uint32_t leftSlot = (uint32_t)receivedFrames[frame * I2S_SLOTS_PER_FRAME];

            audio_MonoSamples[frame] = (int32_t)(leftSlot & AUDIO_SAMPLE_MASK);
        }

        result = i2s_releaseReceivedBlock(receivedFrames);
    }

    if(result == I2S_RESULT_OK)
    {
        result = i2s_allocateTransmitBlock(&transmitFrames);
    }

    if(result == I2S_RESULT_OK)
    {
        for(frame = 0U; frame < I2S_FRAMES_PER_BLOCK; frame++)
        {
            transmitFrames[frame * I2S_SLOTS_PER_FRAME] = audio_MonoSamples[frame];
            transmitFrames[(frame * I2S_SLOTS_PER_FRAME) + 1U] = audio_MonoSamples[frame];
        }

        result = i2s_transmitBlock(transmitFrames);
    }

    return result;
}

static bool audio_isStopRequested(void)
{
    bool isStopRequested = false;
    enum audio_command command = AUDIO_COMMAND_START;

    while(!isStopRequested && (k_msgq_get(&audio_Commands, &command, K_NO_WAIT) == 0))
    {
        isStopRequested = (command == AUDIO_COMMAND_STOP);
    }

    return isStopRequested;
}

static enum feedback_code audio_getFaultCode(enum i2s_result result)
{
    enum feedback_code code = FEEDBACK_NONE;

    switch(result)
    {
    case I2S_RESULT_MICROPHONE_FAILURE:
        code = FEEDBACK_MICROPHONE_FAILURE;
        break;

    case I2S_RESULT_OUTPUT_FAILURE:
        code = FEEDBACK_AUDIO_OUTPUT_FAILURE;
        break;

    default:
        code = FEEDBACK_NONE;
        break;
    }

    return code;
}

/** @} */
