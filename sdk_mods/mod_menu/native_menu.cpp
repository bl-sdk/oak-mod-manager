#include "pyunrealsdk/pch.h"
#include "unrealsdk/hook_manager.h"
#include "unrealsdk/memory.h"
#include "unrealsdk/unreal/classes/properties/uobjectproperty.h"
#include "unrealsdk/unreal/classes/uobject.h"
#include "unrealsdk/unreal/structs/fname.h"
#include "unrealsdk/unreal/structs/ftext.h"
#include "unrealsdk/unreal/wrappers/wrapped_struct.h"

using namespace unrealsdk::unreal;
using namespace unrealsdk::memory;

UObject* mods_menu_button = nullptr;

#pragma region UGFxMainAndPauseBaseMenu::AddMenuItem hook

using add_menu_item_func =
    UObject* (*)(void* self, FText* text, FName callback, bool big, int32_t always_minus_one);

add_menu_item_func add_menu_item_ptr;

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

UObject* add_menu_item_hook(void* self,
                            FText* text,
                            FName callback,
                            bool big,
                            int32_t always_minus_one) {
    if (always_minus_one != -1) {
        LOG(DEV_WARNING,
            "UGFxMainAndPauseBaseMenu::AddMenuItem::always_minus_one was not -1 when called with "
            "'{}' '{}' {}",
            (std::string)*text, callback, big);
    }

    UObject* button = add_menu_item_ptr(self, text, callback, big, always_minus_one);

    if (callback == L"OnStoreClicked"_fn) {
        FText mods_text{"MODS"};
        mods_menu_button =
            add_menu_item_ptr(self, &mods_text, L"OnOtherButtonClicked"_fn, false, -1);
    }

    return button;
}

#pragma endregion

bool other_button_clicked(unrealsdk::hook_manager::Details& hook) {
    if (hook.args->get<UObjectProperty>(L"PressedButton"_fn) == mods_menu_button) {
        LOG(ERROR, "Mods clicked");
    }

    return false;
}

// NOLINTNEXTLINE(readability-identifier-length)
PYBIND11_MODULE(native_menu, m) {
    detour(ADD_MENU_ITEM_PATTERN.sigscan(), add_menu_item_hook, &add_menu_item_ptr,
           "UGFxMainAndPauseBaseMenu::AddMenuItem");

    unrealsdk::hook_manager::add_hook(L"/Script/OakGame.GFxOakMainMenu:OnOtherButtonClicked",
                                      unrealsdk::hook_manager::Type::PRE, L"mod_menu_native_menu",
                                      other_button_clicked);

    (void)m;
}

#pragma endregion
