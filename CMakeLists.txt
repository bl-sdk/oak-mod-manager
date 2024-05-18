cmake_minimum_required(VERSION 3.24)

project(oak_mod_manager)

set(UNREALSDK_ARCH x64)
set(UNREALSDK_UE_VERSION UE4)
set(EXPLICIT_PYTHON_ARCH amd64)
set(EXPLICIT_PYTHON_VERSION 3.12.3)

add_subdirectory(libs/pyunrealsdk)

add_subdirectory(libs/pluginloader EXCLUDE_FROM_ALL)
set_target_properties(pluginloader_dsound PROPERTIES EXCLUDE_FROM_ALL 0)

pyunrealsdk_add_module(dialog_box src/bl3_mod_menu/native/dialog_box.cpp)
pyunrealsdk_add_module(options_getters src/bl3_mod_menu/native/options_getters.cpp)
pyunrealsdk_add_module(options_setup src/bl3_mod_menu/native/options_setup.cpp)
pyunrealsdk_add_module(options_transition src/bl3_mod_menu/native/options_transition.cpp)
pyunrealsdk_add_module(outer_menu src/bl3_mod_menu/native/outer_menu.cpp)

pyunrealsdk_add_module(keybinds src/keybinds/keybinds.cpp)

install(
    TARGETS
        pluginloader_dsound
    RUNTIME DESTINATION
        .exe_folder
)

install(
    TARGETS
        dialog_box
        options_getters
        options_setup
        options_transition
        outer_menu
    DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/src/bl3_mod_menu/native
)

install(
    TARGETS
        keybinds
    DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/src/keybinds/
)
