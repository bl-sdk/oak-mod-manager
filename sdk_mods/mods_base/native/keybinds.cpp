#include "pyunrealsdk/pch.h"
#include "pyunrealsdk/hooks.h"
#include "pyunrealsdk/logging.h"
#include "pyunrealsdk/type_casters.h"
#include "pyunrealsdk/unreal_bindings/uenum.h"
#include "unrealsdk/memory.h"
#include "unrealsdk/unreal/class_name.h"
#include "unrealsdk/unreal/classes/properties/copyable_property.h"
#include "unrealsdk/unreal/classes/uenum.h"
#include "unrealsdk/unreal/classes/uobject.h"
#include "unrealsdk/unreal/classes/uscriptstruct.h"
#include "unrealsdk/unreal/structs/fname.h"
#include "unrealsdk/unreal/wrappers/wrapped_struct.h"
#include "unrealsdk/unrealsdk.h"

using namespace unrealsdk::memory;
using namespace unrealsdk::unreal;

auto key_struct_type =
    validate_type<UScriptStruct>(unrealsdk::find_object(L"ScriptStruct", L"/Script/InputCore.Key"));
auto key_name_prop = key_struct_type->find_prop_and_validate<UNameProperty>(L"KeyName"_fn);
auto input_event_enum = pyunrealsdk::unreal::enum_as_py_enum(
    validate_type<UEnum>(unrealsdk::find_object(L"Enum", L"/Script/Engine.EInputEvent")));

py::object keybind_callback = py::reinterpret_steal<py::object>(nullptr);

using AOakPlayerController = UObject;
using FKey = void;
using EInputEvent = uint32_t;

using oakpc_inputkey_func = uintptr_t (*)(AOakPlayerController* self,
                                          FKey* key,
                                          EInputEvent input_event,
                                          float press_duration,
                                          uint32_t is_gamepad);
oakpc_inputkey_func oakpc_inputkey_ptr;

const constinit Pattern<11> OAKPC_INPUTKEY_PATTERN{
    "40 55"              // push rbp
    "56"                 // push rsi
    "57"                 // push rdi
    "48 81 EC B0000000"  // sub rsp, 000000B0
};

uintptr_t oakpc_inputkey_hook(AOakPlayerController* self,
                              FKey* key,
                              EInputEvent input_event,
                              float press_duration,
                              uint32_t gamepad_id) {
    if (keybind_callback.ptr() != nullptr) {
        try {
            auto key_name = WrappedStruct{key_struct_type, key}.get<UNameProperty>(key_name_prop);

            const py::gil_scoped_acquire gil{};
            auto pc = pyunrealsdk::type_casters::cast(self);
            auto event_enum = input_event_enum(input_event);

            auto ret = keybind_callback(pc, key_name, event_enum);

            if (pyunrealsdk::hooks::is_block_sentinel(ret)) {
                return 0;
            }

        } catch (const std::exception& ex) {
            pyunrealsdk::logging::log_python_exception(ex);
        }
    }

    return oakpc_inputkey_ptr(self, key, input_event, press_duration, gamepad_id);
}

// NOLINTNEXTLINE(readability-identifier-length)
PYBIND11_MODULE(keybinds, m) {
    detour(OAKPC_INPUTKEY_PATTERN.sigscan(), oakpc_inputkey_hook, &oakpc_inputkey_ptr,
           "OakPlayerController::InputKey");

    m.def(
        "set_keybind_callback", [](const py::object& callback) { keybind_callback = callback; },
        "Sets the keybind callback.\n"
        "\n"
        "The callback takes three positional args:\n"
        "    pc: The OakPlayerController which caused the event.\n"
        "    key: The key which was pressed.\n"
        "    event: Which type of input happened.\n"
        "\n"
        "The callback may return the sentinel `Block` type (or an instance thereof) in\n"
        "order to block normal processing of the key event.\n"
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

    // Release does not decrement the ref counter
    auto handle = keybind_callback.release();
    if (handle.ptr() != nullptr) {
        handle.dec_ref();
    }

    handle = input_event_enum.release();
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
