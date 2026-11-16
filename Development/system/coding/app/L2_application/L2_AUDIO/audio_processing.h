/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L2_AUDIO
 * @{
 * @file
 * Block processing of the audio path without driver access: linear volume
 * with saturation on the mono working samples. Private to L2_AUDIO; pure C,
 * so the host tests compile it unchanged.
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
 * The samples are 24-bit values left-aligned in 32 bits; the result keeps that
 * format with the low 8 bits cleared. 100 % leaves every sample unchanged and
 * 0 % silences it.
 *
 * @param[in,out] samples Mono working samples.
 * @param[in] sampleCount Number of samples.
 * @param[in] volumePercent Volume, 0 to 100; higher values count as 100.
 */
void audio_applyVolume(int32_t *samples, uint32_t sampleCount, uint32_t volumePercent);

#endif /* L2_AUDIO_PROCESSING_H */

/** @} */
