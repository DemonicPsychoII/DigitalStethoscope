#ifndef HOST_SOCKET_H
#define HOST_SOCKET_H
#include <zephyr/net/host_network.h>
#define ZSOCK_SOL_SOCKET  1
#define ZSOCK_SO_SNDTIMEO 21

struct zsock_timeval
{
    long tv_sec;
    long tv_usec;
};

int zsock_setsockopt(int, int, int, const void *, net_socklen_t);
#endif
