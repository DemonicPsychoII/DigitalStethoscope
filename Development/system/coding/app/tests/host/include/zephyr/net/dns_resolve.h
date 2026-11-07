#ifndef HOST_DNS_RESOLVE_H
#define HOST_DNS_RESOLVE_H
#include <zephyr/net/host_network.h>

enum dns_query_type
{
    DNS_QUERY_TYPE_A = 1
};

enum dns_resolve_status
{
    DNS_EAI_CANCELED = -101,
    DNS_EAI_INPROGRESS = -100,
    DNS_EAI_ALLDONE = -103
};

struct dns_addrinfo
{
    struct net_sockaddr ai_addr;
    int ai_family;
};

typedef void (*dns_resolve_cb_t)(enum dns_resolve_status, struct dns_addrinfo *, void *);
int dns_get_addr_info(const char *, enum dns_query_type, uint16_t *, dns_resolve_cb_t, void *, int32_t);
int dns_cancel_addr_info_with_name(const char *, enum dns_query_type, uint16_t);
#endif
