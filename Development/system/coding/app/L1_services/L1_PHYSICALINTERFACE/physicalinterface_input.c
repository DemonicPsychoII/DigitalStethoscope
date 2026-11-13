/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L1_PHYSICALINTERFACE
 * @{
 * @file
 * Implementation of the input decoding of the PHYSICALINTERFACE module.
 */

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include "physicalinterface_input.h"

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

#define PHYSICALINTERFACE_FULL_VOLUME_PERCENT 100

/***********************************************************************/
/* LOCAL FUNCTION PROTOTYPES                                           */
/***********************************************************************/

/**
 * @brief Compare two switch samples.
 *
 * @param[in] first First sample.
 * @param[in] second Second sample.
 *
 * @return True if both have the same validity and filter.
 */
static bool physicalinterface_isSameSwitchSample(struct physicalinterface_switch_sample first, struct physicalinterface_switch_sample second);

/***********************************************************************/
/* GLOBAL FUNCTIONS                                                    */
/***********************************************************************/

struct physicalinterface_switch_sample physicalinterface_decodeSwitch(int rawContactLevel, int murmurContactLevel, int bpmContactLevel)
{
    struct physicalinterface_switch_sample sample = {.isValid = false, .filter = PHYSICALINTERFACE_SAFE_LISTENING_FILTER};

    if(rawContactLevel == 1)
    {
        sample.isValid = true;
        sample.filter = PHYSICALINTERFACE_LISTENING_FILTER_RAW;
    }
    else if(rawContactLevel == 0)
    {
        if((murmurContactLevel == 1) && (bpmContactLevel == 0))
        {
            sample.isValid = true;
            sample.filter = PHYSICALINTERFACE_LISTENING_FILTER_MURMUR;
        }
        else if((bpmContactLevel == 1) && (murmurContactLevel == 0))
        {
            sample.isValid = true;
            sample.filter = PHYSICALINTERFACE_LISTENING_FILTER_BPM;
        }
        else
        {
            sample.isValid = false;
        }
    }
    else
    {
        sample.isValid = false;
    }

    return sample;
}

void physicalinterface_resetSwitchDebounce(struct physicalinterface_switch_debounce *debounce)
{
    const struct physicalinterface_switch_sample safeSample = {.isValid = false, .filter = PHYSICALINTERFACE_SAFE_LISTENING_FILTER};

    debounce->stable = safeSample;
    debounce->candidate = safeSample;
    debounce->candidateSinceMilliseconds = 0;
    debounce->isStableReported = false;
    debounce->hasCandidate = false;
}

bool physicalinterface_debounceSwitch(struct physicalinterface_switch_debounce *debounce, struct physicalinterface_switch_sample sample, int64_t nowMilliseconds)
{
    bool isTransition = false;

    if(!debounce->hasCandidate || !physicalinterface_isSameSwitchSample(sample, debounce->candidate))
    {
        debounce->candidate = sample;
        debounce->candidateSinceMilliseconds = nowMilliseconds;
        debounce->hasCandidate = true;
    }

    bool isCandidateStable = (nowMilliseconds - debounce->candidateSinceMilliseconds) >= PHYSICALINTERFACE_DEBOUNCE_MILLISECONDS;
    bool isCandidateNew = !debounce->isStableReported || !physicalinterface_isSameSwitchSample(debounce->candidate, debounce->stable);

    if(isCandidateStable && isCandidateNew)
    {
        debounce->stable = debounce->candidate;
        debounce->isStableReported = true;
        isTransition = true;
    }

    return isTransition;
}

uint8_t physicalinterface_volumePercentFromMillivolts(int32_t millivolts)
{
    int32_t clampedMillivolts = millivolts;

    if(clampedMillivolts < 0)
    {
        clampedMillivolts = 0;
    }
    else if(clampedMillivolts > PHYSICALINTERFACE_POTENTIOMETER_FULL_SCALE_MILLIVOLTS)
    {
        clampedMillivolts = PHYSICALINTERFACE_POTENTIOMETER_FULL_SCALE_MILLIVOLTS;
    }
    else
    {
        /* Already inside the range. */
    }

    int32_t percent = (clampedMillivolts * PHYSICALINTERFACE_FULL_VOLUME_PERCENT) / PHYSICALINTERFACE_POTENTIOMETER_FULL_SCALE_MILLIVOLTS;

    return (uint8_t)percent;
}

void physicalinterface_resetVolumeTracker(struct physicalinterface_volume_tracker *tracker)
{
    tracker->reportedPercent = PHYSICALINTERFACE_SAFE_VOLUME_PERCENT;
    tracker->reportedStatus = PHYSICALINTERFACE_INPUT_FAILED;
    tracker->isReported = false;
}

bool physicalinterface_trackVolume(struct physicalinterface_volume_tracker *tracker, enum physicalinterface_input_status status, int32_t millivolts)
{
    uint8_t percent = (status == PHYSICALINTERFACE_INPUT_VALID) ? physicalinterface_volumePercentFromMillivolts(millivolts) : PHYSICALINTERFACE_SAFE_VOLUME_PERCENT;
    bool isReportNeeded = !tracker->isReported || (status != tracker->reportedStatus);

    if(!isReportNeeded && (percent != tracker->reportedPercent))
    {
        int32_t changePercent = (int32_t)percent - (int32_t)tracker->reportedPercent;
        bool isEndReached = (percent == 0U) || (percent == PHYSICALINTERFACE_FULL_VOLUME_PERCENT);

        isReportNeeded = isEndReached || (changePercent >= PHYSICALINTERFACE_VOLUME_HYSTERESIS_PERCENT) || (changePercent <= -PHYSICALINTERFACE_VOLUME_HYSTERESIS_PERCENT);
    }

    if(isReportNeeded)
    {
        tracker->reportedPercent = percent;
        tracker->reportedStatus = status;
        tracker->isReported = true;
    }

    return isReportNeeded;
}

/***********************************************************************/
/* LOCAL FUNCTIONS                                                     */
/***********************************************************************/

static bool physicalinterface_isSameSwitchSample(struct physicalinterface_switch_sample first, struct physicalinterface_switch_sample second)
{
    return (first.isValid == second.isValid) && (first.filter == second.filter);
}

/** @} */
