/* Including the units permits private-state inspection without exposing firmware internals. */
#define main    simulation_main
#define k_sleep simulation_sleep
#include "simulation.c"
#undef main
#undef k_sleep
int k_sleep(k_timeout_t timeout);
#include "../../L2_application/L2_COMMUNICATION/communication.c"

static int64_t acknowledgement_time_milliseconds = -1;

int k_sleep(k_timeout_t timeout)
{
    int result = simulation_sleep(timeout);
    /* Model the worker's acknowledgement while CONTROL sleeps, without scheduling a second thread. */
    if((acknowledgement_time_milliseconds >= 0) && (acknowledgement_time_milliseconds <= time_milliseconds))
    {
        communication_setState(COMMUNICATION_STATE_STOPPED);
    }
    return result;
}

static bool memory_is_clear(const void *data, size_t size)
{
    const unsigned char *bytes = data;
    bool is_clear = true;
    for(size_t index = 0; index < size; index++)
    {
        is_clear = is_clear && bytes[index] == 0;
    }
    return is_clear;
}

int main(int argument_count, char **arguments)
{
    if(argument_count == 4 && strcmp(arguments[1], "release-wait") == 0)
    {
        int64_t timeout_milliseconds = strtoll(arguments[2], NULL, 10);
        acknowledgement_time_milliseconds = strtoll(arguments[3], NULL, 10);
        horizon_milliseconds = timeout_milliseconds + 1000;
        (void)communication_postEvent(COMMUNICATION_EVENT_LISTENING_STARTED);
        if(acknowledgement_time_milliseconds == 0)
        {
            communication_setState(COMMUNICATION_STATE_STOPPED);
        }
        int result = communication_waitForWiFiStop(K_MSEC(timeout_milliseconds));
        trace("release_wait_result", result);
        trace("release_wait_elapsed", (int)time_milliseconds);
        return 0;
    }
    if(argument_count == 2 && strcmp(arguments[1], "coalesced-boot-resume") == 0)
    {
        horizon_milliseconds = 6000;
        communication_StoredNetwork = record;
        communication_StoredNetworkIsValid = true;
        communication_BootJoinIsPending = true;
        (void)communication_postEvent(COMMUNICATION_EVENT_LISTENING_STARTED);
        (void)communication_postEvent(COMMUNICATION_EVENT_LISTENING_STOPPED);
        communication_runIdleCycle();
        snapshot();
        return 0;
    }
    int result = simulation_main();
    trace("stored_buffer_cleared", memory_is_clear(&communication_StoredNetwork, sizeof(communication_StoredNetwork)));
    trace("request_password_cleared", memory_is_clear(communication_PageRequest.network.password, sizeof(communication_PageRequest.network.password)));
    return result;
}
