#ifndef STETHO_AUDIO_LOOPBACK_H
#define STETHO_AUDIO_LOOPBACK_H

#include <stdbool.h>
#include <stdint.h>

struct audio_snapshot {
	bool running;
	uint32_t blocks;
	uint32_t errors;
	int32_t peak;
};

int audio_loopback_probe_microphone(void);
int audio_loopback_probe_dac(void);
int audio_loopback_start(void);
void audio_loopback_snapshot(struct audio_snapshot *snapshot);

#endif
