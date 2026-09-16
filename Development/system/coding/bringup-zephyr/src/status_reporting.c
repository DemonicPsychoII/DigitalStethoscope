#include "status_reporting.h"

#include <zephyr/logging/log.h>

#include "audio_loopback.h"
#include "display_touch.h"
#include "stetho_control.h"

LOG_MODULE_REGISTER(status_reporting, LOG_LEVEL_INF);

void status_reporting_log(const struct peripheral_registry *registry,
                          const struct runtime_state *runtime)
{
	struct stetho_settings settings;
	stetho_settings_get(&settings);
	if (!settings.diagnostics) {
		struct audio_snapshot audio;
		audio_loopback_snapshot(&audio);
		LOG_INF("audio=%u source=%u filter=%u analysis=%u volume=%u speed=%u "
		        "bpm-valid=%u bpm=%u.%u quality=%u clips=%u errors=%u touch=%u@%d,%d",
		        audio.running, audio.source, settings.filter, settings.analysis,
		        settings.volume, settings.speed, audio.bpm_valid, audio.bpm_tenths / 10,
		        audio.bpm_tenths % 10, audio.quality_percent, audio.output_clips,
		        audio.errors, runtime->touch.count, runtime->touch.x, runtime->touch.y);
		return;
	}
	char buffer[192];
	struct audio_snapshot audio;
	struct app_status_snapshot status = {
	        .show_button = peripherals_operational(registry, COMP_BUTTON_LED),
	        .button_pressed = runtime->button_pressed,
	        .led_on = runtime->led_on,
	        .show_switch = peripherals_operational(registry, COMP_SWITCH),
	        .switch_position = runtime->switch_position,
	        .show_potentiometer = peripherals_operational(registry, COMP_POTENTIOMETER),
	        .potentiometer_mv = runtime->potentiometer_mv,
	        .show_backlight = peripherals_operational(registry, COMP_BACKLIGHT),
	        .brightness_percent = runtime->brightness_percent,
	        .show_display = peripherals_operational(registry, COMP_DISPLAY),
	        .color_name = display_touch_color_name(runtime->touch.color_index),
	        .show_touch = peripherals_operational(registry, COMP_TOUCH),
	        .touch_count = runtime->touch.count,
	        .touch_x = runtime->touch.x,
	        .touch_y = runtime->touch.y,
	};

	audio_loopback_snapshot(&audio);
	status.show_audio = audio.running;
	status.audio_blocks = audio.blocks;
	status.audio_errors = audio.errors;
	status.audio_peak = audio.peak;
	app_format_status(buffer, sizeof(buffer), &status);
	LOG_INF("%s", buffer);
}
