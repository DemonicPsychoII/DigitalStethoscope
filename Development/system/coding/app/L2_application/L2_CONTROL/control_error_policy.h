/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L2_CONTROL
 * @{
 * @file
 * Priority, clear rule and workflow admission of every catalogue error
 * (design/FEEDBACK/catalogue.md). Private to L2_CONTROL; pure C without kernel access.
 */

#ifndef L2_CONTROL_ERROR_POLICY_H
#define L2_CONTROL_ERROR_POLICY_H

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include <stdbool.h>
#include <stdint.h>

#include "feedback.h"

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/** Priority column of the catalogue. */
enum control_priority
{
    CONTROL_PRIORITY_INFORMATION, /**< Statuses. */
    CONTROL_PRIORITY_LOW,
    CONTROL_PRIORITY_MEDIUM,
};

/** "Cleared by" column of the catalogue. */
enum control_clear_rule
{
    CONTROL_CLEAR_RULE_NONE,        /**< Statuses: the next status replaces them. */
    CONTROL_CLEAR_RULE_SHORT_PRESS, /**< The first short press with the error shown acknowledges it. */
    CONTROL_CLEAR_RULE_RESTART,     /**< Stays until reset or power cycle; a short press does not clear it. */
};

/** Effect of a latched error on workflow admission. */
enum control_admission
{
    CONTROL_ADMISSION_NONE,            /**< Statuses. */
    CONTROL_ADMISSION_START_PERMITTED, /**< Wi-Fi, server-connection and registration errors: working audio and offline Start stay. */
    CONTROL_ADMISSION_START_BLOCKED,   /**< Other short-press errors: Start is blocked until acknowledged. */
    CONTROL_ADMISSION_HALTED,          /**< Other restart errors: every input is blocked; while audio runs, only after the manual Stop. */
    CONTROL_ADMISSION_HALTED_AT_ONCE,  /**< Audio errors: every input is blocked at once, also while audio runs. */
};

/** L2_CONTROL columns of one catalogue row. */
struct control_error_row
{
    enum control_priority priority;
    enum control_clear_rule clearRule;
    enum control_admission admission;
};

/** Latched errors in latch order; each code at most once. */
struct control_error_latch
{
    enum feedback_code errors[FEEDBACK_CODE_COUNT];
    uint32_t errorCount;
};

/** What a short press does. */
enum control_press_action
{
    CONTROL_PRESS_IGNORE,      /**< The device is halted: the press is dropped without indication. */
    CONTROL_PRESS_ACKNOWLEDGE, /**< The press acknowledges the error shown. */
    CONTROL_PRESS_REJECT,      /**< A latched error blocks Start: input rejected. */
    CONTROL_PRESS_WORKFLOW,    /**< The press goes to the workflow: Start or Stop. */
};

/***********************************************************************/
/* GLOBAL FUNCTION PROTOTYPES                                          */
/***********************************************************************/

/**
 * @brief L2_CONTROL columns of one catalogue row.
 *
 * @param[in] code Catalogue code below FEEDBACK_CODE_COUNT.
 *
 * @return Row of the code; statuses have priority Information, no clear rule and no admission effect.
 */
const struct control_error_row *control_getErrorRow(enum feedback_code code);

/**
 * @brief Tell whether a code is a catalogue error.
 *
 * @param[in] code Any value.
 *
 * @return True for an error row.
 */
bool control_isError(enum feedback_code code);

/**
 * @brief Clear the latch.
 *
 * @param[out] latch Error latch.
 */
void control_resetErrorLatch(struct control_error_latch *latch);

/**
 * @brief Latch an error.
 *
 * An error already latched keeps its place in the latch order.
 *
 * @param[in,out] latch Error latch.
 * @param[in] code Catalogue code.
 *
 * @return True if the error was not latched before; false for a repeat or a code that is no error.
 */
bool control_latchError(struct control_error_latch *latch, enum feedback_code code);

/**
 * @brief Error the lights show: the highest priority, then the first latched.
 *
 * @param[in] latch Error latch.
 *
 * @return Error code, or FEEDBACK_NONE if nothing is latched.
 */
enum feedback_code control_getShownError(const struct control_error_latch *latch);

/**
 * @brief Acknowledge the error shown if a short press clears it.
 *
 * @param[in,out] latch Error latch; the acknowledged error is removed.
 *
 * @return True if an error was acknowledged.
 */
bool control_acknowledgeShownError(struct control_error_latch *latch);

/**
 * @brief Tell whether a latched error has an admission effect.
 *
 * @param[in] latch Error latch.
 * @param[in] admission Admission effect to look for.
 *
 * @return True if at least one latched error has it.
 */
bool control_hasAdmission(const struct control_error_latch *latch, enum control_admission admission);

/**
 * @brief Tell whether the latched errors halt the device once audio has stopped.
 *
 * @param[in] latch Error latch.
 *
 * @return True if a restart error other than a Wi-Fi error, or an audio error, is latched.
 */
bool control_isHalted(const struct control_error_latch *latch);

/**
 * @brief Choose the code that the lights show.
 *
 * The error shown wins over the status. While the indication is deferred only
 * audio errors do.
 *
 * @param[in] latch Error latch.
 * @param[in] isIndicationDeferred True during startup and while audio is started.
 * @param[in] status Status of the current state.
 *
 * @return Code to show.
 */
enum feedback_code control_selectFeedback(const struct control_error_latch *latch, bool isIndicationDeferred, enum feedback_code status);

/**
 * @brief Decide what a short press does.
 *
 * @param[in] latch Error latch.
 * @param[in] isIndicationDeferred True during startup and while audio is started.
 *
 * @return Action for the press.
 */
enum control_press_action control_decideShortPress(const struct control_error_latch *latch, bool isIndicationDeferred);

/**
 * @brief Decide what a long press does.
 *
 * @param[in] latch Error latch.
 * @param[in] isIndicationDeferred True during startup and while audio is started.
 *
 * @return CONTROL_PRESS_IGNORE or CONTROL_PRESS_WORKFLOW.
 */
enum control_press_action control_decideLongPress(const struct control_error_latch *latch, bool isIndicationDeferred);

#endif /* L2_CONTROL_ERROR_POLICY_H */

/** @} */
