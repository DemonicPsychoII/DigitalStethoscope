#include "audio_loopback.h"
#include "display_touch.h"
#include "stetho_build_id.h"
#include "stetho_control.h"
#include "stetho_fhir.h"
#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include <zephyr/kernel.h>
#include <zephyr/shell/shell.h>
static int number(const char *s, unsigned int *value)
{
	char *end;
	errno = 0;
	unsigned long n = strtoul(s, &end, 10);
	if (!*s || *s == '-' || *end || errno || n > UINT32_MAX)
		return -EINVAL;
	*value = n;
	return 0;
}
static int command(const struct shell *shell, size_t argc, char **argv)
{
	int rc = -EINVAL;
	if (argc == 2 && !strcmp(argv[1], "status")) {
		struct audio_snapshot a;
		struct stetho_settings s;
		int net;
		bool configured, busy;
		uint32_t display_errors, touch_drops, frame_ms;
		audio_loopback_snapshot(&a);
		stetho_settings_get(&s);
		stetho_network_status(&net, &configured, &busy);
		display_touch_stats(&display_errors, &touch_drops, &frame_ms);
		shell_print(shell,
		            "{\"ms\":%u,\"running\":%u,\"source\":%u,\"filter\":%u,\"analysis\":%u,"
		            "\"speed\":%u,\"volume\":%u,\"heart\":%u,\"point\":%u,\"blocks\":%u,"
		            "\"errors\":%u,\"restarts\":%u,\"rx_errors\":%u,\"tx_errors\":%u,"
		            "\"allocation_errors\":%u,\"in_rms_ppm\":%u,\"out_rms_ppm\":%u,\"in_"
		            "peak_ppm\":%u,\"out_peak_ppm\":%u,\"in_clips\":%u,\"out_clips\":%u,"
		            "\"processing_max_us\":%u,\"deadline_misses\":%u,\"rx_buffers\":%u,"
		            "\"tx_buffers\":%u,\"capturing\":%u,\"replaying\":%u,\"clip_frames\":%"
		            "u,\"fixture_frames\":%u,\"bpm_valid\":%u,\"bpm_tenths\":%u,"
		            "\"quality\":%u,\"measured_ms\":%u,\"display_errors\":%u,\"touch_"
		            "drops\":%u,\"frame_max_ms\":%u,\"network_configured\":%u,\"network_"
		            "busy\":%u,\"network_result\":%d}",
		            k_uptime_get_32(), a.running, a.source, s.filter, s.analysis, s.speed,
		            s.volume, s.heart, s.point, a.blocks, a.errors, a.restarts, a.rx_errors,
		            a.tx_errors, a.allocation_errors, a.input_rms_ppm, a.output_rms_ppm,
		            a.input_peak_ppm, a.output_peak_ppm, a.input_clips, a.output_clips,
		            a.processing_max_us, a.deadline_misses, a.rx_buffers_used,
		            a.tx_buffers_used, a.capturing, a.replaying, a.clip_frames,
		            a.fixture_frames, a.bpm_valid, a.bpm_tenths, a.quality_percent,
		            a.measured_ms, display_errors, touch_drops, frame_ms, configured, busy,
		            net);
		return 0;
	}
	if (argc == 4 && !strcmp(argv[1], "set")) {
		unsigned int value;
		rc = number(argv[3], &value);
		if (!rc)
			rc = stetho_setting_set(argv[2], value);
	} else if (argc == 2 && !strcmp(argv[1], "version")) {
		shell_print(shell, "%s", STETHO_BUILD_ID);
		rc = 0;
	} else if (argc == 2 && !strcmp(argv[1], "restart"))
		rc = audio_loopback_start();
	else if (argc == 2 && (!strcmp(argv[1], "capture") || !strcmp(argv[1], "replay") ||
	                       !strcmp(argv[1], "live"))) {
		stetho_action_request(!strcmp(argv[1], "capture")  ? ACTION_CAPTURE
		                      : !strcmp(argv[1], "replay") ? ACTION_REPLAY
		                                                   : ACTION_LIVE);
		rc = 0;
	} else if (argc == 3 && !strcmp(argv[1], "color")) {
		unsigned int value;
		rc = number(argv[2], &value);
		if (!rc && value < display_touch_color_count())
			rc = display_touch_show_color(value);
		else
			rc = -EINVAL;
	} else if (argc == 3 && !strcmp(argv[1], "fixture") && !strcmp(argv[2], "reset"))
		rc = audio_fixture_reset();
	else if (argc == 4 && !strcmp(argv[1], "fixture") && !strcmp(argv[2], "append")) {
		size_t length = strlen(argv[3]);
		int16_t samples[128];
		if (length && length % 4 == 0 && length <= 512) {
			rc = 0;
			for (size_t i = 0; i < length / 4; i++) {
				char word[5];
				memcpy(word, argv[3] + i * 4, 4);
				word[4] = 0;
				for (size_t j = 0; j < 4; j++)
					if (!strchr("0123456789abcdefABCDEF", word[j]))
						rc = -EINVAL;
				if (rc)
					break;
				samples[i] = (int16_t)strtoul(word, NULL, 16);
			}
			if (!rc)
				rc = audio_fixture_append(samples, length / 4);
		}
	} else if (argc >= 3 && !strcmp(argv[1], "net")) {
		if (argc == 7 && !strcmp(argv[2], "configure")) {
			unsigned int port;
			rc = number(argv[4], &port);
			if (!rc)
				rc = stetho_network_configure(argv[3], port, argv[5], argv[6]);
		} else if (argc == 4 && !strcmp(argv[2], "token"))
			rc = stetho_network_token(argv[3]);
		else if (argc == 3 && !strcmp(argv[2], "send"))
			rc = stetho_network_send();
		else if (argc == 4 && !strcmp(argv[2], "sync"))
			rc = stetho_network_sync(argv[3]);
		else if (argc == 4 && !strcmp(argv[2], "time")) {
			char *end;
			errno = 0;
			long long epoch = strtoll(argv[3], &end, 10);
			rc = *argv[3] && !*end && !errno ? stetho_network_time(epoch) : -EINVAL;
		}
	}
	shell_print(shell, "result=%d", rc);
	return rc;
}
SHELL_CMD_ARG_REGISTER(stetho, NULL,
                       "status | version | set NAME VALUE | capture | replay | live | restart | "
                       "color N | "
                       "fixture reset/append HEX | net configure HOST PORT BASE PATIENT | net time "
                       "EPOCH | net sync HOST | net token TOKEN | net send",
                       command, 2, 5);
