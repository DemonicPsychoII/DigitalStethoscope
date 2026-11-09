#include "service_boundary.c"

static bool is_zero(const void *data, size_t size)
{
    const unsigned char *bytes = data;
    bool result = true;
    for(size_t index = 0; index < size; index++)
        result = result && bytes[index] == 0;
    return result;
}

static struct http_client_ctx first_client = {1};
static struct http_client_ctx second_client = {2};

static struct http_response_ctx connect_fragment(struct http_client_ctx *client, const char *body, enum http_transaction_status status)
{
    struct http_request_ctx request = {(const uint8_t *)body, strlen(body)};
    struct http_response_ctx response = {0};
    portal_ConnectDetail.cb(client, status, &request, &response, NULL);
    return response;
}

static enum http_status command_request(enum portal_request_type type)
{
    struct http_request_ctx request = {0};
    struct http_response_ctx response = {0};
    portal_ActivityDetail.cb(&first_client, HTTP_SERVER_REQUEST_DATA_FINAL, &request, &response, &type);
    if(response.status == HTTP_503_SERVICE_UNAVAILABLE)
    {
        assert(response.header_count == 1);
        assert(strcmp(response.headers[0].name, "Retry-After") == 0 && strcmp(response.headers[0].value, "1") == 0);
    }
    return response.status;
}

static enum http_status route_request(const char *path, unsigned method)
{
    const struct host_http_resource *resources[] = {&portal_PageResource, &portal_StatusResource, &portal_ConnectResource, &portal_RescanResource, &portal_CancelResource, &portal_ActivityResource};
    enum http_status status = HTTP_404_NOT_FOUND;
    for(size_t index = 0; index < ARRAY_SIZE(resources); index++)
        if(strcmp(resources[index]->path, path) == 0)
        {
            if((resources[index]->detail->bitmask_of_supported_http_methods & BIT(method)) != 0)
            {
                status = HTTP_200_OK;
            }
            else
            {
                status = HTTP_405_METHOD_NOT_ALLOWED;
            }
        }
    return status;
}

static void publish_network(const char *name, bool password)
{
    struct wifi_scan_entry network = {0};
    assert(strlen(name) <= 32);
    strcpy(network.name, name);
    network.needsPassword = password;
    portal_setNetworks(&network, 1);
}

static void scan_result(const char *name, enum wifi_security_type security, int signal_strength)
{
    struct wifi_scan_result result = {.security = security, .rssi = signal_strength, .ssid_length = (uint8_t)strlen(name)};
    memcpy(result.ssid, name, result.ssid_length);
    emit_event(NET_EVENT_WIFI_SCAN_RESULT, &result);
}

static void finish_scan(void)
{
    emit_event(NET_EVENT_WIFI_SCAN_DONE, NULL);
}

static const char *result_name(int result)
{
    static char other[24];

    const struct
    {
        int code;
        const char *name;
    } names[] = {
        {0, "0"},
        {-EAGAIN, "EAGAIN"},
        {-EBADMSG, "EBADMSG"},
        {-EBUSY, "EBUSY"},
        {-ECANCELED, "ECANCELED"},
        {-EINVAL, "EINVAL"},
        {-EIO, "EIO"},
        {-ENOENT, "ENOENT"},
        {-ENOSYS, "ENOSYS"},
        {-EPROTO, "EPROTO"},
        {-ERANGE, "ERANGE"},
        {-ETIMEDOUT, "ETIMEDOUT"},
    };

    for(size_t index = 0; index < ARRAY_SIZE(names); index++)
        if(names[index].code == result)
            return names[index].name;
    snprintf(other, sizeof(other), "%d", result);
    return other;
}

static const char time_server_name[] = "pool.ntp.org";
static struct normalised_time untouched_time_sample;
static int64_t running_cancel_call_milliseconds;
static int64_t running_cancel_return_milliseconds;
static int running_cancel_result = 1;
static int running_start_result = 1;
static bool late_lookup_answer_is_delivered;

static void model_time_server(enum time_server_lookup lookup)
{
    time_server_is_modelled = true;
    time_worker_is_modelled = true;
    time_server_lookup = lookup;
    memset(&untouched_time_sample, 0x5A, sizeof(untouched_time_sample));
}

static bool run_submitted_work(void)
{
    struct k_work *work = submitted_work;
    submitted_work = NULL;
    if(work != NULL)
        work->handler(work);
    return work != NULL;
}

/* Runs as another thread would while the worker is blocked between two of its steps for the whole stop bound. */
static void cancel_while_worker_runs(void)
{
    running_cancel_call_milliseconds = time_milliseconds;
    running_cancel_result = wifi_cancelTimeSynchronization();
    running_cancel_return_milliseconds = time_milliseconds;
    running_start_result = wifi_startTimeSynchronization(time_server_name);
    if(late_lookup_answer_is_delivered)
    {
        assert(pending_lookup_callback != NULL);
        dns_resolve_cb_t callback = pending_lookup_callback;
        pending_lookup_callback = NULL;
        answer_time_server_lookup(callback, pending_lookup_context);
    }
}

static void cancel_at_next_worker_unlock(void)
{
    host_mutex_unlock_hook = cancel_while_worker_runs;
}

static void print_terminal_wait(const char *prefix)
{
    struct normalised_time sample = untouched_time_sample;
    const int result = wifi_waitForTimeSynchronization(&sample, K_NO_WAIT);
    printf("%swait_terminal_failure=%d %swait_code=%s %ssample_untouched=%d\n",
           prefix,
           (result < 0) && (result != -EAGAIN),
           prefix,
           result_name(result),
           prefix,
           memcmp(&sample, &untouched_time_sample, sizeof(sample)) == 0);
}

static void run_time_synchronization_case(const char *scenario, const char *argument)
{
    if(strcmp(scenario, "time-start-busy") == 0)
    {
        model_time_server(TIME_SERVER_LOOKUP_ANSWERED);
        const int first = wifi_startTimeSynchronization(time_server_name);
        printf("first_start=%s ", result_name(first));
        printf("second_start=%s\n", result_name(wifi_startTimeSynchronization(time_server_name)));
    }
    else if(strcmp(scenario, "time-cancel-inactive") == 0)
    {
        model_time_server(TIME_SERVER_LOOKUP_ANSWERED);
        const int first = wifi_cancelTimeSynchronization();
        const int second = wifi_cancelTimeSynchronization();
        printf("first_cancel=%s second_cancel=%s cancel_milliseconds=%lld\n", result_name(first), result_name(second), (long long)time_milliseconds);
    }
    else if(strcmp(scenario, "time-cancel-before-worker") == 0)
    {
        model_time_server(TIME_SERVER_LOOKUP_ANSWERED);
        time_response_is_queued = true;
        printf("start=%s ", result_name(wifi_startTimeSynchronization(time_server_name)));
        const int cancel = wifi_cancelTimeSynchronization();
        printf("cancel=%s cancel_milliseconds=%lld\n", result_name(cancel), (long long)time_milliseconds);
        print_terminal_wait("");
        (void)run_submitted_work();
        printf("lookups=%d sockets_opened=%d requests=%d\n", time_server_lookups, time_server_sockets_opened, time_requests_sent);
        print_terminal_wait("after_worker_");
        printf("restart=%s\n", result_name(wifi_startTimeSynchronization(time_server_name)));
    }
    else if(strcmp(scenario, "time-cancel-during-lookup") == 0)
    {
        /* Argument: "pending" keeps the query unanswered; "late-answer" answers it during cancellation. */
        model_time_server(TIME_SERVER_LOOKUP_PENDING);
        late_lookup_answer_is_delivered = strcmp(argument, "late-answer") == 0;
        host_time_lookup_hook = cancel_at_next_worker_unlock;
        printf("start=%s\n", result_name(wifi_startTimeSynchronization(time_server_name)));
        assert(run_submitted_work());
        printf("running_cancel_failed=%d running_cancel_code=%s cancel_milliseconds=%lld start_while_cancelling=%s\n",
               running_cancel_result < 0,
               result_name(running_cancel_result),
               (long long)(running_cancel_return_milliseconds - running_cancel_call_milliseconds),
               result_name(running_start_result));
        printf("lookup_cancellations=%d sockets_opened=%d requests=%d\n", time_server_lookup_cancellations, time_server_sockets_opened, time_requests_sent);
        print_terminal_wait("");
        printf("final_cancel=%s ", result_name(wifi_cancelTimeSynchronization()));
        printf("restart=%s\n", result_name(wifi_startTimeSynchronization(time_server_name)));
    }
    else if(strcmp(scenario, "time-cancel-during-exchange") == 0)
    {
        model_time_server(TIME_SERVER_LOOKUP_ANSWERED);
        time_response[0] = (uint8_t)((0U << 6) | (4U << 3) | 4U);
        time_response[1] = 1U;
        time_response_is_queued = true;
        time_response_arrival_milliseconds = 50;
        host_time_request_hook = cancel_at_next_worker_unlock;
        printf("start=%s\n", result_name(wifi_startTimeSynchronization(time_server_name)));
        assert(run_submitted_work());
        printf("running_cancel_failed=%d running_cancel_code=%s cancel_milliseconds=%lld start_while_cancelling=%s\n",
               running_cancel_result < 0,
               result_name(running_cancel_result),
               (long long)(running_cancel_return_milliseconds - running_cancel_call_milliseconds),
               result_name(running_start_result));
        printf("requests=%d responses_parsed=%d sockets_closed=%d\n", time_requests_sent, time_response_parse_calls, time_server_sockets_closed);
        print_terminal_wait("");
        printf("final_cancel=%s ", result_name(wifi_cancelTimeSynchronization()));
        printf("restart=%s\n", result_name(wifi_startTimeSynchronization(time_server_name)));
    }
    else if(strcmp(scenario, "time-single-request") == 0)
    {
        /* Argument: "<arrival milliseconds or none> <native seconds> <native fraction> <native uncertainty>". */
        char arrival[16] = "";
        unsigned long long seconds = 0;
        unsigned fraction = 0;
        unsigned uncertainty = 0;
        assert(sscanf(argument, "%15s %llu %u %u", arrival, &seconds, &fraction, &uncertainty) == 4);
        model_time_server(TIME_SERVER_LOOKUP_ANSWERED);
        time_response_native = (struct sntp_time){.seconds = seconds, .fraction = fraction, .uncertainty_us = uncertainty};
        time_response[0] = (uint8_t)((0U << 6) | (4U << 3) | 4U);
        time_response[1] = 2U;
        time_response_is_queued = strcmp(arrival, "none") != 0;
        time_response_arrival_milliseconds = atoll(arrival);
        printf("start=%s\n", result_name(wifi_startTimeSynchronization(time_server_name)));
        assert(run_submitted_work());
        const struct net_in_addr *address = &time_server_socket_address.sin_addr;
        printf("lookup_name=%s server_address=%u.%u.%u.%u server_port=%u requests=%d\n",
               time_server_lookup_name,
               address->s4_addr[0],
               address->s4_addr[1],
               address->s4_addr[2],
               address->s4_addr[3],
               (unsigned)net_htons(time_server_socket_address.sin_port),
               time_requests_sent);
        struct normalised_time sample = untouched_time_sample;
        const int result = wifi_waitForTimeSynchronization(&sample, K_NO_WAIT);
        printf("wait=%s wait_terminal_failure=%d sample_untouched=%d\n",
               result_name(result),
               (result < 0) && (result != -EAGAIN),
               memcmp(&sample, &untouched_time_sample, sizeof(sample)) == 0);
        if(result == 0)
            printf("utc_seconds=%llu utc_fraction_nanoseconds=%u receive_monotonic_microseconds=%llu uncertainty_microseconds=%u\n",
                   (unsigned long long)sample.utc_seconds,
                   sample.utc_fraction_nanoseconds,
                   (unsigned long long)sample.receive_monotonic_microseconds,
                   sample.estimated_uncertainty_microseconds);
        struct normalised_time repeated = untouched_time_sample;
        const int repeated_result = wifi_waitForTimeSynchronization(&repeated, K_SECONDS(1));
        printf("repeated_wait_same=%d requests_after_waits=%d\n",
               (repeated_result == result) && ((result != 0) || (memcmp(&repeated, &sample, sizeof(sample)) == 0)),
               time_requests_sent);
    }
    else if(strcmp(scenario, "time-apply") == 0)
    {
        /* Argument: "<UTC seconds> <fraction nanoseconds> <receive microseconds> <apply milliseconds> <uncertainty microseconds> <ok|EIO>". */
        unsigned long long seconds = 0;
        unsigned fraction = 0;
        unsigned long long receive = 0;
        long long apply_milliseconds = 0;
        unsigned uncertainty = 0;
        char clock_result[8] = "";
        assert(sscanf(argument, "%llu %u %llu %lld %u %7s", &seconds, &fraction, &receive, &apply_milliseconds, &uncertainty, clock_result) == 6);
        clock_set_result = (strcmp(clock_result, "ok") == 0) ? 0 : -EIO; /**< Real-time clock rejects the set in the host model. */
        time_milliseconds = apply_milliseconds;
        const struct normalised_time sample = {
            .utc_seconds = seconds,
            .utc_fraction_nanoseconds = fraction,
            .receive_monotonic_microseconds = receive,
            .estimated_uncertainty_microseconds = uncertainty,
        };
        struct applied_time_anchor anchor;
        memset(&anchor, 0x5A, sizeof(anchor));
        struct applied_time_anchor untouched_anchor = anchor;
        const int result = wifi_applyTimeSynchronization(&sample, &anchor);
        printf("apply=%s clock_set_calls=%d clock_is_realtime=%d clock_seconds=%lld clock_nanoseconds=%ld anchor_untouched=%d\n",
               result_name(result),
               clock_set_calls,
               clock_set_clock == SYS_CLOCK_REALTIME,
               (long long)clock_set_time.tv_sec,
               clock_set_time.tv_nsec,
               memcmp(&anchor, &untouched_anchor, sizeof(anchor)) == 0);
        if(result == 0)
            printf("anchor_seconds=%llu anchor_fraction_nanoseconds=%u anchor_monotonic_microseconds=%llu anchor_uncertainty_microseconds=%u\n",
                   (unsigned long long)anchor.utc_seconds,
                   anchor.utc_fraction_nanoseconds,
                   (unsigned long long)anchor.applied_monotonic_microseconds,
                   anchor.estimated_uncertainty_microseconds);
    }
    else
        abort();
}

static void run_wifi_case(const char *scenario, const char *argument)
{
    struct wifi_network network = {"selected-network", "test-password"};
    struct wifi_scan_entry networks[16] = {0};
    assert(wifi_init() == 0);
    if(strcmp(scenario, "validity") == 0)
    {
        if(strcmp(argument, "null") == 0)
            printf("%d\n", wifi_isValidNetwork(NULL));
        else
        {
            if(strcmp(argument, "empty-name") == 0)
                network.name[0] = 0;
            else if(strcmp(argument, "unterminated-name") == 0)
                memset(network.name, 'n', sizeof(network.name));
            else if(strcmp(argument, "unterminated-password") == 0)
                memset(network.password, 'p', sizeof(network.password));
            else
            {
                assert(strlen(argument) < sizeof(network.password));
                strcpy(network.password, argument);
            }
            struct wifi_network original = network;
            printf("%d\n", wifi_isValidNetwork(&network));
            assert(memcmp(&network, &original, sizeof(network)) == 0);
        }
    }
    else if(strcmp(scenario, "security") == 0)
    {
        assert(wifi_startScan() == 0);
        scan_result("network", (enum wifi_security_type)atoi(argument), -30);
        finish_scan();
        printf("%d\n", wifi_waitForScanResult(networks, 16, K_NO_WAIT));
    }
    else if(strcmp(scenario, "strongest") == 0)
    {
        assert(wifi_startScan() == 0);
        for(int index = 0; index < 20; index++)
        {
            char name[33];
            snprintf(name, sizeof(name), "network-%02d", index);
            scan_result(name, WIFI_SECURITY_TYPE_NONE, -90 + index);
        }
        scan_result("network-19", WIFI_SECURITY_TYPE_PSK, -1);
        scan_result("network-19", WIFI_SECURITY_TYPE_NONE, -99);
        finish_scan();
        assert(wifi_waitForScanResult(networks, 16, K_NO_WAIT) == 16);
        for(size_t index = 0; index < 16; index++)
        {
            assert(atoi(networks[index].name + 8) >= 4);
            if(strcmp(networks[index].name, "network-19") == 0)
                assert(networks[index].needsPassword);
            for(size_t other_index = index + 1; other_index < 16; other_index++)
                assert(strcmp(networks[index].name, networks[other_index].name) != 0);
        }
    }
    else if(strcmp(scenario, "cancelled-scan") == 0)
    {
        assert(wifi_startScan() == 0);
        assert(wifi_cancelScan() == -ETIMEDOUT); /**< Operation exceeded its wait deadline in the host model. */
        assert(time_milliseconds == 1000);
        scan_result("late-old", WIFI_SECURITY_TYPE_NONE, -1);
        assert(wifi_startScan() == -EBUSY); /**< Service is busy with another operation in the host model. */
        finish_scan();
        assert(wifi_waitForScanResult(networks, 16, K_NO_WAIT) == -ECANCELED); /**< Operation was cancelled in the host model. */
        assert(wifi_startScan() == 0);
        assert(wifi_waitForScanResult(networks, 16, K_NO_WAIT) == -EAGAIN); /**< Operation is still pending; try again in the host model. */
        scan_result("current", WIFI_SECURITY_TYPE_PSK, -50);
        finish_scan();
        assert(wifi_waitForScanResult(networks, 16, K_NO_WAIT) == 1);
        assert(strcmp(networks[0].name, "current") == 0);
    }
    else if(strcmp(scenario, "disconnect-before-rearm") == 0)
    {
        assert(wifi_connect(&network) == 0);
        disconnect_delay_milliseconds = -1;
        assert(wifi_disconnect() == -ETIMEDOUT); /**< Operation exceeded its wait deadline in the host model. */
        assert(time_milliseconds == 1000);
        struct wifi_status status = {0};
        has_address = true;
        station_state = STATION_CONNECTED;
        emit_event(NET_EVENT_WIFI_CONNECT_RESULT, &status);
        emit_event(NET_EVENT_IPV4_ADDR_ADD, NULL);
        assert(!wifi_isConnected());
        assert(wifi_waitForConnection(K_NO_WAIT) == -EAGAIN); /**< Operation is still pending; try again in the host model. */
        assert(wifi_connect(&network) == -ETIMEDOUT);         /**< Operation exceeded its wait deadline in the host model. */
        assert(connect_calls == 1 && time_milliseconds == 2000);
        has_address = false;
        status.status = WIFI_REASON_DISCONN_USER_REQUEST;
        emit_event(NET_EVENT_WIFI_DISCONNECT_RESULT, &status);
        disconnect_is_requested = false;
        station_state = STATION_IDLE;
        assert(wifi_connect(&network) == 0);
        assert(wifi_waitForConnection(K_NO_WAIT) == -EAGAIN); /**< Operation is still pending; try again in the host model. */
        has_address = true;
        station_state = STATION_CONNECTED;
        status.status = 0;
        emit_event(NET_EVENT_WIFI_CONNECT_RESULT, &status);
        assert(wifi_waitForConnection(K_NO_WAIT) == 0);
    }
    else if(strcmp(scenario, "scan-cancel-confirmed") == 0)
    {
        assert(wifi_startScan() == 0);
        scheduled_event = NET_EVENT_WIFI_SCAN_DONE;
        scheduled_event_time_milliseconds = 1000;
        assert(wifi_cancelScan() == 0);
        assert(time_milliseconds == 1000);
        assert(wifi_startScan() == 0);
    }
    else if(strcmp(scenario, "disconnect-confirmed") == 0)
    {
        assert(wifi_connect(&network) == 0);
        disconnect_delay_milliseconds = 1000;
        assert(wifi_disconnect() == 0);
        assert(time_milliseconds == 1000);
        assert(wifi_connect(&network) == 0);
    }
    else if(strcmp(scenario, "old-link") == 0)
    {
        assert(wifi_connect(&network) == 0);
        struct wifi_status status = {0};
        has_address = true;
        station_state = STATION_CONNECTED;
        emit_event(NET_EVENT_WIFI_CONNECT_RESULT, &status);
        assert(wifi_isConnected());
        disconnect_delay_milliseconds = 200;
        assert(wifi_connect(&network) == 0);
        assert(!wifi_isConnected() && !has_address && time_milliseconds <= 1000);
        assert(wifi_waitForConnection(K_NO_WAIT) == -EAGAIN); /**< Operation is still pending; try again in the host model. */
    }
    else if(strcmp(scenario, "join-from-state") == 0)
    {
        if(strcmp(argument, "idle") != 0)
        {
            assert(wifi_connect(&network) == 0);
            assert(disconnect_calls == 0);
            if(strcmp(argument, "connected") == 0)
            {
                struct wifi_status status = {0};
                station_state = STATION_CONNECTED;
                has_address = true;
                emit_event(NET_EVENT_WIFI_CONNECT_RESULT, &status);
                assert(wifi_isConnected());
            }
        }
        int previous_connect_calls = connect_calls;
        assert(wifi_connect(&network) == 0);
        assert(connect_calls == previous_connect_calls + 1);
        if(strcmp(argument, "idle") == 0)
        {
            assert(disconnect_calls == (0));
        }
        else
        {
            assert(disconnect_calls == (1));
        }
        assert(wifi_waitForConnection(K_NO_WAIT) == -EAGAIN); /**< Operation is still pending; try again in the host model. */
        struct wifi_status status = {0};
        station_state = STATION_CONNECTED;
        has_address = true;
        emit_event(NET_EVENT_IPV4_ADDR_ADD, NULL);
        emit_event(NET_EVENT_WIFI_CONNECT_RESULT, &status);
        assert(wifi_waitForConnection(K_NO_WAIT) == 0);
    }
    else if(strcmp(scenario, "retained-address") == 0)
    {
        assert(wifi_connect(&network) == 0);
        struct wifi_status status = {0};
        station_state = STATION_CONNECTED;
        has_address = true;
        emit_event(NET_EVENT_WIFI_CONNECT_RESULT, &status);
        assert(wifi_isConnected());
        retain_dhcp_address = true;
        strcpy(network.name, "different-network");
        assert(wifi_connect(&network) == 0);
        assert(!has_address && !wifi_isConnected());
        station_state = STATION_CONNECTED;
        emit_event(NET_EVENT_WIFI_CONNECT_RESULT, &status);
        assert(wifi_waitForConnection(K_NO_WAIT) == -EAGAIN); /**< Operation is still pending; try again in the host model. */
        has_address = true;
        emit_event(NET_EVENT_IPV4_ADDR_ADD, NULL);
        assert(wifi_waitForConnection(K_NO_WAIT) == 0);
    }
    else if(strcmp(scenario, "disconnect-request-failure") == 0)
    {
        assert(wifi_connect(&network) == 0);
        disconnect_request_result = -EAGAIN;                  /**< Operation is still pending; try again in the host model. */
        assert(wifi_disconnect() == -EAGAIN);                 /**< Operation is still pending; try again in the host model. */
        assert(wifi_waitForConnection(K_NO_WAIT) == -EAGAIN); /**< Operation is still pending; try again in the host model. */
        disconnect_request_result = 0;
        assert(wifi_connect(&network) == 0);
        assert(disconnect_calls == 2 && connect_calls == 2);
    }
    else if(strcmp(scenario, "device-identifier") == 0)
    {
        /* Argument: "<12 hex digits of the factory MAC> <size> [read-error|null]". */
        char mac[13] = "";
        unsigned size = 0;
        char option[16] = "";
        char identifier[64];
        assert(sscanf(argument, "%12s %u %15s", mac, &size, option) >= 2 && strlen(mac) == 12 && size <= sizeof(identifier));
        for(size_t index = 0; index < 6; index++)
        {
            char pair[3] = {mac[2 * index], mac[2 * index + 1], '\0'};
            factory_mac[index] = (uint8_t)strtoul(pair, NULL, 16);
        }
        factory_mac_result = (strcmp(option, "read-error") == 0) ? ESP_ERR_INVALID_CRC : ESP_OK;
        memset(identifier, 0x5A, sizeof(identifier));
        const int result = wifi_getDeviceIdentifier((strcmp(option, "null") == 0) ? NULL : identifier, size);
        bool is_untouched_beyond_size = true;
        for(size_t index = size; index < sizeof(identifier); index++)
            is_untouched_beyond_size = is_untouched_beyond_size && identifier[index] == 0x5A;
        const bool is_terminated = (size == 0) || (memchr(identifier, '\0', size) != NULL);
        const char *name = (result == 0) ? "OK" : (result == -EINVAL) ? "EINVAL"
                                              : (result == -EIO)      ? "EIO"
                                              : (result == -ENODATA)  ? "ENODATA"
                                              : (result == -ENOSYS)   ? "ENOSYS"
                                                                      : "OTHER";
        const bool has_text = (size > 0) && is_terminated && (identifier[0] != '\0') && (strcmp(option, "null") != 0);
        printf("%s %s %d %d %d\n", name, has_text ? identifier : "-", is_untouched_beyond_size, is_terminated, factory_mac_reads);
    }
    else if(strcmp(scenario, "hotspot-name") == 0)
    {
        /* Argument: "ok" or "read-error". The link address stub is 00:01:02:03:04:05, so the name proves the factory source. */
        factory_mac_result = (strcmp(argument, "read-error") == 0) ? ESP_ERR_INVALID_CRC : ESP_OK;
        const int result = wifi_startHotspot();
        printf("%d %s %d\n", result, hotspot_is_enabled ? hotspot_name : "-", factory_mac_reads);
    }
    else if(strcmp(scenario, "hotspot-client-limit") == 0)
    {
        assert(wifi_startHotspot() == 0);
        assert(maximum_hotspot_clients == 1);
    }
    else if(strcmp(scenario, "hotspot-rollback") == 0)
    {
        if(strcmp(argument, "enable") == 0)
            hotspot_enable_result = -EIO; /**< Driver reports failure after partially enabling the AP. */
        else if(strcmp(argument, "get-configuration") == 0)
            hotspot_get_configuration_result = 1;
        else if(strcmp(argument, "set-configuration") == 0)
            hotspot_set_configuration_result = 1;
        else
        {
            assert(strcmp(argument, "dhcp") == 0);
            hotspot_dhcp_start_result = -EIO; /**< DHCP startup fails after partially starting the server. */
        }
        if(strcmp(argument, "dhcp") == 0)
        {
            assert(wifi_startHotspot() == 0);
            assert(wifi_startDHCPServer() == -EIO); /**< Preserve the original DHCP startup error. */
        }
        else
        {
            hotspot_dhcp_is_running = true;
            assert(wifi_startHotspot() == -EIO); /**< Preserve the original AP startup/configuration error. */
        }
        assert(!hotspot_is_enabled && !hotspot_dhcp_is_running);
        assert(hotspot_disable_calls == 1 && hotspot_dhcp_stop_calls == 1);
        assert(time_milliseconds == 0);
    }
    else if(strcmp(scenario, "disconnect-at-address-boundary") == 0)
    {
        assert(wifi_connect(&network) == 0);
        struct wifi_status status = {0};
        station_state = STATION_CONNECTED;
        emit_event(NET_EVENT_WIFI_CONNECT_RESULT, &status);
        assert(wifi_waitForConnection(K_NO_WAIT) == -EAGAIN); /**< Association without IPv4 remains pending. */
        if(strcmp(argument, "online") == 0)
        {
            has_address = true;
            emit_event(NET_EVENT_IPV4_ADDR_ADD, NULL);
            assert(wifi_waitForConnection(K_NO_WAIT) == 0);
        }
        if(strcmp(argument, "requested") == 0)
        {
            assert(wifi_disconnect() == 0);
            assert(wifi_waitForConnection(K_NO_WAIT) == -EAGAIN); /**< Requested disconnect is cancellation, not join failure. */
        }
        else
        {
            station_state = STATION_IDLE;
            has_address = false;
            emit_event(NET_EVENT_WIFI_DISCONNECT_RESULT, &status);
            if(strcmp(argument, "online") == 0)
            {
                assert(wifi_waitForConnection(K_NO_WAIT) == -EAGAIN); /**< Established link loss is handled by recovery, not a pending join. */
            }
            else
            {
                assert(strcmp(argument, "before-ipv4") == 0);
                assert(wifi_waitForConnection(K_SECONDS(15)) == -ENOTCONN); /**< Disconnect terminates the join immediately before IPv4. */
                assert(time_milliseconds == 0);
                has_address = true;
                emit_event(NET_EVENT_IPV4_ADDR_ADD, NULL);
                assert(wifi_waitForConnection(K_NO_WAIT) == -ENOTCONN); /**< Late IPv4 cannot turn the failed join into success. */
                assert(wifi_connect(&network) == 0);
                assert(connect_calls == 2);
                assert(wifi_waitForConnection(K_NO_WAIT) == -EAGAIN); /**< A new attempt clears the previous failure. */
            }
        }
        assert(!wifi_isConnected());
    }
    else if(strcmp(scenario, "deleted-record") == 0)
    {
        deleted_record = true;
        memset(&network, 0x55, sizeof(network));
        assert(storage_read("wifi/network", &network, sizeof(network)) == -ENOENT); /**< Requested record or network was not found in the host model. */
        for(size_t index = 0; index < sizeof(network); index++)
            assert(((unsigned char *)&network)[index] == 0x55);
    }
    else if(strcmp(scenario, "time-response") == 0)
    {
        unsigned leap_indicator;
        unsigned stratum;
        long long arrival_milliseconds;
        assert(sscanf(argument, "%u %u %lld", &leap_indicator, &stratum, &arrival_milliseconds) == 3);
        assert(leap_indicator <= 3 && stratum <= 255);
        time_server_is_modelled = true;
        time_response[0] = (uint8_t)((leap_indicator << 6) | (4U << 3) | 4U);
        time_response[1] = (uint8_t)stratum;
        time_response_is_queued = true;
        time_response_arrival_milliseconds = arrival_milliseconds;
        wifi_TimeSynchronizationGeneration = 1;
        wifi_TimeSynchronizationState = WIFI_TIME_SYNCHRONIZATION_PENDING;
        const struct net_sockaddr_in address = {0};
        struct normalised_time sample = {0};
        const int result = wifi_exchangeTimeSample(1, sys_timepoint_calc(K_MSEC(WIFI_TIME_SYNCHRONIZATION_OPERATION_TIMEOUT_MS)), &address, &sample);
        assert(time_query_timeout_milliseconds == 0);
        assert(time_milliseconds == arrival_milliseconds); /**< The response ends the exchange; no wait until the deadline. */
        if(result == 0)
        {
            assert(sample.utc_seconds == time_response_native.seconds);
            assert(sample.utc_fraction_nanoseconds == time_response_native.fraction * 1000U);
            assert(sample.receive_monotonic_microseconds == (uint64_t)arrival_milliseconds * 1000U);
            assert(sample.estimated_uncertainty_microseconds == time_response_native.uncertainty_us);
        }
        else
        {
            assert(result == -EPROTO);                                                     /**< Rejected response fails the exchange. */
            assert(sample.utc_seconds == 0 && sample.receive_monotonic_microseconds == 0); /**< Not normalized. */
        }
        printf("%d %d\n", result == 0, time_response_parse_calls);
    }
    else if(strncmp(scenario, "time-", 5) == 0)
        run_time_synchronization_case(scenario, argument);
    else
        abort();
}

static void publish_failed_join(void)
{
    portal_setStatus(PORTAL_STATUS_CONNECT_FAILED, -EACCES);
}

static void run_portal_case(const char *scenario, const char *argument)
{
    if(strcmp(scenario, "form-open") == 0)
        publish_network("open-network", false);
    else if(strcmp(scenario, "form-maximum") == 0)
        publish_network("NNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNN", true);
    else
        publish_network("selected-network", true);
    bool listener_never_appears = strcmp(scenario, "no-listener-stop") == 0;
    if(strcmp(scenario, "start-timeout") == 0 || listener_never_appears)
        listener_start_delay_milliseconds = 2000;
    if((strcmp(scenario, "start-timeout") == 0 || listener_never_appears))
    {
        assert(portal_start() == (-ETIMEDOUT)); /**< Operation exceeded its wait deadline in the host model. */
    }
    else
    {
        assert(portal_start() == (0));
    }
    if(strncmp(scenario, "form", 4) == 0)
    {
        struct http_response_ctx response = connect_fragment(&first_client, argument, HTTP_SERVER_REQUEST_DATA_FINAL);
        printf("%d\n", response.status);
        struct portal_request request = {0};
        if(portal_waitForRequest(&request, K_NO_WAIT) == 0)
            printf("%s\n%s\n", request.network.name, request.network.password);
        assert(is_zero(portal_Form, sizeof(portal_Form)));
        assert(is_zero(portal_RequestQueue, sizeof(portal_RequestQueue)));
    }
    else if(strcmp(scenario, "fragment-owner") == 0)
    {
        connect_fragment(&first_client, "network=selected-", HTTP_SERVER_REQUEST_DATA_MORE);
        struct http_response_ctx response = connect_fragment(&second_client, "network=attacker&password=attacker", HTTP_SERVER_REQUEST_DATA_FINAL);
        assert(response.status == HTTP_409_CONFLICT);
        struct http_request_ctx request = {0};
        struct http_response_ctx poll_response = {0};
        portal_StatusDetail.cb(&second_client, HTTP_SERVER_REQUEST_DATA_FINAL, &request, &poll_response, NULL);
        assert(poll_response.body_len > 0 && portal_FormClient == &first_client);
        connect_fragment(&second_client, "", HTTP_SERVER_TRANSACTION_ABORTED);
        response = connect_fragment(&first_client, "network&password=test-password", HTTP_SERVER_REQUEST_DATA_FINAL);
        assert(response.status == HTTP_202_ACCEPTED);
        struct portal_request queued_request = {0};
        assert(portal_waitForRequest(&queued_request, K_NO_WAIT) == 0);
        assert(strcmp(queued_request.network.name, "selected-network") == 0);
        assert(strcmp(queued_request.network.password, "test-password") == 0);
        assert(is_zero(portal_Form, sizeof(portal_Form)) && is_zero(portal_RequestQueue, sizeof(portal_RequestQueue)));
        portal_setStatus(PORTAL_STATUS_SELECTING, 0);
        assert(connect_fragment(&second_client, "network=selected-network&password=test-password", HTTP_SERVER_REQUEST_DATA_FINAL).status == HTTP_409_CONFLICT);
        connect_fragment(&first_client, "", HTTP_SERVER_TRANSACTION_COMPLETE);
        assert(connect_fragment(&second_client, "network=selected-network&password=test-password", HTTP_SERVER_REQUEST_DATA_FINAL).status == HTTP_202_ACCEPTED);
    }
    else if(strcmp(scenario, "abort-wipes") == 0)
    {
        connect_fragment(&first_client, "network=selected-network&password=secret", HTTP_SERVER_REQUEST_DATA_MORE);
        connect_fragment(&first_client, "", HTTP_SERVER_TRANSACTION_ABORTED);
        assert(is_zero(portal_Form, sizeof(portal_Form)) && portal_FormClient == NULL);
        struct http_response_ctx response = connect_fragment(&second_client, "network=selected-network&password=test-password", HTTP_SERVER_REQUEST_DATA_FINAL);
        assert(response.status == HTTP_202_ACCEPTED);
    }
    else if(strcmp(scenario, "activity-state-race") == 0)
    {
        host_mutex_unlock_hook = publish_failed_join;
        assert(command_request(PORTAL_REQUEST_ACTIVITY) == HTTP_202_ACCEPTED);
        assert(portal_Status == PORTAL_STATUS_CONNECT_FAILED);
        assert(portal_Error == -EACCES);
        assert(portal_SelectionIsReady);
        struct portal_request request = {0};
        assert(portal_waitForRequest(&request, K_NO_WAIT) == 0);
        assert(request.type == PORTAL_REQUEST_ACTIVITY);
        assert(command_request(PORTAL_REQUEST_RESCAN) == HTTP_202_ACCEPTED);
    }
    else if(strcmp(scenario, "queue-full") == 0)
    {
        for(int index = 0; index < 4; index++)
            assert(command_request(PORTAL_REQUEST_ACTIVITY) == HTTP_202_ACCEPTED);
        assert(command_request(PORTAL_REQUEST_RESCAN) == HTTP_503_SERVICE_UNAVAILABLE);
        assert(portal_Status == PORTAL_STATUS_SELECTING && portal_RequestCount == 4);
        struct http_response_ctx response = connect_fragment(&first_client, "network=selected-network&password=test-password", HTTP_SERVER_REQUEST_DATA_FINAL);
        assert(response.status == HTTP_503_SERVICE_UNAVAILABLE && response.header_count == 1);
        assert(strcmp(response.headers[0].name, "Retry-After") == 0 && strcmp(response.headers[0].value, "1") == 0);
        assert(portal_Status == PORTAL_STATUS_SELECTING && portal_RequestCount == 4);
    }
    else if(strcmp(scenario, "routing") == 0)
    {
        assert(route_request("/unknown", HTTP_GET) == HTTP_404_NOT_FOUND);
        assert(route_request("/unknown", HTTP_POST) == HTTP_404_NOT_FOUND);
        assert(route_request("/", HTTP_POST) == HTTP_405_METHOD_NOT_ALLOWED);
        assert(route_request("/status", HTTP_POST) == HTTP_405_METHOD_NOT_ALLOWED);
        assert(route_request("/connect", HTTP_GET) == HTTP_405_METHOD_NOT_ALLOWED);
        assert(route_request("/cancel", HTTP_GET) == HTTP_405_METHOD_NOT_ALLOWED);
        assert(route_request("/rescan", HTTP_GET) == HTTP_405_METHOD_NOT_ALLOWED);
        assert(route_request("/activity", HTTP_GET) == HTTP_405_METHOD_NOT_ALLOWED);
        assert(route_request("/", HTTP_GET) == HTTP_200_OK);
    }
    else if(strcmp(scenario, "fragment-overflow") == 0)
    {
        char fragment[PORTAL_FORM_SIZE + 1];
        memset(fragment, 'x', sizeof(fragment) - 1);
        fragment[sizeof(fragment) - 1] = 0;
        connect_fragment(&first_client, fragment, HTTP_SERVER_REQUEST_DATA_MORE);
        struct http_response_ctx response = connect_fragment(&first_client, "overflow", HTTP_SERVER_REQUEST_DATA_FINAL);
        assert(response.status == HTTP_413_PAYLOAD_TOO_LARGE);
        assert(portal_RequestCount == 0 && is_zero(portal_Form, sizeof(portal_Form)));
    }
    else if(strcmp(scenario, "gate") == 0)
    {
        portal_setStatus((enum portal_status)atoi(argument), -EACCES); /**< Credentials or access were rejected in the host model. */
        assert(connect_fragment(&first_client, "network=selected-network&password=test-password", HTTP_SERVER_REQUEST_DATA_FINAL).status == HTTP_409_CONFLICT);
        assert(command_request(PORTAL_REQUEST_RESCAN) == HTTP_409_CONFLICT);
        assert(command_request(PORTAL_REQUEST_CANCEL) == HTTP_409_CONFLICT);
        assert(command_request(PORTAL_REQUEST_ACTIVITY) == HTTP_409_CONFLICT);
    }
    else if(strcmp(scenario, "post-failure-rescan") == 0)
    {
        portal_setStatus(PORTAL_STATUS_CONNECTING, 0);
        portal_setStatus(PORTAL_STATUS_CONNECT_FAILED, -EACCES); /**< Credentials or access were rejected in the host model. */
        assert(command_request(PORTAL_REQUEST_RESCAN) == HTTP_202_ACCEPTED);
        struct portal_request request = {0};
        assert(portal_waitForRequest(&request, K_NO_WAIT) == 0);
        assert(request.type == PORTAL_REQUEST_RESCAN);
        assert(connect_fragment(&first_client, "network=selected-network&password=test-password", HTTP_SERVER_REQUEST_DATA_FINAL).status == HTTP_409_CONFLICT);
        portal_setStatus(PORTAL_STATUS_SCANNING, 0);
        assert(connect_fragment(&first_client, "network=selected-network&password=test-password", HTTP_SERVER_REQUEST_DATA_FINAL).status == HTTP_409_CONFLICT);
        publish_network("selected-network", true);
        assert(connect_fragment(&first_client, "network=selected-network&password=test-password", HTTP_SERVER_REQUEST_DATA_FINAL).status == HTTP_409_CONFLICT);
        portal_setStatus(PORTAL_STATUS_SELECTING, 0);
        assert(connect_fragment(&first_client, "network=selected-network&password=test-password", HTTP_SERVER_REQUEST_DATA_FINAL).status == HTTP_202_ACCEPTED);
        assert(portal_waitForRequest(&request, K_NO_WAIT) == 0);
        assert(request.type == PORTAL_REQUEST_CONNECT);
    }
    else if(strcmp(scenario, "stop-wipes") == 0)
    {
        connect_fragment(&first_client, "network=selected-network&password=test-password", HTTP_SERVER_REQUEST_DATA_FINAL);
        portal_setStatus(PORTAL_STATUS_SELECTING, 0);
        connect_fragment(&first_client, "network=selected-network&password=unread", HTTP_SERVER_REQUEST_DATA_MORE);
        assert(portal_stop() == 0);
        assert(is_zero(portal_Form, sizeof(portal_Form)) && is_zero(portal_RequestQueue, sizeof(portal_RequestQueue)));
        assert(command_request(PORTAL_REQUEST_ACTIVITY) == HTTP_409_CONFLICT);
    }
    else if(strcmp(scenario, "restart-clears") == 0)
    {
        portal_setAddress("10.0.0.17");
        portal_setStatus(PORTAL_STATUS_CONNECT_FAILED, -EACCES); /**< Credentials or access were rejected in the host model. */
        assert(portal_stop() == 0 && portal_start() == 0);
        assert(portal_Address[0] == 0 && portal_Error == 0 && portal_NetworkCount == 1 && portal_Status == PORTAL_STATUS_SELECTING);
        assert(is_zero(portal_Form, sizeof(portal_Form)) && is_zero(portal_RequestQueue, sizeof(portal_RequestQueue)));
    }
    else if(strcmp(scenario, "stop-confirmation") == 0)
    {
        stop_result = -EALREADY; /**< Requested state is already active in the host model. */
        listener_stop_delay_milliseconds = atoi(argument);
        int result = portal_stop();
        if(listener_stop_delay_milliseconds > 1000)
        {
            assert(result == (-ETIMEDOUT)); /**< Operation exceeded its wait deadline in the host model. */
        }
        else
        {
            assert(result == (0));
        }
        printf("%d %lld\n", result == -ETIMEDOUT, (long long)time_milliseconds); /**< Operation exceeded its wait deadline in the host model. */
        if(listener_stop_delay_milliseconds > 1000)
        {
            assert(portal_start() == -EBUSY); /**< Service is busy with another operation in the host model. */
            advance_clock(listener_stop_delay_milliseconds);
            assert(portal_stop() == 0);
        }
    }
    else if(strcmp(scenario, "start-timeout") == 0)
    {
        assert(time_milliseconds == 1000);
        assert(command_request(PORTAL_REQUEST_ACTIVITY) == HTTP_409_CONFLICT);
    }
    else if(listener_never_appears)
    {
        assert(time_milliseconds == 1000 && *portal_service.fd < 0);
        if(strcmp(argument, "already-stopped") == 0)
        {
            stop_result = -EALREADY; /**< Requested state is already active in the host model. */
        }
        else
        {
            stop_result = 0;
        }
        assert(portal_stop() == 0);
        assert(time_milliseconds == 2000);
        listener_start_delay_milliseconds = 0;
        assert(portal_start() == 0);
        assert(command_request(PORTAL_REQUEST_ACTIVITY) == HTTP_202_ACCEPTED);
    }
    else if(strcmp(scenario, "status-json") == 0)
    {
        struct wifi_scan_entry networks[16] = {0};
        for(size_t index = 0; index < 16; index++)
        {
            assert(strlen(argument) <= 32);
            strcpy(networks[index].name, argument);
            networks[index].needsPassword = index % 2 != 0;
        }
        portal_setNetworks(networks, 16);
        struct http_request_ctx request = {0};
        struct http_response_ctx response = {0};
        portal_StatusDetail.cb(&second_client, HTTP_SERVER_REQUEST_DATA_FINAL, &request, &response, NULL);
        fwrite(response.body, 1, response.body_len, stdout);
        assert(portal_RequestCount == 0);
    }
    else if(strcmp(scenario, "page") == 0)
        fputs(portal_Page, stdout);
    else
        abort();
}

static void print_hexadecimal(const char *name, const char *text, size_t length)
{
    printf("%s=", name);
    for(size_t index = 0; index < length; index++)
        printf("%02x", (unsigned char)text[index]);
    printf("\n");
}

static void run_storage_case(const char *scenario, const char *argument)
{
    if(strcmp(scenario, "server-profile") != 0)
        abort();
    /* Argument: "erased", "null" or "<image file> [<read error offset>]". */
    static struct storage_server_profile profile;
    char path[512] = "";
    long long error_offset = -1;
    const int fields = sscanf(argument, "%511s %lld", path, &error_offset);
    assert(fields >= 1);
    if(strcmp(path, "erased") != 0 && strcmp(path, "null") != 0)
    {
        FILE *file = fopen(path, "rb");
        assert(file != NULL);
        host_server_profile_image_length = fread(host_server_profile_image, 1, sizeof(host_server_profile_image), file);
        assert(feof(file) && !ferror(file));
        fclose(file);
    }
    if(fields == 2)
    {
        host_flash_read_error_offset = (off_t)error_offset;
        host_flash_read_error = -EIO; /**< Flash driver read failure in the host model. */
    }
    memset(&profile, 0x5A, sizeof(profile));
    const int result = storage_readServerProfile((strcmp(path, "null") == 0) ? NULL : &profile);
    printf("result=%s cleared=%d\n", result_name(result), is_zero(&profile, sizeof(profile)));
    if(result == 0)
    {
        const size_t base_url_length = strnlen(profile.baseUrl, sizeof(profile.baseUrl));
        const size_t certificate_length = strnlen(profile.certificate, sizeof(profile.certificate));
        printf("base_url_terminated=%d certificate_terminated=%d certificate_length=%zu keep_alive=%u\n",
               base_url_length < sizeof(profile.baseUrl),
               certificate_length < sizeof(profile.certificate),
               profile.certificateLength,
               (unsigned)profile.serverKeepAliveSeconds);
        print_hexadecimal("base_url", profile.baseUrl, base_url_length);
        print_hexadecimal("certificate", profile.certificate, certificate_length);
    }
}

int main(int argument_count, char **arguments)
{
    assert(argument_count >= 3);
    const char *argument;
    if(argument_count > 3)
    {
        argument = arguments[3];
    }
    else
    {
        argument = "";
    }
    if(strcmp(arguments[1], "wifi") == 0)
        run_wifi_case(arguments[2], argument);
    else if(strcmp(arguments[1], "portal") == 0)
        run_portal_case(arguments[2], argument);
    else if(strcmp(arguments[1], "storage") == 0)
        run_storage_case(arguments[2], argument);
    else
        abort();
    return 0;
}
