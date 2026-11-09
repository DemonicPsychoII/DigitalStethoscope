#ifndef HOST_SOCKET_H
#define HOST_SOCKET_H
#include <sys/types.h>
#include <zephyr/net/host_network.h>
#define ZSOCK_SOL_SOCKET  1
#define ZSOCK_SO_SNDTIMEO 21
#define ZSOCK_POLLIN      1
#define ZSOCK_MSG_PEEK    0x02

struct zsock_timeval
{
    long tv_sec;
    long tv_usec;
};

struct zsock_pollfd
{
    int fd;
    short events;
    short revents;
};

int zsock_setsockopt(int, int, int, const void *, net_socklen_t);
int zsock_poll(struct zsock_pollfd *, int, int);
ssize_t zsock_recv(int, void *, size_t, int);
#endif
