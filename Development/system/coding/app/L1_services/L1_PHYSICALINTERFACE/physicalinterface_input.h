/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L1_PHYSICALINTERFACE
 * @{
 * @file
 * Input decoding without driver access: Raw/Murmur/BPM switch decoding and
 * debouncing, and volume scaling with change detection. Private to
 * L1_PHYSICALINTERFACE; pure C, so the host tests compile it unchanged.
 */

#ifndef L1_PHYSICALINTERFACE_INPUT_H
#define L1_PHYSICALINTERFACE_INPUT_H

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include <stdbool.h>
#include <stdint.h>

#include "physicalinterface.h"

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

#define PHYSICALINTERFACE_DEBOUNCE_MILLISECONDS 30 /**< P10 candidate debounce; covers the 10 to 21 ms J8 gaps measured on 10 November 2026. */

/** Highest wiper reading at the 3V3 end of J7 on the Eval carrier, 10 November 2026; the gap to 3300 mV is not explained. */
#define PHYSICALINTERFACE_POTENTIOMETER_FULL_SCALE_MILLIVOLTS 3083

/** Candidate step a reading must move before it is reported; ADC noise of a fitted J7 is not yet measured. */
#define PHYSICALINTERFACE_VOLUME_HYSTERESIS_PERCENT 2

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/** One reading of the listening-filter switch. */
struct physicalinterface_switch_sample
{
    bool isValid;                                   /**< Exactly one position was recognized. */
    enum physicalinterface_listening_filter filter; /**< Recognized position; the safe filter when not valid. */
};

/** Debounce state of the listening-filter switch. */
struct physicalinterface_switch_debounce
{
    struct physicalinterface_switch_sample stable;    /**< Last reported reading. */
    struct physicalinterface_switch_sample candidate; /**< Reading that is waiting to become stable. */
    int64_t candidateSinceMilliseconds;               /**< Uptime of the first sample of the candidate. */
    bool isStableReported;                            /**< A stable reading has been reported since start. */
    bool hasCandidate;                                /**< At least one sample has been taken. */
};

/** Last reported volume. */
struct physicalinterface_volume_tracker
{
    uint8_t reportedPercent;
    enum physicalinterface_input_status reportedStatus;
    bool isReported; /**< A volume has been reported since start. */
};

/***********************************************************************/
/* GLOBAL FUNCTION PROTOTYPES                                          */
/***********************************************************************/

/**
 * @brief Decode the switch position from the active-low contact levels.
 *
 * The fitted J8 has its common contact on the GPIO18 pad and its throws on GND,
 * GPIO21 and GPIO38. Raw grounds GPIO18. Otherwise the caller drives GPIO18 low
 * and reads which of GPIO21 and GPIO38 follows. With the common on GND, as the
 * footprint expects, the same decoding holds.
 *
 * Levels are logical: 1 means the contact reads low (active), 0 means it reads
 * high, and a negative value is a read or drive error.
 *
 * @param[in] rawContactLevel GPIO18 with only its pull-up.
 * @param[in] murmurContactLevel GPIO21 while GPIO18 is driven low; ignored unless rawContactLevel is 0.
 * @param[in] bpmContactLevel GPIO38 while GPIO18 is driven low; ignored unless rawContactLevel is 0.
 *
 * @return Valid sample for exactly one recognized position, otherwise an invalid sample with the safe filter.
 */
struct physicalinterface_switch_sample physicalinterface_decodeSwitch(int rawContactLevel, int murmurContactLevel, int bpmContactLevel);

/**
 * @brief Reset the switch debounce state; the first stable reading is then reported.
 *
 * @param[out] debounce Debounce state.
 */
void physicalinterface_resetSwitchDebounce(struct physicalinterface_switch_debounce *debounce);

/**
 * @brief Feed one switch sample and tell whether a stable transition happened.
 *
 * A reading becomes stable once every sample for PHYSICALINTERFACE_DEBOUNCE_MILLISECONDS
 * has matched it. Each stable transition is reported once, including the first
 * stable reading after the reset; debounce->stable then holds the new reading.
 *
 * @param[in,out] debounce Debounce state.
 * @param[in] sample Decoded sample.
 * @param[in] nowMilliseconds Uptime of the sample; must not decrease between calls.
 *
 * @return True if debounce->stable changed and must be reported.
 */
bool physicalinterface_debounceSwitch(struct physicalinterface_switch_debounce *debounce, struct physicalinterface_switch_sample sample, int64_t nowMilliseconds);

/**
 * @brief Scale a wiper voltage to a volume.
 *
 * @param[in] millivolts Wiper voltage.
 *
 * @return Volume in percent, clamped to 0 to 100; full scale at PHYSICALINTERFACE_POTENTIOMETER_FULL_SCALE_MILLIVOLTS.
 */
uint8_t physicalinterface_volumePercentFromMillivolts(int32_t millivolts);

/**
 * @brief Reset the volume tracker; the next reading is then reported.
 *
 * @param[out] tracker Volume tracker.
 */
void physicalinterface_resetVolumeTracker(struct physicalinterface_volume_tracker *tracker);

/**
 * @brief Feed one volume reading and tell whether it must be reported.
 *
 * A reading is reported when the status changes, when the volume moves by at
 * least PHYSICALINTERFACE_VOLUME_HYSTERESIS_PERCENT, or when it reaches 0 % or
 * 100 %, so that both ends of the range are always reached. Readings that are
 * not valid carry PHYSICALINTERFACE_SAFE_VOLUME_PERCENT.
 *
 * @param[in,out] tracker Volume tracker; holds the reading to report when true is returned.
 * @param[in] status Status of the reading.
 * @param[in] millivolts Wiper voltage; used only for a valid reading.
 *
 * @return True if the reading must be reported.
 */
bool physicalinterface_trackVolume(struct physicalinterface_volume_tracker *tracker, enum physicalinterface_input_status status, int32_t millivolts);

#endif /* L1_PHYSICALINTERFACE_INPUT_H */

/** @} */
