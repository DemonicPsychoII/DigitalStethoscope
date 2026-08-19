/* Application orchestration for the ESP32-S3 digital-stethoscope bring-up. */

#include <errno.h>

#include <zephyr/drivers/gpio.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

#include "analog_backlight.h"
#include "app_logic.h"
#include "app_types.h"
#include "audio_loopback.h"
#include "display_touch.h"
#include "gpio_inputs.h"
#include "peripherals.h"
#include "status_reporting.h"

LOG_MODULE_REGISTER(bringup, LOG_LEVEL_INF);

#define EVENT_QUEUE_DEPTH 16
#define ANALOG_PERIOD_MS 100U
#define STATUS_PERIOD_MS 500U
#define IDLE_PERIOD_MS 5000U
#define INPUT_RESPONSE_REQUIREMENT_MS 35U

/* Producers are GPIO deferred work and the input callback; main is sole consumer. */
K_MSGQ_DEFINE(app_event_queue, sizeof(struct app_event), EVENT_QUEUE_DEPTH, 4);

struct app_context {
	struct peripheral_registry peripherals;
	struct runtime_state runtime;
	unsigned int adc_errors;
	unsigned int pwm_errors;
	unsigned int gpio_errors;
	unsigned int latency_violations;
	uint32_t max_input_latency_ms;
};

static void disable_after_policy(struct app_context *context, enum component_id component,
                                 enum driver_operation operation, unsigned int failures, int error)
{
	enum driver_error_action action = app_driver_error_action(operation, failures);

	if (action == DRIVER_ERROR_DISABLE_COMPONENT) {
		peripherals_disable(&context->peripherals, component, error);
		context->runtime.features = app_degraded_features(context->peripherals.components);
	}
}

static int draw_color(struct app_context *context)
{
	int rc;
	unsigned int failures = 0U;

	do {
		rc = display_touch_show_color(context->runtime.touch.color_index);
		if (rc == 0) {
			return 0;
		}
		failures++;
	} while (app_driver_error_action(DRIVER_OP_DISPLAY_WRITE, failures) == DRIVER_ERROR_RETRY);

	peripherals_disable(&context->peripherals, COMP_DISPLAY, rc);
	context->runtime.features = app_degraded_features(context->peripherals.components);
	return rc;
}

static void sample_potentiometer(struct app_context *context)
{
	int millivolts;
	int rc;

	if (!peripherals_operational(&context->peripherals, COMP_POTENTIOMETER)) {
		return;
	}
	rc = analog_backlight_read_mv(&millivolts);
	if (rc != 0) {
		context->adc_errors++;
		disable_after_policy(context, COMP_POTENTIOMETER, DRIVER_OP_ADC_SAMPLE,
		                     context->adc_errors, rc);
		return;
	}
	context->adc_errors = 0U;
	context->runtime.potentiometer_mv = millivolts;
	context->runtime.brightness_percent = app_brightness_percent(millivolts);
	if (!peripherals_operational(&context->peripherals, COMP_BACKLIGHT)) {
		return;
	}
	rc = analog_backlight_set_mv(millivolts);
	if (rc != 0) {
		context->pwm_errors++;
		disable_after_policy(context, COMP_BACKLIGHT, DRIVER_OP_BACKLIGHT_PWM,
		                     context->pwm_errors, rc);
	} else {
		context->pwm_errors = 0U;
	}
}

static void record_input_latency(struct app_context *context, uint32_t event_time)
{
	uint32_t latency = k_uptime_get_32() - event_time;

	if (latency > context->max_input_latency_ms) {
		context->max_input_latency_ms = latency;
	}
	if (latency > INPUT_RESPONSE_REQUIREMENT_MS) {
		context->latency_violations++;
	}
	if (latency > INPUT_RESPONSE_REQUIREMENT_MS &&
	    app_should_log_failure(context->latency_violations)) {
		LOG_WRN("input response requirement exceeded: %u ms > %u ms", latency,
		        INPUT_RESPONSE_REQUIREMENT_MS);
	}
}

static void handle_button(struct app_context *context, const struct app_event *event)
{
	bool was_pressed = context->runtime.button_pressed;
	int rc;

	context->runtime.button_pressed = event->data.button_pressed;
	if (!event->data.button_pressed || was_pressed) {
		return;
	}
	context->runtime.led_on = !context->runtime.led_on;
	rc = gpio_inputs_set_led(context->runtime.led_on);
	if (rc != 0) {
		context->gpio_errors++;
		disable_after_policy(context, COMP_BUTTON_LED, DRIVER_OP_GPIO_OUTPUT,
		                     context->gpio_errors, rc);
	} else {
		context->gpio_errors = 0U;
	}
}

static void handle_event(struct app_context *context, const struct app_event *event)
{
	record_input_latency(context, event->timestamp_ms);
	switch (event->type) {
	case APP_EVENT_BUTTON:
		if (peripherals_operational(&context->peripherals, COMP_BUTTON_LED)) {
			handle_button(context, event);
		}
		break;
	case APP_EVENT_SWITCH:
		if (peripherals_operational(&context->peripherals, COMP_SWITCH)) {
			context->runtime.switch_position = event->data.switch_position;
			peripherals_note_physical(&context->peripherals, COMP_SWITCH);
		}
		break;
	case APP_EVENT_TOUCH:
		if (!peripherals_operational(&context->peripherals, COMP_TOUCH)) {
			break;
		}
		if (!app_touch_transition(&context->runtime.touch, event->timestamp_ms,
		                          event->data.touch.x, event->data.touch.y,
		                          (uint8_t)display_touch_color_count())) {
			break;
		}
		peripherals_note_physical(&context->peripherals, COMP_TOUCH);
		if (peripherals_operational(&context->peripherals, COMP_DISPLAY)) {
			draw_color(context);
		} else {
			LOG_INF("touch at x=%d y=%d (display unavailable)", event->data.touch.x,
			        event->data.touch.y);
		}
		break;
	default:
		LOG_WRN("unknown application event: %d", event->type);
		break;
	}
}

static void start_available_features(struct app_context *context)
{
	int rc;

	gpio_inputs_get_initial(&context->runtime.button_pressed,
	                        &context->runtime.switch_position);
	if (peripherals_operational(&context->peripherals, COMP_BUTTON_LED)) {
		rc = gpio_inputs_start_button(GPIO_INT_EDGE_BOTH);
		if (rc != 0) {
			peripherals_disable(&context->peripherals, COMP_BUTTON_LED, rc);
		}
	}
	if (peripherals_operational(&context->peripherals, COMP_SWITCH)) {
		rc = gpio_inputs_start_switch(GPIO_INT_EDGE_BOTH);
		if (rc != 0) {
			peripherals_disable(&context->peripherals, COMP_SWITCH, rc);
		}
	}

	if (peripherals_operational(&context->peripherals, COMP_POTENTIOMETER)) {
		sample_potentiometer(context);
	} else if (peripherals_operational(&context->peripherals, COMP_BACKLIGHT)) {
		rc = analog_backlight_set_mv(APP_MAX_MILLIVOLTS);
		if (rc != 0) {
			peripherals_disable(&context->peripherals, COMP_BACKLIGHT, rc);
		}
		context->runtime.brightness_percent = 100U;
	}
	if (peripherals_operational(&context->peripherals, COMP_DISPLAY)) {
		draw_color(context);
	}

	context->runtime.features = app_degraded_features(context->peripherals.components);
	if ((context->runtime.features & APP_FEATURE_AUDIO_LOOPBACK) != 0U) {
		rc = audio_loopback_start();
		if (rc != 0) {
			LOG_ERR("audio loopback start failed; endpoints remain independently "
			        "usable: %d",
			        rc);
		}
	} else if (peripherals_operational(&context->peripherals, COMP_MICROPHONE) !=
	           peripherals_operational(&context->peripherals, COMP_DAC)) {
		LOG_WRN("audio loopback disabled: %s endpoint unavailable",
		        peripherals_operational(&context->peripherals, COMP_MICROPHONE) ? "output"
		                                                                        : "input");
	}
}

int main(void)
{
	struct app_context context = {0};
	struct app_event event;
	uint32_t next_analog;
	uint32_t next_status;
	size_t operational;

	LOG_INF("=== Stethoscope hardware bring-up ===");
	operational = peripherals_probe_all(&context.peripherals);
	peripherals_report(&context.peripherals);
	start_available_features(&context);

	next_analog = k_uptime_get_32() + ANALOG_PERIOD_MS;
	next_status = k_uptime_get_32();
	while (true) {
		uint32_t now;
		int rc = k_msgq_get(&app_event_queue, &event, K_MSEC(20));

		if (rc == 0) {
			handle_event(&context, &event);
		} else if (rc != -EAGAIN) {
			LOG_ERR("application event receive failed: %d", rc);
		}
		now = k_uptime_get_32();
		if ((int32_t)(now - next_analog) >= 0) {
			sample_potentiometer(&context);
			next_analog = now + ANALOG_PERIOD_MS;
		}
		if ((int32_t)(now - next_status) >= 0) {
			if (operational == 0U) {
				LOG_INF("no operational peripherals - check wiring and power, then "
				        "reset");
				next_status = now + IDLE_PERIOD_MS;
			} else {
				status_reporting_log(&context.peripherals, &context.runtime);
				LOG_INF("input-latency-max=%ums requirement<=%ums",
				        context.max_input_latency_ms,
				        INPUT_RESPONSE_REQUIREMENT_MS);
				next_status = now + STATUS_PERIOD_MS;
			}
		}
	}
	return 0;
}
