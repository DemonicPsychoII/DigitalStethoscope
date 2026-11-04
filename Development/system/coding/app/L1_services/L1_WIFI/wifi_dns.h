/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L1_WIFI
 * @{
 * @file
 * Cancellable IPv4 lookup for the WIFI workers, such as time synchronization.
 * Private to L1_WIFI.
 *
 * The resolver may call back before submission returns, and it calls back
 * while holding its own lock. So the lookup is prepared before submission,
 * never submitted or cancelled while the owner's lock is held, and cancelled
 * before its storage is reused: cancel returns only after any callback for the
 * query has finished.
 */

#ifndef L1_WIFI_DNS_H
#define L1_WIFI_DNS_H

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include <stdbool.h>
#include <stdint.h>

#include <zephyr/kernel.h>
#include <zephyr/net/net_ip.h>

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/** One IPv4 lookup of an owning worker; also the resolver's callback context. */
struct wifi_dns_lookup
{
    /* Set once by the owner. */
    struct k_mutex *lock;                   /**< Owner's state lock; protects the fields below it. */
    struct k_event *events;                 /**< Owner's event object. */
    uint32_t resolvedEvent;                 /**< Bit posted when the resolver delivered its terminal status. */
    bool (*isCurrent)(uint32_t generation); /**< Owner's check that the operation is still pending; called with lock held. */

    /* Per lookup, protected by lock. */
    uint32_t generation;            /**< Operation that submitted the query; kept until its callbacks are quiescent. */
    bool addressIsValid;            /**< address holds the first usable IPv4 result. */
    struct net_sockaddr_in address; /**< Owned copy; the resolver's info is valid only during the callback. */
    bool isComplete;                /**< The resolver delivered its terminal status. */
    int result;                     /**< Once complete: 0 with a usable address, or a negative error code. */

    /* Used by the owner's worker only. */
    const char *host;    /**< Name of the submitted query; needed to cancel it. */
    uint16_t identifier; /**< Resolver identifier of the submitted query. */
    bool isSubmitted;    /**< The resolver may still hold the query. */
};

/***********************************************************************/
/* GLOBAL FUNCTION PROTOTYPES                                          */
/***********************************************************************/

/**
 * @brief Resolve a name to its first IPv4 address, checking for cancellation between short waits.
 *
 * Call from the owner's worker, without the owner's lock. Release with
 * wifi_releaseLookup() on every exit, also after success.
 *
 * @param[in,out] lookup             Owner's lookup storage.
 * @param[in]     host               Name to resolve; must stay valid until released.
 * @param[in]     generation         Owning operation.
 * @param[in]     deadline           End of the owner's operation.
 * @param[in]     resolverTimeoutMs  Timeout handed to the resolver.
 * @param[in]     pollIntervalMs     Longest wait between cancellation checks.
 * @param[out]    address            First IPv4 address; written only on success.
 *
 * @return 0 on success, -ECANCELED if the owner's operation ended, -ETIMEDOUT
 *         at the deadline, -ENOENT without an IPv4 record, -EHOSTUNREACH for a
 *         resolver failure, or a negative submission error.
 */
int wifi_resolveIpv4(struct wifi_dns_lookup *lookup,
                     const char *host,
                     uint32_t generation,
                     k_timepoint_t deadline,
                     int32_t resolverTimeoutMs,
                     int32_t pollIntervalMs,
                     struct net_sockaddr_in *address);

/**
 * @brief Cancel the lookup's query; afterwards no resolver callback for it can run.
 *
 * Call from the owner's worker, without the owner's lock.
 *
 * @param[in,out] lookup Owner's lookup storage.
 *
 * @return 0 when no query remains, or the resolver's negative error code.
 */
int wifi_releaseLookup(struct wifi_dns_lookup *lookup);

#endif /* L1_WIFI_DNS_H */

/** @} */
