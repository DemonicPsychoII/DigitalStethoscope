#include "stetho_control.h"
#include <errno.h>
#include <string.h>
#include <zephyr/kernel.h>
static struct stetho_settings settings = {
        .filter = FILTER_RAW,
        .analysis = FILTER_BPM,
        .source = SOURCE_MIC,
        .speed = 100,
        .volume = 0,
        .brightness = 80,
        .test_bpm = 72,
        .heart = true,
        .pot = true,
};
K_MUTEX_DEFINE(settings_lock);
void stetho_settings_get(struct stetho_settings *out)
{
	k_mutex_lock(&settings_lock, K_FOREVER);
	*out = settings;
	k_mutex_unlock(&settings_lock);
}
int stetho_setting_set(const char *name, unsigned int value)
{
	int rc = 0;
	k_mutex_lock(&settings_lock, K_FOREVER);
	if (!strcmp(name, "filter") && value < FILTER_COUNT)
		settings.filter = value;
	else if (!strcmp(name, "analysis") && value < FILTER_COUNT)
		settings.analysis = value;
	else if (!strcmp(name, "source") && value <= SOURCE_FIXTURE)
		settings.source = value;
	else if (!strcmp(name, "speed") && (value == 50 || value == 75 || value == 100))
		settings.speed = value;
	else if (!strcmp(name, "volume") && value <= 100)
		settings.volume = value;
	else if (!strcmp(name, "brightness") && value <= 100)
		settings.brightness = value;
	else if (!strcmp(name, "bpm") && value >= 30 && value <= 200)
		settings.test_bpm = value;
	else if (!strcmp(name, "point") && value < 5)
		settings.point = value;
	else if (!strcmp(name, "heart") && value <= 1)
		settings.heart = value;
	else if (!strcmp(name, "pot") && value <= 1)
		settings.pot = value;
	else if (!strcmp(name, "diagnostics") && value <= 1)
		settings.diagnostics = value;
	else
		rc = -EINVAL;
	k_mutex_unlock(&settings_lock);
	return rc;
}
void stetho_action_request(enum stetho_action action)
{
	k_mutex_lock(&settings_lock, K_FOREVER);
	settings.action = action;
	settings.action_id++;
	k_mutex_unlock(&settings_lock);
}
void stetho_control_touch(int x, int y)
{
	struct stetho_settings s;
	stetho_settings_get(&s);
	/* Bottom four rows of the 240x320 dashboard, matching their labels. */
	if (y >= 192 && y < 224) {
		if (x < 120)
			stetho_setting_set("filter", (s.filter + 1) % FILTER_COUNT);
		else
			stetho_setting_set("speed", s.speed == 100 ? 75 : s.speed == 75 ? 50 : 100);
	} else if (y >= 224 && y < 256) {
		stetho_action_request(x < 120 ? ACTION_CAPTURE : ACTION_REPLAY);
	} else if (y >= 256 && y < 288) {
		if (x < 120)
			stetho_action_request(ACTION_LIVE);
		else
			stetho_setting_set("heart", !s.heart);
	} else if (y >= 288) {
		if (x < 120)
			stetho_setting_set("point", (s.point + 1) % 5);
		else
			stetho_setting_set("brightness",
			                   s.brightness >= 100 ? 20 : s.brightness + 20);
	}
}
