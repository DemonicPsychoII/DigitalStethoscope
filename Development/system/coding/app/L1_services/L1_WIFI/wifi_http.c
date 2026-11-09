/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L1_WIFI
 * @{
 * @file
 * Bounded HTTP/1.1 response reader on Zephyr's http_parser.
 */

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include "wifi_http.h"

#include <ctype.h>
#include <errno.h>
#include <string.h>

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

#define WIFI_HTTP_LOCATION_NAME           "location" /**< Lowercase name of the Location header. */
#define WIFI_HTTP_FIRST_VISIBLE_CHARACTER ('!')      /**< 0x21: visible ASCII starts after the space. */
#define WIFI_HTTP_LAST_VISIBLE_CHARACTER  ('~')      /**< 0x7E: DEL and above are not visible ASCII. */
#define WIFI_HTTP_DECIMAL_DIGITS_MAX      (20U)      /**< Decimal digits of the largest 64-bit size_t. */

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/** Bounded writer of the request head; after the first overflow every append is ignored. */
struct wifi_http_writer
{
    char *buffer;       /**< Caller buffer; borrowed for the writer's lifetime. */
    size_t capacity;    /**< Size of buffer including room for the terminator. */
    size_t length;      /**< Bytes written so far, without the terminator. */
    bool hasOverflowed; /**< An append did not fit; the head is invalid. */
};

/***********************************************************************/
/* LOCAL FUNCTION PROTOTYPES                                           */
/***********************************************************************/

/**
 * @brief Count the reason phrase of the status line against the header capacity.
 *
 * @param[in] parser Parser whose data member is the reader.
 * @param[in] at     Next bytes of the reason phrase; not terminated.
 * @param[in] length Number of bytes at @p at.
 *
 * @return 0 to continue, or nonzero after storing the failure in the reader.
 */
static int wifi_onHttpStatus(struct http_parser *parser, const char *at, size_t length);

/**
 * @brief Collect the next bytes of a header name; a name may arrive in several pieces.
 *
 * @param[in] parser Parser whose data member is the reader.
 * @param[in] at     Next bytes of the name; not terminated.
 * @param[in] length Number of bytes at @p at.
 *
 * @return 0 to continue, or nonzero after storing the failure in the reader.
 */
static int wifi_onHttpHeaderField(struct http_parser *parser, const char *at, size_t length);

/**
 * @brief Collect the next bytes of a header value; keep it only for Location.
 *
 * @param[in] parser Parser whose data member is the reader.
 * @param[in] at     Next bytes of the value; not terminated.
 * @param[in] length Number of bytes at @p at.
 *
 * @return 0 to continue, or nonzero after storing the failure in the reader.
 */
static int wifi_onHttpHeaderValue(struct http_parser *parser, const char *at, size_t length);

/**
 * @brief Copy the next decoded body bytes while they fit; mark the overflow otherwise.
 *
 * @param[in] parser Parser whose data member is the reader.
 * @param[in] at     Next body bytes, with chunked framing already removed; not terminated.
 * @param[in] length Number of bytes at @p at.
 *
 * @return 0; an oversized body is drained, not rejected.
 */
static int wifi_onHttpBody(struct http_parser *parser, const char *at, size_t length);

/**
 * @brief Record status and connection reuse, and stop the parser at the end of the message.
 *
 * @param[in] parser Parser whose data member is the reader.
 *
 * @return 0.
 */
static int wifi_onHttpMessageComplete(struct http_parser *parser);

/**
 * @brief Add status text, header name or value bytes to the aggregate header count.
 *
 * @param[in,out] reader Reader of the current response.
 * @param[in]     length Number of new bytes.
 *
 * @return 0 while the count stays within WIFI_HTTP_HEADER_CAPACITY, or nonzero after storing -EMSGSIZE.
 */
static int wifi_countHttpHeaderBytes(struct wifi_http_reader *reader, size_t length);

/**
 * @brief Store the first failure of a response and tell the parser to stop.
 *
 * @param[in,out] reader  Reader of the current response.
 * @param[in]     failure Negative error code; an earlier failure is kept.
 *
 * @return Nonzero, the value that aborts http_parser_execute().
 */
static int wifi_rejectHttpResponse(struct wifi_http_reader *reader, int failure);

/**
 * @brief Append text to the head while it fits with its terminator.
 *
 * @param[in,out] writer Head writer.
 * @param[in]     text   NUL-terminated text; borrowed for the call only.
 */
static void wifi_appendHttpText(struct wifi_http_writer *writer, const char *text);

/**
 * @brief Append an unsigned value in decimal without leading zeros.
 *
 * @param[in,out] writer Head writer.
 * @param[in]     value  Value to write.
 */
static void wifi_appendHttpUnsigned(struct wifi_http_writer *writer, size_t value);

/**
 * @brief Tell whether text is nonempty visible ASCII, 0x21 to 0x7E.
 *
 * @param[in] text NUL-terminated text; may be NULL.
 *
 * @return True for 1 or more visible ASCII characters.
 */
static bool wifi_isVisibleHttpText(const char *text);

/**
 * @brief Tell whether text is a resource type relative to the base path.
 *
 * @param[in] text NUL-terminated text; may be NULL.
 *
 * @return True for 1 or more ASCII letters.
 */
static bool wifi_isHttpResourcePath(const char *text);

/**
 * @brief Tell whether text is a usable base path.
 *
 * @param[in] text NUL-terminated text; may be NULL.
 *
 * @return True for "" or a path that starts with '/' and does not end with '/'.
 */
static bool wifi_isHttpBasePath(const char *text);

/***********************************************************************/
/* LOCAL CONSTANTS                                                     */
/***********************************************************************/

/** Callbacks shared by every reader; the per-response state lives in the reader. */
static const struct http_parser_settings wifi_HttpSettings = {
    .on_status = wifi_onHttpStatus,
    .on_header_field = wifi_onHttpHeaderField,
    .on_header_value = wifi_onHttpHeaderValue,
    .on_body = wifi_onHttpBody,
    .on_message_complete = wifi_onHttpMessageComplete,
};

/***********************************************************************/
/* GLOBAL FUNCTIONS                                                    */
/***********************************************************************/

int wifi_buildHttpRequestHead(const struct wifi_http_request *request, const char *host, uint16_t port, const char *basePath, char *head, size_t capacity, size_t *length)
{
    struct wifi_http_writer writer = {.buffer = head, .capacity = capacity, .length = 0U, .hasOverflowed = (capacity == 0U)};
    int result = -EINVAL;

    if((head != NULL) && (capacity > 0U))
    {
        head[0] = '\0';
    }

    if(length != NULL)
    {
        *length = 0U;
    }

    /* Visible ASCII only keeps CR and LF out of the head, so no header can be injected. */
    if((request != NULL) && (head != NULL) && (length != NULL) && (port > 0U) && (request->body != NULL) && (request->bodyLength > 0U) && wifi_isHttpResourcePath(request->resourcePath) && wifi_isVisibleHttpText(request->condition) && wifi_isVisibleHttpText(host) && wifi_isHttpBasePath(basePath))
    {
        wifi_appendHttpText(&writer, "POST ");
        wifi_appendHttpText(&writer, basePath);
        wifi_appendHttpText(&writer, "/");
        wifi_appendHttpText(&writer, request->resourcePath);
        wifi_appendHttpText(&writer, " HTTP/1.1\r\nHost: ");
        wifi_appendHttpText(&writer, host);
        wifi_appendHttpText(&writer, ":");
        wifi_appendHttpUnsigned(&writer, port);
        wifi_appendHttpText(&writer, "\r\nContent-Type: application/fhir+json\r\nAccept: application/fhir+json\r\nPrefer: return=representation\r\nIf-None-Exist: ");
        wifi_appendHttpText(&writer, request->condition);
        wifi_appendHttpText(&writer, "\r\nContent-Length: ");
        wifi_appendHttpUnsigned(&writer, request->bodyLength);
        wifi_appendHttpText(&writer, "\r\n\r\n");

        if(writer.hasOverflowed)
        {
            /* Never a truncated head. */
            if(capacity > 0U)
            {
                head[0] = '\0';
            }

            result = -ENOSPC;
        }
        else
        {
            *length = writer.length;
            result = 0;
        }
    }

    return result;
}

void wifi_beginHttpResponse(struct wifi_http_reader *reader, struct wifi_http_response *response)
{
    (void)memset(reader, 0, sizeof(*reader));
    (void)memset(response, 0, sizeof(*response));

    http_parser_init(&reader->parser, HTTP_RESPONSE);

    reader->parser.data = reader;
    reader->response = response;
}

int wifi_readHttpResponse(struct wifi_http_reader *reader, const uint8_t *data, size_t length, size_t *consumed)
{
    int result = -EAGAIN;

    *consumed = 0U;

    if(reader->isComplete || (reader->failure != 0))
    {
        result = -EBADMSG;
    }
    else
    {
        *consumed = http_parser_execute(&reader->parser, &wifi_HttpSettings, (const char *)data, length);

        if(reader->failure != 0)
        {
            result = reader->failure;
        }
        else if(reader->isComplete)
        {
            /* Bytes behind the message are no response of ours, so the connection is not reused. */
            if(*consumed < length)
            {
                reader->response->keepsConnection = false;
            }

            result = 0;
        }
        else if(HTTP_PARSER_ERRNO(&reader->parser) != HPE_OK)
        {
            reader->failure = -EBADMSG;
            result = -EBADMSG;
        }
        else
        {
            /* All bytes parsed, the message continues in the next piece. */
        }
    }

    return result;
}

int wifi_finishHttpResponse(struct wifi_http_reader *reader)
{
    int result = -EBADMSG;

    if(reader->isComplete)
    {
        result = 0;
    }
    else if(reader->failure == 0)
    {
        /* Zero bytes tell the parser that the connection closed. */
        (void)http_parser_execute(&reader->parser, &wifi_HttpSettings, NULL, 0U);

        if(reader->isComplete)
        {
            result = 0;
        }
        else
        {
            reader->failure = -EBADMSG;
        }
    }
    else
    {
        /* The response already failed. */
    }

    /* The server closed the connection, so it cannot carry the next request. */
    reader->response->keepsConnection = false;

    return result;
}

/***********************************************************************/
/* LOCAL FUNCTIONS                                                     */
/***********************************************************************/

static int wifi_onHttpStatus(struct http_parser *parser, const char *at, size_t length)
{
    (void)at;

    return wifi_countHttpHeaderBytes(parser->data, length);
}

static int wifi_onHttpHeaderField(struct http_parser *parser, const char *at, size_t length)
{
    struct wifi_http_reader *reader = parser->data;
    int result = wifi_countHttpHeaderBytes(reader, length);

    /* A name piece after value pieces starts the next header. */
    if((result == 0) && reader->isInHeaderValue)
    {
        reader->isInHeaderValue = false;
        reader->isReadingLocation = false;
        reader->headerNameLength = 0U;
    }

    for(size_t index = 0U; (result == 0) && (index < length); index++)
    {
        /* Header names compare case-insensitively (RFC 9110 section 5.1). */
        if(reader->headerNameLength < sizeof(reader->headerName))
        {
            reader->headerName[reader->headerNameLength] = (char)tolower((unsigned char)at[index]);
        }

        reader->headerNameLength++;
    }

    return result;
}

static int wifi_onHttpHeaderValue(struct http_parser *parser, const char *at, size_t length)
{
    struct wifi_http_reader *reader = parser->data;
    struct wifi_http_response *response = reader->response;
    int result = wifi_countHttpHeaderBytes(reader, length);

    if((result == 0) && !reader->isInHeaderValue)
    {
        reader->isInHeaderValue = true;
        reader->isReadingLocation = ((reader->headerNameLength == (sizeof(WIFI_HTTP_LOCATION_NAME) - 1U)) && (memcmp(reader->headerName, WIFI_HTTP_LOCATION_NAME, sizeof(WIFI_HTTP_LOCATION_NAME) - 1U) == 0));

        if(reader->isReadingLocation && response->hasLocation)
        {
            result = wifi_rejectHttpResponse(reader, -EBADMSG);
        }
        else if(reader->isReadingLocation)
        {
            response->hasLocation = true;
        }
        else
        {
            /* Other headers are counted, not kept. */
        }
    }

    if((result == 0) && reader->isReadingLocation)
    {
        /* The value must fit with its terminator; a longer one is rejected, never truncated. */
        if(length < (sizeof(response->location) - reader->locationLength))
        {
            (void)memcpy(&response->location[reader->locationLength], at, length);

            reader->locationLength += length;
            response->location[reader->locationLength] = '\0';
        }
        else
        {
            result = wifi_rejectHttpResponse(reader, -EMSGSIZE);
        }
    }

    return result;
}

static int wifi_onHttpBody(struct http_parser *parser, const char *at, size_t length)
{
    struct wifi_http_reader *reader = parser->data;
    struct wifi_http_response *response = reader->response;

    if(!response->bodyHasOverflowed && (length <= (sizeof(response->body) - response->bodyLength)))
    {
        (void)memcpy(&response->body[response->bodyLength], at, length);

        response->bodyLength += length;
    }
    else
    {
        /* Keep draining so the message still ends where the server framed it. */
        response->bodyHasOverflowed = true;
    }

    return 0;
}

static int wifi_onHttpMessageComplete(struct http_parser *parser)
{
    struct wifi_http_reader *reader = parser->data;
    struct wifi_http_response *response = reader->response;

    reader->isComplete = true;
    response->status = (uint16_t)parser->status_code;
    response->keepsConnection = ((http_should_keep_alive(parser) != 0) && !response->bodyHasOverflowed);

    /* Stop exactly here, so bytes behind the message stay unparsed. */
    http_parser_pause(parser, 1);

    return 0;
}

static int wifi_countHttpHeaderBytes(struct wifi_http_reader *reader, size_t length)
{
    int result = 0;

    if(length > (WIFI_HTTP_HEADER_CAPACITY - reader->headerBytes))
    {
        result = wifi_rejectHttpResponse(reader, -EMSGSIZE);
    }
    else
    {
        reader->headerBytes += length;
    }

    return result;
}

static int wifi_rejectHttpResponse(struct wifi_http_reader *reader, int failure)
{
    if(reader->failure == 0)
    {
        reader->failure = failure;
    }

    return 1;
}

static void wifi_appendHttpText(struct wifi_http_writer *writer, const char *text)
{
    if(!writer->hasOverflowed)
    {
        const size_t textLength = strlen(text);

        /* length < capacity holds while nothing overflowed, so the subtraction cannot wrap. */
        if(textLength < (writer->capacity - writer->length))
        {
            (void)memcpy(&writer->buffer[writer->length], text, textLength + 1U);

            writer->length += textLength;
        }
        else
        {
            writer->hasOverflowed = true;
        }
    }
}

static void wifi_appendHttpUnsigned(struct wifi_http_writer *writer, size_t value)
{
    char digits[WIFI_HTTP_DECIMAL_DIGITS_MAX + 1U];
    size_t start = WIFI_HTTP_DECIMAL_DIGITS_MAX;
    size_t remaining = value;

    digits[WIFI_HTTP_DECIMAL_DIGITS_MAX] = '\0';

    do
    {
        start--;
        digits[start] = (char)('0' + (remaining % 10U));
        remaining /= 10U;
    } while(remaining > 0U);

    wifi_appendHttpText(writer, &digits[start]);
}

static bool wifi_isVisibleHttpText(const char *text)
{
    bool isVisible = ((text != NULL) && (text[0] != '\0'));

    for(const char *character = text; isVisible && (*character != '\0'); character++)
    {
        isVisible = ((*character >= WIFI_HTTP_FIRST_VISIBLE_CHARACTER) && (*character <= WIFI_HTTP_LAST_VISIBLE_CHARACTER));
    }

    return isVisible;
}

static bool wifi_isHttpResourcePath(const char *text)
{
    bool isLetters = ((text != NULL) && (text[0] != '\0'));

    for(const char *character = text; isLetters && (*character != '\0'); character++)
    {
        isLetters = (((*character >= 'A') && (*character <= 'Z')) || ((*character >= 'a') && (*character <= 'z')));
    }

    return isLetters;
}

static bool wifi_isHttpBasePath(const char *text)
{
    bool isValid = (text != NULL);

    if(isValid && (text[0] != '\0'))
    {
        const size_t textLength = strlen(text);

        isValid = ((text[0] == '/') && (text[textLength - 1U] != '/'));
    }

    return isValid;
}

/** @} */
