/* Run the production workflow against deterministic kernel and L1 substitutes.
 * These tests prove orchestration decisions, not radio or scheduler timing. */
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../../L2_application/L2_COMMUNICATION/communication.c"

static int64_t test_Now;
static int64_t test_EventAt = -1;
static enum communication_event test_Event;
static int test_ConnectResult;
static int test_ConnectionResult;
static int test_ScanResult;
static int test_ScanStartResult;
static int test_SaveResult;
static int test_DisconnectResult;
static int test_CancelResult;
static int test_PortalStopResult;
static int test_DHCPStopResult;
static int test_HotspotStopResult;
static int test_PortalStartResult;
static bool test_Connected;
static bool test_ScanFinished;
static int test_ConnectCount;
static int test_ScanCount;
static int test_SaveCount;
static int test_CancelCount;
static int test_DisconnectCount;
static int test_HotspotCount;
static int64_t test_ConnectTimes[8];
static enum portal_status test_Status;
static bool test_CancelRequest;

static void test_advance(k_timeout_t timeout)
{
    if(timeout.ticks >= 0)
    {
        int64_t end = test_Now + timeout.ticks;

        if((test_EventAt >= test_Now) && (test_EventAt <= end))
        {
            test_Now = test_EventAt;
            test_EventAt = -1;

            assert(communication_postEvent(test_Event) == 0);
        }
        else
        {
            test_Now = end;
        }
    }
}

k_spinlock_key_t k_spin_lock(struct k_spinlock *lock)
{
    ARG_UNUSED(lock);

    return 0;
}

void k_spin_unlock(struct k_spinlock *lock, k_spinlock_key_t key)
{
    ARG_UNUSED(lock);
    ARG_UNUSED(key);
}

void k_sem_give(struct k_sem *sem)
{
    sem->count = 1;
}

int k_sem_take(struct k_sem *sem, k_timeout_t timeout)
{
    if(sem->count == 0)
    {
        test_advance(timeout);
    }

    int result = -EAGAIN;

    if(sem->count != 0)
    {
        sem->count = 0;
        result = 0;
    }

    return result;
}

int32_t k_sleep(k_timeout_t timeout)
{
    test_advance(timeout);

    return 0;
}

k_timepoint_t sys_timepoint_calc(k_timeout_t timeout)
{
    int64_t result = INT64_MAX;

    if(timeout.ticks >= 0)
    {
        result = test_Now + timeout.ticks;
    }

    return result;
}

k_timeout_t sys_timepoint_timeout(k_timepoint_t deadline)
{
    k_timeout_t result = K_FOREVER;

    if(deadline != INT64_MAX)
    {
        result.ticks = deadline - test_Now;

        if(result.ticks < 0)
        {
            result.ticks = 0;
        }
    }

    return result;
}

bool sys_timepoint_expired(k_timepoint_t deadline)
{

    return test_Now >= deadline;
}

void k_thread_create(struct k_thread *thread, void *stack, size_t size, void (*entry)(void *, void *, void *), void *a, void *b, void *c, int priority, uint32_t options, k_timeout_t delay)
{
    ARG_UNUSED(thread);
    ARG_UNUSED(stack);
    ARG_UNUSED(size);
    ARG_UNUSED(entry);
    ARG_UNUSED(a);
    ARG_UNUSED(b);
    ARG_UNUSED(c);
    ARG_UNUSED(priority);
    ARG_UNUSED(options);
    ARG_UNUSED(delay);
}

int k_thread_name_set(struct k_thread *thread, const char *name)
{
    ARG_UNUSED(thread);
    ARG_UNUSED(name);

    return 0;
}

void k_thread_start(struct k_thread *thread)
{
    ARG_UNUSED(thread);
}

int wifi_init(void)
{

    return 0;
}

int wifi_readSettings(struct wifi_network *network)
{
    ARG_UNUSED(network);

    return -ENOENT;
}

int wifi_storeSettings(const struct wifi_network *network)
{
    assert(network->name[0] != '\0');
    test_SaveCount++;

    return test_SaveResult;
}

int wifi_connect(const struct wifi_network *network)
{
    ARG_UNUSED(network);
    assert(test_ConnectCount < 8);

    test_ConnectTimes[test_ConnectCount] = test_Now;
    test_ConnectCount++;

    return test_ConnectResult;
}

int wifi_waitForConnection(k_timeout_t timeout)
{
    if(test_ConnectionResult == -EAGAIN)
    {
        test_advance(timeout);
    }

    return test_ConnectionResult;
}

int wifi_disconnect(void)
{
    test_DisconnectCount++;

    return test_DisconnectResult;
}

bool wifi_isConnected(void)
{

    return test_Connected;
}

int wifi_startScan(void)
{
    test_ScanCount++;

    return test_ScanStartResult;
}

int wifi_cancelScan(void)
{
    test_CancelCount++;

    return test_CancelResult;
}

int wifi_waitForScanResult(struct wifi_scan_entry *list, size_t count, k_timeout_t timeout)
{
    ARG_UNUSED(list);
    ARG_UNUSED(count);

    if(test_ScanResult == -EAGAIN)
    {
        test_advance(timeout);
    }
    else
    {
        test_ScanFinished = true;
    }

    return test_ScanResult;
}

int wifi_startHotspot(void)
{
    assert(test_ScanFinished);
    test_HotspotCount++;

    return 0;
}

int wifi_stopHotspot(void)
{

    return test_HotspotStopResult;
}

int wifi_startDHCPServer(void)
{

    return 0;
}

int wifi_stopDHCPServer(void)
{

    return test_DHCPStopResult;
}

int portal_start(void)
{

    return test_PortalStartResult;
}

int portal_stop(void)
{

    return test_PortalStopResult;
}

void portal_setNetworks(const struct wifi_scan_entry *list, size_t count)
{
    ARG_UNUSED(list);
    ARG_UNUSED(count);
    assert(test_ScanFinished);
}

void portal_setStatus(enum portal_status status, int error)
{
    ARG_UNUSED(error);

    test_Status = status;
}

int portal_waitForRequest(struct portal_request *request, k_timeout_t timeout)
{
    int result = -EAGAIN;

    if(test_CancelRequest)
    {
        request->type = PORTAL_REQUEST_CANCEL;
        test_CancelRequest = false;
        result = 0;
    }
    else
    {
        test_advance(timeout);
    }

    return result;
}

static void test_startAt(int64_t time)
{
    test_EventAt = time;
    test_Event = COMMUNICATION_EVENT_LISTENING_STARTED;
}

int main(int argc, char **argv)
{
    assert(argc == 2);

    struct wifi_network network = {.name = "selected", .password = "password"};

    communication_PageRequest.network = network;

    if(strcmp(argv[1], "control_burst") == 0)
    {
        for(int index = 0; index < 100; index++)
        {
            assert(communication_postEvent(COMMUNICATION_EVENT_SETUP_REQUESTED) == 0);
            assert(communication_postEvent(COMMUNICATION_EVENT_LISTENING_STARTED) == 0);
            assert(communication_postEvent(COMMUNICATION_EVENT_LISTENING_STOPPED) == 0);
        }

        assert(communication_postEvent(COMMUNICATION_EVENT_LISTENING_STARTED) == 0);
        assert(communication_waitForWiFiStop(K_NO_WAIT) == -EAGAIN);
        communication_runIdleCycle();
        assert(communication_waitForWiFiStop(K_NO_WAIT) == 0);
        assert(!communication_SetupIsRequested);
        assert(communication_postEvent(COMMUNICATION_EVENT_LISTENING_STOPPED) == 0);
        communication_waitForEvents(K_NO_WAIT);
        assert(!communication_ListeningIsActive);
        assert(communication_postEvent((enum communication_event)99) == -EINVAL);
    }
    else if(strcmp(argv[1], "retry_deadline") == 0)
    {
        test_ConnectResult = -ECONNREFUSED;
        test_EventAt = 1000;
        test_Event = COMMUNICATION_EVENT_LISTENING_STOPPED;

        assert(communication_connectToNetwork(&network, 4) == -ECONNREFUSED);
        assert(test_ConnectCount == 4);

        for(int index = 0; index < 4; index++)
        {
            assert(test_ConnectTimes[index] == index * 5000);
        }
    }
    else if(strcmp(argv[1], "result_deadline") == 0)
    {
        test_EventAt = 1000;
        test_Event = COMMUNICATION_EVENT_SETUP_REQUESTED;

        assert(communication_handleConnectRequest() == 0);
        assert(test_Now == 10000);
    }
    else if(strcmp(argv[1], "result_interrupt") == 0)
    {
        test_startAt(1000);
        assert(communication_handleConnectRequest() == 0);
        assert(test_Now == 1000);
        communication_runIdleCycle();
        assert(communication_waitForWiFiStop(K_NO_WAIT) == 0);
    }
    else if(strcmp(argv[1], "init_failure_offline") == 0)
    {
        communication_WiFiIsUnavailable = true;

        assert(communication_postEvent(COMMUNICATION_EVENT_LISTENING_STARTED) == 0);
        assert(communication_waitForWiFiStop(K_NO_WAIT) == 0);
    }
    else if(strcmp(argv[1], "scan_interrupt") == 0)
    {
        test_ScanResult = -EAGAIN;

        test_startAt(100);
        assert(communication_scanNetworks() == -ECANCELED);
        assert(test_CancelCount == 1);
        assert(!communication_ScanIsPending);
        communication_runIdleCycle();
        assert(communication_waitForWiFiStop(K_NO_WAIT) == 0);
    }
    else if(strcmp(argv[1], "cleanup_failure") == 0)
    {
        communication_ScanIsPending = true;
        communication_PortalIsActive = true;
        communication_DHCPServerIsActive = true;
        communication_HotspotIsActive = true;
        test_CancelResult = -EIO;
        test_PortalStopResult = -EIO;
        test_DHCPStopResult = -EIO;
        test_HotspotStopResult = -EIO;

        assert(communication_postEvent(COMMUNICATION_EVENT_LISTENING_STARTED) == 0);
        communication_runIdleCycle();
        assert(communication_waitForWiFiStop(K_MSEC(50)) == -EAGAIN);
        assert(test_Now == 250);

        test_CancelResult = 0;
        test_PortalStopResult = 0;
        test_DHCPStopResult = 0;
        test_HotspotStopResult = 0;

        communication_runIdleCycle();
        assert(communication_waitForWiFiStop(K_NO_WAIT) == 0);
    }
    else if(strcmp(argv[1], "connect_cancel_failure") == 0)
    {
        test_ConnectionResult = -EAGAIN;
        test_DisconnectResult = -EIO;

        test_startAt(100);
        assert(communication_connectToNetwork(&network, 4) == -EIO);
        assert(test_ConnectCount == 1);
        communication_runIdleCycle();
        assert(communication_waitForWiFiStop(K_NO_WAIT) == -EAGAIN);
    }
    else if(strcmp(argv[1], "scan_timeout") == 0)
    {
        test_ScanResult = -EAGAIN;

        assert(communication_scanNetworks() == -ETIMEDOUT);
        assert(test_ScanCount == 4);
        assert(test_CancelCount == 4);
        assert(test_Now == 55000);
    }
    else if(strcmp(argv[1], "save_failure") == 0)
    {
        test_SaveResult = -EIO;

        assert(communication_handleConnectRequest() == 0);
        assert(test_ConnectCount == 1);
        assert(test_SaveCount == 2);
        assert(test_Status == PORTAL_STATUS_SAVE_FAILED);
        assert(strcmp(communication_StoredNetwork.password, "password") == 0);
        assert(communication_PageRequest.network.password[0] == '\0');
        assert(test_Now == 10000);
    }
    else if(strcmp(argv[1], "initial_scan_order") == 0)
    {
        test_ScanResult = 1;
        test_CancelRequest = true;

        communication_runSetup();
        assert(test_ScanCount == 1);
        assert(test_HotspotCount == 1);
        assert(test_Now == 2000);
        assert(communication_stopWiFiWork());
    }
    else if(strcmp(argv[1], "recovery_once") == 0)
    {
        communication_StoredNetworkIsValid = true;
        communication_RecoveryIsAllowed = true;
        test_ConnectResult = -ECONNREFUSED;
        test_ScanStartResult = -EIO;

        communication_recoverConnection();
        communication_recoverConnection();
        assert(test_ConnectCount == 4);
        assert(test_ScanCount == 4);
        assert(!communication_RecoveryIsAllowed);
    }
    else if(strcmp(argv[1], "inactivity") == 0)
    {
        int error = 0;

        assert(communication_servePage(&error) == COMMUNICATION_SETUP_CANCELLED);
        assert(test_Now == 300000);
    }
    else if(strcmp(argv[1], "stale_acknowledgement") == 0)
    {
        assert(communication_postEvent(COMMUNICATION_EVENT_LISTENING_STARTED) == 0);
        communication_runIdleCycle();
        assert(communication_waitForWiFiStop(K_NO_WAIT) == 0);
        assert(communication_postEvent(COMMUNICATION_EVENT_LISTENING_STOPPED) == 0);
        assert(communication_postEvent(COMMUNICATION_EVENT_LISTENING_STARTED) == 0);
        assert(communication_waitForWiFiStop(K_NO_WAIT) == -EAGAIN);
        communication_runIdleCycle();
        assert(communication_waitForWiFiStop(K_NO_WAIT) == 0);
    }
    else if(strcmp(argv[1], "start_keeps_station") == 0)
    {
        test_Connected = true;

        assert(communication_postEvent(COMMUNICATION_EVENT_LISTENING_STARTED) == 0);
        assert(communication_connectToNetwork(&network, 4) == -ECANCELED);
        communication_runIdleCycle();
        assert(communication_waitForWiFiStop(K_NO_WAIT) == 0);
        assert(test_DisconnectCount == 0);
        assert(test_ConnectCount == 0);
    }
    else if(strcmp(argv[1], "setup_hold_ignored") == 0)
    {
        communication_SetupIsActive = true;

        assert(communication_postEvent(COMMUNICATION_EVENT_SETUP_REQUESTED) == 0);
        communication_waitForEvents(K_NO_WAIT);
        assert(!communication_SetupIsRequested);
    }
    else if(strcmp(argv[1], "partial_start_failure") == 0)
    {
        test_ScanResult = 1;
        test_PortalStartResult = -EIO;
        test_PortalStopResult = -EIO;

        communication_runSetup();
        assert(communication_PortalIsActive);
        assert(communication_postEvent(COMMUNICATION_EVENT_LISTENING_STARTED) == 0);
        communication_runIdleCycle();
        assert(communication_waitForWiFiStop(K_NO_WAIT) == -EAGAIN);
    }
    else
    {
        assert(false);
    }

    puts("PASS");

    return 0;
}
