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
 *
 * It also reads the provisioning image from its own read-only partition
 * (design/STORAGE/provisioning.md). It checks the image format and leaves
 * the endpoint and the certificate uninterpreted.
 */

#ifndef L1_STORAGE_H
#define L1_STORAGE_H

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include <stddef.h>
#include <stdint.h>

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

#define STORAGE_PROVISIONING_BASE_URL_MAX_LENGTH    (256)  /**< P28-LIMITS: longest canonical base URL in bytes. */
#define STORAGE_PROVISIONING_CERTIFICATE_MAX_LENGTH (8192) /**< P28-LIMITS: longest PEM certificate in bytes. */

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/** Contents of a valid provisioning image, format version 1. */
struct storage_provisioning
{
    char baseUrl[STORAGE_PROVISIONING_BASE_URL_MAX_LENGTH + 1];        /**< Canonical HTTPS FHIR base URL, NUL-terminated. */
    uint32_t serverKeepAliveSeconds;                                   /**< Server idle connection timeout. */
    char certificate[STORAGE_PROVISIONING_CERTIFICATE_MAX_LENGTH + 1]; /**< PEM public server certificate, NUL-terminated. */
    size_t certificateLength;                                          /**< Certificate length in bytes, without the terminating NUL. */
};

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

/**
 * @brief Read and validate the provisioning image.
 *
 * Checks magic, version, field lengths and the CRC-32 of format version 1.
 * Endpoint and certificate are returned as text without further checks.
 * The firmware never writes the provisioning partition.
 *
 * @param[out] provisioning Destination, about 8.5 KiB; cleared unless the image is valid.
 *
 * @return 0 for a valid image, -ENOENT for an erased partition, -EBADMSG for
 *         any other invalid image, -EINVAL for a NULL destination, or another
 *         negative error code from the flash driver.
 */
int storage_readProvisioning(struct storage_provisioning *provisioning);

#endif /* L1_STORAGE_H */

/** @} */
