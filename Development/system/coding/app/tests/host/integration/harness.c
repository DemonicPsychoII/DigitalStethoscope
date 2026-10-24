#include <setjmp.h>
#include "../service_boundary.c"
#include "../../../L2_application/L2_COMMUNICATION/communication.c"

enum integration_event_type
{
    INTEGRATION_SCAN_DONE,
    INTEGRATION_JOIN_DONE,
    INTEGRATION_CONNECT_FORM,
    INTEGRATION_START,
    INTEGRATION_SETUP_HOLD,
    INTEGRATION_RESCAN,
    INTEGRATION_CANCEL
};

struct integration_event
{
    int64_t due_milliseconds;
    enum integration_event_type type;
    bool consumed;
};

static struct integration_event integration_events[64];
static size_t integration_event_count;
static simulation_entry integration_worker;
static jmp_buf integration_finished;
static int64_t integration_horizon_milliseconds = 15000;
static int integration_scan_calls;
static int integration_scan_failures;
static int integration_join_failures;
static int integration_join_delay_milliseconds = 100;
static int integration_last_response;
static int integration_status_at_stop = -1;
static bool integration_open_network;
static bool integration_bad_form;
static bool integration_disconnects_before_ipv4;
static int64_t integration_first_join_milliseconds;
static int64_t integration_last_join_milliseconds;

static void schedule_event(int64_t due_milliseconds, enum integration_event_type type)
{
    assert(integration_event_count < ARRAY_SIZE(integration_events));
    integration_events[integration_event_count++] = (struct integration_event){due_milliseconds, type, false};
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
    integration_worker = entry;
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

static int network_request(int request, struct net_if *interface, void *data, size_t size)
{
    (void)interface;
    (void)size;
    int result = 0;
    if(request == NET_REQUEST_WIFI_SCAN)
    {
        integration_scan_calls++;
        if(integration_scan_failures > 0)
        {
            integration_scan_failures--;
            result = -EIO; /**< Input/output operation failed in the host model. */
        }
        else
            schedule_event(time_milliseconds + 100, INTEGRATION_SCAN_DONE);
    }
    else if(request == NET_REQUEST_WIFI_CONNECT)
    {
        if(connect_calls == 1)
            integration_first_join_milliseconds = time_milliseconds;
        integration_last_join_milliseconds = time_milliseconds;
        const struct wifi_connect_req_params *parameters = data;
        if(integration_open_network)
        {
            assert(parameters->security == (WIFI_SECURITY_TYPE_NONE));
        }
        else
        {
            assert(parameters->security == (WIFI_SECURITY_TYPE_PSK));
        }
        schedule_event(time_milliseconds + integration_join_delay_milliseconds, INTEGRATION_JOIN_DONE);
    }
    else if(request == NET_REQUEST_WIFI_AP_DISABLE)
        integration_status_at_stop = portal_Status;
    return result;
}

static void add_network(const char *name, enum wifi_security_type security, int signal_strength)
{
    struct wifi_scan_result result = {.security = security, .rssi = signal_strength, .ssid_length = (uint8_t)strlen(name)};
    memcpy(result.ssid, name, result.ssid_length);
    emit_event(NET_EVENT_WIFI_SCAN_RESULT, &result);
}

static void handle_event(enum integration_event_type type)
{
    static struct http_client_ctx client = {1};
    struct http_request_ctx request = {0};
    struct http_response_ctx response = {0};
    if(type == INTEGRATION_SCAN_DONE)
    {
        if(integration_open_network)
        {
            add_network("selected-network", WIFI_SECURITY_TYPE_NONE, -40);
        }
        else
        {
            add_network("selected-network", WIFI_SECURITY_TYPE_PSK, -40);
        }
        add_network("unsupported-network", WIFI_SECURITY_TYPE_SAE, -20);
        add_network("selected-network", WIFI_SECURITY_TYPE_NONE, -90);
        emit_event(NET_EVENT_WIFI_SCAN_DONE, NULL);
    }
    else if(type == INTEGRATION_JOIN_DONE)
    {
        if(station_state == STATION_CONNECTING && !disconnect_is_requested)
        {
            struct wifi_status status = {0};
            if(integration_join_failures > 0)
            {
                status.status = WIFI_STATUS_CONN_WRONG_PASSWORD;
            }
            if(integration_join_failures > 0)
            {
                integration_join_failures--;
                station_state = STATION_IDLE;
            }
            else
            {
                station_state = STATION_CONNECTED;
                has_address = true;
            }
            if(integration_disconnects_before_ipv4)
            {
                has_address = false;
                emit_event(NET_EVENT_WIFI_CONNECT_RESULT, &status);
                station_state = STATION_IDLE;
                status.status = WIFI_REASON_DISCONN_USER_REQUEST;
                emit_event(NET_EVENT_WIFI_DISCONNECT_RESULT, &status);
            }
            else
                emit_event(NET_EVENT_WIFI_CONNECT_RESULT, &status);
            if(has_address)
                emit_event(NET_EVENT_IPV4_ADDR_ADD, NULL);
        }
    }
    else if(type == INTEGRATION_CONNECT_FORM)
    {
        const char *body;
        if(integration_bad_form)
        {
            body = "network=selected-network&password=short";
        }
        else
        {
            if(integration_open_network)
            {
                body = "network=selected-network&password=";
            }
            else
            {
                body = "network=selected-network&password=test-password";
            }
        }
        request.data = (const uint8_t *)body;
        request.data_len = strlen(body);
        portal_ConnectDetail.cb(&client, HTTP_SERVER_REQUEST_DATA_FINAL, &request, &response, NULL);
        integration_last_response = response.status;
        portal_ConnectDetail.cb(&client, HTTP_SERVER_TRANSACTION_COMPLETE, &request, &response, NULL);
    }
    else if(type == INTEGRATION_START)
        assert(communication_postEvent(COMMUNICATION_EVENT_LISTENING_STARTED) == 0);
    else if(type == INTEGRATION_SETUP_HOLD)
        assert(communication_postEvent(COMMUNICATION_EVENT_SETUP_REQUESTED) == 0);
    else
    {
        enum portal_request_type command;
        if(type == INTEGRATION_RESCAN)
        {
            command = PORTAL_REQUEST_RESCAN;
        }
        else
        {
            command = PORTAL_REQUEST_CANCEL;
        }
        if(type == INTEGRATION_RESCAN)
            integration_scan_failures = 4;
        portal_ActivityDetail.cb(&client, HTTP_SERVER_REQUEST_DATA_FINAL, &request, &response, &command);
        integration_last_response = response.status;
    }
}

static void advance_events(int64_t deadline)
{
    int64_t limit;
    if(deadline < integration_horizon_milliseconds)
    {
        limit = deadline;
    }
    else
    {
        limit = integration_horizon_milliseconds;
    }
    for(;;)
    {
        struct integration_event *next = NULL;
        for(size_t index = 0; index < integration_event_count; index++)
            /* Select the next integration event that falls within the current time limit. */
            if(!integration_events[index].consumed && integration_events[index].due_milliseconds <= limit &&
               (next == NULL || integration_events[index].due_milliseconds < next->due_milliseconds))
                next = &integration_events[index];
        if(next == NULL)
            break;
        next->consumed = true;
        time_milliseconds = next->due_milliseconds;
        handle_event(next->type);
    }
    if(deadline >= integration_horizon_milliseconds)
    {
        time_milliseconds = integration_horizon_milliseconds;
        longjmp(integration_finished, 1);
    }
}

static int64_t next_wait_deadline(int64_t deadline)
{
    int64_t next;
    if(deadline < integration_horizon_milliseconds)
    {
        next = deadline;
    }
    else
    {
        next = integration_horizon_milliseconds;
    }
    for(size_t index = 0; index < integration_event_count; index++)
        /* Select the next integration event that falls within the current time limit. */
        if(!integration_events[index].consumed && integration_events[index].due_milliseconds < next)
            next = integration_events[index].due_milliseconds;
    return next;
}

int main(int argument_count, char **arguments)
{
    assert(argument_count == 2);
    const char *scenario = arguments[1];
    host_clock_hook = advance_events;
    host_wait_deadline = next_wait_deadline;
    host_network_hook = network_request;
    integration_open_network = strcmp(scenario, "open-join") == 0;
    bool isDisconnectedBoot = strcmp(scenario, "boot-disconnect-before-ipv4") == 0;
    /* Exercise immediate pending-join failure through the real driver-event boundary. */
    integration_disconnects_before_ipv4 = isDisconnectedBoot || (strcmp(scenario, "page-disconnect-before-ipv4") == 0);
    /* These scenarios begin with an existing persisted network. */
    if(strcmp(scenario, "boot-record") == 0 || strcmp(scenario, "save-failure") == 0 || strcmp(scenario, "rescan-exhaustion") == 0 || isDisconnectedBoot)
    {
        has_stored_network = true;
        strcpy(stored_network.name, "old-network");
        strcpy(stored_network.password, "old-password");
        if((strcmp(scenario, "boot-record") != 0) && !isDisconnectedBoot)
            schedule_event(500, INTEGRATION_SETUP_HOLD);
    }
    if(strcmp(scenario, "save-failure") == 0)
        settings_write_failures = 2;
    if(strcmp(scenario, "join-failure") == 0)
        integration_join_failures = 1;
    integration_bad_form = strcmp(scenario, "invalid-form") == 0;
    if(isDisconnectedBoot)
        integration_horizon_milliseconds = 20000;
    else if(strcmp(scenario, "boot-record") == 0)
        integration_horizon_milliseconds = 2000;
    else if(strcmp(scenario, "rescan-exhaustion") == 0)
    {
        schedule_event(1500, INTEGRATION_RESCAN);
        integration_horizon_milliseconds = 25000;
    }
    else if(strcmp(scenario, "start-selection") == 0)
        schedule_event(1000, INTEGRATION_START);
    else if(strcmp(scenario, "cancel-selection") == 0)
        schedule_event(1000, INTEGRATION_CANCEL);
    else
        schedule_event(1500, INTEGRATION_CONNECT_FORM);
    communication_init();
    if(setjmp(integration_finished) == 0)
        integration_worker(NULL, NULL, NULL);
    printf("connected %d\npage %d\nscan_calls %d\nconnect_calls %d\nwrites %d\nrecord_new %d\nrecord_old %d\nresponse %d\nstatus %d\nstatus_at_stop %d\nnetwork_count %zu\nack %d\ncleanup_fault %d\nclients %d\n",
           wifi_isConnected(),
           portal_IsOpen,
           integration_scan_calls,
           connect_calls,
           settings_write_calls,
           has_stored_network && strcmp(stored_network.name, "selected-network") == 0,
           has_stored_network && strcmp(stored_network.name, "old-network") == 0,
           integration_last_response,
           portal_Status,
           integration_status_at_stop,
           portal_NetworkCount,
           communication_waitForWiFiStop(K_NO_WAIT),
           communication_CleanupFaultIsLatched,
           maximum_hotspot_clients);
    printf("first_join_milliseconds %lld\nlast_join_milliseconds %lld\nboot_attempts %d\njoin_failure %d\n",
           (long long)integration_first_join_milliseconds,
           (long long)integration_last_join_milliseconds,
           communication_BootAttemptsUsed,
           atomic_get(&wifi_FailureCause));
    return 0;
}
