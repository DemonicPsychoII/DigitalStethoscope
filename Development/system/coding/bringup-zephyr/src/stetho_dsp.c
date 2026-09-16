/* Portable DSP shared by the firmware and host evaluation. Cutoffs are initial
 * engineering candidates, not clinically validated filter prescriptions. */
#include "stetho_dsp.h"
#include <math.h>
#include <string.h>
#define PI_F 3.14159265358979323846f
static float clamp(float x, float lo, float hi) { return fminf(hi, fmaxf(lo, x)); }
static void design(struct stetho_biquad *b, float hz, bool highpass)
{
	float w = 2.0f * PI_F * hz / STETHO_RATE, c = cosf(w), a = sinf(w) / 1.41421356237f;
	float norm = 1.0f / (1.0f + a);
	b->b0 = (highpass ? 1.0f + c : 1.0f - c) * 0.5f * norm;
	b->b1 = (highpass ? -2.0f : 2.0f) * b->b0;
	b->b2 = b->b0;
	b->a1 = -2.0f * c * norm;
	b->a2 = (1.0f - a) * norm;
}
static float biquad(struct stetho_biquad *b, float x)
{
	float y = b->b0 * x + b->z1;
	b->z1 = b->b1 * x - b->a1 * y + b->z2;
	b->z2 = b->b2 * x - b->a2 * y;
	return y;
}
void stetho_dsp_reset_bpm(struct stetho_dsp *d)
{
	memset(d->envelope, 0, sizeof(d->envelope));
	d->envelope_head = d->envelope_used = d->envelope_samples = d->since_estimate = 0;
	d->envelope_sum = d->bpm = d->quality = 0;
	d->bpm_valid = false;
}
void stetho_dsp_init(struct stetho_dsp *d)
{
	memset(d, 0, sizeof(*d));
	d->weights[FILTER_RAW] = 1;
	design(&d->filters[0][0], 40, true);
	design(&d->filters[0][1], 800, false);
	design(&d->filters[1][0], 25, true);
	design(&d->filters[1][1], 150, false);
}
static void estimate(struct stetho_dsp *d)
{
	float centered[STETHO_ENVELOPE_COUNT], corr[201] = {0}, mean = 0, energy = 0;
	d->bpm_valid = false;
	d->bpm = d->quality = 0;
	if (d->envelope_used < STETHO_ENVELOPE_COUNT)
		return;
	for (unsigned int i = 0; i < STETHO_ENVELOPE_COUNT; i++)
		mean += d->envelope[i];
	mean /= STETHO_ENVELOPE_COUNT;
	for (unsigned int i = 0; i < STETHO_ENVELOPE_COUNT; i++) {
		centered[i] = d->envelope[(d->envelope_head + i) % STETHO_ENVELOPE_COUNT] - mean;
		energy += centered[i] * centered[i];
	}
	float recent = 0;
	for (unsigned int i = 0; i < 200; i++)
		recent += d->envelope[(d->envelope_head + STETHO_ENVELOPE_COUNT - 1 - i) %
		                      STETHO_ENVELOPE_COUNT];
	/* Require envelope modulation, not just a periodic carrier, and expire a
	 * measurement after two seconds without appreciable input. */
	if (mean < 0.00001f || energy < 0.0000001f ||
	    sqrtf(energy / STETHO_ENVELOPE_COUNT) < 0.15f * mean || recent / 200 < 0.00001f)
		return;
	float best = 0;
	for (unsigned int lag = 30; lag <= 200; lag++) {
		float cross = 0, e1 = 0, e2 = 0;
		for (unsigned int i = lag; i < STETHO_ENVELOPE_COUNT; i++) {
			float a = centered[i], b = centered[i - lag];
			cross += a * b;
			e1 += a * a;
			e2 += b * b;
		}
		corr[lag] = cross / sqrtf(fmaxf(e1 * e2, 1e-20f));
		if (corr[lag] > best)
			best = corr[lag];
	}
	/* Choose the first strong local peak, avoiding a multiple-period maximum.
	 * S1/S2 ambiguity remains an explicit evaluation limitation. */
	for (unsigned int lag = 30; lag <= 200; lag++) {
		if (corr[lag] >= 0.9f * best && corr[lag] >= 0.55f &&
		    (lag == 30 || corr[lag] >= corr[lag - 1]) &&
		    (lag == 200 || corr[lag] >= corr[lag + 1])) {
			float refined = (float)lag;
			if (lag > 30 && lag < 200) {
				float denom = corr[lag - 1] - 2 * corr[lag] + corr[lag + 1];
				if (fabsf(denom) > 1e-6f)
					refined += clamp(0.5f * (corr[lag - 1] - corr[lag + 1]) /
					                         denom,
					                 -0.5f, 0.5f);
			}
			d->bpm = 6000.0f / refined;
			d->quality = clamp(corr[lag], 0, 1);
			d->bpm_valid = true;
			return;
		}
	}
}
void stetho_dsp_process(struct stetho_dsp *d, const float *in, float *out, float *filtered,
                        size_t n, enum stetho_filter listening, enum stetho_filter analysis,
                        float gain, bool heart, struct stetho_levels *l)
{
	memset(l, 0, sizeof(*l));
	if (listening >= FILTER_COUNT || listening < 0)
		listening = FILTER_RAW;
	if (analysis >= FILTER_COUNT || analysis < 0)
		analysis = FILTER_BPM;
	gain = clamp(gain, 0, 8);
	for (size_t i = 0; i < n; i++) {
		float x = isfinite(in[i]) ? in[i] : 0;
		float bands[FILTER_COUNT] = {
		        x, biquad(&d->filters[0][1], biquad(&d->filters[0][0], x)),
		        biquad(&d->filters[1][1], biquad(&d->filters[1][0], x))};
		float y = 0;
		enum stetho_filter target = heart ? listening : FILTER_RAW;
		for (unsigned int j = 0; j < FILTER_COUNT; j++) {
			d->weights[j] +=
			        ((j == (unsigned int)target ? 1.0f : 0.0f) - d->weights[j]) /
			        320.0f;
			y += d->weights[j] * bands[j];
		}
		filtered[i] = y;
		d->gain += (gain - d->gain) / 320.0f;
		float amplified = y * d->gain;
		out[i] = clamp(amplified, -1, 0.999999f);
		l->input_clips += fabsf(x) >= 0.999f;
		l->output_clips += fabsf(amplified) >= 1;
		l->input_peak = fmaxf(l->input_peak, fabsf(x));
		l->output_peak = fmaxf(l->output_peak, fabsf(out[i]));
		l->input_rms += x * x;
		l->output_rms += out[i] * out[i];
		if (heart) {
			d->envelope_sum += fabsf(bands[analysis]);
			if (++d->envelope_samples == STETHO_RATE / STETHO_ENVELOPE_RATE) {
				d->envelope[d->envelope_head] =
				        d->envelope_sum / d->envelope_samples;
				d->envelope_head = (d->envelope_head + 1) % STETHO_ENVELOPE_COUNT;
				if (d->envelope_used < STETHO_ENVELOPE_COUNT)
					d->envelope_used++;
				d->envelope_samples = 0;
				d->envelope_sum = 0;
				if (++d->since_estimate == STETHO_ENVELOPE_RATE) {
					estimate(d);
					l->bpm_updated = d->bpm_valid;
					d->since_estimate = 0;
				}
			}
		} else {
			d->bpm_valid = false;
			d->bpm = d->quality = 0;
		}
		d->samples++;
	}
	if (n) {
		l->input_rms = sqrtf(l->input_rms / n);
		l->output_rms = sqrtf(l->output_rms / n);
	}
	if (l->input_clips) {
		stetho_dsp_reset_bpm(d);
		l->bpm_updated = false;
	}
}
void stetho_replay_init(struct stetho_replay *r, const int16_t *clip, size_t length,
                        unsigned int speed)
{
	memset(r, 0, sizeof(*r));
	r->clip = clip;
	r->length = length;
	r->speed_percent = (speed == 50 || speed == 75) ? speed : 100;
	r->target_length = length * 100 / r->speed_percent;
	r->next_offset = STETHO_HOP;
	r->first = true;
}
static float sample(const struct stetho_replay *r, size_t i)
{
	return i < r->length ? r->clip[i] / 32768.0f : 0;
}
static void synthesize(struct stetho_replay *r)
{
	size_t expected = r->emitted * r->speed_percent / 100, start = expected;
	if (!r->first && r->speed_percent != 100 && expected + STETHO_WINDOW + 80 < r->length) {
		float best = -2;
		size_t lo = expected > 80 ? expected - 80 : 0;
		if (lo <= r->previous_start)
			lo = r->previous_start + 1;
		for (size_t p = lo; p <= expected + 80; p += 4) {
			float cross = 0, energy = 1e-12f, tail_energy = 1e-12f;
			for (size_t j = 0; j < STETHO_HOP; j += 2) {
				float x = sample(r, p + j);
				cross += x * r->tail[j];
				energy += x * x;
				tail_energy += r->tail[j] * r->tail[j];
			}
			float c = cross / sqrtf(energy * tail_energy);
			if (c > best) {
				best = c;
				start = p;
			}
		}
	}
	for (size_t j = 0; j < STETHO_HOP; j++) {
		float w = (float)j / STETHO_HOP;
		r->next[j] = r->first ? sample(r, start + j)
		                      : (1 - w) * r->tail[j] + w * sample(r, start + j);
		r->tail[j] = sample(r, start + STETHO_HOP + j);
	}
	r->previous_start = start;
	r->first = false;
	r->next_offset = 0;
}
size_t stetho_replay_read(struct stetho_replay *r, float *out, size_t n)
{
	size_t written = 0;
	while (written < n && r->emitted < r->target_length) {
		if (r->next_offset == STETHO_HOP)
			synthesize(r);
		out[written++] = r->next[r->next_offset++];
		r->emitted++;
	}
	for (size_t i = written; i < n; i++)
		out[i] = 0;
	return written;
}
float stetho_test_signal(uint64_t sample_index, unsigned int bpm, bool tone)
{
	float t = (float)(sample_index % STETHO_RATE) / STETHO_RATE;
	if (tone)
		return 0.03f * sinf(2 * PI_F * 440 * t);
	if (bpm < 30 || bpm > 200)
		bpm = 72;
	uint32_t period = STETHO_RATE * 60 / bpm;
	float phase = (float)(sample_index % period) / STETHO_RATE;
	float s1 = expf(-phase * phase / 0.0008f);
	float s2 = expf(-(phase - 0.28f) * (phase - 0.28f) / 0.00045f) * 0.55f;
	return 0.2f * (s1 + s2) * sinf(2 * PI_F * 80 * t);
}
