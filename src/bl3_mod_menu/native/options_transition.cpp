#include "pyunrealsdk/pch.h"
#include "pyunrealsdk/debugging.h"
#include "pyunrealsdk/logging.h"
#include "pyunrealsdk/static_py_object.h"
#include "unrealsdk/memory.h"
#include "unrealsdk/unreal/classes/properties/copyable_property.h"
#include "unrealsdk/unreal/classes/properties/uenumproperty.h"
#include "unrealsdk/unreal/classes/properties/uobjectproperty.h"
#include "unrealsdk/unreal/classes/properties/ustructproperty.h"
#include "unrealsdk/unreal/classes/uobject.h"
#include "unrealsdk/unreal/classes/uobject_funcs.h"
#include "unrealsdk/unreal/classes/uscriptstruct.h"
#include "unrealsdk/unreal/find_class.h"
#include "unrealsdk/unreal/structs/ftext.h"
#include "unrealsdk/unreal/structs/tarray.h"
#include "unrealsdk/unreal/structs/tarray_funcs.h"
#include "unrealsdk/unrealsdk.h"

using namespace unrealsdk::unreal;
using namespace unrealsdk::memory;

namespace {

namespace transition {

// This signature matches all 6 callbacks for the different option menu entries - they're identical
// save for the constant passed to `SetFirstOptionsToLookAt`
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

using option_menu_type = uint32_t;
using set_first_options_func = void (*)(option_menu_type type);

using EMenuTransition = uint8_t;
using UGFxMainAndPauseBaseMenu = UObject;
using start_menu_transition_func = void (*)(UGFxMainAndPauseBaseMenu* self,
                                            EMenuTransition* transition,
                                            void* some_soft_object,
                                            int32_t controller_id);

set_first_options_func set_first_options_ptr;
int32_t soft_object_offset;
start_menu_transition_func start_menu_transition_ptr;

// The accessibility menu is important for reasons discussed later
const constexpr auto ACCESSIBILITY_OPTION_MENU_TYPE = 16;

/**
 * @brief Performs all required setup needed to be able to start a options transition.
 */
void setup(void) {
    auto option_menu_entry_clicked =
        OPTION_MENU_ENTRY_CLICKED_PATTERN.sigscan("UGFxMainAndPauseBaseMenu::On[menu]Clicked");
    set_first_options_ptr =
        read_offset<set_first_options_func>(option_menu_entry_clicked + SET_FIRST_OPTIONS_OFFSET);
    soft_object_offset =
        *reinterpret_cast<int32_t*>(option_menu_entry_clicked + SOFT_OBJECT_OFFSET_OFFSET);
    start_menu_transition_ptr = read_offset<start_menu_transition_func>(
        option_menu_entry_clicked + START_MENU_TRANSITION_OFFSET);
}

// No transition just feels better ¯\_(ツ)_/¯
const constexpr auto MENU_TRANSITION_NONE = 13;
// As long as no one implements splitscreen this should be safe...
const constexpr auto CONTROLLER_ID = 0;

/**
 * @brief Starts a transition into the options menu.
 *
 * @param self The menu to transition from.
 */
void start_options_transition(UGFxMainAndPauseBaseMenu* self) {
    set_first_options_ptr(ACCESSIBILITY_OPTION_MENU_TYPE);

    auto soft_object_ptr =
        reinterpret_cast<void*>(reinterpret_cast<uintptr_t>(self) + transition::soft_object_offset);

    transition::EMenuTransition transition = MENU_TRANSITION_NONE;
    transition::start_menu_transition_ptr(self, &transition, soft_object_ptr, CONTROLLER_ID);
}

}  // namespace transition

namespace injection {

bool inject_options_this_call = false;
FText options_name_to_inject{};
pyunrealsdk::StaticPyObject injection_callback{};

/*

To fit in the options list, we want a hook in the middle of `UGFxOptionBase::Refresh`.
This function looks approximately like:
```
this->ContentPanel->RemoveAllListItems();
this->SomeList->Resize(0);
this->SomeOtherList->Resize(0);

for (auto description : this->OptionDescriptions) {
    this->CreateContentPanelItem(description);
}

this->ContentPanel->Redraw();
```

Since hooking in the middle is awkward, we use a two-part hook instead.
At the start of `UGFxOptionBase::Refresh`, we modify the list of option descriptions to contain just
a single entry, with an invalid option id. In `CreateContentPanelItem` we then look for this invalid
id, and if we find it inject the rest.

However there's a problem: `CreateContentPanelItem` is a virtual function. We choose to use the base
version `UGFxOptionBase::CreateContentPanelItem`, since it was easiest to find. This is then what
forces us to use the accessibility menu - it's the only one that will pass an invalid option type
back to the base function.

*/

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
    "48 8B 7B ??"        // mov rdi, [rbx+38] <--- Also grab this offset
};
const constexpr auto OPTION_LIST_OFFSET_OFFSET = 62;

using UGFxOptionBase = UObject;
using option_base_refresh_func = void (*)(UGFxOptionBase* self);
option_base_refresh_func option_base_refresh_ptr;

int8_t option_list_offset;

const constinit Pattern<15> OPTION_BASE_CREATE_CONTENT_PANEL_ITEM_PATTERN{
    "48 85 D2"       // test rdx, rdx
    "0F84 ????????"  // je Borderlands3.exe+1191678
    "56"             // push rsi
    "57"             // push rdi
    "48 83 EC 78"    // sub rsp, 78
};

using UOptionDescriptionItem = UObject;
using option_base_create_content_panel_item_func = void (*)(UGFxOptionBase* self,
                                                            UOptionDescriptionItem* description);
option_base_create_content_panel_item_func option_base_create_content_panel_item_ptr;

const constinit Pattern<12> OPTION_MENU_GET_OPTION_TITLE_PATTERN{
    "40 53"        // push rbx
    "48 83 EC 20"  // sub rsp, 20
    "41 FF C8"     // dec r8d
    "48 8B DA"     // mov rbx, rdx
};

using option_menu_get_option_title_func = FText* (*)(transition::option_menu_type type);
option_menu_get_option_title_func option_menu_get_option_title_ptr;

auto option_description_item = unrealsdk::unreal::find_class(L"OptionDescriptionItem"_fn);
auto transient = unrealsdk::find_object(L"Package"_fn, L"/Engine/Transient");
auto option_type_prop =
    option_description_item->find_prop_and_validate<UEnumProperty>(L"OptionType"_fn);
auto option_item_type_prop =
    option_description_item->find_prop_and_validate<UEnumProperty>(L"OptionItemType"_fn);

const constexpr auto INVALID_OPTION_TYPE = std::numeric_limits<uint8_t>::max();
const constexpr auto INVALID_OPTION_ITEM_TYPE = std::numeric_limits<uint8_t>::max();

void option_base_refresh_hook(UGFxOptionBase* self) {
    if (inject_options_this_call) {
        // Done injecting at this point, can clear the flag
        inject_options_this_call = false;

        auto description = unrealsdk::construct_object(option_description_item, transient);
        description->set<UEnumProperty>(option_type_prop, INVALID_OPTION_TYPE);
        description->set<UEnumProperty>(option_item_type_prop, INVALID_OPTION_ITEM_TYPE);

        auto option_list = reinterpret_cast<TArray<UOptionDescriptionItem*>*>(
            reinterpret_cast<uintptr_t>(self) + option_list_offset);
        option_list->resize(1);
        (*option_list)[0] = description;
    }

    option_base_refresh_ptr(self);
}

void option_base_create_content_panel_item_hook(UGFxOptionBase* self,
                                                UOptionDescriptionItem* description) {
    auto option_type = description->get<UEnumProperty>(option_type_prop);

    if (option_type == INVALID_OPTION_TYPE) {
        try {
            const py::gil_scoped_acquire gil{};
            pyunrealsdk::debug_this_thread();

            injection_callback(pyunrealsdk::type_casters::cast(self));
        } catch (const std::exception& ex) {
            pyunrealsdk::logging::log_python_exception(ex);
        }

        return;
    }

    option_base_create_content_panel_item_ptr(self, description);
}

FText* option_menu_get_option_title_hook(transition::option_menu_type type) {
    if (inject_options_this_call) {
        // Don't clear the flag yet, still need it when injecting entries

        return &options_name_to_inject;
    }

    return option_menu_get_option_title_ptr(type);
}

/**
 * @brief Performs all required setup needed to be able to inject custom options.
 */
void setup(void) {
    auto option_base_refresh = OPTION_BASE_REFRESH.sigscan("UGFxOptionBase::Refresh");
    option_list_offset =
        *reinterpret_cast<int8_t*>(option_base_refresh + OPTION_LIST_OFFSET_OFFSET);
    detour(option_base_refresh, option_base_refresh_hook, &option_base_refresh_ptr,
           "UGFxOptionBase::Refresh");

    detour(OPTION_BASE_CREATE_CONTENT_PANEL_ITEM_PATTERN,
           option_base_create_content_panel_item_hook, &option_base_create_content_panel_item_ptr,
           "UGFxOptionBase::CreateContentPanelItem");

    detour(OPTION_MENU_GET_OPTION_TITLE_PATTERN, option_menu_get_option_title_hook,
           &option_menu_get_option_title_ptr, "UGFxOptionsMenu::GetOptionTitle");
}

}  // namespace injection

namespace scroll {

using UGbxGFxGridScrollingList = UObject;

const constinit Pattern<25> SCROLLING_LIST_SCROLL_TO_POSITION_PATTERN{
    "40 53"              // push rbx
    "48 83 EC 20"        // sub rsp, 20
    "80 B9 ???????? 00"  // cmp byte ptr [rcx+00000250], 00
    "48 8B D9"           // mov rbx, rcx
    "74 ??"              // je Borderlands3.exe+2ECD606
    "48 81 C1 B8020000"  // add rcx, 000002B8
};

using scrolling_list_scroll_to_position_func = void (*)(UGbxGFxGridScrollingList* self,
                                                        float pos,
                                                        bool desired);
scrolling_list_scroll_to_position_func scrolling_list_scroll_to_position_ptr;

auto content_panel_prop = unrealsdk::unreal::find_class(L"GFxOptionBase"_fn)
                              ->find_prop_and_validate<UObjectProperty>(L"ContentPanel"_fn);
auto ui_scroller_prop =
    content_panel_prop->get_property_class()->find_prop_and_validate<UStructProperty>(
        L"UiScroller"_fn);
auto scroll_position_prop =
    ui_scroller_prop->get_inner_struct()->find_prop_and_validate<UFloatProperty>(
        L"ScrollPosition"_fn);

/**
 * @brief Performs all required setup needed to be able to manipulate the options scrollbar.
 */
void setup(void) {
    scrolling_list_scroll_to_position_ptr =
        SCROLLING_LIST_SCROLL_TO_POSITION_PATTERN.sigscan<scrolling_list_scroll_to_position_func>(
            "UGbxGFxGridScrollingList::ScrollToPosition");
}

}  // namespace scroll

}  // namespace

// NOLINTNEXTLINE(readability-identifier-length)
PYBIND11_MODULE(options_transition, m) {
    transition::setup();
    injection::setup();
    scroll::setup();

    m.def(
        "open_custom_options",
        [](const py::object& self, const std::wstring& name, const py::object& callback) {
            auto converted_self = pyunrealsdk::type_casters::cast<UObject*>(self);

            injection::inject_options_this_call = true;
            injection::options_name_to_inject = name;
            injection::injection_callback = callback;

            transition::start_options_transition(converted_self);
        },
        "Opens a custom options menu.\n"
        "\n"
        "Uses a callback to specify the menu's entries. This callback takes a single\n"
        "positional arg, the option menu to add entries to. It's return value is ignored.\n"
        "\n"
        "Args:\n"
        "    self: The current menu object to open under.\n"
        "    name: The name of the options menu to open.\n"
        "    callback: The setup callback to use.",
        "self"_a, "name"_a, "callback"_a);

    m.def(
        "refresh_options",
        [](const py::object& self, const py::object& callback, bool preserve_scroll) {
            auto converted_self = pyunrealsdk::type_casters::cast<UObject*>(self);

            float scroll_pos = 0;
            if (preserve_scroll) {
                scroll_pos = converted_self->get<UObjectProperty>(scroll::content_panel_prop)
                                 ->get<UStructProperty>(scroll::ui_scroller_prop)
                                 .get<UFloatProperty>(scroll::scroll_position_prop);
            }

            injection::inject_options_this_call = true;
            injection::injection_callback = callback;

            injection::option_base_refresh_hook(converted_self);

            if (preserve_scroll) {
                auto scroll_list = converted_self->get<UObjectProperty>(scroll::content_panel_prop);

                scroll::scrolling_list_scroll_to_position_ptr(scroll_list, scroll_pos, false);
            }
        },
        "Refreshes the current custom options menu, allowing changing it's entries.\n"
        "\n"
        "Uses a callback to specify the menu's entries. This callback takes a single\n"
        "positional arg, the option menu to add entries to. It's return value is ignored.\n"
        "\n"
        "Args:\n"
        "    self: The current menu object to open under.\n"
        "    callback: The setup callback to use.\n"
        "    preserve_scroll: If true, preserves the current scroll position.",
        "self"_a, "callback"_a, "preserve_scroll"_a = true);
}
