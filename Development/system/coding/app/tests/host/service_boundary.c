#include <assert.h>
#include <errno.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
/* Including the units exposes secret buffers for erasure inspection without production hooks. */
#include "../../L1_services/L1_WIFI/wifi.c"
#include "../../L1_services/L1_PORTAL/portal.c"
#include "../../L1_services/L1_STORAGE/storage.c"

static int64_t time_milliseconds;
static int listener_start_delay_milliseconds;
static int listener_stop_delay_milliseconds;
static int64_t listener_change_time_milliseconds = -1;
static bool listener_is_stopping;
static int stop_result;
static struct net_if station_interface = {1};
static struct net_if hotspot_interface = {2};
static struct net_in_addr station_address = {{10, 0, 0, 17}};
static bool has_address;

enum station_state
{
    STATION_IDLE,
    STATION_CONNECTING,
    STATION_CONNECTED
};
static enum station_state station_state;
static bool retain_dhcp_address;
static bool disconnect_is_requested;
static int disconnect_calls;
static int disconnect_request_result;
static int disconnect_delay_milliseconds;
static int64_t disconnect_due_milliseconds = -1;
static int connect_calls;
static int maximum_hotspot_clients;
static bool hotspot_is_enabled;
static bool hotspot_dhcp_is_running;
static int hotspot_enable_result;
static int hotspot_get_configuration_result;
static int hotspot_set_configuration_result;
static int hotspot_dhcp_start_result;
static int hotspot_disable_calls;
static int hotspot_dhcp_stop_calls;
static uint64_t scheduled_event;
static int64_t scheduled_event_time_milliseconds;
static bool deleted_record;
static void (*host_clock_hook)(int64_t);
static int64_t (*host_wait_deadline)(int64_t);
static int (*host_network_hook)(int, struct net_if *, void *, size_t);
static bool has_stored_network;
static struct wifi_network stored_network;
static int settings_write_failures;
static int settings_write_calls;
static void (*host_mutex_unlock_hook)(void);

static void emit_event(uint64_t event, const void *information)
{
    struct net_mgmt_event_callback *callback;
    if(event < NET_EVENT_IPV4_ADDR_ADD)
    {
        callback = &wifi_LinkLayerCallback;
    }
    else
    {
        callback = &wifi_NetworkLayerCallback;
    }
    callback->info = information;
    callback->handler(callback, event, &station_interface);
}

static void advance_clock(int64_t deadline)
{
    if(host_clock_hook != NULL)
        host_clock_hook(deadline);
    time_milliseconds = deadline;
    if(disconnect_due_milliseconds >= 0 && time_milliseconds >= disconnect_due_milliseconds)
    {
        struct wifi_status status = {WIFI_STATUS_CONN_FAIL};
        if(station_state == STATION_CONNECTED)
        {
            status.status = WIFI_REASON_DISCONN_USER_REQUEST;
        }
        uint64_t event;
        if(station_state == STATION_CONNECTED)
        {
            event = NET_EVENT_WIFI_DISCONNECT_RESULT;
        }
        else
        {
            event = NET_EVENT_WIFI_CONNECT_RESULT;
        }
        disconnect_due_milliseconds = -1;
        if(!retain_dhcp_address)
            has_address = false;
        station_state = STATION_IDLE;
        emit_event(event, &status);
        disconnect_is_requested = false;
    }
    if(scheduled_event && time_milliseconds >= scheduled_event_time_milliseconds)
    {
        struct wifi_status status = {0};
        uint64_t event = scheduled_event;
        scheduled_event = 0;
        emit_event(event, &status);
    }
    /* Apply a scheduled listener transition once simulated time reaches it. */
    if(listener_change_time_milliseconds >= 0 && time_milliseconds >= listener_change_time_milliseconds)
    {
        if(listener_is_stopping)
        {
            *portal_service.fd = -1;
        }
        else
        {
            *portal_service.fd = 3;
        }
        listener_change_time_milliseconds = -1;
    }
}

void simulation_log(const char *format, ...)
{
    (void)format;
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

int k_sleep(k_timeout_t timeout)
{
    advance_clock(time_milliseconds + timeout.ticks);
    return 0;
}

int k_mutex_lock(struct k_mutex *mutex, k_timeout_t timeout)
{
    (void)mutex;
    (void)timeout;
    return 0;
}

int k_mutex_unlock(struct k_mutex *mutex)
{
    (void)mutex;
    if(host_mutex_unlock_hook != NULL)
    {
        void (*callback)(void) = host_mutex_unlock_hook;
        host_mutex_unlock_hook = NULL;
        callback();
    }
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

void k_sem_give(struct k_sem *semaphore)
{
    if(semaphore->count < semaphore->limit)
        semaphore->count++;
}

void k_sem_reset(struct k_sem *semaphore)
{
    semaphore->count = 0;
}

int k_sem_take(struct k_sem *semaphore, k_timeout_t timeout)
{
    int result = -EAGAIN; /**< Operation is still pending; try again in the host model. */
    int64_t deadline = sys_timepoint_calc(timeout);
    while(semaphore->count == 0 && time_milliseconds < deadline)
    {
        if(host_wait_deadline != NULL)
        {
            advance_clock(host_wait_deadline(deadline));
        }
        else
        {
            advance_clock(deadline);
        }
    }
    if(semaphore->count)
    {
        semaphore->count--;
        result = 0;
    }
    return result;
}

uint32_t k_event_test(struct k_event *event, uint32_t mask)
{
    return (event->events & mask);
}

uint32_t k_event_post(struct k_event *event, uint32_t mask)
{
    event->events |= mask;
    return event->events;
}

uint32_t k_event_clear(struct k_event *event, uint32_t mask)
{
    event->events &= ~mask;
    return event->events;
}

uint32_t k_event_wait(struct k_event *event, uint32_t mask, bool reset, k_timeout_t timeout)
{
    (void)reset;
    if(!(event->events & mask) && timeout.ticks > 0)
        advance_clock(time_milliseconds + timeout.ticks);
    return (event->events & mask);
}

int http_server_start(void)
{
    listener_is_stopping = false;
    if(listener_start_delay_milliseconds == 0)
        *portal_service.fd = 3;
    else
        listener_change_time_milliseconds = time_milliseconds + listener_start_delay_milliseconds;
    return 0;
}

int http_server_stop(void)
{
    listener_is_stopping = true;
    if(listener_stop_delay_milliseconds == 0)
        *portal_service.fd = -1;
    else
        listener_change_time_milliseconds = time_milliseconds + listener_stop_delay_milliseconds;
    return stop_result;
}

struct net_if *net_if_get_wifi_sta(void)
{
    return &station_interface;
}

struct net_if *net_if_get_wifi_sap(void)
{
    return &hotspot_interface;
}

void net_mgmt_init_event_callback(struct net_mgmt_event_callback *callback, void (*handler)(struct net_mgmt_event_callback *, uint64_t, struct net_if *), uint64_t mask)
{
    callback->handler = handler;
    callback->event_mask = mask;
}

void net_mgmt_add_event_callback(struct net_mgmt_event_callback *callback)
{
    (void)callback;
}

int net_mgmt(int request, struct net_if *interface, void *data, size_t size)
{
    (void)interface;
    (void)data;
    (void)size;
    int result = 0;
    if(request == NET_REQUEST_WIFI_DISCONNECT)
    {
        disconnect_calls++;
        result = disconnect_request_result;
        if(result == 0)
        {
            disconnect_is_requested = true;
            if(disconnect_delay_milliseconds >= 0)
                disconnect_due_milliseconds = time_milliseconds + disconnect_delay_milliseconds;
        }
    }
    else if(request == NET_REQUEST_WIFI_CONNECT)
    {
        assert(station_state == STATION_IDLE && !disconnect_is_requested);
        connect_calls++;
        station_state = STATION_CONNECTING;
    }
    else if(request == NET_REQUEST_WIFI_AP_ENABLE)
    {
        /* Model a driver that starts the AP before reporting an error. */
        hotspot_is_enabled = true;
        result = hotspot_enable_result;
    }
    else if(request == NET_REQUEST_WIFI_AP_DISABLE)
    {
        hotspot_disable_calls++;
        hotspot_is_enabled = false;
    }
    if(host_network_hook != NULL && result == 0)
        result = host_network_hook(request, interface, data, size);
    return result;
}

const struct net_in_addr *net_if_ipv4_get_global_addr(struct net_if *interface, int state)
{
    (void)interface;
    (void)state;
    struct net_in_addr *selectedValue;
    if(has_address)
    {
        selectedValue = &station_address;
    }
    else
    {
        selectedValue = NULL;
    }
    return selectedValue;
}

bool net_if_ipv4_addr_rm(struct net_if *interface, const struct net_in_addr *address)
{
    assert(interface == &station_interface && memcmp(address, &station_address, sizeof(*address)) == 0);
    bool was_present = has_address;
    has_address = false;
    emit_event(NET_EVENT_IPV4_ADDR_DEL, NULL);
    return was_present;
}

const char *net_addr_ntop(int family, const struct net_in_addr *address, char *text, size_t size)
{
    (void)family;
    (void)address;
    char *selectedValue;
    if(snprintf(text, size, "10.0.0.17") < (int)size)
    {
        selectedValue = text;
    }
    else
    {
        selectedValue = NULL;
    }
    return selectedValue;
}

int net_addr_pton(int family, const char *text, struct net_in_addr *address)
{
    (void)family;
    (void)text;
    memset(address, 0, sizeof(*address));
    return 0;
}

void *net_if_ipv4_addr_lookup(struct net_in_addr *address, struct net_if **interface)
{
    (void)address;
    (void)interface;
    return NULL;
}

void *net_if_ipv4_addr_add(struct net_if *interface, struct net_in_addr *address, int type, int lifetime)
{
    (void)interface;
    (void)type;
    (void)lifetime;
    return address;
}

int net_if_ipv4_set_netmask_by_addr(struct net_if *interface, struct net_in_addr *address, struct net_in_addr *mask)
{
    (void)interface;
    (void)address;
    (void)mask;
    return 0;
}

void net_if_ipv4_set_gw(struct net_if *interface, struct net_in_addr *address)
{
    (void)interface;
    (void)address;
}

struct net_linkaddr *net_if_get_link_addr(struct net_if *interface)
{
    (void)interface;
    static struct net_linkaddr address = {{0, 1, 2, 3, 4, 5}};
    return &address;
}

int net_dhcpv4_server_start(struct net_if *interface, struct net_in_addr *address)
{
    (void)interface;
    (void)address;
    hotspot_dhcp_is_running = true;
    return hotspot_dhcp_start_result;
}

int net_dhcpv4_server_stop(struct net_if *interface)
{
    (void)interface;
    hotspot_dhcp_stop_calls++;
    hotspot_dhcp_is_running = false;
    return 0;
}

int esp_wifi_get_config(int interface, wifi_config_t *configuration)
{
    (void)interface;
    memset(configuration, 0, sizeof(*configuration));
    return hotspot_get_configuration_result;
}

int esp_wifi_set_config(int interface, wifi_config_t *configuration)
{
    (void)interface;
    maximum_hotspot_clients = configuration->ap.max_connection;
    return hotspot_set_configuration_result;
}

int settings_subsys_init(void)
{
    return 0;
}

int settings_save_one(const char *name, const void *data, size_t size)
{
    assert(strcmp(name, "wifi/network") == 0 && size == sizeof(stored_network));
    settings_write_calls++;
    int result;
    if(settings_write_failures > 0)
    {
        result = -EIO; /**< Input/output operation failed in the host model. */
    }
    else
    {
        result = 0;
    }
    if(settings_write_failures > 0)
        settings_write_failures--;
    if(result == 0)
    {
        memcpy(&stored_network, data, size);
        has_stored_network = true;
    }
    return result;
}

static ssize_t read_settings_record(void *context, void *data, size_t size)
{
    (void)context;
    assert(size == sizeof(stored_network));
    memcpy(data, &stored_network, size);
    return (ssize_t)size;
}

int settings_load_subtree_direct(const char *name, settings_load_direct_cb callback, void *context)
{
    assert(strcmp(name, "wifi/network") == 0);
    if(deleted_record)
        (void)callback(NULL, 0, NULL, NULL, context);
    else if(has_stored_network)
        (void)callback(NULL, sizeof(stored_network), read_settings_record, NULL, context);
    return 0;
}
