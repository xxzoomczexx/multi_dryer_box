# == DO NOT EDIT THE FOLLOWING LINES for the Raspberry Pi Pico VS Code Extension to work ==
if(WIN32)
    set(USERHOME $ENV{USERPROFILE})
else()
    set(USERHOME $ENV{HOME})
endif()
set(sdkVersion 2.3.1)
set(toolchainVersion 15_2_Rel1)
set(picotoolVersion 2.3.1)
set(picoVscode ${USERHOME}/.pico-sdk/cmake/pico-vscode.cmake)
if (EXISTS ${picoVscode})
    include(${picoVscode})
endif()
# ====================================================================================
# Testovaci firmware pro oziveni desky susicky (RP2350A + RM2)
cmake_minimum_required(VERSION 3.13)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Deska je zapojena jako Pico 2 W (krystal 12 MHz, RM2 na GPIO23/24/25/29), jen flash je 16 MB
set(PICO_BOARD pico2_w CACHE STRING "Board type")
set(PICO_FLASH_SIZE_BYTES 16777216)

include(pico_sdk_import.cmake)

project(test_desky C CXX ASM)

pico_sdk_init()

add_executable(test_desky test_desky.c)

pico_set_program_name(test_desky "test_desky")
pico_set_program_version(test_desky "1.0")

target_compile_definitions(test_desky PRIVATE PICO_FLASH_SIZE_BYTES=16777216)

# stdio jen pres UART0 (J2, GPIO0/1) - USB je na desce DNP
pico_enable_stdio_uart(test_desky 1)
pico_enable_stdio_usb(test_desky 0)

target_link_libraries(test_desky
    pico_stdlib
    pico_unique_id
    pico_cyw43_arch_none
    hardware_adc
    hardware_clocks
    hardware_flash
    hardware_pwm
    hardware_watchdog
)

pico_add_extra_outputs(test_desky)
