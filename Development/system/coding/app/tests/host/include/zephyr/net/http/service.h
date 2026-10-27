#ifndef HOST_HTTP_SERVICE_H
#define HOST_HTTP_SERVICE_H
#include <zephyr/net/http/server.h>

struct http_service_desc
{
    int *fd;
    const char *host;
    uint16_t *port;
};

#define HTTP_SERVICE_DEFINE(name, address, port_pointer, ...) \
    static int name##_descriptor = -1;                        \
    static struct http_service_desc name = {&name##_descriptor, address, port_pointer}

struct host_http_resource
{
    const char *path;
    const struct http_resource_detail_common *detail;
};

#define HTTP_RESOURCE_DEFINE(name, service, resource_path, resource_detail) \
    static const struct host_http_resource name __attribute__((used)) = {resource_path, (const struct http_resource_detail_common *)resource_detail}
#endif
