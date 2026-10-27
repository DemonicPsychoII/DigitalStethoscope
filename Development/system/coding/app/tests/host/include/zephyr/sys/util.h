#ifndef HOST_UTIL_H
#define HOST_UTIL_H
#include <zephyr/kernel.h>
#include <ctype.h>
#include <errno.h>

static inline size_t host_minimum(size_t first, size_t second)
{
    size_t result = second;
    if(first < second)
    {
        result = first;
    }
    return result;
}

#define MIN(first, second)               host_minimum((first), (second))
#define BUILD_ASSERT(condition, message) _Static_assert(condition, message)

static inline int char2hex(char character, uint8_t *value)
{
    int result = -EINVAL; /**< Invalid argument or unsupported input in the host boundary. */
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
