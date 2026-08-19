#include <errno.h>
#include <string.h>

#include <zephyr/ztest.h>

#include "app_logic.h"

ZTEST_SUITE(app_logic, NULL, NULL, NULL, NULL, NULL);

ZTEST(app_logic, test_probe_retry_and_state_transitions)
{
	struct app_probe_state state = { 0 };

	zassert_true(app_probe_record(&state, -EIO, 4));
	zassert_equal(state.attempts, 1);
	zassert_false(state.done);
	zassert_true(app_probe_record(&state, -EAGAIN, 4));
	zassert_true(app_probe_record(&state, -ENODEV, 4));
	zassert_false(app_probe_record(&state, 0, 4));
	zassert_true(state.done);
	zassert_true(state.success);
	zassert_equal(state.attempts, 4);

	memset(&state, 0, sizeof(state));
	zassert_true(app_probe_record(&state, -EIO, 2));
	zassert_false(app_probe_record(&state, -EIO, 2));
	zassert_true(state.done);
	zassert_false(state.success);
}

ZTEST(app_logic, test_degraded_mode_decisions)
{
	struct component_status status[COMP_COUNT] = { 0 };
	uint32_t features;

	status[COMP_BUTTON_LED].operational = true;
	status[COMP_DISPLAY].operational = true;
	status[COMP_MICROPHONE].operational = true;
	features = app_degraded_features(status);
	zassert_true((features & APP_FEATURE_BUTTON_LED) != 0U);
	zassert_true((features & APP_FEATURE_DISPLAY) != 0U);
	zassert_true((features & APP_FEATURE_AUDIO_LOOPBACK) == 0U);

	status[COMP_DAC].operational = true;
	features = app_degraded_features(status);
	zassert_true((features & APP_FEATURE_AUDIO_LOOPBACK) != 0U);
}

ZTEST(app_logic, test_switch_position_decoding)
{
	zassert_equal(app_switch_decode(1, 0, 0), 1);
	zassert_equal(app_switch_decode(0, 1, 0), 2);
	zassert_equal(app_switch_decode(0, 0, 1), 3);
	zassert_equal(app_switch_decode(0, 0, 0), 0);
	zassert_equal(app_switch_decode(1, 1, 0), -EINVAL);
	zassert_equal(app_switch_decode(-EIO, 0, 0), -EIO);
}

ZTEST(app_logic, test_brightness_conversion_boundaries)
{
	zassert_equal(app_brightness_pulse(1000, -1), 0);
	zassert_equal(app_brightness_pulse(1000, 0), 0);
	zassert_equal(app_brightness_pulse(1000, 1650), 500);
	zassert_equal(app_brightness_pulse(1000, 3300), 1000);
	zassert_equal(app_brightness_pulse(1000, 5000), 1000);
	zassert_equal(app_brightness_percent(-5), 0);
	zassert_equal(app_brightness_percent(1650), 50);
	zassert_equal(app_brightness_percent(4000), 100);
}

ZTEST(app_logic, test_touch_event_color_transitions)
{
	struct app_touch_state state = { 0 };

	zassert_true(app_touch_transition(&state, 1000, 12, 34, 7));
	zassert_equal(state.color_index, 1);
	zassert_equal(state.count, 1);
	zassert_false(app_touch_transition(&state, 1100, 20, 40, 7));
	zassert_equal(state.count, 1);
	zassert_true(app_touch_transition(&state, 1150, 20, 40, 7));
	zassert_equal(state.count, 2);
	zassert_equal(state.x, 20);
	zassert_equal(state.y, 40);
	state.color_index = 6;
	zassert_true(app_touch_transition(&state, 1300, 1, 2, 7));
	zassert_equal(state.color_index, 0);
}

ZTEST(app_logic, test_status_formatting_and_boundaries)
{
	struct app_status_snapshot status = {
		.show_button = true,
		.button_pressed = true,
		.led_on = false,
		.show_display = true,
		.color_name = "magenta",
		.show_audio = true,
		.audio_blocks = 123,
		.audio_errors = 4,
		.audio_peak = 55,
	};
	char full[192];
	char guarded[9];
	char one[1];

	zassert_true(app_format_status(full, sizeof(full), &status) > 0U);
	zassert_not_null(strstr(full, "btn=1 led=0"));
	zassert_not_null(strstr(full, "colour=magenta"));
	zassert_not_null(strstr(full, "audio blocks=123 errs=4 peak=55"));
	memset(guarded, 'X', sizeof(guarded));
	app_format_status(guarded, 8, &status);
	zassert_equal(guarded[7], '\0');
	zassert_equal(guarded[8], 'X');
	app_format_status(one, sizeof(one), &status);
	zassert_equal(one[0], '\0');
	zassert_equal(app_format_status(NULL, 0, &status), 0);
}

ZTEST(app_logic, test_driver_error_handling_decisions)
{
	zassert_equal(app_driver_error_action(DRIVER_OP_ADC_SAMPLE, 1),
		      DRIVER_ERROR_RETRY);
	zassert_equal(app_driver_error_action(DRIVER_OP_ADC_SAMPLE, 3),
		      DRIVER_ERROR_DISABLE_COMPONENT);
	zassert_equal(app_driver_error_action(DRIVER_OP_DISPLAY_WRITE, 2),
		      DRIVER_ERROR_DISABLE_COMPONENT);
	zassert_equal(app_driver_error_action(DRIVER_OP_I2S_TRANSFER, 1),
		      DRIVER_ERROR_DEGRADE);
	zassert_equal(app_driver_error_action(DRIVER_OP_I2S_CONTROL, 3),
		      DRIVER_ERROR_DISABLE_COMPONENT);
	zassert_true(app_should_log_failure(1));
	zassert_true(app_should_log_failure(8));
	zassert_false(app_should_log_failure(3));
}
