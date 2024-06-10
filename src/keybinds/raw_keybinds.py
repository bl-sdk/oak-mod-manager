from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast, overload

from mods_base.keybinds import EInputEvent, KeybindBlockSignal

from .keybinds import deregister_keybind, register_keybind

if TYPE_CHECKING:
    from .keybinds import _KeybindHandle  # pyright: ignore[reportPrivateUsage]

__all__: tuple[str, ...] = (
    "add",
    "pop",
    "push",
)

"""
This module allows for raw access to all key events. It is intended for short term use, to
temporarily add some extra callbacks, primarily to help enhance menus.

Raw keybinds work off of a stack. The top of the stack represents the currently focused menu, only
callbacks within it are processed. On opening a new menu, with different focus, you should push a
new frame, and register callbacks within it. On closing a menu, you should pop it's frame.

Raw keybinds follow the standard blocking logic when multiple callbacks receive the same event. Raw
keybinds are processed *before* gameplay keybinds, so a raw keybind specifying to block the input
will prevent any matching gameplay keybinds from being run.
"""

type RawKeybindCallback_KeyAndEvent = Callable[[str, EInputEvent], KeybindBlockSignal]
type RawKeybindCallback_KeyOnly = Callable[[str], KeybindBlockSignal]
type RawKeybindCallback_EventOnly = Callable[[EInputEvent], KeybindBlockSignal]
type RawKeybindCallback_NoArgs = Callable[[], KeybindBlockSignal]

type RawKeybindCallback_Any = (
    RawKeybindCallback_KeyAndEvent
    | RawKeybindCallback_KeyOnly
    | RawKeybindCallback_EventOnly
    | RawKeybindCallback_NoArgs
)
type RawKeybindDecorator_Any = (
    Callable[[RawKeybindCallback_KeyAndEvent], None]
    | Callable[[RawKeybindCallback_KeyOnly], None]
    | Callable[[RawKeybindCallback_EventOnly], None]
    | Callable[[RawKeybindCallback_NoArgs], None]
)


@dataclass
class RawKeybind:
    key: str | None
    event: EInputEvent | None
    callback: RawKeybindCallback_Any

    _handle: _KeybindHandle | None = None

    def enable(self) -> None:
        """Enables this keybind."""
        if self._handle is not None:
            self.disable()

        # Redundancy for type checking
        if self.key is None:
            if self.event is None:
                self._handle = register_keybind(
                    self.key,
                    self.event,
                    False,
                    cast(RawKeybindCallback_KeyAndEvent, self.callback),
                )
            else:
                self._handle = register_keybind(
                    self.key,
                    self.event,
                    False,
                    cast(RawKeybindCallback_KeyOnly, self.callback),
                )
        elif self.event is None:
            self._handle = register_keybind(
                self.key,
                self.event,
                False,
                cast(RawKeybindCallback_EventOnly, self.callback),
            )
        else:
            self._handle = register_keybind(
                self.key,
                self.event,
                False,
                cast(RawKeybindCallback_NoArgs, self.callback),
            )

    def disable(self) -> None:
        """Disables this keybind."""
        if self._handle is None:
            return

        deregister_keybind(self._handle)
        self._handle = None


raw_keybind_callback_stack: list[list[RawKeybind]] = []


def push() -> None:
    """Pushes a new raw keybind frame."""
    if raw_keybind_callback_stack:
        old_frame = raw_keybind_callback_stack[-1]
        for bind in old_frame:
            bind.disable()

    raw_keybind_callback_stack.append([])


def pop() -> None:
    """Pops the current raw keybind frame."""
    old_frame = raw_keybind_callback_stack.pop()
    for bind in old_frame:
        bind.disable()

    if raw_keybind_callback_stack:
        new_frame = raw_keybind_callback_stack[-1]
        for bind in new_frame:
            bind.enable()


@overload
def add(
    key: str,
    event: EInputEvent,
    callback: RawKeybindCallback_NoArgs,
) -> None: ...


@overload
def add(
    key: str,
    event: None,
    callback: RawKeybindCallback_EventOnly,
) -> None: ...


@overload
def add(
    key: None,
    event: EInputEvent,
    callback: RawKeybindCallback_KeyOnly,
) -> None: ...


@overload
def add(
    key: None,
    event: None,
    callback: RawKeybindCallback_KeyAndEvent,
) -> None: ...


@overload
def add(
    key: str,
    event: EInputEvent = EInputEvent.IE_Pressed,
    callback: None = None,
) -> Callable[[RawKeybindCallback_NoArgs], None]: ...


@overload
def add(
    key: str,
    event: None = None,
    callback: None = None,
) -> Callable[[RawKeybindCallback_EventOnly], None]: ...


@overload
def add(
    key: None,
    event: EInputEvent = EInputEvent.IE_Pressed,
    callback: None = None,
) -> Callable[[RawKeybindCallback_KeyOnly], None]: ...


@overload
def add(
    key: None,
    event: None = None,
    callback: None = None,
) -> Callable[[RawKeybindCallback_KeyAndEvent], None]: ...


def add(
    key: str | None,
    event: EInputEvent | None = EInputEvent.IE_Pressed,
    callback: RawKeybindCallback_Any | None = None,
) -> RawKeybindDecorator_Any | None:
    """
    Adds a new raw keybind callback in the current frame.

    Args:
        key: The key to filter to, or None to be passed all keys.
        event: The event to filter to, or None to be passed all events.
        callback: The callback to run. If None, this function acts as a decorator factory,
    Returns:
        If the callback was not explicitly provided, a decorator to register it.
    """

    def decorator(callback: RawKeybindCallback_Any) -> None:
        bind = RawKeybind(key, event, callback)
        raw_keybind_callback_stack[-1].append(bind)
        bind.enable()

    if callback is None:
        return decorator
    return decorator(callback)
