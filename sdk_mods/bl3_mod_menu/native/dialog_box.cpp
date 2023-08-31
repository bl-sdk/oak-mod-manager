#include "pyunrealsdk/pch.h"
#include "pyunrealsdk/logging.h"
#include "unrealsdk/memory.h"
#include "unrealsdk/unreal/class_name.h"
#include "unrealsdk/unreal/classes/properties/uarrayproperty.h"
#include "unrealsdk/unreal/classes/properties/ustructproperty.h"
#include "unrealsdk/unreal/classes/uobject.h"
#include "unrealsdk/unreal/classes/uscriptstruct.h"
#include "unrealsdk/unreal/wrappers/wrapped_struct.h"
#include "unrealsdk/unrealsdk.h"

using namespace unrealsdk::unreal;
using namespace unrealsdk::memory;

bool injecting_next_call = false;
py::object configure_callback{};

auto info_struct_type = validate_type<UScriptStruct>(
    unrealsdk::find_object(L"ScriptStruct", L"/Script/OakGame.GbxGFxDialogBoxInfo"));
auto choices_prop = info_struct_type->find_prop_and_validate<UArrayProperty>(L"Choices"_fn);

/**
 * @brief Deletes the stored configure callback.
 */
void delete_configure_callback(void) {
    const py::gil_scoped_acquire gil{};

    // Release does not decrement the ref counter
    auto handle = configure_callback.release();
    if (handle.ptr() != nullptr) {
        handle.dec_ref();
    }
}

const constinit Pattern<21> DISPLAY_NAT_HELP_DIALOG{
    "40 55"                 // push rbp
    "56"                    // push rsi
    "57"                    // push rdi
    "48 8D AC 24 ????????"  // lea rbp, [rsp-000000C0]
    "48 81 EC C0010000"     // sub rsp, 000001C0
    "33 D2"                 // xor edx, edx
};

using UOakGameInstance = UObject;
using display_nat_help_dialog_func = void (*)(UOakGameInstance* self);
display_nat_help_dialog_func display_nat_help_dialog_ptr =
    DISPLAY_NAT_HELP_DIALOG.sigscan<display_nat_help_dialog_func>();

const constinit Pattern<23> SHOW_DIALOG{
    "48 89 5C 24 ??"     // mov [rsp+18], rbx
    "55"                 // push rbp
    "56"                 // push rsi
    "57"                 // push rdi
    "41 56"              // push r14
    "41 57"              // push r15
    "48 83 EC 50"        // sub rsp, 50
    "48 8B B2 A8000000"  // mov rsi, [rdx+000000A8]
};

using UGbxPlayerController = UObject;
using UGbxGFxDialogBox = UObject;
using FGbxGFxDialogBoxInfo = void;
using show_dialog_func = UGbxGFxDialogBox* (*)(UGbxPlayerController* pc,
                                               FGbxGFxDialogBoxInfo* info);
show_dialog_func show_dialog_ptr;

UGbxGFxDialogBox* show_dialog_hook(UGbxPlayerController* pc, FGbxGFxDialogBoxInfo* info) {
    if (injecting_next_call) {
        injecting_next_call = false;

        WrappedStruct info_struct{info_struct_type, info};

        // If we delete entries from it it will cause a crash next time we try show this dialog
        // Specifically it crashes trying to create a new FText - presumably at an index which no
        // longer exists
        // To avoid this, swap it out with an empty array for this call
        auto arr = info_struct.get<UArrayProperty>(choices_prop);
        TArray<void> arr_backup = *arr.base;
        *arr.base = TArray<void>{nullptr, 0, 0};

        try {
            py::gil_scoped_acquire gil{};

            configure_callback(pyunrealsdk::type_casters::cast(&info_struct));

            show_dialog_ptr(pc, info);
        } catch (const std::exception& ex) {
            pyunrealsdk::logging::log_python_exception(ex);
        }

        delete_configure_callback();

        // Restore the actual array, so calling code cleans it up properly
        *arr.base = arr_backup;

        return nullptr;
    }

    return show_dialog_ptr(pc, info);
}

PYBIND11_MODULE(dialog_box, m) {
    detour(SHOW_DIALOG.sigscan(), show_dialog_hook, &show_dialog_ptr,
           "UGbxGFxCoreDialogBoxHelpers::ShowDialog");

    m.def(
        "show_dialog_box",
        [](py::object self, py::object callback) {
            injecting_next_call = true;
            configure_callback = callback;

            display_nat_help_dialog_ptr(pyunrealsdk::type_casters::cast<UObject*>(self));
        },
        "Displays a dialog box.\n"
        "\n"
        "Uses a callback to configure the dialog. This callback takes a single positional\n"
        "arg, a `GbxGFxDialogBoxInfo` struct to edit. It's return value is ignored.\n"
        "\n"
        "Args:\n"
        "    self: The current menu object to open under.\n"
        "    callback: The setup callback to use.",
        "self"_a, "callback"_a);
}

/**
 * @brief Cleans up the static python references we have, before we're unloaded.
 */
void finalize(void) {
    py::gil_scoped_acquire gil;

    delete_configure_callback();
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
