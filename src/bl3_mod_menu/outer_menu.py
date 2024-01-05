import re
from typing import Any

import unrealsdk
from mods_base import BoolOption, Mod, get_ordered_mod_list, hook
from unrealsdk.hooks import Block, Type
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

from .native.outer_menu import (
    add_menu_item,
    begin_configure_menu_items,
    get_menu_state,
    set_add_menu_item_callback,
    set_menu_state,
)
from .options_setup import open_options_menu

MAIN_PAUSE_MENU_CLS = unrealsdk.find_class("GFxMainAndPauseBaseMenu")

RE_FONT_TAG = re.compile(r"\s+<font", re.I)
DISABLED_GRAY = "#778899"  # lightslategray

MENU_STATE_OUTERMOST_MAIN_MENU = 0
MENU_STATE_MODS_LIST = 1417


# The index the mods menu was in the outermost main menu last time it was drawn
last_mods_menu_idx: int = -1

# The list of mods we used when drawing the mod list last time
last_displayed_mod_list: list[Mod] = []

hide_behind_the_scenes = BoolOption(
    "Hide Behind The Scenes Menu",
    False,
    description="Hides the 'Behind The Scenes' option from the main menu.",
)
hide_store = BoolOption(
    "Hide Store Menu",
    True,
    description="Hides the 'Store' option from the main menu.",
)
hide_achievements = BoolOption(
    "Hide Achievements Menu",
    True,
    description=(
        "Hides the 'Achievements' option from the pause menu. Useful to prevent ruining SQ muscle"
        " memory."
    ),
)
hide_photo_mode = BoolOption(
    "Hide Photo Mode Menu",
    False,
    description=(
        "Hides the 'Photo Mode' option from the pause menu. Useful to prevent ruining SQ muscle"
        " memory."
    ),
)

hide_menu_options = {
    "OnBehindTheScenesClicked": hide_behind_the_scenes,
    "OnStoreClicked": hide_store,
    "OnAchievementsClicked": hide_achievements,
    "OnPhotoModeClicked": hide_photo_mode,
}


@set_add_menu_item_callback
def add_menu_item_hook(
    self: UObject,
    text: str,
    callback_name: str,
    big: bool,
    always_minus_one: int,
) -> int:
    """Hook to inject the outermost mods option."""

    # Add the mods option right before quit
    if callback_name == "OnQuitClicked":
        global last_mods_menu_idx
        last_mods_menu_idx = add_menu_item(self, "MODS", "OnInviteListClearClicked", False, -1)

    if callback_name in hide_menu_options and hide_menu_options[callback_name].value:
        # Surprisingly, just setting the return value to -1 just works, no menu item is drawn and
        # nothing seems to go wrong
        idx = -1
    else:
        # Show the item properly
        idx = add_menu_item(self, text, callback_name, big, always_minus_one)

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

        add_menu_item(main_menu, formatted_name, "OnInviteListClearClicked", False, -1)

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
    """Hook to refresh the mods list when leaving the options menu."""
    active_menu: UObject = args.ActiveMenu

    # If we transisitoned back onto the main menu, and we're looking at the mod list
    if (
        active_menu.Class._inherits(MAIN_PAUSE_MENU_CLS)
        and get_menu_state(active_menu) == MENU_STATE_MODS_LIST
    ):
        # Refresh it, so that we update the enabled/disabled coloring
        draw_mods_list(active_menu)


@hook(
    "/Script/OakGame.GFxMainAndPauseBaseMenu:OnInviteListClearClicked",
    Type.PRE,
    auto_enable=True,
)
def other_button_hook(
    obj: UObject,
    args: WrappedStruct,
    _3: Any,
    _4: BoundFunction,
) -> None | type[Block]:
    """Hook to detect clicking menu items."""
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
        return Block

    if menu_state == MENU_STATE_MODS_LIST:
        open_options_menu(obj, last_displayed_mod_list[pressed_idx])
        return Block

    return None
