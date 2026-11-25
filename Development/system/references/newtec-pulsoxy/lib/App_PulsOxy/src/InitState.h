/*******************************************************************************
    DESCRIPTION
*******************************************************************************/
/**
 * @file    InitState.h
 *
 * @brief   Initialization state for hardware setup, WiFi connection, and FHIR registration.
 */

#ifndef INIT_STATE_H
#define INIT_STATE_H

/******************************************************************************
 * Compile Switches
 *****************************************************************************/

/******************************************************************************
 * Includes
 *****************************************************************************/

#include "StateMachine.h"

/******************************************************************************
 * Macros
 *****************************************************************************/

/******************************************************************************
 * Types and Classes
 *****************************************************************************/

class InitState : public AbstractState
{
public:

    /**
     * @brief Get state instance as singleton.
     *
     * @return State instance
     */
    static InitState& getInstance()
    {
        static InitState instance;
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

    InitState(const InitState& state) = delete;
    InitState& operator=(const InitState& state) = delete;

private:

    /**
     * @brief Construct an InitState.
     */
    InitState();

    /**
     * @brief Destroy an InitState.
     */
    virtual ~InitState();
};

/******************************************************************************
 * Functions
 *****************************************************************************/

#endif /* INIT_STATE_H */