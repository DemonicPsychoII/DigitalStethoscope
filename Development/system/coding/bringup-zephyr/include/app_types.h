#ifndef STETHO_APP_TYPES_H
#define STETHO_APP_TYPES_H

#include <stdbool.h>
#include <stdint.h>

enum component_id {
	COMP_BUTTON_LED,
	COMP_SWITCH,
	COMP_POTENTIOMETER,
	COMP_BACKLIGHT,
	COMP_DISPLAY,
	COMP_TOUCH,
	COMP_MICROPHONE,
	COMP_DAC,
	COMP_COUNT,
};

/* Evidence levels deliberately separate driver readiness from physical proof. */
enum presence_evidence {
	PRESENCE_NOT_READY,
	PRESENCE_CONTROLLER_READY,
	PRESENCE_TRANSFER_ACCEPTED,
	PRESENCE_PHYSICAL_VERIFIED,
};

struct component_status {
	bool operational;
	enum presence_evidence evidence;
	int error;
	uint8_t attempts;
};

enum app_event_type {
	APP_EVENT_BUTTON,
	APP_EVENT_SWITCH,
	APP_EVENT_TOUCH,
	APP_EVENT_SPEED,
};

struct app_event {
	enum app_event_type type;
	uint32_t timestamp_ms;
	union {
		bool button_pressed;
		int switch_position;
		struct {
			int16_t x;
			int16_t y;
		} touch;
	} data;
};

#endif
