/*
 * libFuzzer target for the L1_FHIR registration parsers. The first three input bytes select
 * the HTTP status, the Location length and whether a Location exists; the rest is the
 * Location followed by the response body, and the whole remainder is also decoded as a
 * stored registration record.
 */
#include "../../L1_services/L1_FHIR/fhir.c"

#include <stdlib.h>

static const char fuzz_BaseUrl[] = "https://fhir.example.org/r4";
static const char fuzz_PhysicalIdentifier[] = "stetho-A1B2C3D4E5F6";

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size)
{
    if(size < 3U)
    {
        return 0;
    }
    static const uint16_t statuses[] = {200, 201, 404, 412, 500, 501};
    uint16_t status = statuses[data[0] % (sizeof(statuses) / sizeof(statuses[0]))];
    size_t locationLength = data[1];
    bool hasLocation = (data[2] & 1U) != 0U;
    data += 3;
    size -= 3U;
    if(locationLength > size)
    {
        locationLength = size;
    }
    char *location = malloc(locationLength + 1U);
    if(location == NULL)
    {
        return 0;
    }
    memcpy(location, data, locationLength);
    location[locationLength] = '\0';
    size_t bodyLength = size - locationLength;
    char *body = (bodyLength > 0U) ? malloc(bodyLength) : NULL;
    if(body != NULL)
    {
        memcpy(body, data + locationLength, bodyLength);
    }
    const struct fhir_response response = {
        .status = status,
        .location = hasLocation ? location : NULL,
        .body = body,
        .bodyLength = (body != NULL) ? bodyLength : 0U,
    };
    char serverDeviceId[FHIR_SERVER_DEVICE_ID_SIZE];
    enum fhir_response_cause cause;
    (void)fhir_parseDeviceRegistration(&response, fuzz_BaseUrl, fuzz_PhysicalIdentifier, serverDeviceId, sizeof(serverDeviceId), &cause);
    (void)fhir_decodeRegistrationRecord(data, size, fuzz_BaseUrl, fuzz_PhysicalIdentifier, serverDeviceId, sizeof(serverDeviceId));
    free(body);
    free(location);
    return 0;
}
