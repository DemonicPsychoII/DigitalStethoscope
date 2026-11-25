/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L2_AUDIO
 * @{
 * @file
 * Implementation of the L2_AUDIO module.
 */

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include "audio.h"

#include <stdbool.h>
#include <stdint.h>

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

#include "audio_processing.h"
#include "i2s.h"

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

#define AUDIO_THREAD_STACK_SIZE (2048) /**< Stack size of the audio thread. */
#define AUDIO_THREAD_PRIORITY   (1)    /**< Highest application thread priority. */

#define AUDIO_COMMAND_QUEUE_LENGTH (4)

/** One debug report per second: 250 blocks of 4 ms. */
#define AUDIO_PROCESSING_REPORT_BLOCKS (250U)

/** Volume until L2_CONTROL passes the first reading: silent output. */
#define AUDIO_SAFE_VOLUME_PERCENT (0)

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/** Block processing times of one stream, in CPU cycles. */
struct audio_processing_time
{
    uint32_t processedBlocks;   /**< Blocks since Start. */
    uint32_t longestSinceStart; /**< Longest block since Start. */
    uint32_t blocksInReport;    /**< Blocks since the last report. */
    uint32_t longestInReport;   /**< Longest block since the last report. */
    uint64_t totalInReport;     /**< Sum since the last report; 64 bits because 250 slow blocks can exceed 32 bits of cycles. */
};

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

/** Set at boot before the thread starts, afterwards only by the audio thread; a fault lasts until the device restarts. */
static bool audio_HasFault;

K_THREAD_STACK_DEFINE(audio_Stack, AUDIO_THREAD_STACK_SIZE);
K_MSGQ_DEFINE(audio_Commands, sizeof(enum audio_command), AUDIO_COMMAND_QUEUE_LENGTH, 4);

static struct k_thread audio_ThreadData;

/** Written by L2_CONTROL, read by the audio thread once per block; atomic, so neither side waits. */
static atomic_t audio_VolumePercent = ATOMIC_INIT(AUDIO_SAFE_VOLUME_PERCENT);

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
 * @brief Start both links, run the block loop until Stop or a fault, then stop or drop both links.
 *
 * @return I2S_RESULT_OK after a normal Stop, otherwise the link that failed.
 */
static enum i2s_result audio_runStream(void);

/**
 * @brief Move one block from the microphone to the DAC: read, apply the volume, send.
 *
 * @param[out] processingCycles CPU cycles from the received block to the queued TX block; the wait for the block is not included.
 *
 * @return I2S_RESULT_OK, or the link that failed.
 */
static enum i2s_result audio_processBlock(uint32_t *processingCycles);

/**
 * @brief Add the processing time of one block and log a debug report every AUDIO_PROCESSING_REPORT_BLOCKS blocks.
 *
 * @param[in,out] processingTime Processing times of the current stream.
 * @param[in] processingCycles Processing time of the block, in CPU cycles.
 */
static void audio_recordProcessingTime(struct audio_processing_time *processingTime, uint32_t processingCycles);

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

LOG_MODULE_REGISTER(audio, LOG_LEVEL_DBG);

/***********************************************************************/
/* GLOBAL FUNCTIONS                                                    */
/***********************************************************************/

enum feedback_code audio_init(audio_event_handler eventHandler)
{
    audio_EventHandler = eventHandler;

    enum feedback_code result = audio_getFaultCode(i2s_initialize());

    audio_HasFault = (result != FEEDBACK_NONE);

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

void audio_setVolume(uint8_t volumePercent)
{
    uint32_t clampedPercent = MIN((uint32_t)volumePercent, AUDIO_FULL_VOLUME_PERCENT);

    (void)atomic_set(&audio_VolumePercent, (atomic_val_t)clampedPercent);
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

        if((command == AUDIO_COMMAND_START) && !audio_HasFault)
        {
            audio_HasFault = (audio_runStream() != I2S_RESULT_OK);
        }
    }
}

static enum i2s_result audio_runStream(void)
{
    enum i2s_result result = i2s_start();
    bool isStopRequested = false;
    struct audio_processing_time processingTime = {0};
    uint32_t processingCycles = 0U;

    if(result == I2S_RESULT_OK)
    {
        audio_EventHandler(AUDIO_EVENT_STARTED, FEEDBACK_NONE);

        while((result == I2S_RESULT_OK) && !isStopRequested)
        {
            result = audio_processBlock(&processingCycles);

            if(result == I2S_RESULT_OK)
            {
                audio_recordProcessingTime(&processingTime, processingCycles);
                isStopRequested = audio_isStopRequested();
            }
        }

        if(result == I2S_RESULT_OK)
        {
            result = i2s_stop();
        }

        if(result != I2S_RESULT_OK)
        {
            (void)i2s_abort();
        }

        LOG_DBG("Stream ended after %u blocks; longest block processing %u us",
                processingTime.processedBlocks,
                k_cyc_to_us_ceil32(processingTime.longestSinceStart));
    }

    if(result == I2S_RESULT_OK)
    {
        audio_EventHandler(AUDIO_EVENT_STOPPED, FEEDBACK_NONE);
    }
    else
    {
        audio_EventHandler(AUDIO_EVENT_FAULT, audio_getFaultCode(result));
    }

    return result;
}

static enum i2s_result audio_processBlock(uint32_t *processingCycles)
{
    int32_t *receivedFrames = NULL;
    int32_t *transmitFrames = NULL;
    uint32_t frame = 0U;
    uint32_t startCycle = 0U;
    enum i2s_result result = i2s_receiveBlock(&receivedFrames);

    if(result == I2S_RESULT_OK)
    {
        startCycle = k_cycle_get_32();

        for(frame = 0U; frame < I2S_FRAMES_PER_BLOCK; frame++)
        {
            uint32_t leftSlot = (uint32_t)receivedFrames[frame * I2S_SLOTS_PER_FRAME];

            audio_MonoSamples[frame] = (int32_t)(leftSlot & AUDIO_SAMPLE_MASK);
        }

        result = i2s_releaseReceivedBlock(receivedFrames);
    }

    if(result == I2S_RESULT_OK)
    {
        audio_applyVolume(audio_MonoSamples, I2S_FRAMES_PER_BLOCK, (uint32_t)atomic_get(&audio_VolumePercent));

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

    *processingCycles = k_cycle_get_32() - startCycle;

    return result;
}

static void audio_recordProcessingTime(struct audio_processing_time *processingTime, uint32_t processingCycles)
{
    processingTime->processedBlocks++;
    processingTime->blocksInReport++;
    processingTime->totalInReport += processingCycles;
    processingTime->longestInReport = MAX(processingTime->longestInReport, processingCycles);
    processingTime->longestSinceStart = MAX(processingTime->longestSinceStart, processingCycles);

    if(processingTime->blocksInReport >= AUDIO_PROCESSING_REPORT_BLOCKS)
    {
        uint32_t meanCycles = (uint32_t)(processingTime->totalInReport / processingTime->blocksInReport);

        LOG_DBG("Block processing over %u blocks: longest %u us, mean %u us; longest since Start %u us",
                processingTime->blocksInReport,
                k_cyc_to_us_ceil32(processingTime->longestInReport),
                k_cyc_to_us_ceil32(meanCycles),
                k_cyc_to_us_ceil32(processingTime->longestSinceStart));

        processingTime->blocksInReport = 0U;
        processingTime->longestInReport = 0U;
        processingTime->totalInReport = 0U;
    }
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
