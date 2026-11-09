/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @defgroup L1_FHIR FHIR
 * @{
 * @file
 * L1 pure C library that serializes results into FHIR Observations.
 */

#ifndef L1_FHIR_H
#define L1_FHIR_H

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

#define FHIR_DEVICE_IDENTIFIER_SYSTEM   "urn:stethoscope:device"                                 /**< P27-IDENTITY: Device.identifier.system. */
#define FHIR_PHYSICAL_IDENTIFIER_PREFIX "stetho-"                                                /**< P27-IDENTITY: prefix before the 12 uppercase MAC hex digits. */
#define FHIR_PHYSICAL_IDENTIFIER_SIZE   (sizeof(FHIR_PHYSICAL_IDENTIFIER_PREFIX "AABBCCDDEEFF")) /**< P27-RECORD: 20 bytes including the terminator. */
#define FHIR_OUTGOING_BODY_CAPACITY     (2048)                                                   /**< P27-BUFFERS: proposed outgoing JSON capacity. */

/** If-None-Exist search parameter: FHIR_DEVICE_IDENTIFIER_SYSTEM percent-encoded, then the token separator. */
#define FHIR_DEVICE_REGISTRATION_CONDITION_PREFIX "identifier=urn%3Astethoscope%3Adevice|"

/** If-None-Exist value of the Device registration, including the terminator. */
#define FHIR_DEVICE_REGISTRATION_CONDITION_SIZE \
    (sizeof(FHIR_DEVICE_REGISTRATION_CONDITION_PREFIX FHIR_PHYSICAL_IDENTIFIER_PREFIX "AABBCCDDEEFF"))

#define FHIR_MEASUREMENT_IDENTIFIER_SYSTEM "urn:stethoscope:measurement"          /**< Observation.identifier.system (system design, delivery). */
#define FHIR_SERVER_DEVICE_ID_MAX_LENGTH   (64)                                   /**< P27-RECORD: FHIR R4 id, 1 to 64 characters. */
#define FHIR_SERVER_DEVICE_ID_SIZE         (FHIR_SERVER_DEVICE_ID_MAX_LENGTH + 1) /**< P27-RECORD: 65-byte id field including the terminator. */
#define FHIR_HEART_RATE_DECIMAL_PLACES_MAX (9)                                    /**< Largest declared precision; 10^9 still fits uint32_t. */

#define FHIR_REGISTRATION_RECORD_NAME    "fhir/device-registration" /**< P27-RECORD: storage name of the registration record. */
#define FHIR_REGISTRATION_RECORD_VERSION (1U)                       /**< P27-RECORD: encoding version in byte 0. */
#define FHIR_BASE_URL_MAX_LENGTH         (256U)                     /**< P27-RECORD: longest canonical base URL in bytes. */
#define FHIR_BASE_URL_SIZE               (FHIR_BASE_URL_MAX_LENGTH + 1U)

/** P27-RECORD: version byte, then base URL, physical identifier and server Device id fields: 343 bytes. */
#define FHIR_REGISTRATION_RECORD_SIZE (1U + FHIR_BASE_URL_SIZE + FHIR_PHYSICAL_IDENTIFIER_SIZE + FHIR_SERVER_DEVICE_ID_SIZE)

/** If-None-Exist search parameter of an Observation: the encoded measurement system, then the token separator. */
#define FHIR_OBSERVATION_CONDITION_PREFIX "identifier=urn%3Astethoscope%3Ameasurement|"

/**
 * If-None-Exist value of an Observation, including the terminator: the longest server Device id,
 * then the encoded colon and measurement-end UTC with its two encoded colons.
 */
#define FHIR_OBSERVATION_CONDITION_SIZE \
    ((sizeof(FHIR_OBSERVATION_CONDITION_PREFIX) + FHIR_SERVER_DEVICE_ID_MAX_LENGTH + sizeof("%3A2026-10-23T12%3A00%3A00.000Z")) - 1U)

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/** Kind of a finalized heart-rate result that is sent. */
enum fhir_observation_kind
{
    FHIR_OBSERVATION_KIND_HEART_RATE,  /**< Valid BPM: valueQuantity in /min. */
    FHIR_OBSERVATION_KIND_POOR_SIGNAL, /**< REQ-08: no value, dataAbsentReason "error". */
};

/**
 * Frozen content of one Observation. Every field is fixed once at finalization;
 * the same input always serializes to the same bytes, so retries resend them unchanged.
 */
struct fhir_observation
{
    const char *serverDeviceId;             /**< Persisted logical Device id, 1-64 of A-Z a-z 0-9 '-' '.'; borrowed. */
    uint64_t measurementEndUtcSeconds;      /**< Frozen measurement end, UTC seconds since 1970; at most year 9999. */
    uint16_t measurementEndUtcMilliseconds; /**< Millisecond part of the frozen end, 0-999. */
    const char *patientReference;           /**< Supplied subject reference, nonempty; NULL omits subject; borrowed. */
    enum fhir_observation_kind kind;        /**< Selects valueQuantity or dataAbsentReason. */
    uint32_t heartRateScaled;               /**< HEART_RATE only: BPM times 10^heartRateDecimalPlaces, above 0. */
    uint8_t heartRateDecimalPlaces;         /**< HEART_RATE only: declared precision, 0 to FHIR_HEART_RATE_DECIMAL_PLACES_MAX. */
};

/** Outcome of a FHIR conditional-create response; carries no response content. */
enum fhir_response_cause
{
    FHIR_RESPONSE_CAUSE_NONE,                   /**< 201 or 200 with valid content. */
    FHIR_RESPONSE_CAUSE_SERVER_ERROR,           /**< 5xx other than 501; transient under P13. */
    FHIR_RESPONSE_CAUSE_MULTIPLE_MATCHES,       /**< 412: the condition matched several resources; terminal. */
    FHIR_RESPONSE_CAUSE_UNSUPPORTED,            /**< 501: the server cannot do the conditional create; terminal. */
    FHIR_RESPONSE_CAUSE_REJECTED,               /**< Any other non-success status, including authentication; terminal. */
    FHIR_RESPONSE_CAUSE_INVALID_REPRESENTATION, /**< 201/200 whose Location or body is missing, malformed or wrong. */
};

/** One complete HTTP response, as handed over by the transport. */
struct fhir_response
{
    uint16_t status;      /**< HTTP status code. */
    const char *location; /**< NUL-terminated Location header value; NULL when absent; borrowed. */
    const char *body;     /**< Body bytes, not terminated; NULL when bodyLength is 0; borrowed. */
    size_t bodyLength;    /**< Body length in bytes; the complete body, never a truncated one. */
};

/***********************************************************************/
/* GLOBAL CONSTANTS                                                    */
/***********************************************************************/

/***********************************************************************/
/* GLOBAL VARIABLES                                                    */
/***********************************************************************/

/***********************************************************************/
/* GLOBAL FUNCTION PROTOTYPES                                          */
/***********************************************************************/

/**
 * @brief Serialize the conditional-create body of this device's FHIR Device.
 *
 * Writes exactly
 * {"resourceType":"Device","identifier":[{"system":"urn:stethoscope:device","value":"<physical identifier>"}],"status":"active"}
 * with no whitespace, logical id, manufacturer, model or patient.
 * No network, clock or storage access.
 *
 * @param[in]  physicalIdentifier NUL-terminated "stetho-" plus 12 uppercase hex digits;
 *                                borrowed for the call only.
 * @param[out] body               Caller buffer; on success the NUL-terminated JSON,
 *                                on failure the empty string when @p capacity > 0.
 * @param[in]  capacity           Size of @p body in bytes, including room for the terminator.
 * @param[out] length             JSON length without the terminator on success, 0 on failure.
 *
 * @return 0 on success, -EINVAL for a NULL pointer or malformed @p physicalIdentifier,
 *         -ENOSPC if the JSON and terminator do not fit. Never returns truncated JSON.
 */
int fhir_buildDeviceRegistration(const char *physicalIdentifier, char *body, size_t capacity, size_t *length);

/**
 * @brief Build the If-None-Exist header value that makes the Device POST conditional.
 *
 * Writes exactly identifier=urn%3Astethoscope%3Adevice|<physical identifier>.
 * The same physical identifier always yields the same condition, so a repeated
 * registration after restart or lost receipt finds the same server resource.
 *
 * @param[in]  physicalIdentifier As for fhir_buildDeviceRegistration().
 * @param[out] condition          Caller buffer; on success the NUL-terminated header value,
 *                                on failure the empty string when @p capacity > 0.
 * @param[in]  capacity           Size of @p condition, at least FHIR_DEVICE_REGISTRATION_CONDITION_SIZE.
 * @param[out] length             Value length without the terminator on success, 0 on failure.
 *
 * @return 0 on success, -EINVAL for a NULL pointer or malformed @p physicalIdentifier,
 *         -ENOSPC if the value and terminator do not fit. Never returns a truncated value.
 */
int fhir_buildDeviceRegistrationCondition(const char *physicalIdentifier, char *condition, size_t capacity, size_t *length);

/**
 * @brief Serialize one frozen result as a FHIR R4 Observation for conditional create.
 *
 * Contains resourceType Observation, status final, the measurement identifier
 * <serverDeviceId>:<YYYY-MM-DDTHH:mm:ss.SSSZ>, category vital-signs, LOINC 8867-4,
 * effectiveDateTime with the same UTC text, device Device/<serverDeviceId>, subject only
 * when a patient reference is given, and either valueQuantity in /min (UCUM) with the
 * declared decimal places or dataAbsentReason "error". No meta.profile, whitespace or send time.
 *
 * @param[in]  observation Frozen content; borrowed for the call only.
 * @param[out] body        Caller buffer; on success the NUL-terminated JSON,
 *                         on failure the empty string when @p capacity > 0.
 * @param[in]  capacity    Size of @p body in bytes, normally FHIR_OUTGOING_BODY_CAPACITY.
 * @param[out] length      JSON length without the terminator on success, 0 on failure.
 *
 * @return 0 on success, -EINVAL for a NULL pointer or invalid content,
 *         -ENOSPC if the JSON and terminator do not fit. Never returns truncated JSON.
 */
int fhir_buildObservation(const struct fhir_observation *observation, char *body, size_t capacity, size_t *length);

/**
 * @brief Build the If-None-Exist header value that makes the Observation POST conditional.
 *
 * Writes identifier=urn%3Astethoscope%3Ameasurement|<value>, where <value> is the
 * measurement identifier percent-encoded for a URI query; for example
 * device-42:2026-10-23T12:00:00.000Z becomes device-42%3A2026-10-23T12%3A00%3A00.000Z.
 * Only serverDeviceId and the measurement end are used.
 *
 * @param[in]  observation As for fhir_buildObservation().
 * @param[out] condition   Caller buffer; on success the NUL-terminated header value,
 *                         on failure the empty string when @p capacity > 0.
 * @param[in]  capacity    Size of @p condition, at least FHIR_OBSERVATION_CONDITION_SIZE.
 * @param[out] length      Value length without the terminator on success, 0 on failure.
 *
 * @return 0 on success, -EINVAL for a NULL pointer or invalid identity fields,
 *         -ENOSPC if the value and terminator do not fit. Never returns a truncated value.
 */
int fhir_buildObservationCondition(const struct fhir_observation *observation, char *condition, size_t capacity, size_t *length);

/**
 * @brief Extract and validate the logical Device id from a conditional-create response.
 *
 * Status: 201 or 200 continue; 412 gives MULTIPLE_MATCHES, 501 UNSUPPORTED, other 5xx
 * SERVER_ERROR and every other status REJECTED (P13 outcome policy). For 201/200:
 * - Location, when present, must be <scheme>://<authority><base path>/Device/<id> with an
 *   optional /_history/<version> suffix. Scheme and base path come from @p baseUrl; the
 *   scheme compares case-insensitively, the base path exactly. The authority is not
 *   compared, because servers write their configured address there; it must be nonempty
 *   and contain no '?' or '#'.
 * - A body, when present, must be one JSON object with resourceType "Device"; its id is
 *   optional, and an identifier array, when present, must contain this device's
 *   urn:stethoscope:device identifier.
 * - At least one source must supply an id; when both do, they must be equal.
 * Any other 201/200 content gives INVALID_REPRESENTATION. HTTP success alone is not a registration.
 *
 * @param[in]  response           Complete, bounded response; borrowed for the call only.
 * @param[in]  baseUrl            Canonical server profile base URL without trailing slash; borrowed.
 * @param[in]  physicalIdentifier This device's identity, as for fhir_buildDeviceRegistration(); borrowed.
 * @param[out] serverDeviceId     Caller buffer; on success the NUL-terminated id,
 *                                otherwise the empty string when @p capacity > 0.
 * @param[in]  capacity           Size of @p serverDeviceId, at least FHIR_SERVER_DEVICE_ID_SIZE.
 * @param[out] cause              Outcome; written on every return except -EINVAL.
 *
 * @return 0 with a validated id, -EBADMSG when the response is no valid registration
 *         (see @p cause), or -EINVAL for a NULL pointer, a capacity below
 *         FHIR_SERVER_DEVICE_ID_SIZE, an empty base URL or a malformed @p physicalIdentifier.
 */
int fhir_parseDeviceRegistration(const struct fhir_response *response, const char *baseUrl, const char *physicalIdentifier, char *serverDeviceId, size_t capacity, enum fhir_response_cause *cause);

/**
 * @brief Map an HTTP status to its P13 outcome class.
 *
 * Shared by the registration parser and Observation delivery, so both apply one policy.
 *
 * @param[in] status HTTP status code.
 *
 * @return NONE for 201 and 200, MULTIPLE_MATCHES for 412, UNSUPPORTED for 501,
 *         SERVER_ERROR for other 5xx and REJECTED for everything else.
 */
enum fhir_response_cause fhir_classifyStatus(uint16_t status);

/**
 * @brief Encode the registration record that binds a server Device id to a server and this device.
 *
 * Layout, FHIR_REGISTRATION_RECORD_SIZE bytes: byte 0 FHIR_REGISTRATION_RECORD_VERSION, then
 * the base URL (FHIR_BASE_URL_SIZE), the physical identifier (FHIR_PHYSICAL_IDENTIFIER_SIZE)
 * and the server Device id (FHIR_SERVER_DEVICE_ID_SIZE). Each field is NUL-terminated and
 * zero-padded to its full size. No C struct is stored, so the layout cannot depend on the compiler.
 *
 * @param[in]  baseUrl            Canonical server profile base URL, 1 to FHIR_BASE_URL_MAX_LENGTH bytes; borrowed.
 * @param[in]  physicalIdentifier This device's identity, as for fhir_buildDeviceRegistration(); borrowed.
 * @param[in]  serverDeviceId     Validated FHIR id; borrowed.
 * @param[out] record             Caller buffer, zero-filled up to @p capacity on every return;
 *                                on success the record occupies its first FHIR_REGISTRATION_RECORD_SIZE bytes.
 * @param[in]  capacity           Size of @p record, at least FHIR_REGISTRATION_RECORD_SIZE.
 *
 * @return 0 on success, or -EINVAL for a NULL pointer, a capacity below
 *         FHIR_REGISTRATION_RECORD_SIZE or an invalid field.
 */
int fhir_encodeRegistrationRecord(const char *baseUrl, const char *physicalIdentifier, const char *serverDeviceId, uint8_t *record, size_t capacity);

/**
 * @brief Decode a stored registration record and check that it belongs to this server and device.
 *
 * @param[in]  record             Stored bytes; borrowed for the call only.
 * @param[in]  size               Number of bytes in @p record.
 * @param[in]  baseUrl            Current canonical base URL; must equal the stored one byte for byte.
 * @param[in]  physicalIdentifier This device's identity; must equal the stored one.
 * @param[out] serverDeviceId     Caller buffer; on success the stored id, otherwise "" when @p capacity > 0.
 * @param[in]  capacity           Size of @p serverDeviceId, at least FHIR_SERVER_DEVICE_ID_SIZE.
 *
 * @return 0 for a valid record of this binding; -EBADMSG for a wrong size or version, a field
 *         without terminator or with nonzero padding, or an invalid stored field; -ESTALE for a
 *         valid record of another base URL or physical identifier; -EINVAL for a NULL pointer,
 *         a capacity below FHIR_SERVER_DEVICE_ID_SIZE, an empty base URL or a malformed
 *         @p physicalIdentifier.
 */
int fhir_decodeRegistrationRecord(const uint8_t *record, size_t size, const char *baseUrl, const char *physicalIdentifier, char *serverDeviceId, size_t capacity);

#endif /* L1_FHIR_H */

/** @} */
