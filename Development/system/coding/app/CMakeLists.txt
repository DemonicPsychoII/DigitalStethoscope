cmake_minimum_required(VERSION 3.20.0)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(stethoscope_application)

target_include_directories(app PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/common
    ${CMAKE_CURRENT_SOURCE_DIR}/L1_services/L1_I2S
    ${CMAKE_CURRENT_SOURCE_DIR}/L1_services/L1_WIFI
    ${CMAKE_CURRENT_SOURCE_DIR}/L1_services/L1_PORTAL
    ${CMAKE_CURRENT_SOURCE_DIR}/L1_services/L1_STORAGE
    ${CMAKE_CURRENT_SOURCE_DIR}/L1_services/L1_PHYSICALINTERFACE
    ${CMAKE_CURRENT_SOURCE_DIR}/L1_services/L1_FILTER
    ${CMAKE_CURRENT_SOURCE_DIR}/L1_services/L1_BPM
    ${CMAKE_CURRENT_SOURCE_DIR}/L1_services/L1_FHIR
    ${CMAKE_CURRENT_SOURCE_DIR}/L2_application/L2_CONTROL
    ${CMAKE_CURRENT_SOURCE_DIR}/L2_application/L2_AUDIO
    ${CMAKE_CURRENT_SOURCE_DIR}/L2_application/L2_COMMUNICATION
    ${CMAKE_CURRENT_SOURCE_DIR}/L2_application/L2_SHELL
    ${CMAKE_CURRENT_SOURCE_DIR}/MONITOR
)

target_sources(app PRIVATE
    common/main.c
    L1_services/L1_I2S/i2s.c
    L1_services/L1_WIFI/wifi.c
    L1_services/L1_PORTAL/portal.c
    L1_services/L1_STORAGE/storage.c
    L1_services/L1_PHYSICALINTERFACE/physicalinterface.c
    L1_services/L1_FILTER/filter.c
    L1_services/L1_BPM/bpm.c
    L1_services/L1_FHIR/fhir.c
    L2_application/L2_CONTROL/control.c
    L2_application/L2_AUDIO/audio.c
    L2_application/L2_COMMUNICATION/communication.c
    L2_application/L2_SHELL/shell.c
    MONITOR/monitor.c
)

generate_inc_file_for_target(app
    ${CMAKE_CURRENT_SOURCE_DIR}/L1_services/L1_PORTAL/portal.html
    ${ZEPHYR_BINARY_DIR}/include/generated/portal.html.inc
)

# The setup page resources live in an iterable section named after its HTTP service.
# Follows Zephyr's samples/net/sockets/http_server/CMakeLists.txt and sections-rom.ld.
zephyr_linker_sources(SECTIONS ${CMAKE_CURRENT_SOURCE_DIR}/L1_services/L1_PORTAL/portal-sections.ld)
