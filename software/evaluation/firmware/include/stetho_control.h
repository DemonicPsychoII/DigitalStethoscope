#ifndef STETHO_CONTROL_H
#define STETHO_CONTROL_H
#include "stetho_dsp.h"
enum stetho_source { SOURCE_MIC, SOURCE_TONE, SOURCE_HEART, SOURCE_FIXTURE };
enum stetho_action { ACTION_NONE, ACTION_CAPTURE, ACTION_REPLAY, ACTION_LIVE, ACTION_RESTART };
struct stetho_settings {
	enum stetho_filter filter, analysis;
	enum stetho_source source;
	unsigned int speed, volume, brightness, test_bpm, point;
	bool heart, diagnostics, pot;
	uint32_t action_id;
	enum stetho_action action;
};
void stetho_settings_get(struct stetho_settings *settings);
int stetho_setting_set(const char *name, unsigned int value);
void stetho_action_request(enum stetho_action action);
void stetho_control_touch(int x, int y);
#endif
