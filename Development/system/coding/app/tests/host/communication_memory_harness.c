/* Including the units permits erasure inspection without exposing firmware internals. */
#define main simulation_main
#include "simulation.c"
#undef main
#include "../../L2_application/L2_COMMUNICATION/communication.c"

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

enum
{
    WHITE_BOX_REGISTRATION_CHANGE = 1, /* A later registration publishes another server Device id. */
    WHITE_BOX_CLOCK_STEP = 2,          /* The thread applies an anchor that steps UTC forward by one hour. */
};

static void change_worker_state(int value)
{
    if(value == WHITE_BOX_REGISTRATION_CHANGE)
    {
        snprintf(communication_ServerDeviceId, sizeof(communication_ServerDeviceId), "%s", "7999");
        communication_publishDeliveryPrerequisites();
    }
    else if(value == WHITE_BOX_CLOCK_STEP)
    {
        k_spinlock_key_t key = k_spin_lock(&communication_ControlLock);
        communication_AppliedTimeAnchor.utc_seconds += 3600U;
        k_spin_unlock(&communication_ControlLock, key);
    }
    else
    {
        abort();
    }
}

int main(int argument_count, char **arguments)
{
    white_box_handler = change_worker_state;
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
