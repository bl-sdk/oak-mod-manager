from __future__ import annotations

from collections.abc import Callable
from enum import auto
from typing import TypeAlias

from unrealsdk.hooks import Block
from unrealsdk.unreal import UObject
from unrealsdk.unreal._uenum import UnrealEnum

__all__: tuple[str, ...] = ("set_keybind_callback",)

class _EInputEvent(UnrealEnum):
    IE_Pressed = auto()
    IE_Released = auto()
    IE_Repeat = auto()
    IE_DoubleClick = auto()
    IE_Axis = auto()
    IE_MAX = auto()

_OakPlayerController: TypeAlias = UObject
_KeybindCallback: TypeAlias = Callable[
    [_OakPlayerController, str, _EInputEvent],
    None | Block | type[Block],
]

def set_keybind_callback(callback: _KeybindCallback) -> None:
    """
    Sets the keybind callback.

    The callback takes three positional args:
        pc: The OakPlayerController which caused the event.
        key: The key which was pressed.
        event: Which type of input happened.

    The callback may return the sentinel `Block` type (or an instance thereof) in
    order to block normal processing of the key event.

    Args:
        callback: The callback to use.
    """
