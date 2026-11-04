#ifndef HOST_FLASH_MAP_H
#define HOST_FLASH_MAP_H
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <sys/types.h>
#include <zephyr/sys/util.h>

/* The host model has the settings and provisioning partitions of the project layout; provisioning is erased. */
#define PARTITION_ID(label)                          0
#define PARTITION_OFFSET(label)                      HOST_PARTITION_OFFSET_##label
#define PARTITION_SIZE(label)                        HOST_PARTITION_SIZE_##label
#define HOST_PARTITION_OFFSET_storage_partition      0xE80000
#define HOST_PARTITION_SIZE_storage_partition        0x30000
#define HOST_PARTITION_OFFSET_provisioning_partition 0xF00000
#define HOST_PARTITION_SIZE_provisioning_partition   0x30000

struct flash_area
{
    uint8_t id;
};

static inline int flash_area_open(uint8_t id, const struct flash_area **area)
{
    static const struct flash_area provisioning_area = {0};
    *area = &provisioning_area;
    return (id == 0U) ? 0 : -ENOENT; /**< Unknown partition in the host model. */
}

static inline int flash_area_read(const struct flash_area *area, off_t offset, void *data, size_t length)
{
    (void)area;
    (void)offset;
    memset(data, 0xFF, length);
    return 0;
}

static inline void flash_area_close(const struct flash_area *area)
{
    (void)area;
}
#endif
