#ifndef STETHO_ANALOG_BACKLIGHT_H
#define STETHO_ANALOG_BACKLIGHT_H

int analog_backlight_probe_potentiometer(void);
int analog_backlight_probe_pwm(void);
int analog_backlight_read_mv(int *millivolts);
int analog_backlight_set_mv(int millivolts);

#endif
