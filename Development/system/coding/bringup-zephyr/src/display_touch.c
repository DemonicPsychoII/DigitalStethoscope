#include "display_touch.h"

#include <errno.h>

#include <zephyr/device.h>
#include <zephyr/drivers/display.h>
#include <zephyr/input/input.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/sys/util.h>

#include "app_events.h"
#include "app_types.h"

LOG_MODULE_REGISTER(display_touch, LOG_LEVEL_INF);

#define SCREEN_WIDTH 240
#define SCREEN_HEIGHT 320
#define DRAW_ROWS 8
#define RGB565(red, green, blue)                                                                   \
	((uint16_t)((((red) & 0xF8) << 8) | (((green) & 0xFC) << 3) | ((blue) >> 3)))

static const struct device *const display = DEVICE_DT_GET(DT_CHOSEN(zephyr_display));
static const struct {
	const char *name;
	uint16_t rgb565;
} palette[] = {
        {"red", RGB565(255, 0, 0)},       {"green", RGB565(0, 255, 0)},
        {"blue", RGB565(0, 0, 255)},      {"yellow", RGB565(255, 255, 0)},
        {"magenta", RGB565(255, 0, 255)}, {"cyan", RGB565(0, 255, 255)},
        {"white", RGB565(255, 255, 255)},
};

static uint16_t draw_buffer[SCREEN_WIDTH * DRAW_ROWS];
static atomic_t touch_x;
static atomic_t touch_y;
static atomic_t dropped_touch_events;

#if DT_NODE_HAS_STATUS_OKAY(DT_NODELABEL(touchscreen))
static void touch_callback(struct input_event *event, void *user_data)
{
	struct app_event app_event = {
	        .type = APP_EVENT_TOUCH,
	};

	ARG_UNUSED(user_data);
	switch (event->code) {
	case INPUT_ABS_X:
		atomic_set(&touch_x, event->value);
		break;
	case INPUT_ABS_Y:
		atomic_set(&touch_y, event->value);
		break;
	case INPUT_BTN_TOUCH:
		if (event->value == 0) {
			break;
		}
		app_event.timestamp_ms = k_uptime_get_32();
		app_event.data.touch.x = (int16_t)atomic_get(&touch_x);
		app_event.data.touch.y = (int16_t)atomic_get(&touch_y);
		if (k_msgq_put(&app_event_queue, &app_event, K_NO_WAIT) != 0) {
			atomic_inc(&dropped_touch_events);
		}
		break;
	default:
		break;
	}
}
INPUT_CALLBACK_DEFINE(DEVICE_DT_GET(DT_NODELABEL(touchscreen)), touch_callback, NULL);
#endif

size_t display_touch_color_count(void) { return ARRAY_SIZE(palette); }

const char *display_touch_color_name(uint8_t color_index)
{
	return palette[color_index % ARRAY_SIZE(palette)].name;
}

int display_touch_probe_display(void)
{
	struct display_capabilities capabilities;
	int rc;

	if (!device_is_ready(display)) {
		return -ENODEV;
	}
	display_get_capabilities(display, &capabilities);
	if (capabilities.x_resolution != SCREEN_WIDTH ||
	    capabilities.y_resolution != SCREEN_HEIGHT) {
		LOG_ERR("unexpected display geometry %ux%u", capabilities.x_resolution,
		        capabilities.y_resolution);
		return -EINVAL;
	}
	rc = display_blanking_off(display);
	if (rc != 0 && rc != -ENOSYS) {
		LOG_ERR("display blanking-off command failed: %d", rc);
		return rc;
	}
	return 0;
}

int display_touch_probe_touch(void)
{
#if DT_NODE_HAS_STATUS_OKAY(DT_NODELABEL(touchscreen))
	return device_is_ready(DEVICE_DT_GET(DT_NODELABEL(touchscreen))) ? 0 : -ENODEV;
#else
	return -ENODEV;
#endif
}

int display_touch_show_color(uint8_t color_index)
{
	const uint16_t color = palette[color_index % ARRAY_SIZE(palette)].rgb565;
	struct display_buffer_descriptor descriptor = {
	        .buf_size = sizeof(draw_buffer),
	        .width = SCREEN_WIDTH,
	        .height = DRAW_ROWS,
	        .pitch = SCREEN_WIDTH,
	};
	int rc;

	for (size_t i = 0; i < ARRAY_SIZE(draw_buffer); i++) {
		draw_buffer[i] = color;
	}
	for (uint16_t y = 0U; y < SCREEN_HEIGHT; y += DRAW_ROWS) {
		rc = display_write(display, 0, y, &descriptor, draw_buffer);
		if (rc != 0) {
			LOG_ERR("display write failed (color=%s y=%u rows=%u): %d",
			        display_touch_color_name(color_index), y, DRAW_ROWS, rc);
			return rc;
		}
		/* Limit each non-preemptible SPI transaction to roughly 3.1 ms at 10 MHz. */
		k_yield();
	}
	LOG_INF("display colour -> %s", display_touch_color_name(color_index));
	return 0;
}
