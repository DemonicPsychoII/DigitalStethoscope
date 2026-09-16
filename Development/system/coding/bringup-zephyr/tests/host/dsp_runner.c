/* Host runner links exactly the portable DSP compiled into firmware. */
#include "stetho_dsp.h"
#include "stetho_fhir.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static struct stetho_dsp dsp;
int main(int argc, char **argv)
{
	if (argc == 2 && !strcmp(argv[1], "boundaries")) {
		float in[128], out[128], filtered[128];
		struct stetho_levels levels;
		stetho_dsp_init(&dsp);
		for (size_t i = 0; i < 128; i++)
			in[i] = 0.8f;
		for (size_t i = 0; i < 100; i++)
			stetho_dsp_process(&dsp, in, out, filtered, 128, FILTER_RAW, FILTER_BPM, 8,
			                   true, &levels);
		assert(levels.output_clips == 128);
		for (size_t i = 0; i < 128; i++)
			assert(isfinite(out[i]) && out[i] >= -1 && out[i] < 1);
		for (size_t i = 0; i < 128; i++)
			in[i] = NAN;
		stetho_dsp_process(&dsp, in, out, filtered, 128, FILTER_RAW, FILTER_BPM, 1, true,
		                   &levels);
		for (size_t i = 0; i < 128; i++)
			assert(isfinite(out[i]));
		for (size_t i = 0; i < 128; i++)
			in[i] = 1;
		stetho_dsp_process(&dsp, in, out, filtered, 128, FILTER_RAW, FILTER_BPM, 1, true,
		                   &levels);
		assert(!dsp.bpm_valid && dsp.envelope_used == 0);
		stetho_dsp_process(&dsp, in, out, filtered, 128, FILTER_RAW, FILTER_BPM, 1, false,
		                   &levels);
		assert(!dsp.bpm_valid);
		puts("boundaries PASS");
		return 0;
	}
	if (argc == 2 && !strcmp(argv[1], "fhir")) {
		char json[1024];
		assert(stetho_fhir_json(json, sizeof(json), "test-patient", "eval-1",
		                        "2026-09-16T12:00:00Z", 725) > 0);
		puts(json);
		assert(stetho_fhir_json(json, 10, "p", "id", "2026-09-16T12:00:00Z", 725) < 0);
		assert(stetho_fhir_json(json, sizeof(json), "p\"", "id", "2026-09-16T12:00:00Z",
		                        725) < 0);
		assert(stetho_fhir_json(json, sizeof(json), "p", "id", "2026-09-16T12:00:00Z", 0) <
		       0);
		assert(stetho_fhir_json(json, sizeof(json), "p", "id", "2026-09-16T12:00:00\"",
		                        700) < 0);
		return 0;
	}
	if (argc == 5 && !strcmp(argv[1], "replay")) {
		FILE *input = fopen(argv[3], "rb"), *output = fopen(argv[4], "wb");
		assert(input && output);
		assert(fseek(input, 0, SEEK_END) == 0);
		long size = ftell(input);
		assert(size >= 0 && size % 2 == 0);
		rewind(input);
		int16_t *clip = malloc((size_t)size + 1);
		assert(clip);
		size_t frames = (size_t)size / 2;
		assert(fread(clip, sizeof(*clip), frames, input) == frames);
		fclose(input);
		struct stetho_replay replay;
		stetho_replay_init(&replay, clip, frames, (unsigned)atoi(argv[2]));
		float out[128];
		size_t n;
		while ((n = stetho_replay_read(&replay, out, 128)))
			assert(fwrite(out, sizeof(*out), n, output) == n);
		fclose(output);
		free(clip);
		return 0;
	}
	if (argc != 6) {
		fprintf(stderr, "process FILTER ANALYSIS INPUT.f32 OUTPUT.f32\n");
		return 2;
	}
	FILE *input = fopen(argv[4], "rb"), *output = fopen(argv[5], "wb");
	assert(input && output);
	stetho_dsp_init(&dsp);
	float in[128], out[128], filtered[128];
	size_t n;
	while ((n = fread(in, sizeof(*in), 128, input))) {
		struct stetho_levels levels;
		stetho_dsp_process(&dsp, in, out, filtered, n, atoi(argv[2]), atoi(argv[3]), 1,
		                   true, &levels);
		assert(fwrite(out, sizeof(*out), n, output) == n);
		if (dsp.samples % STETHO_RATE < 128)
			printf("%llu,%u,%.3f,%.3f\n", (unsigned long long)dsp.samples,
			       dsp.bpm_valid, dsp.bpm, dsp.quality);
	}
	fclose(input);
	fclose(output);
	return 0;
}
