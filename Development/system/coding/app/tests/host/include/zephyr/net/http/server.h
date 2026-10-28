#ifndef HOST_HTTP_SERVER_H
#define HOST_HTTP_SERVER_H
#include <zephyr/kernel.h>

enum http_status
{
    HTTP_200_OK = 200,
    HTTP_202_ACCEPTED = 202,
    HTTP_400_BAD_REQUEST = 400,
    HTTP_404_NOT_FOUND = 404,
    HTTP_405_METHOD_NOT_ALLOWED = 405,
    HTTP_409_CONFLICT = 409,
    HTTP_413_PAYLOAD_TOO_LARGE = 413,
    HTTP_503_SERVICE_UNAVAILABLE = 503
};

enum http_transaction_status
{
    HTTP_SERVER_REQUEST_DATA_MORE,
    HTTP_SERVER_REQUEST_DATA_FINAL,
    HTTP_SERVER_TRANSACTION_ABORTED,
    HTTP_SERVER_TRANSACTION_COMPLETE
};

struct http_client_ctx
{
    int identity;
};

struct http_request_ctx
{
    const uint8_t *data;
    size_t data_len;
};

struct http_header
{
    const char *name;
    const char *value;
};

struct http_response_ctx
{
    enum http_status status;
    const struct http_header *headers;
    size_t header_count;
    const uint8_t *body;
    size_t body_len;
    bool final_chunk;
};

enum
{
    HTTP_GET,
    HTTP_POST,
    HTTP_RESOURCE_TYPE_STATIC,
    HTTP_RESOURCE_TYPE_DYNAMIC
};

struct http_resource_detail_common
{
    unsigned bitmask_of_supported_http_methods;
    int type;
    const char *content_type;
};

struct http_resource_detail_static
{
    struct http_resource_detail_common common;
    const void *static_data;
    size_t static_data_len;
};

typedef int (*http_resource_dynamic_cb_t)(struct http_client_ctx *, enum http_transaction_status, const struct http_request_ctx *, struct http_response_ctx *, void *);

struct http_resource_detail_dynamic
{
    struct http_resource_detail_common common;
    http_resource_dynamic_cb_t cb;
    void *user_data;
};

int http_server_start(void);
int http_server_stop(void);
#define CONFIG_HTTP_SERVER_MAX_CLIENTS 2
#endif
