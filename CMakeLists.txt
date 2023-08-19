cmake_minimum_required(VERSION 3.24)

project(oak_mod_manager)

add_subdirectory(pyunrealsdk EXCLUDE_FROM_ALL)

pyunrealsdk_add_module(native_keybinds sdk_mods/mod_menu/native_keybinds.cpp)
pyunrealsdk_add_module(native_menu sdk_mods/mod_menu/native_menu.cpp)

install(
    TARGETS native_keybinds native_menu
    DESTINATION .
)
