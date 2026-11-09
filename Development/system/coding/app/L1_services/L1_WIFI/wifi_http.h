/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L1_WIFI
 * @{
 * @file
 * HTTP/1.1 framing for the FHIR server. Private to L1_WIFI.
 * The request head builder writes the request line and headers of one
 * conditional POST. The bounded response reader, built on Zephyr's
 * incremental http_parser, takes decrypted bytes as they arrive; it keeps the
 * status, the Location header and the body within fixed bounds and stops
 * at the end of the message, so bytes behind it are never taken as the next
 * response. Neither does I/O or keeps global state. The request and response
 * types are part of the WIFI interface in wifi.h.
 */

#ifndef L1_WIFI_HTTP_H
#define L1_WIFI_HTTP_H

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include "wifi.h"

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include <zephyr/net/http/parser.h>

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

#define WIFI_HTTP_HEADER_CAPACITY       (4096U) /**< P27-BUFFERS: aggregate bytes of the status text, header names and values. */
#define WIFI_HTTP_REQUEST_HEAD_CAPACITY (1024U) /**< Request line and headers: 256-byte base path, 253-byte host, longest condition. */

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/** Parser state of one response; owned by the caller for the duration of the response. */
struct wifi_http_reader
{
    struct http_parser parser;           /**< Zephyr parser; parser.data points back to this reader. */
    struct wifi_http_response *response; /**< Caller's response; borrowed for the reader's lifetime. */
    size_t headerBytes;                  /**< Status text, header name and value bytes counted so far. */
    char headerName[sizeof("location")]; /**< Current header name in lowercase while it still fits. */
    size_t headerNameLength;             /**< Bytes of the current header name seen so far, also beyond the buffer. */
    bool isInHeaderValue;                /**< The last header callback delivered value bytes; new name bytes start the next header. */
    bool isReadingLocation;              /**< The current header value belongs to Location. */
    size_t locationLength;               /**< Bytes of the Location value kept; an oversized value fails at once. */
    bool isComplete;                     /**< The whole message was parsed. */
    int failure;                         /**< 0, or the first error a callback reported. */
};

/***********************************************************************/
/* GLOBAL FUNCTION PROTOTYPES                                          */
/***********************************************************************/

/**
 * @brief Write the request line and headers of one conditional POST; the body follows separately.
 *
 * Exactly, in this order:
 *   POST <basePath>/<resourcePath> HTTP/1.1
 *   Host: <host>:<port>
 *   Content-Type: application/fhir+json
 *   Accept: application/fhir+json
 *   Prefer: return=representation
 *   If-None-Exist: <condition>
 *   Content-Length: <bodyLength>
 * each line ended by CRLF, then one empty line.
 *
 * @param[in]  request  Request; resourcePath 1 or more ASCII letters, condition 1 or more visible
 *                      ASCII characters (0x21 to 0x7E), body of 1 or more bytes; borrowed.
 * @param[in]  host     Configured host, 1 or more visible ASCII characters; borrowed.
 * @param[in]  port     Configured port, 1 to 65535.
 * @param[in]  basePath Configured base path, "" or starting with '/', without trailing '/'; borrowed.
 * @param[out] head     Caller buffer; "" on failure when @p capacity > 0.
 * @param[in]  capacity Size of @p head including the terminator.
 * @param[out] length   Bytes written without the terminator; 0 on failure.
 *
 * @return 0, -EINVAL for a NULL pointer or an invalid field (an empty condition included: never
 *         an unconditional POST), or -ENOSPC if the head does not fit. Never a truncated head.
 */
int wifi_buildHttpRequestHead(const struct wifi_http_request *request, const char *host, uint16_t port, const char *basePath, char *head, size_t capacity, size_t *length);

/**
 * @brief Start reading one response into an empty result.
 *
 * @param[out] reader   Reader to initialize.
 * @param[out] response Result to empty; borrowed until the response is complete or abandoned.
 */
void wifi_beginHttpResponse(struct wifi_http_reader *reader, struct wifi_http_response *response);

/**
 * @brief Feed the next received bytes.
 *
 * @param[in,out] reader   Reader started with wifi_beginHttpResponse().
 * @param[in]     data     Received bytes; borrowed for the call only.
 * @param[in]     length   Number of bytes in @p data.
 * @param[out]    consumed Bytes of @p data that belong to this response.
 *
 * @return -EAGAIN when all bytes were consumed and the response is still incomplete;
 *         0 when the response is complete (bytes behind it clear keepsConnection);
 *         -EMSGSIZE when the status text and headers exceed WIFI_HTTP_HEADER_CAPACITY
 *         or Location exceeds WIFI_HTTP_LOCATION_SIZE; -EBADMSG for malformed HTTP,
 *         a repeated Location header, or a call after the response ended or failed.
 */
int wifi_readHttpResponse(struct wifi_http_reader *reader, const uint8_t *data, size_t length, size_t *consumed);

/**
 * @brief Report that the server closed the connection.
 *
 * A response delimited by connection close becomes complete here; any other
 * unfinished response is truncated.
 *
 * @param[in,out] reader Reader started with wifi_beginHttpResponse().
 *
 * @return 0 when the response is complete, or -EBADMSG for a truncated or failed response.
 */
int wifi_finishHttpResponse(struct wifi_http_reader *reader);

#endif /* L1_WIFI_HTTP_H */

/** @} */
