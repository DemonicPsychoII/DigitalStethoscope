#include "sd_storage.h"

#include <errno.h>
#include <stdbool.h>

#include <ff.h>
#include <zephyr/fs/fs.h>
#include <zephyr/logging/log.h>
#include <zephyr/storage/disk_access.h>

LOG_MODULE_REGISTER(sd_storage, LOG_LEVEL_INF);

#define SD_DISK_NAME "SD"

static FATFS fat;
static struct fs_mount_t mount = {
        .type = FS_FATFS,
        .fs_data = &fat,
        .mnt_point = SD_STORAGE_MOUNT_POINT,
};
static bool probed;
static int probe_result;

static int mount_card(void)
{
	uint32_t sectors = 0U;
	uint32_t sector_size = 0U;
	int rc;

	/* No card-detect line: an empty slot shows up as an init timeout here. */
	rc = disk_access_ioctl(SD_DISK_NAME, DISK_IOCTL_CTRL_INIT, NULL);
	if (rc != 0) {
		LOG_WRN("SD card init failed (no card, or CS/MISO wiring): %d", rc);
		return rc;
	}
	rc = disk_access_ioctl(SD_DISK_NAME, DISK_IOCTL_GET_SECTOR_COUNT, &sectors);
	if (rc == 0) {
		rc = disk_access_ioctl(SD_DISK_NAME, DISK_IOCTL_GET_SECTOR_SIZE, &sector_size);
	}
	if (rc != 0) {
		LOG_ERR("SD card geometry query failed: %d", rc);
		return rc;
	}
	rc = fs_mount(&mount);
	if (rc != 0) {
		LOG_WRN("SD card answered but has no FAT/exFAT volume: %d", rc);
		return rc;
	}
	LOG_INF("SD card mounted at %s (%u MiB)", SD_STORAGE_MOUNT_POINT,
	        (unsigned int)((uint64_t)sectors * sector_size >> 20));
	return 0;
}

int sd_storage_probe(void)
{
	/* The SD stack already retries internally; repeating a failed init would only add
	 * seconds of boot delay when no card is fitted. */
	if (!probed) {
		probe_result = mount_card();
		probed = true;
	}
	return probe_result;
}
