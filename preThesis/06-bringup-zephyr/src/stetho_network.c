#include "stetho_fhir.h"
#include <errno.h>
#if defined(CONFIG_STETHO_NETWORK)
#include "audio_loopback.h"
#include "stetho_ca.h"
#include "stetho_control.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/net/sntp.h>
#include <zephyr/net/socket.h>
#include <zephyr/net/tls_credentials.h>
#include <zephyr/random/random.h>
#include <zephyr/sys/clock.h>
LOG_MODULE_REGISTER(stetho_network, LOG_LEVEL_INF);
#define CA_TAG 42
struct network_config {
	char host[128], base[128], patient[65], token[192];
	unsigned int port;
};
static struct network_config config;
struct network_job {
	struct network_config config;
	struct audio_snapshot measurement;
	int64_t epoch;
	char sntp_host[128];
};
K_MSGQ_DEFINE(network_jobs, sizeof(struct network_job), 1, 4);
K_MUTEX_DEFINE(network_lock);
static int last_result;
static bool busy;
static uint32_t boot_nonce;
static bool clean_text(const char *s, const char *extra, size_t limit)
{
	if (!s || !*s || strlen(s) >= limit)
		return false;
	for (; *s; s++)
		if (!((*s >= 'a' && *s <= 'z') || (*s >= 'A' && *s <= 'Z') ||
		      (*s >= '0' && *s <= '9') || strchr(extra, *s)))
			return false;
	return true;
}
int stetho_network_configure(const char *host, unsigned int port, const char *base,
                             const char *patient)
{
	if (!clean_text(host, ".-", sizeof(config.host)) || !port || port > 65535 ||
	    !clean_text(base, "/.-_", sizeof(config.base)) || base[0] != '/' ||
	    !stetho_fhir_id_valid(patient))
		return -EINVAL;
	k_mutex_lock(&network_lock, K_FOREVER);
	snprintf(config.host, sizeof(config.host), "%s", host);
	snprintf(config.base, sizeof(config.base), "%s", base);
	size_t length = strlen(config.base);
	while (length && config.base[length - 1] == '/')
		config.base[--length] = 0;
	snprintf(config.patient, sizeof(config.patient), "%s", patient);
	config.port = port;
	k_mutex_unlock(&network_lock);
	return 0;
}
int stetho_network_token(const char *token)
{
	if (!token || strlen(token) >= sizeof(config.token))
		return -EINVAL;
	for (const char *p = token; *p; p++)
		if (*p < 33 || *p > 126)
			return -EINVAL;
	k_mutex_lock(&network_lock, K_FOREVER);
	snprintf(config.token, sizeof(config.token), "%s", token);
	k_mutex_unlock(&network_lock);
	return 0;
}
int stetho_network_time(int64_t epoch)
{
	if (epoch < 1704067200LL || epoch > 4102444800LL)
		return -EINVAL;
	struct timespec ts = {.tv_sec = epoch};
	return sys_clock_settime(SYS_CLOCK_REALTIME, &ts);
}
static int queue_job(struct network_job *job)
{
	if (busy)
		return -EBUSY;
	int rc = k_msgq_put(&network_jobs, job, K_NO_WAIT);
	if (!rc)
		busy = true;
	return rc;
}
int stetho_network_sync(const char *host)
{
	if (!clean_text(host, ".-", 128))
		return -EINVAL;
	struct network_job job = {0};
	snprintf(job.sntp_host, sizeof(job.sntp_host), "%s", host);
	k_mutex_lock(&network_lock, K_FOREVER);
	int rc = queue_job(&job);
	k_mutex_unlock(&network_lock);
	return rc;
}
int stetho_network_send(void)
{
	struct stetho_settings settings;
	stetho_settings_get(&settings);
	struct network_job job = {0};
	audio_loopback_snapshot(&job.measurement);
	if (!settings.heart || settings.source != SOURCE_MIC || !job.measurement.running ||
	    job.measurement.source != SOURCE_MIC || !job.measurement.bpm_valid ||
	    k_uptime_get_32() - job.measurement.measured_ms > 2500)
		return -ENODATA;
	time_t now = time(NULL);
	if (now < 1704067200LL)
		return -ETIME;
	job.epoch = now - (k_uptime_get_32() - job.measurement.measured_ms) / 1000;
	k_mutex_lock(&network_lock, K_FOREVER);
	job.config = config;
	int rc = !config.host[0] || !config.patient[0] || sizeof(stetho_ca) <= 1 ? -ENOTCONN
	                                                                         : queue_job(&job);
	k_mutex_unlock(&network_lock);
	return rc;
}
void stetho_network_status(int *result, bool *configured, bool *active)
{
	k_mutex_lock(&network_lock, K_FOREVER);
	*result = last_result;
	*active = busy;
	*configured = config.host[0] && config.patient[0] && sizeof(stetho_ca) > 1;
	k_mutex_unlock(&network_lock);
}
static int transmit(const struct network_job *job)
{
	char port[6], id[64], date[21], body[1024], header[768];
	struct tm utc;
	time_t epoch = job->epoch;
	if (!gmtime_r(&epoch, &utc) || !strftime(date, sizeof(date), "%Y-%m-%dT%H:%M:%SZ", &utc))
		return -EINVAL;
	snprintf(id, sizeof(id), "stetho-%08x-%08x", boot_nonce, job->measurement.measured_ms);
	int length = stetho_fhir_json(body, sizeof(body), job->config.patient, id, date,
	                              job->measurement.bpm_tenths);
	if (length < 0)
		return length;
	char auth[224] = "";
	if (job->config.token[0])
		snprintf(auth, sizeof(auth), "Authorization: Bearer %s\r\n", job->config.token);
	int hlen = snprintf(header, sizeof(header),
	                    "PUT %s/Observation/%s HTTP/1.1\r\nHost: %s:%u\r\nContent-Type: "
	                    "application/fhir+json\r\n"
	                    "Accept: application/fhir+json\r\nPrefer: "
	                    "return=minimal\r\n%sContent-Length: %d\r\nConnection: close\r\n\r\n",
	                    job->config.base, id, job->config.host, job->config.port, auth, length);
	if (hlen < 0 || hlen >= (int)sizeof(header))
		return -ENOSPC;
	struct zsock_addrinfo hints = {.ai_family = AF_INET, .ai_socktype = SOCK_STREAM},
	                      *address = NULL;
	snprintf(port, sizeof(port), "%u", job->config.port);
	if (zsock_getaddrinfo(job->config.host, port, &hints, &address) != 0)
		return -EHOSTUNREACH;
	int fd = zsock_socket(AF_INET, SOCK_STREAM, IPPROTO_TLS_1_2);
	if (fd < 0) {
		zsock_freeaddrinfo(address);
		return -errno;
	}
	int verify = TLS_PEER_VERIFY_REQUIRED;
	sec_tag_t tags[] = {CA_TAG};
	struct zsock_timeval timeout = {.tv_sec = 10};
	int rc = 0;
	if (zsock_setsockopt(fd, SOL_TLS, TLS_SEC_TAG_LIST, tags, sizeof(tags)) ||
	    zsock_setsockopt(fd, SOL_TLS, TLS_PEER_VERIFY, &verify, sizeof(verify)) ||
	    zsock_setsockopt(fd, SOL_TLS, TLS_HOSTNAME, job->config.host,
	                     strlen(job->config.host)) ||
	    zsock_setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout)) ||
	    zsock_setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout))) {
		rc = -errno;
		goto done;
	}
	/* The pinned Zephyr TLS driver uses a blocking handshake, including for
	 * nonblocking sockets. Bound TCP/TLS via the explicit network.conf timeouts;
	 * this worker never holds settings or audio locks during network I/O. */
	if (zsock_connect(fd, address->ai_addr, address->ai_addrlen) < 0) {
		rc = -errno;
		goto done;
	}
	const char *parts[] = {header, body};
	size_t sizes[] = {(size_t)hlen, (size_t)length};
	for (size_t p = 0; p < 2; p++) {
		size_t sent = 0;
		while (sent < sizes[p]) {
			int n = zsock_send(fd, parts[p] + sent, sizes[p] - sent, 0);
			if (n <= 0) {
				rc = n ? -errno : -EIO;
				goto done;
			}
			sent += n;
		}
	}
	/* Only the status line is needed for acceptance. Server readback is a
	 * separate host evaluation step; a 2xx response alone is not that proof. */
	char response[128];
	size_t used = 0;
	int status = 0;
	int64_t deadline = k_uptime_get() + 10000;
	while (used < sizeof(response) - 1 && k_uptime_get() < deadline) {
		int n = zsock_recv(fd, response + used, 1, 0);
		if (n <= 0) {
			rc = n ? -errno : -EIO;
			goto done;
		}
		if (response[used++] == '\n')
			break;
	}
	response[used] = 0;
	if (!used || response[used - 1] != '\n' || sscanf(response, "HTTP/1.%*u %d", &status) != 1)
		rc = -EPROTO;
	else if (status == 200 || status == 201) {
		rc = 0;
		LOG_INF("FHIR accepted id=%s HTTP=%d time=%s bpm=%u.%u; read back on server", id,
		        status, date, job->measurement.bpm_tenths / 10,
		        job->measurement.bpm_tenths % 10);
	} else {
		LOG_WRN("FHIR rejected HTTP=%d", status);
		rc = -EIO;
	}
done:
	zsock_freeaddrinfo(address);
	if (zsock_close(fd) < 0 && !rc)
		rc = -errno;
	return rc;
}
static void network_thread(void *a, void *b, void *c)
{
	ARG_UNUSED(a);
	ARG_UNUSED(b);
	ARG_UNUSED(c);
	boot_nonce = sys_rand32_get();
	int credential = sizeof(stetho_ca) > 1
	                         ? tls_credential_add(CA_TAG, TLS_CREDENTIAL_CA_CERTIFICATE,
	                                              stetho_ca, sizeof(stetho_ca))
	                         : -ENOENT;
	struct network_job job;
	while (true) {
		k_msgq_get(&network_jobs, &job, K_FOREVER);
		int rc;
		if (job.sntp_host[0]) {
			struct sntp_time result;
			rc = sntp_simple(job.sntp_host, 5000, &result);
			if (!rc)
				rc = stetho_network_time(result.seconds);
		} else
			rc = credential ? credential : transmit(&job);
		k_mutex_lock(&network_lock, K_FOREVER);
		last_result = rc;
		busy = false;
		k_mutex_unlock(&network_lock);
		LOG_INF("Network job result=%d", rc);
		memset(&job, 0, sizeof(job));
	}
}
K_THREAD_DEFINE(network_thread_id, 10240, network_thread, NULL, NULL, NULL, 12, 0, 0);
#else
int stetho_network_configure(const char *h, unsigned int p, const char *b, const char *id)
{
	(void)h;
	(void)p;
	(void)b;
	(void)id;
	return -ENOTSUP;
}
int stetho_network_token(const char *t)
{
	(void)t;
	return -ENOTSUP;
}
int stetho_network_send(void) { return -ENOTSUP; }
int stetho_network_time(int64_t t)
{
	(void)t;
	return -ENOTSUP;
}
int stetho_network_sync(const char *h)
{
	(void)h;
	return -ENOTSUP;
}
void stetho_network_status(int *r, bool *c, bool *b)
{
	*r = -ENOTSUP;
	*c = false;
	*b = false;
}
#endif
