# Generated CMake Pico project file for Multi-box Filament Drybox
cmake_minimum_required(VERSION 3.13)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# == Integrace s Raspberry Pi Pico VS Code rozšířením ==
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
# ====================================================

# Nastavení desky na Pico 2 (RP2350)
set(PICO_BOARD pico2 CACHE STRING "Board type")

# Načtení Pico SDK
include(pico_sdk_import.cmake)

project(drybox_firmware C CXX ASM)

# Inicializace Pico SDK
pico_sdk_init()

# Cílová binárka (shodná s názvem projektu drybox_firmware)
add_executable(drybox_firmware
    main.c
)

pico_set_program_name(drybox_firmware "drybox_firmware")
pico_set_program_version(drybox_firmware "1.0")

# Konfigurace stdio: USB CDC zapnuto, UART stdio vypnuto
pico_enable_stdio_uart(drybox_firmware 0)
pico_enable_stdio_usb(drybox_firmware 1)

# Linkování knihoven z Pico SDK
target_link_libraries(drybox_firmware
    pico_stdlib
    pico_time
    hardware_timer
)

target_include_directories(drybox_firmware PRIVATE
    ${CMAKE_CURRENT_LIST_DIR}
)

# Generování výstupních formátů (.uf2, .hex, .bin, .elf)
pico_add_extra_outputs(drybox_firmware)
