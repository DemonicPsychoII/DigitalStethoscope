/***********************************************************************
 * Copyright DemonicPsychoII
 * Project: DigitalStethoscope
 ***********************************************************************/

/** @addtogroup L1_WIFI
 * @{
 * @file
 * Secure connection to the one provisioned server: DNS, TCP and a TLS 1.3
 * handshake with mandatory server verification (design/COMMUNICATION/secure-transport.md).
 *
 * mbedTLS runs directly over a non-blocking TCP socket. Zephyr's TLS sockets
 * would hold the socket lock for the whole connect and handshake, so a Start
 * could not cancel within the one-second stop bound. Here every wait is a
 * short poll, after which the worker checks for cancellation.
 *
 * Lifecycle as for time synchronization: one operation at a time, claimed by
 * the worker, resources released before the terminal result is published.
 * A successful connection is retained until wifi_closeSecureConnection().
 */

/***********************************************************************/
/* INCLUDES                                                            */
/***********************************************************************/

#include "wifi.h"
#include "wifi_dns.h"

#include <errno.h>
#include <string.h>
#include <strings.h>
#include <time.h>

#include <esp_attr.h>
#include <mbedtls/ssl.h>
#include <mbedtls/x509_crt.h>
#include <psa/crypto.h>

#include <zephyr/logging/log.h>
#include <zephyr/net/net_ip.h>
#include <zephyr/net/socket.h>
#include <zephyr/sys/timeutil.h>

/***********************************************************************/
/* DEFINES                                                             */
/***********************************************************************/

#define WIFI_SECURE_EVENT_COMPLETED BIT(0) /**< Wake secure connection waiters; the protected state holds the result. */
#define WIFI_SECURE_EVENT_RESOLVED  BIT(1) /**< Wake the worker; only DNS has ended. */

#define WIFI_SECURE_STACK_SIZE        (8192) /**< mbedTLS handshake with ECDHE and signature checks; proposed pending target measurement. */
#define WIFI_SECURE_PRIORITY          (10)   /**< Same preemptive priority as the communication thread that waits for it. */
#define WIFI_SECURE_POLL_INTERVAL_MS  (100)  /**< Longest worker wait between cancellation checks, well inside the stop bound. */
#define WIFI_SECURE_CANCEL_TIMEOUT_MS (1000) /**< P23 per-service stop bound. */
#define WIFI_SECURE_HOST_MAX_LENGTH   (253)  /**< Longest DNS name. */
#define WIFI_SECURE_DEFAULT_PORT      (443)  /**< HTTPS. */

/***********************************************************************/
/* TYPES                                                               */
/***********************************************************************/

/** Lifecycle of the single secure connection operation. */
enum wifi_secure_state
{
    WIFI_SECURE_IDLE,       /**< Nothing started since boot. */
    WIFI_SECURE_PENDING,    /**< Started; no terminal result yet. */
    WIFI_SECURE_CANCELLING, /**< Cancellation requested; resources not yet released. */
    WIFI_SECURE_COMPLETED,  /**< Terminal result stored; on success the connection is retained. */
};

/***********************************************************************/
/* LOCAL VARIABLES                                                     */
/***********************************************************************/

K_EVENT_DEFINE(wifi_SecureEvents); /**< WIFI_SECURE_EVENT_* bits. */
K_MUTEX_DEFINE(wifi_SecureLock);   /**< Protects the operation record below. */

static enum wifi_secure_state wifi_SecureState;
static uint32_t wifi_SecureGeneration;    /**< Identifies the accepted operation. */
static bool wifi_SecureIsClaimed;         /**< The worker owns the current operation's resources. */
static k_timepoint_t wifi_SecureDeadline; /**< End of the caller's connection setup. */
static int wifi_SecureResult;             /**< Terminal error code; 0 means connected and verified. */
static enum wifi_secure_connection_cause wifi_SecureCause;
static bool wifi_SecureConnectionIsRetained; /**< The socket and session below form a verified connection. */
/** @brief Tell whether an operation is still the pending one; call with wifi_SecureLock held. */
static bool wifi_isSecureConnectionCurrent(uint32_t generation);

static struct wifi_dns_lookup wifi_SecureServerLookup = {
    .lock = &wifi_SecureLock,
    .events = &wifi_SecureEvents,
    .resolvedEvent = WIFI_SECURE_EVENT_RESOLVED,
    .isCurrent = wifi_isSecureConnectionCurrent,
}; /**< Server lookup; its fields are protected by wifi_SecureLock. */

/* Configured once at boot, read-only afterwards. */
static bool wifi_SecureServerIsConfigured;
static char wifi_SecureHost[WIFI_SECURE_HOST_MAX_LENGTH + 1]; /**< Reference identity and DNS name. */
static uint16_t wifi_SecurePort;
static bool wifi_SecureHostIsAddress;                 /**< wifi_SecureHost is an IPv4 literal. */
static struct net_sockaddr_in wifi_SecureHostAddress; /**< Parsed literal when wifi_SecureHostIsAddress. */
static struct wifi_secure_server wifi_SecureServer;
static mbedtls_x509_crt wifi_TrustedCertificate EXT_RAM_BSS_ATTR;    /**< The provisioned certificate, the only trust anchor. */
static mbedtls_ssl_config wifi_SecureConfiguration EXT_RAM_BSS_ATTR; /**< Client, TLS 1.3 only, verification required. */

/* Owned by the worker during an operation, then by the retained connection. */
static int wifi_SecureSocket = -1;
static mbedtls_ssl_context wifi_SecureSession EXT_RAM_BSS_ATTR;
static bool wifi_SecureSessionIsSetUp;

K_THREAD_STACK_DEFINE(wifi_SecureStack, WIFI_SECURE_STACK_SIZE);
static struct k_work_q wifi_SecureQueue;
static struct k_work wifi_SecureWork;

/***********************************************************************/
/* LOCAL FUNCTION PROTOTYPES                                           */
/***********************************************************************/

/** @brief Run one accepted secure connection on the dedicated work queue. */
static void wifi_runSecureConnection(struct k_work *work);

/** @brief Tell whether the worker may continue the given operation. */
static bool wifi_isSecureConnectionAdmitted(uint32_t generation);

/** @brief Resolve the server name, or use the provisioned IPv4 literal. */
static int wifi_resolveSecureServer(uint32_t generation, k_timepoint_t deadline, struct net_sockaddr_in *address);

/** @brief Connect TCP without blocking, polling in short intervals. */
static int wifi_connectSecureSocket(uint32_t generation, k_timepoint_t deadline, const struct net_sockaddr_in *address);

/** @brief Run the TLS 1.3 handshake step by step, polling in short intervals. */
static int wifi_runHandshake(uint32_t generation, k_timepoint_t deadline, enum wifi_secure_connection_cause *cause);

/**
 * @brief Wait until the socket is ready for the given events.
 * @return 0 when ready, -ECANCELED, -ETIMEDOUT, or a negative socket error.
 */
static int wifi_waitForSocket(uint32_t generation, k_timepoint_t deadline, short events);

/** @brief Release the DNS query, session and socket after a failed or cancelled operation. */
static int wifi_releaseSecureResources(void);

/** @brief Publish a released operation's terminal result. */
static void wifi_publishSecureResult(uint32_t generation, int result, enum wifi_secure_connection_cause cause);

/** @brief mbedTLS send callback over the non-blocking socket. */
static int wifi_sendSecureData(void *context, const unsigned char *data, size_t length);

/** @brief mbedTLS receive callback over the non-blocking socket. */
static int wifi_receiveSecureData(void *context, unsigned char *data, size_t length);

/** @brief Split https://host:port/path into host and port. */
static int wifi_parseBaseUrl(const char *baseUrl);

/** @brief Require a DNS or IP Subject Alternative Name that matches the host. */
static int wifi_checkSubjectAlternativeName(const mbedtls_x509_crt *certificate);

/** @brief Convert an X.509 time to UTC seconds. */
static int64_t wifi_convertCertificateTime(const mbedtls_x509_time *time);

/***********************************************************************/
/* MACROS                                                              */
/***********************************************************************/

LOG_MODULE_REGISTER(wifi_secure, LOG_LEVEL_INF);

/***********************************************************************/
/* GLOBAL FUNCTIONS                                                    */
/***********************************************************************/

int wifi_configureSecureServer(const char *baseUrl, const char *certificate, size_t certificateLength, struct wifi_secure_server *server)
{
    if((baseUrl == NULL) || (certificate == NULL) || (certificateLength == 0U) || (server == NULL))
    {
        return -EINVAL; /**< Invalid argument or unsupported input. */
    }
    if(wifi_SecureServerIsConfigured)
    {
        return -EALREADY; /**< The image is validated once at boot. */
    }

    int result = wifi_parseBaseUrl(baseUrl);
    if(result != 0)
    {
        LOG_WRN("Provisioned base URL unusable (%d)", result);
        return result;
    }

    /* PSA must be ready before parsing keys; repeated initialization is harmless. */
    if(psa_crypto_init() != PSA_SUCCESS)
    {
        return -EIO; /**< Crypto subsystem unavailable. */
    }

    mbedtls_x509_crt_init(&wifi_TrustedCertificate);
    /* Parsing copies the certificate, so the caller's buffer is not borrowed. */
    result = mbedtls_x509_crt_parse(&wifi_TrustedCertificate, (const unsigned char *)certificate, certificateLength);
    if((result != 0) || (wifi_TrustedCertificate.next != NULL))
    {
        LOG_WRN("Provisioned certificate unusable (-0x%04x)", (unsigned int)-result);
        mbedtls_x509_crt_free(&wifi_TrustedCertificate);
        return -EBADMSG; /**< Not exactly one parsable certificate. */
    }

    result = wifi_checkSubjectAlternativeName(&wifi_TrustedCertificate);
    if(result != 0)
    {
        LOG_WRN("Provisioned certificate has no Subject Alternative Name for %s", wifi_SecureHost);
        mbedtls_x509_crt_free(&wifi_TrustedCertificate);
        return result;
    }

    mbedtls_ssl_config_init(&wifi_SecureConfiguration);
    result = mbedtls_ssl_config_defaults(&wifi_SecureConfiguration, MBEDTLS_SSL_IS_CLIENT, MBEDTLS_SSL_TRANSPORT_STREAM, MBEDTLS_SSL_PRESET_DEFAULT);
    if(result != 0)
    {
        mbedtls_x509_crt_free(&wifi_TrustedCertificate);
        mbedtls_ssl_config_free(&wifi_SecureConfiguration);
        return -ENOMEM; /**< mbedTLS could not set up its configuration. */
    }
    /* P26-VERSION: TLS 1.3 only, mandatory server verification, no client certificate. */
    mbedtls_ssl_conf_min_tls_version(&wifi_SecureConfiguration, MBEDTLS_SSL_VERSION_TLS1_3);
    mbedtls_ssl_conf_max_tls_version(&wifi_SecureConfiguration, MBEDTLS_SSL_VERSION_TLS1_3);
    mbedtls_ssl_conf_authmode(&wifi_SecureConfiguration, MBEDTLS_SSL_VERIFY_REQUIRED);
    mbedtls_ssl_conf_ca_chain(&wifi_SecureConfiguration, &wifi_TrustedCertificate, NULL);

    wifi_SecureServer.validFromUtcSeconds = wifi_convertCertificateTime(&wifi_TrustedCertificate.valid_from);
    wifi_SecureServer.validUntilUtcSeconds = wifi_convertCertificateTime(&wifi_TrustedCertificate.valid_to);
    *server = wifi_SecureServer;

    const struct k_work_queue_config queueConfiguration = {
        .name = "wifi_secure_connection",
    };
    k_work_init(&wifi_SecureWork, wifi_runSecureConnection);
    k_work_queue_start(&wifi_SecureQueue, wifi_SecureStack, K_THREAD_STACK_SIZEOF(wifi_SecureStack), WIFI_SECURE_PRIORITY, &queueConfiguration);
    wifi_SecureServerIsConfigured = true;

    return 0;
}

int wifi_startSecureConnection(k_timepoint_t deadline)
{
    if(!wifi_SecureServerIsConfigured)
    {
        return -ENOENT; /**< No provisioned server. */
    }

    int result = 0;
    (void)k_mutex_lock(&wifi_SecureLock, K_FOREVER);

    /* COMPLETED is only reached after release, so CANCELLING keeps Start blocked; a retained connection must be closed first. */
    if((wifi_SecureState == WIFI_SECURE_PENDING) || (wifi_SecureState == WIFI_SECURE_CANCELLING) || wifi_SecureConnectionIsRetained)
    {
        result = -EBUSY; /**< Service is busy with another operation or connection. */
    }
    else
    {
        /* Submitting first leaves the previous record intact if the queue rejects the work. */
        const int submissionResult = k_work_submit_to_queue(&wifi_SecureQueue, &wifi_SecureWork);
        if(submissionResult < 0)
        {
            result = submissionResult;
        }
        else
        {
            wifi_SecureGeneration++;
            wifi_SecureIsClaimed = false;
            wifi_SecureDeadline = deadline;
            wifi_SecureState = WIFI_SECURE_PENDING;
            (void)k_event_clear(&wifi_SecureEvents, WIFI_SECURE_EVENT_COMPLETED);
        }
    }

    (void)k_mutex_unlock(&wifi_SecureLock);
    return result;
}

int wifi_waitForSecureConnection(enum wifi_secure_connection_cause *cause, k_timeout_t timeout)
{
    if(cause == NULL)
    {
        return -EINVAL; /**< Invalid argument or unsupported input. */
    }

    const k_timepoint_t deadline = sys_timepoint_calc(timeout);
    if(k_mutex_lock(&wifi_SecureLock, sys_timepoint_timeout(deadline)) != 0)
    {
        return -EAGAIN; /**< State was busy for this call's whole interval. */
    }
    const enum wifi_secure_state stateBeforeWait = wifi_SecureState;
    const uint32_t awaitedGeneration = wifi_SecureGeneration;
    (void)k_mutex_unlock(&wifi_SecureLock);

    if(stateBeforeWait == WIFI_SECURE_IDLE)
    {
        return -EINVAL; /**< No operation to wait for. */
    }
    if(stateBeforeWait != WIFI_SECURE_COMPLETED)
    {
        /* The event only wakes this call; the protected state decides the result. */
        (void)k_event_wait(&wifi_SecureEvents, WIFI_SECURE_EVENT_COMPLETED, false, sys_timepoint_timeout(deadline));
    }

    if(k_mutex_lock(&wifi_SecureLock, sys_timepoint_timeout(deadline)) != 0)
    {
        return -EAGAIN; /**< State was busy for the rest of this call's interval. */
    }
    int result = -EAGAIN; /**< Still pending after this call's interval. */
    if(wifi_SecureGeneration != awaitedGeneration)
    {
        result = -ECANCELED; /**< A newer Start replaced the awaited operation. */
    }
    else if(wifi_SecureState == WIFI_SECURE_COMPLETED)
    {
        result = wifi_SecureResult;
        *cause = wifi_SecureCause;
    }
    (void)k_mutex_unlock(&wifi_SecureLock);

    return result;
}

int wifi_cancelSecureConnection(void)
{
    const k_timepoint_t deadline = sys_timepoint_calc(K_MSEC(WIFI_SECURE_CANCEL_TIMEOUT_MS));

    if(k_mutex_lock(&wifi_SecureLock, sys_timepoint_timeout(deadline)) != 0)
    {
        return -ETIMEDOUT; /**< Release could not be confirmed within the stop bound. */
    }

    const uint32_t generation = wifi_SecureGeneration;
    bool isWithdrawnBeforeWorker = false;
    if(wifi_SecureState == WIFI_SECURE_PENDING)
    {
        wifi_SecureState = WIFI_SECURE_CANCELLING;
        /* Without a claim the worker owns nothing yet; a handler that runs later sees CANCELLING or COMPLETED and exits. */
        isWithdrawnBeforeWorker = !wifi_SecureIsClaimed;
    }
    const bool isWorkerReleasing = (wifi_SecureState == WIFI_SECURE_CANCELLING) && !isWithdrawnBeforeWorker;
    (void)k_mutex_unlock(&wifi_SecureLock);

    if(isWithdrawnBeforeWorker)
    {
        wifi_publishSecureResult(generation, -ECANCELED, WIFI_SECURE_CONNECTION_CAUSE_CANCELLED);
    }
    else if(isWorkerReleasing)
    {
        /* The worker notices CANCELLING within one poll interval, releases its resources and then publishes. */
        (void)k_event_wait(&wifi_SecureEvents, WIFI_SECURE_EVENT_COMPLETED, false, sys_timepoint_timeout(deadline));
    }

    if(k_mutex_lock(&wifi_SecureLock, sys_timepoint_timeout(deadline)) != 0)
    {
        return -ETIMEDOUT; /**< Release could not be confirmed within the stop bound. */
    }
    const int result = (wifi_SecureState == WIFI_SECURE_CANCELLING) ? -ETIMEDOUT : 0;
    (void)k_mutex_unlock(&wifi_SecureLock);

    return result;
}

int wifi_closeSecureConnection(void)
{
    (void)k_mutex_lock(&wifi_SecureLock, K_FOREVER);
    const bool isRetained = wifi_SecureConnectionIsRetained;
    wifi_SecureConnectionIsRetained = false;
    (void)k_mutex_unlock(&wifi_SecureLock);

    if(isRetained)
    {
        /* One non-blocking attempt; the peer may already be gone, and close must stay inside the stop bound. */
        (void)mbedtls_ssl_close_notify(&wifi_SecureSession);
        (void)wifi_releaseSecureResources();
    }

    return 0;
}

/***********************************************************************/
/* LOCAL FUNCTIONS                                                     */
/***********************************************************************/

static void wifi_runSecureConnection(struct k_work *work)
{
    ARG_UNUSED(work);

    (void)k_mutex_lock(&wifi_SecureLock, K_FOREVER);
    const uint32_t generation = wifi_SecureGeneration;
    const k_timepoint_t deadline = wifi_SecureDeadline;
    /* A handler left queued by an earlier submission must not take over an operation that Cancel withdrew. */
    const bool isClaimed = (wifi_SecureState == WIFI_SECURE_PENDING) && !wifi_SecureIsClaimed;
    if(isClaimed)
    {
        wifi_SecureIsClaimed = true;
    }
    (void)k_mutex_unlock(&wifi_SecureLock);

    if(!isClaimed)
    {
        return;
    }

    enum wifi_secure_connection_cause cause = WIFI_SECURE_CONNECTION_CAUSE_NONE;
    struct net_sockaddr_in address = {0};

    int result = wifi_resolveSecureServer(generation, deadline, &address);
    if(result != 0)
    {
        cause = (result == -ETIMEDOUT) ? WIFI_SECURE_CONNECTION_CAUSE_TIMEOUT : WIFI_SECURE_CONNECTION_CAUSE_RESOLUTION;
    }

    if(result == 0)
    {
        result = wifi_connectSecureSocket(generation, deadline, &address);
        if(result != 0)
        {
            cause = (result == -ETIMEDOUT) ? WIFI_SECURE_CONNECTION_CAUSE_TIMEOUT : WIFI_SECURE_CONNECTION_CAUSE_TCP;
        }
    }

    if(result == 0)
    {
        result = wifi_runHandshake(generation, deadline, &cause);
    }

    if(result == 0)
    {
        /* Proves the resolver is quiescent before the callback context can be reused by a later operation. */
        result = wifi_releaseLookup(&wifi_SecureServerLookup);
        if(result != 0)
        {
            cause = WIFI_SECURE_CONNECTION_CAUSE_RESOLUTION;
        }
    }

    if(result == 0)
    {
        /* Admission, retention and publication form one step, so a Cancel that reports release never leaves a retained connection behind. */
        (void)k_mutex_lock(&wifi_SecureLock, K_FOREVER);
        const bool isAdmitted = wifi_isSecureConnectionCurrent(generation);
        if(isAdmitted)
        {
            /* Only the socket and session remain; the retained connection owns them now. */
            wifi_SecureConnectionIsRetained = true;
            wifi_publishSecureResult(generation, 0, WIFI_SECURE_CONNECTION_CAUSE_NONE);
        }
        (void)k_mutex_unlock(&wifi_SecureLock);

        if(isAdmitted)
        {
            return;
        }
        result = -ECANCELED; /**< Cancellation won over a completed handshake. */
    }

    const int releaseResult = wifi_releaseSecureResources();
    if(releaseResult != 0)
    {
        /* Without proven release the operation never completes: Start stays blocked and Cancel reports the fault. */
        LOG_ERR("Secure connection release failed (%d)", releaseResult);
        return;
    }
    wifi_publishSecureResult(generation, result, cause);
}

static bool wifi_isSecureConnectionCurrent(uint32_t generation)
{
    return (generation == wifi_SecureGeneration) && (wifi_SecureState == WIFI_SECURE_PENDING);
}

static bool wifi_isSecureConnectionAdmitted(uint32_t generation)
{
    (void)k_mutex_lock(&wifi_SecureLock, K_FOREVER);
    const bool isAdmitted = wifi_isSecureConnectionCurrent(generation);
    (void)k_mutex_unlock(&wifi_SecureLock);
    return isAdmitted;
}

static int wifi_resolveSecureServer(uint32_t generation, k_timepoint_t deadline, struct net_sockaddr_in *address)
{
    if(wifi_SecureHostIsAddress)
    {
        *address = wifi_SecureHostAddress;
        return 0;
    }

    const k_timeout_t remaining = sys_timepoint_timeout(deadline);
    if(remaining.ticks <= 0)
    {
        return -ETIMEDOUT; /**< No budget left for DNS. */
    }

    return wifi_resolveIpv4(&wifi_SecureServerLookup,
                            wifi_SecureHost,
                            generation,
                            deadline,
                            (int32_t)k_ticks_to_ms_ceil32(remaining.ticks),
                            WIFI_SECURE_POLL_INTERVAL_MS,
                            address);
}

static int wifi_connectSecureSocket(uint32_t generation, k_timepoint_t deadline, const struct net_sockaddr_in *address)
{
    struct net_sockaddr_in serverAddress = *address;
    serverAddress.sin_port = net_htons(wifi_SecurePort);

    wifi_SecureSocket = zsock_socket(NET_AF_INET, NET_SOCK_STREAM, NET_IPPROTO_TCP);
    if(wifi_SecureSocket < 0)
    {
        return -errno;
    }

    const int flags = zsock_fcntl(wifi_SecureSocket, ZVFS_F_GETFL, 0);
    if((flags < 0) || (zsock_fcntl(wifi_SecureSocket, ZVFS_F_SETFL, flags | ZVFS_O_NONBLOCK) < 0))
    {
        return -errno;
    }

    if(zsock_connect(wifi_SecureSocket, (const struct net_sockaddr *)&serverAddress, sizeof(serverAddress)) == 0)
    {
        return 0;
    }
    if(errno != EINPROGRESS)
    {
        return -errno;
    }

    int result = wifi_waitForSocket(generation, deadline, ZSOCK_POLLOUT);
    if(result == 0)
    {
        int socketError = 0;
        net_socklen_t length = sizeof(socketError);
        if(zsock_getsockopt(wifi_SecureSocket, ZSOCK_SOL_SOCKET, ZSOCK_SO_ERROR, &socketError, &length) < 0)
        {
            result = -errno;
        }
        else if(socketError != 0)
        {
            result = -socketError;
        }
    }

    return result;
}

static int wifi_runHandshake(uint32_t generation, k_timepoint_t deadline, enum wifi_secure_connection_cause *cause)
{
    mbedtls_ssl_init(&wifi_SecureSession);
    wifi_SecureSessionIsSetUp = true;

    int result = mbedtls_ssl_setup(&wifi_SecureSession, &wifi_SecureConfiguration);
    if(result == 0)
    {
        /* The configured host is the reference identity; DNS only changes the destination address. */
        result = mbedtls_ssl_set_hostname(&wifi_SecureSession, wifi_SecureHost);
    }
    if(result != 0)
    {
        *cause = WIFI_SECURE_CONNECTION_CAUSE_CONFIGURATION;
        return -ENOMEM; /**< mbedTLS could not set up the session. */
    }
    mbedtls_ssl_set_bio(&wifi_SecureSession, &wifi_SecureSocket, wifi_sendSecureData, wifi_receiveSecureData, NULL);

    result = mbedtls_ssl_handshake(&wifi_SecureSession);
    while(result != 0)
    {
        short events = 0;
        if(result == MBEDTLS_ERR_SSL_WANT_READ)
        {
            events = ZSOCK_POLLIN;
        }
        else if(result == MBEDTLS_ERR_SSL_WANT_WRITE)
        {
            events = ZSOCK_POLLOUT;
        }
        else if((result == MBEDTLS_ERR_SSL_CRYPTO_IN_PROGRESS) || (result == MBEDTLS_ERR_SSL_ASYNC_IN_PROGRESS))
        {
            events = 0;
        }
        else
        {
            break;
        }

        if(events != 0)
        {
            const int waitResult = wifi_waitForSocket(generation, deadline, events);
            if(waitResult != 0)
            {
                *cause = (waitResult == -ETIMEDOUT)   ? WIFI_SECURE_CONNECTION_CAUSE_TIMEOUT
                         : (waitResult == -ECANCELED) ? WIFI_SECURE_CONNECTION_CAUSE_CANCELLED
                                                      : WIFI_SECURE_CONNECTION_CAUSE_TCP;
                return waitResult;
            }
        }
        else if(!wifi_isSecureConnectionAdmitted(generation))
        {
            *cause = WIFI_SECURE_CONNECTION_CAUSE_CANCELLED;
            return -ECANCELED; /**< Cancellation ended the handshake. */
        }

        result = mbedtls_ssl_handshake(&wifi_SecureSession);
    }

    if(result == 0)
    {
        return 0;
    }

    const uint32_t verification = mbedtls_ssl_get_verify_result(&wifi_SecureSession);
    if((result == MBEDTLS_ERR_X509_CERT_VERIFY_FAILED) || ((verification != 0U) && (verification != (uint32_t)-1)))
    {
        LOG_WRN("Server verification failed (flags 0x%x)", verification);
        *cause = WIFI_SECURE_CONNECTION_CAUSE_TRUST;
        return -EACCES; /**< Certificate, name or validity rejected. */
    }

    LOG_WRN("TLS handshake failed (-0x%04x)", (unsigned int)-result);
    *cause = WIFI_SECURE_CONNECTION_CAUSE_TLS;
    return -EPROTO; /**< Handshake failed, for example no TLS 1.3 or a required client certificate. */
}

static int wifi_waitForSocket(uint32_t generation, k_timepoint_t deadline, short events)
{
    while(true)
    {
        if(!wifi_isSecureConnectionAdmitted(generation))
        {
            return -ECANCELED; /**< Cancellation ended the operation. */
        }
        if(sys_timepoint_expired(deadline))
        {
            return -ETIMEDOUT; /**< Not finished within the setup budget. */
        }

        struct zsock_pollfd descriptor = {.fd = wifi_SecureSocket, .events = events};
        const int ready = zsock_poll(&descriptor, 1, WIFI_SECURE_POLL_INTERVAL_MS);
        if(ready < 0)
        {
            return -errno;
        }
        if(ready > 0)
        {
            if((descriptor.revents & (ZSOCK_POLLERR | ZSOCK_POLLNVAL)) != 0)
            {
                return -ECONNRESET; /**< Socket failed while waiting. */
            }
            /* POLLHUP alone still lets mbedTLS read the remaining data and report the close. */
            return 0;
        }
    }
}

static int wifi_releaseSecureResources(void)
{
    if(wifi_SecureSessionIsSetUp)
    {
        mbedtls_ssl_free(&wifi_SecureSession);
        wifi_SecureSessionIsSetUp = false;
    }

    if(wifi_SecureSocket >= 0)
    {
        (void)zsock_close(wifi_SecureSocket);
        wifi_SecureSocket = -1;
    }

    return wifi_releaseLookup(&wifi_SecureServerLookup);
}

static void wifi_publishSecureResult(uint32_t generation, int result, enum wifi_secure_connection_cause cause)
{
    (void)k_mutex_lock(&wifi_SecureLock, K_FOREVER);

    const bool isUnfinished = (wifi_SecureState == WIFI_SECURE_PENDING) || (wifi_SecureState == WIFI_SECURE_CANCELLING);
    if((generation == wifi_SecureGeneration) && isUnfinished)
    {
        if((wifi_SecureState == WIFI_SECURE_CANCELLING) && (result != 0))
        {
            result = -ECANCELED;
            cause = WIFI_SECURE_CONNECTION_CAUSE_CANCELLED;
        }
        wifi_SecureResult = result;
        wifi_SecureCause = cause;
        wifi_SecureState = WIFI_SECURE_COMPLETED;
        /* Stays set until the next accepted Start, so repeated Wait calls return at once. */
        (void)k_event_post(&wifi_SecureEvents, WIFI_SECURE_EVENT_COMPLETED);
    }

    (void)k_mutex_unlock(&wifi_SecureLock);
}

static int wifi_sendSecureData(void *context, const unsigned char *data, size_t length)
{
    const int socket = *(const int *)context;
    const ssize_t sent = zsock_send(socket, data, length, ZSOCK_MSG_DONTWAIT);
    if(sent >= 0)
    {
        return (int)sent;
    }
    return ((errno == EAGAIN) || (errno == EWOULDBLOCK)) ? MBEDTLS_ERR_SSL_WANT_WRITE : MBEDTLS_ERR_SSL_INTERNAL_ERROR;
}

static int wifi_receiveSecureData(void *context, unsigned char *data, size_t length)
{
    const int socket = *(const int *)context;
    const ssize_t received = zsock_recv(socket, data, length, ZSOCK_MSG_DONTWAIT);
    if(received > 0)
    {
        return (int)received;
    }
    if(received == 0)
    {
        return MBEDTLS_ERR_SSL_CONN_EOF;
    }
    return ((errno == EAGAIN) || (errno == EWOULDBLOCK)) ? MBEDTLS_ERR_SSL_WANT_READ : MBEDTLS_ERR_SSL_INTERNAL_ERROR;
}

static int wifi_parseBaseUrl(const char *baseUrl)
{
    static const char scheme[] = "https://";
    if(strncmp(baseUrl, scheme, sizeof(scheme) - 1U) != 0)
    {
        return -EINVAL; /**< Only HTTPS; no plain-HTTP fallback. */
    }

    const char *host = baseUrl + (sizeof(scheme) - 1U);
    if(*host == '[')
    {
        return -EINVAL; /**< IPv6 literals are outside this version; the station resolves IPv4. */
    }

    const char *hostEnd = host;
    while((*hostEnd != '\0') && (*hostEnd != ':') && (*hostEnd != '/'))
    {
        hostEnd++;
    }
    const size_t hostLength = (size_t)(hostEnd - host);
    if((hostLength == 0U) || (hostLength > WIFI_SECURE_HOST_MAX_LENGTH))
    {
        return -EINVAL; /**< Missing or overlong host. */
    }

    uint32_t port = WIFI_SECURE_DEFAULT_PORT;
    if(*hostEnd == ':')
    {
        port = 0U;
        const char *digit = hostEnd + 1;
        while((*digit >= '0') && (*digit <= '9') && (port <= 65535U))
        {
            port = (port * 10U) + (uint32_t)(*digit - '0');
            digit++;
        }
        if((digit == hostEnd + 1) || (port == 0U) || (port > 65535U) || ((*digit != '\0') && (*digit != '/')))
        {
            return -EINVAL; /**< Invalid port. */
        }
    }

    (void)memcpy(wifi_SecureHost, host, hostLength);
    wifi_SecureHost[hostLength] = '\0';
    wifi_SecurePort = (uint16_t)port;

    struct net_in_addr literal = {0};
    wifi_SecureHostIsAddress = (net_addr_pton(NET_AF_INET, wifi_SecureHost, &literal) == 0);
    if(wifi_SecureHostIsAddress)
    {
        wifi_SecureHostAddress = (struct net_sockaddr_in){.sin_family = NET_AF_INET, .sin_addr = literal};
    }

    return 0;
}

static int wifi_checkSubjectAlternativeName(const mbedtls_x509_crt *certificate)
{
    /* Without a SAN extension mbedTLS falls back to the Common Name, which RFC 9525 and the design exclude. */
    if(mbedtls_x509_crt_has_ext_type(certificate, MBEDTLS_X509_EXT_SUBJECT_ALT_NAME) == 0)
    {
        return -EBADMSG; /**< No Subject Alternative Name. */
    }

    const size_t hostLength = strlen(wifi_SecureHost);
    bool isMatched = false;

    for(const mbedtls_x509_sequence *entry = &certificate->subject_alt_names; (entry != NULL) && !isMatched; entry = entry->next)
    {
        mbedtls_x509_subject_alternative_name name;
        if(mbedtls_x509_parse_subject_alt_name(&entry->buf, &name) != 0)
        {
            continue;
        }

        const mbedtls_x509_buf *value = &name.san.unstructured_name;
        if((name.type == MBEDTLS_X509_SAN_DNS_NAME) && !wifi_SecureHostIsAddress && (value->len == hostLength))
        {
            /* Exact match only; wildcard names are left to mbedTLS's own check of the peer. */
            isMatched = (strncasecmp((const char *)value->p, wifi_SecureHost, hostLength) == 0);
        }
        else if((name.type == MBEDTLS_X509_SAN_IP_ADDRESS) && wifi_SecureHostIsAddress && (value->len == sizeof(wifi_SecureHostAddress.sin_addr.s4_addr)))
        {
            isMatched = (memcmp(value->p, wifi_SecureHostAddress.sin_addr.s4_addr, value->len) == 0);
        }
        mbedtls_x509_free_subject_alt_name(&name);
    }

    return isMatched ? 0 : -EBADMSG; /**< No SAN matches the configured host. */
}

static int64_t wifi_convertCertificateTime(const mbedtls_x509_time *time)
{
    struct tm calendar = {
        .tm_year = time->year - 1900,
        .tm_mon = time->mon - 1,
        .tm_mday = time->day,
        .tm_hour = time->hour,
        .tm_min = time->min,
        .tm_sec = time->sec,
    };
    return timeutil_timegm64(&calendar);
}

/** @} */
