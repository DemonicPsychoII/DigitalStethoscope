#ifndef STETHO_AUDIO_LOOPBACK_H
#define STETHO_AUDIO_LOOPBACK_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
struct audio_snapshot {
	bool running, capturing, replaying, bpm_valid;
	uint32_t blocks, errors, restarts, rx_errors, tx_errors, allocation_errors;
	int32_t peak;
	uint32_t input_rms_ppm, output_rms_ppm, input_peak_ppm, output_peak_ppm;
	uint32_t input_clips, output_clips, processing_max_us, deadline_misses;
	uint32_t rx_buffers_used, tx_buffers_used, clip_frames, replay_frames;
	uint32_t bpm_tenths, quality_percent, measured_ms, fixture_frames;
	unsigned int source;
};
int audio_loopback_probe_microphone(void);
int audio_loopback_probe_dac(void);
int audio_loopback_start(void);
void audio_loopback_snapshot(struct audio_snapshot *snapshot);
int audio_fixture_reset(void);
int audio_fixture_append(const int16_t *samples, size_t count);
#endif
