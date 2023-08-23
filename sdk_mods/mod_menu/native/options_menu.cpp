#include "pyunrealsdk/pch.h"
#include "pyunrealsdk/logging.h"
#include "unrealsdk/memory.h"
#include "unrealsdk/unreal/classes/uobject.h"
#include "unrealsdk/unreal/structs/tarray.h"
#include "unrealsdk/unreal/structs/tarray_funcs.h"

using namespace unrealsdk::unreal;
using namespace unrealsdk::memory;

#pragma region Options Menu Entry Clicked

// This signature matches all 6 callbacks for the different option menu entries - they're identical
// save for the constant passed to `SetFirstOptionsToLookAt`
// `SetFirstOptionsToLookAt` is too simple a function to sigscan, so we extract it from this
// Since we fully replicate this function, we also need to find `StartMenuTransition` - might as
// well extract it from this pattern too
const constinit Pattern<66> OPTION_MENU_ENTRY_CLICKED_PATTERN{
    "48 89 5C 24 ??"     // mov [rsp+10], rbx
    "57"                 // push rdi
    "48 83 EC 20"        // sub rsp, 20
    "48 8B F9"           // mov rdi, rcx
    "49 8B D8"           // mov rbx, r8
    "B9 ????????"        // mov ecx, 00000010
    "E8 ????????"        // call Borderlands3.exe+11B2FA0 - UGFxOptionsMenu::SetFirstOptionsToLookAt
    "44 8B 4B ??"        // mov r9d, [rbx+08]
    "4C 8D 87 ????????"  // lea r8, [rdi+00000748] <--- Grab this offset
    "48 8D 54 24 ??"     // lea rdx, [rsp+30]
    "C6 44 24 ?? 0D"     // mov byte ptr [rsp+30], 0D
    "48 8B CF"           // mov rcx, rdi
    "E8 ????????"  // call Borderlands3.exe+1133710 - UGFxMainAndPauseBaseMenu::StartMenuTransition
    "48 8B 5C 24 ??"  // mov rbx, [rsp+38]
    "48 83 C4 20"     // add rsp, 20
    "5F"              // pop rdi
    "C3"              // ret
};
const constexpr auto SET_FIRST_OPTIONS_OFFSET = 22;
const constexpr auto SOFT_OBJECT_OFFSET_OFFSET = 33;
const constexpr auto START_MENU_TRANSITION_OFFSET = 51;

using set_first_options_func = void (*)(uint32_t value);
set_first_options_func set_first_options_ptr;

int32_t soft_object_offset;

using EMenuTransition = uint8_t;
using start_menu_transition_func = void (*)(UObject* self,
                                            EMenuTransition* transition,
                                            void* some_soft_object,
                                            int32_t controller_id);
start_menu_transition_func start_menu_transition_ptr;

#pragma endregion

#pragma region UGFxOptionBase::Refresh

const constinit Pattern<63> OPTION_BASE_REFRESH{
    "40 53"              // push rbx
    "48 83 EC 20"        // sub rsp, 20
    "48 8B D9"           // mov rbx, rcx
    "48 8B 89 ????????"  // mov rcx, [rcx+00000080]
    "48 85 C9"           // test rcx, rcx
    "0F84 ????????"      // je Borderlands3.exe+11B11DF
    "48 89 74 24 ??"     // mov [rsp+30], rsi
    "48 89 7C 24 ??"     // mov [rsp+38], rdi
    "4C 89 74 24 ??"     // mov [rsp+40], r14
    "E8 ????????"        // call Borderlands3.exe+2ECB950
    "48 8B CB"           // mov rcx, rbx
    "E8 ????????"        // call Borderlands3.exe+11B2480
    "48 63 43 ??"        // movsxd rax, dword ptr [rbx+40]
    "33 F6"              // xor esi, esi
    "48 8B 7B ??"        // mov rdi, [rbx+38] <--- Grab this offset
};
const constexpr auto OPTION_LIST_OFFSET_OFFSET = 62;

using option_base_refresh_func = void (*)(UObject* self);
option_base_refresh_func option_base_refresh_ptr;

int8_t option_list_offset;

py::object options_refresh_callback;

void option_base_refresh_hook(UObject* self) {
    auto option_list =
        reinterpret_cast<TArray<UObject*>*>(reinterpret_cast<uintptr_t>(self) + option_list_offset);

    try {
        const py::gil_scoped_acquire gil{};

        auto size = option_list->size();
        py::list options{size};

        for (size_t i = 0; i < size; i++) {
            options[i] = pyunrealsdk::type_casters::cast((*option_list)[i]);
        }

        options_refresh_callback(options);

        size = options.size();
        option_list->resize(size);
        for (size_t i = 0; i < size; i++) {
            (*option_list)[i] = pyunrealsdk::type_casters::cast<UObject*>(options[i]);
        }

    } catch (const std::exception& ex) {
        pyunrealsdk::logging::log_python_exception(ex);
    }

    option_base_refresh_ptr(self);
}

#pragma endregion

// NOLINTNEXTLINE(readability-identifier-length)
PYBIND11_MODULE(options_menu, m) {
    auto option_menu_entry_clicked = OPTION_MENU_ENTRY_CLICKED_PATTERN.sigscan();
    set_first_options_ptr =
        read_offset<set_first_options_func>(option_menu_entry_clicked + SET_FIRST_OPTIONS_OFFSET);
    soft_object_offset =
        *reinterpret_cast<int32_t*>(option_menu_entry_clicked + SOFT_OBJECT_OFFSET_OFFSET);
    start_menu_transition_ptr = read_offset<start_menu_transition_func>(
        option_menu_entry_clicked + START_MENU_TRANSITION_OFFSET);

    auto option_base_refresh = OPTION_BASE_REFRESH.sigscan();
    option_list_offset =
        *reinterpret_cast<int8_t*>(option_base_refresh + OPTION_LIST_OFFSET_OFFSET);
    detour(option_base_refresh, option_base_refresh_hook, &option_base_refresh_ptr,
           "UGFxOptionBase::Refresh");

    m.def(
        "do_options_menu_transition",
        [](py::object self, uint32_t first_option, EMenuTransition transition,
           int32_t controller_id) {
            auto converted_self = pyunrealsdk::type_casters::cast<UObject*>(self);

            set_first_options_ptr(first_option);

            auto soft_object_ptr = reinterpret_cast<void*>(
                reinterpret_cast<uintptr_t>(converted_self) + soft_object_offset);

            start_menu_transition_ptr(converted_self, &transition, soft_object_ptr, controller_id);
        },
        "Performs an options menu transition.\n"
        "\n"
        "Args:\n"
        "    self: The current menu object to perform the transition on.\n"
        "    first_option: The value to set the first option to look at to.\n"
        "    transition: What type of transition to perform.\n"
        "    controller_id: The controller id to perform the transition with.",
        "self"_a, "first_option"_a, "transition"_a = 0xD, "controller_id"_a = 0);

    m.def(
        "set_option_refresh_callback",
        [](py::object callback) { options_refresh_callback = callback; },
        "Sets the callback to use for the option menu refresh.\n"
        "\n"
        "The callback is called with a single positional arg: a list of the intended\n"
        "OptionDescriptionItem. This may be modified in place to affect what items are\n"
        "shown. The return value is ignored.\n"
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
    auto handle = options_refresh_callback.release();
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
