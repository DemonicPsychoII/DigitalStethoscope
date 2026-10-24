/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

#include "portal.h"
#include <errno.h>

int portal_start(void)
{
    return -ENOSYS; /**< Service is not implemented in this stage. */
}

int portal_stop(void)
{
    return 0;
}

void portal_setNetworks(const struct wifi_scan_entry *list, size_t count)
{
    (void)list;
    (void)count;
}

void portal_setStatus(enum portal_status status, int error)
{
    (void)status;
    (void)error;
}

void portal_setAddress(const char *address)
{
    (void)address;
}

int portal_waitForRequest(struct portal_request *request, k_timeout_t timeout)
{
    (void)request;
    k_sleep(timeout);
    return -EAGAIN; /**< No result is available yet. */
}
