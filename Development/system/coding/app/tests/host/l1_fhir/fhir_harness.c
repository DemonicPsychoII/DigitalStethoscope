/* Host harness for the pure C L1_FHIR serializer. Prints one result line per call:
 * <result-name> <length> <output-as-hex> <canary-intact>
 */

#include "../../../L1_services/L1_FHIR/fhir.c"

#include <stdio.h>
#include <stdlib.h>

#define HARNESS_BUFFER_SIZE (4096)
#define HARNESS_CANARY      ((char)0x5A)

static const char *harness_resultName(int result)
{
    switch(result)
    {
    case 0:
        return "OK";
    case -EINVAL:
        return "EINVAL";
    case -ENOSPC:
        return "ENOSPC";
    case -ENOSYS:
        return "ENOSYS";
    case -EBADMSG:
        return "EBADMSG";
    case -ESTALE:
        return "ESTALE";
    default:
        return "OTHER";
    }
}

static void harness_print(int result, size_t length, const char *buffer, size_t capacity)
{
    printf("%s %zu ", harness_resultName(result), length);
    size_t printed = 0;
    while((printed < capacity) && (buffer[printed] != '\0'))
    {
        printf("%02x", (unsigned char)buffer[printed]);
        printed++;
    }
    if(printed == 0)
    {
        printf("-");
    }
    const bool terminated = (capacity == 0) || (printed < capacity);
    bool canaryIsIntact = true;
    for(size_t index = capacity; index < HARNESS_BUFFER_SIZE; index++)
    {
        canaryIsIntact = canaryIsIntact && (buffer[index] == HARNESS_CANARY);
    }
    printf(" %d %d\n", canaryIsIntact ? 1 : 0, terminated ? 1 : 0);
}

static size_t harness_decodeHex(const char *hex, char *bytes, size_t size)
{
    size_t count = 0;
    while((hex[0] != '\0') && (hex[1] != '\0') && (count + 1 < size))
    {
        char pair[3] = {hex[0], hex[1], '\0'};
        bytes[count++] = (char)strtoul(pair, NULL, 16);
        hex += 2;
    }
    bytes[count] = '\0';
    return count;
}

int main(int argumentCount, char **arguments)
{
    if(argumentCount < 4)
    {
        return 2;
    }
    const char *operation = arguments[1];
    const char *input = (strcmp(arguments[2], "<null>") == 0) ? NULL : arguments[2];
    const size_t capacity = (size_t)strtoul(arguments[3], NULL, 10);
    const bool hasNullOutput = (argumentCount > 4) && (strcmp(arguments[4], "null-output") == 0);
    const bool hasNullLength = (argumentCount > 4) && (strcmp(arguments[4], "null-length") == 0);

    static char buffer[HARNESS_BUFFER_SIZE];
    memset(buffer, HARNESS_CANARY, sizeof(buffer));
    size_t length = 12345;
    int result;

    if(strcmp(operation, "device") == 0)
    {
        result = fhir_buildDeviceRegistration(input, hasNullOutput ? NULL : buffer, capacity, hasNullLength ? NULL : &length);
    }
    else if(strcmp(operation, "condition") == 0)
    {
        result = fhir_buildDeviceRegistrationCondition(input, hasNullOutput ? NULL : buffer, capacity, hasNullLength ? NULL : &length);
    }
    else if(strcmp(operation, "escape") == 0)
    {
        char decoded[256];
        (void)harness_decodeHex(input, decoded, sizeof(decoded));
        struct fhir_writer writer;
        fhir_beginWriter(&writer, buffer, capacity);
        fhir_appendJsonString(&writer, decoded);
        result = fhir_finishWriter(&writer, &length);
    }
    else if((strcmp(operation, "observation") == 0) || (strcmp(operation, "observation-condition") == 0))
    {
        /* Arguments: operation server-id capacity seconds milliseconds patient kind scaled places [null-output|null-length|null-observation] */
        if(argumentCount < 10)
        {
            return 2;
        }
        const struct fhir_observation observation = {
            .serverDeviceId = input,
            .measurementEndUtcSeconds = strtoull(arguments[4], NULL, 10),
            .measurementEndUtcMilliseconds = (uint16_t)strtoul(arguments[5], NULL, 10),
            .patientReference = (strcmp(arguments[6], "<null>") == 0) ? NULL : arguments[6],
            .kind = (enum fhir_observation_kind)strtol(arguments[7], NULL, 10),
            .heartRateScaled = (uint32_t)strtoul(arguments[8], NULL, 10),
            .heartRateDecimalPlaces = (uint8_t)strtoul(arguments[9], NULL, 10),
        };
        const char *option = (argumentCount > 10) ? arguments[10] : "";
        const struct fhir_observation *given = (strcmp(option, "null-observation") == 0) ? NULL : &observation;
        char *output = (strcmp(option, "null-output") == 0) ? NULL : buffer;
        size_t *givenLength = (strcmp(option, "null-length") == 0) ? NULL : &length;
        if(strcmp(operation, "observation") == 0)
        {
            result = fhir_buildObservation(given, output, capacity, givenLength);
        }
        else
        {
            result = fhir_buildObservationCondition(given, output, capacity, givenLength);
        }
    }
    else if(strcmp(operation, "registration") == 0)
    {
        /* Arguments: registration physical-id capacity status location body-hex base-url [option] */
        if(argumentCount < 8)
        {
            return 2;
        }
        static const char *const causeNames[] = {"NONE", "SERVER_ERROR", "MULTIPLE_MATCHES", "UNSUPPORTED", "REJECTED", "INVALID_REPRESENTATION"};
        const char *bodyHex = arguments[6];
        const size_t bodyLength = (strcmp(bodyHex, "-") == 0) ? 0U : strlen(bodyHex) / 2U;
        /* Exact-size heap copy without terminator, so the sanitizer reports any read past bodyLength. */
        char *body = NULL;
        if(bodyLength > 0U)
        {
            char *decoded = malloc(bodyLength + 1U);
            (void)harness_decodeHex(bodyHex, decoded, bodyLength + 1U);
            body = malloc(bodyLength);
            memcpy(body, decoded, bodyLength);
            free(decoded);
        }
        const struct fhir_response response = {
            .status = (uint16_t)strtoul(arguments[4], NULL, 10),
            .location = (strcmp(arguments[5], "<null>") == 0) ? NULL : arguments[5],
            .body = body,
            .bodyLength = bodyLength,
        };
        const char *option = (argumentCount > 8) ? arguments[8] : "";
        const char *baseUrl = (strcmp(arguments[7], "<null>") == 0) ? NULL : arguments[7];
        enum fhir_response_cause cause = (enum fhir_response_cause)99;
        result = fhir_parseDeviceRegistration((strcmp(option, "null-response") == 0) ? NULL : &response, baseUrl, input, (strcmp(option, "null-output") == 0) ? NULL : buffer, capacity, (strcmp(option, "null-cause") == 0) ? NULL : &cause);
        free(body);
        const char *causeName = ((unsigned int)cause < (sizeof(causeNames) / sizeof(causeNames[0]))) ? causeNames[cause] : "UNWRITTEN";
        printf("%s %s ", harness_resultName(result), causeName);
        harness_print(0, 0, buffer, capacity);
        return 0;
    }
    else if(strcmp(operation, "record-encode") == 0)
    {
        /* Arguments: record-encode base-url capacity physical-id server-id [null-output]; prints every byte up to capacity. */
        if(argumentCount < 6)
        {
            return 2;
        }
        const char *physicalIdentifier = (strcmp(arguments[4], "<null>") == 0) ? NULL : arguments[4];
        const char *serverDeviceId = (strcmp(arguments[5], "<null>") == 0) ? NULL : arguments[5];
        const char *option = (argumentCount > 6) ? arguments[6] : "";
        uint8_t *record = (uint8_t *)buffer;
        result = fhir_encodeRegistrationRecord(input, physicalIdentifier, serverDeviceId, (strcmp(option, "null-output") == 0) ? NULL : record, capacity);
        printf("%s ", harness_resultName(result));
        for(size_t index = 0; index < capacity; index++)
        {
            printf("%02x", record[index]);
        }
        bool canaryIsIntact = true;
        for(size_t index = capacity; index < HARNESS_BUFFER_SIZE; index++)
        {
            canaryIsIntact = canaryIsIntact && (buffer[index] == HARNESS_CANARY);
        }
        printf("%s %d\n", (capacity == 0) ? "-" : "", canaryIsIntact ? 1 : 0);
        return 0;
    }
    else if(strcmp(operation, "record-decode") == 0)
    {
        /* Arguments: record-decode physical-id capacity record-hex base-url [null-record|null-output]. */
        if(argumentCount < 6)
        {
            return 2;
        }
        const char *recordHex = arguments[4];
        const size_t recordSize = (strcmp(recordHex, "-") == 0) ? 0U : strlen(recordHex) / 2U;
        /* Exact-size heap copy, so the sanitizer reports any read past the record. */
        uint8_t *record = malloc((recordSize > 0U) ? recordSize : 1U);
        for(size_t index = 0; index < recordSize; index++)
        {
            char pair[3] = {recordHex[2 * index], recordHex[2 * index + 1], '\0'};
            record[index] = (uint8_t)strtoul(pair, NULL, 16);
        }
        const char *baseUrl = (strcmp(arguments[5], "<null>") == 0) ? NULL : arguments[5];
        const char *option = (argumentCount > 6) ? arguments[6] : "";
        result = fhir_decodeRegistrationRecord((strcmp(option, "null-record") == 0) ? NULL : record, recordSize, baseUrl, input, (strcmp(option, "null-output") == 0) ? NULL : buffer, capacity);
        free(record);
        harness_print(result, (result == 0) ? strlen(buffer) : 0U, buffer, capacity);
        return 0;
    }
    else if(strcmp(operation, "condition-size") == 0)
    {
        printf("%zu %zu\n", (size_t)FHIR_DEVICE_REGISTRATION_CONDITION_SIZE, (size_t)FHIR_OBSERVATION_CONDITION_SIZE);
        return 0;
    }
    else
    {
        return 2;
    }

    harness_print(result, length, buffer, capacity);
    return 0;
}
