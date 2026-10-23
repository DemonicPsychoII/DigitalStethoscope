cmake_minimum_required(VERSION 3.20.0)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(stetho_logic_tests)

target_include_directories(app PRIVATE ../../include)
target_sources(app PRIVATE
    src/test_app_logic.c
    ../../src/app_logic.c
)
