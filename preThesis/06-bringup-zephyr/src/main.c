/* Main owns peripheral orchestration; audio, display and network have workers. */
#include "analog_backlight.h"
#include "app_logic.h"
#include "app_types.h"
#include "audio_loopback.h"
#include "display_touch.h"
#include "gpio_inputs.h"
#include "peripherals.h"
#include "status_reporting.h"
#include "stetho_build_id.h"
#include "stetho_control.h"
#include <errno.h>
#include <stdlib.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(bringup, LOG_LEVEL_INF);
#define INPUT_RESPONSE_REQUIREMENT_MS 35U
K_MSGQ_DEFINE(app_event_queue, sizeof(struct app_event), 16, 4);
struct app_context {
	struct peripheral_registry peripherals;
	struct runtime_state runtime;
	unsigned int adc_errors, pwm_errors, gpio_errors, latency_violations;
	uint32_t max_input_latency_ms;
};
static void disable_after_policy(struct app_context *c, enum component_id component,
                                 enum driver_operation operation, unsigned int failures, int error)
{
	if (app_driver_error_action(operation, failures) == DRIVER_ERROR_DISABLE_COMPONENT) {
		peripherals_disable(&c->peripherals, component, error);
		c->runtime.features = app_degraded_features(c->peripherals.components);
	}
}
static void sample_analog(struct app_context *c)
{
	struct stetho_settings settings;
	stetho_settings_get(&settings);
	if (peripherals_operational(&c->peripherals, COMP_POTENTIOMETER)) {
		int mv;
		int rc = analog_backlight_read_mv(&mv);
		if (rc)
			disable_after_policy(c, COMP_POTENTIOMETER, DRIVER_OP_ADC_SAMPLE,
			                     ++c->adc_errors, rc);
		else {
			c->adc_errors = 0;
			c->runtime.potentiometer_mv = mv;
			if (settings.pot && !settings.diagnostics) {
				unsigned int volume = (unsigned int)CLAMP(
				        mv * 100 / CONFIG_STETHO_POT_MAX_MV, 0, 100);
				/* Suppress ADC jitter; the audio worker ramps the accepted gain. */
				if (volume == 0 || volume == 100 ||
				    abs((int)volume - (int)settings.volume) >= 2)
					stetho_setting_set("volume", volume);
			}
		}
	}
	if (peripherals_operational(&c->peripherals, COMP_BACKLIGHT)) {
		int mv = settings.diagnostics && peripherals_operational(&c->peripherals,
		                                                         COMP_POTENTIOMETER)
		                 ? c->runtime.potentiometer_mv
		                 : (int)settings.brightness * APP_MAX_MILLIVOLTS / 100;
		int rc = analog_backlight_set_mv(mv);
		if (rc)
			disable_after_policy(c, COMP_BACKLIGHT, DRIVER_OP_BACKLIGHT_PWM,
			                     ++c->pwm_errors, rc);
		else
			c->pwm_errors = 0;
		c->runtime.brightness_percent = app_brightness_percent(mv);
	}
}
static void handle_event(struct app_context *c, const struct app_event *event)
{
	uint32_t latency = k_uptime_get_32() - event->timestamp_ms;
	c->max_input_latency_ms = MAX(c->max_input_latency_ms, latency);
	if (latency > INPUT_RESPONSE_REQUIREMENT_MS &&
	    app_should_log_failure(++c->latency_violations))
		LOG_WRN("Input handler latency %u ms", latency);
	struct stetho_settings settings;
	stetho_settings_get(&settings);
	switch (event->type) {
	case APP_EVENT_BUTTON:
		if (peripherals_operational(&c->peripherals, COMP_BUTTON_LED)) {
			bool previous = c->runtime.button_pressed;
			c->runtime.button_pressed = event->data.button_pressed;
			if (event->data.button_pressed && !previous) {
				if (settings.diagnostics)
					c->runtime.led_on = !c->runtime.led_on;
				else {
					struct audio_snapshot audio;
					audio_loopback_snapshot(&audio);
					stetho_action_request(audio.capturing || audio.replaying
					                              ? ACTION_LIVE
					                              : ACTION_CAPTURE);
					c->runtime.led_on = !(audio.capturing || audio.replaying);
				}
				int rc = gpio_inputs_set_led(c->runtime.led_on);
				if (rc)
					disable_after_policy(c, COMP_BUTTON_LED,
					                     DRIVER_OP_GPIO_OUTPUT,
					                     ++c->gpio_errors, rc);
				else
					c->gpio_errors = 0;
			}
		}
		break;
	case APP_EVENT_SWITCH:
		if (peripherals_operational(&c->peripherals, COMP_SWITCH)) {
			c->runtime.switch_position = event->data.switch_position;
			if (event->data.switch_position >= 1 && event->data.switch_position <= 3)
				stetho_setting_set("filter", event->data.switch_position - 1);
			peripherals_note_physical(&c->peripherals, COMP_SWITCH);
		}
		break;
	case APP_EVENT_SPEED:
		if (event->data.switch_position >= 1 && event->data.switch_position <= 3)
			stetho_setting_set("speed", event->data.switch_position == 1   ? 100
			                            : event->data.switch_position == 2 ? 75
			                                                               : 50);
		break;
	case APP_EVENT_TOUCH:
		if (peripherals_operational(&c->peripherals, COMP_TOUCH) &&
		    app_touch_transition(&c->runtime.touch, event->timestamp_ms,
		                         event->data.touch.x, event->data.touch.y,
		                         (uint8_t)display_touch_color_count())) {
			peripherals_note_physical(&c->peripherals, COMP_TOUCH);
			if (settings.diagnostics) {
				int rc = display_touch_show_color(c->runtime.touch.color_index);
				if (rc)
					LOG_WRN("Color request failed: %d", rc);
			} else
				stetho_control_touch(event->data.touch.x, event->data.touch.y);
		}
		break;
	default:
		break;
	}
}
static void start_available_features(struct app_context *c)
{
	gpio_inputs_get_initial(&c->runtime.button_pressed, &c->runtime.switch_position);
	if (c->runtime.switch_position >= 1 && c->runtime.switch_position <= 3)
		stetho_setting_set("filter", c->runtime.switch_position - 1);
	if (peripherals_operational(&c->peripherals, COMP_BUTTON_LED)) {
		int rc = gpio_inputs_start_button(GPIO_INT_EDGE_BOTH);
		if (rc)
			peripherals_disable(&c->peripherals, COMP_BUTTON_LED, rc);
	}
	if (peripherals_operational(&c->peripherals, COMP_SWITCH)) {
		int rc = gpio_inputs_start_switch(GPIO_INT_EDGE_BOTH);
		if (rc)
			peripherals_disable(&c->peripherals, COMP_SWITCH, rc);
	}
	int rc = gpio_inputs_start_speed();
	if (rc)
		LOG_WRN("Optional speed switch disabled: %d", rc);
	c->runtime.features = app_degraded_features(c->peripherals.components);
	/* DAC test sources remain usable even if the microphone probe fails. */
	if (peripherals_operational(&c->peripherals, COMP_DAC)) {
		rc = audio_loopback_start();
		if (rc)
			LOG_ERR("Audio start failed: %d", rc);
	}
}
int main(void)
{
	struct app_context c = {0};
	struct app_event event;
	/* First console output after Zephyr's banner, so a flashed board names its build. */
	printk("Digital Stethoscope firmware %s\n", STETHO_BUILD_ID);
	LOG_INF("=== Stethoscope integrated evaluation ===");
	peripherals_probe_all(&c.peripherals);
	peripherals_report(&c.peripherals);
	start_available_features(&c);
	uint32_t next_analog = 0, next_status = 0;
	while (true) {
		int rc = k_msgq_get(&app_event_queue, &event, K_MSEC(5));
		if (!rc)
			handle_event(&c, &event);
		else if (rc != -EAGAIN)
			LOG_ERR("Event receive: %d", rc);
		uint32_t now = k_uptime_get_32();
		if ((int32_t)(now - next_analog) >= 0) {
			sample_analog(&c);
			next_analog = now + 100;
		}
		if ((int32_t)(now - next_status) >= 0) {
			status_reporting_log(&c.peripherals, &c.runtime);
			LOG_INF("input-latency-max=%ums requirement<=%ums", c.max_input_latency_ms,
			        INPUT_RESPONSE_REQUIREMENT_MS);
			struct stetho_settings settings;
			stetho_settings_get(&settings);
			if (!settings.diagnostics &&
			    peripherals_operational(&c.peripherals, COMP_BUTTON_LED)) {
				struct audio_snapshot audio;
				audio_loopback_snapshot(&audio);
				c.runtime.led_on = audio.capturing || audio.replaying;
				rc = gpio_inputs_set_led(c.runtime.led_on);
				if (rc)
					disable_after_policy(&c, COMP_BUTTON_LED,
					                     DRIVER_OP_GPIO_OUTPUT, ++c.gpio_errors,
					                     rc);
				else
					c.gpio_errors = 0;
			}
			next_status = now + 2000;
		}
	}
	return 0;
}
