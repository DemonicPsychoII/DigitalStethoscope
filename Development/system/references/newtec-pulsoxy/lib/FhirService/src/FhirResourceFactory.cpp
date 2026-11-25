/*******************************************************************************
    DESCRIPTION
*******************************************************************************/
/**
 * @brief Factory for creating FHIR resources
 */

/******************************************************************************
 * Includes
 *****************************************************************************/

#include "FhirResourceFactory.h"
#include <ArduinoJson.h>
#include <time.h>

/******************************************************************************
 * Compiler Switches
 *****************************************************************************/

/******************************************************************************
 * Macros
 *****************************************************************************/

#define OBSERVATION_JSON_BUFFER_SIZE (1024)
#define DEVICE_JSON_BUFFER_SIZE (512)
#define PATIENT_JSON_BUFFER_SIZE (512)

/******************************************************************************
 * Types and Classes
 *****************************************************************************/

/******************************************************************************
 * Prototypes
 *****************************************************************************/

/******************************************************************************
 * Local Variables
 *****************************************************************************/

/* Heart rate configuration */
static const ObservationConfig HEART_RATE_CONFIG = {
    "https://gematik.de/fhir/isik/StructureDefinition/ISiKHerzfrequenz", /**< ISiK profile URL */
    "8867-4",                                                            /**< LOINC code */
    "Heart rate",                                                        /**< LOINC display text */
    "Herzfrequenz",                                                      /**< German display text */
    "per minute",                                                        /**< Unit of measure */
    "/min"                                                               /**< UCUM code */
};

/* SpO2 configuration */
static const ObservationConfig SPO2_CONFIG = {
    "https://gematik.de/fhir/isik/StructureDefinition/ISiKSauerstoffsaettigungArteriell", /**< ISiK profile URL */
    "59408-5",                                                                            /**< LOINC code */
    "Oxygen saturation in Arterial blood by Pulse oximetry",                              /**< LOINC display text */
    "Sauerstoffsättigung",                                                                /**< German display text */
    "%",                                                                                  /**< Unit of measure */
    "%"                                                                                   /**< UCUM code */
};

/******************************************************************************
 * Public Methods
 *****************************************************************************/

String FhirResourceFactory::createObservation(ObservationType type, const String& patientId, double value, const String& deviceId)
{
    const ObservationConfig* config = getObservationConfig(type);

    /* Serialize to JSON string */
    String json;

    if (nullptr != config)
    {
        DynamicJsonDocument doc(OBSERVATION_JSON_BUFFER_SIZE);

        /* Base structure */
        doc["resourceType"] = "Observation";
        doc["status"]       = "final";

        /* Meta with ISiK profile */
        JsonObject meta     = doc["meta"].to<JsonObject>();
        JsonArray  profiles = meta["profile"].to<JsonArray>();
        profiles.add(config->profileUrl);

        /* Category */
        JsonArray  category      = doc["category"].to<JsonArray>();
        JsonObject vitalSigns    = category.createNestedObject();
        JsonArray  vsCoding      = vitalSigns["coding"].to<JsonArray>();
        JsonObject vsCode        = vsCoding.createNestedObject();
        vsCode["system"]         = "http://terminology.hl7.org/CodeSystem/observation-category";
        vsCode["code"]           = "vital-signs";

        /* Code (LOINC) */
        JsonObject code          = doc["code"].to<JsonObject>();
        JsonArray  coding        = code["coding"].to<JsonArray>();
        JsonObject loincCode     = coding.createNestedObject();
        loincCode["system"]      = "http://loinc.org";
        loincCode["code"]        = config->loincCode;
        loincCode["display"]     = config->loincDisplay;
        code["text"]             = config->displayText;

        /* Subject (Patient) */
        JsonObject subject       = doc["subject"].to<JsonObject>();
        subject["reference"]     = "Patient/" + patientId;

        /* Effective DateTime */

        doc["effectiveDateTime"] = getCurrentTimestamp();

        /* Value Quantity */
        JsonObject valueQuantity = doc["valueQuantity"].to<JsonObject>();
        valueQuantity["value"]   = value;
        valueQuantity["unit"]    = config->unit;
        valueQuantity["system"]  = "http://unitsofmeasure.org";
        valueQuantity["code"]    = config->unitCode;

        /* Device */
        JsonObject device        = doc["device"].to<JsonObject>();
        device["reference"]      = "Device/" + deviceId;


        serializeJson(doc, json);
    }
    else
    {
        json = "";
    }

    return json;
}

String FhirResourceFactory::createDevice(const String& deviceId, const String& manufacturer, const String& modelNumber, const String& serialNumber)
{
    DynamicJsonDocument doc(DEVICE_JSON_BUFFER_SIZE);

    /* Base structure */
    doc["resourceType"] = "Device";
    doc["id"]           = deviceId;
    doc["status"]       = "active";

    /* Manufacturer */
    doc["manufacturer"] = manufacturer;

    /* Serial number */
    doc["serialNumber"] = serialNumber;

    /* Model number */
    doc["modelNumber"]  = modelNumber;

    /* Serialize to JSON string */
    String json;
    serializeJson(doc, json);

    return json;
}

String FhirResourceFactory::createPatient(const String& patientId, const String& familyName, const String& givenName)
{
    DynamicJsonDocument doc(PATIENT_JSON_BUFFER_SIZE);

    /* Base structure */
    doc["resourceType"] = "Patient";
    doc["id"]           = patientId;
    doc["active"]       = true;

    /* Name */
    JsonArray  name       = doc["name"].to<JsonArray>();
    JsonObject humanName  = name.createNestedObject();
    humanName["use"]      = "official";
    humanName["family"]   = familyName;
    JsonArray  given      = humanName["given"].to<JsonArray>();
    given.add(givenName);

    /* Serialize to JSON string */
    String json;
    serializeJson(doc, json);

    return json;
}

/******************************************************************************
 * Private Methods
 *****************************************************************************/

String FhirResourceFactory::getCurrentTimestamp()
{
    time_t    now;
    struct tm timeinfo;
    char      timestamp[25];

    time(&now);
    gmtime_r(&now, &timeinfo);
    strftime(timestamp, sizeof(timestamp), "%Y-%m-%dT%H:%M:%SZ", &timeinfo);

    return String(timestamp);
}

const ObservationConfig* FhirResourceFactory::getObservationConfig(ObservationType type)
{
    const ObservationConfig* config = nullptr;

    switch (type)
    {
    case ObservationType::HEART_RATE:
        config = &HEART_RATE_CONFIG;
        break;

    case ObservationType::SPO2:
        config = &SPO2_CONFIG;
        break;

    default:
        config = nullptr;
        break;
    }

    return config;
}

/******************************************************************************
 * External Functions
 *****************************************************************************/

/******************************************************************************
 * Local Functions
 *****************************************************************************/