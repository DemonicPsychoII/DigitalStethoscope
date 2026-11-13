/* Host harness for the pure input decoding of L1_PHYSICALINTERFACE.
 *
 *   decode <raw> <murmur> <bpm>            prints <status> <filter>
 *   debounce <time>:<sample> ...           sample is raw, murmur, bpm or invalid;
 *                                          prints <time> <status> <filter> per reported transition
 *   volume <millivolts>                    prints <percent>
 *   track <time>:<status>:<millivolts> ... status is valid, failed or absent;
 *                                          prints <time> <status> <percent> per reported reading
 */

#include "../../../L1_services/L1_PHYSICALINTERFACE/physicalinterface_input.c"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const char *harness_statusName(bool isValid)
{
    return isValid ? "VALID" : "FAILED";
}

static const char *harness_inputStatusName(enum physicalinterface_input_status status)
{
    const char *name = "ABSENT";

    if(status == PHYSICALINTERFACE_INPUT_VALID)
    {
        name = "VALID";
    }
    else if(status == PHYSICALINTERFACE_INPUT_FAILED)
    {
        name = "FAILED";
    }
    else
    {
        name = "ABSENT";
    }

    return name;
}

static const char *harness_filterName(enum physicalinterface_listening_filter filter)
{
    const char *name = "BPM";

    if(filter == PHYSICALINTERFACE_LISTENING_FILTER_RAW)
    {
        name = "RAW";
    }
    else if(filter == PHYSICALINTERFACE_LISTENING_FILTER_MURMUR)
    {
        name = "MURMUR";
    }
    else
    {
        name = "BPM";
    }

    return name;
}

static struct physicalinterface_switch_sample harness_sample(const char *name)
{
    struct physicalinterface_switch_sample sample = physicalinterface_decodeSwitch(-1, -1, -1);

    if(strcmp(name, "raw") == 0)
    {
        sample = physicalinterface_decodeSwitch(1, 0, 0);
    }
    else if(strcmp(name, "murmur") == 0)
    {
        sample = physicalinterface_decodeSwitch(0, 1, 0);
    }
    else if(strcmp(name, "bpm") == 0)
    {
        sample = physicalinterface_decodeSwitch(0, 0, 1);
    }
    else if(strcmp(name, "invalid") == 0)
    {
        sample = physicalinterface_decodeSwitch(0, 0, 0);
    }
    else
    {
        fprintf(stderr, "unknown sample %s\n", name);
        exit(2);
    }

    return sample;
}

static enum physicalinterface_input_status harness_inputStatus(const char *name)
{
    enum physicalinterface_input_status status = PHYSICALINTERFACE_INPUT_ABSENT;

    if(strcmp(name, "valid") == 0)
    {
        status = PHYSICALINTERFACE_INPUT_VALID;
    }
    else if(strcmp(name, "failed") == 0)
    {
        status = PHYSICALINTERFACE_INPUT_FAILED;
    }
    else if(strcmp(name, "absent") == 0)
    {
        status = PHYSICALINTERFACE_INPUT_ABSENT;
    }
    else
    {
        fprintf(stderr, "unknown status %s\n", name);
        exit(2);
    }

    return status;
}

static void harness_debounce(int count, char **steps)
{
    struct physicalinterface_switch_debounce debounce;

    physicalinterface_resetSwitchDebounce(&debounce);

    for(int index = 0; index < count; index++)
    {
        char name[16] = {0};
        long long timeMilliseconds = 0;

        if(sscanf(steps[index], "%lld:%15s", &timeMilliseconds, name) != 2)
        {
            fprintf(stderr, "bad step %s\n", steps[index]);
            exit(2);
        }

        if(physicalinterface_debounceSwitch(&debounce, harness_sample(name), (int64_t)timeMilliseconds))
        {
            printf("%lld %s %s\n", timeMilliseconds, harness_statusName(debounce.stable.isValid), harness_filterName(debounce.stable.filter));
        }
    }
}

static void harness_track(int count, char **steps)
{
    struct physicalinterface_volume_tracker tracker;

    physicalinterface_resetVolumeTracker(&tracker);

    for(int index = 0; index < count; index++)
    {
        char status[16] = {0};
        long long timeMilliseconds = 0;
        long millivolts = 0;

        if(sscanf(steps[index], "%lld:%15[a-z]:%ld", &timeMilliseconds, status, &millivolts) != 3)
        {
            fprintf(stderr, "bad step %s\n", steps[index]);
            exit(2);
        }

        if(physicalinterface_trackVolume(&tracker, harness_inputStatus(status), (int32_t)millivolts))
        {
            printf("%lld %s %u\n", timeMilliseconds, harness_inputStatusName(tracker.reportedStatus), (unsigned)tracker.reportedPercent);
        }
    }
}

int main(int argumentCount, char **arguments)
{
    if(argumentCount < 2)
    {
        fprintf(stderr, "missing operation\n");
        return 2;
    }

    if((strcmp(arguments[1], "decode") == 0) && (argumentCount == 5))
    {
        struct physicalinterface_switch_sample sample = physicalinterface_decodeSwitch(atoi(arguments[2]), atoi(arguments[3]), atoi(arguments[4]));

        printf("%s %s\n", harness_statusName(sample.isValid), harness_filterName(sample.filter));
    }
    else if(strcmp(arguments[1], "debounce") == 0)
    {
        harness_debounce(argumentCount - 2, &arguments[2]);
    }
    else if((strcmp(arguments[1], "volume") == 0) && (argumentCount == 3))
    {
        printf("%u\n", (unsigned)physicalinterface_volumePercentFromMillivolts((int32_t)strtol(arguments[2], NULL, 10)));
    }
    else if(strcmp(arguments[1], "track") == 0)
    {
        harness_track(argumentCount - 2, &arguments[2]);
    }
    else
    {
        fprintf(stderr, "unknown operation %s\n", arguments[1]);
        return 2;
    }

    return 0;
}
