#include "pyunrealsdk/pch.h"
#include "unrealsdk/memory.h"
#include "unrealsdk/unreal/class_name.h"
#include "unrealsdk/unreal/classes/properties/copyable_property.h"
#include "unrealsdk/unreal/classes/properties/uarrayproperty.h"
#include "unrealsdk/unreal/classes/properties/uboolproperty.h"
#include "unrealsdk/unreal/classes/properties/utextproperty.h"
#include "unrealsdk/unreal/classes/uclass.h"
#include "unrealsdk/unreal/classes/uobject.h"
#include "unrealsdk/unreal/classes/uobject_funcs.h"
#include "unrealsdk/unreal/classes/uscriptstruct.h"
#include "unrealsdk/unreal/find_class.h"
#include "unrealsdk/unreal/structs/fname.h"
#include "unrealsdk/unreal/structs/ftext.h"
#include "unrealsdk/unreal/structs/tarray.h"
#include "unrealsdk/unreal/structs/tarray_funcs.h"

using namespace unrealsdk::unreal;
using namespace unrealsdk::memory;

using UGFxOptionBase = UObject;
using UOptionDescriptionItem = UObject;

namespace {

const FName OPTION_CALLBACK = L"OnUnimplementedOptionClicked"_fn;
const auto OPTION_DESCRIPTION_ITEM = unrealsdk::unreal::find_class(L"OptionDescriptionItem"_fn);

/**
 * @brief Creates an option description item object.
 *
 * @param name The name of the option.
 * @param description_title The title of the option's description. If not given, copies the name.
 * @param description The option's description.
 * @return The created object.
 */
UOptionDescriptionItem* create_description_item(
    const std::wstring& name,
    const std::optional<std::wstring>& description_title,
    const std::wstring& description) {
    static auto name_prop =
        OPTION_DESCRIPTION_ITEM->find_prop_and_validate<UTextProperty>(L"OptionItemName"_fn);
    static auto description_title_prop =
        OPTION_DESCRIPTION_ITEM->find_prop_and_validate<UTextProperty>(
            L"OptionDescriptionTitle"_fn);
    static auto description_prop =
        OPTION_DESCRIPTION_ITEM->find_prop_and_validate<UTextProperty>(L"OptionDescriptionText"_fn);

    static auto transient = unrealsdk::find_object(L"Package"_fn, L"/Engine/Transient");

    auto obj = unrealsdk::construct_object(OPTION_DESCRIPTION_ITEM, transient);
    obj->set<UTextProperty>(name_prop, name);
    obj->set<UTextProperty>(description_title_prop, description_title ? *description_title : name);
    obj->set<UTextProperty>(description_prop, description);

    return obj;
}

}  // namespace

namespace title {

// UGFxEchoCastMenu::SetupTitleItem and UGFxOptionBase::SetupTitleItem are essentially identical
// functions, which have the exact same signature, but they're incompatible for our purposes
// Instead, we'll extract it from UGFxOptionBase::CreateContentPanelItem
const constinit Pattern<36> SETUP_TITLE_ITEM{
    "E8 {????????}"         // call Borderlands3.exe+11B6990  <--- UGFxOptionBase::SetupTitleItem
    "48 8B 7C 24 ??"        // mov rdi, [rsp+58]
    "E9 ????????"           // jmp Borderlands3.exe+1191623
    "41 B8 01000000"        // mov r8d, 00000001
    "48 8D 15 ????????"     // lea rdx, [Borderlands3.exe+46CCCE8]
    "48 8D 8C 24 ????????"  // lea rcx, [rsp+00000098]
};

using setup_title_item_func = UObject* (*)(UGFxOptionBase* self, FText* title);
setup_title_item_func setup_title_item_ptr =
    read_offset<setup_title_item_func>(SETUP_TITLE_ITEM.sigscan("UGFxOptionBase::SetupTitleItem"));

void add_title(UGFxOptionBase* self, const std::wstring& name) {
    FText converted_name{name};
    setup_title_item_ptr(self, &converted_name);
}

}  // namespace title

namespace slider {

const constinit Pattern<14> SETUP_SLIDER_ITEM_OLD{
    "48 8B C4"           // mov rax, rsp
    "55"                 // push rbp
    "56"                 // push rsi
    "41 57"              // push r15
    "48 81 EC C0000000"  // sub rsp, 000000C0
};

const constinit Pattern<29> SETUP_SLIDER_ITEM_NEW{
    "48 89 5C 24 ??"  // mov [rsp+08], rbx
    "48 89 74 24 ??"  // mov [rsp+10], rsi
    "57"              // push rdi
    "48 83 EC ??"     // sub rsp, 70
    "0F29 74 24 ??"   // movaps [rsp+60], xmm6
    "0F28 F2"         // movaps xmm6, xmm2
    "49 8B F1"        // mov rsi, r9
    "48 8B DA"        // mov rbx, rdx
};

using setup_slider_item_func = UObject* (*)(UGFxOptionBase* self,
                                            UOptionDescriptionItem* description,
                                            float32_t default_value,
                                            const FName* callback);
setup_slider_item_func setup_slider_item_ptr;

/**
 * @brief Performs all required setup needed to be able to add a slider item.
 */
void setup(void) {
    setup_slider_item_ptr = SETUP_SLIDER_ITEM_NEW.sigscan_nullable<setup_slider_item_func>();
    if (setup_slider_item_ptr == nullptr) {
        setup_slider_item_ptr = SETUP_SLIDER_ITEM_OLD.sigscan<setup_slider_item_func>(
            "UGFxOptionBase::SetupSliderItem");
    }
}

void add_slider(UGFxOptionBase* self,
                const std::wstring& name,
                float32_t value,
                float32_t slider_min,
                float32_t slider_max,
                float32_t slider_step,
                bool slider_is_integer,
                const std::optional<std::wstring>& description_title,
                const std::wstring& description) {
    static auto slider_min_prop =
        OPTION_DESCRIPTION_ITEM->find_prop_and_validate<UFloatProperty>(L"SliderMin"_fn);
    static auto slider_max_prop =
        OPTION_DESCRIPTION_ITEM->find_prop_and_validate<UFloatProperty>(L"SliderMax"_fn);
    static auto slider_step_prop =
        OPTION_DESCRIPTION_ITEM->find_prop_and_validate<UFloatProperty>(L"SliderStep"_fn);
    static auto slider_is_integer_prop =
        OPTION_DESCRIPTION_ITEM->find_prop_and_validate<UBoolProperty>(L"SliderIsInteger"_fn);

    auto desc_item = create_description_item(name, description_title, description);
    desc_item->set<UFloatProperty>(slider_min_prop, slider_min);
    desc_item->set<UFloatProperty>(slider_max_prop, slider_max);
    desc_item->set<UFloatProperty>(slider_step_prop, slider_step);
    desc_item->set<UBoolProperty>(slider_is_integer_prop, slider_is_integer);

    setup_slider_item_ptr(self, desc_item, value, &OPTION_CALLBACK);
}

}  // namespace slider

namespace spinner {

const constinit Pattern<106> SETUP_SPINNER_ITEM{
    "48 89 5C 24 ??"     // mov [rsp+08], rbx
    "48 89 6C 24 ??"     // mov [rsp+10], rbp
    "48 89 74 24 ??"     // mov [rsp+18], rsi
    "57"                 // push rdi
    "48 83 EC 50"        // sub rsp, 50
    "49 8B F1"           // mov rsi, r9
    "41 8B E8"           // mov ebp, r8d
    "48 8B DA"           // mov rbx, rdx
    "48 8B F9"           // mov rdi, rcx
    "48 85 D2"           // test rdx, rdx
    "0F84 ????????"      // je Borderlands3.exe+11B64A6
    "48 8D 54 24 ??"     // lea rdx, [rsp+30]
    "48 8B CB"           // mov rcx, rbx
    "E8 ????????"        // call Borderlands3.exe+10C9890
    "4C 8D 83 ????????"  // lea r8, [rbx+00000090]
    "48 89 74 24 ??"     // mov [rsp+20], rsi
    "44 8B CD"           // mov r9d, ebp
    "48 8D 54 24 ??"     // lea rdx, [rsp+30]
    "48 8B CF"           // mov rcx, rdi
    "E8 ????????"        // call Borderlands3.exe+11B60F0
    "48 8B F0"           // mov rsi, rax
    "48 85 C0"           // test rax, rax
    "74 ??"              // je Borderlands3.exe+11B6469
    "48 8B D3"           // mov rdx, rbx
    "48 8B C8"           // mov rcx, rax
    "E8 ????????"        // call Borderlands3.exe+2ECE400
    "48 83 7F ?? 00"     // cmp qword ptr [rdi+70], 00
};

using setup_spinner_item_func = UObject* (*)(UGFxOptionBase* self,
                                             UOptionDescriptionItem* description,
                                             int32_t default_idx,
                                             const FName* callback);
setup_spinner_item_func setup_spinner_item_ptr =
    SETUP_SPINNER_ITEM.sigscan<setup_spinner_item_func>("UGFxOptionBase::SetupSpinnerItem");

const constinit Pattern<25> SETUP_SPINNER_ITEM_AS_BOOL{
    "48 8B C4"           // mov rax, rsp
    "48 89 58 ??"        // mov [rax+20], rbx
    "55"                 // push rbp
    "57"                 // push rdi
    "41 55"              // push r13
    "48 81 EC A0000000"  // sub rsp, 000000A0
    "49 8B D9"           // mov rbx, r9
    "41 0FB6 F8"         // movzx edi, r8l
};

using setup_spinner_item_as_bool_func = UObject* (*)(UGFxOptionBase* self,
                                                     UOptionDescriptionItem* description,
                                                     int32_t default_idx,
                                                     const FName* callback);
setup_spinner_item_as_bool_func setup_spinner_item_as_bool_ptr =
    SETUP_SPINNER_ITEM_AS_BOOL.sigscan<setup_spinner_item_as_bool_func>(
        "UGFxOptionBase::SetupSpinnerItemAsBoolean");

void add_spinner(UGFxOptionBase* self,
                 const std::wstring& name,
                 int32_t idx,
                 const std::vector<std::wstring>& options,
                 bool wrap_enabled,
                 const std::optional<std::wstring>& description_title,
                 const std::wstring& description) {
    static auto options_prop =
        OPTION_DESCRIPTION_ITEM->find_prop_and_validate<UArrayProperty>(L"SpinnerOptions"_fn);
    static auto wrap_enabled_prop =
        OPTION_DESCRIPTION_ITEM->find_prop_and_validate<UBoolProperty>(L"SpinnerWrapEnabled"_fn);

    auto desc_item = create_description_item(name, description_title, description);
    desc_item->set<UBoolProperty>(wrap_enabled_prop, wrap_enabled);

    auto options_array = desc_item->get<UArrayProperty>(options_prop);
    auto size = options.size();
    options_array.resize(size);
    for (size_t i = 0; i < size; i++) {
        options_array.set_at<UTextProperty>(i, options[i]);
    }

    setup_spinner_item_ptr(self, desc_item, idx, &OPTION_CALLBACK);
}

void add_bool_spinner(UGFxOptionBase* self,
                      const std::wstring& name,
                      bool value,
                      const std::optional<std::wstring>& true_text,
                      const std::optional<std::wstring>& false_text,
                      const std::optional<std::wstring>& description_title,
                      const std::wstring& description) {
    static auto true_text_prop =
        OPTION_DESCRIPTION_ITEM->find_prop_and_validate<UTextProperty>(L"BooleanOnText"_fn);
    static auto false_text_prop =
        OPTION_DESCRIPTION_ITEM->find_prop_and_validate<UTextProperty>(L"BooleanOffText"_fn);

    auto desc_item = create_description_item(name, description_title, description);
    if (true_text) {
        desc_item->set<UTextProperty>(true_text_prop, *true_text);
    }
    if (false_text) {
        desc_item->set<UTextProperty>(false_text_prop, *false_text);
    }

    setup_spinner_item_as_bool_ptr(self, desc_item, value ? 1 : 0, &OPTION_CALLBACK);
}

}  // namespace spinner

namespace dropdown {

const constinit Pattern<163> SETUP_DROPDOWN_ITEM{
    "48 89 5C 24 ??"        // mov [rsp+08], rbx
    "48 89 6C 24 ??"        // mov [rsp+10], rbp
    "48 89 74 24 ??"        // mov [rsp+18], rsi
    "57"                    // push rdi
    "48 83 EC 50"           // sub rsp, 50
    "41 8B F1"              // mov esi, r9d
    "49 8B E8"              // mov rbp, r8
    "48 8B DA"              // mov rbx, rdx
    "48 8B F9"              // mov rdi, rcx
    "48 85 D2"              // test rdx, rdx
    "0F84 ????????"         // je Borderlands3.exe+11B534B
    "48 8D 54 24 ??"        // lea rdx, [rsp+30]
    "48 8B CB"              // mov rcx, rbx
    "E8 ????????"           // call Borderlands3.exe+10C9890
    "48 8B 84 24 ????????"  // mov rax, [rsp+00000080]
    "48 8D 54 24 ??"        // lea rdx, [rsp+30]
    "44 8B CE"              // mov r9d, esi
    "48 89 44 24 ??"        // mov [rsp+20], rax
    "4C 8B C5"              // mov r8, rbp
    "48 8B CF"              // mov rcx, rdi
    "E8 ????????"           // call Borderlands3.exe+11B5020
    "48 8B F0"              // mov rsi, rax
    "48 85 C0"              // test rax, rax
    "74 ??"                 // je Borderlands3.exe+11B530E
    "48 8B D3"              // mov rdx, rbx
    "48 8B C8"              // mov rcx, rax
    "E8 ????????"           // call Borderlands3.exe+2ECE400
    "48 83 7F ?? 00"        // cmp qword ptr [rdi+70], 00
    "74 ??"                 // je Borderlands3.exe+11B52FF
    "80 BB ???????? 00"     // cmp byte ptr [rbx+00000119], 00
    "74 ??"                 // je Borderlands3.exe+11B52FB
    "48 8B 4F ??"           // mov rcx, [rdi+68]
    "48 85 C9"              // test rcx, rcx
    "74 ??"                 // je Borderlands3.exe+11B52FF
    "E8 ????????"           // call Borderlands3.exe+270BD90
    "84 C0"                 // test al, al
    "74 ??"                 // je Borderlands3.exe+11B52FF
    "B2 01"                 // mov dl, 01
    "EB ??"                 // jmp Borderlands3.exe+11B5301
    "32 D2"                 // xor dl, dl
    "48 8D 8E ????????"     // lea rcx, [rsi+00000170]
    "48 8B 01"              // mov rax, [rcx]
    "FF 50 ??"              // call qword ptr [rax+38]
    "48 8B 5C 24 ??"        // mov rbx, [rsp+38]
};

using setup_dropdown_item_func = UObject* (*)(UGFxOptionBase* self,
                                              UOptionDescriptionItem* description,
                                              TArray<FText> options,
                                              int32_t default_idx,
                                              const FName* callback);
setup_dropdown_item_func setup_dropdown_item_ptr =
    SETUP_DROPDOWN_ITEM.sigscan<setup_dropdown_item_func>("UGFxOptionBase::SetupDropDownListItem");

void add_dropdown(UGFxOptionBase* self,
                  const std::wstring& name,
                  int32_t idx,
                  const std::vector<std::wstring>& options,
                  const std::optional<std::wstring>& description_title,
                  const std::wstring& description) {
    auto desc_item = create_description_item(name, description_title, description);

    TArray<FText> converted_options{};

    auto size = options.size();
    converted_options.resize(size);
    for (size_t i = 0; i < size; i++) {
        converted_options[i] = options[i];
    }

    setup_dropdown_item_ptr(self, desc_item, converted_options, idx, &OPTION_CALLBACK);
}

}  // namespace dropdown

namespace button {

const constinit Pattern<19> SETUP_BUTTON_ITEM{
    "48 89 5C 24 ??"  // mov [rsp+18], rbx
    "48 89 6C 24 ??"  // mov [rsp+20], rbp
    "41 56"           // push r14
    "48 83 EC 40"     // sub rsp, 40
    "49 8B D8"        // mov rbx, r8
};

using setup_button_item_func = UObject* (*)(UGFxOptionBase* self,
                                            UOptionDescriptionItem* description,
                                            const FName* callback);
setup_button_item_func setup_button_item_ptr =
    SETUP_BUTTON_ITEM.sigscan<setup_button_item_func>("UGFxOptionBase::SetupButtonItem");

void add_button(UGFxOptionBase* self,
                const std::wstring& name,
                const std::optional<std::wstring>& description_title,
                const std::wstring& description) {
    auto desc_item = create_description_item(name, description_title, description);
    setup_button_item_ptr(self, desc_item, &OPTION_CALLBACK);
}

}  // namespace button

namespace controls {

const constinit Pattern<14> SETUP_CONTROLS_ITEM{
    "48 8B C4"     // mov rax, rsp
    "5?"           // push rdi     |  push rsi
    "41 54"        // push r12
    "41 56"        // push r14
    "41 57"        // push r15
    "48 83 EC 68"  // sub rsp, 68
};

using EBindingType = uint8_t;
const constexpr auto BINDING_TYPE_COMMON = 1;

using UGbxGFxListItemControls = UObject;
using TBaseDelegate = void;
using setup_controls_item_func = UGbxGFxListItemControls* (*)(UGFxOptionBase* self,
                                                              UOptionDescriptionItem* description,
                                                              FText* first,
                                                              FText* second,
                                                              EBindingType binding_type,
                                                              TBaseDelegate* callback);
setup_controls_item_func setup_controls_item_ptr =
    SETUP_CONTROLS_ITEM.sigscan<setup_controls_item_func>("UGFxOptionBase::SetupControlsItem");

// Rather than properly reverse engineering delegates, this is the function the other setup
// functions call to convert an fname into a delegate, we'll just call it on a byte buffer
const constinit Pattern<54> BIND_UFUNCTION{
    "48 89 5C 24 ??"  // mov [rsp+08], rbx
    "48 89 6C 24 ??"  // mov [rsp+10], rbp
    "48 89 74 24 ??"  // mov [rsp+18], rsi
    "57"              // push rdi
    "48 83 EC 30"     // sub rsp, 30
    "49 8B F0"        // mov rsi, r8
    "48 8B EA"        // mov rbp, rdx
    "45 33 C0"        // xor r8d, r8d
    "48 8B F9"        // mov rdi, rcx
    "33 C9"           // xor ecx, ecx
    "41 8D 50 ??"     // lea edx, [r8+30]
    "E8 ????????"     // call Borderlands3.exe+15DEB00
    "48 8B D8"        // mov rbx, rax
    "48 85 C0"        // test rax, rax
    "74 ??"           // je Borderlands3.exe+F10A31
    "4C 8B C6"        // mov r8, rsi
};

using bind_ufunction_func = void (*)(void* self, UGFxOptionBase* obj, const FName* func_name);
bind_ufunction_func bind_ufunction_ptr =
    BIND_UFUNCTION.sigscan<bind_ufunction_func>("TBaseDelegate<>::BindUFunction<UGFxOptionBase>");

// I think this might actually be as low as 16, but better safe than sorry
const constexpr auto TBASEDELEGATE_SIZE = 0x40;

void add_binding(UGFxOptionBase* self,
                 const std::wstring& name,
                 const std::wstring& display,
                 const std::optional<std::wstring>& description_title,
                 const std::wstring& description) {
    auto desc_item = create_description_item(name, description_title, description);
    FText converted_display{display};

    // There should only ever be one options menu open at a time, so multiple controls will just
    // bind the same object to the same function
    static uint8_t fake_delegate[TBASEDELEGATE_SIZE];
    bind_ufunction_ptr(static_cast<uint8_t*>(fake_delegate), self, &OPTION_CALLBACK);

    // Pass the display value to both columns just in case
    setup_controls_item_ptr(self, desc_item, &converted_display, &converted_display,
                            BINDING_TYPE_COMMON, &fake_delegate);
}

}  // namespace controls

// NOLINTNEXTLINE(readability-identifier-length)
PYBIND11_MODULE(options_setup, m) {
    slider::setup();

    m.def(
        "add_title",
        [](const py::object& self, const std::wstring& name) {
            title::add_title(pyunrealsdk::type_casters::cast<UObject*>(self), name);
        },
        "Adds a title to the options list.\n"
        "\n"
        "Args:\n"
        "    self: The current options menu object to add to.\n"
        "    name: The name of the title.",
        "self"_a, "name"_a);

    m.def(
        "add_slider",
        [](const py::object& self, const std::wstring& name, float32_t value, float32_t slider_min,
           float32_t slider_max, float32_t slider_step, bool slider_is_integer,
           const std::optional<std::wstring>& description_title, const std::wstring& description) {
            slider::add_slider(pyunrealsdk::type_casters::cast<UObject*>(self), name, value,
                               slider_min, slider_max, slider_step, slider_is_integer,
                               description_title, description);
        },
        "Adds a slider to the options list.\n"
        "\n"
        "Args:\n"
        "    self: The current options menu object to add to.\n"
        "    name: The name of the slider.\n"
        "    value: The current value of the slider.\n"
        "    slider_min: The minimum value of the slider.\n"
        "    slider_max: The maximum value of the slider.\n"
        "    slider_step: How far the slider moves each step.\n"
        "    slider_is_integer: True if the slider should only use integer values.\n"
        "    description_title: The title of the slider's description. Defaults to\n"
        "                       copying the name.\n"
        "    description: The slider's description.",
        "self"_a, "name"_a, "value"_a, "slider_min"_a, "slider_max"_a, "slider_step"_a = 1.0,
        "slider_is_integer"_a = false, "description_title"_a = std::nullopt,
        "description"_a = std::wstring{});

    m.def(
        "add_spinner",
        [](const py::object& self, const std::wstring& name, int32_t idx,
           const std::vector<std::wstring>& options, bool wrap_enabled,
           const std::optional<std::wstring>& description_title, const std::wstring& description) {
            spinner::add_spinner(pyunrealsdk::type_casters::cast<UObject*>(self), name, idx,
                                 options, wrap_enabled, description_title, description);
        },
        "Adds a spinner to the options list.\n"
        "\n"
        "Args:\n"
        "    self: The current options menu object to add to.\n"
        "    name: The name of the slider.\n"
        "    idx: The index of the current option to select.\n"
        "    options: The list of options the spinner switches between.\n"
        "    wrap_enabled: True if to allow wrapping from the last option back to the\n"
        "                  first.\n"
        "    description_title: The title of the spinner's description. Defaults to\n"
        "                       copying the name.\n"
        "    description: The spinner's description.",
        "self"_a, "name"_a, "idx"_a, "options"_a, "wrap_enabled"_a = false,
        "description_title"_a = std::nullopt, "description"_a = std::wstring{});

    m.def(
        "add_bool_spinner",
        [](const py::object& self, const std::wstring& name, bool value,
           const std::optional<std::wstring>& true_text,
           const std::optional<std::wstring>& false_text,
           const std::optional<std::wstring>& description_title, const std::wstring& description) {
            spinner::add_bool_spinner(pyunrealsdk::type_casters::cast<UObject*>(self), name, value,
                                      true_text, false_text, description_title, description);
        },
        "Adds a boolean spinner to the options list.\n"
        "\n"
        "Args:\n"
        "    self: The current options menu object to add to.\n"
        "    name: The name of the spinner.\n"
        "    value: The current value of the spinner.\n"
        "    true_text: If set, overwrites the default text for the true option.\n"
        "    false_text: If set, overwrites the default text for the false option.\n"
        "    description_title: The title of the spinner's description. Defaults to\n"
        "                       copying the name.\n"
        "    description: The spinner's description.",
        "self"_a, "name"_a, "value"_a, "true_text"_a = std::nullopt, "false_text"_a = std::nullopt,
        "description_title"_a = std::nullopt, "description"_a = std::wstring{});

    m.def(
        "add_dropdown",
        [](const py::object& self, const std::wstring& name, int32_t idx,
           const std::vector<std::wstring>& options,
           const std::optional<std::wstring>& description_title, const std::wstring& description) {
            dropdown::add_dropdown(pyunrealsdk::type_casters::cast<UObject*>(self), name, idx,
                                   options, description_title, description);
        },
        "Adds a dropdown to the options list.\n"
        "\n"
        "Args:\n"
        "    self: The current options menu object to add to.\n"
        "    name: The name of the dropdown.\n"
        "    idx: The index of the current option to select.\n"
        "    options: The list of options to display.\n"
        "    description_title: The title of the dropdown's description. Defaults to\n"
        "                       copying the name.\n"
        "    description: The dropdown's description.",
        "self"_a, "name"_a, "idx"_a, "options"_a, "description_title"_a = std::nullopt,
        "description"_a = std::wstring{});

    m.def(
        "add_button",
        [](const py::object& self, const std::wstring& name,
           const std::optional<std::wstring>& description_title, const std::wstring& description) {
            button::add_button(pyunrealsdk::type_casters::cast<UObject*>(self), name,
                               description_title, description);
        },
        "Adds a button to the options list.\n"
        "\n"
        "Args:\n"
        "    self: The current options menu object to add to.\n"
        "    name: The name of the button.\n"
        "    description_title: The title of the button's description. Defaults to\n"
        "                       copying the name.\n"
        "    description: The button's description.",
        "self"_a, "name"_a, "description_title"_a = std::nullopt, "description"_a = std::wstring{});

    m.def(
        "add_binding",
        [](const py::object& self, const std::wstring& name, const std::wstring& display,
           const std::optional<std::wstring>& description_title, const std::wstring& description) {
            controls::add_binding(pyunrealsdk::type_casters::cast<UObject*>(self), name, display,
                                  description_title, description);
        },
        "Adds a binding to the options list.\n"
        "\n"
        "Args:\n"
        "    self: The current options menu object to add to.\n"
        "    name: The name of the binding.\n"
        "    display: The binding's display value. This is generally an image.\n"
        "    description_title: The title of the binding's description. Defaults to\n"
        "                       copying the name.\n"
        "    description: The binding's description.",
        "self"_a, "name"_a, "display"_a, "description_title"_a = std::nullopt,
        "description"_a = std::wstring{});
}
