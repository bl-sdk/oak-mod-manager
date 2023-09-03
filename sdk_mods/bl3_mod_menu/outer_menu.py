# ruff: noqa: D103

import re
from typing import Any

import unrealsdk
from mods_base import Mod, get_ordered_mod_list, hook
from unrealsdk.hooks import Type
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

from .native.outer_menu import (
    add_menu_item,
    begin_configure_menu_items,
    get_menu_state,
    set_add_menu_item_callback,
    set_menu_state,
)
from .options_setup import on_options_close, open_options_menu

MAIN_MENU_CLS = unrealsdk.find_class("GFxOakMainMenu")

RE_FONT_TAG = re.compile(r"\s+<font", re.I)
DISABLED_GRAY = "#778899"  # lightslategray

MENU_STATE_OUTERMOST_MAIN_MENU = 0
MENU_STATE_MODS_LIST = 1417


# The index the mods menu was in the outermost main menu last time it was drawn
last_mods_menu_idx: int = -1

# The list of mods we used when drawing the mod list last time
last_displayed_mod_list: list[Mod] = []


@set_add_menu_item_callback
def add_menu_item_hook(
    self: UObject,
    text: str,
    callback_name: str,
    big: bool,
    always_minus_one: int,
) -> int:
    idx = add_menu_item(self, text, callback_name, big, always_minus_one)

    if callback_name == "OnStoreClicked":
        global last_mods_menu_idx
        last_mods_menu_idx = add_menu_item(self, "MODS", "OnOtherButtonClicked", False, -1)

    return idx


def draw_mods_list(main_menu: UObject) -> None:
    """
    Draws the mods list.

    Args:
        main_menu: The main menu to draw within.
    """
    global last_displayed_mod_list
    last_displayed_mod_list = get_ordered_mod_list()

    begin_configure_menu_items(main_menu)
    for mod in last_displayed_mod_list:
        formatted_name = mod.name

        # If the mod is disabled, and doesn't appear to start with a font tag already, make it gray
        if not mod.is_enabled and not RE_FONT_TAG.match(mod.name):
            formatted_name = f"<font color='{DISABLED_GRAY}'>{mod.name}</font>"

        add_menu_item(main_menu, formatted_name, "OnOtherButtonClicked", False, -1)

    # If we have too many mods, they'll end up scrolling behind the news box
    # To avoid this, add some dummy entries
    # To make it less obvious, since they still have a highlight, only do so when there are too many
    if len(last_displayed_mod_list) > 8:
        for _ in range(4):
            add_menu_item(main_menu, "", "", True, -1)


@hook("/Script/OakGame.GFxFrontendMenu:OnMenuStackChanged", Type.POST, auto_enable=True)
def frontend_menu_change_hook(
    _1: UObject,
    args: WrappedStruct,
    _3: Any,
    _4: BoundFunction,
) -> None:
    active_menu: UObject = args.ActiveMenu

    # If we transisitoned back onto the main menu, and we're looking at the mod list
    if (
        active_menu.Class._inherits(MAIN_MENU_CLS)
        and get_menu_state(active_menu) == MENU_STATE_MODS_LIST
    ):
        # Refresh it, so that we update the enabled/disabled coloring
        draw_mods_list(active_menu)

        on_options_close()


@hook("/Script/OakGame.GFxOakMainMenu:OnOtherButtonClicked", Type.PRE, auto_enable=True)
def other_button_hook(
    obj: UObject,
    args: WrappedStruct,
    _3: Any,
    _4: BoundFunction,
) -> None:
    pressed_idx: int
    pressed_button = args.PressedButton
    for idx, entry in enumerate(obj.MenuItems):
        if entry.MenuItem == pressed_button:
            pressed_idx = idx
            break
    else:
        raise ValueError("Couldn't find button which was pressed!")

    menu_state = get_menu_state(obj)

    if menu_state == MENU_STATE_OUTERMOST_MAIN_MENU and pressed_idx == last_mods_menu_idx:
        set_menu_state(obj, MENU_STATE_MODS_LIST)
        draw_mods_list(obj)

    if menu_state == MENU_STATE_MODS_LIST:
        open_options_menu(obj, last_displayed_mod_list[pressed_idx])
