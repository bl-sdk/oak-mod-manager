from __future__ import annotations

from collections.abc import Callable
from typing import TypeAlias

from mods_base import EInputEvent
from unrealsdk.hooks import Block
from unrealsdk.unreal import UObject

__all__: tuple[str, ...] = ("set_keybind_callback",)

_OakPlayerController: TypeAlias = UObject
_KeybindCallback: TypeAlias = Callable[
    [_OakPlayerController, str, EInputEvent],
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
