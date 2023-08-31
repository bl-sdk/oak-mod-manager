from typing import Any

import unrealsdk
from unrealsdk.hooks import Block, Type, add_hook, remove_hook
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

from .native.dialog_box import show_dialog_box
from .native.options_getters import (
    get_combo_box_selected_idx,
    get_number_value,
    get_spinner_selected_idx,
)
from .native.options_setup import (
    add_binding,
    add_bool_spinner,
    add_button,
    add_dropdown,
    add_slider,
    add_spinner,
    add_title,
)
from .native.options_transition import open_custom_options, refresh_options
from .native.outer_menu import (
    add_menu_item,
    begin_configure_menu_items,
    get_menu_state,
    set_add_menu_item_callback,
    set_menu_state,
)

mods_menu_idx: int | None = None


def add_menu_item_hook(
    self: UObject,
    text: str,
    callback_name: str,
    big: bool,
    always_minus_one: int,
) -> int:
    idx = add_menu_item(self, text, callback_name, big, always_minus_one)

    if callback_name == "OnStoreClicked":
        global mods_menu_idx
        mods_menu_idx = add_menu_item(self, "MODS", "OnOtherButtonClicked", False, -1)

    return idx


def other_button_hook(
    obj: UObject,
    args: WrappedStruct,
    _3: Any,
    _4: BoundFunction,
) -> None:
    global mods_menu_idx

    pressed_idx = None

    pressed_button = args.PressedButton
    for idx, entry in enumerate(obj.MenuItems):
        if entry.MenuItem == pressed_button:
            pressed_idx = idx
            break

    menu_state = get_menu_state(obj)

    if menu_state == 0 and pressed_idx == mods_menu_idx:
        mods_menu_idx = None
        set_menu_state(obj, 1000)

        begin_configure_menu_items(obj)
        add_menu_item(obj, "Big Mod Header?", "OnOtherButtonClicked", True, -1)
        add_menu_item(obj, "mod B", "OnOtherButtonClicked", False, -1)
        add_menu_item(obj, "mod C", "OnOtherButtonClicked", False, -1)

    if menu_state == 1000:

        def setup_options(self: UObject) -> None:
            add_button(self, "Description", description="some long description goes here")
            add_bool_spinner(self, "Enabled", False)
            add_title(self, "Options")
            add_dropdown(self, "dropdown", 2, ["1", "2", "3", "4"])
            add_slider(self, "slider", 5.2, 1, 10, 0.1)
            add_spinner(self, "spinner", 0, ["A", "B", "C"], True)
            add_title(self, "Keybinds")
            for i in range(10):
                add_binding(
                    self,
                    f"bind {i}",
                    '<img src="img://Game/UI/_Shared/GamepadButtonIcons/Keyboard/PC_W.PC_W"/>',
                )

        open_custom_options(obj, "Some Mod", setup_options)


set_add_menu_item_callback(add_menu_item_hook)
remove_hook(
    "/Script/OakGame.GFxOakMainMenu:OnOtherButtonClicked",
    Type.PRE,
    __file__,
)
add_hook(
    "/Script/OakGame.GFxOakMainMenu:OnOtherButtonClicked",
    Type.PRE,
    __file__,
    other_button_hook,
)


def unimplemented_option_hook(
    obj: UObject,
    args: WrappedStruct,
    _3: Any,
    _4: BoundFunction,
) -> None:
    print(args)
    button = args.PressedButton

    match button.Class.Name:
        case "GbxGFxListItemComboBox":
            print(get_combo_box_selected_idx(button))
        case "GbxGFxListItemNumber":
            print(get_number_value(button))
        case "GbxGFxListItemSpinner":
            print(get_spinner_selected_idx(button))
        case "GbxGFxListItemControls":

            def setup_options(self: UObject) -> None:
                add_button(self, "Description", description="some long description goes here")
                add_bool_spinner(self, "Enabled", False)
                add_title(self, "Options")
                add_dropdown(self, "dropdown", 2, ["1", "2", "3", "4"])
                add_slider(self, "slider", 5.2, 1, 10, 0.1)
                add_spinner(self, "spinner", 0, ["A", "B", "C"], True)
                add_title(self, "Keybinds")
                for i in range(10):
                    add_binding(
                        self,
                        f"bind {i}",
                        '<img src="img://Game/UI/_Shared/GamepadButtonIcons/Keyboard/PC_Q.PC_Q"/>',
                    )

            refresh_options(obj, setup_options)
        case _:

            def setup_dialog(struct: WrappedStruct) -> None:
                struct.HeaderText = "header"
                struct.BodyText = ("body " * 5 + "\n") * 5
                struct.Choices = [
                    unrealsdk.make_struct(
                        "GbxGFxDialogBoxChoiceInfo",
                        LabelText="Test",
                        bCloseDialogOnSelection=True,
                    ),
                ]

            engine = unrealsdk.find_object("OakGameEngine", "/Engine/Transient.OakGameEngine_0")
            show_dialog_box(engine.GameInstance, setup_dialog)


remove_hook(
    "/Script/OakGame.GFxOptionBase:OnUnimplementedOptionClicked",
    Type.PRE,
    __file__,
)
add_hook(
    "/Script/OakGame.GFxOptionBase:OnUnimplementedOptionClicked",
    Type.PRE,
    __file__,
    unimplemented_option_hook,
)


def dialog_box_hook(
    _1: UObject,
    args: WrappedStruct,
    _3: Any,
    _4: BoundFunction,
) -> Block:
    print(args)
    return Block()


remove_hook(
    "/Script/OakGame.OakGameInstance:OnNATHelpChoiceMade",
    Type.PRE,
    "test",
)
add_hook(
    "/Script/OakGame.OakGameInstance:OnNATHelpChoiceMade",
    Type.PRE,
    "test",
    dialog_box_hook,
)
