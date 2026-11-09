#include_next <errno.h>

/* Zephyr's C library defines ESTALE; MinGW's does not. The value only has to
 * differ from every other host error number, and MinGW's end at 140. */
#ifndef ESTALE
#define ESTALE 200
#endif
