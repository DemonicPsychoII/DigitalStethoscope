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
 *
 * The provisioning image is read sequentially from its own partition
 * through the flash map; the CRC-32 accumulates over every byte read.
 */

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include "storage.h"

#include <errno.h>
#include <stdbool.h>
#include <string.h>

#include <zephyr/logging/log.h>
#include <zephyr/settings/settings.h>
#include <zephyr/storage/flash_map.h>
#include <zephyr/sys/byteorder.h>
#include <zephyr/sys/crc.h>

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

#define STORAGE_PROVISIONING_MAGIC        "STPV"  /**< P28-IMAGE: marks a provisioning image. */
#define STORAGE_PROVISIONING_MAGIC_LENGTH (4)     /**< Magic length in bytes, without a NUL. */
#define STORAGE_PROVISIONING_VERSION      (1U)    /**< P28-IMAGE: format version this firmware reads. */
#define STORAGE_ERASED_FLASH_BYTE         (0xFFU) /**< Value of erased NOR flash. */

/** 16 MB flash of the N16R8 module. */
#define STORAGE_FLASH_SIZE (0x1000000U)

/** P28-PARTITION: fixed across firmware versions, so an update still finds the image flashed before it. */
#define STORAGE_PROVISIONING_PARTITION_OFFSET (0xF00000U)

/** Largest image: magic, version, URL length and URL, keep-alive, certificate length and certificate, CRC-32. */
#define STORAGE_PROVISIONING_MAX_SIZE                                                               \
    (STORAGE_PROVISIONING_MAGIC_LENGTH + 1 + 2 + STORAGE_PROVISIONING_BASE_URL_MAX_LENGTH + 4 + 2 + \
     STORAGE_PROVISIONING_CERTIFICATE_MAX_LENGTH + 4)

BUILD_ASSERT(STORAGE_PROVISIONING_MAX_SIZE <= PARTITION_SIZE(provisioning_partition), "The largest provisioning image must fit its partition");
BUILD_ASSERT((PARTITION_OFFSET(storage_partition) + PARTITION_SIZE(storage_partition)) <= PARTITION_OFFSET(provisioning_partition), "Settings must end before the provisioning partition starts");
BUILD_ASSERT(PARTITION_OFFSET(provisioning_partition) == STORAGE_PROVISIONING_PARTITION_OFFSET, "The provisioning partition must keep its fixed start");
BUILD_ASSERT((PARTITION_OFFSET(provisioning_partition) + PARTITION_SIZE(provisioning_partition)) <= STORAGE_FLASH_SIZE, "The provisioning partition must end within the flash");

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

/** Sequential reader over the provisioning partition. */
struct storage_image_reader
{
    const struct flash_area *area; /**< Open provisioning partition. */
    off_t offset;                  /**< Next byte to read. */
    uint32_t checksum;             /**< IEEE CRC-32 over all bytes read so far. */
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

/**
 * @brief Read and check all image fields from the start of the open partition.
 *
 * @param[in,out] reader       Open reader at offset 0.
 * @param[out]    provisioning Destination of the text fields and the keep-alive.
 *
 * @return 0 for a valid image, -ENOENT for an erased partition, -EBADMSG for
 *         any other invalid image, or a negative error code from the flash driver.
 */
static int storage_parseProvisioning(struct storage_image_reader *reader, struct storage_provisioning *provisioning);

/**
 * @brief Read a length field and check it against its limit.
 *
 * @param[in,out] reader        Reader position and checksum.
 * @param[in]     maximumLength Largest allowed value; zero is never allowed.
 * @param[out]    length        Length read.
 *
 * @return 0 if the length is 1 to maximumLength, -EBADMSG otherwise, or a flash driver error.
 */
static int storage_readLength(struct storage_image_reader *reader, uint16_t maximumLength, uint16_t *length);

/**
 * @brief Read the next image bytes and add them to the running CRC-32.
 *
 * @param[in,out] reader Reader position and checksum.
 * @param[out]    data   Destination.
 * @param[in]     size   Number of bytes.
 *
 * @return 0 on success, or a negative error code from the flash driver.
 */
static int storage_readImage(struct storage_image_reader *reader, void *data, size_t size);

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
    struct storage_read_context context = {.data = data, .size = size, .result = -ENOENT}; /**< Requested record or network was not found. */

    int result = settings_load_subtree_direct(name, storage_loadRecord, &context);

    if(result == 0)
    {
        result = context.result;
    }

    return result;
}

int storage_write(const char *name, const void *data, size_t size)
{
    int result = -EINVAL; /**< Invalid argument or unsupported input. */

    /* A zero-length save makes the settings backend delete the record and
     * report success, so reject it before the backend call. */
    if((data != NULL) && (size != 0U))
    {
        result = settings_save_one(name, data, size);
    }

    return result;
}

int storage_readProvisioning(struct storage_provisioning *provisioning)
{
    int result = -EINVAL; /**< Invalid argument or unsupported input. */

    if(provisioning != NULL)
    {
        struct storage_image_reader reader = {.area = NULL, .offset = 0, .checksum = 0U};

        (void)memset(provisioning, 0, sizeof(*provisioning));
        result = flash_area_open(PARTITION_ID(provisioning_partition), &reader.area);

        if(result == 0)
        {
            result = storage_parseProvisioning(&reader, provisioning);
            flash_area_close(reader.area);
        }

        if(result != 0)
        {
            (void)memset(provisioning, 0, sizeof(*provisioning));
        }
    }

    return result;
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
            context->result = -ENOENT; /**< Requested record or network was not found. */
        }
        else if(length != context->size)
        {
            /* Stored by another firmware version with a different layout. */
            context->result = -EINVAL; /**< Invalid argument or unsupported input. */
        }
        else
        {
            ssize_t readLength = read(readArgument, context->data, context->size);

            if(readLength == (ssize_t)context->size)
            {
                context->result = 0;
            }
            else
            {
                context->result = -EIO; /**< Input/output operation failed. */
            }
        }
    }

    return 0;
}

static int storage_parseProvisioning(struct storage_image_reader *reader, struct storage_provisioning *provisioning)
{
    uint8_t magic[STORAGE_PROVISIONING_MAGIC_LENGTH] = {0};
    uint8_t version = 0U;
    uint8_t keepAliveBytes[4] = {0};
    uint8_t checksumBytes[4] = {0};
    uint16_t baseUrlLength = 0U;
    uint16_t certificateLength = 0U;

    int result = storage_readImage(reader, magic, sizeof(magic));

    if(result == 0)
    {
        bool isErased = true;

        for(size_t index = 0U; index < sizeof(magic); index++)
        {
            isErased = isErased && (magic[index] == STORAGE_ERASED_FLASH_BYTE);
        }

        if(isErased)
        {
            result = -ENOENT; /**< No image was flashed. */
        }
        else if(memcmp(magic, STORAGE_PROVISIONING_MAGIC, sizeof(magic)) != 0)
        {
            result = -EBADMSG; /**< Not a provisioning image. */
        }
        else
        {
            result = storage_readImage(reader, &version, sizeof(version));
            if((result == 0) && (version != STORAGE_PROVISIONING_VERSION))
            {
                result = -EBADMSG; /**< Image format this firmware cannot read. */
            }
        }
    }

    if(result == 0)
    {
        result = storage_readLength(reader, STORAGE_PROVISIONING_BASE_URL_MAX_LENGTH, &baseUrlLength);
    }
    if(result == 0)
    {
        result = storage_readImage(reader, provisioning->baseUrl, baseUrlLength);
    }
    if(result == 0)
    {
        result = storage_readImage(reader, keepAliveBytes, sizeof(keepAliveBytes));
        provisioning->serverKeepAliveSeconds = sys_get_le32(keepAliveBytes);
    }
    if(result == 0)
    {
        result = storage_readLength(reader, STORAGE_PROVISIONING_CERTIFICATE_MAX_LENGTH, &certificateLength);
    }
    if(result == 0)
    {
        result = storage_readImage(reader, provisioning->certificate, certificateLength);
    }
    if(result == 0)
    {
        const uint32_t calculatedChecksum = reader->checksum;

        result = storage_readImage(reader, checksumBytes, sizeof(checksumBytes));
        if((result == 0) && (sys_get_le32(checksumBytes) != calculatedChecksum))
        {
            result = -EBADMSG; /**< Corrupted image. */
        }
    }

    /* The text fields are used as C strings, so an embedded NUL would shorten them silently. */
    if((result == 0) && ((strlen(provisioning->baseUrl) != baseUrlLength) || (strlen(provisioning->certificate) != certificateLength)))
    {
        result = -EBADMSG; /**< Length field does not match the text. */
    }
    if(result == 0)
    {
        provisioning->certificateLength = certificateLength;
    }

    return result;
}

static int storage_readLength(struct storage_image_reader *reader, uint16_t maximumLength, uint16_t *length)
{
    uint8_t lengthBytes[2] = {0};

    int result = storage_readImage(reader, lengthBytes, sizeof(lengthBytes));

    if(result == 0)
    {
        *length = sys_get_le16(lengthBytes);
        if((*length == 0U) || (*length > maximumLength))
        {
            result = -EBADMSG; /**< Length out of range. */
        }
    }

    return result;
}

static int storage_readImage(struct storage_image_reader *reader, void *data, size_t size)
{
    int result = flash_area_read(reader->area, reader->offset, data, size);

    if(result == 0)
    {
        reader->offset += (off_t)size;
        reader->checksum = crc32_ieee_update(reader->checksum, data, size);
    }

    return result;
}

/** @} */
