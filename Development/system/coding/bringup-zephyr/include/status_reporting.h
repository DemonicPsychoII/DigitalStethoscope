#ifndef STETHO_STATUS_REPORTING_H
#define STETHO_STATUS_REPORTING_H

#include <stdbool.h>
#include <stdint.h>

#include "app_logic.h"
#include "peripherals.h"

/* Written only by main; callbacks and the audio thread publish messages/snapshots. */
struct runtime_state {
	uint32_t features;
	bool button_pressed;
	bool led_on;
	int switch_position;
	int potentiometer_mv;
	unsigned int brightness_percent;
	struct app_touch_state touch;
};

void status_reporting_log(const struct peripheral_registry *registry,
                          const struct runtime_state *runtime);

#endif
