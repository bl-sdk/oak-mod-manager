from typing import Any

from unrealsdk.hooks import Type, add_hook, remove_hook
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

from .native.options_transition import open_custom_options
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
            print(f"setting up options: {self}")

        open_custom_options(obj, "mod options", setup_options)


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
    _1: UObject,
    args: WrappedStruct,
    _3: Any,
    _4: BoundFunction,
) -> None:
    print(args)


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
