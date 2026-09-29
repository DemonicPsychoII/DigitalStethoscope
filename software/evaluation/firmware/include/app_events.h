#ifndef STETHO_APP_EVENTS_H
#define STETHO_APP_EVENTS_H

#include <zephyr/kernel.h>

/* Defined by main.c. Callbacks only enqueue; main is the sole consumer. */
extern struct k_msgq app_event_queue;

#endif
