#ifndef STETHO_DSP_H
#define STETHO_DSP_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#define STETHO_RATE 16000
#define STETHO_ENVELOPE_RATE 100
#define STETHO_ENVELOPE_COUNT 800
#define STETHO_HOP 160
#define STETHO_WINDOW (2 * STETHO_HOP)
enum stetho_filter { FILTER_RAW, FILTER_MURMUR, FILTER_BPM, FILTER_COUNT };
struct stetho_biquad {
	float b0, b1, b2, a1, a2, z1, z2;
};
struct stetho_dsp {
	struct stetho_biquad filters[2][2];
	float weights[FILTER_COUNT], gain;
	float envelope[STETHO_ENVELOPE_COUNT], envelope_sum;
	unsigned int envelope_samples, envelope_head, envelope_used, since_estimate;
	float bpm, quality;
	bool bpm_valid;
	uint64_t samples;
};
struct stetho_levels {
	float input_rms, output_rms, input_peak, output_peak;
	uint32_t input_clips, output_clips;
};
struct stetho_replay {
	const int16_t *clip;
	size_t length, emitted, target_length;
	unsigned int speed_percent, next_offset;
	size_t previous_start;
	float tail[STETHO_HOP], next[STETHO_HOP];
	bool first;
};
void stetho_dsp_init(struct stetho_dsp *dsp);
void stetho_dsp_reset_bpm(struct stetho_dsp *dsp);
void stetho_dsp_process(struct stetho_dsp *dsp, const float *input, float *audible, float *filtered,
                        size_t count, enum stetho_filter listening, enum stetho_filter analysis,
                        float gain, bool heart, struct stetho_levels *levels);
void stetho_replay_init(struct stetho_replay *replay, const int16_t *clip, size_t length,
                        unsigned int speed_percent);
size_t stetho_replay_read(struct stetho_replay *replay, float *output, size_t count);
float stetho_test_signal(uint64_t sample, unsigned int bpm, bool tone);
#endif
