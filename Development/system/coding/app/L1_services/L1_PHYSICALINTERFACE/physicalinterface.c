/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L1_PHYSICALINTERFACE
 * @{
 * @file
 * Implementation of the PHYSICALINTERFACE module.
 */

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include "physicalinterface.h"
#include "physicalinterface_input.h"

#include <errno.h>
#include <stdbool.h>
#include <stdint.h>

#include <zephyr/device.h>
#include <zephyr/drivers/adc.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/led_strip.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

/** Pattern steps are rendered at this period; fine enough for smooth breathing. */
#define PHYSICALINTERFACE_RENDER_PERIOD_MILLISECONDS 20

#define PHYSICALINTERFACE_FULL_BRIGHTNESS_PERCENT     100
#define PHYSICALINTERFACE_IDLE_DIM_BRIGHTNESS_PERCENT 20 /**< P22 Idle dim candidate. */
#define PHYSICALINTERFACE_REJECTION_DIM_PERCENT       50 /**< Catalogue: input rejected dims by at least 50 %. */

#define PHYSICALINTERFACE_SLOW_BLINK_HALF_PERIOD_MILLISECONDS  1000 /**< P22 slow blink: 0.5 Hz, 1 s on/off. */
#define PHYSICALINTERFACE_BREATHING_PERIOD_MILLISECONDS        3000 /**< P22 breathing: 3 s. */
#define PHYSICALINTERFACE_QUICK_FLASH_HALF_PERIOD_MILLISECONDS 250  /**< P22 flashes: 2 Hz, 250 ms on/off. */
#define PHYSICALINTERFACE_QUICK_FLASH_COUNT                    3
#define PHYSICALINTERFACE_REJECTION_DIM_MILLISECONDS           250 /**< P22 input-rejected dimming: 250 ms. */

#define PHYSICALINTERFACE_STATUS_LIGHT_NODE DT_NODELABEL(status_light)

#define PHYSICALINTERFACE_BUTTON_LONG_PRESS_MILLISECONDS 2000 /**< Long press: at least 2 s. */

#define PHYSICALINTERFACE_USER_NODE DT_PATH(zephyr_user)

/** Murmur and BPM give no edge, because their pins rest high; so the switch is polled. With the 30 ms debounce, a change is reported after about 40 ms (P10: ≤100 ms). */
#define PHYSICALINTERFACE_SWITCH_POLL_MILLISECONDS   10
#define PHYSICALINTERFACE_SWITCH_SETTLE_MICROSECONDS 20 /**< After driving GPIO18 low; a margin, not measured. */
#define PHYSICALINTERFACE_VOLUME_POLL_MILLISECONDS   50 /**< Candidate within P10 (≤100 ms). */

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/** Context colour of the RGB status light. */
enum physicalinterface_colour
{
    PHYSICALINTERFACE_COLOUR_OFF,
    PHYSICALINTERFACE_COLOUR_BLUE,   /**< FHIR. */
    PHYSICALINTERFACE_COLOUR_CYAN,   /**< Audio. */
    PHYSICALINTERFACE_COLOUR_GREEN,  /**< Idle. */
    PHYSICALINTERFACE_COLOUR_VIOLET, /**< Wi-Fi. */
    PHYSICALINTERFACE_COLOUR_WHITE,  /**< Device. */
};

/** Light pattern of a colour. */
enum physicalinterface_pattern
{
    PHYSICALINTERFACE_PATTERN_NO_CHANGE, /**< Keep the current indication. */
    PHYSICALINTERFACE_PATTERN_OFF,
    PHYSICALINTERFACE_PATTERN_STEADY,
    PHYSICALINTERFACE_PATTERN_STEADY_DIM,
    PHYSICALINTERFACE_PATTERN_BLINK_SLOW,
    PHYSICALINTERFACE_PATTERN_BREATHING_SLOW,
    PHYSICALINTERFACE_PATTERN_THREE_QUICK_FLASHES, /**< Runs once, then the light stays off. */
    PHYSICALINTERFACE_PATTERN_DIM_ONCE,            /**< Dims the current indication once; keeps its colour and pattern. */
};

/** RGB part of one catalogue row. */
struct physicalinterface_status_light_row
{
    enum physicalinterface_colour colour;
    enum physicalinterface_pattern pattern;
};

/** Indication currently rendered on the status light. */
struct physicalinterface_status_light_state
{
    enum physicalinterface_colour colour;
    enum physicalinterface_pattern pattern;
    int64_t patternStartMilliseconds;
    int64_t rejectionDimEndMilliseconds; /**< Uptime at which the input-rejected dimming ends. */
};

/***********************************************************************/
/* GLOBAL CONSTANTS                                                    */
/***********************************************************************/

/***********************************************************************/
/* LOCAL CONSTANTS                                                     */
/***********************************************************************/

/** RGB column of the status and error catalogue, indexed by code. */
static const struct physicalinterface_status_light_row physicalinterface_statusLightRows[FEEDBACK_CODE_COUNT] = {
    [FEEDBACK_NONE] = {PHYSICALINTERFACE_COLOUR_OFF, PHYSICALINTERFACE_PATTERN_OFF},
    [FEEDBACK_DELIVERY_SENDING] = {PHYSICALINTERFACE_COLOUR_BLUE, PHYSICALINTERFACE_PATTERN_BREATHING_SLOW},
    [FEEDBACK_DELIVERY_PENDING] = {PHYSICALINTERFACE_COLOUR_BLUE, PHYSICALINTERFACE_PATTERN_BLINK_SLOW},
    [FEEDBACK_DELIVERY_RECEIVED] = {PHYSICALINTERFACE_COLOUR_BLUE, PHYSICALINTERFACE_PATTERN_THREE_QUICK_FLASHES},
    [FEEDBACK_DELIVERY_FAILURE] = {PHYSICALINTERFACE_COLOUR_BLUE, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_DELIVERY_NOT_POSSIBLE] = {PHYSICALINTERFACE_COLOUR_BLUE, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_SERVER_CONNECTION_FAILURE] = {PHYSICALINTERFACE_COLOUR_BLUE, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_DEVICE_REGISTRATION_FAILURE] = {PHYSICALINTERFACE_COLOUR_BLUE, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_LISTENING] = {PHYSICALINTERFACE_COLOUR_CYAN, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_MEASUREMENT_RUNNING] = {PHYSICALINTERFACE_COLOUR_CYAN, PHYSICALINTERFACE_PATTERN_BLINK_SLOW},
    [FEEDBACK_MEASUREMENT_MINIMUM_REACHED] = {PHYSICALINTERFACE_COLOUR_CYAN, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_ANALYSIS_RUNNING] = {PHYSICALINTERFACE_COLOUR_CYAN, PHYSICALINTERFACE_PATTERN_BREATHING_SLOW},
    [FEEDBACK_MICROPHONE_FAILURE] = {PHYSICALINTERFACE_COLOUR_CYAN, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_AUDIO_WORKER_STALL] = {PHYSICALINTERFACE_COLOUR_CYAN, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_AUDIO_OUTPUT_FAILURE] = {PHYSICALINTERFACE_COLOUR_CYAN, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_HEART_RATE_WORKER_STALL] = {PHYSICALINTERFACE_COLOUR_CYAN, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_MEASUREMENT_INVALID] = {PHYSICALINTERFACE_COLOUR_CYAN, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_CONTROL_INPUT_FAILURE] = {PHYSICALINTERFACE_COLOUR_CYAN, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_IDLE] = {PHYSICALINTERFACE_COLOUR_GREEN, PHYSICALINTERFACE_PATTERN_STEADY_DIM},
    [FEEDBACK_WIFI_CONNECTING] = {PHYSICALINTERFACE_COLOUR_VIOLET, PHYSICALINTERFACE_PATTERN_BREATHING_SLOW},
    [FEEDBACK_WIFI_CONNECTED] = {PHYSICALINTERFACE_COLOUR_VIOLET, PHYSICALINTERFACE_PATTERN_THREE_QUICK_FLASHES},
    [FEEDBACK_PORTAL_OPEN] = {PHYSICALINTERFACE_COLOUR_VIOLET, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_JOIN_FAILURE] = {PHYSICALINTERFACE_COLOUR_VIOLET, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_RECONNECT_FAILURE] = {PHYSICALINTERFACE_COLOUR_VIOLET, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_SCAN_FAILURE] = {PHYSICALINTERFACE_COLOUR_VIOLET, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_HOTSPOT_START_FAILURE] = {PHYSICALINTERFACE_COLOUR_VIOLET, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_WIFI_SETTINGS_SAVE_FAILURE] = {PHYSICALINTERFACE_COLOUR_VIOLET, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_WIFI_CLEANUP_FAILURE] = {PHYSICALINTERFACE_COLOUR_VIOLET, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_STARTUP_RUNNING] = {PHYSICALINTERFACE_COLOUR_WHITE, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_SETTINGS_READ_FAILURE] = {PHYSICALINTERFACE_COLOUR_WHITE, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_SETTINGS_SAVE_FAILURE] = {PHYSICALINTERFACE_COLOUR_WHITE, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_STARTUP_FAILURE] = {PHYSICALINTERFACE_COLOUR_WHITE, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_RESET_UNEXPECTED] = {PHYSICALINTERFACE_COLOUR_WHITE, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_SESSION_CONTEXT_CHANGE] = {PHYSICALINTERFACE_COLOUR_WHITE, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_INPUT_REJECTED] = {PHYSICALINTERFACE_COLOUR_OFF, PHYSICALINTERFACE_PATTERN_DIM_ONCE},
    [FEEDBACK_ERROR_ACKNOWLEDGED] = {PHYSICALINTERFACE_COLOUR_OFF, PHYSICALINTERFACE_PATTERN_NO_CHANGE},
};

/** Full-brightness components per colour. Violet keeps red low, because red is reserved for errors. */
static const struct led_rgb physicalinterface_colourComponents[] = {
    [PHYSICALINTERFACE_COLOUR_OFF] = {.r = 0, .g = 0, .b = 0},
    [PHYSICALINTERFACE_COLOUR_BLUE] = {.r = 0, .g = 0, .b = 255},
    [PHYSICALINTERFACE_COLOUR_CYAN] = {.r = 0, .g = 255, .b = 255},
    [PHYSICALINTERFACE_COLOUR_GREEN] = {.r = 0, .g = 255, .b = 0},
    [PHYSICALINTERFACE_COLOUR_VIOLET] = {.r = 128, .g = 0, .b = 255},
    [PHYSICALINTERFACE_COLOUR_WHITE] = {.r = 255, .g = 255, .b = 255},
};

static const struct device *const physicalinterface_statusLightDevice = DEVICE_DT_GET(PHYSICALINTERFACE_STATUS_LIGHT_NODE);

static const struct gpio_dt_spec physicalinterface_button = GPIO_DT_SPEC_GET(PHYSICALINTERFACE_USER_NODE, start_stop_button_gpios);

static const struct gpio_dt_spec physicalinterface_rawContact = GPIO_DT_SPEC_GET_BY_IDX(PHYSICALINTERFACE_USER_NODE, listening_filter_switch_gpios, 0);
static const struct gpio_dt_spec physicalinterface_murmurContact = GPIO_DT_SPEC_GET_BY_IDX(PHYSICALINTERFACE_USER_NODE, listening_filter_switch_gpios, 1);
static const struct gpio_dt_spec physicalinterface_bpmContact = GPIO_DT_SPEC_GET_BY_IDX(PHYSICALINTERFACE_USER_NODE, listening_filter_switch_gpios, 2);

static const struct adc_dt_spec physicalinterface_potentiometer = ADC_DT_SPEC_GET(PHYSICALINTERFACE_USER_NODE);

/***********************************************************************/
/* GLOBAL VARIABLES                                                    */
/***********************************************************************/

/***********************************************************************/
/* LOCAL VARIABLES                                                     */
/***********************************************************************/

static struct k_spinlock physicalinterface_statusLightLock;
static struct physicalinterface_status_light_state physicalinterface_statusLight;
static struct k_work_delayable physicalinterface_statusLightWork;
static struct led_rgb physicalinterface_shownPixel;
static bool physicalinterface_isPixelShown;
static bool physicalinterface_isStatusLightReady;

static struct gpio_callback physicalinterface_buttonEdgeCallback;
static struct k_work_delayable physicalinterface_buttonDebounceWork;
static struct k_work_delayable physicalinterface_buttonLongPressWork;
static struct physicalinterface_input_handlers physicalinterface_handlers;
static bool physicalinterface_isButtonPressed;
static bool physicalinterface_isLongPressReported;

static struct k_work_delayable physicalinterface_switchPollWork;
static struct physicalinterface_switch_debounce physicalinterface_switchDebounce;
static bool physicalinterface_isSwitchReady;

static struct k_work_delayable physicalinterface_volumePollWork;
static struct physicalinterface_volume_tracker physicalinterface_volumeTracker;
static bool physicalinterface_isPotentiometerReady;

/***********************************************************************/
/* LOCAL FUNCTION PROTOTYPES                                           */
/***********************************************************************/

/**
 * @brief Render the current pattern step and schedule the next step if the pattern is animated.
 *
 * @param[in] work Status light work item.
 */
static void physicalinterface_renderStatusLight(struct k_work *work);

/**
 * @brief Brightness of a pattern at a time since its start.
 *
 * @param[in] pattern Pattern to evaluate.
 * @param[in] elapsedMilliseconds Time since the pattern started.
 * @param[out] isAnimated True while later steps can still change the brightness.
 *
 * @return Brightness in percent.
 */
static uint32_t physicalinterface_patternBrightnessPercent(enum physicalinterface_pattern pattern, int64_t elapsedMilliseconds, bool *isAnimated);

/**
 * @brief Initialize the status light and switch it off.
 *
 * @return 0 on success, -ENODEV if the LED strip driver is not ready.
 */
static int physicalinterface_initStatusLight(void);

/**
 * @brief Configure the Start/Stop button input and its edge interrupt.
 *
 * @return 0 on success, -ENODEV if the GPIO port is not ready, or the GPIO error.
 */
static int physicalinterface_initButton(void);

/**
 * @brief Restart the debounce time on every button edge.
 *
 * @param[in] port GPIO port of the button.
 * @param[in] callback Registered edge callback.
 * @param[in] pins Pins that changed.
 */
static void physicalinterface_onButtonEdge(const struct device *port, struct gpio_callback *callback, gpio_port_pins_t pins);

/**
 * @brief Take the button level once it has been stable for the debounce time and report a short press.
 *
 * @param[in] work Debounce work item.
 */
static void physicalinterface_debounceButton(struct k_work *work);

/**
 * @brief Report a long press if the button is still held.
 *
 * @param[in] work Long-press work item.
 */
static void physicalinterface_reportLongPress(struct k_work *work);

/**
 * @brief Configure the switch contacts as inputs and start polling them.
 *
 * Polling also starts after a failure, so the failure is reported as a FAILED reading.
 *
 * @return 0 on success, -ENODEV if a GPIO port is not ready, or the GPIO error.
 */
static int physicalinterface_initSwitch(void);

/**
 * @brief Read the switch once, debounce it, report a stable transition and schedule the next poll.
 *
 * @param[in] work Switch poll work item.
 */
static void physicalinterface_pollSwitch(struct k_work *work);

/**
 * @brief Read the active-low contact levels and decode the switch position.
 *
 * GPIO18 is driven only low, so a contact to ground cannot short a driven high level.
 *
 * @return Decoded sample; invalid if a GPIO access failed.
 */
static struct physicalinterface_switch_sample physicalinterface_readSwitch(void);

/**
 * @brief Set up the potentiometer ADC channel and start polling it.
 *
 * Without a fitted potentiometer the ADC is not touched; the first poll reports
 * it absent and the polling ends.
 *
 * @return 0 on success or if the potentiometer is not fitted, -ENODEV if the ADC is not ready, or the ADC error.
 */
static int physicalinterface_initPotentiometer(void);

/**
 * @brief Read the potentiometer once, report a volume change and schedule the next poll.
 *
 * @param[in] work Volume poll work item.
 */
static void physicalinterface_pollVolume(struct k_work *work);

/**
 * @brief Read the potentiometer wiper voltage.
 *
 * @param[out] millivolts Wiper voltage.
 *
 * @return 0 on success, -ENODEV if the ADC is not set up, or the ADC error.
 */
static int physicalinterface_readPotentiometerMillivolts(int32_t *millivolts);

LOG_MODULE_REGISTER(physicalinterface, LOG_LEVEL_INF);

/***********************************************************************/
/* GLOBAL FUNCTIONS                                                    */
/***********************************************************************/

int physicalinterface_init(const struct physicalinterface_input_handlers *handlers)
{
    physicalinterface_handlers = *handlers;

    int statusLightResult = physicalinterface_initStatusLight();
    int buttonResult = physicalinterface_initButton();
    int switchResult = physicalinterface_initSwitch();
    int potentiometerResult = physicalinterface_initPotentiometer();
    int firstError = potentiometerResult;

    if(statusLightResult != 0)
    {
        firstError = statusLightResult;
    }
    else if(buttonResult != 0)
    {
        firstError = buttonResult;
    }
    else if(switchResult != 0)
    {
        firstError = switchResult;
    }
    else
    {
        /* The potentiometer result stays. */
    }

    return firstError;
}

void physicalinterface_showStatusLight(enum feedback_code code)
{
    if(!physicalinterface_isStatusLightReady)
    {
        return;
    }

    if((code < FEEDBACK_NONE) || (code >= FEEDBACK_CODE_COUNT))
    {
        LOG_WRN("Unknown feedback code %d", code);
        return;
    }

    const struct physicalinterface_status_light_row *row = &physicalinterface_statusLightRows[code];

    if(row->pattern == PHYSICALINTERFACE_PATTERN_NO_CHANGE)
    {
        return;
    }

    k_spinlock_key_t key = k_spin_lock(&physicalinterface_statusLightLock);

    if(row->pattern == PHYSICALINTERFACE_PATTERN_DIM_ONCE)
    {
        physicalinterface_statusLight.rejectionDimEndMilliseconds = k_uptime_get() + PHYSICALINTERFACE_REJECTION_DIM_MILLISECONDS;
    }
    else
    {
        physicalinterface_statusLight.colour = row->colour;
        physicalinterface_statusLight.pattern = row->pattern;
        physicalinterface_statusLight.patternStartMilliseconds = k_uptime_get();
    }

    k_spin_unlock(&physicalinterface_statusLightLock, key);

    (void)k_work_reschedule(&physicalinterface_statusLightWork, K_NO_WAIT);
}

/***********************************************************************/
/* LOCAL FUNCTIONS                                                     */
/***********************************************************************/

static int physicalinterface_initStatusLight(void)
{
    k_work_init_delayable(&physicalinterface_statusLightWork, physicalinterface_renderStatusLight);

    if(!device_is_ready(physicalinterface_statusLightDevice))
    {
        LOG_ERR("Status light driver %s is not ready", physicalinterface_statusLightDevice->name);
        return -ENODEV;
    }

    physicalinterface_isStatusLightReady = true;
    physicalinterface_showStatusLight(FEEDBACK_NONE);

    return 0;
}

static int physicalinterface_initButton(void)
{
    k_work_init_delayable(&physicalinterface_buttonDebounceWork, physicalinterface_debounceButton);
    k_work_init_delayable(&physicalinterface_buttonLongPressWork, physicalinterface_reportLongPress);

    if(!gpio_is_ready_dt(&physicalinterface_button))
    {
        LOG_ERR("Button GPIO port %s is not ready", physicalinterface_button.port->name);
        return -ENODEV;
    }

    int result = gpio_pin_configure_dt(&physicalinterface_button, GPIO_INPUT);

    if(result != 0)
    {
        LOG_ERR("Button input configuration failed: %d", result);
        return result;
    }

    /* A press already held at boot is the baseline, not an event. */
    physicalinterface_isButtonPressed = (gpio_pin_get_dt(&physicalinterface_button) == 1);
    physicalinterface_isLongPressReported = physicalinterface_isButtonPressed;

    gpio_init_callback(&physicalinterface_buttonEdgeCallback, physicalinterface_onButtonEdge, BIT(physicalinterface_button.pin));

    result = gpio_add_callback_dt(&physicalinterface_button, &physicalinterface_buttonEdgeCallback);

    if(result != 0)
    {
        LOG_ERR("Button callback registration failed: %d", result);
        return result;
    }

    result = gpio_pin_interrupt_configure_dt(&physicalinterface_button, GPIO_INT_EDGE_BOTH);

    if(result != 0)
    {
        LOG_ERR("Button interrupt configuration failed: %d", result);
    }

    return result;
}

static void physicalinterface_onButtonEdge(const struct device *port, struct gpio_callback *callback, gpio_port_pins_t pins)
{
    ARG_UNUSED(port);
    ARG_UNUSED(callback);
    ARG_UNUSED(pins);

    (void)k_work_reschedule(&physicalinterface_buttonDebounceWork, K_MSEC(PHYSICALINTERFACE_DEBOUNCE_MILLISECONDS));
}

static void physicalinterface_debounceButton(struct k_work *work)
{
    ARG_UNUSED(work);

    int level = gpio_pin_get_dt(&physicalinterface_button);

    if(level < 0)
    {
        LOG_WRN("Button read failed: %d", level);
        return;
    }

    bool isPressed = (level == 1);

    if(isPressed == physicalinterface_isButtonPressed)
    {
        return;
    }

    physicalinterface_isButtonPressed = isPressed;

    if(isPressed)
    {
        physicalinterface_isLongPressReported = false;
        (void)k_work_schedule(&physicalinterface_buttonLongPressWork, K_MSEC(PHYSICALINTERFACE_BUTTON_LONG_PRESS_MILLISECONDS));
        return;
    }

    (void)k_work_cancel_delayable(&physicalinterface_buttonLongPressWork);

    if(!physicalinterface_isLongPressReported)
    {
        physicalinterface_handlers.button(PHYSICALINTERFACE_BUTTON_SHORT_PRESS, k_uptime_get());
    }
}

static void physicalinterface_reportLongPress(struct k_work *work)
{
    ARG_UNUSED(work);

    if(physicalinterface_isButtonPressed && !physicalinterface_isLongPressReported)
    {
        physicalinterface_isLongPressReported = true;
        physicalinterface_handlers.button(PHYSICALINTERFACE_BUTTON_LONG_PRESS, k_uptime_get());
    }
}

static int physicalinterface_initSwitch(void)
{
    const struct gpio_dt_spec *contacts[] = {&physicalinterface_rawContact, &physicalinterface_murmurContact, &physicalinterface_bpmContact};
    int result = 0;

    physicalinterface_resetSwitchDebounce(&physicalinterface_switchDebounce);
    k_work_init_delayable(&physicalinterface_switchPollWork, physicalinterface_pollSwitch);

    for(size_t index = 0; (index < ARRAY_SIZE(contacts)) && (result == 0); index++)
    {
        if(!gpio_is_ready_dt(contacts[index]))
        {
            LOG_ERR("Switch GPIO port %s is not ready", contacts[index]->port->name);
            result = -ENODEV;
        }
        else
        {
            result = gpio_pin_configure_dt(contacts[index], GPIO_INPUT);

            if(result != 0)
            {
                LOG_ERR("Switch input %u configuration failed: %d", contacts[index]->pin, result);
            }
        }
    }

    physicalinterface_isSwitchReady = (result == 0);
    (void)k_work_schedule(&physicalinterface_switchPollWork, K_NO_WAIT);

    return result;
}

static void physicalinterface_pollSwitch(struct k_work *work)
{
    ARG_UNUSED(work);

    struct physicalinterface_switch_sample sample = physicalinterface_readSwitch();
    int64_t nowMilliseconds = k_uptime_get();

    if(physicalinterface_debounceSwitch(&physicalinterface_switchDebounce, sample, nowMilliseconds))
    {
        struct physicalinterface_listening_filter_reading reading = {
            .filter = physicalinterface_switchDebounce.stable.filter,
            .status = physicalinterface_switchDebounce.stable.isValid ? PHYSICALINTERFACE_INPUT_VALID : PHYSICALINTERFACE_INPUT_FAILED,
            .timestampMilliseconds = nowMilliseconds,
        };

        physicalinterface_handlers.listeningFilter(&reading);
    }

    (void)k_work_schedule(&physicalinterface_switchPollWork, K_MSEC(PHYSICALINTERFACE_SWITCH_POLL_MILLISECONDS));
}

static struct physicalinterface_switch_sample physicalinterface_readSwitch(void)
{
    int rawContactLevel = -ENODEV;
    int murmurContactLevel = -ENODEV;
    int bpmContactLevel = -ENODEV;

    if(physicalinterface_isSwitchReady)
    {
        rawContactLevel = gpio_pin_get_dt(&physicalinterface_rawContact);
    }

    if(rawContactLevel == 0)
    {
        int driveResult = gpio_pin_configure_dt(&physicalinterface_rawContact, GPIO_OUTPUT_ACTIVE);

        if(driveResult == 0)
        {
            k_busy_wait(PHYSICALINTERFACE_SWITCH_SETTLE_MICROSECONDS);
            murmurContactLevel = gpio_pin_get_dt(&physicalinterface_murmurContact);
            bpmContactLevel = gpio_pin_get_dt(&physicalinterface_bpmContact);
        }

        int releaseResult = gpio_pin_configure_dt(&physicalinterface_rawContact, GPIO_INPUT);

        if(releaseResult != 0)
        {
            murmurContactLevel = releaseResult;
        }
    }

    return physicalinterface_decodeSwitch(rawContactLevel, murmurContactLevel, bpmContactLevel);
}

static int physicalinterface_initPotentiometer(void)
{
    int result = 0;

    physicalinterface_resetVolumeTracker(&physicalinterface_volumeTracker);
    k_work_init_delayable(&physicalinterface_volumePollWork, physicalinterface_pollVolume);

    if(!IS_ENABLED(CONFIG_PHYSICALINTERFACE_VOLUME_POTENTIOMETER_FITTED))
    {
        LOG_INF("Volume potentiometer not fitted; reporting it absent");
    }
    else if(!adc_is_ready_dt(&physicalinterface_potentiometer))
    {
        LOG_ERR("Potentiometer ADC %s is not ready", physicalinterface_potentiometer.dev->name);
        result = -ENODEV;
    }
    else
    {
        result = adc_channel_setup_dt(&physicalinterface_potentiometer);

        if(result != 0)
        {
            LOG_ERR("Potentiometer ADC channel setup failed: %d", result);
        }
    }

    physicalinterface_isPotentiometerReady = IS_ENABLED(CONFIG_PHYSICALINTERFACE_VOLUME_POTENTIOMETER_FITTED) && (result == 0);
    (void)k_work_schedule(&physicalinterface_volumePollWork, K_NO_WAIT);

    return result;
}

static void physicalinterface_pollVolume(struct k_work *work)
{
    ARG_UNUSED(work);

    bool isFitted = IS_ENABLED(CONFIG_PHYSICALINTERFACE_VOLUME_POTENTIOMETER_FITTED);
    int32_t millivolts = 0;
    int result = isFitted ? physicalinterface_readPotentiometerMillivolts(&millivolts) : 0;
    int64_t nowMilliseconds = k_uptime_get();
    enum physicalinterface_input_status status = PHYSICALINTERFACE_INPUT_ABSENT;

    if(isFitted)
    {
        status = (result == 0) ? PHYSICALINTERFACE_INPUT_VALID : PHYSICALINTERFACE_INPUT_FAILED;
    }

    if(physicalinterface_trackVolume(&physicalinterface_volumeTracker, status, millivolts))
    {
        if(status == PHYSICALINTERFACE_INPUT_FAILED)
        {
            LOG_WRN("Potentiometer read failed: %d", result);
        }

        struct physicalinterface_volume_reading reading = {
            .percent = physicalinterface_volumeTracker.reportedPercent,
            .status = physicalinterface_volumeTracker.reportedStatus,
            .timestampMilliseconds = nowMilliseconds,
        };

        physicalinterface_handlers.volume(&reading);
    }

    if(isFitted)
    {
        (void)k_work_schedule(&physicalinterface_volumePollWork, K_MSEC(PHYSICALINTERFACE_VOLUME_POLL_MILLISECONDS));
    }
}

static int physicalinterface_readPotentiometerMillivolts(int32_t *millivolts)
{
    int16_t sample = 0;
    struct adc_sequence sequence = {.buffer = &sample, .buffer_size = sizeof(sample)};
    int result = physicalinterface_isPotentiometerReady ? 0 : -ENODEV;

    if(result == 0)
    {
        result = adc_sequence_init_dt(&physicalinterface_potentiometer, &sequence);
    }

    if(result == 0)
    {
        result = adc_read_dt(&physicalinterface_potentiometer, &sequence);
    }

    if(result == 0)
    {
        *millivolts = sample;
        result = adc_raw_to_millivolts_dt(&physicalinterface_potentiometer, millivolts);
    }

    return result;
}

static void physicalinterface_renderStatusLight(struct k_work *work)
{
    ARG_UNUSED(work);

    k_spinlock_key_t key = k_spin_lock(&physicalinterface_statusLightLock);
    struct physicalinterface_status_light_state state = physicalinterface_statusLight;
    k_spin_unlock(&physicalinterface_statusLightLock, key);

    int64_t nowMilliseconds = k_uptime_get();
    bool isAnimated = false;
    uint32_t brightnessPercent = physicalinterface_patternBrightnessPercent(state.pattern, nowMilliseconds - state.patternStartMilliseconds, &isAnimated);

    if(nowMilliseconds < state.rejectionDimEndMilliseconds)
    {
        brightnessPercent = (brightnessPercent * PHYSICALINTERFACE_REJECTION_DIM_PERCENT) / PHYSICALINTERFACE_FULL_BRIGHTNESS_PERCENT;
        isAnimated = true;
    }

    const struct led_rgb *fullColour = &physicalinterface_colourComponents[state.colour];
    struct led_rgb pixel = {
        .r = (uint8_t)((fullColour->r * brightnessPercent) / PHYSICALINTERFACE_FULL_BRIGHTNESS_PERCENT),
        .g = (uint8_t)((fullColour->g * brightnessPercent) / PHYSICALINTERFACE_FULL_BRIGHTNESS_PERCENT),
        .b = (uint8_t)((fullColour->b * brightnessPercent) / PHYSICALINTERFACE_FULL_BRIGHTNESS_PERCENT),
    };

    bool isPixelChanged = !physicalinterface_isPixelShown || (pixel.r != physicalinterface_shownPixel.r) ||
                          (pixel.g != physicalinterface_shownPixel.g) || (pixel.b != physicalinterface_shownPixel.b);

    if(isPixelChanged)
    {
        int result = led_strip_update_rgb(physicalinterface_statusLightDevice, &pixel, 1);

        if(result == 0)
        {
            physicalinterface_shownPixel = pixel;
            physicalinterface_isPixelShown = true;
        }
        else
        {
            LOG_WRN("Status light update failed: %d", result);
        }
    }

    if(isAnimated)
    {
        (void)k_work_schedule(&physicalinterface_statusLightWork, K_MSEC(PHYSICALINTERFACE_RENDER_PERIOD_MILLISECONDS));
    }
}

static uint32_t physicalinterface_patternBrightnessPercent(enum physicalinterface_pattern pattern, int64_t elapsedMilliseconds, bool *isAnimated)
{
    *isAnimated = false;

    switch(pattern)
    {
    case PHYSICALINTERFACE_PATTERN_STEADY:
        return PHYSICALINTERFACE_FULL_BRIGHTNESS_PERCENT;

    case PHYSICALINTERFACE_PATTERN_STEADY_DIM:
        return PHYSICALINTERFACE_IDLE_DIM_BRIGHTNESS_PERCENT;

    case PHYSICALINTERFACE_PATTERN_BLINK_SLOW:
    {
        *isAnimated = true;
        int64_t phaseMilliseconds = elapsedMilliseconds % (2 * PHYSICALINTERFACE_SLOW_BLINK_HALF_PERIOD_MILLISECONDS);

        return (phaseMilliseconds < PHYSICALINTERFACE_SLOW_BLINK_HALF_PERIOD_MILLISECONDS) ? PHYSICALINTERFACE_FULL_BRIGHTNESS_PERCENT : 0;
    }

    case PHYSICALINTERFACE_PATTERN_BREATHING_SLOW:
    {
        *isAnimated = true;
        int64_t halfPeriodMilliseconds = PHYSICALINTERFACE_BREATHING_PERIOD_MILLISECONDS / 2;
        int64_t phaseMilliseconds = elapsedMilliseconds % PHYSICALINTERFACE_BREATHING_PERIOD_MILLISECONDS;
        int64_t distanceFromPeakMilliseconds = (phaseMilliseconds < halfPeriodMilliseconds) ? phaseMilliseconds : (PHYSICALINTERFACE_BREATHING_PERIOD_MILLISECONDS - phaseMilliseconds);

        return (uint32_t)((distanceFromPeakMilliseconds * PHYSICALINTERFACE_FULL_BRIGHTNESS_PERCENT) / halfPeriodMilliseconds);
    }

    case PHYSICALINTERFACE_PATTERN_THREE_QUICK_FLASHES:
    {
        int64_t flashSequenceMilliseconds = 2 * PHYSICALINTERFACE_QUICK_FLASH_COUNT * PHYSICALINTERFACE_QUICK_FLASH_HALF_PERIOD_MILLISECONDS;

        if(elapsedMilliseconds >= flashSequenceMilliseconds)
        {
            return 0;
        }

        *isAnimated = true;
        bool isFlashOn = ((elapsedMilliseconds / PHYSICALINTERFACE_QUICK_FLASH_HALF_PERIOD_MILLISECONDS) % 2) == 0;

        return isFlashOn ? PHYSICALINTERFACE_FULL_BRIGHTNESS_PERCENT : 0;
    }

    case PHYSICALINTERFACE_PATTERN_OFF:
    case PHYSICALINTERFACE_PATTERN_NO_CHANGE:
    case PHYSICALINTERFACE_PATTERN_DIM_ONCE:
    default:
        return 0;
    }
}

/** @} */
