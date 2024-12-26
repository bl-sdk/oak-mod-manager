from __future__ import annotations

from collections.abc import Callable
from typing import NewType, overload

from unrealsdk.hooks import Block

from mods_base import EInputEvent

__all__: tuple[str, ...] = (
    "deregister_keybind",
    "register_keybind",
)

_KeybindHandle = NewType("_KeybindHandle", object)
type _BlockSignal = None | Block | type[Block]

@overload
def register_keybind(
    key: str,
    event: EInputEvent,
    gameplay_bind: bool,
    callback: Callable[[], _BlockSignal],
) -> _KeybindHandle: ...
@overload
def register_keybind(
    key: None,
    event: EInputEvent,
    gameplay_bind: bool,
    callback: Callable[[str], _BlockSignal],
) -> _KeybindHandle: ...
@overload
def register_keybind(
    key: str,
    event: None,
    gameplay_bind: bool,
    callback: Callable[[EInputEvent], _BlockSignal],
) -> _KeybindHandle: ...
@overload
def register_keybind(
    key: None,
    event: None,
    gameplay_bind: bool,
    callback: Callable[[str, EInputEvent], _BlockSignal],
) -> _KeybindHandle: ...
def register_keybind(
    key: str | None,
    event: EInputEvent | None,
    gameplay_bind: bool,
    callback: Callable[..., _BlockSignal],
) -> _KeybindHandle:
    """
    Registers a new keybind.

    If key or event are None, any key or event will be matched, and their values
    will be passed back to the callback. Therefore, based on these args, the
    callback is run with 0-2 arguments.

    The callback may return the sentinel `Block` type (or an instance thereof) in
    order to block normal processing of the key event.

    Args:
        key: The key to match, or None to match any.
        event: The key event to match, or None to match any.
        gameplay_bind: True if this keybind should only trigger during gameplay.
        callback: The callback to use.
    Returns:
        An opaque handle to be used in calls to deregister_keybind.
    """

def deregister_keybind(handle: _KeybindHandle) -> None:
    """
    Removes a previously registered keybind.

    Does nothing if the passed handle is invalid.

    Args:
        handle: The handle returned from `register_keybind`.
    """

def _deregister_by_key(key: str | None) -> None:
    """
    Deregisters all keybinds matching the given key.

    Not intended for regular use, only exists for recovery during debugging, in case
    a handle was lost.

    Args:
        key: The key to remove all keybinds of.
    """

def _deregister_all() -> None:
    """
    Deregisters all keybinds.

    Not intended for regular use, only exists for recovery during debugging, in case
    a handle was lost.
    """
