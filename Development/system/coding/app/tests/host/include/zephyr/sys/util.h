#ifndef HOST_UTIL_H
#define HOST_UTIL_H
#include <zephyr/kernel.h>
#include <ctype.h>
#include <errno.h>
#define MIN(first, second)               ((first) < (second) ? (first) : (second))
#define BUILD_ASSERT(condition, message) _Static_assert(condition, message)

static inline int char2hex(char character, uint8_t *value)
{
    int result = -EINVAL;
    if(character >= '0' && character <= '9')
    {
        *value = (uint8_t)(character - '0');
        result = 0;
    }
    else if(character >= 'a' && character <= 'f')
    {
        *value = (uint8_t)(character - 'a' + 10);
        result = 0;
    }
    else if(character >= 'A' && character <= 'F')
    {
        *value = (uint8_t)(character - 'A' + 10);
        result = 0;
    }
    return result;
}
#endif
