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

int main(int argument_count, char **arguments)
{
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
