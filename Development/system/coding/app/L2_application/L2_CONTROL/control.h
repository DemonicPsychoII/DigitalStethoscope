/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @defgroup L2_CONTROL CONTROL
 * @{
 * @file
 * L2 controller; single writer of mode state and owner of the network
 * lease.
 */

#ifndef L2_CONTROL_H
#define L2_CONTROL_H

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

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
 * @brief Initialize the controller, show STARTUP_RUNNING, initialize AUDIO
 * and start the control thread.
 *
 * Call first at boot, so the startup indication covers the
 * initialization of the other components.
 */
void control_init(void);

/**
 * @brief End startup and show IDLE, or the audio error that blocks Start.
 *
 * Blocks until STARTUP_RUNNING has been shown for the P22 lamp test
 * minimum. Afterwards a short button press starts and stops listening.
 */
void control_completeStartup(void);

#endif /* L2_CONTROL_H */

/** @} */
