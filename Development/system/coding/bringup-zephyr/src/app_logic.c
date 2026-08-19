#include "app_logic.h"

#include <errno.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>

bool app_probe_record(struct app_probe_state *state, int result, uint8_t max_attempts)
{
	if (state == NULL || state->done || max_attempts == 0U) {
		return false;
	}

	state->attempts++;
	state->last_error = result;
	state->success = result == 0;
	state->done = state->success || state->attempts >= max_attempts;
	return !state->done;
}

uint32_t app_degraded_features(const struct component_status status[COMP_COUNT])
{
	uint32_t features = 0U;

	if (status[COMP_BUTTON_LED].operational) {
		features |= APP_FEATURE_BUTTON_LED;
	}
	if (status[COMP_SWITCH].operational) {
		features |= APP_FEATURE_SWITCH;
	}
	if (status[COMP_BACKLIGHT].operational) {
		features |= APP_FEATURE_BACKLIGHT;
	}
	if (status[COMP_DISPLAY].operational) {
		features |= APP_FEATURE_DISPLAY;
	}
	if (status[COMP_TOUCH].operational) {
		features |= APP_FEATURE_TOUCH;
	}
	if (status[COMP_MICROPHONE].operational && status[COMP_DAC].operational) {
		features |= APP_FEATURE_AUDIO_LOOPBACK;
	}
	return features;
}

int app_switch_decode(int position_1, int position_2, int position_3)
{
	const int active[] = {position_1 > 0, position_2 > 0, position_3 > 0};
	int selected = 0;
	int count = 0;

	if (position_1 < 0 || position_2 < 0 || position_3 < 0) {
		return -EIO;
	}
	for (size_t i = 0; i < sizeof(active) / sizeof(active[0]); i++) {
		if (active[i] != 0) {
			selected = (int)i + 1;
			count++;
		}
	}
	return count > 1 ? -EINVAL : selected;
}

uint32_t app_brightness_pulse(uint32_t period, int millivolts)
{
	if (millivolts <= 0) {
		return 0U;
	}
	if (millivolts >= APP_MAX_MILLIVOLTS) {
		return period;
	}
	return (uint32_t)(((uint64_t)period * (uint32_t)millivolts) / APP_MAX_MILLIVOLTS);
}

unsigned int app_brightness_percent(int millivolts)
{
	if (millivolts <= 0) {
		return 0U;
	}
	if (millivolts >= APP_MAX_MILLIVOLTS) {
		return 100U;
	}
	return (unsigned int)(((uint32_t)millivolts * 100U) / APP_MAX_MILLIVOLTS);
}

bool app_touch_transition(struct app_touch_state *state, uint32_t timestamp_ms, int16_t x,
                          int16_t y, uint8_t color_count)
{
	if (state == NULL || color_count == 0U) {
		return false;
	}
	if (state->initialized &&
	    (uint32_t)(timestamp_ms - state->last_timestamp_ms) < APP_TOUCH_DEBOUNCE_MS) {
		return false;
	}

	state->initialized = true;
	state->last_timestamp_ms = timestamp_ms;
	state->count++;
	state->x = x;
	state->y = y;
	state->color_index = (uint8_t)((state->color_index + 1U) % color_count);
	return true;
}

enum driver_error_action app_driver_error_action(enum driver_operation operation,
                                                 unsigned int consecutive_errors)
{
	if (consecutive_errors == 0U) {
		return DRIVER_ERROR_RETRY;
	}

	switch (operation) {
	case DRIVER_OP_ADC_SAMPLE:
	case DRIVER_OP_BACKLIGHT_PWM:
	case DRIVER_OP_GPIO_OUTPUT:
		return consecutive_errors < 3U ? DRIVER_ERROR_RETRY
		                               : DRIVER_ERROR_DISABLE_COMPONENT;
	case DRIVER_OP_DISPLAY_WRITE:
		return consecutive_errors < 2U ? DRIVER_ERROR_RETRY
		                               : DRIVER_ERROR_DISABLE_COMPONENT;
	case DRIVER_OP_I2S_TRANSFER:
	case DRIVER_OP_I2S_CONTROL:
		return consecutive_errors < 3U ? DRIVER_ERROR_DEGRADE
		                               : DRIVER_ERROR_DISABLE_COMPONENT;
	default:
		return DRIVER_ERROR_CONTROLLED_SHUTDOWN;
	}
}

bool app_should_log_failure(uint32_t failure_count)
{
	return failure_count != 0U && (failure_count & (failure_count - 1U)) == 0U;
}

static void append_text(char *buffer, size_t capacity, size_t *used, const char *format, ...)
{
	va_list args;
	int result;

	if (capacity == 0U || *used >= capacity) {
		return;
	}
	va_start(args, format);
	result = vsnprintf(buffer + *used, capacity - *used, format, args);
	va_end(args);
	if (result < 0) {
		buffer[*used] = '\0';
		return;
	}
	if ((size_t)result >= capacity - *used) {
		*used = capacity - 1U;
		buffer[*used] = '\0';
		return;
	}
	*used += (size_t)result;
}

size_t app_format_status(char *buffer, size_t capacity, const struct app_status_snapshot *status)
{
	size_t used = 0U;

	if (buffer == NULL || capacity == 0U || status == NULL) {
		return 0U;
	}
	buffer[0] = '\0';
	if (status->show_button) {
		append_text(buffer, capacity, &used, "btn=%d led=%d | ", status->button_pressed,
		            status->led_on);
	}
	if (status->show_switch) {
		append_text(buffer, capacity, &used, "sw=%d | ", status->switch_position);
	}
	if (status->show_potentiometer) {
		append_text(buffer, capacity, &used, "poti=%dmV | ", status->potentiometer_mv);
	}
	if (status->show_backlight) {
		append_text(buffer, capacity, &used, "backlight=%u%% | ",
		            status->brightness_percent);
	}
	if (status->show_display) {
		append_text(buffer, capacity, &used, "colour=%s | ",
		            status->color_name != NULL ? status->color_name : "unknown");
	}
	if (status->show_touch) {
		append_text(buffer, capacity, &used, "touch=%u@%d,%d | ", status->touch_count,
		            status->touch_x, status->touch_y);
	}
	if (status->show_audio) {
		append_text(buffer, capacity, &used, "audio blocks=%u errs=%u peak=%d | ",
		            status->audio_blocks, status->audio_errors, status->audio_peak);
	}
	return used;
}
