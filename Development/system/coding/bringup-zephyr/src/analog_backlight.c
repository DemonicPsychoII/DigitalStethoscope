#include "analog_backlight.h"

#include <errno.h>

#include <zephyr/drivers/adc.h>
#include <zephyr/drivers/pwm.h>
#include <zephyr/logging/log.h>

#include "app_logic.h"

LOG_MODULE_REGISTER(analog_backlight, LOG_LEVEL_INF);

#define ZUSER DT_PATH(zephyr_user)

static const struct adc_dt_spec potentiometer = ADC_DT_SPEC_GET(ZUSER);
static const struct pwm_dt_spec backlight = PWM_DT_SPEC_GET(ZUSER);

int analog_backlight_read_mv(int *millivolts)
{
	int16_t sample = 0;
	int32_t converted;
	int rc;
	struct adc_sequence sequence = {
		.buffer = &sample,
		.buffer_size = sizeof(sample),
	};

	if (millivolts == NULL) {
		return -EINVAL;
	}
	rc = adc_sequence_init_dt(&potentiometer, &sequence);
	if (rc != 0) {
		LOG_ERR("ADC sequence init failed: %d", rc);
		return rc;
	}
	rc = adc_read_dt(&potentiometer, &sequence);
	if (rc != 0) {
		LOG_ERR("potentiometer ADC read failed: %d", rc);
		return rc;
	}
	converted = sample;
	rc = adc_raw_to_millivolts_dt(&potentiometer, &converted);
	if (rc != 0) {
		LOG_ERR("potentiometer raw-to-mV conversion failed (raw=%d): %d", sample, rc);
		return rc;
	}
	*millivolts = (int)converted;
	return 0;
}

int analog_backlight_probe_potentiometer(void)
{
	int sample_mv;
	int rc;

	if (!adc_is_ready_dt(&potentiometer)) {
		return -ENODEV;
	}
	rc = adc_channel_setup_dt(&potentiometer);
	if (rc != 0) {
		LOG_ERR("potentiometer ADC channel setup failed: %d", rc);
		return rc;
	}
	return analog_backlight_read_mv(&sample_mv);
}

int analog_backlight_set_mv(int millivolts)
{
	uint32_t pulse = app_brightness_pulse(backlight.period, millivolts);
	int rc = pwm_set_pulse_dt(&backlight, pulse);

	if (rc != 0) {
		LOG_ERR("backlight PWM write failed (mv=%d pulse=%u period=%u): %d",
			millivolts, pulse, backlight.period, rc);
	}
	return rc;
}

int analog_backlight_probe_pwm(void)
{
	if (!pwm_is_ready_dt(&backlight)) {
		return -ENODEV;
	}
	return analog_backlight_set_mv(APP_MAX_MILLIVOLTS);
}
