#include "pyunrealsdk/pch.h"
#include "pyunrealsdk/hooks.h"
#include "pyunrealsdk/logging.h"
#include "pyunrealsdk/unreal_bindings/uenum.h"
#include "unrealsdk/memory.h"
#include "unrealsdk/unreal/class_name.h"
#include "unrealsdk/unreal/classes/properties/copyable_property.h"
#include "unrealsdk/unreal/classes/uenum.h"
#include "unrealsdk/unreal/classes/uscriptstruct.h"
#include "unrealsdk/unreal/structs/fname.h"
#include "unrealsdk/unreal/wrappers/wrapped_struct.h"
#include "unrealsdk/unrealsdk.h"

using namespace unrealsdk::memory;
using namespace unrealsdk::unreal;

using FKey = void;
using EInputEvent = uint32_t;

/**
 * @brief Callback for a key input event.
 *
 * @param key The key which had an event.
 * @param input_event What type of event it was.
 * @return True if to block the key event, false otherwise.
 */
using keybind_callback = std::function<bool(FKey* key, EInputEvent input_event)>;

/**
 * @brief Dummy key callback, which does nothing.
 */
bool noop_callback(FKey* /* key */, EInputEvent /* input_event */) {
    return false;
}

keybind_callback gameplay_callback = noop_callback;
keybind_callback menu_callback = noop_callback;

#pragma region PlayerController::InputKey hook

using pc_inputkey_func = uintptr_t (*)(void* self,
                                       FKey* key,
                                       EInputEvent input_event,
                                       float press_duration,
                                       uint32_t gamepad_id);
pc_inputkey_func pc_inputkey_ptr;

const constinit Pattern<24> PC_INPUTKEY_PATTERN{
    "48 8B C4"           // mov rax, rsp
    "48 89 58 ??"        // mov [rax+10], rbx
    "48 89 70 ??"        // mov [rax+18], rsi
    "48 89 78 ??"        // mov [rax+20], rdi
    "41 56"              // push r14
    "48 81 EC 20010000"  // sub rsp, 00000120
};

uintptr_t pc_inputkey_hook(void* self,
                           FKey* key,
                           EInputEvent input_event,
                           float press_duration,
                           uint32_t gamepad_id) {
    if (gameplay_callback(key, input_event)) {
        return 0;
    }

    return pc_inputkey_ptr(self, key, input_event, press_duration, gamepad_id);
}

#pragma endregion

#pragma region UGbxMenuInput::HandleRawInput hook

using menuinput_func = uintptr_t (*)(void* self,
                                     FKey* key,
                                     EInputEvent input_event,
                                     uint32_t gamepad_id);
menuinput_func menuinput_ptr;

const constinit Pattern<17> MENUINPUT_PATTERN{
    "44 89 44 24 ??"     // mov [rsp+18], r8d
    "56"                 // push rsi
    "41 54"              // push r12
    "41 55"              // push r13
    "48 81 EC F0000000"  // sub rsp, 000000F0

};

uintptr_t menuinput_hook(void* self, FKey* key, EInputEvent input_event, uint32_t gamepad_id) {
    if (menu_callback(key, input_event)) {
        return 0;
    }

    return menuinput_ptr(self, key, input_event, gamepad_id);
}

#pragma endregion

// It's safe to call sdk functions statically because everything must already have been initalized
// for us to get loaded
auto key_struct_type =
    validate_type<UScriptStruct>(unrealsdk::find_object(L"ScriptStruct", L"/Script/InputCore.Key"));
auto key_name_prop = key_struct_type->find_prop_and_validate<UNameProperty>(L"KeyName"_fn);
auto input_event_enum = pyunrealsdk::unreal::enum_as_py_enum(
    validate_type<UEnum>(unrealsdk::find_object(L"Enum", L"/Script/Engine.EInputEvent")));

/**
 * @brief Converts a python callback to one we can store.
 *
 * @param callback The python callback to convert.
 * @return The new keybind callback.
 */
keybind_callback convert_py_callback(const py::object& callback) {
    return [callback](FKey* key, EInputEvent input_event) {
        try {
            auto key_name = WrappedStruct{key_struct_type, key}.get<UNameProperty>(key_name_prop);

            const py::gil_scoped_acquire gil{};
            auto event_enum = input_event_enum(input_event);

            return pyunrealsdk::hooks::is_block_sentinel(callback(key_name, event_enum));

        } catch (const std::exception& ex) {
            pyunrealsdk::logging::log_python_exception(ex);
            return false;
        }
    };
}

// NOLINTNEXTLINE(readability-identifier-length)
PYBIND11_MODULE(native_keybinds, m) {
    detour(PC_INPUTKEY_PATTERN.sigscan(), pc_inputkey_hook, &pc_inputkey_ptr,
           "PlayerController::InputKey");
    detour(MENUINPUT_PATTERN.sigscan(), menuinput_hook, &menuinput_ptr,
           "GbxMenuInput::HandleRawInput");

    m.def(
        "set_gameplay_keybind_callback",
        [](const py::object& callback) { gameplay_callback = convert_py_callback(callback); },
        "Sets the callback to use for gameplay keybinds.\n"
        "\n"
        "Keybind callbacks take two positional args:\n"
        "    key: The key which was pressed.\n"
        "    event: Which type of input happened.\n"
        "\n"
        "Keybind callbacks can return the sentinel `Block` type (or an instance thereof)\n"
        "in order to block normal processing of the key event.\n"
        "\n"
        "Args:\n"
        "    callback: The callback to use.",
        "callback"_a);
    m.def(
        "set_menu_keybind_callback",
        [](const py::object& callback) { menu_callback = convert_py_callback(callback); },
        "Sets the callback to use for menu keybinds.\n"
        "\n"
        "Keybind callbacks take two positional args:\n"
        "    key: The key which was pressed.\n"
        "    event: Which type of input happened.\n"
        "\n"
        "Keybind callbacks can return the sentinel `Block` type (or an instance thereof)\n"
        "in order to block normal processing of the key event.\n"
        "\n"
        "Args:\n"
        "    callback: The callback to use.",
        "callback"_a);
}

/**
 * @brief Cleans up the static python references we have, before we're unloaded.
 */
void finalize(void) {
    py::gil_scoped_acquire gil;

    gameplay_callback = noop_callback;
    menu_callback = noop_callback;

    // Release does not decrement the ref counter
    auto handle = input_event_enum.release();
    if (handle.ptr() != nullptr) {
        handle.dec_ref();
    }
}

// NOLINTNEXTLINE(readability-identifier-naming)
BOOL APIENTRY DllMain(HMODULE h_module, DWORD ul_reason_for_call, LPVOID /*unused*/) {
    switch (ul_reason_for_call) {
        case DLL_PROCESS_ATTACH:
            DisableThreadLibraryCalls(h_module);
            break;
        case DLL_PROCESS_DETACH:
            finalize();
            break;
        case DLL_THREAD_ATTACH:
        case DLL_THREAD_DETACH:
            break;
    }
    return TRUE;
}
