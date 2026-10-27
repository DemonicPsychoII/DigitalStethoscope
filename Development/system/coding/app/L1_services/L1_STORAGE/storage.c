/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

#include "storage.h"
#include <errno.h>

int storage_init(void)
{
    return -ENOSYS; /**< Service is not implemented in this stage. */
}

int storage_read(const char *name, void *data, size_t size)
{
    (void)name;
    (void)data;
    (void)size;
    return -ENOSYS; /**< Service is not implemented in this stage. */
}

int storage_write(const char *name, const void *data, size_t size)
{
    (void)name;
    (void)data;
    (void)size;
    return -ENOSYS; /**< Service is not implemented in this stage. */
}
