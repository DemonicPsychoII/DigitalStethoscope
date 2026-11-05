#ifndef HOST_BYTEORDER_H
#define HOST_BYTEORDER_H
#include <stdint.h>

static inline uint16_t sys_get_le16(const uint8_t source[2])
{
    return (uint16_t)(source[0] | (source[1] << 8));
}

static inline uint32_t sys_get_le32(const uint8_t source[4])
{
    return (uint32_t)source[0] | ((uint32_t)source[1] << 8) | ((uint32_t)source[2] << 16) | ((uint32_t)source[3] << 24);
}
#endif
