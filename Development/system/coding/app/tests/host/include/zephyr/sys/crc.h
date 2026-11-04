#ifndef HOST_CRC_H
#define HOST_CRC_H
#include <stddef.h>
#include <stdint.h>

static inline uint32_t crc32_ieee_update(uint32_t crc, const uint8_t *data, size_t length)
{
    crc = ~crc;
    for(size_t index = 0; index < length; index++)
    {
        crc ^= data[index];
        for(int bit = 0; bit < 8; bit++)
        {
            crc = (crc >> 1) ^ (0xEDB88320U & (0U - (crc & 1U)));
        }
    }
    return ~crc;
}
#endif
