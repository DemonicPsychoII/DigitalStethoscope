/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L1_STORAGE
 * @{
 * @file
 * Implementation of the STORAGE module.
 *
 * Each record is one settings entry on ZMS. A read loads the full record
 * name as the subtree, so ZMS finds the entry by its hash and does not
 * walk all entries.
 */

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include "storage.h"

#include <errno.h>

#include <zephyr/logging/log.h>
#include <zephyr/settings/settings.h>

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/** Result of storage_read(), filled by the settings callback. */
struct storage_read_context
{
    void *data;  /**< Destination of the record. */
    size_t size; /**< Expected record size. */
    int result;  /**< 0 when read, -ENOENT until found, or an error code. */
};

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

/***********************************************************************/
/* LOCAL FUNCTION PROTOTYPES                                           */
/***********************************************************************/

/**
 * @brief Copy the requested record into the read context.
 *
 * Parameters as settings_load_direct_cb.
 *
 * @return 0 to continue loading, as the settings subsystem expects.
 */
static int storage_loadRecord(const char *key, size_t length, settings_read_cb read, void *readArgument, void *parameter);

/***********************************************************************/
/* MACROS                                                              */
/***********************************************************************/

LOG_MODULE_REGISTER(storage, LOG_LEVEL_INF);

/***********************************************************************/
/* GLOBAL FUNCTIONS                                                    */
/***********************************************************************/

int storage_init(void)
{
    int result = settings_subsys_init();

    if(result != 0)
    {
        LOG_ERR("Settings init failed (%d)", result);
    }

    return result;
}

int storage_read(const char *name, void *data, size_t size)
{
    struct storage_read_context context = {.data = data, .size = size, .result = -ENOENT};

    int result = settings_load_subtree_direct(name, storage_loadRecord, &context);

    if(result == 0)
    {
        result = context.result;
    }

    return result;
}

int storage_write(const char *name, const void *data, size_t size)
{
    return settings_save_one(name, data, size);
}

/***********************************************************************/
/* LOCAL FUNCTIONS                                                     */
/***********************************************************************/

static int storage_loadRecord(const char *key, size_t length, settings_read_cb read, void *readArgument, void *parameter)
{
    struct storage_read_context *context = parameter;

    /* The subtree is the full name, so the record itself has no key left;
     * entries below it, such as "<name>/x", are other records. */
    if(key == NULL)
    {
        if(length == 0U)
        {
            context->result = -ENOENT;
        }
        else if(length != context->size)
        {
            /* Stored by another firmware version with a different layout. */
            context->result = -EINVAL;
        }
        else
        {
            ssize_t readLength = read(readArgument, context->data, context->size);

            context->result = (readLength == (ssize_t)context->size) ? 0 : -EIO;
        }
    }

    return 0;
}

/** @} */
