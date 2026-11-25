/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L2_AUDIO
 * @{
 * @file
 * Implementation of the block processing of the L2_AUDIO module.
 */

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include "audio_processing.h"

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

/** The gain is a fixed-point factor, so each sample needs no division by 100. */
#define AUDIO_GAIN_ONE (65536)

/** One step of the 24-bit value in the left-aligned 32-bit sample. */
#define AUDIO_SAMPLE_STEP (256)

#define AUDIO_SAMPLE_MAXIMUM (8388607)  /**< Largest 24-bit value. */
#define AUDIO_SAMPLE_MINIMUM (-8388608) /**< Smallest 24-bit value. */

/***********************************************************************/
/* GLOBAL FUNCTIONS                                                    */
/***********************************************************************/

void audio_applyVolume(int32_t *samples, uint32_t sampleCount, uint32_t volumePercent)
{
    uint32_t clampedPercent = ((volumePercent > AUDIO_FULL_VOLUME_PERCENT) ? AUDIO_FULL_VOLUME_PERCENT : volumePercent);
    int64_t gain = (((int64_t)clampedPercent * AUDIO_GAIN_ONE) / (int64_t)AUDIO_FULL_VOLUME_PERCENT);

    for(uint32_t index = 0U; index < sampleCount; index++)
    {
        /* Scaling the 24-bit value truncates positive and negative samples alike toward zero. */
        int64_t value = ((int64_t)samples[index] / AUDIO_SAMPLE_STEP);
        int64_t scaled = ((value * gain) / AUDIO_GAIN_ONE);

        if(scaled > AUDIO_SAMPLE_MAXIMUM)
        {
            scaled = AUDIO_SAMPLE_MAXIMUM;
        }
        else if(scaled < AUDIO_SAMPLE_MINIMUM)
        {
            scaled = AUDIO_SAMPLE_MINIMUM;
        }
        else
        {
            /* Inside the 24-bit range. */
        }

        samples[index] = (int32_t)(scaled * AUDIO_SAMPLE_STEP);
    }
}

/** @} */
