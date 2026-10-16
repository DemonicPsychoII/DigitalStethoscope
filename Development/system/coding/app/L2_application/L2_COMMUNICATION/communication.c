/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L2_COMMUNICATION
 * @{
 * @file
 * Implementation of the COMMUNICATION module.
 *
 * References:
 * - Threads (k_thread_create, stacks, priorities):
 *   https://docs.zephyrproject.org/latest/kernel/services/threads/index.html
 * - Message queues, to pass requests from another thread (for example a
 *   setup page) to this one:
 *   https://docs.zephyrproject.org/latest/kernel/services/data_passing/message_queues.html
 * - Wi-Fi references: see wifi.c.
 */

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include "communication.h"

#include <zephyr/kernel.h>

#include "wifi.h"

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

/* Measure with "kernel thread stacks" before the thread does real work;
 * Wi-Fi requests through net_mgmt need more than this. */
#define COMMUNICATION_THREAD_STACK_SIZE (1024) /**< Stack size for the communication thread. */
#define COMMUNICATION_THREAD_PRIORITY   (10)   /**< Priority for the communication thread. */

K_THREAD_STACK_DEFINE(communication_stack,
                      COMMUNICATION_THREAD_STACK_SIZE); /**< Stack for the communication thread. */

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/***********************************************************************/
/* GLOBAL CONSTANTS                                                    */
/***********************************************************************/

/***********************************************************************/
/* LOCAL CONSTANTS                                                     */
/***********************************************************************/

/***********************************************************************/
/* GLOBAL VARIABLES                                                    */
/***********************************************************************/

/***********************************************************************/
/* LOCAL VARIABLES                                                     */
/***********************************************************************/

static struct k_thread communication_thread_data; /**< Thread data for the communication thread. */

/***********************************************************************/
/* LOCAL FUNCTION PROTOTYPES                                           */
/***********************************************************************/

/**
 * @brief Thread for handling communication tasks.
 *
 * @param[in] arg1 Unused parameter.
 * @param[in] arg2 Unused parameter.
 * @param[in] arg3 Unused parameter.
 */
static void communication_thread(void *arg1, void *arg2, void *arg3);

/***********************************************************************/
/* MACROS                                                              */
/***********************************************************************/

/***********************************************************************/
/* GLOBAL FUNCTIONS                                                    */
/***********************************************************************/

void communication_init(void)
{
    k_thread_create(&communication_thread_data,
                    communication_stack,
                    K_THREAD_STACK_SIZEOF(communication_stack),
                    communication_thread,
                    NULL,
                    NULL,
                    NULL,
                    COMMUNICATION_THREAD_PRIORITY,
                    0,
                    K_FOREVER);

    k_thread_start(&communication_thread_data);
}

/***********************************************************************/
/* LOCAL FUNCTIONS                                                     */
/***********************************************************************/

static void communication_thread(void *arg1, void *arg2, void *arg3)
{
    ARG_UNUSED(arg1);
    ARG_UNUSED(arg2);
    ARG_UNUSED(arg3);

    (void)wifi_init();

    for(;;)
    {
        /* Connection and delivery work goes here. */
        k_sleep(K_SECONDS(1));
    }
}

/** @} */
