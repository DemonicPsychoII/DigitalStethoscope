#ifndef HOST_NETWORK_H
#define HOST_NETWORK_H
#include <zephyr/sys/util.h>
#include <stdio.h>
#include <string.h>
#define WIFI_PSK_MIN_LEN                 8
#define SYS_FOREVER_MS                   -1
#define WIFI_CHANNEL_ANY                 0
#define WIFI_MFP_OPTIONAL                0
#define WIFI_FREQ_BAND_2_4_GHZ           0
#define NET_AF_INET                      2
#define NET_ADDR_PREFERRED               1
#define NET_ADDR_MANUAL                  2
#define WIFI_STATUS_CONN_FAIL            1
#define WIFI_STATUS_CONN_WRONG_PASSWORD  2
#define WIFI_STATUS_CONN_TIMEOUT         3
#define WIFI_STATUS_CONN_AP_NOT_FOUND    4
#define WIFI_REASON_DISCONN_USER_REQUEST 2

enum wifi_security_type
{
    WIFI_SECURITY_TYPE_NONE,
    WIFI_SECURITY_TYPE_PSK,
    WIFI_SECURITY_TYPE_WPA_PSK,
    WIFI_SECURITY_TYPE_PSK_SHA256,
    WIFI_SECURITY_TYPE_SAE,
    WIFI_SECURITY_TYPE_EAP,
    WIFI_SECURITY_TYPE_WEP
};

enum
{
    NET_EVENT_WIFI_CONNECT_RESULT = 1,
    NET_EVENT_WIFI_DISCONNECT_RESULT = 2,
    NET_EVENT_WIFI_SCAN_RESULT = 4,
    NET_EVENT_WIFI_SCAN_DONE = 8,
    NET_EVENT_IPV4_ADDR_ADD = 16,
    NET_EVENT_IPV4_ADDR_DEL = 32
};

enum
{
    NET_REQUEST_WIFI_CONNECT = 1,
    NET_REQUEST_WIFI_DISCONNECT,
    NET_REQUEST_WIFI_SCAN,
    NET_REQUEST_WIFI_AP_ENABLE,
    NET_REQUEST_WIFI_AP_DISABLE
};

struct net_if
{
    int identity;
};

struct net_in_addr
{
    uint8_t s4_addr[4];
};

struct net_linkaddr
{
    uint8_t addr[6];
};

struct net_mgmt_event_callback
{
    const void *info;
    void (*handler)(struct net_mgmt_event_callback *, uint64_t, struct net_if *);
    uint64_t event_mask;
};

struct wifi_status
{
    int status;
};

struct wifi_scan_result
{
    uint8_t ssid[32];
    uint8_t ssid_length;
    enum wifi_security_type security;
    int rssi;
};

struct wifi_connect_req_params
{
    const uint8_t *ssid;
    uint8_t ssid_length;
    const uint8_t *psk;
    uint8_t psk_length;
    enum wifi_security_type security;
    int band;
    int channel;
    int mfp;
    int timeout;
};
struct net_if *net_if_get_wifi_sta(void);
struct net_if *net_if_get_wifi_sap(void);
void net_mgmt_init_event_callback(struct net_mgmt_event_callback *, void (*)(struct net_mgmt_event_callback *, uint64_t, struct net_if *), uint64_t);
void net_mgmt_add_event_callback(struct net_mgmt_event_callback *);
int net_mgmt(int, struct net_if *, void *, size_t);
const struct net_in_addr *net_if_ipv4_get_global_addr(struct net_if *, int);
bool net_if_ipv4_addr_rm(struct net_if *, const struct net_in_addr *);
const char *net_addr_ntop(int, const struct net_in_addr *, char *, size_t);
int net_addr_pton(int, const char *, struct net_in_addr *);
void *net_if_ipv4_addr_lookup(struct net_in_addr *, struct net_if **);
void *net_if_ipv4_addr_add(struct net_if *, struct net_in_addr *, int, int);
int net_if_ipv4_set_netmask_by_addr(struct net_if *, struct net_in_addr *, struct net_in_addr *);
void net_if_ipv4_set_gw(struct net_if *, struct net_in_addr *);
struct net_linkaddr *net_if_get_link_addr(struct net_if *);
int net_dhcpv4_server_start(struct net_if *, struct net_in_addr *);
int net_dhcpv4_server_stop(struct net_if *);
#endif
