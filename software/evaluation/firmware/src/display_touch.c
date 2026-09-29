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
#include "audio_loopback.h"
#include "stetho_control.h"
#include "stetho_fhir.h"
#include <stdio.h>

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
static atomic_t touch_pressed;
static atomic_t dropped_touch_events;
static atomic_t display_enabled;
static atomic_t requested_color = ATOMIC_INIT(-1);
static atomic_t display_errors;
static atomic_t frame_max_ms;

#if DT_NODE_HAS_STATUS_OKAY(DT_NODELABEL(touchscreen))
static void touch_callback(struct input_event *event, void *user_data)
{
	static bool pressed;
	ARG_UNUSED(user_data);
	if (event->code == INPUT_ABS_X)
		atomic_set(&touch_x, event->value);
	if (event->code == INPUT_ABS_Y)
		atomic_set(&touch_y, event->value);
	if (event->code == INPUT_BTN_TOUCH)
		pressed = event->value != 0;
	/* Consume complete coordinate frames rather than relying on event order. */
	if (!event->sync)
		return;
	if (!pressed) {
		atomic_clear(&touch_pressed);
		return;
	}
	if (atomic_get(&touch_pressed))
		return;
	struct app_event e = {.type = APP_EVENT_TOUCH, .timestamp_ms = k_uptime_get_32()};
	e.data.touch.x = atomic_get(&touch_x);
	e.data.touch.y = atomic_get(&touch_y);
	if (k_msgq_put(&app_event_queue, &e, K_NO_WAIT) == 0)
		atomic_set(&touch_pressed, 1);
	else
		atomic_inc(&dropped_touch_events);
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
	atomic_set(&display_enabled, 1);
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

static int render_color(uint8_t color_index)
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

/* Application-owned 5x7 font. Each row is five bits, MSB at the left. */
struct glyph {
	char c;
	uint8_t row[7];
};
static const struct glyph font[] = {
        {'A', {14, 17, 17, 31, 17, 17, 17}}, {'B', {30, 17, 17, 30, 17, 17, 30}},
        {'C', {15, 16, 16, 16, 16, 16, 15}}, {'D', {30, 17, 17, 17, 17, 17, 30}},
        {'E', {31, 16, 16, 30, 16, 16, 31}}, {'F', {31, 16, 16, 30, 16, 16, 16}},
        {'G', {15, 16, 16, 23, 17, 17, 15}}, {'H', {17, 17, 17, 31, 17, 17, 17}},
        {'I', {31, 4, 4, 4, 4, 4, 31}},      {'J', {7, 2, 2, 2, 18, 18, 12}},
        {'K', {17, 18, 20, 24, 20, 18, 17}}, {'L', {16, 16, 16, 16, 16, 16, 31}},
        {'M', {17, 27, 21, 21, 17, 17, 17}}, {'N', {17, 25, 25, 21, 19, 19, 17}},
        {'O', {14, 17, 17, 17, 17, 17, 14}}, {'P', {30, 17, 17, 30, 16, 16, 16}},
        {'Q', {14, 17, 17, 17, 21, 18, 13}}, {'R', {30, 17, 17, 30, 20, 18, 17}},
        {'S', {15, 16, 16, 14, 1, 1, 30}},   {'T', {31, 4, 4, 4, 4, 4, 4}},
        {'U', {17, 17, 17, 17, 17, 17, 14}}, {'V', {17, 17, 17, 17, 17, 10, 4}},
        {'W', {17, 17, 17, 21, 21, 21, 10}}, {'X', {17, 17, 10, 4, 10, 17, 17}},
        {'Y', {17, 17, 10, 4, 4, 4, 4}},     {'Z', {31, 1, 2, 4, 8, 16, 31}},
        {'0', {14, 17, 19, 21, 25, 17, 14}}, {'1', {4, 12, 4, 4, 4, 4, 14}},
        {'2', {14, 17, 1, 2, 4, 8, 31}},     {'3', {30, 1, 1, 14, 1, 1, 30}},
        {'4', {2, 6, 10, 18, 31, 2, 2}},     {'5', {31, 16, 16, 30, 1, 1, 30}},
        {'6', {14, 16, 16, 30, 17, 17, 14}}, {'7', {31, 1, 2, 4, 8, 8, 8}},
        {'8', {14, 17, 17, 14, 17, 17, 14}}, {'9', {14, 17, 17, 15, 1, 1, 14}},
        {'-', {0, 0, 0, 31, 0, 0, 0}},       {'.', {0, 0, 0, 0, 0, 6, 6}},
        {':', {0, 6, 6, 0, 6, 6, 0}},        {'/', {1, 2, 2, 4, 8, 8, 16}},
        {'%', {25, 26, 4, 8, 22, 6, 0}},
};
static uint8_t glyph_row(char c, unsigned int row)
{
	for (size_t i = 0; i < ARRAY_SIZE(font); i++)
		if (font[i].c == c)
			return font[i].row[row];
	return 0;
}
static int render_dashboard(void)
{
	char lines[20][21] = {{0}};
	struct stetho_settings settings;
	struct audio_snapshot audio;
	stetho_settings_get(&settings);
	audio_loopback_snapshot(&audio);
	static const char *const filters[] = {"RAW", "MURMUR", "BPM"};
	static const char *const sources[] = {"MIC", "TONE", "HEART TEST", "FIXTURE"};
	snprintf(lines[0], 21, "STETHOSCOPE EVAL");
	snprintf(lines[1], 21, "%s %s", settings.heart ? "HEART" : "LUNG",
	         audio.running ? "RUN" : "STOPPED");
	if (audio.bpm_valid)
		snprintf(lines[2], 21, "BPM %u.%u Q %u", audio.bpm_tenths / 10,
		         audio.bpm_tenths % 10, audio.quality_percent);
	else
		snprintf(lines[2], 21, "BPM -- Q --");
	snprintf(lines[3], 21, "FILTER %s", filters[settings.filter]);
	snprintf(lines[4], 21, "ANALYSIS %s", filters[settings.analysis]);
	snprintf(lines[5], 21, "VOLUME %u SPEED %u", settings.volume, settings.speed);
	snprintf(lines[6], 21, "SOURCE %s", sources[settings.source]);
	snprintf(lines[7], 21, "%s %u MS",
	         audio.capturing   ? "CAPTURE"
	         : audio.replaying ? "REPLAY"
	                           : "CLIP",
	         audio.clip_frames / 16);
	snprintf(lines[8], 21, "IN %u OUT %u", MIN(audio.input_rms_ppm / 1000, 9999U),
	         MIN(audio.output_rms_ppm / 1000, 9999U));
	snprintf(lines[9], 21, "CLIP %u ERR %u", MIN(audio.output_clips, 9999U),
	         MIN(audio.errors, 9999U));
	snprintf(lines[10], 21, "POINT %u LIGHT %u", settings.point + 1, settings.brightness);
	int net_result;
	bool net_ready, net_busy;
	stetho_network_status(&net_result, &net_ready, &net_busy);
	snprintf(lines[11], 21, "NET %s",
	         net_busy     ? "BUSY"
	         : !net_ready ? "OFF"
	         : net_result ? "ERROR"
	                      : "READY");
	snprintf(lines[12], 21, "FILTER    SPEED");
	snprintf(lines[14], 21, "CAPTURE   REPLAY");
	snprintf(lines[16], 21, "LIVE      HEART/LUNG");
	snprintf(lines[18], 21, "POINT     LIGHT");
	struct display_buffer_descriptor desc = {.buf_size = sizeof(draw_buffer),
	                                         .width = SCREEN_WIDTH,
	                                         .height = DRAW_ROWS,
	                                         .pitch = SCREEN_WIDTH};
	for (uint16_t y = 0; y < SCREEN_HEIGHT; y += DRAW_ROWS) {
		for (unsigned int row = 0; row < DRAW_ROWS; row++) {
			unsigned int line = (y + row) / 16, glyph_y = ((y + row) % 16) / 2;
			for (unsigned int x = 0; x < SCREEN_WIDTH; x++) {
				unsigned int col = x / 12, glyph_x = (x % 12) / 2;
				bool on = glyph_y < 7 && glyph_x < 5 &&
				          (glyph_row(lines[line][col], glyph_y) & BIT(4 - glyph_x));
				draw_buffer[row * SCREEN_WIDTH + x] =
				        on ? RGB565(255, 255, 255)
				           : (line >= 12 ? RGB565(0, 24, 48) : 0);
			}
		}
		int rc = display_write(display, 0, y, &desc, draw_buffer);
		if (rc)
			return rc;
		k_msleep(1);
	}
	return 0;
}
int display_touch_show_color(uint8_t color_index)
{
	if (!atomic_get(&display_enabled))
		return -ENODEV;
	atomic_set(&requested_color, color_index);
	return 0;
}
void display_touch_stats(uint32_t *errors, uint32_t *drops, uint32_t *max_ms)
{
	*errors = atomic_get(&display_errors);
	*drops = atomic_get(&dropped_touch_events);
	*max_ms = atomic_get(&frame_max_ms);
}
static void display_thread(void *a, void *b, void *c)
{
	unsigned int failures = 0;
	ARG_UNUSED(a);
	ARG_UNUSED(b);
	ARG_UNUSED(c);
	while (true) {
		if (atomic_get(&display_enabled)) {
			struct stetho_settings settings;
			stetho_settings_get(&settings);
			int color = atomic_get(&requested_color), rc = 0;
			uint32_t began = k_uptime_get_32();
			if (settings.diagnostics && color >= 0) {
				rc = render_color(color);
				if (!rc)
					atomic_cas(&requested_color, color, -1);
			} else if (!settings.diagnostics)
				rc = render_dashboard();
			uint32_t elapsed = k_uptime_get_32() - began;
			if (elapsed > (uint32_t)atomic_get(&frame_max_ms))
				atomic_set(&frame_max_ms, elapsed);
			if (rc) {
				atomic_inc(&display_errors);
				if (++failures >= 2) {
					atomic_clear(&display_enabled);
					LOG_ERR("Display disabled: %d", rc);
				}
			} else
				failures = 0;
		}
		k_msleep(500);
	}
}
K_THREAD_DEFINE(display_thread_id, 4096, display_thread, NULL, NULL, NULL, 10, 0, 0);
