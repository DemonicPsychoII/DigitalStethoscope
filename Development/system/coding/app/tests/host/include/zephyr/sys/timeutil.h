#ifndef HOST_TIMEUTIL_H
#define HOST_TIMEUTIL_H
#include <time.h>
#define SYS_TIME_T_MAX ((((time_t)1 << (8 * sizeof(time_t) - 2)) - 1) * 2 + 1)
#endif
