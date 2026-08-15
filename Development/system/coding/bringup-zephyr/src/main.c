/*
 * Hardware bring-up test for the digital stethoscope (ESP32-S3-DevKitC-1).
 *
 * Every peripheral of the pin map is probed at boot (one try plus PROBE_RETRIES
 * retries each). Only the peripherals that actually answer are enabled:
 *
 *   - display       : shows a solid colour, every touch rotates to the next one
 *   - pushbutton    : each press toggles the LED built into the button
 *   - mic + DAC     : INMP441 (I2S RX) is looped through to the PCM5102A (I2S TX)
 *   - potentiometer : dims the display backlight (PWM/LEDC)
 *   - SP3T switch   : position is reported in the status line
 *
 * Console: the detected peripherals are listed once, then their live status is
 * logged every 500 ms. If nothing was detected at all, a single static message
 * is repeated every 5 s instead.
 */

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/adc.h>
#include <zephyr/drivers/i2s.h>
#include <zephyr/drivers/pwm.h>
#include <zephyr/drivers/display.h>
#include <zephyr/input/input.h>
#include <zephyr/logging/log.h>
#include <string.h>
#include <stdio.h>

LOG_MODULE_REGISTER(bringup, LOG_LEVEL_INF);

#define PROBE_RETRIES     3
#define PROBE_RETRY_MS    50
#define LOOP_MS           20
#define STATUS_PERIOD_MS  500
#define IDLE_PERIOD_MS    5000

/* ------------------------------------------------------------- GPIO */
#define ZUSER DT_PATH(zephyr_user)

static const struct gpio_dt_spec status_led = GPIO_DT_SPEC_GET(ZUSER, led_gpios);
static const struct gpio_dt_spec user_btn   = GPIO_DT_SPEC_GET(ZUSER, btn_gpios);
static const struct gpio_dt_spec sw_pos1    = GPIO_DT_SPEC_GET_BY_IDX(ZUSER, sw1_gpios, 0);
static const struct gpio_dt_spec sw_pos2    = GPIO_DT_SPEC_GET_BY_IDX(ZUSER, sw1_gpios, 1);
static const struct gpio_dt_spec sw_pos3    = GPIO_DT_SPEC_GET_BY_IDX(ZUSER, sw1_gpios, 2);

/* ------------------------------------------------------------- PWM backlight */
static const struct pwm_dt_spec backlight = PWM_DT_SPEC_GET(ZUSER);

/* ------------------------------------------------------------- ADC (poti) */
static const struct adc_dt_spec poti = ADC_DT_SPEC_GET(ZUSER);

/* ------------------------------------------------------------- Display */
static const struct device *disp = DEVICE_DT_GET(DT_CHOSEN(zephyr_display));
#define RGB565(r, g, b) ((uint16_t)((((r) & 0xF8) << 8) | (((g) & 0xFC) << 3) | ((b) >> 3)))

#define SCR_W 240
#define SCR_H 320

static const struct {
	const char *name;
	uint16_t rgb565;
} palette[] = {
	{ "red",     RGB565(255, 0, 0) },
	{ "green",   RGB565(0, 255, 0) },
	{ "blue",    RGB565(0, 0, 255) },
	{ "yellow",  RGB565(255, 255, 0) },
	{ "magenta", RGB565(255, 0, 255) },
	{ "cyan",    RGB565(0, 255, 255) },
	{ "white",   RGB565(255, 255, 255) },
};

/* ------------------------------------------------------------- shared state */
static int color_idx;
static bool led_on;
static int poti_mv = -1;

/* ------------------------------------------------------------- I2S audio */
#define I2S_MIC_NODE   DT_ALIAS(i2s_mic)
#define I2S_DAC_NODE   DT_ALIAS(i2s_dac)
#define I2S_SAMPLE_HZ  16000
#define I2S_BLOCK_SMPL 256
#define I2S_CHANNELS   2
#define I2S_BLOCK_SIZE (I2S_BLOCK_SMPL * I2S_CHANNELS * sizeof(int32_t))
K_MEM_SLAB_DEFINE(i2s_rx_slab, I2S_BLOCK_SIZE, 4, 4);
K_MEM_SLAB_DEFINE(i2s_tx_slab, I2S_BLOCK_SIZE, 4, 4);

static volatile uint32_t audio_blocks;
static volatile uint32_t audio_errs;
static volatile int32_t audio_peak;

/* ------------------------------------------------------------- touch state */
static volatile int16_t touch_x, touch_y;
static volatile bool touch_event;
static volatile uint32_t touch_count;

#if DT_NODE_HAS_STATUS_OKAY(DT_NODELABEL(touchscreen))
static void touch_cb(struct input_event *evt, void *user_data)
{
	ARG_UNUSED(user_data);
	switch (evt->code) {
	case INPUT_ABS_X:
		touch_x = evt->value;
		break;
	case INPUT_ABS_Y:
		touch_y = evt->value;
		break;
	case INPUT_BTN_TOUCH:
		if (evt->value) {           /* press */
			touch_count++;
			touch_event = true;
		}
		break;
	default:
		break;
	}
}
INPUT_CALLBACK_DEFINE(DEVICE_DT_GET(DT_NODELABEL(touchscreen)), touch_cb, NULL);
#endif

/* ------------------------------------------------------------- display helpers */
static void fill_rect(int x, int y, int w, int h, uint16_t color)
{
	static uint16_t line[SCR_W];
	struct display_buffer_descriptor desc;

	if (w > SCR_W) {
		w = SCR_W;
	}
	for (int i = 0; i < w; i++) {
		line[i] = color;
	}
	desc.buf_size = (uint32_t)w * 2;
	desc.width = w;
	desc.height = 1;
	desc.pitch = w;

	for (int row = 0; row < h; row++) {
		display_write(disp, x, y + row, &desc, line);
	}
}

static void fill_screen(uint16_t color)
{
	fill_rect(0, 0, SCR_W, SCR_H, color);
}

static void show_color(int idx)
{
	color_idx = idx % (int)ARRAY_SIZE(palette);
	fill_screen(palette[color_idx].rgb565);
	LOG_INF("display colour -> %s", palette[color_idx].name);
}

/* ------------------------------------------------------------- audio loopback */
static int i2s_cfg(const struct device *dev, enum i2s_dir dir, struct k_mem_slab *slab)
{
	struct i2s_config cfg = {
		.word_size = 32,
		.channels = I2S_CHANNELS,
		.format = I2S_FMT_DATA_FORMAT_I2S,
		.options = I2S_OPT_FRAME_CLK_CONTROLLER | I2S_OPT_BIT_CLK_CONTROLLER,
		.frame_clk_freq = I2S_SAMPLE_HZ,
		.mem_slab = slab,
		.block_size = I2S_BLOCK_SIZE,
		.timeout = 1000,
	};

	if (!device_is_ready(dev)) {
		return -ENODEV;
	}
	return i2s_configure(dev, dir, &cfg);
}

static void audio_thread(void *a, void *b, void *c)
{
	ARG_UNUSED(a);
	ARG_UNUSED(b);
	ARG_UNUSED(c);

	const struct device *mic = DEVICE_DT_GET(I2S_MIC_NODE);
	const struct device *dac = DEVICE_DT_GET(I2S_DAC_NODE);

	/* The probe left both streams in READY, so they must be configured again. */
	if (i2s_cfg(mic, I2S_DIR_RX, &i2s_rx_slab) != 0 ||
	    i2s_cfg(dac, I2S_DIR_TX, &i2s_tx_slab) != 0) {
		LOG_ERR("audio: re-configure failed, loopback disabled");
		return;
	}

	/* Prime the TX queue with silence before starting. */
	for (int i = 0; i < 2; i++) {
		void *tx;

		if (k_mem_slab_alloc(&i2s_tx_slab, &tx, K_MSEC(200)) == 0) {
			memset(tx, 0, I2S_BLOCK_SIZE);
			i2s_write(dac, tx, I2S_BLOCK_SIZE);
		}
	}

	if (i2s_trigger(mic, I2S_DIR_RX, I2S_TRIGGER_START) != 0 ||
	    i2s_trigger(dac, I2S_DIR_TX, I2S_TRIGGER_START) != 0) {
		LOG_ERR("audio: stream start failed, loopback disabled");
		return;
	}
	LOG_INF("audio loopback running (INMP441 -> PCM5102A)");

	while (1) {
		void *rx, *tx;
		size_t size;
		int rc = i2s_read(mic, &rx, &size);

		if (rc != 0) {
			/* Must not spin here: this thread outranks the logging thread. */
			audio_errs++;
			k_msleep(10);
			continue;
		}
		if (k_mem_slab_alloc(&i2s_tx_slab, &tx, K_MSEC(200)) != 0) {
			k_mem_slab_free(&i2s_rx_slab, rx);
			audio_errs++;
			k_msleep(10);
			continue;
		}

		int32_t *in = rx;
		int32_t *out = tx;
		size_t frames = size / (I2S_CHANNELS * sizeof(int32_t));
		int32_t peak = 0;

		for (size_t i = 0; i < frames; i++) {
			int32_t left = in[i * I2S_CHANNELS];   /* INMP441 = left ch. */
			int32_t mag = left >> 16;

			if (mag < 0) {
				mag = -mag;
			}
			if (mag > peak) {
				peak = mag;
			}
			out[i * I2S_CHANNELS] = left;
			out[i * I2S_CHANNELS + 1] = left;      /* duplicate to right */
		}
		audio_peak = peak;
		audio_blocks++;

		i2s_write(dac, tx, size);
		k_mem_slab_free(&i2s_rx_slab, rx);
	}
}

/* Started from main() only when both the mic and the DAC answered the probe. */
K_THREAD_DEFINE(audio_tid, 4096, audio_thread, NULL, NULL, NULL, 5, 0, K_TICKS_FOREVER);

/* ------------------------------------------------------------- helpers */
static int read_switch_position(void)
{
	if (gpio_pin_get_dt(&sw_pos1)) {
		return 1;
	}
	if (gpio_pin_get_dt(&sw_pos2)) {
		return 2;
	}
	if (gpio_pin_get_dt(&sw_pos3)) {
		return 3;
	}
	return 0;
}

static int poti_read_mv(void)
{
	int16_t sample = 0;
	int32_t val_mv;
	struct adc_sequence seq = {
		.buffer = &sample,
		.buffer_size = sizeof(sample),
	};

	(void)adc_sequence_init_dt(&poti, &seq);
	if (adc_read_dt(&poti, &seq) != 0) {
		return -1;
	}
	val_mv = sample;
	if (adc_raw_to_millivolts_dt(&poti, &val_mv) != 0) {
		return sample;
	}
	return val_mv;
}

static void set_brightness(int mv)
{
	uint32_t period = backlight.period;
	uint32_t pulse;

	if (mv < 0) {
		mv = 0;
	} else if (mv > 3300) {
		mv = 3300;
	}
	pulse = (uint32_t)((uint64_t)period * (uint32_t)mv / 3300U);
	pwm_set_pulse_dt(&backlight, pulse);
}

/* ------------------------------------------------------------- probes */
enum {
	C_BTN_LED, C_SWITCH, C_POTI, C_BACKLIGHT, C_DISPLAY, C_TOUCH, C_MIC, C_DAC, C_COUNT
};

static int probe_btn_led(void)
{
	int rc;

	if (!gpio_is_ready_dt(&status_led) || !gpio_is_ready_dt(&user_btn)) {
		return -ENODEV;
	}
	rc = gpio_pin_configure_dt(&status_led, GPIO_OUTPUT_INACTIVE);
	if (rc) {
		return rc;
	}
	return gpio_pin_configure_dt(&user_btn, GPIO_INPUT);
}

static int probe_switch(void)
{
	const struct gpio_dt_spec *sw[] = { &sw_pos1, &sw_pos2, &sw_pos3 };

	for (size_t i = 0; i < ARRAY_SIZE(sw); i++) {
		int rc;

		if (!gpio_is_ready_dt(sw[i])) {
			return -ENODEV;
		}
		rc = gpio_pin_configure_dt(sw[i], GPIO_INPUT);
		if (rc) {
			return rc;
		}
	}
	/* Common pole sits on GND, so a wired SP3T always pulls one throw low. */
	return read_switch_position() ? 0 : -ENODATA;
}

static int probe_poti(void)
{
	int rc;

	if (!adc_is_ready_dt(&poti)) {
		return -ENODEV;
	}
	rc = adc_channel_setup_dt(&poti);
	if (rc) {
		return rc;
	}
	return poti_read_mv() < 0 ? -EIO : 0;
}

static int probe_backlight(void)
{
	if (!pwm_is_ready_dt(&backlight)) {
		return -ENODEV;
	}
	return pwm_set_pulse_dt(&backlight, backlight.period);
}

static int probe_display(void)
{
	struct display_capabilities cap;

	if (!device_is_ready(disp)) {
		return -ENODEV;
	}
	display_get_capabilities(disp, &cap);
	if (cap.x_resolution == 0 || cap.y_resolution == 0) {
		return -EIO;
	}
	return display_blanking_off(disp);
}

static int probe_touch(void)
{
#if DT_NODE_HAS_STATUS_OKAY(DT_NODELABEL(touchscreen))
	return device_is_ready(DEVICE_DT_GET(DT_NODELABEL(touchscreen))) ? 0 : -ENODEV;
#else
	return -ENODEV;
#endif
}

static int probe_mic(void)
{
	const struct device *mic = DEVICE_DT_GET(I2S_MIC_NODE);
	void *rx;
	size_t size;
	int rc = i2s_cfg(mic, I2S_DIR_RX, &i2s_rx_slab);

	if (rc) {
		return rc;
	}
	rc = i2s_trigger(mic, I2S_DIR_RX, I2S_TRIGGER_START);
	if (rc) {
		return rc;
	}
	rc = i2s_read(mic, &rx, &size);
	if (rc == 0) {
		const int32_t *s = rx;
		size_t n = size / sizeof(int32_t);
		bool varies = false;

		/* An unwired SD line yields a constant block; a live INMP441 dithers. */
		for (size_t i = 1; i < n; i++) {
			if (s[i] != s[0]) {
				varies = true;
				break;
			}
		}
		k_mem_slab_free(&i2s_rx_slab, rx);
		if (!varies) {
			rc = -ENODATA;
		}
	}
	i2s_trigger(mic, I2S_DIR_RX, I2S_TRIGGER_DROP);
	return rc;
}

static int probe_dac(void)
{
	const struct device *dac = DEVICE_DT_GET(I2S_DAC_NODE);
	void *tx;
	int rc = i2s_cfg(dac, I2S_DIR_TX, &i2s_tx_slab);

	if (rc) {
		return rc;
	}
	rc = k_mem_slab_alloc(&i2s_tx_slab, &tx, K_MSEC(200));
	if (rc) {
		return rc;
	}
	memset(tx, 0, I2S_BLOCK_SIZE);
	rc = i2s_write(dac, tx, I2S_BLOCK_SIZE);   /* takes ownership of the block */
	if (rc) {
		k_mem_slab_free(&i2s_tx_slab, tx);
		return rc;
	}
	rc = i2s_trigger(dac, I2S_DIR_TX, I2S_TRIGGER_START);
	i2s_trigger(dac, I2S_DIR_TX, I2S_TRIGGER_DROP);
	return rc;
}

struct component {
	const char *name;
	const char *hint;
	int (*probe)(void);
};

static const struct component components[C_COUNT] = {
	[C_BTN_LED]   = { "pushbutton + LED (GPIO16/17)", "button to GND, LED via series resistor",
			  probe_btn_led },
	[C_SWITCH]    = { "SP3T switch      (GPIO18/21/38)", "common pole must sit on GND",
			  probe_switch },
	[C_POTI]      = { "potentiometer    (GPIO1, ADC1_CH0)", "wiper to GPIO1, ends to 3V3/GND",
			  probe_poti },
	[C_BACKLIGHT] = { "backlight PWM    (GPIO8, LEDC ch0)", "LEDC controller not ready",
			  probe_backlight },
	[C_DISPLAY]   = { "display ILI9341  (SPI2, CS GPIO10)", "check SCK/MOSI/MISO, DC, RESET",
			  probe_display },
	[C_TOUCH]     = { "touch XPT2046    (SPI2, CS GPIO7)", "check T_CS and PENIRQ (GPIO15)",
			  probe_touch },
	[C_MIC]       = { "mic INMP441      (I2S0)", "check BCLK/WS/SD and L/R to GND",
			  probe_mic },
	[C_DAC]       = { "DAC PCM5102A     (I2S1)", "check BCK/LCK/DIN, SCK to GND, XSMT to 3V3",
			  probe_dac },
};

static bool present[C_COUNT];
static int probe_err[C_COUNT];
static uint8_t probe_tries[C_COUNT];

static int probe_all(void)
{
	int found = 0;

	for (int i = 0; i < C_COUNT; i++) {
		int rc = -ENODEV;

		for (int attempt = 0; attempt <= PROBE_RETRIES; attempt++) {
			probe_tries[i] = (uint8_t)(attempt + 1);
			rc = components[i].probe();
			if (rc == 0) {
				break;
			}
			k_msleep(PROBE_RETRY_MS);
		}
		present[i] = (rc == 0);
		probe_err[i] = rc;
		found += (rc == 0);
	}
	return found;
}

static void probe_report(int found)
{
	LOG_INF("---- peripheral probe: %d of %d connected (max %d retries each) ----",
		found, C_COUNT, PROBE_RETRIES);
	for (int i = 0; i < C_COUNT; i++) {
		if (present[i]) {
			LOG_INF("[ OK ] %s  (attempt %u)", components[i].name, probe_tries[i]);
		}
	}
	for (int i = 0; i < C_COUNT; i++) {
		if (!present[i]) {
			LOG_WRN("[ -- ] %s  not connected (err %d) - %s",
				components[i].name, probe_err[i], components[i].hint);
		}
	}
}

/* ------------------------------------------------------------- status line */
static void log_status(void)
{
	char buf[192];
	size_t off = 0;

#define APPEND(...)                                                                    \
	do {                                                                           \
		if (off < sizeof(buf)) {                                               \
			int _n = snprintf(buf + off, sizeof(buf) - off, __VA_ARGS__);  \
			off = (_n < 0) ? sizeof(buf) : off + (size_t)_n;                \
			if (off > sizeof(buf)) {                                       \
				off = sizeof(buf);                                     \
			}                                                              \
		}                                                                      \
	} while (0)

	buf[0] = '\0';
	if (present[C_BTN_LED]) {
		APPEND("btn=%d led=%d | ", gpio_pin_get_dt(&user_btn), led_on);
	}
	if (present[C_SWITCH]) {
		APPEND("sw=%d | ", read_switch_position());
	}
	if (present[C_POTI]) {
		APPEND("poti=%dmV | ", poti_mv);
	}
	if (present[C_BACKLIGHT]) {
		APPEND("backlight=%u%% | ",
		       present[C_POTI] && poti_mv >= 0 ? (unsigned int)(poti_mv * 100 / 3300) : 100U);
	}
	if (present[C_DISPLAY]) {
		APPEND("colour=%s | ", palette[color_idx].name);
	}
	if (present[C_TOUCH]) {
		APPEND("touch=%u@%d,%d | ", touch_count, touch_x, touch_y);
	}
	if (present[C_MIC] && present[C_DAC]) {
		APPEND("audio blocks=%u errs=%u peak=%d | ",
		       audio_blocks, audio_errs, audio_peak);
	}
#undef APPEND

	LOG_INF("%s", buf);
}

int main(void)
{
	uint32_t tick = 0;
	int prev_btn = 0;

	LOG_INF("=== Stethoscope hardware bring-up ===");

	int found = probe_all();

	probe_report(found);

	if (found == 0) {
		while (1) {
			LOG_INF("no peripherals connected - check wiring and power, then reset");
			k_msleep(IDLE_PERIOD_MS);
		}
	}

	if (present[C_POTI]) {
		poti_mv = poti_read_mv();
	}
	if (present[C_BACKLIGHT]) {
		set_brightness(present[C_POTI] ? poti_mv : 3300);
	}
	if (present[C_DISPLAY]) {
		show_color(0);
	}
	if (present[C_MIC] && present[C_DAC]) {
		k_thread_start(audio_tid);
	} else if (present[C_MIC] != present[C_DAC]) {
		LOG_WRN("audio loopback disabled: %s missing",
			present[C_MIC] ? "DAC" : "microphone");
	}

	while (1) {
		/* (f) button press edge toggles the LED inside the button */
		if (present[C_BTN_LED]) {
			int btn = gpio_pin_get_dt(&user_btn);

			if (btn && !prev_btn) {
				led_on = !led_on;
				gpio_pin_set_dt(&status_led, led_on);
			}
			prev_btn = btn;
		}

		/* potentiometer dims the backlight */
		if (present[C_POTI]) {
			int mv = poti_read_mv();

			if (mv >= 0) {
				poti_mv = mv;
				if (present[C_BACKLIGHT]) {
					set_brightness(mv);
				}
			}
		}

		/* (e) every touch rotates the displayed colour */
		if (present[C_TOUCH] && touch_event) {
			touch_event = false;
			if (present[C_DISPLAY]) {
				show_color(color_idx + 1);
			} else {
				LOG_INF("touch at x=%d y=%d (no display connected)",
					touch_x, touch_y);
			}
		}

		if ((tick % (STATUS_PERIOD_MS / LOOP_MS)) == 0) {
			log_status();
		}
		tick++;
		k_msleep(LOOP_MS);
	}
	return 0;
}
