#ifndef STETHO_GPIO_INPUTS_H
#define STETHO_GPIO_INPUTS_H

#include <stdbool.h>
#include <zephyr/drivers/gpio.h>

int gpio_inputs_probe_button_led(void);
int gpio_inputs_probe_switch(void);
void gpio_inputs_get_initial(bool *button_pressed, int *switch_position);
int gpio_inputs_start(bool button_enabled, bool switch_enabled, gpio_flags_t interrupt_mode);
int gpio_inputs_set_led(bool enabled);

#endif
