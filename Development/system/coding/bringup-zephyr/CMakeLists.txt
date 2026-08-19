# CMakeLists.txt — Zephyr bring-up test for the digital stethoscope hardware
cmake_minimum_required(VERSION 3.20.0)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(stetho_bringup)

target_include_directories(app PRIVATE include)

target_sources(app PRIVATE
    src/main.c
    src/app_logic.c
    src/peripherals.c
    src/gpio_inputs.c
    src/analog_backlight.c
    src/display_touch.c
    src/audio_loopback.c
    src/status_reporting.c
)
