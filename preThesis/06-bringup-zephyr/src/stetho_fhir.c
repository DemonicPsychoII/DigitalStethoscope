#include "stetho_fhir.h"
#include <errno.h>
#include <stdio.h>
#include <string.h>
bool stetho_fhir_id_valid(const char *s)
{
	if (!s || !*s || strlen(s) > 64)
		return false;
	for (; *s; s++)
		if (!((*s >= 'a' && *s <= 'z') || (*s >= 'A' && *s <= 'Z') ||
		      (*s >= '0' && *s <= '9') || *s == '-' || *s == '.'))
			return false;
	return true;
}
int stetho_fhir_json(char *buf, size_t n, const char *patient, const char *id, const char *date,
                     uint32_t bpm)
{
	if (!buf || !n || !stetho_fhir_id_valid(patient) || !stetho_fhir_id_valid(id) || !date ||
	    strlen(date) != 20 || bpm < 300 || bpm > 2000)
		return -EINVAL;
	/* Timestamp must be the fixed UTC representation, never arbitrary JSON. */
	for (size_t i = 0; i < 20; i++) {
		char c = date[i];
		char expected = i == 4 || i == 7     ? '-'
		                : i == 10            ? 'T'
		                : i == 13 || i == 16 ? ':'
		                : i == 19            ? 'Z'
		                                     : 0;
		if (expected ? c != expected : c < '0' || c > '9')
			return -EINVAL;
	}
	int written =
	        snprintf(buf, n,
	                 "{\"resourceType\":\"Observation\",\"id\":\"%s\",\"meta\":{\"profile\":["
	                 "\"http://hl7.org/fhir/StructureDefinition/heartrate\"]},"
	                 "\"status\":\"final\",\"category\":[{\"coding\":[{\"system\":\"http://"
	                 "terminology.hl7.org/CodeSystem/"
	                 "observation-category\",\"code\":\"vital-signs\"}]}],"
	                 "\"code\":{\"coding\":[{\"system\":\"http://"
	                 "loinc.org\",\"code\":\"8867-4\",\"display\":\"Heart rate\"}]},"
	                 "\"subject\":{\"reference\":\"Patient/%s\"},\"effectiveDateTime\":\"%s\","
	                 "\"valueQuantity\":{\"value\":%u.%u,\"unit\":\"beats/"
	                 "minute\",\"system\":\"http://unitsofmeasure.org\",\"code\":\"/min\"}}",
	                 id, patient, date, bpm / 10, bpm % 10);
	return written < 0 || (size_t)written >= n ? -ENOSPC : written;
}
