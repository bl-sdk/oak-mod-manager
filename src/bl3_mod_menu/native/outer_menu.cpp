#include "pyunrealsdk/pch.h"
#include "pyunrealsdk/debugging.h"
#include "pyunrealsdk/logging.h"
#include "pyunrealsdk/static_py_object.h"
#include "unrealsdk/hook_manager.h"
#include "unrealsdk/memory.h"
#include "unrealsdk/unreal/classes/properties/uobjectproperty.h"
#include "unrealsdk/unreal/classes/uobject.h"
#include "unrealsdk/unreal/structs/fname.h"
#include "unrealsdk/unreal/structs/ftext.h"
#include "unrealsdk/unreal/wrappers/wrapped_struct.h"

using namespace unrealsdk::unreal;
using namespace unrealsdk::memory;

pyunrealsdk::StaticPyObject add_menu_item_callback{};

#pragma region UGFxMainAndPauseBaseMenu::AddMenuItem

using add_menu_item_func =
    int32_t(UObject* self, FText* text, FName callback_name, bool big, int32_t always_minus_one);

add_menu_item_func* add_menu_item_ptr;

const constinit Pattern<40> ADD_MENU_ITEM_PATTERN{
    "48 89 54 24 ??"        // mov [rsp+10], rdx
    "48 89 4C 24 ??"        // mov [rsp+08], rcx
    "55"                    // push rbp
    "53"                    // push rbx
    "56"                    // push rsi
    "57"                    // push rdi
    "41 55"                 // push r13
    "41 56"                 // push r14
    "41 57"                 // push r15
    "48 8D 6C 24 ??"        // lea rbp, [rsp-1F]
    "48 81 EC E0000000"     // sub rsp, 000000E0
    "48 83 B9 ???????? 00"  // cmp qword ptr [rcx+00000980], 00
};

int32_t add_menu_item_hook(UObject* self,
                           FText* text,
                           FName callback_name,
                           bool big,
                           int32_t always_minus_one) {
    if (always_minus_one != -1) {
        LOG(DEV_WARNING,
            "UGFxMainAndPauseBaseMenu::AddMenuItem::always_minus_one was not -1 when called with "
            "'{}' '{}' {}",
            (std::string)*text, callback_name, big);
    }

    if (add_menu_item_callback) {
        try {
            const py::gil_scoped_acquire gil{};
            pyunrealsdk::debug_this_thread();

            auto converted_self = pyunrealsdk::type_casters::cast(self);

            auto ret = add_menu_item_callback(converted_self, (std::string)*text, callback_name,
                                              big, always_minus_one);

            return py::cast<int32_t>(ret);

        } catch (const std::exception& ex) {
            pyunrealsdk::logging::log_python_exception(ex);
        }
    }

    return add_menu_item_ptr(self, text, callback_name, big, always_minus_one);
}

#pragma endregion

#pragma region UGFxMainAndPauseBaseMenu::BeginConfigureMenuItems

using begin_configure_menu_items_func = void (*)(UObject* self);

const constinit Pattern<16> BEGIN_CONFIGURE_MENU_ITEMS_PATTERN{
    "40 53"              // push rbx
    "48 83 EC 20"        // sub rsp, 20
    "48 8B D9"           // mov rbx, rcx
    "48 81 C1 A0080000"  // add rcx, 000008A0
};

begin_configure_menu_items_func begin_configure_menu_items_ptr =
    reinterpret_cast<begin_configure_menu_items_func>(BEGIN_CONFIGURE_MENU_ITEMS_PATTERN.sigscan(
        "UGFxMainAndPauseBaseMenu::BeginConfigureMenuItems"));

#pragma endregion

#pragma region UGFxMainAndPauseBaseMenu::SetMenuState

using set_menu_state_func = void (*)(UObject* self, int32_t value);

const constinit Pattern<27> SET_MENU_STATE_PATTERN{
    "48 89 5C 24 ??"     // mov [rsp+08], rbx
    "48 89 74 24 ??"     // mov [rsp+10], rsi
    "57"                 // push rdi
    "48 83 EC 20"        // sub rsp, 20
    "48 63 B9 ????????"  // movsxd rdi, dword ptr [rcx+0000089C] <--- Grab this offset
    "8B F2"              // mov esi, edx
    "48 8B 01"           // mov rax, [rcx]
};
const constexpr auto MENU_STATE_OFFSET_OFFSET = 18;

set_menu_state_func set_menu_state_ptr =
    SET_MENU_STATE_PATTERN.sigscan<set_menu_state_func>("UGFxMainAndPauseBaseMenu::SetMenuStatec");
int32_t menu_state_offset = *reinterpret_cast<int32_t*>(
    reinterpret_cast<uintptr_t>(set_menu_state_ptr) + MENU_STATE_OFFSET_OFFSET);

#pragma endregion

// NOLINTNEXTLINE(readability-identifier-length)
PYBIND11_MODULE(outer_menu, m) {
    detour(ADD_MENU_ITEM_PATTERN, add_menu_item_hook, &add_menu_item_ptr,
           "UGFxMainAndPauseBaseMenu::AddMenuItem");

    m.def(
        "add_menu_item",
        [](const py::object& self, const std::string& text, FName callback_name, bool big,
           int32_t always_minus_one) {
            auto converted_self = pyunrealsdk::type_casters::cast<UObject*>(self);
            FText converted_text{text};

            return add_menu_item_ptr(converted_self, &converted_text, callback_name, big,
                                     always_minus_one);
        },
        "Calls GFxMainAndPauseBaseMenu::AddMenuItem. This does not trigger a callback.\n"
        "\n"
        "Args:\n"
        "    self: The object to call on.\n"
        "    text: The text to display in the menu.\n"
        "    callback_name: The name of the unreal callback to use.\n"
        "    big: True if the menu item should be big.\n"
        "    always_minus_one: Always -1. ¯\\_(ツ)_/¯\n"
        "Returns:\n"
        "    The index of the inserted menu item.",
        "self"_a, "text"_a, "callback_name"_a, "big"_a, "always_minus_one"_a);

    m.def(
        "set_add_menu_item_callback",
        [](const py::object& callback) { add_menu_item_callback = callback; },
        "Sets the callback to use when GFxMainAndPauseBaseMenu::AddMenuItem is called.\n"
        "\n"
        "This callback will be passed all 5 args positionally, and must return the return\n"
        "value to use - i.e. a no-op callback is `lambda *args: add_menu_item(*args)`.\n"
        "\n"
        "Args:\n"
        "    callback: The callback to use.",
        "callback"_a);

    m.def(
        "begin_configure_menu_items",
        [](const py::object& self) {
            begin_configure_menu_items_ptr(pyunrealsdk::type_casters::cast<UObject*>(self));
        },
        "Calls GFxMainAndPauseBaseMenu::AddMenuItem.\n"
        "\n"
        "Args:\n"
        "    self: The object to call on.",
        "self"_a);

    m.def(
        "set_menu_state",
        [](const py::object& self, int32_t state) {
            set_menu_state_ptr(pyunrealsdk::type_casters::cast<UObject*>(self), state);
        },
        "Calls GFxMainAndPauseBaseMenu::SetMenuState.\n"
        "\n"
        "Args:\n"
        "    self: The object to call on.\n"
        "    state: The state to set the menu to.",
        "self"_a, "state"_a);

    m.def(
        "get_menu_state",
        [](const py::object& self) {
            auto obj = pyunrealsdk::type_casters::cast<UObject*>(self);
            return *reinterpret_cast<int32_t*>(reinterpret_cast<uintptr_t>(obj)
                                               + menu_state_offset);
        },
        "Gets the menu state, which was previously set by a call to set menu state.\n"
        "\n"
        "Args:\n"
        "    self: The object to get the state of.\n"
        "Returns:\n"
        "    The object's menu state.");
}
