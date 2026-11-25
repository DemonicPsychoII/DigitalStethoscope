/*******************************************************************************
    DESCRIPTION
*******************************************************************************/
/**
 * @brief   Active measurement state for acquiring sensor data and sending FHIR observations.
 */

/******************************************************************************
 * Includes
 *****************************************************************************/

#include "Board.h"
#include "ConfigService.h"
#include "ConnectedReadyState.h"
#include "FhirResourceFactory.h"
#include "FhirService.h"
#include "IPulseOximeter.h"
#include "Logging.h"
#include "MeasuringState.h"
#include "SensorDataProvider.h"
#include "SimpleTimer.h"

/******************************************************************************
 * Compiler Switches
 *****************************************************************************/

/******************************************************************************
 * Macros
 *****************************************************************************/

#define MEASURING_DURATION_MS (15000U) /**< Measuring duration in ms */

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
void MeasuringState::entry(StateMachine& stateMachine)
{
    m_measuringTimer.start(MEASURING_DURATION_MS);
    if (nullptr != m_pulseOximeter)
    {
        m_pulseOximeter->start(); /*< Due to timing constraints of the used library the sensor has to be started right before processing. */
    }
}

void MeasuringState::process(StateMachine& stateMachine)
{
    m_pulseOximeter->process();

    if (m_measuringTimer.isTimeout())
    {
        /* Transition back to relevant ReadyState */
        switch (m_measurementContext.getMeasurementType())
        {
        case MeasurementType::UNREQUESTED:
            LOG_INFO("MeasuringState: Measurement complete, transitioning to ConnectedReadyState");
            stateMachine.setState(ConnectedReadyState::getInstance());
            break;
        case MeasurementType::REQUESTED:
            LOG_INFO("MeasuringState: Measurement complete, transitioning to ConnectedReadyState");
            stateMachine.setState(ConnectedReadyState::getInstance());
            break;
        case MeasurementType::UNCONNECTED:
            /* Not implemented yet */
            break;
        default:
            break;
        }
    }
}

void MeasuringState::exit(StateMachine& stateMachine)
{
    int heartRate   = m_pulseOximeter->getHeartRate();
    int spo2 = m_pulseOximeter->getSpo2();

    LOG_INFO("Result: Heartrate=" + String(heartRate) + " SpO2=" + String(spo2));

    switch (m_measurementContext.getMeasurementType())
    {
    case MeasurementType::UNREQUESTED:
        sendMeasurements(heartRate, spo2);
        break;
    case MeasurementType::REQUESTED:
        sendMeasurements(heartRate, spo2);
        /* Further handling for requested measurements */
        /* Not implemented yet */
        break;
    case MeasurementType::UNCONNECTED:
        break;
    default:
        break;
    }
}

void MeasuringState::handleButtonEvent(StateMachine& stateMachine, ButtonId buttonId, ButtonEvent buttonEvent)
{
}

MeasurementContext& MeasuringState::getMeasurementContext()
{
    return m_measurementContext;
}

/******************************************************************************
 * Protected Methods
 *****************************************************************************/

/******************************************************************************
 * Private Methods
 *****************************************************************************/

MeasuringState::MeasuringState() :
    m_pulseOximeter(static_cast<IPulseOximeter*>(SensorDataProvider::getInstance().getSensor(0))),
    m_measuringTimer(),
    m_measurementContext()
{
}

MeasuringState::~MeasuringState() = default;

void MeasuringState::sendMeasurements(int heartRate, int spo2)
{
    String patientId     = m_measurementContext.getPatientID();
    String deviceId      = m_measurementContext.getDeviceID();
    /* Create FHIR Observation resources */
    String heartRateJson = FhirResourceFactory::createObservation(
        ObservationType::HEART_RATE,
        patientId, /*< Patient ID */
        heartRate, /*< Heart rate value */
        deviceId   /*< Device ID */
    );

    /* Create SpO2 Observation resource */
    String spo2Json = FhirResourceFactory::createObservation(
        ObservationType::SPO2,
        patientId, /*< Patient ID */
        spo2,      /*< SpO2 value */
        deviceId   /*< Device ID */
    );

    /* Send Heart Rate Observation to FHIR server */
    FhirResponse hrResponse = FhirService::getInstance().postResource(FhirResourceType::OBSERVATION, heartRateJson);
    LOG_INFO("MeasuringState: Heart Rate Observation POST HTTP Code: " + String(hrResponse.httpCode));
    LOG_INFO("MeasuringState: Heart Rate Observation Resource ID: " + hrResponse.resourceId);

    /* Send SpO2 Observation to FHIR server */
    FhirResponse sp02Response = FhirService::getInstance().postResource(FhirResourceType::OBSERVATION, spo2Json);
    LOG_INFO("MeasuringState: SpO2 Observation POST HTTP Code: " + String(sp02Response.httpCode));
    LOG_INFO("MeasuringState: SpO2 Observation Resource ID: " + sp02Response.resourceId);
}
/******************************************************************************
 * External Functions
 *****************************************************************************/

/******************************************************************************
 * Local Functions
 *****************************************************************************/
