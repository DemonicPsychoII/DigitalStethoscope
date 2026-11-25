/*******************************************************************************
    DESCRIPTION
*******************************************************************************/
/**
 * @file    MeasuringState.h
 *
 * @brief   Active measurement state for acquiring sensor data and sending FHIR observations.
 */

#ifndef MEASURING_STATE_H
#define MEASURING_STATE_H

/******************************************************************************
 * Compile Switches
 *****************************************************************************/

/******************************************************************************
 * Includes
 *****************************************************************************/

#include "IPulseOximeter.h"
#include "MeasurementContext.h"
#include "SensorDataProvider.h"
#include "SimpleTimer.h"
#include "StateMachine.h"

/******************************************************************************
 * Macros
 *****************************************************************************/

/******************************************************************************
 * Types and Classes
 *****************************************************************************/

class MeasuringState : public AbstractState
{
public:

    /**
     * @brief Get state instance as singleton.
     *
     * @return State instance
     */
    static MeasuringState& getInstance()
    {
        static MeasuringState instance;
        return instance;
    }

    /**
     * @brief The entry is called once when the state is entered.
     *
     * @param[in] stateMachine Responsible state machine
     */
    void entry(StateMachine& stateMachine) override;

    /**
     * @brief The process routine is called cyclically while the state is active.
     *
     * @param[in] stateMachine Responsible state machine
     */
    void process(StateMachine& stateMachine) override;

    /**
     * @brief The exit is called once when the state is left.
     *
     * @param[in] stateMachine Responsible state machine
     */
    void exit(StateMachine& stateMachine) override;

    /**
     * @brief Handle button event.
     *
     * @param[in] stateMachine Responsible state machine
     * @param[in] buttonId     Button identifier
     * @param[in] buttonEvent  Button event
     */
    void handleButtonEvent(StateMachine& stateMachine, ButtonId buttonId, ButtonEvent buttonEvent) override;

    /**
     * @brief Get the measurement context.
     *
     * @return Reference to the measurement context.
     */
    MeasurementContext& getMeasurementContext();

    MeasuringState(const MeasuringState& state) = delete;
    MeasuringState& operator=(const MeasuringState& state) = delete;

private:

    IPulseOximeter*    m_pulseOximeter;      /**< Pulse oximeter sensor instance */
    SimpleTimer        m_measuringTimer;     /**< Timer for measuring duration */
    MeasurementContext m_measurementContext; /**< Measurement context information */

    /**
     * @brief Construct a MeasuringState.
     */
    MeasuringState();

    /**
     * @brief Destroy a MeasuringState.
     */
    virtual ~MeasuringState();

    /**
     * @brief Send heart rate and SpO2 measurements to FHIR server.
     *
     * @param[in] heartRate Heart rate value in bpm.
     * @param[in] spo2      SpO2 value in percent.
     */
    void sendMeasurements(int heartRate, int spo2);
};

/******************************************************************************
 * Functions
 *****************************************************************************/

#endif /* MEASURING_STATE_H */
