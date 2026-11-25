/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L1_I2S
 * @{
 * @file
 * Implementation of the L1_I2S module.
 */

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include "i2s.h"

#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/i2s.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/util.h>

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

#define I2S_WORD_SIZE_BITS   32 /**< A 24-bit sample needs a 32-bit slot; equal word sizes keep both dividers equal. */
#define I2S_BLOCK_SIZE_BYTES (I2S_FRAMES_PER_BLOCK * I2S_SLOTS_PER_FRAME * sizeof(int32_t))
#define I2S_BLOCK_PERIOD_MS  ((I2S_FRAMES_PER_BLOCK * 1000) / I2S_SAMPLE_RATE_HZ)
#define I2S_BLOCK_WAIT_MS    (5 * I2S_BLOCK_PERIOD_MS) /**< P11: receive and TX-block waits. */
#define I2S_STOP_WAIT_MS     (2 * I2S_BLOCK_PERIOD_MS) /**< The block in DMA completes within one block period. */

#define I2S_POOL_BLOCKS   5 /**< P11, per pool. */
#define I2S_PRIMED_BLOCKS 4 /**< Silent TX blocks queued before TX starts; sets the 16 ms transport delay. */

#define I2S_POOL_ALIGNMENT_BYTES 4

#define I2S_MICROPHONE_NODE DT_ALIAS(i2s_microphone)
#define I2S_DAC_NODE        DT_ALIAS(i2s_dac)

/* RX pool: one block in DMA, the driver queue, one block lent to the audio thread. */
BUILD_ASSERT(CONFIG_I2S_ESP32_RX_BLOCK_COUNT == (I2S_POOL_BLOCKS - 2), "RX driver queue must leave one pool block for DMA and one for the audio thread");
BUILD_ASSERT(CONFIG_I2S_ESP32_TX_BLOCK_COUNT >= I2S_PRIMED_BLOCKS, "The primed blocks wait in the TX driver queue before TX starts");
/* Without it, k_mem_slab_max_used_get() returns 0 instead of failing. */
BUILD_ASSERT(IS_ENABLED(CONFIG_MEM_SLAB_TRACE_MAX_UTILIZATION), "Pool monitoring needs CONFIG_MEM_SLAB_TRACE_MAX_UTILIZATION");

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/***********************************************************************/
/* GLOBAL CONSTANTS                                                    */
/***********************************************************************/

/***********************************************************************/
/* LOCAL CONSTANTS                                                     */
/***********************************************************************/

static const struct device *const i2s_MicrophoneDevice = DEVICE_DT_GET(I2S_MICROPHONE_NODE);

static const struct device *const i2s_DACDevice = DEVICE_DT_GET(I2S_DAC_NODE);

/***********************************************************************/
/* GLOBAL VARIABLES                                                    */
/***********************************************************************/

/***********************************************************************/
/* LOCAL VARIABLES                                                     */
/***********************************************************************/

/* The pools must stay in internal DMA-capable RAM; do not move them to PSRAM. */
K_MEM_SLAB_DEFINE_STATIC(i2s_ReceivePool, I2S_BLOCK_SIZE_BYTES, I2S_POOL_BLOCKS, I2S_POOL_ALIGNMENT_BYTES);
K_MEM_SLAB_DEFINE_STATIC(i2s_TransmitPool, I2S_BLOCK_SIZE_BYTES, I2S_POOL_BLOCKS, I2S_POOL_ALIGNMENT_BYTES);

/*
 * Both links use the same word size, slot count and rate, so both controllers derive the same clock dividers.
 *
 * I2S_FMT_DATA_FORMAT_I2S shifts each 24-bit INMP441 sample one bit too far left on this link,
 * discarding the sign bit and wrapping loud samples. Left-justified with the inverted frame clock
 * keeps the left slot on WS low and samples one bit clock earlier, which aligns the sample.
 */
static const struct i2s_config i2s_ReceiveConfiguration = {
    .word_size = I2S_WORD_SIZE_BITS,
    .channels = I2S_SLOTS_PER_FRAME,
    .format = I2S_FMT_DATA_FORMAT_LEFT_JUSTIFIED | I2S_FMT_FRAME_CLK_INV,
    .options = I2S_OPT_FRAME_CLK_CONTROLLER | I2S_OPT_BIT_CLK_CONTROLLER,
    .frame_clk_freq = I2S_SAMPLE_RATE_HZ,
    .mem_slab = &i2s_ReceivePool,
    .block_size = I2S_BLOCK_SIZE_BYTES,
    .timeout = I2S_BLOCK_WAIT_MS,
};

static const struct i2s_config i2s_TransmitConfiguration = {
    .word_size = I2S_WORD_SIZE_BITS,
    .channels = I2S_SLOTS_PER_FRAME,
    .format = I2S_FMT_DATA_FORMAT_I2S,
    .options = I2S_OPT_FRAME_CLK_CONTROLLER | I2S_OPT_BIT_CLK_CONTROLLER,
    .frame_clk_freq = I2S_SAMPLE_RATE_HZ,
    .mem_slab = &i2s_TransmitPool,
    .block_size = I2S_BLOCK_SIZE_BYTES,
    .timeout = I2S_BLOCK_WAIT_MS,
};

/***********************************************************************/
/* LOCAL FUNCTION PROTOTYPES                                           */
/***********************************************************************/

/**
 * @brief Configure the microphone link for RX and the DAC link for TX.
 *
 * @return I2S_RESULT_OK, or the link that rejected its configuration.
 */
static enum i2s_result i2s_configureLinks(void);

/**
 * @brief Queue the silent TX blocks that are played while the first RX block fills.
 *
 * @return I2S_RESULT_OK, or I2S_RESULT_OUTPUT_FAILURE.
 */
static enum i2s_result i2s_primeTransmitQueue(void);

/**
 * @brief Name the failed link from one finding per link; the microphone link comes first.
 *
 * @param[in] microphoneFinding Non-zero if the microphone link failed.
 * @param[in] outputFinding Non-zero if the DAC link failed.
 *
 * @return I2S_RESULT_OK if both findings are 0, otherwise the failed link.
 */
static enum i2s_result i2s_getFailedLink(int microphoneFinding, int outputFinding);

/***********************************************************************/
/* MACROS                                                              */
/***********************************************************************/

LOG_MODULE_REGISTER(i2s, LOG_LEVEL_INF);

/***********************************************************************/
/* GLOBAL FUNCTIONS                                                    */
/***********************************************************************/

enum i2s_result i2s_initialize(void)
{
    const bool isMicrophoneReady = device_is_ready(i2s_MicrophoneDevice);
    enum i2s_result result = I2S_RESULT_OK;

    if(!isMicrophoneReady)
    {
        LOG_ERR("Microphone I2S device %s is not ready", i2s_MicrophoneDevice->name);
        result = I2S_RESULT_MICROPHONE_FAILURE;
    }
    else
    {
        const bool isDACReady = device_is_ready(i2s_DACDevice);

        if(!isDACReady)
        {
            LOG_ERR("DAC I2S device %s is not ready", i2s_DACDevice->name);
            result = I2S_RESULT_OUTPUT_FAILURE;
        }
        else
        {
            result = i2s_configureLinks();
        }
    }

    return result;
}

enum i2s_result i2s_start(void)
{
    enum i2s_result result = i2s_configureLinks();

    if(result == I2S_RESULT_OK)
    {
        result = i2s_primeTransmitQueue();
    }

    if(result == I2S_RESULT_OK)
    {
        int error = i2s_trigger(i2s_MicrophoneDevice, I2S_DIR_RX, I2S_TRIGGER_START);

        if(error != 0)
        {
            LOG_ERR("Microphone start failed: %d", error);
            result = I2S_RESULT_MICROPHONE_FAILURE;
        }
    }

    if(result == I2S_RESULT_OK)
    {
        int error = i2s_trigger(i2s_DACDevice, I2S_DIR_TX, I2S_TRIGGER_START);

        if(error != 0)
        {
            LOG_ERR("DAC start failed: %d", error);
            result = I2S_RESULT_OUTPUT_FAILURE;
        }
    }

    if(result != I2S_RESULT_OK)
    {
        (void)i2s_abort();
    }

    return result;
}

enum i2s_result i2s_stop(void)
{
    /* DROP alone would lose the block in DMA: the driver clears its pointer without freeing it. STOP lets it complete first. */
    int microphoneError = i2s_trigger(i2s_MicrophoneDevice, I2S_DIR_RX, I2S_TRIGGER_STOP);
    int outputError = i2s_trigger(i2s_DACDevice, I2S_DIR_TX, I2S_TRIGGER_STOP);
    enum i2s_result result = i2s_getFailedLink(microphoneError, outputError);

    if(result != I2S_RESULT_OK)
    {
        LOG_ERR("STOP rejected (microphone %d, DAC %d)", microphoneError, outputError);
    }
    else
    {
        k_msleep(I2S_STOP_WAIT_MS);

        microphoneError = i2s_trigger(i2s_MicrophoneDevice, I2S_DIR_RX, I2S_TRIGGER_DROP);
        outputError = i2s_trigger(i2s_DACDevice, I2S_DIR_TX, I2S_TRIGGER_DROP);
        result = i2s_getFailedLink(microphoneError, outputError);

        if(result != I2S_RESULT_OK)
        {
            LOG_ERR("DROP failed (microphone %d, DAC %d)", microphoneError, outputError);
        }
    }

    if(result == I2S_RESULT_OK)
    {
        uint32_t receiveBlocksInUse = k_mem_slab_num_used_get(&i2s_ReceivePool);
        uint32_t transmitBlocksInUse = k_mem_slab_num_used_get(&i2s_TransmitPool);

        result = i2s_getFailedLink((int)receiveBlocksInUse, (int)transmitBlocksInUse);

        if(result != I2S_RESULT_OK)
        {
            LOG_ERR("Blocks still in use after stop: RX %u, TX %u", receiveBlocksInUse, transmitBlocksInUse);
        }
    }

    return result;
}

enum i2s_result i2s_abort(void)
{
    int microphoneError = i2s_trigger(i2s_MicrophoneDevice, I2S_DIR_RX, I2S_TRIGGER_DROP);
    int outputError = i2s_trigger(i2s_DACDevice, I2S_DIR_TX, I2S_TRIGGER_DROP);

    if((microphoneError != 0) || (outputError != 0))
    {
        LOG_ERR("DROP failed (microphone %d, DAC %d)", microphoneError, outputError);
    }

    return I2S_RESULT_OK;
}

enum i2s_result i2s_receiveBlock(int32_t **receivedFrames)
{
    enum i2s_result result = I2S_RESULT_OK;
    void *block = NULL;
    size_t blockSize = 0U;
    int error = i2s_read(i2s_MicrophoneDevice, &block, &blockSize);

    if(error != 0)
    {
        LOG_ERR("Microphone read failed: %d", error);
        block = NULL;
        result = I2S_RESULT_MICROPHONE_FAILURE;
    }
    else if(blockSize != I2S_BLOCK_SIZE_BYTES)
    {
        LOG_ERR("Microphone block has %zu bytes instead of %zu", blockSize, I2S_BLOCK_SIZE_BYTES);
        k_mem_slab_free(&i2s_ReceivePool, block);
        block = NULL;
        result = I2S_RESULT_MICROPHONE_FAILURE;
    }
    else
    {
        result = I2S_RESULT_OK;
    }

    *receivedFrames = (int32_t *)block;

    return result;
}

enum i2s_result i2s_releaseReceivedBlock(int32_t *receivedFrames)
{
    k_mem_slab_free(&i2s_ReceivePool, receivedFrames);

    return I2S_RESULT_OK;
}

enum i2s_result i2s_allocateTransmitBlock(int32_t **transmitFrames)
{
    enum i2s_result result = I2S_RESULT_OK;
    void *block = NULL;
    int error = k_mem_slab_alloc(&i2s_TransmitPool, &block, K_MSEC(I2S_BLOCK_WAIT_MS));

    if(error != 0)
    {
        LOG_ERR("No free TX block: %d", error);
        block = NULL;
        result = I2S_RESULT_OUTPUT_FAILURE;
    }

    *transmitFrames = (int32_t *)block;

    return result;
}

enum i2s_result i2s_transmitBlock(int32_t *transmitFrames)
{
    enum i2s_result result = I2S_RESULT_OK;
    int error = i2s_write(i2s_DACDevice, transmitFrames, I2S_BLOCK_SIZE_BYTES);

    if(error != 0)
    {
        LOG_ERR("DAC write failed: %d", error);
        k_mem_slab_free(&i2s_TransmitPool, transmitFrames);
        result = I2S_RESULT_OUTPUT_FAILURE;
    }

    return result;
}

enum i2s_result i2s_getPoolUse(uint32_t *receivePoolHighestUse, uint32_t *transmitBlocksInDriver)
{
    *receivePoolHighestUse = k_mem_slab_max_used_get(&i2s_ReceivePool);
    *transmitBlocksInDriver = k_mem_slab_num_used_get(&i2s_TransmitPool);

    return I2S_RESULT_OK;
}

/***********************************************************************/
/* LOCAL FUNCTIONS                                                     */
/***********************************************************************/

static enum i2s_result i2s_configureLinks(void)
{
    enum i2s_result result = I2S_RESULT_OK;
    int error = i2s_configure(i2s_MicrophoneDevice, I2S_DIR_RX, &i2s_ReceiveConfiguration);

    if(error != 0)
    {
        LOG_ERR("Microphone configuration failed: %d", error);
        result = I2S_RESULT_MICROPHONE_FAILURE;
    }
    else
    {
        error = i2s_configure(i2s_DACDevice, I2S_DIR_TX, &i2s_TransmitConfiguration);

        if(error != 0)
        {
            LOG_ERR("DAC configuration failed: %d", error);
            result = I2S_RESULT_OUTPUT_FAILURE;
        }
    }

    return result;
}

static enum i2s_result i2s_primeTransmitQueue(void)
{
    enum i2s_result result = I2S_RESULT_OK;
    uint32_t primedBlocks = 0U;

    /* The driver accepts writes before TX START, and TX START fails with an empty queue. */
    while((result == I2S_RESULT_OK) && (primedBlocks < I2S_PRIMED_BLOCKS))
    {
        int32_t *transmitFrames = NULL;

        result = i2s_allocateTransmitBlock(&transmitFrames);

        if(result == I2S_RESULT_OK)
        {
            (void)memset(transmitFrames, 0, I2S_BLOCK_SIZE_BYTES);
            result = i2s_transmitBlock(transmitFrames);
        }

        primedBlocks++;
    }

    return result;
}

static enum i2s_result i2s_getFailedLink(int microphoneFinding, int outputFinding)
{
    enum i2s_result result = I2S_RESULT_OK;

    if(microphoneFinding != 0)
    {
        result = I2S_RESULT_MICROPHONE_FAILURE;
    }
    else if(outputFinding != 0)
    {
        result = I2S_RESULT_OUTPUT_FAILURE;
    }
    else
    {
        result = I2S_RESULT_OK;
    }

    return result;
}

/** @} */
