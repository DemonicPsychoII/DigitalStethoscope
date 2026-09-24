#ifndef STETHO_DISPLAY_TOUCH_H
#define STETHO_DISPLAY_TOUCH_H

#include <stddef.h>
#include <stdint.h>

void display_touch_stats(uint32_t *errors, uint32_t *drops, uint32_t *max_ms);
int display_touch_probe_display(void);
int display_touch_probe_touch(void);
int display_touch_show_color(uint8_t color_index);
size_t display_touch_color_count(void);
const char *display_touch_color_name(uint8_t color_index);

#endif
