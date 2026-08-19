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

LOG_MODULE_REGISTER(audio_loopback, LOG_LEVEL_INF);

#define I2S_MIC_NODE DT_ALIAS(i2s_mic)
#define I2S_DAC_NODE DT_ALIAS(i2s_dac)
#define I2S_SAMPLE_RATE 16000
#define I2S_BLOCK_SAMPLES 256
#define I2S_CHANNELS 2
#define I2S_BLOCK_SIZE (I2S_BLOCK_SAMPLES * I2S_CHANNELS * sizeof(int32_t))

K_MEM_SLAB_DEFINE(i2s_rx_slab, I2S_BLOCK_SIZE, 4, 4);
K_MEM_SLAB_DEFINE(i2s_tx_slab, I2S_BLOCK_SIZE, 4, 4);

static const struct device *const microphone = DEVICE_DT_GET(I2S_MIC_NODE);
static const struct device *const dac = DEVICE_DT_GET(I2S_DAC_NODE);
static atomic_t blocks_processed;
static atomic_t transfer_errors;
static atomic_t peak_sample;
static atomic_t running;

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
	        .timeout = 1000,
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
	void *rx_block = NULL;
	size_t size = 0U;
	int rc = configure_stream(microphone, I2S_DIR_RX, &i2s_rx_slab);
	int cleanup_rc;

	if (rc != 0) {
		return rc;
	}
	rc = trigger_checked(microphone, I2S_DIR_RX, I2S_TRIGGER_START, "probe start");
	if (rc == 0) {
		rc = i2s_read(microphone, &rx_block, &size);
		if (rc != 0) {
			LOG_ERR("microphone probe read failed: %d", rc);
		} else {
			const int32_t *samples = rx_block;
			size_t count = size / sizeof(samples[0]);
			bool varies = false;

			for (size_t i = 1U; i < count; i++) {
				if (samples[i] != samples[0]) {
					varies = true;
					break;
				}
			}
			k_mem_slab_free(&i2s_rx_slab, rx_block);
			if (!varies) {
				rc = -ENODATA;
			}
		}
	}
	cleanup_rc = trigger_checked(microphone, I2S_DIR_RX, I2S_TRIGGER_DROP, "probe cleanup");
	return rc != 0 ? rc : cleanup_rc;
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
	return rc != 0 ? rc : cleanup_rc;
}

static int prime_dac(void)
{
	for (int i = 0; i < 2; i++) {
		void *tx_block = NULL;
		int rc = k_mem_slab_alloc(&i2s_tx_slab, &tx_block, K_MSEC(200));

		if (rc != 0) {
			LOG_ERR("audio TX prime allocation %d failed: %d", i, rc);
			return rc;
		}
		memset(tx_block, 0, I2S_BLOCK_SIZE);
		rc = i2s_write(dac, tx_block, I2S_BLOCK_SIZE);
		if (rc != 0) {
			LOG_ERR("audio TX prime write %d failed: %d", i, rc);
			k_mem_slab_free(&i2s_tx_slab, tx_block);
			return rc;
		}
	}
	return 0;
}

static void stop_streams(void)
{
	int mic_rc = i2s_trigger(microphone, I2S_DIR_RX, I2S_TRIGGER_DROP);
	int dac_rc = i2s_trigger(dac, I2S_DIR_TX, I2S_TRIGGER_DROP);

	if (mic_rc != 0) {
		LOG_ERR("audio RX controlled shutdown failed: %d", mic_rc);
	}
	if (dac_rc != 0) {
		LOG_ERR("audio TX controlled shutdown failed: %d", dac_rc);
	}
	atomic_clear(&running);
}

static void audio_thread(void *arg_1, void *arg_2, void *arg_3)
{
	unsigned int consecutive_errors = 0U;

	ARG_UNUSED(arg_1);
	ARG_UNUSED(arg_2);
	ARG_UNUSED(arg_3);
	while (true) {
		void *rx_block = NULL;
		void *tx_block = NULL;
		size_t size = 0U;
		int rc = i2s_read(microphone, &rx_block, &size);

		if (rc != 0) {
			uint32_t count = (uint32_t)atomic_inc(&transfer_errors) + 1U;

			consecutive_errors++;
			if (app_should_log_failure(count)) {
				LOG_ERR("audio RX read failed (total=%u consecutive=%u): %d", count,
				        consecutive_errors, rc);
			}
			if (app_driver_error_action(DRIVER_OP_I2S_TRANSFER, consecutive_errors) ==
			    DRIVER_ERROR_DISABLE_COMPONENT) {
				stop_streams();
				LOG_ERR("audio loopback disabled after repeated RX failures");
				return;
			}
			k_msleep(10);
			continue;
		}

		rc = k_mem_slab_alloc(&i2s_tx_slab, &tx_block, K_MSEC(200));
		if (rc != 0) {
			k_mem_slab_free(&i2s_rx_slab, rx_block);
			atomic_inc(&transfer_errors);
			consecutive_errors++;
			LOG_ERR("audio TX buffer unavailable (consecutive=%u): %d",
			        consecutive_errors, rc);
			if (app_driver_error_action(DRIVER_OP_I2S_TRANSFER, consecutive_errors) ==
			    DRIVER_ERROR_DISABLE_COMPONENT) {
				stop_streams();
				return;
			}
			continue;
		}

		const int32_t *input = rx_block;
		int32_t *output = tx_block;
		size_t frames = size / (I2S_CHANNELS * sizeof(int32_t));
		int32_t peak = 0;

		for (size_t i = 0U; i < frames; i++) {
			int32_t left = input[i * I2S_CHANNELS];
			int32_t magnitude = left >> 16;

			magnitude = magnitude < 0 ? -magnitude : magnitude;
			peak = MAX(peak, magnitude);
			output[i * I2S_CHANNELS] = left;
			output[i * I2S_CHANNELS + 1U] = left;
		}
		atomic_set(&peak_sample, peak);
		rc = i2s_write(dac, tx_block, size);
		k_mem_slab_free(&i2s_rx_slab, rx_block);
		if (rc != 0) {
			uint32_t count = (uint32_t)atomic_inc(&transfer_errors) + 1U;

			k_mem_slab_free(&i2s_tx_slab, tx_block);
			consecutive_errors++;
			if (app_should_log_failure(count)) {
				LOG_ERR("audio TX write failed (total=%u consecutive=%u): %d",
				        count, consecutive_errors, rc);
			}
			if (app_driver_error_action(DRIVER_OP_I2S_TRANSFER, consecutive_errors) ==
			    DRIVER_ERROR_DISABLE_COMPONENT) {
				stop_streams();
				return;
			}
			continue;
		}
		consecutive_errors = 0U;
		atomic_inc(&blocks_processed);
	}
}

K_THREAD_DEFINE(audio_thread_id, 4096, audio_thread, NULL, NULL, NULL, 5, 0, K_TICKS_FOREVER);

int audio_loopback_start(void)
{
	int rc = configure_stream(microphone, I2S_DIR_RX, &i2s_rx_slab);

	if (rc == 0) {
		rc = configure_stream(dac, I2S_DIR_TX, &i2s_tx_slab);
	}
	if (rc == 0) {
		rc = prime_dac();
	}
	if (rc == 0) {
		rc = trigger_checked(microphone, I2S_DIR_RX, I2S_TRIGGER_START, "loopback start");
	}
	if (rc == 0) {
		rc = trigger_checked(dac, I2S_DIR_TX, I2S_TRIGGER_START, "loopback start");
		if (rc != 0) {
			int cleanup_rc = i2s_trigger(microphone, I2S_DIR_RX, I2S_TRIGGER_DROP);

			if (cleanup_rc != 0) {
				LOG_ERR("audio RX rollback failed: %d", cleanup_rc);
			}
		}
	}
	if (rc != 0) {
		return rc;
	}
	atomic_set(&running, 1);
	k_thread_start(audio_thread_id);
	LOG_INF("audio loopback running (INMP441 -> PCM5102A)");
	return 0;
}

void audio_loopback_snapshot(struct audio_snapshot *snapshot)
{
	if (snapshot == NULL) {
		return;
	}
	snapshot->running = atomic_get(&running) != 0;
	snapshot->blocks = (uint32_t)atomic_get(&blocks_processed);
	snapshot->errors = (uint32_t)atomic_get(&transfer_errors);
	snapshot->peak = (int32_t)atomic_get(&peak_sample);
}
