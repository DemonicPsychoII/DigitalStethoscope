/*******************************************************************************
    DESCRIPTION
*******************************************************************************/
/**
 * @file    FhirService.h
 *
 * @brief   FHIR server communication service.
 */

#ifndef FHIR_SERVICE_H
#define FHIR_SERVICE_H

/******************************************************************************
 * Compile Switches
 *****************************************************************************/

/******************************************************************************
 * Includes
 *****************************************************************************/

#include <WiFiClientSecure.h>

#include "IService.h"

/******************************************************************************
 * Macros
 *****************************************************************************/

/******************************************************************************
 * Types and Classes
 *****************************************************************************/

/**
 * @enum FhirResourceType
 *
 * @brief FHIR resource types supported by this service.
 */
enum class FhirResourceType
{
    OBSERVATION,  /**< Observation resource */
    PATIENT,      /**< Patient resource */
    DEVICE,       /**< Device resource */
    SUBSCRIPTION, /**< Subscription resource */
    TASK          /**< Task resource */
};

/**
 * @struct FhirResponse
 *
 * @brief Response structure for FHIR operations.
 */
struct FhirResponse
{
    int    httpCode;   /**< HTTP response code */
    String resourceId; /**< Created/updated resource ID */
    String payload;    /**< Response payload (JSON) */
    bool   success;    /**< Operation success flag */
};

/**
 * @class FhirService
 *
 * @brief Singleton service for secure FHIR server communication via HTTPS.
 */
class FhirService : public IService
{
public:

    /**
     * @brief Get the global FhirService instance.
     *
     * @return Reference to the FhirService singleton.
     */
    static FhirService& getInstance()
    {
        static FhirService instance;
        return instance;
    }

    FhirService(const FhirService& service) = delete;
    FhirService& operator=(const FhirService& service) = delete;

    /**
     * @brief Start the FHIR service.
     *
     * @return True on success, false otherwise.
     */
    bool start() final;

    /**
     * @brief Stop the FHIR service.
     */
    void stop() final;

    /**
     * @brief Process service logic (handle WebSocket messages, etc.).
     */
    void process() final;

    /**
     * @brief Create a resource on the FHIR server.
     *
     * @param[in] resourceType Type of FHIR resource to create.
     * @param[in] resourceJson JSON string containing the resource.
     *
     * @return FhirResponse structure with operation result.
     */
    FhirResponse postResource(FhirResourceType resourceType, const String& resourceJson);

    /**
     * @brief Create or update a resource on the FHIR server.
     *
     * @param[in] resourceType Type of FHIR resource to create or update.
     * @param[in] resourceId ID of the resource to update.
     * @param[in] resourceJson JSON string containing the resource.
     *
     * @return FhirResponse structure with operation result.
     */
    FhirResponse putResource(FhirResourceType resourceType, const String& resourceId, const String& resourceJson);

    /**
     * @brief Get a resource from the FHIR server.
     *
     * @param[in] resourceType Type of resource to retrieve.
     * @param[in] resourceId ID of the resource.
     *
     * @return FhirResponse structure with the resource data.
     */
    FhirResponse getResource(FhirResourceType resourceType, const String& resourceId);

private:

    WiFiClientSecure m_wifiClient;  /**< Secure WiFi client */
    String           m_fhirBaseUrl; /**< Base URL of FHIR server */
    String           m_certificate; /**< Server certificate for HTTPS */
    bool             m_isStarted;   /**< Service started flag */

    /**
     * @brief Construct a FhirService object.
     */
    FhirService();

    /**
     * @brief Destroy a FhirService object.
     */
    ~FhirService();

    /**
     * @brief Check server capabilities.
     *
     * @return True if capabilities are sufficient, false otherwise.
     */
    bool checkCapabilities();

    /**
     * @brief Load configuration from ConfigService.
     *
     * @return True if configuration loaded successfully.
     */
    bool loadConfiguration();

    /**
     * @brief Build full URL for a FHIR resource endpoint.
     *
     * @param[in] resourceType Type of resource.
     * @param[in] resourceId Optional resource ID.
     *
     * @return Full URL string.
     */
    String buildUrl(FhirResourceType resourceType, const String& resourceId = "");

    /**
     * @brief Build full URL for a custom path.
     *
     * @param[in] path Path relative to base URL.
     *
     * @return Full URL string.
     */
    String buildUrl(const String& path);

    /**
     * @brief Perform HTTP GET request.
     *
     * @param[in] url Target URL.
     *
     * @return Server response.
     */
    FhirResponse httpGet(const String& url);

    /**
     * @brief Perform HTTP POST request.
     *
     * @param[in] url Target URL.
     * @param[in] payload JSON payload.
     *
     * @return Server response.
     */
    FhirResponse httpPost(const String& url, const String& payload);

    /**
     * @brief Perform HTTP PUT request.
     *
     * @param[in] url Target URL.
     * @param[in] payload JSON payload.
     *
     * @return Server response.
     */
    FhirResponse httpPut(const String& url, const String& payload);

    /**
     * @brief Convert FhirResourceType to string.
     *
     * @param[in] resourceType Resource type enum.
     *
     * @return String representation of resource type.
     */
    String resourceTypeToString(FhirResourceType resourceType)
    {
        String typeStr;

        switch (resourceType)
        {
        case FhirResourceType::OBSERVATION:
            typeStr = "Observation";
            break;
        case FhirResourceType::PATIENT:
            typeStr = "Patient";
            break;
        case FhirResourceType::DEVICE:
            typeStr = "Device";
            break;
        case FhirResourceType::SUBSCRIPTION:
            typeStr = "Subscription";
            break;
        case FhirResourceType::TASK:
            typeStr = "Task";
            break;
        default:
            typeStr = "";
            break;
        }

        return typeStr;
    }
};

/******************************************************************************
 * Functions
 *****************************************************************************/

#endif /* FHIR_SERVICE_H */