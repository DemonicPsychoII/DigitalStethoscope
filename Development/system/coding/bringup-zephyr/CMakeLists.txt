# CMakeLists.txt — Zephyr bring-up test for the digital stethoscope hardware
cmake_minimum_required(VERSION 3.20.0)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(stetho_bringup)

target_include_directories(app PRIVATE include)

# Build identity printed at boot. run_ci.py passes -DSTETHO_BUILD_ID; a plain west build
# reports "local". The cache entry is dropped once read, so reconfiguring the directory
# without the option falls back to "local" instead of keeping an earlier CI identity.
set(STETHO_BUILD_ID_VALUE "local")
if(DEFINED STETHO_BUILD_ID)
  set(STETHO_BUILD_ID_VALUE "${STETHO_BUILD_ID}")
  unset(STETHO_BUILD_ID CACHE)
endif()
if(NOT STETHO_BUILD_ID_VALUE MATCHES "^[A-Za-z0-9 ._:+/-]+$")
  message(FATAL_ERROR "STETHO_BUILD_ID allows only letters, digits, spaces and ._:+/-")
endif()
file(CONFIGURE OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/stetho_build_id.h"
     CONTENT "#define STETHO_BUILD_ID \"@STETHO_BUILD_ID_VALUE@\"\n" @ONLY)
target_include_directories(app PRIVATE "${CMAKE_CURRENT_BINARY_DIR}")

target_sources(app PRIVATE
    src/main.c
    src/app_logic.c
    src/peripherals.c
    src/gpio_inputs.c
    src/analog_backlight.c
    src/display_touch.c
    src/audio_loopback.c
    src/status_reporting.c
    src/stetho_dsp.c
    src/stetho_control.c
    src/stetho_shell.c
    src/stetho_fhir.c
    src/stetho_network.c
)

target_link_libraries(app PRIVATE m)
if(CONFIG_STETHO_NETWORK)
  set(STETHO_CA_HEADER "${CMAKE_CURRENT_BINARY_DIR}/stetho_ca.h")
  if(CONFIG_STETHO_CA_FILE)
    if(NOT EXISTS "${CONFIG_STETHO_CA_FILE}")
      message(FATAL_ERROR "STETHO_CA_FILE does not exist")
    endif()
    set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${CONFIG_STETHO_CA_FILE}")
    file(READ "${CONFIG_STETHO_CA_FILE}" CA_HEX HEX)
    string(REGEX REPLACE "(..)" "0x\\1," CA_BYTES "${CA_HEX}")
    file(WRITE "${STETHO_CA_HEADER}" "static const unsigned char stetho_ca[] = {${CA_BYTES}0};\n")
  else()
    file(WRITE "${STETHO_CA_HEADER}" "static const unsigned char stetho_ca[] = {0};\n")
  endif()
  target_include_directories(app PRIVATE "${CMAKE_CURRENT_BINARY_DIR}")
endif()
