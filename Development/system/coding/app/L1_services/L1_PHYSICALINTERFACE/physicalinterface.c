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

#include <errno.h>
#include <stdbool.h>
#include <stdint.h>

#include <zephyr/device.h>
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

#define PHYSICALINTERFACE_SLOW_BLINK_HALF_PERIOD_MILLISECONDS  1000 /**< P22 slow blink: 0.5 Hz, 1 s on/off. */
#define PHYSICALINTERFACE_BREATHING_PERIOD_MILLISECONDS        3000 /**< P22 breathing: 3 s. */
#define PHYSICALINTERFACE_QUICK_FLASH_HALF_PERIOD_MILLISECONDS 250  /**< P22 flashes: 2 Hz, 250 ms on/off. */
#define PHYSICALINTERFACE_QUICK_FLASH_COUNT                    3

#define PHYSICALINTERFACE_STATUS_LIGHT_NODE DT_NODELABEL(status_light)

#define PHYSICALINTERFACE_BUTTON_DEBOUNCE_MILLISECONDS   30   /**< P10 candidate debounce. */
#define PHYSICALINTERFACE_BUTTON_LONG_PRESS_MILLISECONDS 2000 /**< Long press: at least 2 s. */

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/** Context colour of the RGB status light. */
enum physicalinterface_colour
{
    PHYSICALINTERFACE_COLOUR_OFF,
    PHYSICALINTERFACE_COLOUR_WHITE,  /**< Device. */
    PHYSICALINTERFACE_COLOUR_GREEN,  /**< Idle. */
    PHYSICALINTERFACE_COLOUR_CYAN,   /**< Audio. */
    PHYSICALINTERFACE_COLOUR_VIOLET, /**< Wi-Fi. */
    PHYSICALINTERFACE_COLOUR_BLUE,   /**< FHIR. */
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
    [FEEDBACK_SERVER_CONNECTION_FAILURE] = {PHYSICALINTERFACE_COLOUR_BLUE, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_DEVICE_REGISTRATION_FAILURE] = {PHYSICALINTERFACE_COLOUR_BLUE, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_DELIVERY_FAILURE] = {PHYSICALINTERFACE_COLOUR_BLUE, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_DELIVERY_NOT_POSSIBLE] = {PHYSICALINTERFACE_COLOUR_BLUE, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_LISTENING] = {PHYSICALINTERFACE_COLOUR_CYAN, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_MEASUREMENT_RUNNING] = {PHYSICALINTERFACE_COLOUR_CYAN, PHYSICALINTERFACE_PATTERN_BLINK_SLOW},
    [FEEDBACK_MEASUREMENT_MINIMUM_REACHED] = {PHYSICALINTERFACE_COLOUR_CYAN, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_ANALYSIS_RUNNING] = {PHYSICALINTERFACE_COLOUR_CYAN, PHYSICALINTERFACE_PATTERN_BREATHING_SLOW},
    [FEEDBACK_AUDIO_WORKER_STALL] = {PHYSICALINTERFACE_COLOUR_CYAN, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_HEART_RATE_WORKER_STALL] = {PHYSICALINTERFACE_COLOUR_CYAN, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_MEASUREMENT_INVALID] = {PHYSICALINTERFACE_COLOUR_CYAN, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_MICROPHONE_FAILURE] = {PHYSICALINTERFACE_COLOUR_CYAN, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_AUDIO_OUTPUT_FAILURE] = {PHYSICALINTERFACE_COLOUR_CYAN, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_CONTROL_INPUT_FAILURE] = {PHYSICALINTERFACE_COLOUR_CYAN, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_IDLE] = {PHYSICALINTERFACE_COLOUR_GREEN, PHYSICALINTERFACE_PATTERN_STEADY_DIM},
    [FEEDBACK_PORTAL_OPEN] = {PHYSICALINTERFACE_COLOUR_VIOLET, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_WIFI_CONNECTING] = {PHYSICALINTERFACE_COLOUR_VIOLET, PHYSICALINTERFACE_PATTERN_BREATHING_SLOW},
    [FEEDBACK_WIFI_CONNECTED] = {PHYSICALINTERFACE_COLOUR_VIOLET, PHYSICALINTERFACE_PATTERN_THREE_QUICK_FLASHES},
    [FEEDBACK_WIFI_SETTINGS_SAVE_FAILURE] = {PHYSICALINTERFACE_COLOUR_VIOLET, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_SCAN_FAILURE] = {PHYSICALINTERFACE_COLOUR_VIOLET, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_JOIN_FAILURE] = {PHYSICALINTERFACE_COLOUR_VIOLET, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_RECONNECT_FAILURE] = {PHYSICALINTERFACE_COLOUR_VIOLET, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_HOTSPOT_START_FAILURE] = {PHYSICALINTERFACE_COLOUR_VIOLET, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_WIFI_CLEANUP_FAILURE] = {PHYSICALINTERFACE_COLOUR_VIOLET, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_STARTUP_RUNNING] = {PHYSICALINTERFACE_COLOUR_WHITE, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_SETTINGS_READ_FAILURE] = {PHYSICALINTERFACE_COLOUR_WHITE, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_STARTUP_FAILURE] = {PHYSICALINTERFACE_COLOUR_WHITE, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_RESET_UNEXPECTED] = {PHYSICALINTERFACE_COLOUR_WHITE, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_SETTINGS_SAVE_FAILURE] = {PHYSICALINTERFACE_COLOUR_WHITE, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_SESSION_CONTEXT_CHANGE] = {PHYSICALINTERFACE_COLOUR_WHITE, PHYSICALINTERFACE_PATTERN_STEADY},
    [FEEDBACK_INPUT_REJECTED] = {PHYSICALINTERFACE_COLOUR_OFF, PHYSICALINTERFACE_PATTERN_NO_CHANGE},
    [FEEDBACK_ERROR_ACKNOWLEDGED] = {PHYSICALINTERFACE_COLOUR_OFF, PHYSICALINTERFACE_PATTERN_NO_CHANGE},
};

/** Full-brightness components per colour. Violet keeps red low, because red is reserved for errors. */
static const struct led_rgb physicalinterface_colourComponents[] = {
    [PHYSICALINTERFACE_COLOUR_OFF] = {.r = 0, .g = 0, .b = 0},
    [PHYSICALINTERFACE_COLOUR_WHITE] = {.r = 255, .g = 255, .b = 255},
    [PHYSICALINTERFACE_COLOUR_GREEN] = {.r = 0, .g = 255, .b = 0},
    [PHYSICALINTERFACE_COLOUR_CYAN] = {.r = 0, .g = 255, .b = 255},
    [PHYSICALINTERFACE_COLOUR_VIOLET] = {.r = 128, .g = 0, .b = 255},
    [PHYSICALINTERFACE_COLOUR_BLUE] = {.r = 0, .g = 0, .b = 255},
};

static const struct device *const physicalinterface_statusLightDevice = DEVICE_DT_GET(PHYSICALINTERFACE_STATUS_LIGHT_NODE);

static const struct gpio_dt_spec physicalinterface_button = GPIO_DT_SPEC_GET(DT_PATH(zephyr_user), start_stop_button_gpios);

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
static physicalinterface_button_handler physicalinterface_buttonHandler;
static bool physicalinterface_isButtonPressed;
static bool physicalinterface_isLongPressReported;

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

LOG_MODULE_REGISTER(physicalinterface, LOG_LEVEL_INF);

/***********************************************************************/
/* GLOBAL FUNCTIONS                                                    */
/***********************************************************************/

int physicalinterface_init(physicalinterface_button_handler buttonHandler)
{
    physicalinterface_buttonHandler = buttonHandler;

    int statusLightResult = physicalinterface_initStatusLight();
    int buttonResult = physicalinterface_initButton();

    return (statusLightResult != 0) ? statusLightResult : buttonResult;
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

    physicalinterface_statusLight.colour = row->colour;
    physicalinterface_statusLight.pattern = row->pattern;
    physicalinterface_statusLight.patternStartMilliseconds = k_uptime_get();

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

    (void)k_work_reschedule(&physicalinterface_buttonDebounceWork, K_MSEC(PHYSICALINTERFACE_BUTTON_DEBOUNCE_MILLISECONDS));
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
        physicalinterface_buttonHandler(PHYSICALINTERFACE_BUTTON_SHORT_PRESS);
    }
}

static void physicalinterface_reportLongPress(struct k_work *work)
{
    ARG_UNUSED(work);

    if(physicalinterface_isButtonPressed && !physicalinterface_isLongPressReported)
    {
        physicalinterface_isLongPressReported = true;
        physicalinterface_buttonHandler(PHYSICALINTERFACE_BUTTON_LONG_PRESS);
    }
}

static void physicalinterface_renderStatusLight(struct k_work *work)
{
    ARG_UNUSED(work);

    k_spinlock_key_t key = k_spin_lock(&physicalinterface_statusLightLock);
    struct physicalinterface_status_light_state state = physicalinterface_statusLight;
    k_spin_unlock(&physicalinterface_statusLightLock, key);

    bool isAnimated = false;
    uint32_t brightnessPercent = physicalinterface_patternBrightnessPercent(state.pattern, k_uptime_get() - state.patternStartMilliseconds, &isAnimated);

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
    default:
        return 0;
    }
}

/** @} */
