/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L2_AUDIO
 * @{
 * @file
 * Block processing of the audio path. Private to L2_AUDIO; pure C without driver access.
 */

#ifndef L2_AUDIO_PROCESSING_H
#define L2_AUDIO_PROCESSING_H

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include <stdint.h>

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

/** The INMP441 does not drive the 8 bits after the 24-bit sample. */
#define AUDIO_SAMPLE_MASK (0xFFFFFF00U)

#define AUDIO_FULL_VOLUME_PERCENT (100U)

/***********************************************************************/
/* GLOBAL FUNCTION PROTOTYPES                                          */
/***********************************************************************/

/**
 * @brief Scale samples linearly by a volume, saturating at the 24-bit limits.
 *
 * The samples are 24-bit values left-aligned in 32 bits. 100 % leaves them unchanged.
 *
 * @param[in,out] samples Mono working samples.
 * @param[in] sampleCount Number of samples.
 * @param[in] volumePercent Volume, 0 to 100; higher values count as 100.
 */
void audio_applyVolume(int32_t *samples, uint32_t sampleCount, uint32_t volumePercent);

#endif /* L2_AUDIO_PROCESSING_H */

/** @} */
