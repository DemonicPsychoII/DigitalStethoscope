/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L1_PORTAL
 * @{
 * @file
 * Implementation of the PORTAL module: the Wi-Fi setup page.
 *
 * Role in the workflow (architecture/wifi-flow.puml): the HTTP server
 * serves one HTML document with changing views at http://192.168.4.1 on
 * the open setup hotspot. The browser polls the status and sends requests:
 * - Connect (network name and password), Rescan, Cancel.
 * - Activity, at most once per second while the user selects or types,
 *   so the 5 min timer only runs while nobody uses the page.
 * The HTTP server thread queues the requests; L2_COMMUNICATION reads them
 * with portal_waitForRequest() and publishes the list and status with
 * portal_setNetworks() and portal_setStatus(). The page never touches
 * Wi-Fi itself.
 *
 * Status: implemented, not yet tested on the board. Requests are accepted
 * only while the user selects a network (Cancel lock; see
 * Development/system/planning/mvp-decisions-2026-10-19.md, item 5).
 *
 * Coding rules: one return per function (MISRA C:2012 Rule 15.5); unused
 * return values are cast to void (Rule 17.7).
 *
 * References:
 * - HTTP server API (static and dynamic resources, linker section):
 *   https://docs.zephyrproject.org/latest/services/connectivity/networking/api/http_server.html
 * - HTTP server sample; it also shows how CMake turns an .html file into
 *   an include file (generate_inc_file_for_target):
 *   https://docs.zephyrproject.org/latest/samples/net/sockets/http_server/README.html
 *   (code: .ci-workspace/zephyr/samples/net/sockets/http_server)
 * - Message queues, to hand requests from the HTTP server thread to
 *   portal_waitForRequest():
 *   https://docs.zephyrproject.org/latest/kernel/services/data_passing/message_queues.html
 * - Browser side, fetch() for the requests and the status poll:
 *   https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch
 *
 * Where the headers for these APIs are (the pinned Zephyr tree matches the
 * build exactly; the web documentation can be newer):
 * - <zephyr/X> is .ci-workspace/zephyr/include/zephyr/X, for example
 *   <zephyr/net/http/server.h> (server start and stop),
 *   <zephyr/net/http/service.h> (HTTP_SERVICE_DEFINE, HTTP_RESOURCE_DEFINE)
 *   and <zephyr/kernel.h> (message queues).
 * - The HTTP server sample is in .ci-workspace/zephyr/samples/net/sockets/http_server/.
 * - <errno.h>: the C library of the toolchain (picolibc) in
 *   .ci-workspace/zephyr-sdk-1.0.1/gnu/<target>/<target>/include/.
 * - "wifi.h" (network types): the module folder that CMakeLists.txt lists
 *   in target_include_directories.
 * - Any other header: build-app/compile_commands.json lists every include
 *   path (-I) that the compiler searches, in order.
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

#define PORTAL_HTTP_PORT            (80)   /**< Port of the setup page. */
#define PORTAL_HTTP_BACKLOG         (4)    /**< Connections waiting for a client slot. */
#define PORTAL_REQUEST_QUEUE_LENGTH (4)    /**< Requests not yet read by L2_COMMUNICATION. */
#define PORTAL_NETWORK_CAPACITY     (16)   /**< Networks shown on the page. */
#define PORTAL_FORM_SIZE            (320)  /**< URL-encoded "n=<name>&p=<password>", worst case 293 bytes. */
#define PORTAL_RESPONSE_SIZE        (2048) /**< Status JSON with PORTAL_NETWORK_CAPACITY escaped names. */

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/***********************************************************************/
/* GLOBAL CONSTANTS                                                    */
/***********************************************************************/

/***********************************************************************/
/* LOCAL CONSTANTS                                                     */
/***********************************************************************/

/*
 * Setup page: one document with changing views. Every request goes to the
 * device; the page polls /status once per second and follows it, so the
 * device stays the only place that decides the workflow (wifi-flow.puml).
 * ASCII only, because the server sends the bytes as they are.
 */
static const char portal_Page[] =
    "<!DOCTYPE html><html><head><meta charset='utf-8'>"
    "<meta name='viewport' content='width=device-width,initial-scale=1'>"
    "<title>Stethoscope Wi-Fi</title><style>"
    "body{background:#000;color:#fff;font:16px sans-serif;margin:0 auto;padding:16px;max-width:420px}"
    "button,input{display:block;width:100%;box-sizing:border-box;font-size:16px;padding:12px;margin:0 0 8px;"
    "background:#000;color:#fff;border:1px solid #555;border-radius:6px;text-align:left}"
    ".k{float:right}"
    "</style></head><body><div id='v'><p>Loading...</p></div><script>"
    "var v=document.getElementById('v'),nets=[],sel=null,view='busy',last='',act=0;"
    /* Network names come from any access point in range, so they are escaped before display. */
    "function esc(s){return s.replace(/[&<>'\"]/g,function(c){return '&#'+c.charCodeAt(0)+';'})}"
    "function post(p,b){return fetch(p,{method:'POST',body:b||''})}"
    /* At most one activity request per second keeps setup open while the user types (P21). */
    "function activity(){var t=Date.now();if(t-act>1000){act=t;post('/activity')}}"
    "function msg(t,d){view=d?'done':'busy';v.innerHTML='<p>'+t+'</p>'}"
    "function list(m){view='list';sel=null;var h='<p>'+(m||'Select a Wi-Fi network')+'</p>';"
    /* A lock marks networks that need a password; open networks have none. */
    "nets.forEach(function(n,i){h+='<button onclick=\"pick('+i+')\">'+esc(n.name)"
    "+(n.password?'<span class=\"k\" aria-label=\"Password required\">&#128274;</span>':'')+'</button>'});"
    "v.innerHTML=h+'<button onclick=\"rescan()\">Rescan</button><button onclick=\"stop()\">Cancel setup</button>'}"
    "function pick(i){activity();sel=nets[i];view='form';"
    "v.innerHTML='<p>'+esc(sel.name)+'</p>'+(sel.password?'<input id=\"pw\" type=\"password\" placeholder=\"Password\" oninput=\"activity()\">':'')"
    "+'<button onclick=\"go()\">Connect</button><button onclick=\"back()\">Back</button>'}"
    "function back(){activity();list()}"
    "function go(){var p=sel.password?document.getElementById('pw').value:'';msg('Connecting to '+esc(sel.name)+'...');"
    "post('/connect',new URLSearchParams({n:sel.name,p:p}).toString()).then(function(r){if(!r.ok){list('The device did not accept the request.')}})}"
    "function rescan(){msg('Scanning...');post('/rescan')}"
    "function stop(){msg('Closing setup...',true);post('/cancel')}"
    "function show(d){var s=d.status,c=d.cause?' '+esc(d.cause):'',l=JSON.stringify(d.networks),ch=l!==last;nets=d.networks;last=l;"
    "if(s=='scanning'){if(view!='form'){msg('Scanning...')}}"
    "else if(s=='selecting'){if(view=='busy'||view=='done'||(view=='list'&&ch)){list()}}"
    "else if(s=='connect_failed'){if(view=='busy'||view=='done'||(view=='list'&&ch)){list('Could not connect.'+c)}}"
    "else if(s=='connecting'){if(view!='busy'){msg('Connecting...')}}"
    "else if(s=='connected'){msg('Connected and saved. The setup hotspot closes now; you can close this page.',true)}"
    "else if(s=='save_failed'){msg('Connected, but the network could not be saved; it is lost at the next restart.'+c,true)}"
    "else{msg('Setup closed.'+c,true)}}"
    /* The phone can lose the hotspot while the device changes channel, so polling goes on. */
    "function poll(){fetch('/status').then(function(r){return r.json()}).then(show)"
    ".catch(function(){if(view!='done'){msg('No answer from the device. If its hotspot is gone, setup has ended.',true)}})"
    ".then(function(){setTimeout(poll,1000)})}"
    "poll();"
    "</script></body></html>";

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

/***********************************************************************/
/* GLOBAL VARIABLES                                                    */
/***********************************************************************/

/***********************************************************************/
/* LOCAL VARIABLES                                                     */
/***********************************************************************/

K_MSGQ_DEFINE(portal_RequestQueue, sizeof(struct portal_request), PORTAL_REQUEST_QUEUE_LENGTH, 4); /**< Requests for L2_COMMUNICATION. */
K_MUTEX_DEFINE(portal_Lock);                                                                       /**< Status, cause and network list change in another thread than the server. */

static struct wifi_scan_entry portal_Networks[PORTAL_NETWORK_CAPACITY]; /**< Networks shown on the page. */
static size_t portal_NetworkCount;                                      /**< Valid entries in portal_Networks. */
static enum portal_status portal_Status = PORTAL_STATUS_SELECTING;      /**< Status shown on the page. */
static bool portal_IsOpen;                                              /**< Handlers may queue requests. */
static int portal_Error;                                                /**< Cause shown with the status. */

/* The HTTP server runs every callback in one thread and sends each response
 * before the next callback, so one buffer of each kind is enough. */
static char portal_Response[PORTAL_RESPONSE_SIZE]; /**< Body of the /status response. */
static char portal_Form[PORTAL_FORM_SIZE + 1];     /**< Body of the running /connect request, with password. */
static size_t portal_FormLength;                   /**< Bytes in portal_Form. */
static bool portal_FormIsTooLong;                  /**< The body did not fit into portal_Form. */

static uint16_t portal_HTTPPort = PORTAL_HTTP_PORT; /**< HTTP_SERVICE_DEFINE needs the port as a variable. */

/***********************************************************************/
/* LOCAL FUNCTION PROTOTYPES                                           */
/***********************************************************************/

/**
 * @brief Send the status, its cause and the network list as JSON.
 *
 * Parameters as http_resource_dynamic_cb_t.
 *
 * @return 0, as the HTTP server expects.
 */
static int portal_sendStatus(struct http_client_ctx *client, enum http_transaction_status status, const struct http_request_ctx *requestContext, struct http_response_ctx *responseContext, void *userData);

/**
 * @brief Queue a connect request from the form body "n=<name>&p=<password>".
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
 * Requests are accepted only while the portal is open and the user selects
 * a network. This locks Cancel from Connect submission until setup closes
 * (see Development/system/planning/mvp-decisions-2026-10-19.md, item 5).
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

/***********************************************************************/
/* MACROS                                                              */
/***********************************************************************/

LOG_MODULE_REGISTER(portal, LOG_LEVEL_INF);

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

static struct http_resource_detail_dynamic portal_ConnectDetail = {
    .common = {
        .bitmask_of_supported_http_methods = BIT(HTTP_POST),
        .type = HTTP_RESOURCE_TYPE_DYNAMIC,
        .content_type = "application/json",
    },
    .cb = portal_receiveConnect,
};

static struct http_resource_detail_dynamic portal_RescanDetail = {
    .common = {
        .bitmask_of_supported_http_methods = BIT(HTTP_POST),
        .type = HTTP_RESOURCE_TYPE_DYNAMIC,
        .content_type = "application/json",
    },
    .cb = portal_receiveCommand,
    .user_data = (void *)&portal_RescanType,
};

static struct http_resource_detail_dynamic portal_CancelDetail = {
    .common = {
        .bitmask_of_supported_http_methods = BIT(HTTP_POST),
        .type = HTTP_RESOURCE_TYPE_DYNAMIC,
        .content_type = "application/json",
    },
    .cb = portal_receiveCommand,
    .user_data = (void *)&portal_CancelType,
};

static struct http_resource_detail_dynamic portal_ActivityDetail = {
    .common = {
        .bitmask_of_supported_http_methods = BIT(HTTP_POST),
        .type = HTTP_RESOURCE_TYPE_DYNAMIC,
        .content_type = "application/json",
    },
    .cb = portal_receiveCommand,
    .user_data = (void *)&portal_ActivityType,
};

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
    (void)k_mutex_lock(&portal_Lock, K_FOREVER);

    portal_IsOpen = true;

    (void)k_mutex_unlock(&portal_Lock);

    int result = http_server_start();

    if(result == -EALREADY)
    {
        /* A second setup in the same boot finds the server running. */
        result = 0;
    }

    if(result == 0)
    {
        LOG_INF("Setup page at http://%s/", WIFI_HOTSPOT_ADDRESS);
    }
    else
    {
        (void)k_mutex_lock(&portal_Lock, K_FOREVER);

        portal_IsOpen = false;

        (void)k_mutex_unlock(&portal_Lock);
        LOG_ERR("HTTP server start failed (%d)", result);
    }

    return result;
}

int portal_stop(void)
{
    struct portal_request request;

    /* http_server_stop() only signals the server thread, which closes its sockets
     * later. Closing the portal first makes every handler that still runs reject
     * its request, so no request can arrive after this function returns. */
    (void)k_mutex_lock(&portal_Lock, K_FOREVER);

    portal_IsOpen = false;

    (void)k_mutex_unlock(&portal_Lock);

    int result = http_server_stop();

    if(result == -EALREADY)
    {
        /* A stopped server is not an error for the caller. */
        result = 0;
    }

    /* Unread requests can hold a password. */
    while(k_msgq_get(&portal_RequestQueue, &request, K_NO_WAIT) == 0)
    {
        (void)memset(&request, 0, sizeof(request));
    }

    return result;
}

void portal_setNetworks(const struct wifi_scan_entry *list, size_t count)
{
    (void)k_mutex_lock(&portal_Lock, K_FOREVER);

    portal_NetworkCount = MIN(count, PORTAL_NETWORK_CAPACITY);

    (void)memcpy(portal_Networks, list, portal_NetworkCount * sizeof(portal_Networks[0]));
    (void)k_mutex_unlock(&portal_Lock);
}

void portal_setStatus(enum portal_status status, int error)
{
    (void)k_mutex_lock(&portal_Lock, K_FOREVER);

    portal_Status = status;
    portal_Error = error;

    (void)k_mutex_unlock(&portal_Lock);
}

int portal_waitForRequest(struct portal_request *request, k_timeout_t timeout)
{
    int result = 0;

    if(k_msgq_get(&portal_RequestQueue, request, timeout) != 0)
    {
        /* k_msgq_get() reports -ENOMSG for K_NO_WAIT and -EAGAIN otherwise; callers need one code. */
        result = -EAGAIN;
    }

    return result;
}

/***********************************************************************/
/* LOCAL FUNCTIONS                                                     */
/***********************************************************************/

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
        portal_appendText(&length, "\",\"networks\":[");

        for(size_t index = 0U; index < portal_NetworkCount; index++)
        {
            portal_appendText(&length, (index == 0U) ? "{\"name\":\"" : ",{\"name\":\"");
            portal_appendName(&length, portal_Networks[index].name);
            portal_appendText(&length, portal_Networks[index].needsPassword ? "\",\"password\":true}" : "\",\"password\":false}");
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
    ARG_UNUSED(client);
    ARG_UNUSED(userData);

    if((status == HTTP_SERVER_TRANSACTION_ABORTED) || (status == HTTP_SERVER_TRANSACTION_COMPLETE))
    {
        /* The body holds the password; nothing of it stays for the next request. */
        (void)memset(portal_Form, 0, sizeof(portal_Form));

        portal_FormLength = 0U;
        portal_FormIsTooLong = false;
    }
    else
    {
        if((portal_FormLength + requestContext->data_len) <= PORTAL_FORM_SIZE)
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
            bool isValid = !portal_FormIsTooLong && portal_readFormValue(portal_Form, "n", request.network.name, sizeof(request.network.name)) && portal_readFormValue(portal_Form, "p", request.network.password, sizeof(request.network.password)) && (request.network.name[0] != '\0');

            responseContext->status = isValid ? portal_queueRequest(&request, PORTAL_STATUS_CONNECTING) : HTTP_400_BAD_REQUEST;
            responseContext->body = (const uint8_t *)"{}";
            responseContext->body_len = 2U;
            responseContext->final_chunk = true;

            (void)memset(&request, 0, sizeof(request));
        }
    }

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

    if(portal_IsOpen && ((portal_Status == PORTAL_STATUS_SELECTING) || (portal_Status == PORTAL_STATUS_CONNECT_FAILED)))
    {
        if(k_msgq_put(&portal_RequestQueue, request, K_NO_WAIT) == 0)
        {
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
        text = "Invalid network name or password length.";
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

    /* A full buffer drops the rest; the page then shows fewer networks, never broken memory. */
    if((*length + textLength) < sizeof(portal_Response))
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

        if((*character == '"') || (*character == '\\'))
        {
            portal_appendText(length, escaped);
        }
        else
        {
            /* JSON forbids raw control characters; a name cannot show them anyway. */
            escaped[0] = ((unsigned char)*character < 0x20U) ? '?' : *character;
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
        if((strncmp(field, key, keyLength) == 0) && (field[keyLength] == '='))
        {
            isFound = true;
        }
        else
        {
            field = strchr(field, '&');
            field = (field != NULL) ? (field + 1) : NULL;
        }
    }

    if(isFound)
    {
        const char *source = &field[keyLength + 1U];
        size_t length = 0U;

        isValid = true;

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
                isValid = (char2hex(source[1], &high) == 0) && (char2hex(source[2], &low) == 0);
                character = (char)((high << 4) | low);
                source += isValid ? 2 : 0;
            }
            else
            {
                /* Plain character. */
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

/** @} */
