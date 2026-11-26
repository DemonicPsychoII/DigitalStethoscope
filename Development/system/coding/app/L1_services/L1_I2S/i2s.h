/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @defgroup L1_I2S I2S
 * @{
 * @file
 * Adapter over the Zephyr I2S drivers for microphone RX and DAC TX.
 *
 * Owns both links and their block pools. Only the audio thread calls the
 * stream functions; i2s_initialize() runs once at boot before that thread starts.
 *
 * P01 is defined in design/AUDIO/parameters.md, P11 in design/cross-module.md.
 */

#ifndef L1_I2S_H
#define L1_I2S_H

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include <stdint.h>

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

#define I2S_SAMPLE_RATE_HZ   16000 /**< P01: both links. */
#define I2S_FRAMES_PER_BLOCK 64    /**< P01: one block is 4 ms. */
#define I2S_SLOTS_PER_FRAME  2     /**< The driver accepts only two channels. */

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/** Result of an I2S operation; the failure values name the failed link. */
enum i2s_result
{
    I2S_RESULT_OK,
    I2S_RESULT_MICROPHONE_FAILURE, /**< Microphone link; catalogue MICROPHONE_FAILURE. */
    I2S_RESULT_OUTPUT_FAILURE,     /**< DAC link; catalogue AUDIO_OUTPUT_FAILURE. */
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
 * @brief Check that both I2S devices are ready and configure both links.
 *
 * No stream runs afterwards.
 *
 * @return I2S_RESULT_OK, or the link that is not ready or rejected its configuration.
 */
enum i2s_result i2s_initialize(void);

/**
 * @brief Start both links while they are stopped.
 *
 * Configures both links again, queues 4 silent TX blocks, then starts RX and TX.
 * On failure both links are dropped as i2s_abort() does.
 *
 * @return I2S_RESULT_OK, or the link that failed.
 */
enum i2s_result i2s_start(void);

/**
 * @brief Stop both running links for a normal Stop and return every block the driver holds to its pool.
 *
 * Triggers STOP on both links, waits two block periods so the block in DMA
 * completes, then triggers DROP on both. Blocks the thread for about 8 ms.
 * A link that rejects STOP, for example in the driver's error state, ends the
 * sequence at once, without the wait. The caller must not hold a block.
 *
 * @return I2S_RESULT_OK, or the link that rejected STOP or DROP or whose pool still has blocks in use; the caller then calls i2s_abort().
 */
enum i2s_result i2s_stop(void);

/**
 * @brief Drop both links at once after an audio fault, without STOP or a wait.
 *
 * Blocks the driver held at that moment may stay in use until the device
 * restarts. Harmless when repeated.
 *
 * @return I2S_RESULT_OK.
 */
enum i2s_result i2s_abort(void);

/**
 * @brief Wait for the next completed RX block and lend it to the caller.
 *
 * Waits at most the receive wait (P11). The block holds
 * I2S_FRAMES_PER_BLOCK frames of I2S_SLOTS_PER_FRAME 32-bit slots.
 *
 * @param[out] receivedFrames The lent block; NULL on failure. Must not be NULL.
 *
 * @return I2S_RESULT_OK, or I2S_RESULT_MICROPHONE_FAILURE on timeout or driver error.
 */
enum i2s_result i2s_receiveBlock(int32_t **receivedFrames);

/**
 * @brief Return a block lent by i2s_receiveBlock() to the RX pool.
 *
 * @param[in] receivedFrames The lent block.
 *
 * @return I2S_RESULT_OK.
 */
enum i2s_result i2s_releaseReceivedBlock(int32_t *receivedFrames);

/**
 * @brief Wait for a free TX block.
 *
 * Waits at most the TX-block wait (P11). The caller fills all
 * I2S_FRAMES_PER_BLOCK frames and passes the block to i2s_transmitBlock().
 *
 * @param[out] transmitFrames The free block; NULL on failure. Must not be NULL.
 *
 * @return I2S_RESULT_OK, or I2S_RESULT_OUTPUT_FAILURE on timeout.
 */
enum i2s_result i2s_allocateTransmitBlock(int32_t **transmitFrames);

/**
 * @brief Queue a filled TX block for the DAC; the driver owns it afterwards.
 *
 * On failure the block returns to the TX pool.
 *
 * @param[in] transmitFrames A block from i2s_allocateTransmitBlock().
 *
 * @return I2S_RESULT_OK, or I2S_RESULT_OUTPUT_FAILURE.
 */
enum i2s_result i2s_transmitBlock(int32_t *transmitFrames);

/**
 * @brief Read the pool use for monitoring.
 *
 * Read the TX value before allocating the next TX block; otherwise it also
 * counts the block the caller holds.
 *
 * @param[out] receivePoolHighestUse Highest number of RX pool blocks in use since boot. Must not be NULL.
 * @param[out] transmitBlocksInDriver TX pool blocks currently in use. Must not be NULL.
 *
 * @return I2S_RESULT_OK.
 */
enum i2s_result i2s_getPoolUse(uint32_t *receivePoolHighestUse, uint32_t *transmitBlocksInDriver);

#endif /* L1_I2S_H */

/** @} */
