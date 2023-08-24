#include "pyunrealsdk/pch.h"
#include "unrealsdk/memory.h"
#include "unrealsdk/unreal/classes/properties/uenumproperty.h"
#include "unrealsdk/unreal/classes/uobject.h"
#include "unrealsdk/unreal/classes/uobject_funcs.h"
#include "unrealsdk/unreal/find_class.h"
#include "unrealsdk/unreal/structs/ftext.h"
#include "unrealsdk/unreal/structs/tarray.h"
#include "unrealsdk/unreal/structs/tarray_funcs.h"
#include "unrealsdk/unrealsdk.h"

using namespace unrealsdk::unreal;
using namespace unrealsdk::memory;

#pragma region Transition into options menu

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

void setup(void) {
    auto option_menu_entry_clicked = OPTION_MENU_ENTRY_CLICKED_PATTERN.sigscan();
    set_first_options_ptr =
        read_offset<set_first_options_func>(option_menu_entry_clicked + SET_FIRST_OPTIONS_OFFSET);
    soft_object_offset =
        *reinterpret_cast<int32_t*>(option_menu_entry_clicked + SOFT_OBJECT_OFFSET_OFFSET);
    start_menu_transition_ptr = read_offset<start_menu_transition_func>(
        option_menu_entry_clicked + START_MENU_TRANSITION_OFFSET);
}

}  // namespace transition

/**
 * @brief Starts a transition into the options menu.
 *
 * @param self The menu to transition from.
 */
void start_options_transition(transition::UGFxMainAndPauseBaseMenu* self) {
    // No transition just feels better ¯\_(ツ)_/¯
    const constexpr auto MENU_TRANSITION_NONE = 13;
    // As long as no one implements splitscreen this should be safe...
    const constexpr auto CONTROLLER_ID = 0;

    transition::set_first_options_ptr(transition::ACCESSIBILITY_OPTION_MENU_TYPE);

    auto soft_object_ptr =
        reinterpret_cast<void*>(reinterpret_cast<uintptr_t>(self) + transition::soft_object_offset);

    transition::EMenuTransition transition = MENU_TRANSITION_NONE;
    transition::start_menu_transition_ptr(self, &transition, soft_object_ptr, CONTROLLER_ID);
}

#pragma endregion

#pragma region Injecting Options

bool inject_options_this_call = false;

namespace injection {

/*

To fit in the options list, we want a hook in the middle of `UGFxOptionBase::Refresh`.
This function looks aproximately like:
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
    "48 8B 7B ??"        // mov rdi, [rbx+38] <--- Grab this offset
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

using UGFxOptionsMenu = UObject;
using option_menu_get_option_title_func = FText* (*)(UGFxOptionsMenu* self,
                                                     transition::option_menu_type type);
option_menu_get_option_title_func option_menu_get_option_title_ptr;

auto option_description_item = unrealsdk::unreal::find_class(L"OptionDescriptionItem"_fn);
auto transient = unrealsdk::find_object(L"Package"_fn, L"/Engine/Transient");
auto option_type_prop =
    option_description_item->find_prop_and_validate<UEnumProperty>(L"OptionType"_fn);

const constexpr auto INVALID_OPTION_TYPE = std::numeric_limits<uint8_t>::max();

void option_base_refresh_hook(UGFxOptionBase* self) {
    if (inject_options_this_call) {
        auto description = unrealsdk::construct_object(option_description_item, transient);
        description->set<UEnumProperty>(option_type_prop, INVALID_OPTION_TYPE);

        auto option_list = reinterpret_cast<TArray<UOptionDescriptionItem*>*>(
            reinterpret_cast<uintptr_t>(self) + option_list_offset);
        option_list->resize(1);
        (*option_list)[0] = description;

        inject_options_this_call = false;
    }

    option_base_refresh_ptr(self);
}

void option_base_create_content_panel_item_hook(UGFxOptionBase* self,
                                                UOptionDescriptionItem* description) {
    auto option_type = description->get<UEnumProperty>(option_type_prop);

    if (option_type == INVALID_OPTION_TYPE) {
        // TODO: inject callback
        return;
    }

    option_base_create_content_panel_item_ptr(self, description);
}

FText* option_menu_get_option_title_hook(UGFxOptionsMenu* self, transition::option_menu_type type) {
    // TODO: user provided
    // return option_menu_get_option_title_ptr(self, type);
    (void)self;
    (void)type;

    static FText mod_options_title{"mod options"};
    return &mod_options_title;
}

void setup(void) {
    auto option_base_refresh = OPTION_BASE_REFRESH.sigscan();
    option_list_offset =
        *reinterpret_cast<int8_t*>(option_base_refresh + OPTION_LIST_OFFSET_OFFSET);
    detour(option_base_refresh, option_base_refresh_hook, &option_base_refresh_ptr,
           "UGFxOptionBase::Refresh");

    detour(OPTION_BASE_CREATE_CONTENT_PANEL_ITEM_PATTERN.sigscan(),
           option_base_create_content_panel_item_hook, &option_base_create_content_panel_item_ptr,
           "UGFxOptionBase::CreateContentPanelItem");

    detour(OPTION_MENU_GET_OPTION_TITLE_PATTERN.sigscan(), option_menu_get_option_title_hook,
           &option_menu_get_option_title_ptr, "UGFxOptionsMenu::GetOptionTitle");
}

}  // namespace injection

#pragma endregion

PYBIND11_MODULE(options, m) {
    transition::setup();
    injection::setup();

    m.def("inject", [](py::object self) {
        inject_options_this_call = true;

        start_options_transition(pyunrealsdk::type_casters::cast<UObject*>(self));
    });
}
