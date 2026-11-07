#ifndef HOST_CLOCK_H
#define HOST_CLOCK_H
#include <zephyr/kernel.h>
#include <time.h>
#define SYS_CLOCK_REALTIME 1
int sys_clock_settime(int, const struct timespec *);
#endif
