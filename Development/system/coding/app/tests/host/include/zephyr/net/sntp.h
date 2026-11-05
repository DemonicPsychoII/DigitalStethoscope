#ifndef HOST_SNTP_H
#define HOST_SNTP_H
#include <zephyr/net/host_network.h>

struct sntp_time
{
    uint64_t seconds;
    uint32_t fraction;
    uint32_t uncertainty_us;
};

struct sntp_ctx
{
    struct
    {
        int fd;
    } sock;
};

int sntp_init(struct sntp_ctx *, const struct net_sockaddr *, net_socklen_t);
int sntp_query(struct sntp_ctx *, uint32_t, struct sntp_time *);
int sntp_recv_response(struct sntp_ctx *, uint32_t, struct sntp_time *);
void sntp_close(struct sntp_ctx *);
#endif
