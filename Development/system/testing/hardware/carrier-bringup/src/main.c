/*
 * Carrier bring-up for the DigitalStethoscope_Eval PCB: checks each peripheral
 * on its own and logs every driver result, so a fault points to one part.
 */

#include <errno.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

#include <zephyr/device.h>
#include <zephyr/drivers/adc.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/hwinfo.h>
#include <zephyr/drivers/i2s.h>
#include <zephyr/drivers/led_strip.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/shell/shell.h>
#include <zephyr/sys/atomic.h>

LOG_MODULE_REGISTER(carrier, LOG_LEVEL_DBG);

#define USER_NODE DT_PATH(zephyr_user)

#define SAMPLE_RATE_HZ 16000
#define CHANNELS 2
#define FRAMES_PER_BLOCK 128
#define BLOCK_SIZE_BYTES (FRAMES_PER_BLOCK * CHANNELS * sizeof(int32_t))
#define RECEIVE_BLOCK_COUNT 8
#define TRANSMIT_BLOCK_COUNT 4
#define PASSTHROUGH_FIFO_SAMPLES (FRAMES_PER_BLOCK * 8)
#define DEFAULT_PASSTHROUGH_GAIN 16
/* The INMP441 starts with about 1 s of near full-scale output; keep it off the headphones. */
#define MICROPHONE_SETTLING_BLOCKS (SAMPLE_RATE_HZ / FRAMES_PER_BLOCK)
/* One-pole DC blocker, about 20 Hz at 16 kHz: the INMP441 output carries a drifting offset. */
#define DC_BLOCKER_POLE 0.992f
#define I2S_TIMEOUT_MS 100
#define INPUT_POLL_MS 10
#define BUTTON_DEBOUNCE_MS 30
/* The pad-link scan of 10 November 2026 saw 10 to 20 ms gaps between positions, at the
 * 10 ms poll resolution. */
#define SWITCH_DEBOUNCE_MS 30
/* Settle time after driving GPIO18 low; a margin, not measured. */
#define SWITCH_SETTLE_MICROSECONDS 20
#define POTENTIOMETER_STEP_MV 40
#define SUMMARY_PERIOD_MS 1000
#define RAW_DUMP_PERIOD_MS 5000
#define FULL_SCALE_24_BIT 8388607.0f
#define POTENTIOMETER_FULL_MV 3300
/* Highest reading at the 3V3 end of J7 on the Eval carrier, 10 November 2026. The cause of
 * the gap to 3300 mV is not established. */
#define POTENTIOMETER_MEASURED_TOP_MV 3083

K_MEM_SLAB_DEFINE_STATIC(receive_slab, BLOCK_SIZE_BYTES, RECEIVE_BLOCK_COUNT, 4);
K_MEM_SLAB_DEFINE_STATIC(transmit_slab, BLOCK_SIZE_BYTES, TRANSMIT_BLOCK_COUNT, 4);

static const struct device *const microphone = DEVICE_DT_GET(DT_ALIAS(i2s_mic));
static const struct device *const dac = DEVICE_DT_GET(DT_ALIAS(i2s_dac));
static const struct device *const status_light = DEVICE_DT_GET(DT_ALIAS(status_light));

static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(USER_NODE, led_gpios);
static const struct gpio_dt_spec button = GPIO_DT_SPEC_GET(USER_NODE, button_gpios);
static const struct gpio_dt_spec filter_switch[] = {
        GPIO_DT_SPEC_GET_BY_IDX(USER_NODE, filter_switch_gpios, 0),
        GPIO_DT_SPEC_GET_BY_IDX(USER_NODE, filter_switch_gpios, 1),
        GPIO_DT_SPEC_GET_BY_IDX(USER_NODE, filter_switch_gpios, 2),
};
static const char *const filter_switch_name[] = {"RAW GPIO18", "MURMUR GPIO21", "BPM GPIO38"};
static const struct gpio_dt_spec microphone_data =
        GPIO_DT_SPEC_GET(USER_NODE, microphone_data_gpios);
static const struct adc_dt_spec potentiometer = ADC_DT_SPEC_GET_BY_IDX(USER_NODE, 0);

enum output_mode { OUTPUT_SILENCE, OUTPUT_TONE, OUTPUT_LOOPBACK };
enum led_mode { LED_FOLLOWS_BUTTON, LED_ON, LED_OFF };

static atomic_t output_mode = ATOMIC_INIT(OUTPUT_LOOPBACK);
static atomic_t led_mode = ATOMIC_INIT(LED_FOLLOWS_BUTTON);
static atomic_t tone_frequency_hz = ATOMIC_INIT(440);
static atomic_t tone_level_percent = ATOMIC_INIT(100);

static atomic_t passthrough_gain = ATOMIC_INIT(DEFAULT_PASSTHROUGH_GAIN);

/* Microphone to DAC FIFO; both I2S controllers run at the same nominal rate. */
static int32_t passthrough_fifo[PASSTHROUGH_FIFO_SAMPLES];
static size_t passthrough_read_index;
static size_t passthrough_count;
static uint32_t passthrough_underruns;
static uint32_t passthrough_overruns;
static uint32_t passthrough_clipped_samples;
static struct k_spinlock passthrough_lock;

static int32_t passthrough_process(float *previous_input, float *previous_output,
                                   int32_t microphone_value)
{
	const float output =
	        (float)microphone_value - *previous_input + DC_BLOCKER_POLE * *previous_output;
	const int64_t amplified = (int64_t)(output * 256.0f) * atomic_get(&passthrough_gain);

	*previous_input = (float)microphone_value;
	*previous_output = output;
	if (amplified > INT32_MAX || amplified < INT32_MIN) {
		passthrough_clipped_samples++;
		return amplified > 0 ? INT32_MAX : INT32_MIN;
	}
	return (int32_t)amplified;
}

static void passthrough_push(const int32_t *samples, size_t count)
{
	k_spinlock_key_t key = k_spin_lock(&passthrough_lock);

	for (size_t index = 0; index < count; index++) {
		if (passthrough_count == PASSTHROUGH_FIFO_SAMPLES) {
			passthrough_read_index =
			        (passthrough_read_index + 1) % PASSTHROUGH_FIFO_SAMPLES;
			passthrough_count--;
			passthrough_overruns++;
		}
		passthrough_fifo[(passthrough_read_index + passthrough_count) %
		                 PASSTHROUGH_FIFO_SAMPLES] = samples[index];
		passthrough_count++;
	}
	k_spin_unlock(&passthrough_lock, key);
}

static bool passthrough_pop_block(int32_t *words)
{
	k_spinlock_key_t key = k_spin_lock(&passthrough_lock);
	const bool available = passthrough_count >= FRAMES_PER_BLOCK;

	if (available) {
		for (size_t frame = 0; frame < FRAMES_PER_BLOCK; frame++) {
			words[frame * CHANNELS] = passthrough_fifo[passthrough_read_index];
			words[frame * CHANNELS + 1] = passthrough_fifo[passthrough_read_index];
			passthrough_read_index =
			        (passthrough_read_index + 1) % PASSTHROUGH_FIFO_SAMPLES;
		}
		passthrough_count -= FRAMES_PER_BLOCK;
	} else {
		passthrough_underruns++;
	}
	k_spin_unlock(&passthrough_lock, key);
	return available;
}

struct channel_statistics {
	int32_t minimum;
	int32_t maximum;
	int64_t sum;
	double sum_of_squares;
	uint32_t count;
	uint32_t zero_count;
	uint32_t minus_one_count;
};

struct receive_counters {
	uint32_t blocks;
	uint32_t short_blocks;
	uint32_t read_errors;
	uint32_t restarts;
	int32_t first_non_zero_block;
	int last_error;
};

struct transmit_counters {
	uint32_t blocks;
	uint32_t allocation_errors;
	uint32_t write_errors;
	uint32_t restarts;
	uint32_t minimum_free_blocks;
	int last_error;
};

static struct receive_counters receive_status = {.first_non_zero_block = -1};
static struct transmit_counters transmit_status = {.minimum_free_blocks = TRANSMIT_BLOCK_COUNT};
static int potentiometer_millivolts = -1;
static int potentiometer_raw = -1;
static int button_pressed = -1;
static int filter_position = -2;

static void statistics_reset(struct channel_statistics *statistics)
{
	*statistics = (struct channel_statistics){.minimum = INT32_MAX, .maximum = INT32_MIN};
}

static void statistics_add(struct channel_statistics *statistics, int32_t value)
{
	statistics->minimum = MIN(statistics->minimum, value);
	statistics->maximum = MAX(statistics->maximum, value);
	statistics->sum += value;
	statistics->sum_of_squares += (double)value * value;
	statistics->count++;
	statistics->zero_count += (value == 0);
	statistics->minus_one_count += (value == -1);
}

static void statistics_log(const char *name, const struct channel_statistics *statistics)
{
	if (statistics->count == 0) {
		LOG_WRN("mic %s: no samples", name);
		return;
	}
	const int32_t mean = (int32_t)(statistics->sum / statistics->count);
	const double mean_square = statistics->sum_of_squares / statistics->count;
	const double variance = mean_square - (double)mean * mean;
	const int32_t alternating_rms = (int32_t)sqrt(variance > 0 ? variance : 0);
	const int dbfs_tenths =
	        alternating_rms > 0 ? (int)(200.0f * log10f(alternating_rms / FULL_SCALE_24_BIT))
	                            : -1999;

	LOG_INF("mic %s: n=%u min=%d max=%d mean=%d ac_rms=%d (%d.%d dBFS) zeros=%u minus_ones=%u",
	        name, statistics->count, statistics->minimum, statistics->maximum, mean,
	        alternating_rms, dbfs_tenths / 10, abs(dbfs_tenths % 10), statistics->zero_count,
	        statistics->minus_one_count);
}

static int configure_stream(const struct device *device, enum i2s_dir direction,
                            struct k_mem_slab *slab)
{
	struct i2s_config config = {
	        .word_size = 32,
	        .channels = CHANNELS,
	        .format = I2S_FMT_DATA_FORMAT_I2S,
	        .options = I2S_OPT_FRAME_CLK_CONTROLLER | I2S_OPT_BIT_CLK_CONTROLLER,
	        .frame_clk_freq = SAMPLE_RATE_HZ,
	        .mem_slab = slab,
	        .block_size = BLOCK_SIZE_BYTES,
	        .timeout = I2S_TIMEOUT_MS,
	};

	if (!device_is_ready(device)) {
		LOG_ERR("%s: device not ready", device->name);
		return -ENODEV;
	}
	int result = i2s_configure(device, direction, &config);

	LOG_INF("%s dir=%s configure: %d (word 32, 2 ch, I2S, controller, %u Hz, block %u B)",
	        device->name, direction == I2S_DIR_RX ? "RX" : "TX", result, SAMPLE_RATE_HZ,
	        (unsigned int)BLOCK_SIZE_BYTES);
	return result;
}

static int trigger(const struct device *device, enum i2s_dir direction,
                   enum i2s_trigger_cmd command, const char *what)
{
	int result = i2s_trigger(device, direction, command);

	LOG_INF("%s dir=%s trigger %s: %d", device->name, direction == I2S_DIR_RX ? "RX" : "TX",
	        what, result);
	return result;
}

/* The shell probe reconfigures the input pins, so it must not run during an input poll. */
K_MUTEX_DEFINE(input_pins_lock);

static void probe_pin(const char *name, const struct gpio_dt_spec *specification)
{
	int result_up = gpio_pin_configure(specification->port, specification->pin,
	                                   GPIO_INPUT | GPIO_PULL_UP);

	k_busy_wait(500);
	const int level_with_pull_up = gpio_pin_get_raw(specification->port, specification->pin);
	int result_down = gpio_pin_configure(specification->port, specification->pin,
	                                     GPIO_INPUT | GPIO_PULL_DOWN);

	k_busy_wait(500);
	const int level_with_pull_down = gpio_pin_get_raw(specification->port, specification->pin);
	const char *verdict =
	        (level_with_pull_up == 1 && level_with_pull_down == 1)
	                ? "driven or pulled HIGH externally"
	        : (level_with_pull_up == 0 && level_with_pull_down == 0)
	                ? "driven or pulled LOW externally"
	        : (level_with_pull_up == 1 && level_with_pull_down == 0)
	                ? "follows internal pull (floating, or only a weak external pull)"
	                : "inverted (unexpected)";

	LOG_INF("probe %-14s pull-up=%d pull-down=%d -> %s (configure %d/%d)", name,
	        level_with_pull_up, level_with_pull_down, verdict, result_up, result_down);
}

static void probe_all_pins(void)
{
	LOG_INF("--- pin probe: internal pull-up vs pull-down reading ---");
	LOG_INF("expected: button and J8 pins HIGH externally (R11, R14..R16) unless pressed or "
	        "selected");
	probe_pin("BUTTON GPIO16", &button);
	for (size_t index = 0; index < ARRAY_SIZE(filter_switch); index++) {
		probe_pin(filter_switch_name[index], &filter_switch[index]);
	}
	probe_pin("MIC SD GPIO6", &microphone_data);
	LOG_INF("MIC SD GPIO6 has only R1 100k to GND, weaker than the internal pull-up, so 1/0 is "
	        "expected here");
}

static int configure_inputs(void)
{
	int result = gpio_pin_configure_dt(&button, GPIO_INPUT);

	LOG_INF("button GPIO16 configure: %d", result);
	for (size_t index = 0; index < ARRAY_SIZE(filter_switch); index++) {
		int switch_result = gpio_pin_configure_dt(&filter_switch[index], GPIO_INPUT);

		LOG_INF("switch %s configure: %d", filter_switch_name[index], switch_result);
		result = result ? result : switch_result;
	}
	return result;
}

static void blink_led_at_boot(void)
{
	int result = gpio_pin_configure_dt(&led, GPIO_OUTPUT_INACTIVE);

	LOG_INF("LED GPIO17 configure: %d; blinking 3 times (500 ms on, 500 ms off)", result);
	for (int index = 0; index < 3; index++) {
		LOG_INF("LED on (set %d)", gpio_pin_set_dt(&led, 1));
		k_msleep(500);
		LOG_INF("LED off (set %d)", gpio_pin_set_dt(&led, 0));
		k_msleep(500);
	}
}

static int read_potentiometer(int *raw, int *millivolts)
{
	int16_t sample = 0;
	struct adc_sequence sequence = {.buffer = &sample, .buffer_size = sizeof(sample)};
	int result = adc_sequence_init_dt(&potentiometer, &sequence);

	if (result == 0) {
		result = adc_read_dt(&potentiometer, &sequence);
	}
	if (result == 0) {
		int32_t value = sample;

		*raw = sample;
		result = adc_raw_to_millivolts_dt(&potentiometer, &value);
		*millivolts = value;
	}
	return result;
}

static void set_status_light_brightness(int millivolts)
{
	static int last_brightness = -1;
	const int brightness = CLAMP(millivolts * 255 / POTENTIOMETER_MEASURED_TOP_MV, 0, 255);

	if (brightness == last_brightness) {
		return;
	}
	struct led_rgb pixel = {.r = brightness, .g = brightness, .b = brightness};
	int result = led_strip_update_rgb(status_light, &pixel, 1);

	if (result != 0 || abs(brightness - last_brightness) >= 8 || brightness == 0 ||
	    brightness == 255) {
		LOG_INF("RGB LED GPIO48 white brightness %d/255 from %d mV: update %d", brightness,
		        millivolts, result);
	}
	last_brightness = brightness;
}

/*
 * The fitted J8 has its common contact on part pin 2, which the Eval footprint routes
 * to the RAW net (GPIO18); its throws land on GND, MURMUR (GPIO21) and BPM (GPIO38).
 * Raw grounds GPIO18 directly; for the others GPIO18 is pulled low and the linked pad
 * follows. Only low is driven, so the GND throw cannot short a high output.
 */
enum filter_switch_position { SWITCH_NONE = -1, SWITCH_RAW, SWITCH_MURMUR, SWITCH_BPM };

static const char *const filter_switch_position_name[] = {"Raw", "Murmur", "BPM"};

static enum filter_switch_position read_filter_switch(int *murmur_level, int *bpm_level)
{
	const struct gpio_dt_spec *common = &filter_switch[0];
	enum filter_switch_position position = SWITCH_NONE;

	*murmur_level = -1;
	*bpm_level = -1;
	if (gpio_pin_get_raw(common->port, common->pin) == 0) {
		return SWITCH_RAW;
	}
	if (gpio_pin_configure(common->port, common->pin, GPIO_OUTPUT_LOW) == 0) {
		k_busy_wait(SWITCH_SETTLE_MICROSECONDS);
		*murmur_level = gpio_pin_get_raw(filter_switch[1].port, filter_switch[1].pin);
		*bpm_level = gpio_pin_get_raw(filter_switch[2].port, filter_switch[2].pin);
		position = *murmur_level == 0 && *bpm_level == 1   ? SWITCH_MURMUR
		           : *bpm_level == 0 && *murmur_level == 1 ? SWITCH_BPM
		                                                   : SWITCH_NONE;
	}
	(void)gpio_pin_configure_dt(common, GPIO_INPUT);
	return position;
}

static void input_thread(void *unused1, void *unused2, void *unused3)
{
	ARG_UNUSED(unused1);
	ARG_UNUSED(unused2);
	ARG_UNUSED(unused3);

	int stable_button = -1;
	int candidate_button = -1;
	int64_t candidate_since = 0;
	enum filter_switch_position switch_candidate = SWITCH_NONE;
	int64_t switch_candidate_since = 0;
	int last_reported_millivolts = -1000;
	uint32_t poll_count = 0;
	int last_adc_error = 0;

	LOG_INF("RGB LED WS2812 on GPIO48 (SPI3 MOSI): %s; the potentiometer sets its brightness",
	        device_is_ready(status_light) ? "ready" : "NOT READY");
	if (!adc_is_ready_dt(&potentiometer)) {
		LOG_ERR("ADC1 not ready");
	} else {
		LOG_INF("ADC1 channel 0 (GPIO1) setup: %d", adc_channel_setup_dt(&potentiometer));
	}

	while (true) {
		k_mutex_lock(&input_pins_lock, K_FOREVER);
		const int raw_button = gpio_pin_get_dt(&button);

		if (raw_button != candidate_button) {
			candidate_button = raw_button;
			candidate_since = k_uptime_get();
		}
		if (candidate_button != stable_button &&
		    k_uptime_get() - candidate_since >= BUTTON_DEBOUNCE_MS) {
			stable_button = candidate_button;
			button_pressed = stable_button;
			LOG_INF("BUTTON %s (logical %d, raw level %d)",
			        stable_button == 1 ? "PRESSED" : "released", stable_button,
			        gpio_pin_get_raw(button.port, button.pin));
		}

		switch (atomic_get(&led_mode)) {
		case LED_ON:
			gpio_pin_set_dt(&led, 1);
			break;
		case LED_OFF:
			gpio_pin_set_dt(&led, 0);
			break;
		default:
			gpio_pin_set_dt(&led, stable_button == 1);
			break;
		}

		int murmur_level = 0;
		int bpm_level = 0;
		const enum filter_switch_position switch_reading =
		        read_filter_switch(&murmur_level, &bpm_level);

		k_mutex_unlock(&input_pins_lock);

		if (switch_reading != switch_candidate) {
			switch_candidate = switch_reading;
			switch_candidate_since = k_uptime_get();
		}
		if (switch_candidate != filter_position &&
		    k_uptime_get() - switch_candidate_since >= SWITCH_DEBOUNCE_MS) {
			filter_position = switch_candidate;
			if (filter_position == SWITCH_NONE) {
				LOG_WRN("J8 SWITCH no valid position for %d ms (MURMUR level %d, "
				        "BPM level %d while GPIO18 low)",
				        SWITCH_DEBOUNCE_MS, murmur_level, bpm_level);
			} else {
				LOG_INF("J8 SWITCH position %s",
				        filter_switch_position_name[filter_position]);
			}
		}

		if (poll_count % 5 == 0) {
			int raw = 0;
			int millivolts = 0;
			int result = read_potentiometer(&raw, &millivolts);

			if (result != 0) {
				if (result != last_adc_error) {
					LOG_ERR("POTENTIOMETER read error %d", result);
				}
			} else {
				potentiometer_raw = raw;
				potentiometer_millivolts = millivolts;
				set_status_light_brightness(millivolts);
				if (abs(millivolts - last_reported_millivolts) >=
				    POTENTIOMETER_STEP_MV) {
					last_reported_millivolts = millivolts;
					LOG_INF("POTENTIOMETER raw=%d %d mV (%d %% of %d mV)", raw,
					        millivolts,
					        millivolts * 100 / POTENTIOMETER_FULL_MV,
					        POTENTIOMETER_FULL_MV);
				}
			}
			last_adc_error = result;
		}
		poll_count++;
		k_msleep(INPUT_POLL_MS);
	}
}

static void receive_restart(void)
{
	receive_status.restarts++;
	trigger(microphone, I2S_DIR_RX, I2S_TRIGGER_DROP, "DROP");
	LOG_INF("mic RX slab free blocks after DROP: %u of %u",
	        k_mem_slab_num_free_get(&receive_slab), RECEIVE_BLOCK_COUNT);
	k_msleep(100);
	if (configure_stream(microphone, I2S_DIR_RX, &receive_slab) == 0) {
		trigger(microphone, I2S_DIR_RX, I2S_TRIGGER_START, "START");
	}
}

static void receive_thread(void *unused1, void *unused2, void *unused3)
{
	ARG_UNUSED(unused1);
	ARG_UNUSED(unused2);
	ARG_UNUSED(unused3);

	struct channel_statistics left;
	struct channel_statistics right;
	int64_t next_summary = k_uptime_get() + SUMMARY_PERIOD_MS;
	int64_t next_dump = k_uptime_get() + 500;
	float dc_blocker_input = 0.0f;
	float dc_blocker_output = 0.0f;
	int32_t passthrough_block[FRAMES_PER_BLOCK];

	statistics_reset(&left);
	statistics_reset(&right);
	LOG_INF("--- mic INMP441 on I2S0: SCK GPIO4, WS GPIO5, SD GPIO6, L/R=GND -> data in LEFT "
	        "slot ---");
	while (configure_stream(microphone, I2S_DIR_RX, &receive_slab) != 0 ||
	       trigger(microphone, I2S_DIR_RX, I2S_TRIGGER_START, "START") != 0) {
		LOG_ERR("mic RX start failed; retrying in 1 s");
		k_msleep(1000);
	}

	while (true) {
		void *block = NULL;
		size_t size = 0;
		int result = i2s_read(microphone, &block, &size);

		if (result != 0) {
			receive_status.read_errors++;
			receive_status.last_error = result;
			LOG_ERR("mic i2s_read: %d (block %u)", result, receive_status.blocks);
			receive_restart();
			continue;
		}
		if (size != BLOCK_SIZE_BYTES) {
			receive_status.short_blocks++;
			LOG_WRN("mic short block: %u B", (unsigned int)size);
		}

		const int32_t *words = block;
		bool block_has_signal = false;
		const size_t frames = size / (CHANNELS * sizeof(int32_t));

		for (size_t frame = 0; frame < frames; frame++) {
			const int32_t left_value = words[frame * CHANNELS] >> 8;
			const int32_t right_value = words[frame * CHANNELS + 1] >> 8;

			statistics_add(&left, left_value);
			statistics_add(&right, right_value);
			block_has_signal |= (left_value != 0 && left_value != -1);
			passthrough_block[frame] = passthrough_process(
			        &dc_blocker_input, &dc_blocker_output, left_value);
		}
		if (receive_status.blocks < MICROPHONE_SETTLING_BLOCKS) {
			memset(passthrough_block, 0, sizeof(passthrough_block));
		}
		passthrough_push(passthrough_block, frames);

		if (block_has_signal && receive_status.first_non_zero_block < 0) {
			receive_status.first_non_zero_block = receive_status.blocks;
			LOG_INF("mic first block with varying left data: #%u (%u ms after start)",
			        receive_status.blocks,
			        receive_status.blocks * FRAMES_PER_BLOCK * 1000 / SAMPLE_RATE_HZ);
		}
		if (k_uptime_get() >= next_dump) {
			next_dump = k_uptime_get() + RAW_DUMP_PERIOD_MS;
			LOG_INF("mic raw words L/R: %08x %08x | %08x %08x | %08x %08x | %08x %08x",
			        words[0], words[1], words[2], words[3], words[4], words[5],
			        words[6], words[7]);
		}
		k_mem_slab_free(&receive_slab, block);
		receive_status.blocks++;

		if (k_uptime_get() >= next_summary) {
			next_summary += SUMMARY_PERIOD_MS;
			LOG_INF("mic RX: blocks=%u errors=%u restarts=%u short=%u free_slab=%u",
			        receive_status.blocks, receive_status.read_errors,
			        receive_status.restarts, receive_status.short_blocks,
			        k_mem_slab_num_free_get(&receive_slab));
			statistics_log("LEFT ", &left);
			statistics_log("RIGHT", &right);
			statistics_reset(&left);
			statistics_reset(&right);
		}
	}
}

static void fill_transmit_block(int32_t *words, uint32_t *phase)
{
	const enum output_mode mode = atomic_get(&output_mode);
	const double amplitude = 2147483647.0 * atomic_get(&tone_level_percent) / 100.0;
	const double step =
	        2.0 * 3.141592653589793 * atomic_get(&tone_frequency_hz) / SAMPLE_RATE_HZ;

	if (mode == OUTPUT_LOOPBACK) {
		if (!passthrough_pop_block(words)) {
			memset(words, 0, BLOCK_SIZE_BYTES);
		}
		return;
	}
	for (size_t frame = 0; frame < FRAMES_PER_BLOCK; frame++) {
		const int32_t value =
		        mode == OUTPUT_TONE ? (int32_t)(amplitude * sin(step * (double)*phase)) : 0;

		words[frame * CHANNELS] = value;
		words[frame * CHANNELS + 1] = value;
		*phase = (*phase + 1) % SAMPLE_RATE_HZ;
	}
}

static int transmit_one_block(uint32_t *phase)
{
	void *block = NULL;
	int result = k_mem_slab_alloc(&transmit_slab, &block, K_MSEC(I2S_TIMEOUT_MS));

	transmit_status.minimum_free_blocks =
	        MIN(transmit_status.minimum_free_blocks, k_mem_slab_num_free_get(&transmit_slab));
	if (result != 0) {
		transmit_status.allocation_errors++;
		transmit_status.last_error = result;
		LOG_ERR("DAC TX slab alloc: %d (free %u of %u)", result,
		        k_mem_slab_num_free_get(&transmit_slab), TRANSMIT_BLOCK_COUNT);
		return result;
	}
	fill_transmit_block(block, phase);
	result = i2s_write(dac, block, BLOCK_SIZE_BYTES);
	if (result != 0) {
		transmit_status.write_errors++;
		transmit_status.last_error = result;
		LOG_ERR("DAC i2s_write: %d (free %u)", result,
		        k_mem_slab_num_free_get(&transmit_slab));
		k_mem_slab_free(&transmit_slab, block);
		return result;
	}
	transmit_status.blocks++;
	return 0;
}

static int transmit_start(uint32_t *phase)
{
	int result = configure_stream(dac, I2S_DIR_TX, &transmit_slab);

	for (int index = 0; result == 0 && index < 2; index++) {
		result = transmit_one_block(phase);
	}
	LOG_INF("DAC TX primed 2 blocks: %d, free slab %u", result,
	        k_mem_slab_num_free_get(&transmit_slab));
	if (result == 0) {
		result = trigger(dac, I2S_DIR_TX, I2S_TRIGGER_START, "START");
	}
	return result;
}

static void transmit_thread(void *unused1, void *unused2, void *unused3)
{
	ARG_UNUSED(unused1);
	ARG_UNUSED(unused2);
	ARG_UNUSED(unused3);

	uint32_t phase = 0;
	int64_t next_summary = k_uptime_get() + SUMMARY_PERIOD_MS;

	LOG_INF("--- DAC PCM5102A on I2S1: BCK GPIO40, LRCK GPIO41, DIN GPIO42; SCK=GND (PLL), "
	        "XSMT high ---");
	while (transmit_start(&phase) != 0) {
		LOG_ERR("DAC TX start failed; dropping and retrying in 1 s");
		trigger(dac, I2S_DIR_TX, I2S_TRIGGER_DROP, "DROP");
		LOG_INF("DAC TX slab free after DROP: %u of %u",
		        k_mem_slab_num_free_get(&transmit_slab), TRANSMIT_BLOCK_COUNT);
		k_msleep(1000);
	}

	while (true) {
		if (transmit_one_block(&phase) != 0) {
			transmit_status.restarts++;
			trigger(dac, I2S_DIR_TX, I2S_TRIGGER_DROP, "DROP");
			LOG_INF("DAC TX slab free after DROP: %u of %u",
			        k_mem_slab_num_free_get(&transmit_slab), TRANSMIT_BLOCK_COUNT);
			k_msleep(100);
			while (transmit_start(&phase) != 0) {
				trigger(dac, I2S_DIR_TX, I2S_TRIGGER_DROP, "DROP");
				LOG_INF("DAC TX slab free after DROP: %u of %u",
				        k_mem_slab_num_free_get(&transmit_slab),
				        TRANSMIT_BLOCK_COUNT);
				k_msleep(1000);
			}
		}
		if (k_uptime_get() >= next_summary) {
			next_summary += SUMMARY_PERIOD_MS;
			const enum output_mode mode = atomic_get(&output_mode);

			LOG_INF("DAC TX: blocks=%u alloc_errors=%u write_errors=%u restarts=%u "
			        "min_free=%u mode=%s %ld Hz %ld %%",
			        transmit_status.blocks, transmit_status.allocation_errors,
			        transmit_status.write_errors, transmit_status.restarts,
			        transmit_status.minimum_free_blocks,
			        mode == OUTPUT_TONE       ? "tone"
			        : mode == OUTPUT_LOOPBACK ? "loopback"
			                                  : "silence",
			        atomic_get(&tone_frequency_hz), atomic_get(&tone_level_percent));
			if (mode == OUTPUT_LOOPBACK) {
				LOG_INF("PASSTHROUGH gain x%ld, fifo %u samples, underruns=%u "
				        "overruns=%u clipped=%u",
				        atomic_get(&passthrough_gain),
				        (unsigned int)passthrough_count, passthrough_underruns,
				        passthrough_overruns, passthrough_clipped_samples);
			}
			transmit_status.minimum_free_blocks = TRANSMIT_BLOCK_COUNT;
		}
	}
}

K_THREAD_STACK_DEFINE(input_stack, 3072);
K_THREAD_STACK_DEFINE(receive_stack, 4096);
K_THREAD_STACK_DEFINE(transmit_stack, 4096);
static struct k_thread input_thread_data;
static struct k_thread receive_thread_data;
static struct k_thread transmit_thread_data;

int main(void)
{
	uint8_t identifier[8] = {0};
	ssize_t identifier_length = hwinfo_get_device_id(identifier, sizeof(identifier));
	uint32_t reset_cause = 0;

	(void)hwinfo_get_reset_cause(&reset_cause);
	LOG_INF("=== carrier bring-up, DigitalStethoscope_Eval pin map (Altium a8f23a2) ===");
	LOG_INF("device id length %d: %02x%02x%02x%02x%02x%02x, reset cause 0x%08x",
	        (int)identifier_length, identifier[0], identifier[1], identifier[2], identifier[3],
	        identifier[4], identifier[5], reset_cause);

	probe_all_pins();
	LOG_INF("inputs configured: %d", configure_inputs());
	blink_led_at_boot();

	k_thread_create(&input_thread_data, input_stack, K_THREAD_STACK_SIZEOF(input_stack),
	                input_thread, NULL, NULL, NULL, 7, 0, K_NO_WAIT);
	k_thread_create(&receive_thread_data, receive_stack, K_THREAD_STACK_SIZEOF(receive_stack),
	                receive_thread, NULL, NULL, NULL, 3, 0, K_NO_WAIT);
	k_thread_create(&transmit_thread_data, transmit_stack,
	                K_THREAD_STACK_SIZEOF(transmit_stack), transmit_thread, NULL, NULL, NULL, 2,
	                0, K_NO_WAIT);
	return 0;
}

static int command_tone(const struct shell *shell, size_t argc, char **argv)
{
	atomic_set(&tone_frequency_hz, CLAMP(strtol(argv[1], NULL, 10), 20, 7000));
	if (argc > 2) {
		atomic_set(&tone_level_percent, CLAMP(strtol(argv[2], NULL, 10), 0, 100));
	}
	atomic_set(&output_mode, OUTPUT_TONE);
	shell_print(shell, "tone %ld Hz at %ld %% of full scale", atomic_get(&tone_frequency_hz),
	            atomic_get(&tone_level_percent));
	return 0;
}

static int command_silence(const struct shell *shell, size_t argc, char **argv)
{
	atomic_set(&output_mode, OUTPUT_SILENCE);
	shell_print(shell, "DAC output silent");
	return 0;
}

static int command_loopback(const struct shell *shell, size_t argc, char **argv)
{
	if (argc > 1) {
		atomic_set(&passthrough_gain, CLAMP(strtol(argv[1], NULL, 10), 1, 256));
	}
	atomic_set(&output_mode, OUTPUT_LOOPBACK);
	shell_print(shell, "DAC plays the microphone left channel, DC blocked, gain x%ld",
	            atomic_get(&passthrough_gain));
	return 0;
}

static int command_led(const struct shell *shell, size_t argc, char **argv)
{
	atomic_set(&led_mode, !strcmp(argv[1], "on")    ? LED_ON
	                      : !strcmp(argv[1], "off") ? LED_OFF
	                                                : LED_FOLLOWS_BUTTON);
	shell_print(shell, "LED mode %s", argv[1]);
	return 0;
}

static int command_probe(const struct shell *shell, size_t argc, char **argv)
{
	k_mutex_lock(&input_pins_lock, K_FOREVER);
	probe_all_pins();
	configure_inputs();
	k_mutex_unlock(&input_pins_lock);
	return 0;
}

static int command_status(const struct shell *shell, size_t argc, char **argv)
{
	shell_print(shell,
	            "STATUS button=%d filter=%d pot_raw=%d pot_mv=%d rx_blocks=%u rx_errors=%u "
	            "rx_restarts=%u "
	            "rx_first_signal=%d tx_blocks=%u tx_alloc_errors=%u tx_write_errors=%u "
	            "tx_restarts=%u mode=%ld",
	            button_pressed, filter_position, potentiometer_raw, potentiometer_millivolts,
	            receive_status.blocks, receive_status.read_errors, receive_status.restarts,
	            receive_status.first_non_zero_block, transmit_status.blocks,
	            transmit_status.allocation_errors, transmit_status.write_errors,
	            transmit_status.restarts, atomic_get(&output_mode));
	return 0;
}

SHELL_STATIC_SUBCMD_SET_CREATE(
        carrier_commands,
        SHELL_CMD_ARG(tone, NULL, "tone <Hz> [percent]: sine on both DAC channels", command_tone, 2,
                      1),
        SHELL_CMD(silence, NULL, "DAC outputs zeros", command_silence),
        SHELL_CMD_ARG(loopback, NULL, "loopback [gain 1..256]: DAC plays the microphone",
                      command_loopback, 1, 1),
        SHELL_CMD_ARG(led, NULL, "led <on|off|button>", command_led, 2, 0),
        SHELL_CMD(probe, NULL, "repeat the pull-up/pull-down pin probe", command_probe),
        SHELL_CMD(status, NULL, "one-line counters", command_status), SHELL_SUBCMD_SET_END);
SHELL_CMD_REGISTER(carrier, &carrier_commands, "Eval carrier bring-up", NULL);
