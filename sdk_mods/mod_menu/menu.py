from typing import Any

from unrealsdk.hooks import Type, add_hook, remove_hook
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

from .native import options

# from .create_option_description_item import EOptionItemType, create_option_description_item
# from .native.options_menu import do_options_menu_transition, set_option_refresh_callback
from .native.outer_menu import (
    add_menu_item,
    begin_configure_menu_items,
    get_menu_state,
    set_add_menu_item_callback,
    set_menu_state,
)

mods_menu_idx: int | None = None
next_option_refresh_is_mod: bool = False


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
        global next_option_refresh_is_mod
        next_option_refresh_is_mod = True
        options.inject(obj)


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

"""
def options_refresh_hook(items: list[UObject]) -> None:
    global next_option_refresh_is_mod

    if next_option_refresh_is_mod:
        items[:] = [
            create_option_description_item(
                OptionType=255,
                OptionItemType=EOptionItemType.Title,
                OptionItemName="Mod Options",
            ),
            create_option_description_item(
                OptionType=255,
                OptionItemType=EOptionItemType.Slider,
                OptionItemName="slider",
                OptionDescriptionTitle="this is no longer stealing the id of the dialog volume slider",
                OptionDescriptionText=(
                    "how many lines can I have\n" * 12 + "13 before it starts scaling down"
                ),
                SliderMin=0.0,
                SliderMax=100.0,
                SliderStep=1.0,
                SliderIsInteger=True,
            ),
            create_option_description_item(
                OptionType=255,
                OptionItemType=EOptionItemType.BooleanSpinner,
                OptionItemName="bool spinner",
            ),
            create_option_description_item(
                OptionType=255,
                OptionItemType=EOptionItemType.TodoItem,
                OptionItemName="todo??",
            ),
        ]

        print(items)

    next_option_refresh_is_mod = False


set_option_refresh_callback(options_refresh_hook)
"""


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
