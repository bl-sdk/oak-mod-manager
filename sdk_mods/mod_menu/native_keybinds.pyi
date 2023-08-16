from __future__ import annotations

from collections.abc import Callable
from enum import auto
from typing import TypeAlias

from unrealsdk.hooks import Block
from unrealsdk.unreal._uenum import UnrealEnum

__all__: tuple[str, ...] = (
    "set_gameplay_keybind_callback",
    "set_menu_keybind_callback",
)

class _EInputEvent(UnrealEnum):
    IE_Pressed = auto()
    IE_Released = auto()
    IE_Repeat = auto()
    IE_DoubleClick = auto()
    IE_Axis = auto()
    IE_MAX = auto()

_KeybindCallback: TypeAlias = Callable[[str, _EInputEvent], None | Block | type[Block]]

def set_gameplay_keybind_callback(callback: _KeybindCallback) -> None:
    """
    Sets the callback to use for gameplay keybinds.

    Keybind callbacks take two positional args:
        key: The key which was pressed.
        event: Which type of input happened.

    Keybind callbacks can return the sentinel `Block` type (or an instance thereof)
    in order to block normal processing of the key event.

    Args:
        callback: The callback to use.
    """

def set_menu_keybind_callback(callback: _KeybindCallback) -> None:
    """
    Sets the callback to use for menu keybinds.

    Keybind callbacks take two positional args:
        key: The key which was pressed.
        event: Which type of input happened.

    Keybind callbacks can return the sentinel `Block` type (or an instance thereof)
    in order to block normal processing of the key event.

    Args:
        callback: The callback to use.
    """
