#ifndef HOST_ESP_MAC_H
#define HOST_ESP_MAC_H
#include <stdint.h>

#ifndef ESP_OK
#define ESP_OK 0
#endif
#define ESP_ERR_INVALID_CRC 0x10D

typedef int esp_err_t;

esp_err_t esp_efuse_mac_get_default(uint8_t *mac);
#endif
