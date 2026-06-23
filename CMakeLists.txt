cmake_minimum_required(VERSION 3.25)

project(oak_mod_manager)

set(UNREALSDK_FLAVOUR OAK)
set(EXPLICIT_PYTHON_ARCH amd64)
set(EXPLICIT_PYTHON_VERSION 3.14.6)
set(EXPLICIT_PYTHON_HASH_BASE SHA256=75afa83f93b284d19040e24bc440ab741c09582c0d5310504d607a4e08c3dbaf)
set(EXPLICIT_PYTHON_HASH_TEST SHA256=2e903c82f7fc7081aa59e21752309dd6a1180297950d6b0587c39da606549867)
set(EXPLICIT_PYTHON_HASH_EMBEDDABLE SHA256=c3a89aa7ead530bcac4729f3db7d000fbadb6ca7aa0461c2841867172aa0752a)

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
