#include "audio_loopback.h"

#include <errno.h>
#include <string.h>

#include <zephyr/device.h>
#include <zephyr/drivers/i2s.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/sys/util.h>

#include "app_logic.h"
#include "stetho_control.h"
#include <math.h>

LOG_MODULE_REGISTER(audio_loopback, LOG_LEVEL_INF);

#define I2S_MIC_NODE DT_ALIAS(i2s_mic)
#define I2S_DAC_NODE DT_ALIAS(i2s_dac)
#define I2S_SAMPLE_RATE STETHO_RATE
#define I2S_BLOCK_SAMPLES 128
#define I2S_CHANNELS 2
#define I2S_BLOCK_SIZE (I2S_BLOCK_SAMPLES * I2S_CHANNELS * sizeof(int32_t))

K_MEM_SLAB_DEFINE(i2s_rx_slab, I2S_BLOCK_SIZE, 4, 4);
K_MEM_SLAB_DEFINE(i2s_tx_slab, I2S_BLOCK_SIZE, 4, 4);

static const struct device *const microphone = DEVICE_DT_GET(I2S_MIC_NODE);
static const struct device *const dac = DEVICE_DT_GET(I2S_DAC_NODE);
#define CLIP_FRAMES (STETHO_RATE * CONFIG_STETHO_CAPTURE_SECONDS)
/* DMA slabs stay in internal SRAM; only CPU-owned clips live in PSRAM. */
static int16_t clip[CLIP_FRAMES] __attribute__((section(".ext_ram.bss")));
static int16_t fixture[CLIP_FRAMES] __attribute__((section(".ext_ram.bss")));
static size_t fixture_count, fixture_position;
K_MUTEX_DEFINE(fixture_lock);
K_SEM_DEFINE(audio_wake, 0, 1);
static struct k_spinlock telemetry_lock;
static struct audio_snapshot telemetry;
static struct stetho_dsp dsp;
static struct stetho_replay replay;
static bool mic_verified;
static atomic_t started;
static atomic_t dac_probed;

static int configure_stream(const struct device *device, enum i2s_dir direction,
                            struct k_mem_slab *slab)
{
	struct i2s_config config = {
	        .word_size = 32,
	        .channels = I2S_CHANNELS,
	        .format = I2S_FMT_DATA_FORMAT_I2S,
	        .options = I2S_OPT_FRAME_CLK_CONTROLLER | I2S_OPT_BIT_CLK_CONTROLLER,
	        .frame_clk_freq = I2S_SAMPLE_RATE,
	        .mem_slab = slab,
	        .block_size = I2S_BLOCK_SIZE,
	        .timeout = 40,
	};
	int rc;

	if (!device_is_ready(device)) {
		return -ENODEV;
	}
	rc = i2s_configure(device, direction, &config);
	if (rc != 0) {
		LOG_ERR("I2S configure failed (%s dir=%d): %d", device->name, direction, rc);
	}
	return rc;
}

static int trigger_checked(const struct device *device, enum i2s_dir direction,
                           enum i2s_trigger_cmd command, const char *context)
{
	int rc = i2s_trigger(device, direction, command);

	if (rc != 0) {
		LOG_ERR("I2S %s failed (%s dir=%d cmd=%d): %d", context, device->name, direction,
		        command, rc);
	}
	return rc;
}

int audio_loopback_probe_microphone(void)
{
	int rc = configure_stream(microphone, I2S_DIR_RX, &i2s_rx_slab);
	mic_verified = false;
	if (rc)
		return rc;
	rc = trigger_checked(microphone, I2S_DIR_RX, I2S_TRIGGER_START, "probe start");
	int32_t min = INT32_MAX, max = INT32_MIN;
	/* Drain startup clocks before inspecting four consecutive left-channel
	 * blocks. Never infer variation from a constant L/R difference. */
	for (unsigned int block = 0; !rc && block < 36; block++) {
		void *rx = NULL;
		size_t bytes = 0;
		rc = i2s_read(microphone, &rx, &bytes);
		if (rc)
			break;
		if (bytes != I2S_BLOCK_SIZE)
			rc = -EIO;
		else if (block >= 32) {
			const int32_t *samples = rx;
			for (size_t i = 0; i < I2S_BLOCK_SAMPLES; i++) {
				int32_t value = samples[i * I2S_CHANNELS] >> 8;
				min = MIN(min, value);
				max = MAX(max, value);
			}
		}
		k_mem_slab_free(&i2s_rx_slab, rx);
	}
	if (!rc && (int64_t)max - min < 2)
		rc = -ENODATA;
	int cleanup = trigger_checked(microphone, I2S_DIR_RX, I2S_TRIGGER_DROP, "probe cleanup");
	mic_verified = rc == 0 && cleanup == 0;
	return rc ? rc : cleanup;
}

int audio_loopback_probe_dac(void)
{
	void *tx_block = NULL;
	int rc = configure_stream(dac, I2S_DIR_TX, &i2s_tx_slab);
	int cleanup_rc;

	if (rc != 0) {
		return rc;
	}
	rc = k_mem_slab_alloc(&i2s_tx_slab, &tx_block, K_MSEC(200));
	if (rc != 0) {
		LOG_ERR("DAC probe buffer allocation failed: %d", rc);
		return rc;
	}
	memset(tx_block, 0, I2S_BLOCK_SIZE);
	rc = i2s_write(dac, tx_block, I2S_BLOCK_SIZE);
	if (rc != 0) {
		LOG_ERR("DAC probe write failed: %d", rc);
		k_mem_slab_free(&i2s_tx_slab, tx_block);
		return rc;
	}
	rc = trigger_checked(dac, I2S_DIR_TX, I2S_TRIGGER_START, "probe start");
	cleanup_rc = trigger_checked(dac, I2S_DIR_TX, I2S_TRIGGER_DROP, "probe cleanup");
	atomic_set(&dac_probed, rc == 0 && cleanup_rc == 0);
	return rc != 0 ? rc : cleanup_rc;
}

static void publish(const struct audio_snapshot *s)
{
	k_spinlock_key_t key = k_spin_lock(&telemetry_lock);
	telemetry = *s;
	k_spin_unlock(&telemetry_lock, key);
}
void audio_loopback_snapshot(struct audio_snapshot *s)
{
	if (!s)
		return;
	k_spinlock_key_t key = k_spin_lock(&telemetry_lock);
	*s = telemetry;
	k_spin_unlock(&telemetry_lock, key);
}
int audio_fixture_reset(void)
{
	k_mutex_lock(&fixture_lock, K_FOREVER);
	fixture_count = fixture_position = 0;
	k_mutex_unlock(&fixture_lock);
	return 0;
}
int audio_fixture_append(const int16_t *samples, size_t count)
{
	int rc = 0;
	struct stetho_settings settings;
	stetho_settings_get(&settings);
	if (settings.source == SOURCE_FIXTURE)
		return -EBUSY;
	k_mutex_lock(&fixture_lock, K_FOREVER);
	if (count > CLIP_FRAMES - fixture_count)
		rc = -ENOSPC;
	else {
		memcpy(fixture + fixture_count, samples, count * sizeof(*samples));
		fixture_count += count;
	}
	k_mutex_unlock(&fixture_lock);
	return rc;
}
static int prime_dac(void)
{
	/* Two blocks cover one RX acquisition plus processing/scheduling margin. */
	for (unsigned int i = 0; i < 2; i++) {
		void *block = NULL;
		int rc = k_mem_slab_alloc(&i2s_tx_slab, &block, K_MSEC(40));
		if (rc)
			return rc;
		memset(block, 0, I2S_BLOCK_SIZE);
		rc = i2s_write(dac, block, I2S_BLOCK_SIZE);
		if (rc) {
			k_mem_slab_free(&i2s_tx_slab, block);
			return rc;
		}
	}
	return 0;
}
static void stop_streams(void)
{
	int rx_rc = i2s_trigger(microphone, I2S_DIR_RX, I2S_TRIGGER_DROP);
	int tx_rc = i2s_trigger(dac, I2S_DIR_TX, I2S_TRIGGER_DROP);
	if (rx_rc && rx_rc != -EIO)
		LOG_WRN("RX shutdown: %d", rx_rc);
	if (tx_rc && tx_rc != -EIO)
		LOG_WRN("TX shutdown: %d", tx_rc);
}
static int start_streams(void)
{
	int rc = configure_stream(dac, I2S_DIR_TX, &i2s_tx_slab);
	if (!rc && mic_verified)
		rc = configure_stream(microphone, I2S_DIR_RX, &i2s_rx_slab);
	if (!rc)
		rc = prime_dac();
	if (!rc && mic_verified)
		rc = trigger_checked(microphone, I2S_DIR_RX, I2S_TRIGGER_START, "run");
	if (!rc)
		rc = trigger_checked(dac, I2S_DIR_TX, I2S_TRIGGER_START, "run");
	if (rc)
		stop_streams();
	return rc;
}
static void audio_thread(void *a, void *b, void *c)
{
	struct audio_snapshot s = {0};
	struct stetho_settings settings, previous = {0};
	uint32_t action_id = 0;
	size_t clip_count = 0;
	unsigned int restart_budget = 0, successful_blocks = 0;
	float in[I2S_BLOCK_SAMPLES], out[I2S_BLOCK_SAMPLES], filtered[I2S_BLOCK_SAMPLES];
	ARG_UNUSED(a);
	ARG_UNUSED(b);
	ARG_UNUSED(c);
	stetho_dsp_init(&dsp);
	while (true) {
		k_sem_take(&audio_wake, K_FOREVER);
		if (!mic_verified) {
			int probe_rc = audio_loopback_probe_microphone();
			if (probe_rc)
				LOG_WRN("Mic unavailable (%d); test sources still usable",
				        probe_rc);
		}
		stetho_dsp_reset_bpm(&dsp);
		if (start_streams() != 0) {
			s.errors++;
			publish(&s);
			continue;
		}
		s.running = true;
		restart_budget = 0;
		successful_blocks = 0;
		while (s.running) {
			void *rx = NULL, *tx = NULL;
			size_t bytes = I2S_BLOCK_SIZE;
			bool intentional_restart = false;
			stetho_settings_get(&settings);
			if (settings.source != previous.source ||
			    settings.analysis != previous.analysis ||
			    settings.heart != previous.heart ||
			    settings.test_bpm != previous.test_bpm) {
				stetho_dsp_reset_bpm(&dsp);
				s.bpm_valid = false;
				s.capturing = s.replaying = false;
			}
			previous = settings;
			if (settings.action_id != action_id) {
				action_id = settings.action_id;
				if (settings.action == ACTION_RESTART) {
					intentional_restart = true;
					restart_budget = 0;
					goto recover;
				}
				if (settings.action == ACTION_CAPTURE && settings.heart) {
					clip_count = 0;
					s.capturing = true;
					s.replaying = false;
				} else if (settings.action == ACTION_REPLAY && settings.heart &&
				           clip_count && !s.capturing) {
					stetho_replay_init(&replay, clip, clip_count,
					                   settings.speed);
					s.replaying = true;
				} else if (settings.action == ACTION_LIVE)
					s.capturing = s.replaying = false;
			}
			int rc = 0;
			if (mic_verified) {
				rc = i2s_read(microphone, &rx, &bytes);
				if (rc || bytes != I2S_BLOCK_SIZE) {
					if (rx)
						k_mem_slab_free(&i2s_rx_slab, rx);
					s.rx_errors++;
					goto recover;
				}
			}
			rc = k_mem_slab_alloc(&i2s_tx_slab, &tx, K_MSEC(40));
			if (rc) {
				if (rx)
					k_mem_slab_free(&i2s_rx_slab, rx);
				s.allocation_errors++;
				goto recover;
			}
			uint32_t began = k_cycle_get_32();
			if (settings.source == SOURCE_FIXTURE)
				k_mutex_lock(&fixture_lock, K_FOREVER);
			for (size_t i = 0; i < I2S_BLOCK_SAMPLES; i++) {
				if (settings.source == SOURCE_MIC)
					in[i] = rx ? ((int32_t *)rx)[i * 2] / 2147483648.0f : 0;
				else if (settings.source == SOURCE_FIXTURE) {
					in[i] = fixture_count ? fixture[fixture_position++ %
					                                fixture_count] /
					                                32768.0f
					                      : 0;
				} else
					in[i] = stetho_test_signal(dsp.samples + i,
					                           settings.test_bpm,
					                           settings.source == SOURCE_TONE);
			}
			if (settings.source == SOURCE_FIXTURE)
				k_mutex_unlock(&fixture_lock);
			if (rx)
				k_mem_slab_free(&i2s_rx_slab, rx);
			float volume = settings.volume / 100.0f;
			float gain = 8.0f * volume * volume;
			struct stetho_levels levels;
			uint64_t before = dsp.samples;
			stetho_dsp_process(&dsp, in, out, filtered, I2S_BLOCK_SAMPLES,
			                   settings.filter, settings.analysis, gain, settings.heart,
			                   &levels);
			if (s.capturing) {
				for (size_t i = 0;
				     i < I2S_BLOCK_SAMPLES && clip_count < CLIP_FRAMES; i++)
					clip[clip_count++] =
					        (int16_t)(fminf(0.999969f, fmaxf(-1, filtered[i])) *
					                  32768.0f);
				if (clip_count == CLIP_FRAMES)
					s.capturing = false;
			}
			if (s.replaying) {
				size_t got = stetho_replay_read(&replay, out, I2S_BLOCK_SAMPLES);
				levels.output_rms = levels.output_peak = 0;
				levels.output_clips = 0;
				for (size_t i = 0; i < I2S_BLOCK_SAMPLES; i++) {
					float x = out[i] * dsp.gain;
					levels.output_clips += fabsf(x) >= 1;
					out[i] = fmaxf(-1, fminf(0.999999f, x));
					levels.output_peak =
					        fmaxf(levels.output_peak, fabsf(out[i]));
					levels.output_rms += out[i] * out[i];
				}
				levels.output_rms = sqrtf(levels.output_rms / I2S_BLOCK_SAMPLES);
				if (got < I2S_BLOCK_SAMPLES ||
				    replay.emitted == replay.target_length)
					s.replaying = false;
			}
			for (size_t i = 0; i < I2S_BLOCK_SAMPLES; i++) {
				int32_t value = (int32_t)(out[i] * 2147483520.0f);
				((int32_t *)tx)[i * 2] = ((int32_t *)tx)[i * 2 + 1] = value;
			}
			uint32_t us = k_cyc_to_us_floor32(k_cycle_get_32() - began);
			s.processing_max_us = MAX(s.processing_max_us, us);
			s.deadline_misses += us > 8000;
			s.rx_buffers_used = k_mem_slab_num_used_get(&i2s_rx_slab);
			s.tx_buffers_used = k_mem_slab_num_used_get(&i2s_tx_slab);
			rc = i2s_write(dac, tx, I2S_BLOCK_SIZE);
			if (rc) {
				k_mem_slab_free(&i2s_tx_slab, tx);
				s.tx_errors++;
				goto recover;
			}
			s.blocks++;
			s.source = settings.source;
			s.peak = (int32_t)(levels.input_peak * 32768);
			s.input_rms_ppm = (uint32_t)(levels.input_rms * 1000000);
			s.output_rms_ppm = (uint32_t)(levels.output_rms * 1000000);
			s.input_peak_ppm = (uint32_t)(levels.input_peak * 1000000);
			s.output_peak_ppm = (uint32_t)(levels.output_peak * 1000000);
			s.input_clips += levels.input_clips;
			s.output_clips += levels.output_clips;
			s.bpm_valid = dsp.bpm_valid;
			s.bpm_tenths = (uint32_t)(dsp.bpm * 10 + 0.5f);
			s.quality_percent = (uint32_t)(dsp.quality * 100);
			if (dsp.bpm_valid && before / STETHO_RATE != dsp.samples / STETHO_RATE)
				s.measured_ms = k_uptime_get_32();
			s.clip_frames = clip_count;
			s.replay_frames = s.replaying ? replay.emitted : 0;
			k_mutex_lock(&fixture_lock, K_FOREVER);
			s.fixture_frames = fixture_count;
			k_mutex_unlock(&fixture_lock);
			publish(&s);
			if (++successful_blocks >= 1250) {
				restart_budget = 0;
				successful_blocks = 0;
			}
			continue;
		recover:
			stop_streams();
			if (!intentional_restart)
				s.errors++;
			s.running = false;
			s.bpm_valid = false;
			s.capturing = s.replaying = false;
			publish(&s);
			stetho_dsp_reset_bpm(&dsp);
			if (++restart_budget <= 3) {
				k_msleep(100);
				s.restarts++;
				if (start_streams() == 0) {
					s.running = true;
					successful_blocks = 0;
				} else { /* A failed restart consumes the remaining bounded attempts
					    here. */
					while (restart_budget++ < 3) {
						k_msleep(100);
						s.restarts++;
						if (start_streams() == 0) {
							s.running = true;
							break;
						}
					}
				}
			}
			if (!s.running)
				LOG_ERR("Audio stopped; stetho restart retries explicitly");
			publish(&s);
		}
	}
}
K_THREAD_DEFINE(audio_thread_id, 12288, audio_thread, NULL, NULL, NULL, 5, 0, 0);
int audio_loopback_start(void)
{
	if (!atomic_get(&dac_probed))
		return -EAGAIN;
	if (!device_is_ready(dac))
		return -ENODEV;
	if (atomic_cas(&started, 0, 1))
		k_sem_give(&audio_wake);
	else {
		struct audio_snapshot s;
		audio_loopback_snapshot(&s);
		if (!s.running)
			k_sem_give(&audio_wake);
		else
			stetho_action_request(ACTION_RESTART);
	}
	return 0;
}
