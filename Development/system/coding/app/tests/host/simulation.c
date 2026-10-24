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
    return timeout.ticks < 0 ? INT64_MAX : time_milliseconds + timeout.ticks;
}

bool sys_timepoint_expired(k_timepoint_t deadline)
{
    return time_milliseconds >= deadline;
}

k_timeout_t sys_timepoint_timeout(k_timepoint_t deadline)
{
    return deadline == INT64_MAX ? K_FOREVER : K_MSEC(deadline > time_milliseconds ? deadline - time_milliseconds : 0);
}

int k_sem_take(struct k_sem *semaphore, k_timeout_t timeout)
{
    int64_t deadline = timeout.ticks < 0 ? horizon_milliseconds : time_milliseconds + timeout.ticks;
    /* Radio events and observation checkpoints do not signal the control semaphore. */
    while(semaphore->count == 0 && time_milliseconds < deadline)
        advance(deadline);
    if(semaphore->count != 0)
    {
        semaphore->count--;
        return 0;
    }
    return -EAGAIN;
}

void k_sem_give(struct k_sem *semaphore)
{
    semaphore->count = semaphore->limit;
}

int k_sleep(k_timeout_t timeout)
{
    int64_t deadline = timeout.ticks < 0 ? horizon_milliseconds : time_milliseconds + timeout.ticks;
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
        return -ECANCELED;
    int64_t deadline = time_milliseconds + timeout.ticks;
    advance(operation->due < deadline ? operation->due : deadline);
    if(time_milliseconds < operation->due)
        return -EAGAIN;
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
        return -EBUSY;
    connected = false;
    trace("disconnect_before_rearm", 0);
    return begin(&join, "join");
}

int wifi_waitForConnection(k_timeout_t timeout)
{
    int result = wait_result(&join, timeout);
    if(result != -EAGAIN)
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
        trace("disconnect_failed", -ETIMEDOUT);
        (void)k_sleep(K_MSEC(1000));
        return -ETIMEDOUT;
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
    snprintf(text, size, "%s", available ? "10.0.0.17" : "");
    trace("address", available);
    return available ? 0 : -ENOTCONN;
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
        trace("scan_cancel_failed", -ETIMEDOUT);
        (void)k_sleep(K_MSEC(1000));
        return -ETIMEDOUT;
    }
    scan.pending = false;
    trace("scan_done", 0);
    return 0;
}

int wifi_waitForScanResult(struct wifi_scan_entry *list, size_t size, k_timeout_t timeout)
{
    int result = wait_result(&scan, timeout);
    if(result != -EAGAIN)
    {
        trace("scan_result", result);
        if(result == 0)
        {
            size_t count = (size_t)scan_count < size ? (size_t)scan_count : size;
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
    return start_failure == 1 ? -EIO : 0;
}

int wifi_stopHotspot(void)
{
    trace("ap_stop", 0);
    if(ap_stop_failures > 0)
    {
        ap_stop_failures--;
        trace("ap_stop_failed", -EIO);
        (void)k_sleep(K_MSEC(1000));
        return -EIO;
    }
    hotspot = false;
    return 0;
}

int wifi_startDHCPServer(void)
{
    trace("dhcp_start", 0);
    (void)k_sleep(K_MSEC(service_start_delay_milliseconds));
    dhcp = true;
    return start_failure == 2 ? -EIO : 0;
}

int wifi_stopDHCPServer(void)
{
    trace("dhcp_stop", 0);
    if(dhcp_stop_failures > 0)
    {
        dhcp_stop_failures--;
        trace("dhcp_stop_failed", -EIO);
        (void)k_sleep(K_MSEC(1000));
        return -EIO;
    }
    dhcp = false;
    return 0;
}

int portal_start(void)
{
    trace("page_start", 0);
    (void)k_sleep(K_MSEC(service_start_delay_milliseconds));
    page = true;
    return start_failure == 3 ? -EIO : 0;
}

int portal_stop(void)
{
    if(stop_failures > 0)
    {
        stop_failures--;
        trace("page_stop_failed", -EIO);
        (void)k_sleep(K_MSEC(1000));
        return -EIO;
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
        return -EAGAIN;
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

int storage_read(const char *name, void *data, size_t size)
{
    if(strcmp(name, "wifi/network") != 0 || size != sizeof(record))
        abort();
    trace("read", 0);
    if(read_error != 0)
    {
        memcpy(data, &record, size);
        return read_error;
    }
    if(!has_record)
        return -ENOENT;
    memcpy(data, &record, size);
    return 0;
}

int storage_write(const char *name, const void *data, size_t size)
{
    if(strcmp(name, "wifi/network") != 0 || size != sizeof(record))
        abort();
    trace("write", ++writes);
    int64_t deadline = time_milliseconds + write_delay;
    while(time_milliseconds < deadline)
        advance(deadline);
    if(writes <= write_failures)
        return -EIO;
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
        else if(sscanf(line, "scan %d %d", &first, &second) == 2 || sscanf(line, "join %d %d", &first, &second) == 2)
        {
            struct operation *operation = line[0] == 's' ? &scan : &join;
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
