from __future__ import annotations

from enum import auto
from typing import TypeAlias

from unrealsdk.unreal import UObject
from unrealsdk.unreal._uenum import UnrealEnum

_GFxMainAndPauseBaseMenu: TypeAlias = UObject

class _EMenuTransition(UnrealEnum):
    CreateCharacterMenu_MainMenu = auto()
    LoadCharacterMenu_MainMenu = auto()
    MainMenu_LoadCharacterMenu = auto()
    MainMenu_NewGameSettingMenu = auto()
    MainMenu_OptionMenu = auto()
    NewGameSettingsMenu_MainMenu = auto()
    OptionMenu_MainMenu = auto()
    TitleScreen_MainMenu = auto()
    TitleScreen_FirstBoot = auto()
    FirstBoot_MainMenu = auto()
    PlaythroughSelectionMenu_MainMenu = auto()
    MainMenu_PlaythroughSelectionMenu = auto()
    Invalid = auto()
    # None = auto()  # NOTE: this is the actual name, conflicting with python's `None``
    EMenuTransition_MAX = auto()

def do_options_menu_transition(
    self: _GFxMainAndPauseBaseMenu,
    first_option: int,
    transition: _EMenuTransition = _EMenuTransition(0xD),  # noqa: B008  # Equivalent to `None`
    controller_id: int = 0,
) -> None:
    """
    Performs an options menu transition.

    Args:
        self: The current menu object to perform the transition on.
        first_option: The value to set the first option to look at to.
        transition: What type of transition to perform.
        controller_id: The controller id to perform the transition with.
    """
