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
#include "physicalinterface_indication.h"
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

/** Pattern steps are rendered at this period; fine enough for smooth breathing and 250 ms code blinks. */
#define PHYSICALINTERFACE_RENDER_PERIOD_MILLISECONDS 20

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

/***********************************************************************/
/* GLOBAL CONSTANTS                                                    */
/***********************************************************************/

/***********************************************************************/
/* LOCAL CONSTANTS                                                     */
/***********************************************************************/

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
static const struct gpio_dt_spec physicalinterface_buttonLight = GPIO_DT_SPEC_GET(PHYSICALINTERFACE_USER_NODE, start_stop_button_light_gpios);

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

static struct k_spinlock physicalinterface_indicationLock;
static struct physicalinterface_indication physicalinterface_lightsIndication;
static struct k_work_delayable physicalinterface_lightsWork;
static struct led_rgb physicalinterface_shownPixel;
static bool physicalinterface_isPixelShown;
static bool physicalinterface_isStatusLightReady;
static bool physicalinterface_isButtonLightShownOn;
static bool physicalinterface_isButtonLightLevelShown;
static bool physicalinterface_isButtonLightReady;

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
 * @brief Render the current pattern step on both lights and schedule the next step if a pattern is animated.
 *
 * @param[in] work Lights work item.
 */
static void physicalinterface_updateLights(struct k_work *work);

/**
 * @brief Show a colour at a brightness on the status light, if it changed.
 *
 * @param[in] colour Context colour.
 * @param[in] brightnessPercent Brightness, 0 to 100.
 */
static void physicalinterface_writeStatusLight(enum physicalinterface_colour colour, uint32_t brightnessPercent);

/**
 * @brief Set the red button light, if its level changed.
 *
 * @param[in] isOn True to switch the light on.
 */
static void physicalinterface_writeButtonLight(bool isOn);

/**
 * @brief Initialize the status light.
 *
 * @return 0 on success, -ENODEV if the LED strip driver is not ready.
 */
static int physicalinterface_initStatusLight(void);

/**
 * @brief Configure the red button light as an output, switched off.
 *
 * @return 0 on success, -ENODEV if the GPIO port is not ready, or the GPIO error.
 */
static int physicalinterface_initButtonLight(void);

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

/***********************************************************************/
/* MACROS                                                              */
/***********************************************************************/

LOG_MODULE_REGISTER(physicalinterface, LOG_LEVEL_INF);

/***********************************************************************/
/* GLOBAL FUNCTIONS                                                    */
/***********************************************************************/

int physicalinterface_init(const struct physicalinterface_input_handlers *handlers)
{
    physicalinterface_handlers = *handlers;
    physicalinterface_resetIndication(&physicalinterface_lightsIndication);
    k_work_init_delayable(&physicalinterface_lightsWork, physicalinterface_updateLights);

    int statusLightResult = physicalinterface_initStatusLight();
    int buttonLightResult = physicalinterface_initButtonLight();
    int buttonResult = physicalinterface_initButton();
    int switchResult = physicalinterface_initSwitch();
    int potentiometerResult = physicalinterface_initPotentiometer();
    int firstError = potentiometerResult;

    physicalinterface_showFeedback(FEEDBACK_NONE);

    if(statusLightResult != 0)
    {
        firstError = statusLightResult;
    }
    else if(buttonLightResult != 0)
    {
        firstError = buttonLightResult;
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

void physicalinterface_showFeedback(enum feedback_code code)
{
    if(!physicalinterface_isFeedbackCode(code))
    {
        LOG_WRN("Unknown feedback code %d", code);
    }
    else if(physicalinterface_isStatusLightReady || physicalinterface_isButtonLightReady)
    {
        k_spinlock_key_t key = k_spin_lock(&physicalinterface_indicationLock);

        physicalinterface_applyIndication(&physicalinterface_lightsIndication, code, k_uptime_get());
        k_spin_unlock(&physicalinterface_indicationLock, key);

        (void)k_work_reschedule(&physicalinterface_lightsWork, K_NO_WAIT);
    }
    else
    {
        /* Neither light works; the serial log keeps the cause. */
    }
}

/***********************************************************************/
/* LOCAL FUNCTIONS                                                     */
/***********************************************************************/

static int physicalinterface_initStatusLight(void)
{
    int result = 0;

    if(!device_is_ready(physicalinterface_statusLightDevice))
    {
        LOG_ERR("Status light driver %s is not ready", physicalinterface_statusLightDevice->name);
        result = -ENODEV;
    }

    physicalinterface_isStatusLightReady = (result == 0);

    return result;
}

static int physicalinterface_initButtonLight(void)
{
    int result = 0;

    if(!gpio_is_ready_dt(&physicalinterface_buttonLight))
    {
        LOG_ERR("Button light GPIO port %s is not ready", physicalinterface_buttonLight.port->name);
        result = -ENODEV;
    }
    else
    {
        result = gpio_pin_configure_dt(&physicalinterface_buttonLight, GPIO_OUTPUT_INACTIVE);

        if(result != 0)
        {
            LOG_ERR("Button light output configuration failed: %d", result);
        }
    }

    physicalinterface_isButtonLightReady = (result == 0);

    return result;
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

    k_spinlock_key_t key = k_spin_lock(&physicalinterface_indicationLock);
    physicalinterface_setIndicationButtonPressed(&physicalinterface_lightsIndication, isPressed);
    k_spin_unlock(&physicalinterface_indicationLock, key);
    (void)k_work_reschedule(&physicalinterface_lightsWork, K_NO_WAIT);

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

static void physicalinterface_updateLights(struct k_work *work)
{
    ARG_UNUSED(work);

    k_spinlock_key_t key = k_spin_lock(&physicalinterface_indicationLock);
    struct physicalinterface_indication_output output = physicalinterface_renderIndication(&physicalinterface_lightsIndication, k_uptime_get());
    k_spin_unlock(&physicalinterface_indicationLock, key);

    if(physicalinterface_isStatusLightReady)
    {
        physicalinterface_writeStatusLight(output.colour, output.statusLightBrightnessPercent);
    }

    if(physicalinterface_isButtonLightReady)
    {
        physicalinterface_writeButtonLight(output.isButtonLightOn);
    }

    if(output.isAnimated)
    {
        (void)k_work_schedule(&physicalinterface_lightsWork, K_MSEC(PHYSICALINTERFACE_RENDER_PERIOD_MILLISECONDS));
    }
}

static void physicalinterface_writeStatusLight(enum physicalinterface_colour colour, uint32_t brightnessPercent)
{
    const struct led_rgb *fullColour = &physicalinterface_colourComponents[colour];
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
}

static void physicalinterface_writeButtonLight(bool isOn)
{
    if(!physicalinterface_isButtonLightLevelShown || (isOn != physicalinterface_isButtonLightShownOn))
    {
        int result = gpio_pin_set_dt(&physicalinterface_buttonLight, isOn ? 1 : 0);

        if(result == 0)
        {
            physicalinterface_isButtonLightShownOn = isOn;
            physicalinterface_isButtonLightLevelShown = true;
        }
        else
        {
            LOG_WRN("Button light update failed: %d", result);
        }
    }
}

/** @} */
