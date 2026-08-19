#include "peripherals.h"

#include <errno.h>

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/util.h>

#include "analog_backlight.h"
#include "app_logic.h"
#include "audio_loopback.h"
#include "display_touch.h"
#include "gpio_inputs.h"

LOG_MODULE_REGISTER(peripherals, LOG_LEVEL_INF);

#define PROBE_RETRY_MS 50

struct component_definition {
	const char *name;
	const char *hint;
	int (*probe)(void);
	enum presence_evidence success_evidence;
};

static const struct component_definition definitions[COMP_COUNT] = {
        [COMP_BUTTON_LED] =
                {
                        "pushbutton + LED (GPIO16/17)",
                        "controller/pin configuration failed",
                        gpio_inputs_probe_button_led,
                        PRESENCE_CONTROLLER_READY,
                },
        [COMP_SWITCH] =
                {
                        "SP3T switch (GPIO18/21/38)",
                        "common pole to GND; exactly one throw active",
                        gpio_inputs_probe_switch,
                        PRESENCE_PHYSICAL_VERIFIED,
                },
        [COMP_POTENTIOMETER] =
                {
                        "potentiometer (GPIO1, ADC1_CH0)",
                        "ADC conversion or wiring failed",
                        analog_backlight_probe_potentiometer,
                        PRESENCE_TRANSFER_ACCEPTED,
                },
        [COMP_BACKLIGHT] =
                {
                        "backlight PWM (GPIO8, LEDC ch0)",
                        "LEDC controller/duty setup failed",
                        analog_backlight_probe_pwm,
                        PRESENCE_CONTROLLER_READY,
                },
        [COMP_DISPLAY] =
                {
                        "display ILI9341 (SPI2, CS GPIO10)",
                        "driver/geometry/blanking command failed",
                        display_touch_probe_display,
                        PRESENCE_TRANSFER_ACCEPTED,
                },
        [COMP_TOUCH] =
                {
                        "touch XPT2046 (SPI2, CS GPIO7)",
                        "driver not ready; no touch response proven",
                        display_touch_probe_touch,
                        PRESENCE_CONTROLLER_READY,
                },
        [COMP_MICROPHONE] =
                {
                        "mic INMP441 (I2S0)",
                        "check BCLK/WS/SD, power and L/R",
                        audio_loopback_probe_microphone,
                        PRESENCE_PHYSICAL_VERIFIED,
                },
        [COMP_DAC] =
                {
                        "DAC PCM5102A (I2S1)",
                        "TX accepted only; acoustic output still unverified",
                        audio_loopback_probe_dac,
                        PRESENCE_TRANSFER_ACCEPTED,
                },
};

const char *peripherals_component_name(enum component_id component)
{
	return component < COMP_COUNT ? definitions[component].name : "unknown";
}

const char *peripherals_evidence_name(enum presence_evidence evidence)
{
	switch (evidence) {
	case PRESENCE_CONTROLLER_READY:
		return "controller-ready";
	case PRESENCE_TRANSFER_ACCEPTED:
		return "transfer-accepted";
	case PRESENCE_PHYSICAL_VERIFIED:
		return "physical-response";
	default:
		return "not-ready";
	}
}

static enum presence_evidence failure_evidence(enum component_id component, int error)
{
	if (component == COMP_SWITCH && error == -ENODATA) {
		return PRESENCE_CONTROLLER_READY;
	}
	if (component == COMP_MICROPHONE && error == -ENODATA) {
		return PRESENCE_TRANSFER_ACCEPTED;
	}
	return PRESENCE_NOT_READY;
}

size_t peripherals_probe_all(struct peripheral_registry *registry)
{
	size_t operational_count = 0U;

	for (enum component_id id = 0; id < COMP_COUNT; id++) {
		struct app_probe_state probe = {0};
		int rc;

		do {
			rc = definitions[id].probe();
			if (app_probe_record(&probe, rc, PERIPHERAL_MAX_ATTEMPTS)) {
				k_msleep(PROBE_RETRY_MS);
			}
		} while (!probe.done);

		registry->components[id] = (struct component_status){
		        .operational = probe.success,
		        .evidence = probe.success ? definitions[id].success_evidence
		                                  : failure_evidence(id, probe.last_error),
		        .error = probe.last_error,
		        .attempts = probe.attempts,
		};
		if (probe.success) {
			operational_count++;
		}
	}
	return operational_count;
}

void peripherals_report(const struct peripheral_registry *registry)
{
	size_t usable = 0U;

	for (enum component_id id = 0; id < COMP_COUNT; id++) {
		usable += registry->components[id].operational ? 1U : 0U;
	}
	LOG_INF("---- peripheral probe: %u of %u operational (max %u attempts each) ----",
	        (unsigned int)usable, COMP_COUNT, PERIPHERAL_MAX_ATTEMPTS);
	for (enum component_id id = 0; id < COMP_COUNT; id++) {
		const struct component_status *status = &registry->components[id];

		if (status->operational) {
			LOG_INF("[ OK ] %s (%s, attempt %u)", definitions[id].name,
			        peripherals_evidence_name(status->evidence), status->attempts);
		} else {
			LOG_WRN("[ -- ] %s (%s, err %d after %u attempts) - %s",
			        definitions[id].name, peripherals_evidence_name(status->evidence),
			        status->error, status->attempts, definitions[id].hint);
		}
	}
	LOG_INF("Evidence labels describe firmware knowledge, not blanket physical presence");
}

bool peripherals_operational(const struct peripheral_registry *registry,
                             enum component_id component)
{
	return component < COMP_COUNT && registry->components[component].operational;
}

void peripherals_disable(struct peripheral_registry *registry, enum component_id component,
                         int error)
{
	if (component >= COMP_COUNT) {
		return;
	}
	registry->components[component].operational = false;
	registry->components[component].error = error;
	LOG_ERR("component disabled: %s (err %d)", definitions[component].name, error);
}

void peripherals_note_physical(struct peripheral_registry *registry, enum component_id component)
{
	if (component < COMP_COUNT && registry->components[component].operational) {
		registry->components[component].evidence = PRESENCE_PHYSICAL_VERIFIED;
	}
}
