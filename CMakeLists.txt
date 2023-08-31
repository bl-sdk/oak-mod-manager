cmake_minimum_required(VERSION 3.24)

project(oak_mod_manager)

add_subdirectory(pyunrealsdk EXCLUDE_FROM_ALL)

pyunrealsdk_add_module(keybinds sdk_mods/mods_base/native/keybinds.cpp)

pyunrealsdk_add_module(dialog_box sdk_mods/bl3_mod_menu/native/dialog_box.cpp)
pyunrealsdk_add_module(options_getters sdk_mods/bl3_mod_menu/native/options_getters.cpp)
pyunrealsdk_add_module(options_setup sdk_mods/bl3_mod_menu/native/options_setup.cpp)
pyunrealsdk_add_module(options_transition sdk_mods/bl3_mod_menu/native/options_transition.cpp)
pyunrealsdk_add_module(outer_menu sdk_mods/bl3_mod_menu/native/outer_menu.cpp)

install(
    TARGETS
        keybinds
    DESTINATION mods_base/native
)

install(
    TARGETS
        dialog_box
        options_getters
        options_setup
        options_transition
        outer_menu
    DESTINATION bl3_mod_menu/native
)
