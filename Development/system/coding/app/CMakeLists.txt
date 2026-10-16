cmake_minimum_required(VERSION 3.20.0)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(stetho_app)

target_include_directories(app PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/common
    ${CMAKE_CURRENT_SOURCE_DIR}/L1_services/L1_I2S
    ${CMAKE_CURRENT_SOURCE_DIR}/L1_services/L1_WIFI
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
