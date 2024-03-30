#include "pyunrealsdk/pch.h"
#include "pyunrealsdk/debugging.h"
#include "pyunrealsdk/hooks.h"
#include "pyunrealsdk/logging.h"
#include "pyunrealsdk/static_py_object.h"
#include "pyunrealsdk/type_casters.h"
#include "pyunrealsdk/unreal_bindings/uenum.h"
#include "unrealsdk/memory.h"
#include "unrealsdk/unreal/class_name.h"
#include "unrealsdk/unreal/classes/properties/copyable_property.h"
#include "unrealsdk/unreal/classes/properties/uboolproperty.h"
#include "unrealsdk/unreal/classes/uenum.h"
#include "unrealsdk/unreal/classes/uobject.h"
#include "unrealsdk/unreal/classes/uobject_funcs.h"
#include "unrealsdk/unreal/classes/uscriptstruct.h"
#include "unrealsdk/unreal/structs/fname.h"
#include "unrealsdk/unreal/wrappers/bound_function.h"
#include "unrealsdk/unreal/wrappers/wrapped_struct.h"
#include "unrealsdk/unrealsdk.h"

#include <ranges>

using namespace unrealsdk::memory;
using namespace unrealsdk::unreal;

using AOakPlayerController = UObject;
using EInputEvent = uint32_t;

namespace processing {

pyunrealsdk::StaticPyObject input_event_enum = pyunrealsdk::unreal::enum_as_py_enum(
    validate_type<UEnum>(unrealsdk::find_object(L"Enum", L"/Script/Engine.EInputEvent")));

struct PY_OBJECT_VISIBILITY KeybindData {
    pyunrealsdk::StaticPyObject callback;
    std::optional<EInputEvent> event;
    bool gameplay_bind{};
};

const FName ANY_KEY{0, 0};
std::unordered_multimap<FName, std::shared_ptr<KeybindData>> all_keybinds{};

/**
 * @brief Checks if the given player controller is in a menu.
 *
 * @param player_controller The player controller to check.
 * @return True if in a menu.
 */
bool is_in_menu(AOakPlayerController* player_controller) {
    // WL and BL3 use two different menu systems, so we need to check differently on each of them.
    static auto is_bl3 =
        unrealsdk::utils::get_executable().filename().string() == "Borderlands3.exe";

    if (is_bl3) {
        // This is the more correct method - but it doesn't work under WL
        static auto is_in_menu = validate_type<UFunction>(
            unrealsdk::find_object(L"Function", L"/Script/OakGame.OakPlayerController:IsInMenu"));

        return BoundFunction{is_in_menu, player_controller}.call<UBoolProperty>();

    } else {  // NOLINT(readability-else-after-return)

        // This is less correct, but it seems to work well enough, even works on controller when no
        // cursor is actually drawn
        // Since this uses a generic playercontroller property, rather than something oak-specific,
        // we default to it on unknown executables
        static auto show_mouse_cursor = validate_type<UBoolProperty>(unrealsdk::find_object(
            L"BoolProperty", L"/Script/Engine.PlayerController:bShowMouseCursor"));

        return player_controller->get<UBoolProperty>(show_mouse_cursor);
    }
}

/**
 * @brief Handles a key event.
 *
 * @param player_controller The player controller who pressed the key.
 * @param key_name The key's name.
 * @param input_event What type of event it was.
 * @return True if to block key processing, false to allow it through.
 */
bool handle_key_event(AOakPlayerController* player_controller,
                      FName key_name,
                      EInputEvent input_event) {
    // The original keybind implementation was mostly python. It caused massive lockups if you
    // scrolled, even without freescroll it was relatively easy to trigger half second freezes.

    // In this implementation, we therefore try our best to keep everything as fast as possible,
    // which also means touching python as little as possible

    const auto any_key_match = all_keybinds.equal_range(ANY_KEY);
    const auto specific_key_match = all_keybinds.equal_range(key_name);

    const std::array<std::ranges::subrange<decltype(all_keybinds)::iterator>, 2> both_matches{{
        std::ranges::subrange(any_key_match.first, any_key_match.second),
        std::ranges::subrange(specific_key_match.first, specific_key_match.second),
    }};
    auto with_matching_key = both_matches | std::views::join;

    auto with_matching_event =
        with_matching_key | std::views::filter([input_event](const auto& ittr) {
            auto data = ittr.second;
            return !(data->event.has_value() && data->event != input_event);
        });

    if (with_matching_event.empty()) {
        return false;
    }

    // At this point, the only case where we won't run the callback is if we're in a menu and only
    // have gameplay binds.
    // We need to copy into a vector later, in case the callbacks remove themselves
    // Assuming the range is probably quite small at this point, so iterating through it an extra
    // time now should be faster than doing some allocations.
    const bool has_gameplay_bind = std::ranges::any_of(
        with_matching_event, [](const auto& val) { return val.second->gameplay_bind; });

    // Checking if we're in a menu is potentially slow (it may call an unreal function), so don't
    // need to do it if we don't have any gameplay binds
    auto dont_run_gameplay_binds = !has_gameplay_bind || is_in_menu(player_controller);

    if (dont_run_gameplay_binds) {
        const bool has_raw_bind = std::ranges::any_of(
            with_matching_event, [](const auto& val) { return !val.second->gameplay_bind; });
        if (!has_raw_bind) {
            return false;
        }
    }

    // Now we're definitely going to run the callback, copy into vectors
    std::vector<decltype(all_keybinds)::value_type> raw_binds{};
    std::vector<decltype(all_keybinds)::value_type> gameplay_binds{};
    std::ranges::partition_copy(with_matching_event, std::back_inserter(gameplay_binds),
                                std::back_inserter(raw_binds),
                                [](auto val) { return val.second->gameplay_bind; });

    const py::gil_scoped_acquire gil{};

    // We might be able to get away with skipping creating this enum, saves us some more time.
    py::object event_as_enum{};

    auto run_callbacks = [key_name, &event_as_enum, input_event](auto range) {
        bool should_block = false;
        for (const auto& ittr : range) {
            auto [key, data] = ittr;

            py::list args;
            if (key == ANY_KEY) {
                args.append(key_name);
            }
            if (!data->event.has_value()) {
                if (!event_as_enum) {
                    event_as_enum = input_event_enum(input_event);
                }
                args.append(event_as_enum);
            }

            auto ret = data->callback(*args);
            if (pyunrealsdk::hooks::is_block_sentinel(ret)) {
                should_block = true;
            }
        }
        return should_block;
    };

    if (run_callbacks(raw_binds)) {
        return true;
    }
    if (!dont_run_gameplay_binds && run_callbacks(gameplay_binds)) {
        return true;
    }

    return false;
}

}  // namespace processing

namespace hook {

auto key_struct_type =
    validate_type<UScriptStruct>(unrealsdk::find_object(L"ScriptStruct", L"/Script/InputCore.Key"));
auto key_name_prop = key_struct_type->find_prop_and_validate<UNameProperty>(L"KeyName"_fn);

using FKey = void;
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
    try {
        auto key_name = WrappedStruct{key_struct_type, key}.get<UNameProperty>(key_name_prop);

        if (processing::handle_key_event(self, key_name, input_event)) {
            return 0;
        }

    } catch (const std::exception& ex) {
        pyunrealsdk::logging::log_python_exception(ex);
    }

    return oakpc_inputkey_ptr(self, key, input_event, press_duration, gamepad_id);
}

}  // namespace hook

// NOLINTNEXTLINE(readability-identifier-length)
PYBIND11_MODULE(keybinds, m) {
    detour(hook::OAKPC_INPUTKEY_PATTERN.sigscan(), hook::oakpc_inputkey_hook,
           &hook::oakpc_inputkey_ptr, "OakPlayerController::InputKey");

    m.def(
        "register_keybind",
        [](const std::optional<FName>& key, const std::optional<EInputEvent>& event,
           bool gameplay_bind, const py::object& callback) -> void* {
            auto key_name = key.has_value() ? *key : processing::ANY_KEY;
            auto data = std::make_shared<processing::KeybindData>(callback, event, gameplay_bind);

            processing::all_keybinds.emplace(std::make_pair(key_name, data));
            return data.get();
        },
        "Registers a new keybind.\n"
        "\n"
        "If key or event are None, any key or event will be matched, and their values\n"
        "will be passed back to the callback. Therefore, based on these args, the\n"
        "callback is run with 0-2 arguments.\n"
        "\n"
        "The callback may return the sentinel `Block` type (or an instance thereof) in\n"
        "order to block normal processing of the key event.\n"
        "\n"
        "Args:\n"
        "    key: The key to match, or None to match any.\n"
        "    event: The key event to match, or None to match any.\n"
        "    gameplay_bind: True if this keybind should only trigger during gameplay.\n"
        "    callback: The callback to use.\n"
        "Returns:\n"
        "    An opaque handle to be used in calls to deregister_keybind.",
        "key"_a, "event"_a, "gameplay_bind"_a, "callback"_a);

    m.def(
        "deregister_keybind",
        [](void* handle) {
            std::erase_if(processing::all_keybinds, [handle](const auto& entry) {
                const auto& [key, data] = entry;
                return data.get() == handle;
            });
        },
        "Removes a previously registered keybind.\n"
        "\n"
        "Does nothing if the passed handle is invalid.\n"
        "\n"
        "Args:\n"
        "    handle: The handle returned from `register_keybind`.",
        "handle"_a);

    m.def(
        "_deregister_by_key",
        [](const std::optional<FName>& key) {
            auto key_to_erase = key.has_value() ? *key : processing::ANY_KEY;
            std::erase_if(processing::all_keybinds, [key_to_erase](const auto& entry) {
                const auto& [key_in_map, data] = entry;
                return key_to_erase == key_in_map;
            });
        },
        "Deregisters all keybinds matching the given key.\n"
        "\n"
        "Not intended for regular use, only exists for recovery during debugging, in case\n"
        "a handle was lost.\n"
        "\n"
        "Args:\n"
        "    key: The key to remove all keybinds of.");

    m.def(
        "_deregister_all", []() { processing::all_keybinds.clear(); },
        "Deregisters all keybinds.\n"
        "\n"
        "Not intended for regular use, only exists for recovery during debugging, in case\n"
        "a handle was lost.");
}
