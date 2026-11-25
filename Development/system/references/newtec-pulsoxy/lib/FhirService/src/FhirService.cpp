/*******************************************************************************
    DESCRIPTION
*******************************************************************************/
/**
 * @brief   FHIR server communication service.
 */

/******************************************************************************
 * Includes
 *****************************************************************************/

#include <ArduinoJson.h>
#include <HTTPClient.h>

#include "ConfigService.h"
#include "FhirService.h"

/******************************************************************************
 * Compiler Switches
 *****************************************************************************/

/******************************************************************************
 * Macros
 *****************************************************************************/

/** HTTP timeout in milliseconds */
#define HTTP_TIMEOUT_MS (10000U)

/** JSON content type header */
#define CONTENT_TYPE_JSON ("application/fhir+json")

/** Size of the JSON buffer
 *  According to https://arduinojson.org/v7/assistant/#/step1, our current
 *  Observation resources require approximately 1300 bytes each. 
 *  We allocate 1536 bytes to have some margin for future extensions.
 */
#define JSON_BUFFER_SIZE (1536)

/******************************************************************************
 * Types and Classes
 *****************************************************************************/

/******************************************************************************
 * Prototypes
 *****************************************************************************/

/******************************************************************************
 * Local Variables
 *****************************************************************************/

/******************************************************************************
 * Public Methods
 *****************************************************************************/

bool FhirService::start()
{
    bool ret = false;

    if (m_isStarted)
    {
        ret = true;
    }
    else if (loadConfiguration())
    {
        /* Configure secure client */
        if (m_certificate.length() > 0)
        {
            m_wifiClient.setCACert(m_certificate.c_str());
        }

        /* Check server capabilities */
        if (checkCapabilities())
        {
            m_isStarted = true;
            ret         = true;
        }
    }
    else
    {
        ; /* Nothing to do */
    }

    return ret;
}

void FhirService::process()
{
    /* No periodic processing needed for now */
}

void FhirService::stop()
{
    if (m_isStarted)
    {
        m_wifiClient.stop();
        m_isStarted = false;
    }
}

FhirResponse FhirService::postResource(FhirResourceType resourceType, const String& resourceJson)
{
    String url = buildUrl(resourceType);
    return httpPost(url, resourceJson);
}

FhirResponse FhirService::putResource(FhirResourceType resourceType, const String& resourceId, const String& resourceJson)
{
    String url = buildUrl(resourceType, resourceId);
    return httpPut(url, resourceJson);
}

FhirResponse FhirService::getResource(FhirResourceType resourceType, const String& resourceId)
{
    String url = buildUrl(resourceType, resourceId);
    return httpGet(url);
}

/******************************************************************************
 * Protected Methods
 *****************************************************************************/

/******************************************************************************
 * Private Methods
 *****************************************************************************/

FhirService::FhirService() :
    m_wifiClient(),
    m_fhirBaseUrl(""),
    m_certificate(""),
    m_isStarted(false)
{
}

FhirService::~FhirService()
{
    stop();
}

/** @todo ticket: K11001MEDLINK-25: Implement proper capability checking. */
bool FhirService::checkCapabilities()
{
    HTTPClient client;
    String     metadataUrl = buildUrl("metadata");

    client.begin(m_wifiClient, metadataUrl);
    client.setTimeout(HTTP_TIMEOUT_MS);
    int httpCode = client.GET();
    client.end();

    return (httpCode == HTTP_CODE_OK);
}

bool FhirService::loadConfiguration()
{
    bool result = false;
    ConfigService& configService = ConfigService::getInstance();

    if (configService.open(AccessMode::READ_ONLY))
    {
        m_fhirBaseUrl = configService.get<String>(Config::FHIR_URL);
        m_certificate = configService.get<String>(Config::CERTIFICATE);

        configService.close();

        /* Validate that FHIR URL is configured */
        if (m_fhirBaseUrl.length() > 0)
        {
            result = true;
        }
    }

    return result;
}

String FhirService::buildUrl(FhirResourceType resourceType, const String& resourceId)
{
    String url = m_fhirBaseUrl;

    if (!url.endsWith("/"))
    {
        url += "/";
    }

    url += resourceTypeToString(resourceType);

    if (resourceId.length() > 0)
    {
        url += "/" + resourceId;
    }

    return url;
}

String FhirService::buildUrl(const String& path)
{
    String url = m_fhirBaseUrl;

    if (!url.endsWith("/"))
    {
        url += "/";
    }

    if (path.startsWith("/"))
    {
        url += path.substring(1);
    }
    else
    {
        url += path;
    }

    return url;
}

FhirResponse FhirService::httpGet(const String& url)
{
    FhirResponse response;
    response.success = false;

    HTTPClient client;

    client.begin(m_wifiClient, url);
    client.setTimeout(HTTP_TIMEOUT_MS);
    client.addHeader("Accept", CONTENT_TYPE_JSON);

    response.httpCode = client.GET();
    response.payload  = client.getString();

    if (response.httpCode == HTTP_CODE_OK)
    {
        response.success = true;
    }

    /* Extract resource ID from URL */
    int lastSlash = url.lastIndexOf('/');
    if (lastSlash >= 0)
    {
        response.resourceId = url.substring(lastSlash + 1);
    }

    client.end();

    return response;
}

FhirResponse FhirService::httpPost(const String& url, const String& payload)
{
    FhirResponse response;
    response.success = false;

    HTTPClient client;

    client.begin(m_wifiClient, url);
    client.setTimeout(HTTP_TIMEOUT_MS);
    client.addHeader("Content-Type", CONTENT_TYPE_JSON);
    client.addHeader("Accept", CONTENT_TYPE_JSON);

    response.httpCode = client.POST(payload);
    response.payload  = client.getString();

    if ((response.httpCode == HTTP_CODE_OK) || (response.httpCode == HTTP_CODE_CREATED))
    {
        response.success = true;

        /* Extract resource ID from JSON response */
        DynamicJsonDocument  doc(JSON_BUFFER_SIZE);
        DeserializationError error = deserializeJson(doc, response.payload);

        if (!error && doc.containsKey("id"))
        {
            response.resourceId = doc["id"].as<String>();
        }
    }

    client.end();

    return response;
}

FhirResponse FhirService::httpPut(const String& url, const String& payload)
{
    FhirResponse response;
    response.success = false;

    HTTPClient client;

    client.begin(m_wifiClient, url);
    client.setTimeout(HTTP_TIMEOUT_MS);
    client.addHeader("Content-Type", CONTENT_TYPE_JSON);
    client.addHeader("Accept", CONTENT_TYPE_JSON);

    response.httpCode = client.PUT(payload);
    response.payload  = client.getString();

    if ((response.httpCode == HTTP_CODE_OK) || (response.httpCode == HTTP_CODE_CREATED))
    {
        response.success = true;

        /* Extract resource ID from URL */
        int lastSlash = url.lastIndexOf('/');
        if (lastSlash >= 0)
        {
            response.resourceId = url.substring(lastSlash + 1);
        }
    }

    client.end();

    return response;
}

/******************************************************************************
 * External Functions
 *****************************************************************************/

/******************************************************************************
 * Local Functions
 *****************************************************************************/