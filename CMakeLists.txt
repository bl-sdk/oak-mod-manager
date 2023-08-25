cmake_minimum_required(VERSION 3.24)

project(oak_mod_manager)

add_subdirectory(pyunrealsdk EXCLUDE_FROM_ALL)

pyunrealsdk_add_module(keybinds sdk_mods/mod_menu/native/keybinds.cpp)
pyunrealsdk_add_module(options_transition sdk_mods/mod_menu/native/options_transition.cpp)
pyunrealsdk_add_module(outer_menu sdk_mods/mod_menu/native/outer_menu.cpp)

install(
    TARGETS keybinds options_transition outer_menu
    DESTINATION .
)
