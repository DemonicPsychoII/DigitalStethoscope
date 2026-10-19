/* HTTP_RESOURCE_DEFINE() places the setup page resources in a section named after
 * portal_service. Declare this custom service's iterable section so the HTTP
 * server can find its resources through the generated list start/end symbols. */
#include <zephyr/linker/iterable_sections.h>

ITERABLE_SECTION_ROM(http_resource_desc_portal_service, Z_LINK_ITERABLE_SUBALIGN)
