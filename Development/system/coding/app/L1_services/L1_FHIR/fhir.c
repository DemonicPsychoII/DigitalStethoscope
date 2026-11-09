/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L1_FHIR
 * @{
 * @file
 * Implementation of the FHIR module: bounded FHIR R4 JSON serialization
 * (design/COMMUNICATION/server-communication.md).
 */

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include "fhir.h"

#include <errno.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

#define FHIR_LATEST_UTC_SECONDS      (253402300799U) /**< 9999-12-31T23:59:59Z, the last second with a four-digit year. */
#define FHIR_MILLISECONDS_PER_SECOND (1000U)
#define FHIR_SECONDS_PER_DAY         (86400U)
#define FHIR_SECONDS_PER_HOUR        (3600U)
#define FHIR_SECONDS_PER_MINUTE      (60U)
#define FHIR_UNSIGNED_DECIMAL_DIGITS (10U) /**< Decimal digits of the largest uint32_t, 4294967295. */

/** Observation.category: vital signs. */
#define FHIR_VITAL_SIGNS_CATEGORY_JSON "[{\"coding\":[{\"system\":\"http://terminology.hl7.org/CodeSystem/observation-category\",\"code\":\"vital-signs\"}]}]"

/** Observation.code: LOINC 8867-4, heart rate. */
#define FHIR_HEART_RATE_CODE_JSON "{\"coding\":[{\"system\":\"http://loinc.org\",\"code\":\"8867-4\"}]}"

/** valueQuantity members after the value: UCUM beats per minute. */
#define FHIR_HEART_RATE_UNIT_JSON "\"unit\":\"/min\",\"system\":\"http://unitsofmeasure.org\",\"code\":\"/min\""

/** Observation.dataAbsentReason for a poor signal (REQ-08). */
#define FHIR_ERROR_ABSENT_REASON_JSON "{\"coding\":[{\"system\":\"http://terminology.hl7.org/CodeSystem/data-absent-reason\",\"code\":\"error\"}]}"

#define FHIR_HTTP_200_OK                  (200U)
#define FHIR_HTTP_201_CREATED             (201U)
#define FHIR_HTTP_412_PRECONDITION_FAILED (412U) /**< Conditional create matched more than one resource. */
#define FHIR_HTTP_501_NOT_IMPLEMENTED     (501U) /**< Server does not support conditional create. */
#define FHIR_HTTP_SERVER_ERROR_FIRST      (500U) /**< First status of the 5xx server error class. */
#define FHIR_HTTP_SERVER_ERROR_LAST       (599U) /**< Last status of the 5xx server error class. */

#define FHIR_JSON_DEPTH_MAX                 (16U)   /**< Nesting limit of skipped response values; size of the bracket stack. */
#define FHIR_JSON_FIRST_UNESCAPED_CHARACTER (0x20U) /**< RFC 8259 section 7: U+0000 to U+001F only appear escaped in a string. */
#define FHIR_JSON_UNICODE_ESCAPE_DIGITS     (4U)    /**< Hex digits of a JSON unicode escape. */

#define FHIR_RECORD_VERSION_OFFSET             (0U) /**< P27-RECORD: byte offsets of the version-1 fields. */
#define FHIR_RECORD_BASE_URL_OFFSET            (1U)
#define FHIR_RECORD_PHYSICAL_IDENTIFIER_OFFSET (FHIR_RECORD_BASE_URL_OFFSET + FHIR_BASE_URL_SIZE)
#define FHIR_RECORD_SERVER_DEVICE_ID_OFFSET    (FHIR_RECORD_PHYSICAL_IDENTIFIER_OFFSET + FHIR_PHYSICAL_IDENTIFIER_SIZE)

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/**
 * Bounded writer over a caller buffer. After the first overflow every append
 * is ignored, so a builder appends all parts and checks once at the end.
 */
struct fhir_writer
{
    char *buffer;       /**< Caller buffer; borrowed for the writer's lifetime. */
    size_t capacity;    /**< Size of @c buffer including room for the terminator. */
    size_t length;      /**< Bytes written so far, without the terminator. */
    bool hasOverflowed; /**< An append did not fit; the content is invalid. */
};

/** Read position in a bounded, not necessarily terminated JSON text. */
struct fhir_json_scanner
{
    const char *text; /**< Response body; borrowed for the scanner's lifetime. */
    size_t length;    /**< Bytes in @c text. */
    size_t position;  /**< Next byte to read; never beyond @c length. */
};

/***********************************************************************/
/* GLOBAL CONSTANTS                                                    */
/***********************************************************************/

/***********************************************************************/
/* LOCAL CONSTANTS                                                     */
/***********************************************************************/

static const char fhir_HexDigits[] = "0123456789ABCDEF";

/***********************************************************************/
/* GLOBAL VARIABLES                                                    */
/***********************************************************************/

/***********************************************************************/
/* LOCAL VARIABLES                                                     */
/***********************************************************************/

/***********************************************************************/
/* LOCAL FUNCTION PROTOTYPES                                           */
/***********************************************************************/

/**
 * @brief Empty the caller's output and tell whether both output pointers are given.
 *
 * @param[out] output   Caller buffer, emptied when it has room for the terminator; may be NULL.
 * @param[in]  capacity Size of @p output in bytes.
 * @param[out] length   Set to 0; may be NULL.
 *
 * @return True if @p output and @p length are not NULL.
 */
static bool fhir_prepareOutput(char *output, size_t capacity, size_t *length);

/**
 * @brief Start an empty writer over a caller buffer.
 *
 * @param[out] writer   Writer to initialize.
 * @param[in]  buffer   Caller buffer; borrowed until fhir_finishWriter().
 * @param[in]  capacity Size of @p buffer in bytes, including room for the terminator.
 */
static void fhir_beginWriter(struct fhir_writer *writer, char *buffer, size_t capacity);

/**
 * @brief Append text verbatim; for JSON syntax and constants that need no escaping.
 *
 * Ignored after an overflow. Text that does not fit completely marks the overflow.
 *
 * @param[in,out] writer Writer to append to.
 * @param[in]     text   NUL-terminated text.
 */
static void fhir_appendText(struct fhir_writer *writer, const char *text);

/**
 * @brief Append text as a quoted JSON string, escaped per RFC 8259 section 7.
 *
 * @param[in,out] writer Writer to append to.
 * @param[in]     text   NUL-terminated text; UTF-8 bytes pass through unchanged.
 */
static void fhir_appendJsonString(struct fhir_writer *writer, const char *text);

/**
 * @brief Terminate the content, or empty the buffer after an overflow.
 *
 * @param[in,out] writer Writer to finish; its buffer is no longer borrowed afterwards.
 * @param[out]    length Content length without the terminator, 0 after an overflow.
 *
 * @return 0, or -ENOSPC after an overflow, with no partial content left.
 */
static int fhir_finishWriter(struct fhir_writer *writer, size_t *length);

/**
 * @brief Tell whether an identity is "stetho-" plus exactly 12 uppercase hex digits.
 *
 * @param[in] physicalIdentifier NUL-terminated identity; may be NULL.
 *
 * @return True for the P27-IDENTITY format; false otherwise, including lowercase hex.
 */
static bool fhir_isValidPhysicalIdentifier(const char *physicalIdentifier);

/**
 * @brief Tell whether a logical server Device id matches FHIR R4 id.
 *
 * @param[in] serverDeviceId NUL-terminated id; may be NULL.
 *
 * @return True for 1 to FHIR_SERVER_DEVICE_ID_MAX_LENGTH characters of A-Z, a-z, 0-9, '-' and '.'.
 */
static bool fhir_isValidServerDeviceId(const char *serverDeviceId);

/**
 * @brief Tell whether the fields that form the measurement identity are valid.
 *
 * @param[in] observation Frozen content; may be NULL.
 *
 * @return True for a valid server Device id, milliseconds 0-999 and an end no later than year 9999.
 */
static bool fhir_hasValidMeasurementIdentity(const struct fhir_observation *observation);

/**
 * @brief Tell whether a complete Observation may be serialized.
 *
 * @param[in] observation Frozen content; may be NULL.
 *
 * @return True for a valid identity, a NULL or nonempty patient reference, a known kind and,
 *         for HEART_RATE, a value above 0 with supported decimal places.
 */
static bool fhir_isValidObservation(const struct fhir_observation *observation);

/**
 * @brief Append an unsigned value in decimal, padded with leading zeros.
 *
 * @param[in,out] writer        Writer to append to.
 * @param[in]     value         Value to write.
 * @param[in]     minimumDigits Digits written at least, up to FHIR_UNSIGNED_DECIMAL_DIGITS.
 */
static void fhir_appendUnsigned(struct fhir_writer *writer, uint32_t value, uint8_t minimumDigits);

/**
 * @brief Append a UTC time as YYYY-MM-DDTHH:mm:ss.SSSZ, without quotes.
 *
 * @param[in,out] writer       Writer to append to.
 * @param[in]     utcSeconds   Seconds since 1970-01-01T00:00:00Z; already checked against year 9999.
 * @param[in]     milliseconds Millisecond part, 0-999.
 */
static void fhir_appendUtcTime(struct fhir_writer *writer, uint64_t utcSeconds, uint16_t milliseconds);

/**
 * @brief Append a fixed-point value as a JSON number with exactly the declared decimal places.
 *
 * For example 725 with 1 place gives 72.5, 7250 with 2 places 72.50 and 5 with 2 places 0.05.
 *
 * @param[in,out] writer        Writer to append to.
 * @param[in]     scaled        Value times 10^decimalPlaces.
 * @param[in]     decimalPlaces 0 to FHIR_HEART_RATE_DECIMAL_PLACES_MAX; 0 writes an integer without a point.
 */
static void fhir_appendScaledDecimal(struct fhir_writer *writer, uint32_t scaled, uint8_t decimalPlaces);

/**
 * @brief Append the measurement identifier <serverDeviceId>:<UTC end>, without quotes.
 *
 * @param[in,out] writer      Writer to append to.
 * @param[in]     observation Content with an already validated identity.
 */
static void fhir_appendMeasurementIdentifier(struct fhir_writer *writer, const struct fhir_observation *observation);

/**
 * @brief Append text percent-encoded for a URI query value (RFC 3986 section 2.1).
 *
 * Unreserved characters A-Z, a-z, 0-9, '-', '.', '_' and '~' pass unchanged;
 * every other byte becomes %XX with uppercase hex digits.
 *
 * @param[in,out] writer Writer to append to.
 * @param[in]     text   NUL-terminated text.
 */
static void fhir_appendPercentEncoded(struct fhir_writer *writer, const char *text);

/**
 * @brief Take the logical id from a Location header with the expected base path and Device type.
 *
 * Accepts exactly <scheme>://<authority><base path>/Device/<id>, optionally followed by
 * /_history/<version>. The authority is not compared: HAPI writes its configured server
 * address there, and the pinned TLS certificate already authenticates the server.
 *
 * @param[in]  location       NUL-terminated header value.
 * @param[in]  baseUrl        Canonical base URL; its scheme compares case-insensitively and its
 *                            base path exactly. The Location authority must be nonempty without '?' or '#'.
 * @param[out] serverDeviceId Destination of at least FHIR_SERVER_DEVICE_ID_SIZE bytes; written only on success.
 *
 * @return True with a valid FHIR id; false for another scheme, base path or resource type, an empty
 *         authority, a malformed id or version.
 */
static bool fhir_parseDeviceLocation(const char *location, const char *baseUrl, char *serverDeviceId);

/**
 * @brief Tell whether text starts with a prefix, ignoring ASCII letter case.
 *
 * strncasecmp is POSIX, not C11, so L1 compares by itself.
 *
 * @param[in] text         NUL-terminated text.
 * @param[in] prefix       Expected prefix; at least @p prefixLength bytes.
 * @param[in] prefixLength Bytes of @p prefix to compare.
 *
 * @return True if the first @p prefixLength bytes are equal apart from letter case.
 */
static bool fhir_startsWithIgnoringCase(const char *text, const char *prefix, size_t prefixLength);

/**
 * @brief Read the Device representation: resourceType, optional id and identifiers.
 *
 * @param[in]  body               Response body; not terminated.
 * @param[in]  bodyLength         Bytes in @p body, above 0.
 * @param[in]  physicalIdentifier Identifier value that an identifier array must contain.
 * @param[out] serverDeviceId     Destination of at least FHIR_SERVER_DEVICE_ID_SIZE bytes; "" when the body has no id.
 *
 * @return True for one JSON object of resourceType Device with a valid or absent id and,
 *         when present, an identifier array containing this device; false otherwise.
 */
static bool fhir_parseDeviceRepresentation(const char *body, size_t bodyLength, const char *physicalIdentifier, char *serverDeviceId);

/**
 * @brief Read an identifier array and tell whether it holds this device's identifier.
 *
 * @param[in,out] scanner                    Positioned at '['; afterwards behind ']'.
 * @param[in]     physicalIdentifier         Expected value with system FHIR_DEVICE_IDENTIFIER_SYSTEM.
 * @param[out]    containsPhysicalIdentifier True if one element matches both system and value.
 *
 * @return 0, or -EBADMSG for malformed JSON.
 */
static int fhir_parseJsonIdentifiers(struct fhir_json_scanner *scanner, const char *physicalIdentifier, bool *containsPhysicalIdentifier);

/**
 * @brief Read one identifier object; its system and value are captured, other members skipped.
 *
 * A system or value too long for this device's identifier cannot match and counts as skipped.
 *
 * @param[in,out] scanner              Positioned at '{'; afterwards behind '}'.
 * @param[in]     physicalIdentifier   Expected value with system FHIR_DEVICE_IDENTIFIER_SYSTEM.
 * @param[out]    isPhysicalIdentifier True if both system and value match.
 *
 * @return 0, or -EBADMSG for malformed JSON.
 */
static int fhir_parseJsonIdentifier(struct fhir_json_scanner *scanner, const char *physicalIdentifier, bool *isPhysicalIdentifier);

/**
 * @brief Read one JSON string (RFC 8259 section 7).
 *
 * With a destination, the string is captured and must contain no escape (fail closed:
 * valid servers have no reason to escape the plain ASCII values read here).
 * Without one it is skipped; escapes are then only checked for well-formedness.
 * Unescaped bytes below 0x20 are malformed in either mode.
 *
 * @param[in,out] scanner     Positioned at the opening quote, after optional whitespace; afterwards behind the closing quote.
 * @param[out]    destination NUL-terminated copy, or NULL to skip.
 * @param[in]     capacity    Size of @p destination; ignored when it is NULL.
 *
 * @return 0, -ENOSPC if the string does not fit @p destination, or -EBADMSG.
 */
static int fhir_readJsonString(struct fhir_json_scanner *scanner, char *destination, size_t capacity);

/**
 * @brief Check one escape sequence of a skipped string.
 *
 * @param[in,out] scanner Positioned behind the backslash; afterwards behind the sequence.
 *
 * @return 0 for one of \" \\ \/ \b \f \n \r \t or \u with four hex digits, otherwise -EBADMSG.
 */
static int fhir_skipJsonEscape(struct fhir_json_scanner *scanner);

/**
 * @brief Read an object member name and the colon behind it.
 *
 * @param[in,out] scanner  Positioned at the name; afterwards behind the colon.
 * @param[out]    name     NUL-terminated name, or NULL to skip it.
 * @param[in]     capacity Size of @p name; ignored when it is NULL.
 *
 * @return 0, -ENOSPC for a well-formed name that does not fit, or -EBADMSG.
 */
static int fhir_readJsonMemberName(struct fhir_json_scanner *scanner, char *name, size_t capacity);

/**
 * @brief Read the comma or closing bracket behind an object member or array element.
 *
 * @param[in,out] scanner  Scanner to advance.
 * @param[in]     closing  '}' or ']'.
 * @param[out]    isClosed True if @p closing was read, false after a comma.
 *
 * @return 0, or -EBADMSG if neither follows.
 */
static int fhir_readJsonSeparator(struct fhir_json_scanner *scanner, char closing, bool *isClosed);

/**
 * @brief Skip one JSON value of any type.
 *
 * Iterates over a bracket stack instead of recursing (MISRA C:2012 Rule 17.2), so the
 * stack use stays fixed whatever the server sends.
 *
 * @param[in,out] scanner Positioned at the value, after optional whitespace; afterwards behind it.
 *
 * @return 0, or -EBADMSG for malformed JSON or nesting deeper than FHIR_JSON_DEPTH_MAX.
 */
static int fhir_skipJsonValue(struct fhir_json_scanner *scanner);

/**
 * @brief Skip one string, literal or number.
 *
 * Numbers are accepted as a nonempty run of digits, '-', '+', '.', 'e' and 'E'; their
 * value is never used.
 *
 * @param[in,out] scanner Positioned at the first byte of the value; afterwards behind it.
 *
 * @return 0, or -EBADMSG.
 */
static int fhir_skipJsonScalar(struct fhir_json_scanner *scanner);

/**
 * @brief Skip JSON whitespace: space, tab, line feed and carriage return.
 *
 * @param[in,out] scanner Scanner to advance.
 */
static void fhir_skipJsonWhitespace(struct fhir_json_scanner *scanner);

/**
 * @brief Skip whitespace, then consume one expected structural character.
 *
 * @param[in,out] scanner  Scanner to advance; unchanged past the whitespace on mismatch.
 * @param[in]     expected Character such as '{', ':', ',' or ']'.
 *
 * @return True if @p expected was consumed.
 */
static bool fhir_consumeJsonCharacter(struct fhir_json_scanner *scanner, char expected);

/**
 * @brief Tell whether one text field of a stored record is NUL-terminated and zero-padded.
 *
 * A valid field can then be read in place as a C string.
 *
 * @param[in] field     First byte of the field inside the record.
 * @param[in] fieldSize Size of the field, including room for the terminator.
 *
 * @return True if the field holds a terminator and every byte behind the first one is zero.
 */
static bool fhir_isValidRecordField(const uint8_t *field, size_t fieldSize);

/***********************************************************************/
/* GLOBAL FUNCTIONS                                                    */
/***********************************************************************/

int fhir_buildDeviceRegistration(const char *physicalIdentifier, char *body, size_t capacity, size_t *length)
{
    struct fhir_writer writer;
    int result = -EINVAL;

    if(fhir_prepareOutput(body, capacity, length) && fhir_isValidPhysicalIdentifier(physicalIdentifier))
    {
        fhir_beginWriter(&writer, body, capacity);
        fhir_appendText(&writer, "{\"resourceType\":\"Device\",\"identifier\":[{\"system\":");
        fhir_appendJsonString(&writer, FHIR_DEVICE_IDENTIFIER_SYSTEM);
        fhir_appendText(&writer, ",\"value\":");
        fhir_appendJsonString(&writer, physicalIdentifier);
        fhir_appendText(&writer, "}],\"status\":\"active\"}");

        result = fhir_finishWriter(&writer, length);
    }

    return result;
}

int fhir_buildDeviceRegistrationCondition(const char *physicalIdentifier, char *condition, size_t capacity, size_t *length)
{
    struct fhir_writer writer;
    int result = -EINVAL;

    if(fhir_prepareOutput(condition, capacity, length) && fhir_isValidPhysicalIdentifier(physicalIdentifier))
    {
        fhir_beginWriter(&writer, condition, capacity);
        fhir_appendText(&writer, FHIR_DEVICE_REGISTRATION_CONDITION_PREFIX);
        fhir_appendText(&writer, physicalIdentifier);

        result = fhir_finishWriter(&writer, length);
    }

    return result;
}

int fhir_buildObservation(const struct fhir_observation *observation, char *body, size_t capacity, size_t *length)
{
    struct fhir_writer writer;
    int result = -EINVAL;

    if(fhir_prepareOutput(body, capacity, length) && fhir_isValidObservation(observation))
    {
        fhir_beginWriter(&writer, body, capacity);
        fhir_appendText(&writer, "{\"resourceType\":\"Observation\",\"identifier\":[{\"system\":");
        fhir_appendJsonString(&writer, FHIR_MEASUREMENT_IDENTIFIER_SYSTEM);
        fhir_appendText(&writer, ",\"value\":\"");
        fhir_appendMeasurementIdentifier(&writer, observation);
        fhir_appendText(&writer, "\"}],\"status\":\"final\",\"category\":" FHIR_VITAL_SIGNS_CATEGORY_JSON ",\"code\":" FHIR_HEART_RATE_CODE_JSON);

        if(observation->patientReference != NULL)
        {
            fhir_appendText(&writer, ",\"subject\":{\"reference\":");
            fhir_appendJsonString(&writer, observation->patientReference);
            fhir_appendText(&writer, "}");
        }

        fhir_appendText(&writer, ",\"effectiveDateTime\":\"");
        fhir_appendUtcTime(&writer, observation->measurementEndUtcSeconds, observation->measurementEndUtcMilliseconds);
        fhir_appendText(&writer, "\",\"device\":{\"reference\":\"Device/");
        fhir_appendText(&writer, observation->serverDeviceId);
        fhir_appendText(&writer, "\"}");

        if(observation->kind == FHIR_OBSERVATION_KIND_HEART_RATE)
        {
            fhir_appendText(&writer, ",\"valueQuantity\":{\"value\":");
            fhir_appendScaledDecimal(&writer, observation->heartRateScaled, observation->heartRateDecimalPlaces);
            fhir_appendText(&writer, "," FHIR_HEART_RATE_UNIT_JSON "}");
        }
        else
        {
            fhir_appendText(&writer, ",\"dataAbsentReason\":" FHIR_ERROR_ABSENT_REASON_JSON);
        }

        fhir_appendText(&writer, "}");

        result = fhir_finishWriter(&writer, length);
    }

    return result;
}

int fhir_buildObservationCondition(const struct fhir_observation *observation, char *condition, size_t capacity, size_t *length)
{
    char identifier[FHIR_SERVER_DEVICE_ID_MAX_LENGTH + sizeof(":YYYY-MM-DDTHH:mm:ss.SSSZ")];
    size_t identifierLength = 0U;
    struct fhir_writer identifierWriter;
    struct fhir_writer writer;
    int result = -EINVAL;

    if(fhir_prepareOutput(condition, capacity, length) && fhir_hasValidMeasurementIdentity(observation))
    {
        fhir_beginWriter(&identifierWriter, identifier, sizeof(identifier));
        fhir_appendMeasurementIdentifier(&identifierWriter, observation);

        result = fhir_finishWriter(&identifierWriter, &identifierLength);

        if(result == 0)
        {
            fhir_beginWriter(&writer, condition, capacity);
            fhir_appendText(&writer, FHIR_OBSERVATION_CONDITION_PREFIX);
            fhir_appendPercentEncoded(&writer, identifier);

            result = fhir_finishWriter(&writer, length);
        }
    }

    return result;
}

int fhir_parseDeviceRegistration(const struct fhir_response *response, const char *baseUrl, const char *physicalIdentifier, char *serverDeviceId, size_t capacity, enum fhir_response_cause *cause)
{
    char locationId[FHIR_SERVER_DEVICE_ID_SIZE] = "";
    char bodyId[FHIR_SERVER_DEVICE_ID_SIZE] = "";
    enum fhir_response_cause outcome = FHIR_RESPONSE_CAUSE_NONE;
    int result = -EINVAL;

    if((serverDeviceId != NULL) && (capacity > 0U))
    {
        serverDeviceId[0] = '\0';
    }

    if((response != NULL) && (baseUrl != NULL) && (baseUrl[0] != '\0') && (serverDeviceId != NULL) && (capacity >= FHIR_SERVER_DEVICE_ID_SIZE) && (cause != NULL) && fhir_isValidPhysicalIdentifier(physicalIdentifier))
    {
        outcome = fhir_classifyStatus(response->status);

        if(outcome == FHIR_RESPONSE_CAUSE_NONE)
        {
            const bool hasLocation = (response->location != NULL);
            const bool hasBody = ((response->body != NULL) && (response->bodyLength > 0U));
            const char *agreedId = locationId;
            bool isValid = ((!hasLocation || fhir_parseDeviceLocation(response->location, baseUrl, locationId)) && (!hasBody || fhir_parseDeviceRepresentation(response->body, response->bodyLength, physicalIdentifier, bodyId)));

            if(locationId[0] == '\0')
            {
                agreedId = bodyId;
            }

            isValid = (isValid && (agreedId[0] != '\0') && ((bodyId[0] == '\0') || (strcmp(agreedId, bodyId) == 0)));

            if(isValid)
            {
                (void)memcpy(serverDeviceId, agreedId, strlen(agreedId) + 1U);
            }
            else
            {
                outcome = FHIR_RESPONSE_CAUSE_INVALID_REPRESENTATION;
            }
        }

        *cause = outcome;

        if(outcome == FHIR_RESPONSE_CAUSE_NONE)
        {
            result = 0;
        }
        else
        {
            result = -EBADMSG;
        }
    }

    return result;
}

int fhir_encodeRegistrationRecord(const char *baseUrl, const char *physicalIdentifier, const char *serverDeviceId, uint8_t *record, size_t capacity)
{
    size_t baseUrlLength = 0U;
    int result = -EINVAL;

    if(record != NULL)
    {
        (void)memset(record, 0, capacity);
    }

    if(baseUrl != NULL)
    {
        baseUrlLength = strlen(baseUrl);
    }

    if((record != NULL) && (capacity >= FHIR_REGISTRATION_RECORD_SIZE) && (baseUrlLength > 0U) && (baseUrlLength <= FHIR_BASE_URL_MAX_LENGTH) && fhir_isValidPhysicalIdentifier(physicalIdentifier) && fhir_isValidServerDeviceId(serverDeviceId))
    {
        /* The zero fill above supplies every terminator and the padding behind it. */
        record[FHIR_RECORD_VERSION_OFFSET] = FHIR_REGISTRATION_RECORD_VERSION;
        (void)memcpy(&record[FHIR_RECORD_BASE_URL_OFFSET], baseUrl, baseUrlLength);
        (void)memcpy(&record[FHIR_RECORD_PHYSICAL_IDENTIFIER_OFFSET], physicalIdentifier, strlen(physicalIdentifier));
        (void)memcpy(&record[FHIR_RECORD_SERVER_DEVICE_ID_OFFSET], serverDeviceId, strlen(serverDeviceId));

        result = 0;
    }

    return result;
}

int fhir_decodeRegistrationRecord(const uint8_t *record, size_t size, const char *baseUrl, const char *physicalIdentifier, char *serverDeviceId, size_t capacity)
{
    const char *storedBaseUrl = NULL;
    const char *storedPhysicalIdentifier = NULL;
    const char *storedServerDeviceId = NULL;
    int result = 0;

    if((serverDeviceId != NULL) && (capacity > 0U))
    {
        serverDeviceId[0] = '\0';
    }

    if((record == NULL) || (serverDeviceId == NULL) || (capacity < FHIR_SERVER_DEVICE_ID_SIZE) || (baseUrl == NULL) || (baseUrl[0] == '\0') || !fhir_isValidPhysicalIdentifier(physicalIdentifier))
    {
        result = -EINVAL;
    }
    else if((size != FHIR_REGISTRATION_RECORD_SIZE) || (record[FHIR_RECORD_VERSION_OFFSET] != FHIR_REGISTRATION_RECORD_VERSION))
    {
        result = -EBADMSG;
    }
    else if(!fhir_isValidRecordField(&record[FHIR_RECORD_BASE_URL_OFFSET], FHIR_BASE_URL_SIZE) || !fhir_isValidRecordField(&record[FHIR_RECORD_PHYSICAL_IDENTIFIER_OFFSET], FHIR_PHYSICAL_IDENTIFIER_SIZE) || !fhir_isValidRecordField(&record[FHIR_RECORD_SERVER_DEVICE_ID_OFFSET], FHIR_SERVER_DEVICE_ID_SIZE))
    {
        result = -EBADMSG;
    }
    else
    {
        /* Each field holds its terminator, so the texts are read in place without copies. */
        storedBaseUrl = (const char *)&record[FHIR_RECORD_BASE_URL_OFFSET];
        storedPhysicalIdentifier = (const char *)&record[FHIR_RECORD_PHYSICAL_IDENTIFIER_OFFSET];
        storedServerDeviceId = (const char *)&record[FHIR_RECORD_SERVER_DEVICE_ID_OFFSET];

        if((storedBaseUrl[0] == '\0') || !fhir_isValidPhysicalIdentifier(storedPhysicalIdentifier) || !fhir_isValidServerDeviceId(storedServerDeviceId))
        {
            result = -EBADMSG;
        }
        /* Exact comparison: both sides are our own canonical data, unlike a server's Location header. */
        else if((strcmp(storedBaseUrl, baseUrl) != 0) || (strcmp(storedPhysicalIdentifier, physicalIdentifier) != 0))
        {
            result = -ESTALE;
        }
        else
        {
            (void)memcpy(serverDeviceId, storedServerDeviceId, strlen(storedServerDeviceId) + 1U);
        }
    }

    return result;
}

/***********************************************************************/
/* LOCAL FUNCTIONS                                                     */
/***********************************************************************/

static bool fhir_isValidRecordField(const uint8_t *field, size_t fieldSize)
{
    const uint8_t *terminator = memchr(field, 0, fieldSize);
    size_t textLength = 0U;
    bool isValid = (terminator != NULL);

    if(isValid)
    {
        textLength = (size_t)(terminator - field);
    }

    /* Erased flash reads 0xFF, so nonzero padding also exposes a partly written record. */
    for(size_t index = (textLength + 1U); isValid && (index < fieldSize); index++)
    {
        isValid = (field[index] == 0U);
    }

    return isValid;
}

static bool fhir_prepareOutput(char *output, size_t capacity, size_t *length)
{
    if((output != NULL) && (capacity > 0U))
    {
        output[0] = '\0';
    }

    if(length != NULL)
    {
        *length = 0U;
    }

    return ((output != NULL) && (length != NULL));
}

static void fhir_beginWriter(struct fhir_writer *writer, char *buffer, size_t capacity)
{
    writer->buffer = buffer;
    writer->capacity = capacity;
    writer->length = 0U;
    writer->hasOverflowed = (capacity == 0U);
}

static void fhir_appendText(struct fhir_writer *writer, const char *text)
{
    if(!writer->hasOverflowed)
    {
        size_t textLength = strlen(text);

        /* Without an overflow length < capacity holds, so the subtraction cannot wrap
         * and the strict comparison keeps one byte for the terminator. */
        if(textLength < (writer->capacity - writer->length))
        {
            (void)memcpy(&writer->buffer[writer->length], text, textLength);

            writer->length += textLength;
        }
        else
        {
            writer->hasOverflowed = true;
        }
    }
}

static void fhir_appendJsonString(struct fhir_writer *writer, const char *text)
{
    fhir_appendText(writer, "\"");

    for(const char *character = text; *character != '\0'; character++)
    {
        unsigned char byte = (unsigned char)*character;
        char unescaped[2] = {*character, '\0'};
        char unicodeEscape[sizeof("\\u0000")] = {'\\', 'u', '0', '0', fhir_HexDigits[byte >> 4U], fhir_HexDigits[byte & 0x0FU], '\0'};
        const char *escape = unescaped;

        switch(byte)
        {
        case '"':
            escape = "\\\"";
            break;
        case '\\':
            escape = "\\\\";
            break;
        case '\b':
            escape = "\\b";
            break;
        case '\f':
            escape = "\\f";
            break;
        case '\n':
            escape = "\\n";
            break;
        case '\r':
            escape = "\\r";
            break;
        case '\t':
            escape = "\\t";
            break;
        default:
            if(byte < FHIR_JSON_FIRST_UNESCAPED_CHARACTER)
            {
                escape = unicodeEscape;
            }
            break;
        }

        fhir_appendText(writer, escape);
    }

    fhir_appendText(writer, "\"");
}

static int fhir_finishWriter(struct fhir_writer *writer, size_t *length)
{
    int result = 0;

    if(writer->hasOverflowed)
    {
        if(writer->capacity > 0U)
        {
            writer->buffer[0] = '\0';
        }

        *length = 0U;
        result = -ENOSPC;
    }
    else
    {
        writer->buffer[writer->length] = '\0';
        *length = writer->length;
    }

    return result;
}

static bool fhir_isValidPhysicalIdentifier(const char *physicalIdentifier)
{
    const size_t prefixLength = (sizeof(FHIR_PHYSICAL_IDENTIFIER_PREFIX) - 1U);
    const size_t identifierLength = (FHIR_PHYSICAL_IDENTIFIER_SIZE - 1U);
    bool isValid = ((physicalIdentifier != NULL) && (strlen(physicalIdentifier) == identifierLength) && (strncmp(physicalIdentifier, FHIR_PHYSICAL_IDENTIFIER_PREFIX, prefixLength) == 0));

    for(size_t index = prefixLength; isValid && (index < identifierLength); index++)
    {
        char digit = physicalIdentifier[index];

        isValid = (((digit >= '0') && (digit <= '9')) || ((digit >= 'A') && (digit <= 'F')));
    }

    return isValid;
}

static bool fhir_isValidServerDeviceId(const char *serverDeviceId)
{
    size_t idLength = 0U;
    bool isValid = (serverDeviceId != NULL);

    if(isValid)
    {
        idLength = strlen(serverDeviceId);
        isValid = ((idLength > 0U) && (idLength <= FHIR_SERVER_DEVICE_ID_MAX_LENGTH));
    }

    for(size_t index = 0U; isValid && (index < idLength); index++)
    {
        char character = serverDeviceId[index];

        isValid = (((character >= 'A') && (character <= 'Z')) || ((character >= 'a') && (character <= 'z')) || ((character >= '0') && (character <= '9')) || (character == '-') || (character == '.'));
    }

    return isValid;
}

static bool fhir_hasValidMeasurementIdentity(const struct fhir_observation *observation)
{
    return ((observation != NULL) && fhir_isValidServerDeviceId(observation->serverDeviceId) && (observation->measurementEndUtcMilliseconds < FHIR_MILLISECONDS_PER_SECOND) && (observation->measurementEndUtcSeconds <= FHIR_LATEST_UTC_SECONDS));
}

static bool fhir_isValidObservation(const struct fhir_observation *observation)
{
    bool isValid = (fhir_hasValidMeasurementIdentity(observation) && ((observation->patientReference == NULL) || (observation->patientReference[0] != '\0')));

    if(isValid)
    {
        switch(observation->kind)
        {
        case FHIR_OBSERVATION_KIND_HEART_RATE:
            isValid = ((observation->heartRateScaled > 0U) && (observation->heartRateDecimalPlaces <= FHIR_HEART_RATE_DECIMAL_PLACES_MAX));
            break;
        case FHIR_OBSERVATION_KIND_POOR_SIGNAL:
            break;
        default:
            isValid = false;
            break;
        }
    }

    return isValid;
}

static void fhir_appendUnsigned(struct fhir_writer *writer, uint32_t value, uint8_t minimumDigits)
{
    char digits[FHIR_UNSIGNED_DECIMAL_DIGITS + 1U];
    size_t start = FHIR_UNSIGNED_DECIMAL_DIGITS;
    uint32_t remaining = value;

    digits[start] = '\0';

    do
    {
        start--;
        digits[start] = (char)('0' + (remaining % 10U));
        remaining /= 10U;
    } while((start > 0U) && ((remaining > 0U) || ((FHIR_UNSIGNED_DECIMAL_DIGITS - start) < minimumDigits)));

    fhir_appendText(writer, &digits[start]);
}

static void fhir_appendUtcTime(struct fhir_writer *writer, uint64_t utcSeconds, uint16_t milliseconds)
{
    /* Days to a civil date by H. Hinnant's civil_from_days, because not every host build declares gmtime_r. */
    const uint64_t secondsOfDay = (utcSeconds % FHIR_SECONDS_PER_DAY);
    const uint64_t shiftedDays = ((utcSeconds / FHIR_SECONDS_PER_DAY) + 719468U);
    const uint64_t era = (shiftedDays / 146097U);
    const uint64_t dayOfEra = (shiftedDays - (era * 146097U));
    const uint64_t yearOfEra = ((((dayOfEra - (dayOfEra / 1460U)) + (dayOfEra / 36524U)) - (dayOfEra / 146096U)) / 365U);
    const uint64_t dayOfYear = (dayOfEra - (((365U * yearOfEra) + (yearOfEra / 4U)) - (yearOfEra / 100U)));
    const uint64_t monthIndex = (((5U * dayOfYear) + 2U) / 153U);
    const uint32_t day = (uint32_t)((dayOfYear - (((153U * monthIndex) + 2U) / 5U)) + 1U);
    const uint32_t month = (uint32_t)((monthIndex < 10U) ? (monthIndex + 3U) : (monthIndex - 9U));
    const uint32_t year = (uint32_t)((yearOfEra + (era * 400U)) + ((month <= 2U) ? 1U : 0U));

    fhir_appendUnsigned(writer, year, 4U);
    fhir_appendText(writer, "-");
    fhir_appendUnsigned(writer, month, 2U);
    fhir_appendText(writer, "-");
    fhir_appendUnsigned(writer, day, 2U);
    fhir_appendText(writer, "T");
    fhir_appendUnsigned(writer, (uint32_t)(secondsOfDay / FHIR_SECONDS_PER_HOUR), 2U);
    fhir_appendText(writer, ":");
    fhir_appendUnsigned(writer, (uint32_t)((secondsOfDay % FHIR_SECONDS_PER_HOUR) / FHIR_SECONDS_PER_MINUTE), 2U);
    fhir_appendText(writer, ":");
    fhir_appendUnsigned(writer, (uint32_t)(secondsOfDay % FHIR_SECONDS_PER_MINUTE), 2U);
    fhir_appendText(writer, ".");
    fhir_appendUnsigned(writer, milliseconds, 3U);
    fhir_appendText(writer, "Z");
}

static void fhir_appendScaledDecimal(struct fhir_writer *writer, uint32_t scaled, uint8_t decimalPlaces)
{
    uint32_t divisor = 1U;

    for(uint8_t place = 0U; place < decimalPlaces; place++)
    {
        divisor *= 10U;
    }

    fhir_appendUnsigned(writer, scaled / divisor, 1U);

    if(decimalPlaces > 0U)
    {
        fhir_appendText(writer, ".");
        fhir_appendUnsigned(writer, scaled % divisor, decimalPlaces);
    }
}

static void fhir_appendMeasurementIdentifier(struct fhir_writer *writer, const struct fhir_observation *observation)
{
    fhir_appendText(writer, observation->serverDeviceId);
    fhir_appendText(writer, ":");
    fhir_appendUtcTime(writer, observation->measurementEndUtcSeconds, observation->measurementEndUtcMilliseconds);
}

static void fhir_appendPercentEncoded(struct fhir_writer *writer, const char *text)
{
    for(const char *character = text; *character != '\0'; character++)
    {
        unsigned char byte = (unsigned char)*character;
        bool isUnreserved = (((byte >= 'A') && (byte <= 'Z')) || ((byte >= 'a') && (byte <= 'z')) || ((byte >= '0') && (byte <= '9')) || (byte == '-') || (byte == '.') || (byte == '_') || (byte == '~'));
        char encoded[sizeof("%XX")] = {'%', fhir_HexDigits[byte >> 4U], fhir_HexDigits[byte & 0x0FU], '\0'};

        if(isUnreserved)
        {
            encoded[0] = *character;
            encoded[1] = '\0';
        }

        fhir_appendText(writer, encoded);
    }
}

enum fhir_response_cause fhir_classifyStatus(uint16_t status)
{
    enum fhir_response_cause cause = FHIR_RESPONSE_CAUSE_REJECTED;

    if((status == FHIR_HTTP_201_CREATED) || (status == FHIR_HTTP_200_OK))
    {
        cause = FHIR_RESPONSE_CAUSE_NONE;
    }
    else if(status == FHIR_HTTP_412_PRECONDITION_FAILED)
    {
        cause = FHIR_RESPONSE_CAUSE_MULTIPLE_MATCHES;
    }
    else if(status == FHIR_HTTP_501_NOT_IMPLEMENTED)
    {
        cause = FHIR_RESPONSE_CAUSE_UNSUPPORTED;
    }
    else if((status >= FHIR_HTTP_SERVER_ERROR_FIRST) && (status <= FHIR_HTTP_SERVER_ERROR_LAST))
    {
        cause = FHIR_RESPONSE_CAUSE_SERVER_ERROR;
    }
    else
    {
        /* Every other status, including authentication and 3xx, is a terminal rejection. */
    }

    return cause;
}

static bool fhir_parseDeviceLocation(const char *location, const char *baseUrl, char *serverDeviceId)
{
    static const char devicePath[] = "/Device/";
    static const char historyPath[] = "/_history/";
    static const char schemeSeparator[] = "://";
    const char *schemeEnd = strstr(baseUrl, schemeSeparator);
    size_t schemeLength = 0U;
    const char *basePath = "";
    const char *id = NULL;
    const char *idEnd = NULL;
    size_t idLength = 0U;
    char candidate[FHIR_SERVER_DEVICE_ID_SIZE] = "";
    bool isValid = (schemeEnd != NULL);

    if(isValid)
    {
        const char *baseAuthorityEnd = NULL;

        schemeLength = ((size_t)(schemeEnd - baseUrl) + (sizeof(schemeSeparator) - 1U));
        baseAuthorityEnd = strchr(&baseUrl[schemeLength], '/');

        if(baseAuthorityEnd != NULL)
        {
            basePath = baseAuthorityEnd;
        }

        isValid = fhir_startsWithIgnoringCase(location, baseUrl, schemeLength);
    }

    if(isValid)
    {
        /* A query or fragment also ends the authority (RFC 3986 section 3.2), so '?' and '#' never pass as part of it. */
        const size_t authorityLength = strcspn(&location[schemeLength], "/?#");
        const char *path = &location[schemeLength + authorityLength];
        const size_t basePathLength = strlen(basePath);

        /* Each comparison only passes if location is at least as long, so the next offset stays inside it. */
        isValid = ((authorityLength > 0U) && (strncmp(path, basePath, basePathLength) == 0) && (strncmp(&path[basePathLength], devicePath, sizeof(devicePath) - 1U) == 0));

        if(isValid)
        {
            id = &path[(basePathLength + sizeof(devicePath)) - 1U];
        }
    }

    if(isValid)
    {
        idEnd = strchr(id, '/');
        idLength = ((idEnd != NULL) ? (size_t)(idEnd - id) : strlen(id));
        isValid = ((idLength > 0U) && (idLength <= FHIR_SERVER_DEVICE_ID_MAX_LENGTH));

        if(isValid)
        {
            (void)memcpy(candidate, id, idLength);

            candidate[idLength] = '\0';
        }
    }

    isValid = (isValid && fhir_isValidServerDeviceId(candidate) && ((idEnd == NULL) || ((strncmp(idEnd, historyPath, sizeof(historyPath) - 1U) == 0) && fhir_isValidServerDeviceId(&idEnd[sizeof(historyPath) - 1U]))));

    if(isValid)
    {
        (void)memcpy(serverDeviceId, candidate, idLength + 1U);
    }

    return isValid;
}

static bool fhir_startsWithIgnoringCase(const char *text, const char *prefix, size_t prefixLength)
{
    bool isEqual = true;

    for(size_t index = 0U; isEqual && (index < prefixLength); index++)
    {
        char textCharacter = text[index];
        char prefixCharacter = prefix[index];

        if((textCharacter >= 'A') && (textCharacter <= 'Z'))
        {
            textCharacter = (char)((textCharacter - 'A') + 'a');
        }

        if((prefixCharacter >= 'A') && (prefixCharacter <= 'Z'))
        {
            prefixCharacter = (char)((prefixCharacter - 'A') + 'a');
        }

        isEqual = ((textCharacter != '\0') && (textCharacter == prefixCharacter));
    }

    return isEqual;
}

static bool fhir_parseDeviceRepresentation(const char *body, size_t bodyLength, const char *physicalIdentifier, char *serverDeviceId)
{
    struct fhir_json_scanner scanner = {body, bodyLength, 0U};
    char name[sizeof("resourceType")];
    char resourceType[sizeof("Device")] = "";
    bool hasResourceType = false;
    bool hasId = false;
    bool hasIdentifiers = false;
    bool containsPhysicalIdentifier = false;
    bool isClosed = false;
    bool isValid = false;
    int result = 0;

    serverDeviceId[0] = '\0';

    if(fhir_consumeJsonCharacter(&scanner, '{'))
    {
        isClosed = fhir_consumeJsonCharacter(&scanner, '}');
    }
    else
    {
        result = -EBADMSG;
    }

    /* A repeated resourceType, id or identifier is malformed: RFC 8259 section 4 leaves duplicates undefined. */
    while((result == 0) && !isClosed)
    {
        const int nameResult = fhir_readJsonMemberName(&scanner, name, sizeof(name));

        if(nameResult == -EBADMSG)
        {
            result = -EBADMSG;
        }
        else if((nameResult == 0) && (strcmp(name, "resourceType") == 0))
        {
            result = (hasResourceType ? -EBADMSG : fhir_readJsonString(&scanner, resourceType, sizeof(resourceType)));
            hasResourceType = true;
        }
        else if((nameResult == 0) && (strcmp(name, "id") == 0))
        {
            result = (hasId ? -EBADMSG : fhir_readJsonString(&scanner, serverDeviceId, FHIR_SERVER_DEVICE_ID_SIZE));
            hasId = true;
        }
        else if((nameResult == 0) && (strcmp(name, "identifier") == 0))
        {
            result = (hasIdentifiers ? -EBADMSG : fhir_parseJsonIdentifiers(&scanner, physicalIdentifier, &containsPhysicalIdentifier));
            hasIdentifiers = true;
        }
        else
        {
            result = fhir_skipJsonValue(&scanner);
        }

        if(result == 0)
        {
            result = fhir_readJsonSeparator(&scanner, '}', &isClosed);
        }
    }

    if(result == 0)
    {
        fhir_skipJsonWhitespace(&scanner);

        isValid = ((scanner.position == bodyLength) && hasResourceType && (strcmp(resourceType, "Device") == 0) && (!hasId || fhir_isValidServerDeviceId(serverDeviceId)) && (!hasIdentifiers || containsPhysicalIdentifier));
    }

    if(!isValid)
    {
        serverDeviceId[0] = '\0';
    }

    return isValid;
}

static int fhir_parseJsonIdentifiers(struct fhir_json_scanner *scanner, const char *physicalIdentifier, bool *containsPhysicalIdentifier)
{
    bool isClosed = false;
    int result = 0;

    *containsPhysicalIdentifier = false;

    if(fhir_consumeJsonCharacter(scanner, '['))
    {
        isClosed = fhir_consumeJsonCharacter(scanner, ']');
    }
    else
    {
        result = -EBADMSG;
    }

    while((result == 0) && !isClosed)
    {
        bool isPhysicalIdentifier = false;

        result = fhir_parseJsonIdentifier(scanner, physicalIdentifier, &isPhysicalIdentifier);
        *containsPhysicalIdentifier = (*containsPhysicalIdentifier || isPhysicalIdentifier);

        if(result == 0)
        {
            result = fhir_readJsonSeparator(scanner, ']', &isClosed);
        }
    }

    return result;
}

static int fhir_parseJsonIdentifier(struct fhir_json_scanner *scanner, const char *physicalIdentifier, bool *isPhysicalIdentifier)
{
    char name[sizeof("system")];
    char system[sizeof(FHIR_DEVICE_IDENTIFIER_SYSTEM)];
    char value[FHIR_PHYSICAL_IDENTIFIER_SIZE];
    bool isSystemMatched = false;
    bool isValueMatched = false;
    bool isClosed = false;
    int result = 0;

    if(fhir_consumeJsonCharacter(scanner, '{'))
    {
        isClosed = fhir_consumeJsonCharacter(scanner, '}');
    }
    else
    {
        result = -EBADMSG;
    }

    while((result == 0) && !isClosed)
    {
        const int nameResult = fhir_readJsonMemberName(scanner, name, sizeof(name));

        if(nameResult == -EBADMSG)
        {
            result = -EBADMSG;
        }
        else if((nameResult == 0) && (strcmp(name, "system") == 0))
        {
            result = fhir_readJsonString(scanner, system, sizeof(system));
            isSystemMatched = ((result == 0) && (strcmp(system, FHIR_DEVICE_IDENTIFIER_SYSTEM) == 0));
        }
        else if((nameResult == 0) && (strcmp(name, "value") == 0))
        {
            result = fhir_readJsonString(scanner, value, sizeof(value));
            isValueMatched = ((result == 0) && (strcmp(value, physicalIdentifier) == 0));
        }
        else
        {
            result = fhir_skipJsonValue(scanner);
        }

        /* Too long for this device's identifier: well-formed, but no match. */
        if(result == -ENOSPC)
        {
            result = 0;
        }

        if(result == 0)
        {
            result = fhir_readJsonSeparator(scanner, '}', &isClosed);
        }
    }

    *isPhysicalIdentifier = (result == 0) && isSystemMatched && isValueMatched;

    return result;
}

static int fhir_readJsonString(struct fhir_json_scanner *scanner, char *destination, size_t capacity)
{
    size_t copiedLength = 0U;
    bool isClosed = false;
    bool hasOverflowed = false;
    int result = 0;

    if(!fhir_consumeJsonCharacter(scanner, '"'))
    {
        result = -EBADMSG;
    }

    while((result == 0) && !isClosed)
    {
        if(scanner->position < scanner->length)
        {
            const unsigned char byte = (unsigned char)scanner->text[scanner->position];

            scanner->position++;

            if(byte == '"')
            {
                isClosed = true;
            }
            else if(byte < FHIR_JSON_FIRST_UNESCAPED_CHARACTER)
            {
                result = -EBADMSG;
            }
            else if(byte == '\\')
            {
                result = ((destination != NULL) ? -EBADMSG : fhir_skipJsonEscape(scanner));
            }
            else if(destination == NULL)
            {
                /* Skipped content is not kept. */
            }
            else if((copiedLength + 1U) < capacity)
            {
                destination[copiedLength] = (char)byte;
                copiedLength++;
            }
            else
            {
                hasOverflowed = true;
            }
        }
        else
        {
            result = -EBADMSG;
        }
    }

    if((destination != NULL) && (capacity > 0U))
    {
        destination[copiedLength] = '\0';
    }

    if((result == 0) && hasOverflowed)
    {
        result = -ENOSPC;
    }

    return result;
}

static int fhir_skipJsonEscape(struct fhir_json_scanner *scanner)
{
    int result = -EBADMSG;

    if(scanner->position < scanner->length)
    {
        const char character = scanner->text[scanner->position];

        scanner->position++;

        /* strchr also finds the terminator, so a NUL byte must not reach it. */
        if((character != '\0') && (strchr("\"\\/bfnrt", character) != NULL))
        {
            result = 0;
        }
        else if(character == 'u')
        {
            result = 0;

            for(size_t digit = 0U; (result == 0) && (digit < FHIR_JSON_UNICODE_ESCAPE_DIGITS); digit++)
            {
                const char hex = ((scanner->position < scanner->length) ? scanner->text[scanner->position] : '\0');
                const bool isHexDigit = (((hex >= '0') && (hex <= '9')) || ((hex >= 'a') && (hex <= 'f')) || ((hex >= 'A') && (hex <= 'F')));

                if(isHexDigit)
                {
                    scanner->position++;
                }
                else
                {
                    result = -EBADMSG;
                }
            }
        }
        else
        {
            /* Any other escape is malformed. */
        }
    }

    return result;
}

static int fhir_readJsonMemberName(struct fhir_json_scanner *scanner, char *name, size_t capacity)
{
    int result = fhir_readJsonString(scanner, name, capacity);

    if((result != -EBADMSG) && !fhir_consumeJsonCharacter(scanner, ':'))
    {
        result = -EBADMSG;
    }

    return result;
}

static int fhir_readJsonSeparator(struct fhir_json_scanner *scanner, char closing, bool *isClosed)
{
    int result = 0;

    *isClosed = fhir_consumeJsonCharacter(scanner, closing);

    if(!*isClosed && !fhir_consumeJsonCharacter(scanner, ','))
    {
        result = -EBADMSG;
    }

    return result;
}

static int fhir_skipJsonValue(struct fhir_json_scanner *scanner)
{
    char closings[FHIR_JSON_DEPTH_MAX]; /* Expected closing bracket of every open container. */
    size_t depth = 0U;
    bool expectsValue = true;
    bool isComplete = false;
    int result = 0;

    while((result == 0) && !isComplete)
    {
        if(expectsValue)
        {
            fhir_skipJsonWhitespace(scanner);

            if(scanner->position >= scanner->length)
            {
                result = -EBADMSG;
            }
            else if((scanner->text[scanner->position] == '{') || (scanner->text[scanner->position] == '['))
            {
                if(depth < FHIR_JSON_DEPTH_MAX)
                {
                    closings[depth] = ((scanner->text[scanner->position] == '{') ? '}' : ']');
                    depth++;
                    scanner->position++;

                    if(fhir_consumeJsonCharacter(scanner, closings[depth - 1U]))
                    {
                        depth--;
                        expectsValue = false;
                    }
                    else if(closings[depth - 1U] == '}')
                    {
                        result = fhir_readJsonMemberName(scanner, NULL, 0U);
                    }
                    else
                    {
                        /* The first array element follows. */
                    }
                }
                else
                {
                    result = -EBADMSG;
                }
            }
            else
            {
                result = fhir_skipJsonScalar(scanner);
                expectsValue = false;
            }
        }
        else if(depth == 0U)
        {
            isComplete = true;
        }
        else
        {
            bool isClosed = false;

            result = fhir_readJsonSeparator(scanner, closings[depth - 1U], &isClosed);

            if(isClosed)
            {
                depth--;
            }
            else if(result == 0)
            {
                expectsValue = true;

                if(closings[depth - 1U] == '}')
                {
                    result = fhir_readJsonMemberName(scanner, NULL, 0U);
                }
            }
            else
            {
                /* Malformed: neither a comma nor the closing bracket. */
            }
        }
    }

    return result;
}

static int fhir_skipJsonScalar(struct fhir_json_scanner *scanner)
{
    static const char *const literals[] = {"true", "false", "null"};
    const size_t remaining = (scanner->length - scanner->position);
    const size_t start = scanner->position;
    bool isLiteral = false;
    int result = 0;

    if(scanner->text[start] == '"')
    {
        result = fhir_readJsonString(scanner, NULL, 0U);
    }
    else
    {
        for(size_t index = 0U; !isLiteral && (index < (sizeof(literals) / sizeof(literals[0]))); index++)
        {
            const size_t literalLength = strlen(literals[index]);

            if((remaining >= literalLength) && (memcmp(&scanner->text[start], literals[index], literalLength) == 0))
            {
                scanner->position += literalLength;
                isLiteral = true;
            }
        }

        while(!isLiteral && (scanner->position < scanner->length) && (scanner->text[scanner->position] != '\0') && (strchr("0123456789-+.eE", scanner->text[scanner->position]) != NULL))
        {
            scanner->position++;
        }

        if(!isLiteral && (scanner->position == start))
        {
            result = -EBADMSG;
        }
    }

    return result;
}

static void fhir_skipJsonWhitespace(struct fhir_json_scanner *scanner)
{
    bool isWhitespace = true;

    while(isWhitespace && (scanner->position < scanner->length))
    {
        const char character = scanner->text[scanner->position];

        isWhitespace = ((character == ' ') || (character == '\t') || (character == '\n') || (character == '\r'));

        if(isWhitespace)
        {
            scanner->position++;
        }
    }
}

static bool fhir_consumeJsonCharacter(struct fhir_json_scanner *scanner, char expected)
{
    bool isConsumed = false;

    fhir_skipJsonWhitespace(scanner);

    if((scanner->position < scanner->length) && (scanner->text[scanner->position] == expected))
    {
        scanner->position++;
        isConsumed = true;
    }

    return isConsumed;
}

/** @} */
