#include "pyunrealsdk/pch.h"
#include "unrealsdk/pch.h"
#include "unrealsdk/memory.h"
#include "unrealsdk/unreal/class_name.h"
#include "unrealsdk/unreal/classes/properties/copyable_property.h"
#include "unrealsdk/unreal/classes/uobject.h"
#include "unrealsdk/unreal/classes/uscriptstruct.h"
#include "unrealsdk/unreal/wrappers/wrapped_struct.h"
#include "unrealsdk/unrealsdk.h"

using namespace unrealsdk::unreal;
using namespace unrealsdk::memory;

const constinit Pattern<25> COMBO_BOX_GET_SELECTED_INDEX{
    "48 8B 81 ????????"  // mov rax, [rcx+00000318]
    "48 85 C0"           // test rax, rax
    "74 ??"              // je Borderlands3.exe+2EB339A
    "48 8B 80 ????????"  // mov rax, [rax+00000198]
    "8B 80 ????????"     // mov eax, [rax+00000270]
};

using UGbxGFxListItemComboBox = UObject;
using combo_box_get_selected_index_func = int32_t (*)(UGbxGFxListItemComboBox* self);
combo_box_get_selected_index_func combo_box_get_selected_index_ptr =
    COMBO_BOX_GET_SELECTED_INDEX.sigscan<combo_box_get_selected_index_func>();

const constinit Pattern<35> NUMBER_GET_CURRENT_VALUE{
    "48 85 D2"        // test rdx, rdx
    "74 ??"           // je Borderlands3.exe+11A23BD
    "53"              // push rbx
    "48 83 EC 20"     // sub rsp, 20
    "48 83 79 ?? 00"  // cmp qword ptr [rcx+70], 00
    "48 8B D9"        // mov rbx, rcx
    "74 ??"           // je Borderlands3.exe+11A23B8
    "48 83 79 ?? 00"  // cmp qword ptr [rcx+68], 00
    "74 ??"           // je Borderlands3.exe+11A23B8
    "48 8B CA"        // mov rcx, rdx
    "E8 ????????",    // call Borderlands3.exe+27F9F70
    31};

using UGbxGFxListItemNumber = UObject;
using number_get_current_value_func = float32_t (*)(UGbxGFxListItemNumber* self);
number_get_current_value_func number_get_current_value_ptr =
    read_offset<number_get_current_value_func>(NUMBER_GET_CURRENT_VALUE.sigscan());

const constinit Pattern<41> SPINNER_GET_CURRENT_SELECTION_INDEX{
    "40 53"                 // push rbx
    "48 83 EC 20"           // sub rsp, 20
    "48 8B D9"              // mov rbx, rcx
    "48 85 D2"              // test rdx, rdx
    "74 ??"                 // je Borderlands3.exe+119FAC1
    "48 83 B9 ???????? 00"  // cmp qword ptr [rcx+000000C0], 00
    "74 ??"                 // je Borderlands3.exe+119FAC1
    "48 8B CA"              // mov rcx, rdx
    "E8 ????????"           // call Borderlands3.exe+2EB1C70
    "48 8B 8B ????????"     // mov rcx, [rbx+000000C0]
    "85 C0",                // test eax, eax
    28};

using UGbxGFxListItemSpinner = UObject;
using spinner_get_current_selection_index_func = int32_t (*)(UGbxGFxListItemSpinner* self);
spinner_get_current_selection_index_func spinner_get_current_selection_index_ptr =
    read_offset<spinner_get_current_selection_index_func>(
        SPINNER_GET_CURRENT_SELECTION_INDEX.sigscan());

PYBIND11_MODULE(options_getters, m) {
    m.def(
        "get_combo_box_selected_idx",
        [](py::object self) {
            return combo_box_get_selected_index_ptr(
                pyunrealsdk::type_casters::cast<UObject*>(self));
        },
        "Gets the selected index of a GbxGFxListItemComboBox.\n"
        "\n"
        "Args:\n"
        "    self: The combo box item to get the selected index of.",
        "self"_a);

    m.def(
        "get_number_value",
        [](py::object self) {
            return number_get_current_value_ptr(pyunrealsdk::type_casters::cast<UObject*>(self));
        },
        "Gets the value of a GbxGFxListItemNumber.\n"
        "\n"
        "Args:\n"
        "    self: The number item to get the value of.",
        "self"_a);

    m.def(
        "get_spinner_selected_idx",
        [](py::object self) {
            return spinner_get_current_selection_index_ptr(
                pyunrealsdk::type_casters::cast<UObject*>(self));
        },
        "Gets the selected index of a GbxGFxListItemSpinner.\n"
        "\n"
        "Args:\n"
        "    self: The spinner item to get the selected index of.",
        "self"_a);
}
