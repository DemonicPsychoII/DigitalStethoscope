#ifndef HOST_ESP_WIFI_H
#define HOST_ESP_WIFI_H
#define WIFI_IF_AP 1
#define ESP_OK     0

typedef struct
{
    struct
    {
        int max_connection;
    } ap;
} wifi_config_t;

int esp_wifi_get_config(int, wifi_config_t *);
int esp_wifi_set_config(int, wifi_config_t *);
#endif
