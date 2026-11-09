/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L1_WIFI
 * @{
 * @file
 * Implementation of the shared cancellable IPv4 lookup.
 */

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include "wifi_dns.h"

#include <errno.h>

#include <zephyr/logging/log.h>
#include <zephyr/net/dns_resolve.h>

/***********************************************************************/
/* LOCAL FUNCTION PROTOTYPES                                           */
/***********************************************************************/

/**
 * @brief Record DNS progress for the owning operation.
 * @param[in] status    Resolver progress or terminal status.
 * @param[in] info      Borrowed address result; may be NULL for terminal callbacks.
 * @param[in] user_data The owner's wifi_dns_lookup.
 */
static void wifi_handleResolution(enum dns_resolve_status status, struct dns_addrinfo *info, void *user_data);

/***********************************************************************/
/* MACROS                                                              */
/***********************************************************************/

LOG_MODULE_REGISTER(wifi_dns, LOG_LEVEL_INF);

/***********************************************************************/
/* GLOBAL FUNCTIONS                                                    */
/***********************************************************************/

int wifi_resolveIpv4(struct wifi_dns_lookup *lookup,
                     const char *host,
                     uint32_t generation,
                     k_timepoint_t deadline,
                     int32_t resolverTimeoutMs,
                     int32_t pollIntervalMs,
                     struct net_sockaddr_in *address)
{
    (void)k_mutex_lock(lookup->lock, K_FOREVER);
    const bool isAdmitted = lookup->isCurrent(generation);
    if(isAdmitted)
    {
        /* Ready before submission: the resolver calls back inline for cached and numeric names. */
        lookup->generation = generation;
        lookup->addressIsValid = false;
        lookup->isComplete = false;
        lookup->result = 0;
        (void)k_event_clear(lookup->events, lookup->resolvedEvent);
    }
    (void)k_mutex_unlock(lookup->lock);

    if(!isAdmitted)
    {
        return -ECANCELED; /**< Cancellation withdrew the operation before DNS. */
    }
    if(sys_timepoint_expired(deadline))
    {
        return -ETIMEDOUT; /**< No budget left for DNS. */
    }

    /* Submitted without the owner's lock: the resolver holds its own lock while calling back, and the callback takes the owner's. */
    uint16_t identifier = 0U;
    int result = dns_get_addr_info(host, DNS_QUERY_TYPE_A, &identifier, wifi_handleResolution, lookup, resolverTimeoutMs);
    if(result != 0)
    {
        return result;
    }
    lookup->host = host;
    lookup->identifier = identifier;
    lookup->isSubmitted = true;

    result = -EAGAIN; /**< DNS is still running. */
    while(result == -EAGAIN)
    {
        (void)k_event_wait(lookup->events, lookup->resolvedEvent, false, K_MSEC(pollIntervalMs));

        (void)k_mutex_lock(lookup->lock, K_FOREVER);
        if(!lookup->isCurrent(generation))
        {
            result = -ECANCELED; /**< Cancellation ended the operation during DNS. */
        }
        else if(lookup->isComplete)
        {
            result = lookup->result;
            if(result == 0)
            {
                *address = lookup->address;
            }
        }
        else if(sys_timepoint_expired(deadline))
        {
            result = -ETIMEDOUT; /**< DNS did not finish within the operation's time. */
        }
        (void)k_mutex_unlock(lookup->lock);
    }

    return result;
}

int wifi_releaseLookup(struct wifi_dns_lookup *lookup)
{
    int result = 0;

    if(lookup->isSubmitted)
    {
        /* The resolver calls back and cancels under its own lock, so after this returns no callback for the query runs.
         * -ENOENT: the query had already ended. */
        const int cancelResult = dns_cancel_addr_info_with_name(lookup->host, DNS_QUERY_TYPE_A, lookup->identifier);
        if((cancelResult == 0) || (cancelResult == -ENOENT))
        {
            lookup->isSubmitted = false;
        }
        else
        {
            result = cancelResult;
        }
    }

    return result;
}

/***********************************************************************/
/* LOCAL FUNCTIONS                                                     */
/***********************************************************************/

static void wifi_handleResolution(enum dns_resolve_status status, struct dns_addrinfo *info, void *user_data)
{
    struct wifi_dns_lookup *lookup = user_data;
    if(lookup == NULL)
    {
        return;
    }

    bool hasFailed = false;
    (void)k_mutex_lock(lookup->lock, K_FOREVER);

    /* The generation check rejects callbacks of an older operation; isComplete keeps the first terminal status. */
    if(lookup->isCurrent(lookup->generation) && !lookup->isComplete)
    {
        if(status == DNS_EAI_INPROGRESS)
        {
            if((info != NULL) && (info->ai_family == NET_AF_INET) && !lookup->addressIsValid)
            {
                lookup->address = *net_sin(&info->ai_addr);
                lookup->addressIsValid = true;
            }
        }
        else
        {
            if(status == DNS_EAI_ALLDONE)
            {
                lookup->result = lookup->addressIsValid ? 0 : -ENOENT; /**< No IPv4 record. */
            }
            else if(status == DNS_EAI_CANCELED)
            {
                /* Cancellation ends the owner's operation first, so a cancel seen here comes from a timeout. */
                lookup->result = -ETIMEDOUT;
            }
            else
            {
                lookup->result = -EHOSTUNREACH; /**< The resolver could not resolve the name. */
            }
            lookup->isComplete = true;
            hasFailed = (lookup->result != 0);
            (void)k_event_post(lookup->events, lookup->resolvedEvent);
        }
    }

    (void)k_mutex_unlock(lookup->lock);

    if(hasFailed)
    {
        LOG_WRN("Name resolution failed (DNS status %d)", status);
    }
}

/** @} */
