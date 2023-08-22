#include "pyunrealsdk/pch.h"
#include <vadefs.h>
#include "unrealsdk/memory.h"
#include "unrealsdk/unreal/classes/uobject.h"

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
    "4C 8D 87 ????????"  // lea r8, [rdi+00000748] <--- This offset
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

// NOLINTNEXTLINE(readability-identifier-length)
PYBIND11_MODULE(options_menu, m) {
    auto option_menu_entry_clicked = OPTION_MENU_ENTRY_CLICKED_PATTERN.sigscan();
    set_first_options_ptr =
        read_offset<set_first_options_func>(option_menu_entry_clicked + SET_FIRST_OPTIONS_OFFSET);
    soft_object_offset =
        *reinterpret_cast<int32_t*>(option_menu_entry_clicked + SOFT_OBJECT_OFFSET_OFFSET);
    start_menu_transition_ptr = read_offset<start_menu_transition_func>(
        option_menu_entry_clicked + START_MENU_TRANSITION_OFFSET);

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
}
