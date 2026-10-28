/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @defgroup L1_STORAGE STORAGE
 * @{
 * @file
 * L1 adapter over the Zephyr settings subsystem: named records in flash.
 *
 * The module does not know what the records hold. The caller gives the
 * name, the buffer and its size.
 */

#ifndef L1_STORAGE_H
#define L1_STORAGE_H

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include <stddef.h>

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
 * @brief Initialize the settings subsystem and its flash backend.
 *
 * Call once, before any other function of this module.
 *
 * @return 0 on success, or a negative error code.
 */
int storage_init(void);

/**
 * @brief Read a record from flash.
 *
 * @param[in]  name Record name, for example "wifi/network".
 * @param[out] data Destination of the record.
 * @param[in]  size Expected record size in bytes.
 *
 * @return 0 on success, -ENOENT if no record is stored, -EINVAL if the
 *         stored size is different, or a negative error code.
 */
int storage_read(const char *name, void *data, size_t size);

/**
 * @brief Write a record to flash.
 *
 * The record is written as a whole, so the previous record stays valid
 * if the write fails.
 *
 * @param[in] name Record name.
 * @param[in] data Record to store.
 * @param[in] size Record size in bytes.
 *
 * @return 0 on success, or a negative error code.
 */
int storage_write(const char *name, const void *data, size_t size);

#endif /* L1_STORAGE_H */

/** @} */
