/* Host harness for the L1_WIFI HTTP response reader on Zephyr's http_parser.
 * Arguments: <response-file> <piece-size> [finish|read-after-complete]
 * Prints:    <result> <consumed> <status> <has-location> <location-hex|-> <body-length>
 *            <body-overflowed> <keeps-connection> <body-hex|->
 */

#include "../../../L1_services/L1_WIFI/wifi_http.c"

#include <stdio.h>
#include <stdlib.h>

static const char *harness_resultName(int result)
{
    switch(result)
    {
    case 0:
        return "OK";
    case -EAGAIN:
        return "EAGAIN";
    case -EBADMSG:
        return "EBADMSG";
    case -EMSGSIZE:
        return "EMSGSIZE";
    case -ENOSYS:
        return "ENOSYS";
    default:
        return "OTHER";
    }
}

static void harness_printHex(const char *data, size_t length)
{
    if(length == 0)
    {
        printf(" -");
        return;
    }
    printf(" ");
    for(size_t index = 0; index < length; index++)
    {
        printf("%02x", (unsigned char)data[index]);
    }
}

static const char *harness_argument(const char *text)
{
    return (strcmp(text, "<null>") == 0) ? NULL : text;
}

/* Arguments: request-head resource-path condition body-length host port base-path capacity [null-request|null-output|null-length]
 * Prints:    <result> <length> <head-hex|-> <untouched-beyond-capacity> <terminated> */
static int harness_requestHead(int argumentCount, char **arguments)
{
    if(argumentCount < 9)
    {
        return 2;
    }
    static const char body[] = "{}";
    const struct wifi_http_request request = {
        .resourcePath = harness_argument(arguments[2]),
        .condition = harness_argument(arguments[3]),
        .body = body,
        .bodyLength = (size_t)strtoul(arguments[4], NULL, 10),
    };
    static char head[4096];
    memset(head, 0x5A, sizeof(head));
    const size_t capacity = (size_t)strtoul(arguments[8], NULL, 10);
    const char *option = (argumentCount > 9) ? arguments[9] : "";
    size_t length = 12345;
    const int result = wifi_buildHttpRequestHead((strcmp(option, "null-request") == 0) ? NULL : &request,
                                                 harness_argument(arguments[5]),
                                                 (uint16_t)strtoul(arguments[6], NULL, 10),
                                                 harness_argument(arguments[7]),
                                                 (strcmp(option, "null-output") == 0) ? NULL : head,
                                                 capacity,
                                                 (strcmp(option, "null-length") == 0) ? NULL : &length);
    const char *name = (result == 0) ? "OK" : (result == -EINVAL) ? "EINVAL"
                                          : (result == -ENOSPC)   ? "ENOSPC"
                                          : (result == -ENOSYS)   ? "ENOSYS"
                                                                  : "OTHER";
    size_t printed = 0;
    printf("%s %zu ", name, length);
    while((strcmp(option, "null-output") != 0) && (printed < capacity) && (head[printed] != '\0'))
    {
        printf("%02x", (unsigned char)head[printed]);
        printed++;
    }
    if(printed == 0)
    {
        printf("-");
    }
    bool isUntouched = true;
    for(size_t index = capacity; index < sizeof(head); index++)
    {
        isUntouched = isUntouched && (head[index] == 0x5A);
    }
    const bool isTerminated = (capacity == 0) || (strcmp(option, "null-output") == 0) || (memchr(head, '\0', capacity) != NULL);
    printf(" %d %d\n", isUntouched ? 1 : 0, isTerminated ? 1 : 0);
    return 0;
}

int main(int argumentCount, char **arguments)
{
    if((argumentCount > 1) && (strcmp(arguments[1], "request-head") == 0))
    {
        return harness_requestHead(argumentCount, arguments);
    }
    if(argumentCount < 3)
    {
        return 2;
    }
    FILE *file = fopen(arguments[1], "rb");
    if(file == NULL)
    {
        return 2;
    }
    static uint8_t input[1U << 20];
    const size_t inputLength = fread(input, 1, sizeof(input), file);
    fclose(file);
    const size_t pieceSize = (size_t)strtoul(arguments[2], NULL, 10);
    const char *option = (argumentCount > 3) ? arguments[3] : "";

    static struct wifi_http_reader reader;
    static struct wifi_http_response response;
    wifi_beginHttpResponse(&reader, &response);

    int result = -EAGAIN;
    size_t total = 0;
    size_t offset = 0;
    while((result == -EAGAIN) && (offset < inputLength))
    {
        const size_t length = ((inputLength - offset) < pieceSize) ? (inputLength - offset) : pieceSize;
        /* Exact-size heap copy of every piece, so the sanitizer reports reads beyond it. */
        uint8_t *piece = malloc(length);
        memcpy(piece, &input[offset], length);
        size_t consumed = 12345;
        result = wifi_readHttpResponse(&reader, piece, length, &consumed);
        free(piece);
        if(consumed > length)
        {
            return 3;
        }
        total += consumed;
        offset += length;
    }
    if((result == -EAGAIN) && (strcmp(option, "finish") == 0))
    {
        result = wifi_finishHttpResponse(&reader);
    }
    if((result == 0) && (strcmp(option, "read-after-complete") == 0))
    {
        const uint8_t extra[] = "HTTP/1.1 200 OK\r\n";
        size_t consumed = 12345;
        result = wifi_readHttpResponse(&reader, extra, sizeof(extra) - 1U, &consumed);
        total += (consumed == 0U) ? 0U : 1000000U;
    }

    printf("%s %zu %u %d", harness_resultName(result), total, (unsigned)response.status, response.hasLocation ? 1 : 0);
    const size_t locationLength = strnlen(response.location, sizeof(response.location));
    if(locationLength == sizeof(response.location))
    {
        return 4; /* Location without terminator. */
    }
    harness_printHex(response.location, locationLength);
    printf(" %zu %d %d", response.bodyLength, response.bodyHasOverflowed ? 1 : 0, response.keepsConnection ? 1 : 0);
    if(response.bodyLength > sizeof(response.body))
    {
        return 5;
    }
    harness_printHex(response.body, response.bodyLength);
    printf("\n");
    return 0;
}
