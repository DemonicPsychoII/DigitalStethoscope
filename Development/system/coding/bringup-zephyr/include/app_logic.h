#ifndef STETHO_APP_LOGIC_H
#define STETHO_APP_LOGIC_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "app_types.h"

#define APP_MAX_MILLIVOLTS 3300
#define APP_TOUCH_DEBOUNCE_MS 150U

struct app_probe_state {
	uint8_t attempts;
	bool done;
	bool success;
	int last_error;
};

enum app_feature {
	APP_FEATURE_BUTTON_LED = 1U << 0,
	APP_FEATURE_SWITCH = 1U << 1,
	APP_FEATURE_BACKLIGHT = 1U << 2,
	APP_FEATURE_DISPLAY = 1U << 3,
	APP_FEATURE_TOUCH = 1U << 4,
	APP_FEATURE_AUDIO_LOOPBACK = 1U << 5,
};

enum driver_operation {
	DRIVER_OP_ADC_SAMPLE,
	DRIVER_OP_BACKLIGHT_PWM,
	DRIVER_OP_DISPLAY_WRITE,
	DRIVER_OP_GPIO_OUTPUT,
	DRIVER_OP_I2S_TRANSFER,
	DRIVER_OP_I2S_CONTROL,
};

enum driver_error_action {
	DRIVER_ERROR_RETRY,
	DRIVER_ERROR_DEGRADE,
	DRIVER_ERROR_DISABLE_COMPONENT,
	DRIVER_ERROR_CONTROLLED_SHUTDOWN,
};

struct app_touch_state {
	bool initialized;
	uint32_t last_timestamp_ms;
	uint32_t count;
	int16_t x;
	int16_t y;
	uint8_t color_index;
};

struct app_status_snapshot {
	bool show_button;
	bool button_pressed;
	bool led_on;
	bool show_switch;
	int switch_position;
	bool show_potentiometer;
	int potentiometer_mv;
	bool show_backlight;
	unsigned int brightness_percent;
	bool show_display;
	const char *color_name;
	bool show_touch;
	uint32_t touch_count;
	int16_t touch_x;
	int16_t touch_y;
	bool show_audio;
	uint32_t audio_blocks;
	uint32_t audio_errors;
	int32_t audio_peak;
};

bool app_probe_record(struct app_probe_state *state, int result, uint8_t max_attempts);
uint32_t app_degraded_features(const struct component_status status[COMP_COUNT]);
int app_switch_decode(int position_1, int position_2, int position_3);
uint32_t app_brightness_pulse(uint32_t period, int millivolts);
unsigned int app_brightness_percent(int millivolts);
bool app_touch_transition(struct app_touch_state *state, uint32_t timestamp_ms,
			  int16_t x, int16_t y, uint8_t color_count);
enum driver_error_action app_driver_error_action(enum driver_operation operation,
						  unsigned int consecutive_errors);
bool app_should_log_failure(uint32_t failure_count);
size_t app_format_status(char *buffer, size_t capacity,
			 const struct app_status_snapshot *status);

#endif
