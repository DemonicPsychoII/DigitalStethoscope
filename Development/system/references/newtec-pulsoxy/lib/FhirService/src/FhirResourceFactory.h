/*******************************************************************************
    DESCRIPTION
*******************************************************************************/
/**
 * @file FhirResourceFactory.h
 *
 * @brief Factory for creating FHIR resources
 */

#ifndef FHIR_RESOURCE_FACTORY_H
#define FHIR_RESOURCE_FACTORY_H

/******************************************************************************
 * Compile Switches
 *****************************************************************************/

/******************************************************************************
 * Includes
 *****************************************************************************/

#include <Arduino.h>

/******************************************************************************
 * Macros
 *****************************************************************************/

/******************************************************************************
 * Types and Classes
 *****************************************************************************/

/**
 * @enum ObservationType
 *
 * @brief Supported observation types.
 */
enum class ObservationType
{
    HEART_RATE, /**< Heart rate ISiK Profile (https://gematik.de/fhir/isik/StructureDefinition/ISiKHerzfrequenz) */
    SPO2        /**< Oxygen saturation ISiK Profile (https://gematik.de/fhir/isik/StructureDefinition/ISiKSauerstoffsaettigungArteriell) */
};

/**
 * @struct ObservationConfig
 *
 * @brief Configuration for an observation type.
 */
struct ObservationConfig
{
    const char* profileUrl;   /**< ISiK profile URL */
    const char* loincCode;    /**< LOINC code */
    const char* loincDisplay; /**< LOINC display text */
    const char* displayText;  /**< German display text */
    const char* unit;         /**< Unit of measure */
    const char* unitCode;     /**< UCUM code */
};

/**
 * @class FhirResourceFactory
 *
 * @brief Factory for creating FHIR resources.
 */
class FhirResourceFactory
{
public:

    /**
     * @brief Create a simple ISIK observation with a single numeric value.
     *
     * @param[in] type Observation type.
     * @param[in] patientId Patient ID.
     * @param[in] value Numeric value.
     * @param[in] deviceId Device ID.
     *
     * @return JSON string containing the observation.
     */
    static String createObservation(ObservationType type, const String& patientId, double value, const String& deviceId);

    /**
     * @brief Create a device resource.
     *
     * @param[in] deviceId Logical identifier for the device (used as resource ID).
     * @param[in] manufacturer Device manufacturer name.
     * @param[in] modelNumber Device model number.
     * @param[in] serialNumber Device serial number.
     *
     * @return JSON string containing the device resource.
     */
    static String createDevice(const String& deviceId, const String& manufacturer, const String& modelNumber, const String& serialNumber);

    /**
     * @brief Create a patient resource.
     *
     * @param[in] patientId Logical identifier for the patient (used as resource ID).
     * @param[in] familyName Patient's family name.
     * @param[in] givenName Patient's given name.
     *
     * @return JSON string containing the patient resource.
     */
    static String createPatient(const String& patientId, const String& familyName, const String& givenName);

private:

    /**
     * @brief Get current timestamp.
     *
     * @return Timestamp string.
     */
    static String getCurrentTimestamp();

    /**
     * @brief Get configuration for an observation type.
     *
     * @param[in] type ObservationType.
     *
     * @return Pointer to configuration.
     */
    static const ObservationConfig* getObservationConfig(ObservationType type);
};

/******************************************************************************
 * Functions
 *****************************************************************************/

#endif /* FHIR_RESOURCE_FACTORY_H */