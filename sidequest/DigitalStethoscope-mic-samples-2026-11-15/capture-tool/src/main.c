/*
 * Throwaway microphone capture for the DigitalStethoscope_Eval carrier: plays the INMP441 live on
 * the PCM5102A as the application does, records 15 s clips into PSRAM and sends them, or streams
 * live, as framed binary over UART0.
 * The frame format is documented in ../README.md and parsed by ../capture.py.
 */

#include <string.h>

#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/i2s.h>
#include <zephyr/drivers/uart.h>
#include <zephyr/kernel.h>
#include <zephyr/multi_heap/shared_multi_heap.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/sys/byteorder.h>
#include <zephyr/sys/crc.h>

#define USER_NODE DT_PATH(zephyr_user)

#define SAMPLE_RATE_HZ 16000
#define CHANNELS 2
#define FRAMES_PER_BLOCK 128
#define BLOCK_SIZE_BYTES (FRAMES_PER_BLOCK * CHANNELS * sizeof(int32_t))
#define BLOCK_PERIOD_MS ((FRAMES_PER_BLOCK * 1000) / SAMPLE_RATE_HZ)
#define RECEIVE_BLOCK_COUNT 8
#define TRANSMIT_BLOCK_COUNT 8
/* Silent blocks queued before the DAC link starts; the driver rejects a start with an empty queue. */
#define PRIMED_TRANSMIT_BLOCKS 4
#define I2S_TIMEOUT_MS 100
/* The INMP441 starts with about 1 s of near full-scale output (carrier-bringup, 10 Nov 2026). */
#define SETTLING_BLOCKS (SAMPLE_RATE_HZ / FRAMES_PER_BLOCK)
/* The INMP441 does not drive the 8 bits after the 24-bit sample. */
#define SAMPLE_MASK 0xFFFFFF00U

#define BYTES_PER_SAMPLE 3
#define RECORDING_SECONDS 15
#define RECORDING_SAMPLES (RECORDING_SECONDS * SAMPLE_RATE_HZ)
#define RECORDING_BYTES (RECORDING_SAMPLES * BYTES_PER_SAMPLE)
/* One clip at a time: it is sent before the next one can start. */
#define RECORDING_SLOTS 1
#define NO_RECORDING_SLOT (-1)
#define FRAME_PAYLOAD_BYTES (FRAMES_PER_BLOCK * BYTES_PER_SAMPLE)
#define STREAM_QUEUE_BLOCKS 48

#define FRAME_HEADER_BYTES 16
#define FRAME_KIND_STREAM 1
#define FRAME_KIND_RECORDING 2
#define FRAME_KIND_RECORDING_END 3
#define FRAME_FLAG_RECEIVE_ERROR 0x01

#define BUTTON_DEBOUNCE_MS 30
#define CONTROL_POLL_MS 2

struct stream_block {
	uint32_t first_sample_index;
	uint8_t payload[FRAME_PAYLOAD_BYTES];
};

K_MEM_SLAB_DEFINE_STATIC(receive_slab, BLOCK_SIZE_BYTES, RECEIVE_BLOCK_COUNT, 4);
K_MEM_SLAB_DEFINE_STATIC(transmit_slab, BLOCK_SIZE_BYTES, TRANSMIT_BLOCK_COUNT, 4);
K_MSGQ_DEFINE(stream_queue, sizeof(struct stream_block), STREAM_QUEUE_BLOCKS, 4);
K_MSGQ_DEFINE(completed_recordings, sizeof(int), RECORDING_SLOTS, 4);

static const struct device *const microphone = DEVICE_DT_GET(DT_ALIAS(i2s_mic));
static const struct device *const dac = DEVICE_DT_GET(DT_ALIAS(i2s_dac));
static const struct device *const console = DEVICE_DT_GET(DT_CHOSEN(zephyr_console));
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(USER_NODE, led_gpios);
static const struct gpio_dt_spec button = GPIO_DT_SPEC_GET(USER_NODE, button_gpios);

static atomic_t streaming;
static atomic_t listening_requested;
static atomic_t filling_slot = ATOMIC_INIT(NO_RECORDING_SLOT);
static atomic_t microphone_ready;
static atomic_t received_blocks;
static atomic_t receive_errors;
static atomic_t transmit_errors;
static atomic_t stream_dropped_blocks;
static atomic_t recording_receive_error[RECORDING_SLOTS];

static uint8_t *recording_buffer[RECORDING_SLOTS];
/* Written only by the main thread. */
static bool recording_slot_in_use[RECORDING_SLOTS];
/* Written by the receive thread while a slot is filling; reset by the main thread before that. */
static size_t recorded_samples;
static uint32_t total_samples;
/* Written only by the receive thread. */
static bool listening;

static void pack_sample(uint8_t *destination, int32_t word)
{
	const int32_t sample = word >> 8;

	destination[0] = (uint8_t)sample;
	destination[1] = (uint8_t)(sample >> 8);
	destination[2] = (uint8_t)(sample >> 16);
}

static int start_receive(void)
{
	struct i2s_config config = {
	        .word_size = 32,
	        .channels = CHANNELS,
	        .format = I2S_FMT_DATA_FORMAT_LEFT_JUSTIFIED | I2S_FMT_FRAME_CLK_INV,
	        .options = I2S_OPT_FRAME_CLK_CONTROLLER | I2S_OPT_BIT_CLK_CONTROLLER,
	        .frame_clk_freq = SAMPLE_RATE_HZ,
	        .mem_slab = &receive_slab,
	        .block_size = BLOCK_SIZE_BYTES,
	        .timeout = I2S_TIMEOUT_MS,
	};
	int result = i2s_configure(microphone, I2S_DIR_RX, &config);

	if (result == 0) {
		result = i2s_trigger(microphone, I2S_DIR_RX, I2S_TRIGGER_START);
	}
	return result;
}

static int write_transmit_block(const int32_t *words)
{
	void *block = NULL;
	int result = k_mem_slab_alloc(&transmit_slab, &block, K_NO_WAIT);

	if (result != 0) {
		return result;
	}
	if (words == NULL) {
		memset(block, 0, BLOCK_SIZE_BYTES);
	} else {
		int32_t *output = block;

		/* Same as the application: the left slot unchanged on both DAC channels. */
		for (size_t frame = 0; frame < FRAMES_PER_BLOCK; frame++) {
			const int32_t sample =
			        (int32_t)((uint32_t)words[frame * CHANNELS] & SAMPLE_MASK);

			output[frame * CHANNELS] = sample;
			output[frame * CHANNELS + 1] = sample;
		}
	}
	result = i2s_write(dac, block, BLOCK_SIZE_BYTES);
	if (result != 0) {
		k_mem_slab_free(&transmit_slab, block);
	}
	return result;
}

static int start_transmit(void)
{
	struct i2s_config config = {
	        .word_size = 32,
	        .channels = CHANNELS,
	        .format = I2S_FMT_DATA_FORMAT_I2S,
	        .options = I2S_OPT_FRAME_CLK_CONTROLLER | I2S_OPT_BIT_CLK_CONTROLLER,
	        .frame_clk_freq = SAMPLE_RATE_HZ,
	        .mem_slab = &transmit_slab,
	        .block_size = BLOCK_SIZE_BYTES,
	        .timeout = I2S_TIMEOUT_MS,
	};
	int result = i2s_configure(dac, I2S_DIR_TX, &config);

	for (int block = 0; result == 0 && block < PRIMED_TRANSMIT_BLOCKS; block++) {
		result = write_transmit_block(NULL);
	}
	if (result == 0) {
		result = i2s_trigger(dac, I2S_DIR_TX, I2S_TRIGGER_START);
	}
	return result;
}

static void stop_transmit(void)
{
	/* DROP alone loses the block in DMA: the driver clears its pointer without freeing it. */
	if (i2s_trigger(dac, I2S_DIR_TX, I2S_TRIGGER_STOP) == 0) {
		k_msleep(2 * BLOCK_PERIOD_MS);
	}
	i2s_trigger(dac, I2S_DIR_TX, I2S_TRIGGER_DROP);
	listening = false;
}

static void play_block(const int32_t *words, size_t frames)
{
	const bool requested = atomic_get(&listening_requested) != 0;

	if (requested && !listening) {
		if (start_transmit() == 0) {
			listening = true;
		} else {
			atomic_inc(&transmit_errors);
			atomic_set(&listening_requested, 0);
			stop_transmit();
		}
	} else if (!requested && listening) {
		stop_transmit();
	} else if (listening && frames == FRAMES_PER_BLOCK && write_transmit_block(words) != 0) {
		/* The link restarts with the next block. */
		atomic_inc(&transmit_errors);
		stop_transmit();
	}
}

static void handle_block(const int32_t *words, size_t frames)
{
	const int slot = atomic_get(&filling_slot);

	if (slot != NO_RECORDING_SLOT) {
		for (size_t frame = 0; frame < frames && recorded_samples < RECORDING_SAMPLES;
		     frame++) {
			pack_sample(&recording_buffer[slot][recorded_samples * BYTES_PER_SAMPLE],
			            words[frame * CHANNELS]);
			recorded_samples++;
		}
		if (recorded_samples == RECORDING_SAMPLES &&
		    atomic_cas(&filling_slot, slot, NO_RECORDING_SLOT)) {
			k_msgq_put(&completed_recordings, &slot, K_NO_WAIT);
		}
	} else if (atomic_get(&streaming) && frames == FRAMES_PER_BLOCK) {
		struct stream_block block = {.first_sample_index = total_samples};

		for (size_t frame = 0; frame < frames; frame++) {
			pack_sample(&block.payload[frame * BYTES_PER_SAMPLE], words[frame * CHANNELS]);
		}
		if (k_msgq_put(&stream_queue, &block, K_NO_WAIT) != 0) {
			atomic_inc(&stream_dropped_blocks);
		}
	}
	total_samples += frames;
}

static void receive_thread(void *unused1, void *unused2, void *unused3)
{
	ARG_UNUSED(unused1);
	ARG_UNUSED(unused2);
	ARG_UNUSED(unused3);

	uint32_t settling_blocks = 0;

	while (start_receive() != 0) {
		k_msleep(1000);
	}
	while (true) {
		void *block = NULL;
		size_t size = 0;
		int result = i2s_read(microphone, &block, &size);

		if (result != 0) {
			const int slot = atomic_get(&filling_slot);

			atomic_inc(&receive_errors);
			if (slot != NO_RECORDING_SLOT) {
				atomic_set(&recording_receive_error[slot], 1);
			}
			i2s_trigger(microphone, I2S_DIR_RX, I2S_TRIGGER_DROP);
			k_msleep(100);
			start_receive();
			continue;
		}
		if (settling_blocks < SETTLING_BLOCKS) {
			settling_blocks++;
		} else {
			const size_t frames = size / (CHANNELS * sizeof(int32_t));

			atomic_set(&microphone_ready, 1);
			play_block(block, frames);
			handle_block(block, frames);
		}
		k_mem_slab_free(&receive_slab, block);
		atomic_inc(&received_blocks);
	}
}

K_THREAD_DEFINE(receive_thread_id, 2048, receive_thread, NULL, NULL, NULL, 2, 0, 0);

static void send_bytes(const uint8_t *data, size_t length)
{
	for (size_t index = 0; index < length; index++) {
		uart_poll_out(console, data[index]);
	}
}

static void send_frame(uint8_t kind, uint8_t flags, uint32_t sequence, uint32_t first_sample_index,
                       const uint8_t *payload, uint16_t sample_count)
{
	uint8_t header[FRAME_HEADER_BYTES] = {'S', 'T', 'H', 'A', kind, flags};
	uint8_t checksum[4];
	const size_t payload_bytes = (size_t)sample_count * BYTES_PER_SAMPLE;

	sys_put_le16(sample_count, &header[6]);
	sys_put_le32(sequence, &header[8]);
	sys_put_le32(first_sample_index, &header[12]);
	sys_put_le32(crc32_ieee_update(crc32_ieee(header, sizeof(header)), payload, payload_bytes),
	             checksum);
	send_bytes(header, sizeof(header));
	send_bytes(payload, payload_bytes);
	send_bytes(checksum, sizeof(checksum));
}

static bool is_recording_busy(void)
{
	for (int slot = 0; slot < RECORDING_SLOTS; slot++) {
		if (recording_slot_in_use[slot]) {
			return true;
		}
	}
	return false;
}

static void print_status(void)
{
	const char *state = atomic_get(&streaming)                          ? "streaming"
	                    : atomic_get(&filling_slot) != NO_RECORDING_SLOT ? "recording"
	                    : is_recording_busy()                            ? "sending"
	                                                                     : "idle";

	printk("\nmic-capture ready=%d state=%s listening=%d rate=%d seconds=%d blocks=%ld errors=%ld "
	       "transmit_errors=%ld stream_dropped=%ld psram=%s\n",
	       (int)atomic_get(&microphone_ready), state, (int)atomic_get(&listening_requested),
	       SAMPLE_RATE_HZ, RECORDING_SECONDS, atomic_get(&received_blocks),
	       atomic_get(&receive_errors), atomic_get(&transmit_errors),
	       atomic_get(&stream_dropped_blocks),
	       recording_buffer[RECORDING_SLOTS - 1] != NULL ? "ok" : "missing");
}

static void start_recording(void)
{
	int free_slot = NO_RECORDING_SLOT;

	for (int slot = 0; slot < RECORDING_SLOTS; slot++) {
		if (!recording_slot_in_use[slot] && recording_buffer[slot] != NULL) {
			free_slot = slot;
			break;
		}
	}
	if (!atomic_get(&microphone_ready) || free_slot == NO_RECORDING_SLOT ||
	    atomic_get(&streaming) || atomic_get(&filling_slot) != NO_RECORDING_SLOT) {
		print_status();
		return;
	}
	recording_slot_in_use[free_slot] = true;
	recorded_samples = 0;
	atomic_set(&recording_receive_error[free_slot], 0);
	atomic_set(&filling_slot, free_slot);
}

static void start_streaming(void)
{
	if (!atomic_get(&microphone_ready) || is_recording_busy()) {
		print_status();
		return;
	}
	k_msgq_purge(&stream_queue);
	atomic_set(&stream_dropped_blocks, 0);
	atomic_set(&streaming, 1);
}

static void stop(void)
{
	atomic_set(&streaming, 0);
	atomic_set(&listening_requested, 0);
	atomic_set(&filling_slot, NO_RECORDING_SLOT);
	k_msgq_purge(&stream_queue);
	k_msgq_purge(&completed_recordings);
	memset(recording_slot_in_use, 0, sizeof(recording_slot_in_use));
}

static void handle_command(unsigned char command)
{
	switch (command) {
	case 'l':
		atomic_set(&listening_requested, 1);
		break;
	case 'r':
		start_recording();
		break;
	case 's':
		start_streaming();
		break;
	case 'x':
		stop();
		print_status();
		break;
	case '?':
		print_status();
		break;
	default:
		break;
	}
}

static bool button_pressed_edge(void)
{
	static bool stable_pressed;
	static bool last_reading;
	static int64_t last_change_ms;
	const bool reading = gpio_pin_get_dt(&button) == 1;
	const int64_t now = k_uptime_get();

	if (reading != last_reading) {
		last_reading = reading;
		last_change_ms = now;
	} else if (reading != stable_pressed && now - last_change_ms >= BUTTON_DEBOUNCE_MS) {
		stable_pressed = reading;
		return stable_pressed;
	}
	return false;
}

/* The first button press turns the headphones on; every further press records one clip. */
static void service_controls(void)
{
	unsigned char command;

	while (uart_poll_in(console, &command) == 0) {
		handle_command(command);
	}
	if (button_pressed_edge()) {
		if (atomic_get(&listening_requested)) {
			start_recording();
		} else {
			atomic_set(&listening_requested, 1);
		}
	}
	/* Lit from the start of a clip until it has reached the PC. */
	gpio_pin_set_dt(&led, atomic_get(&streaming) || is_recording_busy());
}

static void send_recording(int slot)
{
	const uint8_t flags =
	        atomic_get(&recording_receive_error[slot]) ? FRAME_FLAG_RECEIVE_ERROR : 0;
	uint32_t sequence = 0;

	for (size_t first = 0; first < RECORDING_SAMPLES; first += FRAMES_PER_BLOCK) {
		const uint16_t count = MIN(FRAMES_PER_BLOCK, RECORDING_SAMPLES - first);

		send_frame(FRAME_KIND_RECORDING, flags, sequence++, first,
		           &recording_buffer[slot][first * BYTES_PER_SAMPLE], count);
		service_controls();
	}
	send_frame(FRAME_KIND_RECORDING_END, flags, sequence, RECORDING_SAMPLES, NULL, 0);
}

int main(void)
{
	gpio_pin_configure_dt(&led, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&button, GPIO_INPUT);
	for (int slot = 0; slot < RECORDING_SLOTS; slot++) {
		recording_buffer[slot] =
		        shared_multi_heap_aligned_alloc(SMH_REG_ATTR_EXTERNAL, 4, RECORDING_BYTES);
	}
	print_status();

	while (true) {
		struct stream_block block;
		int completed_slot;

		service_controls();

		if (k_msgq_get(&completed_recordings, &completed_slot, K_NO_WAIT) == 0) {
			send_recording(completed_slot);
			recording_slot_in_use[completed_slot] = false;
			print_status();
		} else if (atomic_get(&streaming)) {
			if (k_msgq_get(&stream_queue, &block, K_MSEC(CONTROL_POLL_MS)) == 0) {
				send_frame(FRAME_KIND_STREAM, 0, block.first_sample_index /
				           FRAMES_PER_BLOCK, block.first_sample_index, block.payload,
				           FRAMES_PER_BLOCK);
			}
		} else {
			k_msleep(CONTROL_POLL_MS);
		}
	}
	return 0;
}
