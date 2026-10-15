#include <errno.h>

#include <zephyr/device.h>
#include <zephyr/drivers/led_strip.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(devkit_led_test);

int devkit_led_test_run(void)
{
	const struct device *led = DEVICE_DT_GET(DT_ALIAS(devkit_led));
	bool on = true;

	if (!device_is_ready(led)) {
		LOG_ERR("Devkit LED is not ready");
		return -ENODEV;
	}

	LOG_INF("Devkit LED test: one second green, one second off");
	while (true) {
		struct led_rgb pixel = {.g = on ? 16 : 0};
		int err = led_strip_update_rgb(led, &pixel, 1);

		if (err != 0) {
			LOG_ERR("Devkit LED update failed: %d", err);
			return err;
		}
		on = !on;
		k_sleep(K_SECONDS(1));
	}
}
