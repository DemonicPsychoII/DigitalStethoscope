/*
 * libFuzzer target for the L1_WIFI HTTP response reader. The first input byte sets the size
 * of the pieces in which the rest arrives, as a socket delivers a response in reads of
 * varying length.
 */
#include "../../L1_services/L1_WIFI/wifi_http.c"

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size)
{
    if(size < 1U)
    {
        return 0;
    }
    size_t pieceSize = (size_t)data[0] + 1U;
    data++;
    size--;
    struct wifi_http_reader reader;
    struct wifi_http_response response;
    memset(&response, 0, sizeof(response));
    wifi_beginHttpResponse(&reader, &response);
    int result = -EAGAIN;
    while((result == -EAGAIN) && (size > 0U))
    {
        size_t length = (size < pieceSize) ? size : pieceSize;
        size_t consumed = 0U;
        result = wifi_readHttpResponse(&reader, data, length, &consumed);
        if(consumed > length)
        {
            __builtin_trap();
        }
        data += length;
        size -= length;
    }
    if(result == -EAGAIN)
    {
        (void)wifi_finishHttpResponse(&reader);
    }
    return 0;
}
