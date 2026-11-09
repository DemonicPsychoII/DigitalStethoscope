/* VT-14: deterministic service-boundary simulation. See README.md for limits. */
#include <errno.h>
#include <ctype.h>
#include <setjmp.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "communication.h"
#include "portal.h"
#include "storage.h"

enum
{
    CAPACITY = 512
};

struct event
{
    int64_t time_milliseconds;
    char kind[32];
    int value;
    bool consumed;
};

struct outcome
{
    int result;
    int delay;
};

struct operation
{
    struct outcome plan[CAPACITY];
    int count;
    int calls;
    int64_t due;
    int result;
    bool pending;
};
static struct event events[CAPACITY];
static int event_count;
static struct operation scan, join;
static int64_t time_milliseconds, horizon_milliseconds;
static bool connected, hotspot, dhcp, page, has_record;
static struct wifi_network record = {"old-network", "old-password"};
static int init_error, read_error, write_failures, writes, start_failure, stop_failures;
static int write_delay, scan_count = 1;
static int scan_stop_failures, disconnect_failures, dhcp_stop_failures, ap_stop_failures;
static int service_start_delay_milliseconds;
static int64_t disconnect_confirmation_time;
static bool address_error;
static simulation_entry worker;
static jmp_buf finished;
static struct portal_request requests[CAPACITY];
static int request_count;

/* Server communication model; inactive unless the script configures a server. */
#define SIMULATION_BASE_URL    "https://172.20.10.7:8443/fhir"
#define SIMULATION_OTHER_BASE  "https://192.168.2.40:8443/fhir"
#define SIMULATION_IDENTITY    "stetho-3030F912D838"
#define SIMULATION_STORED_ID   "7400"
#define SIMULATION_REGISTERED  "7501"
#define SIMULATION_RECORD_SIZE 343
#define SIMULATION_RECORD_BASE 1
#define SIMULATION_RECORD_ID   (1 + 257 + 20)
static bool server_configured;
static int identity_error;
static int registration_state; /* 0 none, 1 this binding, 2 another base URL, 3 unsupported version. */
static int registration_read_error, registration_write_failures, registration_writes;
static struct operation tls, exchange;
static bool retained;
static struct wifi_http_response *exchange_response;
static bool exchange_is_observation;
static int sntp_error;                    /* Set by an sntp_fail event: every later time synchronization fails with it. */
static int observation_requests;          /* Observation requests of the current job. */
static char observation_first_body[2048]; /* First request of the job; every retry must repeat it. */
static char observation_first_condition[256];

static void trace(const char *kind, int value)
{
    printf("%lld %s %d\n", (long long)time_milliseconds, kind, value);
}

void simulation_log(const char *format, ...)
{
    va_list arguments;
    va_start(arguments, format);
    fprintf(stderr, "%lld ", (long long)time_milliseconds);
    vfprintf(stderr, format, arguments);
    fputc('\n', stderr);
    va_end(arguments);
}

static void snapshot(void)
{
    trace("connected", connected);
    trace("hotspot", hotspot);
    trace("dhcp", dhcp);
    trace("page", page);
    trace("scan_pending", scan.pending);
    trace("join_pending", join.pending);
    trace("ack", communication_waitForWiFiStop(K_NO_WAIT));
    trace("record_new", has_record && strcmp(record.name, "selected-network") == 0);
    trace("record_old", has_record && strcmp(record.name, "old-network") == 0);
}

static void dispatch(struct event *event)
{
    event->consumed = true;
    trace(event->kind, event->value);
    if(strcmp(event->kind, "start") == 0)
        (void)communication_postEvent(COMMUNICATION_EVENT_LISTENING_STARTED);
    else if(strcmp(event->kind, "stop") == 0)
        (void)communication_postEvent(COMMUNICATION_EVENT_LISTENING_STOPPED);
    else if(strcmp(event->kind, "release_wait") == 0)
    {
        int64_t started_milliseconds = time_milliseconds;
        trace("release_wait_result", communication_waitForWiFiStop(K_MSEC(event->value)));
        trace("release_wait_elapsed", (int)(time_milliseconds - started_milliseconds));
    }
    else if(strcmp(event->kind, "hold") == 0)
        (void)communication_postEvent(COMMUNICATION_EVENT_SETUP_REQUESTED);
    else if(strcmp(event->kind, "deliver") == 0)
    {
        /* CONTROL after finalization: value 0 is 72.3 BPM, 1 a poor-signal report; the P13 deadline is Stop + 10 s. */
        const struct communication_delivery delivery = {
            .measurementEndMonotonicMicroseconds = (uint64_t)time_milliseconds * 1000U,
            .kind = (event->value == 1) ? COMMUNICATION_DELIVERY_POOR_SIGNAL : COMMUNICATION_DELIVERY_HEART_RATE,
            .heartRateScaled = 723U,
            .heartRateDecimalPlaces = 1U,
        };
        observation_requests = 0;
        trace("deliver_result", communication_submitDelivery(&delivery, sys_timepoint_calc(K_MSEC(10000))));
    }
    else if(strcmp(event->kind, "outcome") == 0)
        trace("delivery_outcome", (int)communication_getDeliveryOutcome());
    else if(strcmp(event->kind, "sntp_fail") == 0)
        sntp_error = event->value;
    else if(strcmp(event->kind, "drop") == 0)
        connected = false;
    else if(strcmp(event->kind, "snapshot") == 0)
        snapshot();
    else if(strcmp(event->kind, "late_link") == 0)
    {
        connected = true;
        trace("unsolicited_link", 1);
    }
    else if(strcmp(event->kind, "poll") != 0)
    {
        if(page)
        {
            if(request_count == CAPACITY)
                abort();
            struct portal_request *request = &requests[request_count++];
            memset(request, 0, sizeof(*request));
            if(strcmp(event->kind, "connect") == 0)
            {
                request->type = PORTAL_REQUEST_CONNECT;
                strcpy(request->network.name, "selected-network");
                if(event->value == 2)
                    strcpy(request->network.password, "short");
                else if(event->value != 0)
                    strcpy(request->network.password, "test-password");
            }
            else if(strcmp(event->kind, "rescan") == 0)
                request->type = PORTAL_REQUEST_RESCAN;
            else if(strcmp(event->kind, "cancel") == 0)
                request->type = PORTAL_REQUEST_CANCEL;
            else if(strcmp(event->kind, "activity") == 0)
                request->type = PORTAL_REQUEST_ACTIVITY;
            else
                abort();
        }
        else
            trace("request_dropped", 0);
    }
}

/* Yield at one external event so public wait calls observe control changes. */
static void advance(int64_t target)
{
    if(target > horizon_milliseconds)
        target = horizon_milliseconds;
    struct event *next = NULL;
    for(int index = 0; index < event_count; index++)
        /* Select the earliest unconsumed event within this advance interval. */
        if(!events[index].consumed && events[index].time_milliseconds <= target && (next == NULL || events[index].time_milliseconds < next->time_milliseconds))
            next = &events[index];
    if(next != NULL)
    {
        time_milliseconds = next->time_milliseconds;
        dispatch(next);
        /* Same-time inputs arrive before the worker is scheduled again. */
        for(int index = 0; index < event_count; index++)
            if(!events[index].consumed && events[index].time_milliseconds == time_milliseconds)
                dispatch(&events[index]);
    }
    else
        time_milliseconds = target;
    if(time_milliseconds >= horizon_milliseconds)
        longjmp(finished, 1);
}

k_timepoint_t sys_timepoint_calc(k_timeout_t timeout)
{
    k_timepoint_t selectedValue;
    if(timeout.ticks < 0)
    {
        selectedValue = INT64_MAX;
    }
    else
    {
        selectedValue = time_milliseconds + timeout.ticks;
    }
    return selectedValue;
}

bool sys_timepoint_expired(k_timepoint_t deadline)
{
    return time_milliseconds >= deadline;
}

k_timeout_t sys_timepoint_timeout(k_timepoint_t deadline)
{
    k_timeout_t selectedValue;
    if(deadline == INT64_MAX)
    {
        selectedValue = K_FOREVER;
    }
    else
    {
        if(deadline > time_milliseconds)
        {
            selectedValue = K_MSEC(deadline - time_milliseconds);
        }
        else
        {
            selectedValue = K_MSEC(0);
        }
    }
    return selectedValue;
}

/* One tick is one simulated millisecond, as for the timeouts above. */
int64_t k_uptime_ticks(void)
{
    return time_milliseconds;
}

uint64_t k_ticks_to_us_floor64(uint64_t ticks)
{
    return ticks * USEC_PER_MSEC;
}

int k_sem_take(struct k_sem *semaphore, k_timeout_t timeout)
{
    int64_t deadline;
    if(timeout.ticks < 0)
    {
        deadline = horizon_milliseconds;
    }
    else
    {
        deadline = time_milliseconds + timeout.ticks;
    }
    /* Radio events and observation checkpoints do not signal the control semaphore. */
    while(semaphore->count == 0 && time_milliseconds < deadline)
        advance(deadline);
    if(semaphore->count != 0)
    {
        semaphore->count--;
        return 0;
    }
    return -EAGAIN; /**< Operation is still pending; try again in the host model. */
}

void k_sem_give(struct k_sem *semaphore)
{
    semaphore->count = semaphore->limit;
}

int k_sleep(k_timeout_t timeout)
{
    int64_t deadline;
    if(timeout.ticks < 0)
    {
        deadline = horizon_milliseconds;
    }
    else
    {
        deadline = time_milliseconds + timeout.ticks;
    }
    while(time_milliseconds < deadline)
        advance(deadline);
    return 0;
}

k_spinlock_key_t k_spin_lock(struct k_spinlock *lock)
{
    (void)lock;
    return 0;
}

void k_spin_unlock(struct k_spinlock *lock, k_spinlock_key_t key)
{
    (void)lock;
    (void)key;
}

struct k_thread *k_thread_create(struct k_thread *thread, char *stack, size_t size, simulation_entry entry, void *first, void *second, void *third, int priority, uint32_t options, k_timeout_t delay)
{
    (void)stack;
    (void)size;
    (void)first;
    (void)second;
    (void)third;
    (void)priority;
    (void)options;
    (void)delay;
    worker = entry;
    return thread;
}

int k_thread_name_set(struct k_thread *thread, const char *name)
{
    (void)thread;
    (void)name;
    return 0;
}

void k_thread_start(struct k_thread *thread)
{
    (void)thread;
}

static int begin(struct operation *operation, const char *name)
{
    struct outcome outcome = {0, 100};
    if(operation->calls < operation->count)
        outcome = operation->plan[operation->calls];
    operation->calls++;
    operation->pending = true;
    operation->due = time_milliseconds + outcome.delay;
    operation->result = outcome.result;
    trace(name, operation->calls);
    return 0;
}

static int wait_result(struct operation *operation, k_timeout_t timeout)
{
    if(!operation->pending)
        return -ECANCELED; /**< Operation was cancelled in the host model. */
    int64_t deadline = time_milliseconds + timeout.ticks;
    if(operation->due < deadline)
    {
        advance(operation->due);
    }
    else
    {
        advance(deadline);
    }
    if(time_milliseconds < operation->due)
        return -EAGAIN; /**< Operation is still pending; try again in the host model. */
    operation->pending = false;
    return operation->result;
}

int wifi_init(void)
{
    trace("wifi_init", init_error);
    return init_error;
}

bool wifi_isValidNetwork(const struct wifi_network *network)
{
    if(network == NULL)
        return false;
    const char *name_end = memchr(network->name, 0, sizeof(network->name));
    const char *password_end = memchr(network->password, 0, sizeof(network->password));
    bool valid_key = true;
    if(password_end == network->password + 64)
        for(size_t index = 0; index < 64; index++)
            valid_key = valid_key && isxdigit((unsigned char)network->password[index]);
    return valid_key && name_end != NULL && name_end != network->name && password_end != NULL && (password_end == network->password || password_end - network->password >= 8);
}

int wifi_connect(const struct wifi_network *network)
{
    trace("join_selected", strcmp(network->name, "selected-network") == 0);
    trace("join_protected", network->password[0] != 0);
    /* L1 drains DISCONNECT_RESULT before accepting the next request. */
    if(time_milliseconds < disconnect_confirmation_time)
        return -EBUSY; /**< Service is busy with another operation in the host model. */
    connected = false;
    trace("disconnect_before_rearm", 0);
    return begin(&join, "join");
}

int wifi_waitForConnection(k_timeout_t timeout)
{
    int result = wait_result(&join, timeout);
    if(result != -EAGAIN) /**< Operation is still pending; try again in the host model. */
    {
        connected = result == 0;
        trace("join_result", result);
    }
    return result;
}

int wifi_disconnect(void)
{
    trace("disconnect", 0);
    if(disconnect_failures > 0)
    {
        disconnect_failures--;
        trace("disconnect_failed", -ETIMEDOUT); /**< Operation exceeded its wait deadline in the host model. */
        (void)k_sleep(K_MSEC(1000));
        return -ETIMEDOUT; /**< Operation exceeded its wait deadline in the host model. */
    }
    join.pending = false;
    disconnect_confirmation_time = time_milliseconds;
    trace("disconnect_result", 0);
    connected = false;
    return 0;
}

bool wifi_isConnected(void)
{
    return connected;
}

int wifi_getAddress(char *text, size_t size)
{
    /* Fault injection: the address is lost between join completion and query. */
    if(address_error)
        connected = false;
    bool available = connected;
    if(available)
    {
        snprintf(text, size, "%s", "10.0.0.17");
    }
    else
    {
        snprintf(text, size, "%s", "");
    }
    trace("address", available);
    int selectedValue;
    if(available)
    {
        selectedValue = 0;
    }
    else
    {
        selectedValue = -ENOTCONN; /**< Station has no usable connection in the host model. */
    }
    return selectedValue;
}

int wifi_startScan(void)
{
    return begin(&scan, "scan");
}

int wifi_cancelScan(void)
{
    trace("scan_cancel", 0);
    if(scan_stop_failures > 0)
    {
        scan_stop_failures--;
        trace("scan_cancel_failed", -ETIMEDOUT); /**< Operation exceeded its wait deadline in the host model. */
        (void)k_sleep(K_MSEC(1000));
        return -ETIMEDOUT; /**< Operation exceeded its wait deadline in the host model. */
    }
    scan.pending = false;
    trace("scan_done", 0);
    return 0;
}

int wifi_waitForScanResult(struct wifi_scan_entry *list, size_t size, k_timeout_t timeout)
{
    int result = wait_result(&scan, timeout);
    if(result != -EAGAIN) /**< Operation is still pending; try again in the host model. */
    {
        trace("scan_result", result);
        if(result == 0)
        {
            size_t count;
            if((size_t)scan_count < size)
            {
                count = (size_t)scan_count;
            }
            else
            {
                count = size;
            }
            for(size_t index = 0; index < count; index++)
            {
                snprintf(list[index].name, sizeof(list[index].name), "network-%u", (unsigned)index);
                list[index].needsPassword = index % 2 != 0;
            }
            return (int)count;
        }
    }
    return result;
}

int wifi_startHotspot(void)
{
    trace("ap_start", 0);
    (void)k_sleep(K_MSEC(service_start_delay_milliseconds));
    hotspot = true;
    int selectedValue;
    if(start_failure == 1)
    {
        selectedValue = -EIO; /**< Input/output operation failed in the host model. */
    }
    else
    {
        selectedValue = 0;
    }
    return selectedValue;
}

int wifi_stopHotspot(void)
{
    trace("ap_stop", 0);
    if(ap_stop_failures > 0)
    {
        ap_stop_failures--;
        trace("ap_stop_failed", -EIO); /**< Input/output operation failed in the host model. */
        (void)k_sleep(K_MSEC(1000));
        return -EIO; /**< Input/output operation failed in the host model. */
    }
    hotspot = false;
    return 0;
}

int wifi_startDHCPServer(void)
{
    trace("dhcp_start", 0);
    (void)k_sleep(K_MSEC(service_start_delay_milliseconds));
    dhcp = true;
    int selectedValue;
    if(start_failure == 2)
    {
        selectedValue = -EIO; /**< Input/output operation failed in the host model. */
    }
    else
    {
        selectedValue = 0;
    }
    return selectedValue;
}

int wifi_stopDHCPServer(void)
{
    trace("dhcp_stop", 0);
    if(dhcp_stop_failures > 0)
    {
        dhcp_stop_failures--;
        trace("dhcp_stop_failed", -EIO); /**< Input/output operation failed in the host model. */
        (void)k_sleep(K_MSEC(1000));
        return -EIO; /**< Input/output operation failed in the host model. */
    }
    dhcp = false;
    return 0;
}

/* Without a configured server, time synchronization and TLS are unavailable, so the VT-14 scenarios keep their traces and timing.
 * With one, SNTP answers at once with a fixed UTC time and TLS and exchanges follow the script plans. */
int wifi_startTimeSynchronization(const char *ntpServer)
{
    (void)ntpServer;
    if(server_configured && (sntp_error != 0))
    {
        trace("sntp_failed", sntp_error);
        return sntp_error;
    }
    return server_configured ? 0 : -ENOSYS; /**< Not modelled without a server. */
}

int wifi_waitForTimeSynchronization(struct normalised_time *time, k_timeout_t timeout)
{
    (void)timeout;
    if(!server_configured)
        return -ENOSYS; /**< Not modelled without a server. */
    *time = (struct normalised_time){.utc_seconds = 1794182400U, .receive_monotonic_microseconds = (uint64_t)time_milliseconds * 1000U, .estimated_uncertainty_microseconds = 1000U};
    return 0;
}

int wifi_cancelTimeSynchronization(void)
{
    return 0;
}

int wifi_applyTimeSynchronization(const struct normalised_time *time, struct applied_time_anchor *anchor)
{
    if(!server_configured)
        return -ENOSYS; /**< Not modelled without a server. */
    *anchor = (struct applied_time_anchor){time->utc_seconds, 0U, (uint64_t)time_milliseconds * 1000U, time->estimated_uncertainty_microseconds};
    trace("sntp", 0);
    return 0;
}

int wifi_configureSecureServer(const char *baseUrl, const char *certificate, size_t certificateLength, struct wifi_secure_server *server)
{
    (void)certificate;
    (void)certificateLength;
    if(!server_configured || strcmp(baseUrl, SIMULATION_BASE_URL) != 0)
        return -ENOSYS; /**< Not modelled without a server. */
    *server = (struct wifi_secure_server){0, INT64_MAX};
    return 0;
}

int wifi_startSecureConnection(k_timepoint_t deadline)
{
    (void)deadline;
    if(!server_configured)
        return -ENOSYS; /**< Not modelled without a server. */
    if(retained || tls.pending || exchange.pending)
        return -EBUSY;
    return begin(&tls, "tls");
}

int wifi_waitForSecureConnection(enum wifi_secure_connection_cause *cause, k_timeout_t timeout)
{
    if(!server_configured)
        return -ENOSYS; /**< Not modelled without a server. */
    const int result = wait_result(&tls, timeout);
    if(result != -EAGAIN)
    {
        *cause = (result == 0) ? WIFI_SECURE_CONNECTION_CAUSE_NONE : WIFI_SECURE_CONNECTION_CAUSE_TCP;
        retained = (result == 0);
        trace("tls_result", result);
    }
    return result;
}

int wifi_cancelSecureConnection(void)
{
    if(tls.pending || exchange.pending)
    {
        trace("secure_cancel", exchange.pending);
        /* A cancelled exchange leaves no usable connection behind. */
        retained = retained && !exchange.pending;
        tls.pending = false;
        exchange.pending = false;
    }
    return 0;
}

int wifi_closeSecureConnection(void)
{
    if(exchange.pending)
        return -EBUSY;
    if(retained)
        trace("tls_close", 0);
    retained = false;
    return 0;
}

int wifi_getDeviceIdentifier(char *identifier, size_t size)
{
    if(size > 0)
        identifier[0] = '\0';
    trace("identity", identity_error);
    if(identity_error != 0)
        return identity_error;
    snprintf(identifier, size, "%s", SIMULATION_IDENTITY);
    return 0;
}

/* Plan values: an HTTP status (100 to 599) gives a complete response; 1 gives 201 without any id;
 * 2 gives 201 for another device; a negative value is the exchange's error result. */
int wifi_startSecureExchange(const struct wifi_http_request *request, struct wifi_http_response *response, k_timepoint_t deadline)
{
    (void)deadline;
    if(!retained)
        return -ENOTCONN;
    if(tls.pending || exchange.pending)
        return -EBUSY;
    exchange_is_observation = strcmp(request->resourcePath, "Observation") == 0;
    if(exchange_is_observation)
    {
        if(request->bodyLength >= sizeof(observation_first_body) || strlen(request->condition) >= sizeof(observation_first_condition))
            abort();
        if(observation_requests++ == 0)
        {
            memcpy(observation_first_body, request->body, request->bodyLength);
            observation_first_body[request->bodyLength] = '\0';
            snprintf(observation_first_condition, sizeof(observation_first_condition), "%s", request->condition);
            simulation_log("observation_body %s", observation_first_body);
            simulation_log("observation_condition %s", observation_first_condition);
        }
        const bool is_same = (request->bodyLength == strlen(observation_first_body)) && (memcmp(request->body, observation_first_body, request->bodyLength) == 0) && (strcmp(request->condition, observation_first_condition) == 0);
        trace("exchange_observation", observation_requests);
        trace("exchange_same_observation", is_same);
    }
    else
    {
        trace("exchange_device", strcmp(request->resourcePath, "Device") == 0);
        trace("exchange_conditional", strcmp(request->condition, "identifier=urn%3Astethoscope%3Adevice|" SIMULATION_IDENTITY) == 0);
        trace("exchange_body_identity", (request->bodyLength > 0) && (strstr(request->body, "\"" SIMULATION_IDENTITY "\"") != NULL));
    }
    exchange_response = response;
    return begin(&exchange, "exchange");
}

int wifi_waitForSecureExchange(k_timeout_t timeout)
{
    const int outcome = wait_result(&exchange, timeout);
    if(outcome == -EAGAIN)
        return outcome;
    trace("exchange_result", outcome);
    if(outcome <= 0)
    {
        retained = false;
        return outcome;
    }
    struct wifi_http_response *response = exchange_response;
    memset(response, 0, sizeof(*response));
    const char *identity = (outcome == 2) ? "stetho-000000000001" : SIMULATION_IDENTITY;
    response->status = (outcome < 100) ? 201 : (uint16_t)outcome;
    if(outcome == 1)
        snprintf(response->body, sizeof(response->body), "%s", "{}");
    else if(exchange_is_observation && ((response->status == 201) || (response->status == 200)))
    {
        response->hasLocation = true;
        snprintf(response->location, sizeof(response->location), "%s", SIMULATION_OTHER_BASE "/Observation/8001/_history/1");
        snprintf(response->body, sizeof(response->body), "%s", "{\"resourceType\":\"Observation\",\"id\":\"8001\"}");
    }
    else if((response->status == 201) || (response->status == 200))
    {
        response->hasLocation = true;
        snprintf(response->location, sizeof(response->location), "%s", SIMULATION_OTHER_BASE "/Device/" SIMULATION_REGISTERED "/_history/1");
        snprintf(response->body,
                 sizeof(response->body),
                 "{\"resourceType\":\"Device\",\"id\":\"" SIMULATION_REGISTERED "\",\"identifier\":[{\"system\":\"urn:stethoscope:device\",\"value\":\"%s\"}],\"status\":\"active\"}",
                 identity);
    }
    else
        snprintf(response->body, sizeof(response->body), "%s", "{\"resourceType\":\"OperationOutcome\"}");
    response->bodyLength = strlen(response->body);
    response->keepsConnection = true;
    return 0;
}

int portal_start(void)
{
    trace("page_start", 0);
    (void)k_sleep(K_MSEC(service_start_delay_milliseconds));
    page = true;
    int selectedValue;
    if(start_failure == 3)
    {
        selectedValue = -EIO; /**< Input/output operation failed in the host model. */
    }
    else
    {
        selectedValue = 0;
    }
    return selectedValue;
}

int portal_stop(void)
{
    if(stop_failures > 0)
    {
        stop_failures--;
        trace("page_stop_failed", -EIO); /**< Input/output operation failed in the host model. */
        (void)k_sleep(K_MSEC(1000));
        return -EIO; /**< Input/output operation failed in the host model. */
    }
    trace("page_stop", 0);
    page = false;
    memset(requests, 0, sizeof(requests));
    request_count = 0;
    return 0;
}

void portal_setNetworks(const struct wifi_scan_entry *list, size_t count)
{
    if(count > WIFI_SCAN_LIST_SIZE)
        abort();
    for(size_t index = 0; index < count; index++)
        if(memchr(list[index].name, 0, sizeof(list[index].name)) == NULL)
            abort();
    trace("networks", (int)count);
}

void portal_setStatus(enum portal_status status, int error)
{
    static const char *names[] = {"scanning", "selecting", "connecting", "join_failed", "success", "save_failed", "closing"};
    trace(names[status], error);
}

void portal_setAddress(const char *address)
{
    trace("page_address", strcmp(address, "10.0.0.17") == 0);
}

int portal_waitForRequest(struct portal_request *request, k_timeout_t timeout)
{
    if(request_count == 0 && timeout.ticks != 0)
        advance(time_milliseconds + timeout.ticks);
    if(request_count == 0)
        return -EAGAIN; /**< Operation is still pending; try again in the host model. */
    *request = requests[0];
    memmove(requests, requests + 1, (size_t)(--request_count) * sizeof(*requests));
    memset(&requests[request_count], 0, sizeof(*requests));
    trace("request", request->type);
    return 0;
}

int storage_init(void)
{
    return 0;
}

/* Version-1 registration record, built from the design layout independently of L1_FHIR. */
static void registration_record(uint8_t *bytes, const char *base, const char *identifier, uint8_t version)
{
    memset(bytes, 0, SIMULATION_RECORD_SIZE);
    bytes[0] = version;
    memcpy(&bytes[SIMULATION_RECORD_BASE], base, strlen(base));
    memcpy(&bytes[SIMULATION_RECORD_BASE + 257], SIMULATION_IDENTITY, strlen(SIMULATION_IDENTITY));
    memcpy(&bytes[SIMULATION_RECORD_ID], identifier, strlen(identifier));
}

static int registration_read(void *data, size_t size)
{
    if(size != SIMULATION_RECORD_SIZE)
        abort();
    trace("registration_read", registration_read_error);
    if(registration_read_error != 0)
        return registration_read_error;
    if(registration_state == 0)
        return -ENOENT;
    registration_record(data, (registration_state == 2) ? SIMULATION_OTHER_BASE : SIMULATION_BASE_URL, SIMULATION_STORED_ID, (registration_state == 3) ? 2U : 1U);
    return 0;
}

static int registration_write(const void *data, size_t size)
{
    if(size != SIMULATION_RECORD_SIZE)
        abort();
    trace("registration_write", ++registration_writes);
    if(registration_writes <= registration_write_failures)
        return -EIO; /**< Input/output operation failed in the host model. */
    uint8_t expected[SIMULATION_RECORD_SIZE];
    registration_record(expected, SIMULATION_BASE_URL, SIMULATION_REGISTERED, 1U);
    trace("registration_saved", memcmp(data, expected, sizeof(expected)) == 0);
    return 0;
}

int storage_read(const char *name, void *data, size_t size)
{
    if(strcmp(name, "fhir/device-registration") == 0)
        return registration_read(data, size);
    if(strcmp(name, "wifi/network") != 0 || size != sizeof(record))
        abort();
    trace("read", 0);
    if(read_error != 0)
    {
        memcpy(data, &record, size);
        return read_error;
    }
    if(!has_record)
        return -ENOENT; /**< Requested record or network was not found in the host model. */
    memcpy(data, &record, size);
    return 0;
}

int storage_readServerProfile(struct storage_server_profile *serverProfile)
{
    memset(serverProfile, 0, sizeof(*serverProfile));
    if(!server_configured)
        return -ENOENT; /**< Erased server profile partition in the host model. */
    snprintf(serverProfile->baseUrl, sizeof(serverProfile->baseUrl), "%s", SIMULATION_BASE_URL);
    serverProfile->serverKeepAliveSeconds = 600U;
    snprintf(serverProfile->certificate, sizeof(serverProfile->certificate), "%s", "-----BEGIN CERTIFICATE-----\n-----END CERTIFICATE-----\n");
    serverProfile->certificateLength = strlen(serverProfile->certificate);
    return 0;
}

int storage_write(const char *name, const void *data, size_t size)
{
    if(strcmp(name, "fhir/device-registration") == 0)
        return registration_write(data, size);
    if(strcmp(name, "wifi/network") != 0 || size != sizeof(record))
        abort();
    trace("write", ++writes);
    int64_t deadline = time_milliseconds + write_delay;
    while(time_milliseconds < deadline)
        advance(deadline);
    if(writes <= write_failures)
        return -EIO; /**< Input/output operation failed in the host model. */
    memcpy(&record, data, size);
    has_record = true;
    trace("write_complete", writes);
    return 0;
}

int main(void)
{
    char line[160], key[32];
    int first, second;
    long long event_time_milliseconds;
    horizon_milliseconds = 1000;
    while(fgets(line, sizeof(line), stdin) != NULL)
    {
        if(sscanf(line, "event %lld %31s %d", &event_time_milliseconds, key, &first) == 3)
        {
            if(event_count == CAPACITY || event_time_milliseconds < 0)
                abort();
            events[event_count].time_milliseconds = event_time_milliseconds;
            strcpy(events[event_count].kind, key);
            events[event_count++].value = first;
        }
        /* Parse either supported radio-operation script command. */
        else if(sscanf(line, "scan %d %d", &first, &second) == 2 || sscanf(line, "join %d %d", &first, &second) == 2 || sscanf(line, "tls %d %d", &first, &second) == 2 || sscanf(line, "exchange %d %d", &first, &second) == 2)
        {
            struct operation *operation;
            if(line[0] == 's')
            {
                operation = &scan;
            }
            else if(line[0] == 't')
            {
                operation = &tls;
            }
            else if(line[0] == 'e')
            {
                operation = &exchange;
            }
            else
            {
                operation = &join;
            }
            if(operation->count == CAPACITY || second < 0)
                abort();
            operation->plan[operation->count++] = (struct outcome){first, second};
        }
        else if(sscanf(line, "%31s %d", key, &first) == 2)
        {
            if(strcmp(key, "horizon") == 0)
                horizon_milliseconds = first;
            else if(strcmp(key, "stored") == 0)
            {
                has_record = first != 0;
                if(first == 2)
                    record.name[0] = 0;
            }
            else if(strcmp(key, "init_error") == 0)
                init_error = first;
            else if(strcmp(key, "read_error") == 0)
                read_error = first;
            else if(strcmp(key, "write_failures") == 0)
                write_failures = first;
            else if(strcmp(key, "start_failure") == 0)
                start_failure = first;
            else if(strcmp(key, "stop_failures") == 0)
                stop_failures = first;
            else if(strcmp(key, "address_error") == 0)
                address_error = first != 0;
            else if(strcmp(key, "write_delay") == 0)
                write_delay = first;
            else if(strcmp(key, "scan_stop_failures") == 0)
                scan_stop_failures = first;
            else if(strcmp(key, "disconnect_failures") == 0)
                disconnect_failures = first;
            else if(strcmp(key, "dhcp_stop_failures") == 0)
                dhcp_stop_failures = first;
            else if(strcmp(key, "ap_stop_failures") == 0)
                ap_stop_failures = first;
            else if(strcmp(key, "service_delay") == 0)
                service_start_delay_milliseconds = first;
            else if(strcmp(key, "scan_count") == 0)
                scan_count = first;
            else if(strcmp(key, "server") == 0)
                server_configured = first != 0;
            else if(strcmp(key, "identity_error") == 0)
                identity_error = first;
            else if(strcmp(key, "registration") == 0)
                registration_state = first;
            else if(strcmp(key, "registration_read_error") == 0)
                registration_read_error = first;
            else if(strcmp(key, "registration_write_failures") == 0)
                registration_write_failures = first;
            else
                abort();
        }
        else
            abort();
    }
    communication_init();
    if(setjmp(finished) == 0)
    {
        for(int index = 0; index < event_count; index++)
            if(!events[index].consumed && events[index].time_milliseconds == 0)
                dispatch(&events[index]);
        worker(NULL, NULL, NULL);
        /* An init failure ends the worker; CONTROL remains usable offline. */
        while(time_milliseconds < horizon_milliseconds)
            advance(horizon_milliseconds);
    }
    snapshot();
    return 0;
}
