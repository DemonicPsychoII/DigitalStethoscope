#ifndef HOST_FLASH_MAP_H
#define HOST_FLASH_MAP_H
#include <errno.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <sys/types.h>
#include <zephyr/sys/util.h>

/* The host model has the settings and server profile partitions of the project layout; the server profile is erased unless a scenario programs it. */
#define PARTITION_ID(label)                            0
#define PARTITION_OFFSET(label)                        HOST_PARTITION_OFFSET_##label
#define PARTITION_SIZE(label)                          HOST_PARTITION_SIZE_##label
#define HOST_PARTITION_OFFSET_storage_partition        0xE80000
#define HOST_PARTITION_SIZE_storage_partition          0x30000
#define HOST_PARTITION_OFFSET_server_profile_partition 0xF00000
#define HOST_PARTITION_SIZE_server_profile_partition   0x30000
#define HOST_ERASED_FLASH_BYTE                         0xFFU

struct flash_area
{
    uint8_t id;
};

/* Bytes from host_server_profile_image_length onwards read as erased flash. */
static uint8_t host_server_profile_image[HOST_PARTITION_SIZE_server_profile_partition];
static size_t host_server_profile_image_length;
/* A read that covers this offset fails with host_flash_read_error; a negative offset injects no error. */
static off_t host_flash_read_error_offset = -1;
static int host_flash_read_error;

static inline int flash_area_open(uint8_t id, const struct flash_area **area)
{
    static const struct flash_area server_profile_area = {0};
    *area = &server_profile_area;
    return (id == 0U) ? 0 : -ENOENT; /**< Unknown partition in the host model. */
}

static inline int flash_area_read(const struct flash_area *area, off_t offset, void *data, size_t length)
{
    (void)area;
    if((offset < 0) || ((size_t)offset + length > sizeof(host_server_profile_image)))
        return -EINVAL; /**< Read outside the partition, as the flash map rejects it. */
    if((host_flash_read_error_offset >= offset) && (host_flash_read_error_offset < offset + (off_t)length))
        return host_flash_read_error;
    uint8_t *bytes = data;
    for(size_t index = 0; index < length; index++)
    {
        const size_t position = (size_t)offset + index;
        bytes[index] = (position < host_server_profile_image_length) ? host_server_profile_image[position] : HOST_ERASED_FLASH_BYTE;
    }
    return 0;
}

static inline void flash_area_close(const struct flash_area *area)
{
    (void)area;
}
#endif
