#ifndef STETHO_FHIR_H
#define STETHO_FHIR_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
bool stetho_fhir_id_valid(const char *value);
int stetho_fhir_json(char *buffer, size_t capacity, const char *patient, const char *id,
                     const char *timestamp, uint32_t bpm_tenths);
int stetho_network_configure(const char *host, unsigned int port, const char *base,
                             const char *patient);
int stetho_network_token(const char *token);
int stetho_network_send(void);
int stetho_network_time(int64_t epoch);
int stetho_network_sync(const char *host);
void stetho_network_status(int *result, bool *configured, bool *busy);
#endif
