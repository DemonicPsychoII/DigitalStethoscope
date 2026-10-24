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
    else
        abort();
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
    else
        abort();
    return 0;
}
