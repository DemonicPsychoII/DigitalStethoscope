/*******************************************************************************
    DESCRIPTION
*******************************************************************************/
/**
 * @brief   Initialization state for hardware setup, WiFi connection, and FHIR registration.
 */
/******************************************************************************
 * Includes
 *****************************************************************************/

#include <WiFi.h>

#include "Board.h"
#include "ButtonDriver.h"
#include "ConfigService.h"
#include "ConfigState.h"
#include "ConnectedReadyState.h"
#include "ErrorState.h"
#include "FhirResourceFactory.h"
#include "FhirService.h"
#include "InitState.h"
#include "Logging.h"
#include "SensorDataProvider.h"

/******************************************************************************
 * Compiler Switches
 *****************************************************************************/

/******************************************************************************
 * Macros
 *****************************************************************************/

#define WIFI_CONNECTION_TIMEOUT_MS (5000U) /**< WiFi connection timeout */
#define CONFIG_MODE_DELAY_MS (1000U)    /**< Delay to allow user input */

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

void InitState::entry(StateMachine& stateMachine)
{
    bool           initError     = false;
    ConfigService& configService = ConfigService::getInstance();
    
    /* Ensure WiFi is off */
    WiFi.softAPdisconnect(true);
    WiFi.mode(WIFI_OFF);

    /* Initialize board hardware */
    if (!Board::getInstance().init())
    {
        LOG_ERROR("InitState: Failed to initialize Board");
        initError = true;
    }
    /* Initialize ConfigService */
    else if (!configService.start())
    {
        LOG_ERROR("InitState: Failed to start ConfigService");
        initError = true;
    }
    /* Initialize ButtonDriver */
    else if (!ButtonDriver::getInstance().init())
    {
        LOG_ERROR("InitState: Failed to initialize ButtonDriver");
        initError = true;
    }
    /* Initialize SensorDataProvider */
    else if (!SensorDataProvider::getInstance().start())
    {
        LOG_ERROR("InitState: Failed to start SensorDataProvider");
        initError = true;
    }
    else
    {
        /* Nothing to do */
    }

    /* Small delay to allow user to press the configuration button */
    delay(CONFIG_MODE_DELAY_MS);
    /* Check if configuration mode is requested */
    if (ButtonDriver::getInstance().getState(CONFIG_BUTTON_INDEX) == ButtonState::BUTTON_STATE_PRESSED)
    {
        LOG_INFO("InitState: Configuration mode requested");

        stateMachine.setState(ConfigState::getInstance());
    }
    else
    {
        /* Initialize WiFi */
        if (!initError)
        {
            configService.open(AccessMode::READ_ONLY);
            String wifiSSID     = configService.get<String>(Config::WIFI_SSID);
            String wifiPassword = configService.get<String>(Config::WIFI_PASSWORD);
            String ntpServer    = configService.get<String>(Config::NTP_SERVER);
            String timezone     = configService.get<String>(Config::TIMEZONE);
            String deviceId     = configService.get<String>(Config::DEVICE_ID);
            configService.close();
    
            WiFi.mode(WIFI_STA);
            WiFi.begin(wifiSSID.c_str(), wifiPassword.c_str());
    
            /* Wait for WiFi connection */
            if (WiFi.waitForConnectResult(WIFI_CONNECTION_TIMEOUT_MS) == WL_CONNECTED)
            {
                /* Set system time */
                configTzTime(timezone.c_str(), ntpServer.c_str());
            }
            else
            {
                LOG_ERROR("InitState: Failed to connect to WiFi");
                initError = true;
            }
            /* Initialize FhirService */
            if (!initError)
            {
                if (!FhirService::getInstance().start())
                {
                    LOG_ERROR("InitState: Failed to start FhirService");
                    initError = true;
                }
                else
                {
                    configService.open(AccessMode::READ_ONLY);
                    String patientId = configService.get<String>(Config::PATIENT_ID);
                    configService.close();

                    /* Create and send patient resource to FHIR server */
                    String patientResource = FhirResourceFactory::createPatient(
                        patientId,
                        "Mustermann",
                        "Max");

                    FhirResponse patientResponse = FhirService::getInstance().putResource(
                        FhirResourceType::PATIENT,
                        patientId,
                        patientResource);

                    if (patientResponse.success)
                    {
                        LOG_INFO("InitState: Patient resource registered successfully");
                    }
                    else
                    {
                        LOG_ERROR("InitState: Failed to register patient resource");
                        LOG_ERROR("InitState: HTTP Code: " + String(patientResponse.httpCode));
                    }

                    /* Create and send device resource to FHIR server */
                    String deviceResource = FhirResourceFactory::createDevice(
                        deviceId,
                        "NewTec GmbH",
                        "PulsOxy-ESP32",
                        deviceId);
    
                    FhirResponse deviceResponse = FhirService::getInstance().putResource(
                        FhirResourceType::DEVICE,
                        deviceId,
                        deviceResource);
    
                    if (deviceResponse.success)
                    {
                        LOG_INFO("InitState: Device resource registered successfully");
                    }
                    else
                    {
                        LOG_ERROR("InitState: Failed to register device resource");
                        LOG_ERROR("InitState: HTTP Code: " + String(deviceResponse.httpCode));
                    }
                }
            }
        }
    
        if (!initError)
        {
            LOG_INFO("InitState: Initialization successful, transitioning to ConnectedReadyState");
            stateMachine.setState(ConnectedReadyState::getInstance());
        }
        else
        {
            LOG_ERROR("InitState: Initialization failed, transitioning to ErrorState");
            stateMachine.setState(ErrorState::getInstance());
        }
    }
}

void InitState::process(StateMachine& stateMachine)
{
    /* Nothing to do */
}

void InitState::exit(StateMachine& stateMachine)
{
    /* Nothing to do */
}

void InitState::handleButtonEvent(StateMachine& stateMachine, ButtonId buttonId, ButtonEvent buttonEvent)
{
    /* Nothing to do */
}

/******************************************************************************
 * Protected Methods
 *****************************************************************************/

/******************************************************************************
 * Private Methods
 *****************************************************************************/

InitState::InitState() = default;

InitState::~InitState() = default;

/******************************************************************************
 * External Functions
 *****************************************************************************/

/******************************************************************************
 * Local Functions
 *****************************************************************************/