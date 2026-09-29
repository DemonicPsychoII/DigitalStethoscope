#ifndef STETHO_PERIPHERALS_H
#define STETHO_PERIPHERALS_H

#include <stdbool.h>
#include <stddef.h>

#include "app_types.h"

#define PERIPHERAL_MAX_ATTEMPTS 4U

struct peripheral_registry {
	struct component_status components[COMP_COUNT];
};

size_t peripherals_probe_all(struct peripheral_registry *registry);
void peripherals_report(const struct peripheral_registry *registry);
bool peripherals_operational(const struct peripheral_registry *registry,
                             enum component_id component);
void peripherals_disable(struct peripheral_registry *registry, enum component_id component,
                         int error);
void peripherals_note_physical(struct peripheral_registry *registry, enum component_id component);
const char *peripherals_component_name(enum component_id component);
const char *peripherals_evidence_name(enum presence_evidence evidence);

#endif
