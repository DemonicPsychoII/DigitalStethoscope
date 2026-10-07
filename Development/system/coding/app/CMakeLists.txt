cmake_minimum_required(VERSION 3.20.0)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(stetho_app)

target_include_directories(app PRIVATE common)
target_sources(app PRIVATE
    main.c
    L0_platform/platform.c
    L1_services/audio/audio.c
    L1_services/bpm/bpm.c
    L1_services/storage/storage.c
    L1_services/network/network.c
    L1_services/dsp_core/filter.c
    L1_services/dsp_core/envelope.c
    L1_services/dsp_core/autocorrelation.c
    L1_services/dsp_core/wsola.c
    L2_application/controller/controller.c
    L2_application/ui/ui.c
    L2_application/shell/shell.c
    MON/monitor.c
)
