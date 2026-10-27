/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

#include "wifi.h"
#include <errno.h>

int wifi_init(void)
{
    return -ENOSYS; /**< Service is not implemented in this stage. */
}

bool wifi_isValidNetwork(const struct wifi_network *network)
{
    (void)network;
    return false;
}

int wifi_connect(const struct wifi_network *network)
{
    (void)network;
    return -ENOSYS; /**< Service is not implemented in this stage. */
}

int wifi_waitForConnection(k_timeout_t timeout)
{
    (void)timeout;
    return -ENOSYS; /**< Service is not implemented in this stage. */
}

int wifi_disconnect(void)
{
    return 0;
}

bool wifi_isConnected(void)
{
    return false;
}

int wifi_getAddress(char *text, size_t size)
{
    if(text != NULL && size > 0)
    {
        text[0] = '\0';
    }
    return -ENOTCONN; /**< Station is not connected. */
}

int wifi_startScan(void)
{
    return -ENOSYS; /**< Service is not implemented in this stage. */
}

int wifi_cancelScan(void)
{
    return 0;
}

int wifi_waitForScanResult(struct wifi_scan_entry *list, size_t listSize, k_timeout_t timeout)
{
    (void)list;
    (void)listSize;
    (void)timeout;
    return -ENOSYS; /**< Service is not implemented in this stage. */
}

int wifi_startHotspot(void)
{
    return -ENOSYS; /**< Service is not implemented in this stage. */
}

int wifi_stopHotspot(void)
{
    return 0;
}

int wifi_startDHCPServer(void)
{
    return -ENOSYS; /**< Service is not implemented in this stage. */
}

int wifi_stopDHCPServer(void)
{
    return 0;
}
