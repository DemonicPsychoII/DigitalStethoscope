#ifndef STETHO_SD_STORAGE_H
#define STETHO_SD_STORAGE_H

/* FatFs resolves the volume by disk name, so this must stay "/<disk-name>:". */
#define SD_STORAGE_MOUNT_POINT "/SD:"

int sd_storage_probe(void);

#endif
