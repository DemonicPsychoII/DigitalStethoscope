/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L1_PORTAL
 * @{
 * @file
 * Implementation of the L1_PORTAL module: the Wi-Fi setup page.
 *
 * The HTTP server serves one page at http://192.168.4.1 on the open setup
 * hotspot. The page polls /status once per second and posts Connect,
 * Rescan, Cancel and Activity requests. The server thread puts them into a
 * queue; L2_COMMUNICATION reads them with portal_waitForRequest() and
 * publishes the list and status. The page never touches Wi-Fi itself.
 *
 * Requests are accepted only while the page shows the network list. From a
 * Connect until the end of setup, the device ignores the page, so a Cancel
 * cannot interrupt a join or a save.
 */

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include "portal.h"

#include <errno.h>
#include <string.h>

#include <zephyr/logging/log.h>
#include <zephyr/net/http/server.h>
#include <zephyr/net/http/service.h>
#include <zephyr/sys/util.h>

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

#define PORTAL_HTTP_PORT                              (80)  /**< Port of the setup page. */
#define PORTAL_HTTP_BACKLOG                           (4)   /**< Connections waiting for a client slot. */
#define PORTAL_REQUEST_QUEUE_LENGTH                   (4)   /**< Requests not yet read by L2_COMMUNICATION. */
#define PORTAL_FORM_SIZE                              (320) /**< URL-encoded "network=<name>&password=<password>", worst case 306 bytes. */
#define PORTAL_SERVER_TRANSITION_TIMEOUT_MILLISECONDS (1000)

#define PORTAL_RESPONSE_SIZE (2048) /**< Status JSON with WIFI_SCAN_LIST_SIZE escaped names. */

/** Resource for a POST request from the page; @p data goes to @p callback as user_data. */
#define PORTAL_POST_DETAIL(callback, data)                       \
    {                                                            \
        .common = {                                              \
            .bitmask_of_supported_http_methods = BIT(HTTP_POST), \
            .type = HTTP_RESOURCE_TYPE_DYNAMIC,                  \
            .content_type = "application/json",                  \
        },                                                       \
        .cb = (callback),                                        \
        .user_data = (void *)(data),                             \
    }

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

enum portal_wait_target
{
    PORTAL_WAIT_SERVER_READY,   /**< Wait for a listening socket; listener readiness or the deadline ends the wait. */
    PORTAL_WAIT_SERVER_STOPPED, /**< Wait for listener closure after client aborts; confirmed closure or the deadline ends the wait. */
};

/***********************************************************************/
/* GLOBAL CONSTANTS                                                    */
/***********************************************************************/

/***********************************************************************/
/* LOCAL CONSTANTS                                                     */
/***********************************************************************/

static const char portal_Page[] = {
#include "portal.html.inc"
    0};

/** Names of enum portal_status in the /status response; the page compares them. */
static const char *const portal_StatusNames[] = {
    [PORTAL_STATUS_SCANNING] = "scanning",
    [PORTAL_STATUS_SELECTING] = "selecting",
    [PORTAL_STATUS_CONNECTING] = "connecting",
    [PORTAL_STATUS_CONNECT_FAILED] = "connect_failed",
    [PORTAL_STATUS_CONNECTED] = "connected",
    [PORTAL_STATUS_SAVE_FAILED] = "save_failed",
    [PORTAL_STATUS_CLOSING] = "closing",
};

static const enum portal_request_type portal_RescanType = PORTAL_REQUEST_RESCAN;     /**< user_data of /rescan. */
static const enum portal_request_type portal_CancelType = PORTAL_REQUEST_CANCEL;     /**< user_data of /cancel. */
static const enum portal_request_type portal_ActivityType = PORTAL_REQUEST_ACTIVITY; /**< user_data of /activity. */
static const struct http_header portal_RetryAfterHeader = {"Retry-After", "1"};

/***********************************************************************/
/* GLOBAL VARIABLES                                                    */
/***********************************************************************/

/***********************************************************************/
/* LOCAL VARIABLES                                                     */
/***********************************************************************/

static struct portal_request portal_RequestQueue[PORTAL_REQUEST_QUEUE_LENGTH];
static size_t portal_RequestReadIndex;
static size_t portal_RequestWriteIndex;
static size_t portal_RequestCount;
K_SEM_DEFINE(portal_RequestAvailable, 0, PORTAL_REQUEST_QUEUE_LENGTH);
K_MUTEX_DEFINE(portal_Lock); /**< Status, cause and network list change in another thread than the server. */

static struct wifi_scan_entry portal_Networks[WIFI_SCAN_LIST_SIZE]; /**< Networks shown on the page. */
static size_t portal_NetworkCount;                                  /**< Valid entries in portal_Networks. */
static enum portal_status portal_Status = PORTAL_STATUS_SELECTING;  /**< Status shown on the page. */
static bool portal_ServerStopIsConfirmed = true;
static bool portal_ServerHasListener;
static bool portal_SelectionIsReady;
static bool portal_IsOpen;                     /**< Handlers may queue requests. */
static int portal_Error;                       /**< Cause shown with the status. */
static char portal_Address[WIFI_ADDRESS_SIZE]; /**< Device address shown after a join. */

/* The HTTP server runs every callback in one thread and sends each response
 * before the next callback, so one buffer of each kind is enough. */
static char portal_Response[PORTAL_RESPONSE_SIZE]; /**< Body of the /status response. */
static char portal_Form[PORTAL_FORM_SIZE + 1];     /**< Body of the running /connect request, with password. */
static struct http_client_ctx *portal_FormClient;
static size_t portal_FormLength;  /**< Bytes in portal_Form. */
static bool portal_FormIsTooLong; /**< The body did not fit into portal_Form. */

static uint16_t portal_HTTPPort = PORTAL_HTTP_PORT; /**< HTTP_SERVICE_DEFINE needs the port as a variable. */

/***********************************************************************/
/* LOCAL FUNCTION PROTOTYPES                                           */
/***********************************************************************/

/**
 * @brief Overwrite a buffer with zeros so credentials do not stay in memory.
 *
 * @param[out] data Buffer to clear.
 * @param[in]  size Size of @p data in bytes.
 */
static void portal_clearSecret(void *data, size_t size);

/**
 * @brief Send the status, its cause and the network list as JSON.
 *
 * Parameters as http_resource_dynamic_cb_t.
 *
 * @return 0, as the HTTP server expects.
 */
static int portal_sendStatus(struct http_client_ctx *client, enum http_transaction_status status, const struct http_request_ctx *requestContext, struct http_response_ctx *responseContext, void *userData);

/**
 * @brief Queue a connect request from the form body "network=<name>&password=<password>".
 *
 * Parameters as http_resource_dynamic_cb_t.
 *
 * @return 0, as the HTTP server expects.
 */
static int portal_receiveConnect(struct http_client_ctx *client, enum http_transaction_status status, const struct http_request_ctx *requestContext, struct http_response_ctx *responseContext, void *userData);

/**
 * @brief Queue a request without data: Rescan, Cancel or activity, as given in @p userData.
 *
 * Parameters as http_resource_dynamic_cb_t.
 *
 * @return 0, as the HTTP server expects.
 */
static int portal_receiveCommand(struct http_client_ctx *client, enum http_transaction_status status, const struct http_request_ctx *requestContext, struct http_response_ctx *responseContext, void *userData);

/**
 * @brief Queue a request if the page may send one now.
 *
 * Requests are accepted only while the portal is open and the page shows
 * the network list.
 *
 * @param[in] request   Request to queue.
 * @param[in] newStatus Status shown at once, so polls cannot see the old one.
 *
 * @return HTTP_202_ACCEPTED, HTTP_409_CONFLICT or HTTP_503_SERVICE_UNAVAILABLE.
 */
static enum http_status portal_queueRequest(const struct portal_request *request, enum portal_status newStatus);

/**
 * @brief Describe an error code for the page.
 *
 * @param[in] error Error code from L2_COMMUNICATION, or 0.
 *
 * @return Short English text; empty for 0.
 */
static const char *portal_describeError(int error);

/**
 * @brief Append text to the response and stop at its end.
 *
 * @param[in,out] length Current length of portal_Response.
 * @param[in]     text   Text to append.
 */
static void portal_appendText(size_t *length, const char *text);

/**
 * @brief Append a network name as a JSON string body, escaped.
 *
 * @param[in,out] length Current length of portal_Response.
 * @param[in]     name   Network name.
 */
static void portal_appendName(size_t *length, const char *name);

/**
 * @brief Read one value from a URL-encoded form body.
 *
 * @param[in]  form        Form body, NUL-terminated.
 * @param[in]  key         Field name.
 * @param[out] value       Decoded value, NUL-terminated.
 * @param[in]  valueSize   Size of @p value.
 *
 * @return True if the field was found and fits; false if missing, malformed or too long.
 */
static bool portal_readFormValue(const char *form, const char *key, char *value, size_t valueSize);

/**
 * @brief Wait until the Zephyr HTTP server has opened or closed its listening socket.
 *
 * @param[in] target  Listener state to wait for.
 * @param[in] timeout Longest wait.
 *
 * @return True if the listener reached the state of @p target within @p timeout.
 */
static bool portal_waitForServerState(enum portal_wait_target target, k_timeout_t timeout);

/***********************************************************************/
/* MACROS                                                              */
/***********************************************************************/

LOG_MODULE_REGISTER(portal, LOG_LEVEL_INF);

BUILD_ASSERT(PORTAL_RESPONSE_SIZE >= (WIFI_SCAN_LIST_SIZE * (2 * WIFI_SSID_MAX_LEN + 40) + 256), "Status JSON buffer must hold all escaped names");

static struct http_resource_detail_static portal_PageDetail = {
    .common = {
        .bitmask_of_supported_http_methods = BIT(HTTP_GET),
        .type = HTTP_RESOURCE_TYPE_STATIC,
        .content_type = "text/html",
    },
    .static_data = portal_Page,
    .static_data_len = sizeof(portal_Page) - 1U,
};

static struct http_resource_detail_dynamic portal_StatusDetail = {
    .common = {
        .bitmask_of_supported_http_methods = BIT(HTTP_GET),
        .type = HTTP_RESOURCE_TYPE_DYNAMIC,
        .content_type = "application/json",
    },
    .cb = portal_sendStatus,
};

static struct http_resource_detail_dynamic portal_ConnectDetail = PORTAL_POST_DETAIL(portal_receiveConnect, NULL);
static struct http_resource_detail_dynamic portal_RescanDetail = PORTAL_POST_DETAIL(portal_receiveCommand, &portal_RescanType);
static struct http_resource_detail_dynamic portal_CancelDetail = PORTAL_POST_DETAIL(portal_receiveCommand, &portal_CancelType);
static struct http_resource_detail_dynamic portal_ActivityDetail = PORTAL_POST_DETAIL(portal_receiveCommand, &portal_ActivityType);

/* Bound to the hotspot address only, so the page never appears on the clinic network. */
HTTP_SERVICE_DEFINE(portal_service,
                    WIFI_HOTSPOT_ADDRESS,
                    &portal_HTTPPort,
                    CONFIG_HTTP_SERVER_MAX_CLIENTS,
                    PORTAL_HTTP_BACKLOG,
                    NULL,
                    NULL,
                    NULL);

HTTP_RESOURCE_DEFINE(portal_PageResource, portal_service, "/", &portal_PageDetail);
HTTP_RESOURCE_DEFINE(portal_StatusResource, portal_service, "/status", &portal_StatusDetail);
HTTP_RESOURCE_DEFINE(portal_ConnectResource, portal_service, "/connect", &portal_ConnectDetail);
HTTP_RESOURCE_DEFINE(portal_RescanResource, portal_service, "/rescan", &portal_RescanDetail);
HTTP_RESOURCE_DEFINE(portal_CancelResource, portal_service, "/cancel", &portal_CancelDetail);
HTTP_RESOURCE_DEFINE(portal_ActivityResource, portal_service, "/activity", &portal_ActivityDetail);

/***********************************************************************/
/* GLOBAL FUNCTIONS                                                    */
/***********************************************************************/

int portal_start(void)
{
    if(!portal_ServerStopIsConfirmed)
    {
        return -EBUSY;
    }
    (void)k_mutex_lock(&portal_Lock, K_FOREVER);
    portal_clearSecret(portal_RequestQueue, sizeof(portal_RequestQueue));
    portal_clearSecret(portal_Form, sizeof(portal_Form));
    (void)memset(portal_Address, 0, sizeof(portal_Address));
    portal_RequestReadIndex = 0U;
    portal_RequestWriteIndex = 0U;
    portal_RequestCount = 0U;
    k_sem_reset(&portal_RequestAvailable);
    portal_FormLength = 0U;
    portal_FormIsTooLong = false;
    portal_FormClient = NULL;
    portal_Error = 0;
    portal_Status = PORTAL_STATUS_SELECTING;
    portal_SelectionIsReady = true;
    portal_IsOpen = true;
    portal_ServerStopIsConfirmed = false;
    portal_ServerHasListener = false;
    (void)k_mutex_unlock(&portal_Lock);

    int result = http_server_start();
    if(result == 0)
    {
        portal_ServerHasListener = portal_waitForServerState(PORTAL_WAIT_SERVER_READY,
                                                             K_MSEC(PORTAL_SERVER_TRANSITION_TIMEOUT_MILLISECONDS));
        if(portal_ServerHasListener)
        {
            result = 0;
        }
        else
        {
            result = -ETIMEDOUT;
        }
    }
    if(result != 0)
    {
        (void)k_mutex_lock(&portal_Lock, K_FOREVER);
        portal_IsOpen = false;
        (void)k_mutex_unlock(&portal_Lock);
    }
    return result;
}

int portal_stop(void)
{
    (void)k_mutex_lock(&portal_Lock, K_FOREVER);
    portal_IsOpen = false;
    portal_SelectionIsReady = false;
    portal_clearSecret(portal_Form, sizeof(portal_Form));
    portal_FormLength = 0U;
    portal_FormIsTooLong = false;
    portal_FormClient = NULL;
    portal_clearSecret(portal_RequestQueue, sizeof(portal_RequestQueue));
    portal_RequestCount = 0U;
    portal_RequestReadIndex = 0U;
    portal_RequestWriteIndex = 0U;
    k_sem_reset(&portal_RequestAvailable);
    (void)k_mutex_unlock(&portal_Lock);

    if(portal_ServerStopIsConfirmed)
    {
        return 0;
    }
    int result = http_server_stop();
    if((result != 0) && (result != -EALREADY))
    {
        return result;
    }

    const bool isServerStopped = portal_waitForServerState(PORTAL_WAIT_SERVER_STOPPED, K_MSEC(PORTAL_SERVER_TRANSITION_TIMEOUT_MILLISECONDS));

    if(!isServerStopped)
    {
        return -ETIMEDOUT;
    }
    (void)k_mutex_lock(&portal_Lock, K_FOREVER);
    portal_clearSecret(portal_Form, sizeof(portal_Form));
    portal_FormLength = 0U;
    portal_FormIsTooLong = false;
    portal_FormClient = NULL;
    portal_ServerStopIsConfirmed = true;
    (void)k_mutex_unlock(&portal_Lock);
    return 0;
}

void portal_setNetworks(const struct wifi_scan_entry *list, size_t count)
{
    (void)k_mutex_lock(&portal_Lock, K_FOREVER);

    portal_NetworkCount = MIN(count, WIFI_SCAN_LIST_SIZE);
    portal_SelectionIsReady = true;

    (void)memcpy(portal_Networks, list, portal_NetworkCount * sizeof(portal_Networks[0]));
    (void)k_mutex_unlock(&portal_Lock);
}

void portal_setStatus(enum portal_status status, int error)
{
    (void)k_mutex_lock(&portal_Lock, K_FOREVER);

    /* A failed join keeps the last completed list selectable. */
    portal_SelectionIsReady = (status == PORTAL_STATUS_SELECTING) || (status == PORTAL_STATUS_CONNECT_FAILED);
    portal_Status = status;
    portal_Error = error;

    (void)k_mutex_unlock(&portal_Lock);
}

void portal_setAddress(const char *address)
{
    (void)k_mutex_lock(&portal_Lock, K_FOREVER);
    (void)strncpy(portal_Address, address, sizeof(portal_Address) - 1U);
    (void)k_mutex_unlock(&portal_Lock);
}

int portal_waitForRequest(struct portal_request *request, k_timeout_t timeout)
{
    if(request == NULL)
    {
        return -EINVAL;
    }
    int result = -EAGAIN;
    const int semaphoreResult = k_sem_take(&portal_RequestAvailable, timeout);

    if(semaphoreResult == 0)
    {
        (void)k_mutex_lock(&portal_Lock, K_FOREVER);
        if(portal_RequestCount != 0U)
        {
            *request = portal_RequestQueue[portal_RequestReadIndex];
            portal_clearSecret(&portal_RequestQueue[portal_RequestReadIndex], sizeof(*request));
            portal_RequestReadIndex = (portal_RequestReadIndex + 1U) % PORTAL_REQUEST_QUEUE_LENGTH;
            portal_RequestCount--;
            result = 0;
        }
        (void)k_mutex_unlock(&portal_Lock);
    }

    return result;
}

/***********************************************************************/
/* LOCAL FUNCTIONS                                                     */
/***********************************************************************/

static void portal_clearSecret(void *data, size_t size)
{
    /* Volatile writes prevent dead-store elimination of credential erasure. */
    volatile unsigned char *destination = data;
    for(size_t index = 0U; index < size; index++)
    {
        destination[index] = 0U;
    }
}

static int portal_sendStatus(struct http_client_ctx *client, enum http_transaction_status status, const struct http_request_ctx *requestContext, struct http_response_ctx *responseContext, void *userData)
{
    ARG_UNUSED(client);
    ARG_UNUSED(requestContext);
    ARG_UNUSED(userData);

    if(status == HTTP_SERVER_REQUEST_DATA_FINAL)
    {
        size_t length = 0U;

        portal_Response[0] = '\0';

        (void)k_mutex_lock(&portal_Lock, K_FOREVER);
        portal_appendText(&length, "{\"status\":\"");
        portal_appendText(&length, portal_StatusNames[portal_Status]);
        portal_appendText(&length, "\",\"cause\":\"");
        portal_appendText(&length, portal_describeError(portal_Error));
        portal_appendText(&length, "\",\"address\":\"");
        portal_appendText(&length, portal_Address);
        portal_appendText(&length, "\",\"networks\":[");

        for(size_t index = 0U; index < portal_NetworkCount; index++)
        {
            if(index == 0U)
            {
                portal_appendText(&length, "{\"name\":\"");
            }
            else
            {
                portal_appendText(&length, ",{\"name\":\"");
            }
            portal_appendName(&length, portal_Networks[index].name);
            if(portal_Networks[index].needsPassword)
            {
                portal_appendText(&length, "\",\"password\":true}");
            }
            else
            {
                portal_appendText(&length, "\",\"password\":false}");
            }
        }

        (void)k_mutex_unlock(&portal_Lock);

        portal_appendText(&length, "]}");

        responseContext->body = (const uint8_t *)portal_Response;
        responseContext->body_len = length;
        responseContext->final_chunk = true;
    }

    return 0;
}

static int portal_receiveConnect(struct http_client_ctx *client, enum http_transaction_status status, const struct http_request_ctx *requestContext, struct http_response_ctx *responseContext, void *userData)
{
    ARG_UNUSED(userData);
    (void)k_mutex_lock(&portal_Lock, K_FOREVER);
    /* Both completion callbacks end ownership of the current HTTP form. */
    bool isCompletion = (status == HTTP_SERVER_TRANSACTION_ABORTED) || (status == HTTP_SERVER_TRANSACTION_COMPLETE);
    if((portal_FormClient != NULL) && (portal_FormClient != client))
    {
        if(!isCompletion)
        {
            responseContext->status = HTTP_409_CONFLICT;
            responseContext->final_chunk = true;
        }
        (void)k_mutex_unlock(&portal_Lock);
        return 0;
    }
    if(isCompletion)
    {
        portal_clearSecret(portal_Form, sizeof(portal_Form));
        portal_FormLength = 0U;
        portal_FormIsTooLong = false;
        portal_FormClient = NULL;
        (void)k_mutex_unlock(&portal_Lock);
        return 0;
    }
    /* Reject form input unless setup is open and a selectable list is ready. */
    if(!portal_IsOpen || !portal_SelectionIsReady ||
       ((portal_Status != PORTAL_STATUS_SELECTING) && (portal_Status != PORTAL_STATUS_CONNECT_FAILED)))
    {
        responseContext->status = HTTP_409_CONFLICT;
        responseContext->final_chunk = true;
        portal_clearSecret(portal_Form, sizeof(portal_Form));
        portal_FormLength = 0U;
        portal_FormIsTooLong = false;
        portal_FormClient = NULL;
        (void)k_mutex_unlock(&portal_Lock);
        return 0;
    }
    portal_FormClient = client;

    const size_t remainingFormCapacity = (PORTAL_FORM_SIZE - portal_FormLength);

    if(requestContext->data_len <= remainingFormCapacity)
    {
        (void)memcpy(&portal_Form[portal_FormLength], requestContext->data, requestContext->data_len);
        portal_FormLength += requestContext->data_len;
        portal_Form[portal_FormLength] = '\0';
    }
    else
    {
        portal_FormIsTooLong = true;
    }
    if(status == HTTP_SERVER_REQUEST_DATA_FINAL)
    {
        struct portal_request request = {.type = PORTAL_REQUEST_CONNECT};
        enum http_status rejectionStatus;
        if(portal_FormIsTooLong)
        {
            rejectionStatus = HTTP_413_PAYLOAD_TOO_LARGE;
        }
        else
        {
            rejectionStatus = HTTP_400_BAD_REQUEST;
        }
        /* Accept only a bounded form with both decoded fields and a valid network. */
        bool isValid = !portal_FormIsTooLong &&
                       portal_readFormValue(portal_Form, "network", request.network.name, sizeof(request.network.name)) &&
                       portal_readFormValue(portal_Form, "password", request.network.password, sizeof(request.network.password)) &&
                       wifi_isValidNetwork(&request.network);
        bool isListed = false;
        for(size_t index = 0U; isValid && (index < portal_NetworkCount); index++)
        {
            const bool isNameListed = (strcmp(request.network.name, portal_Networks[index].name) == 0);

            if(isNameListed)
            {
                isListed = portal_Networks[index].needsPassword == (request.network.password[0] != '\0');
                break;
            }
        }
        portal_clearSecret(portal_Form, sizeof(portal_Form));
        portal_FormLength = 0U;
        portal_FormIsTooLong = false;
        (void)k_mutex_unlock(&portal_Lock);
        if(isValid && isListed)
        {
            responseContext->status = portal_queueRequest(&request, PORTAL_STATUS_CONNECTING);
        }
        else
        {
            responseContext->status = rejectionStatus;
        }
        if(responseContext->status == HTTP_503_SERVICE_UNAVAILABLE)
        {
            responseContext->headers = &portal_RetryAfterHeader;
            responseContext->header_count = 1U;
        }
        responseContext->body = (const uint8_t *)"{}";
        responseContext->body_len = 2U;
        responseContext->final_chunk = true;
        portal_clearSecret(&request, sizeof(request));
        return 0;
    }
    (void)k_mutex_unlock(&portal_Lock);
    return 0;
}

static int portal_receiveCommand(struct http_client_ctx *client, enum http_transaction_status status, const struct http_request_ctx *requestContext, struct http_response_ctx *responseContext, void *userData)
{
    ARG_UNUSED(client);
    ARG_UNUSED(requestContext);

    if(status == HTTP_SERVER_REQUEST_DATA_FINAL)
    {
        struct portal_request request = {.type = *(const enum portal_request_type *)userData};
        enum portal_status newStatus = PORTAL_STATUS_SELECTING;

        if(request.type == PORTAL_REQUEST_RESCAN)
        {
            newStatus = PORTAL_STATUS_SCANNING;
        }
        else if(request.type == PORTAL_REQUEST_CANCEL)
        {
            newStatus = PORTAL_STATUS_CLOSING;
        }
        else
        {
            /* Activity keeps the current status. */
        }

        responseContext->status = portal_queueRequest(&request, newStatus);
        if(responseContext->status == HTTP_503_SERVICE_UNAVAILABLE)
        {
            responseContext->headers = &portal_RetryAfterHeader;
            responseContext->header_count = 1U;
        }
        responseContext->body = (const uint8_t *)"{}";
        responseContext->body_len = 2U;
        responseContext->final_chunk = true;
    }

    return 0;
}

static enum http_status portal_queueRequest(const struct portal_request *request, enum portal_status newStatus)
{
    enum http_status response = HTTP_409_CONFLICT;

    (void)k_mutex_lock(&portal_Lock, K_FOREVER);

    if(request->type == PORTAL_REQUEST_ACTIVITY)
    {
        newStatus = portal_Status;
    }

    /* Selection remains available after a failed join. */
    bool isSelection = (portal_Status == PORTAL_STATUS_SELECTING) || (portal_Status == PORTAL_STATUS_CONNECT_FAILED);
    /* A rescan after a failed join can refresh the existing selection. */
    bool isFailedJoinRescan = (request->type == PORTAL_REQUEST_RESCAN) && (portal_Status == PORTAL_STATUS_CONNECT_FAILED);
    /* Queue commands only while setup accepts a selection or a failed-join rescan. */
    if(portal_IsOpen && isSelection && (portal_SelectionIsReady || isFailedJoinRescan))
    {
        if(portal_RequestCount < PORTAL_REQUEST_QUEUE_LENGTH)
        {
            portal_RequestQueue[portal_RequestWriteIndex] = *request;
            portal_RequestWriteIndex = (portal_RequestWriteIndex + 1U) % PORTAL_REQUEST_QUEUE_LENGTH;
            portal_RequestCount++;
            k_sem_give(&portal_RequestAvailable);
            if((newStatus != PORTAL_STATUS_SELECTING) && (newStatus != PORTAL_STATUS_CONNECT_FAILED))
            {
                portal_SelectionIsReady = false;
            }
            /* Activity keeps the status, so the cause of a failed join stays on the page. */
            if(newStatus != portal_Status)
            {
                portal_Status = newStatus;
                portal_Error = 0;
            }

            response = HTTP_202_ACCEPTED;
        }
        else
        {
            response = HTTP_503_SERVICE_UNAVAILABLE;
        }
    }

    (void)k_mutex_unlock(&portal_Lock);

    return response;
}

static const char *portal_describeError(int error)
{
    const char *text = "Unexpected error; the serial log has the details.";

    switch(error)
    {
    case 0:
        text = "";
        break;

    case -EINVAL:
        text = "Invalid network or password.";
        break;

    case -EACCES:
        text = "Wrong password.";
        break;

    case -ENOENT:
        text = "Network not found.";
        break;

    case -ETIMEDOUT:
        text = "No answer from the network.";
        break;

    case -ECONNREFUSED:
        text = "The network refused the connection.";
        break;

    default:
        break;
    }

    return text;
}

static void portal_appendText(size_t *length, const char *text)
{
    size_t textLength = strlen(text);
    const size_t appendedLength = (*length + textLength);

    /* If the buffer is full, the rest is dropped and the page shows fewer networks. */
    if(appendedLength < sizeof(portal_Response))
    {
        (void)memcpy(&portal_Response[*length], text, textLength + 1U);

        *length += textLength;
    }
}

static void portal_appendName(size_t *length, const char *name)
{
    for(const char *character = name; *character != '\0'; character++)
    {
        char escaped[3] = {'\\', *character, '\0'};
        const unsigned char byte = (unsigned char)*character;

        if((*character == '"') || (*character == '\\'))
        {
            portal_appendText(length, escaped);
        }
        else
        {
            /* JSON does not allow raw control characters. */
            if(byte < 0x20U)
            {
                escaped[0] = '?';
            }
            else
            {
                escaped[0] = *character;
            }
            escaped[1] = '\0';

            portal_appendText(length, escaped);
        }
    }
}

static bool portal_readFormValue(const char *form, const char *key, char *value, size_t valueSize)
{
    size_t keyLength = strlen(key);
    const char *field = form;
    bool isFound = false;
    bool isValid = false;

    /* Fields are "key=value" pairs separated by '&'. */
    while((field != NULL) && !isFound)
    {
        const bool isFieldOfKey = ((strncmp(field, key, keyLength) == 0) && (field[keyLength] == '='));

        if(isFieldOfKey)
        {
            isFound = true;
        }
        else
        {
            field = strchr(field, '&');
            if(field != NULL)
            {
                field = (field + 1);
            }
        }
    }

    if(isFound)
    {
        const char *source = &field[keyLength + 1U];
        size_t length = 0U;

        isValid = true;

        /* Decode one bounded form field until its separator or terminator. */
        while(isValid && (*source != '\0') && (*source != '&'))
        {
            char character = *source;
            uint8_t high = 0U;
            uint8_t low = 0U;

            if(character == '+')
            {
                character = ' ';
            }
            else if(character == '%')
            {
                /* A percent escape needs two present hexadecimal digits. */
                isValid = (source[1] != '\0') && (source[2] != '\0') && (char2hex(source[1], &high) == 0) && (char2hex(source[2], &low) == 0);
                character = (char)((high << 4) | low);
                if(isValid)
                {
                    source += 2;
                }
            }
            else
            {
                /* Copy as it is. */
            }

            /* An embedded NUL would cut the value short without notice. */
            isValid = isValid && (character != '\0') && ((length + 1U) < valueSize);

            if(isValid)
            {
                value[length] = character;
                length++;
                source++;
            }
        }

        value[length] = '\0';
    }

    return isValid;
}

static bool portal_waitForServerState(enum portal_wait_target target, k_timeout_t timeout)
{
    k_timepoint_t deadline = sys_timepoint_calc(timeout);
    bool isWaiting = true;
    bool isDeadlineExpired = sys_timepoint_expired(deadline);

    while(isWaiting && !isDeadlineExpired)
    {
        bool hasListener = *(volatile int *)portal_service.fd >= 0;
        if(target == PORTAL_WAIT_SERVER_READY)
        {
            isWaiting = !hasListener;
        }
        else
        {
            /* The Zephyr HTTP server resets fd only after all client abort callbacks. */
            isWaiting = !portal_ServerHasListener || hasListener;
            if(hasListener)
            {
                portal_ServerHasListener = true;
            }
        }
        if(isWaiting)
        {
            k_sleep(K_MSEC(10));

            isDeadlineExpired = sys_timepoint_expired(deadline);
        }
    }
    bool isReady = *(volatile int *)portal_service.fd >= 0;
    if(target == PORTAL_WAIT_SERVER_STOPPED)
    {
        /* For a stop, the result is true when the listener is closed. */
        isReady = !isReady;
    }
    return isReady;
}

/** @} */
