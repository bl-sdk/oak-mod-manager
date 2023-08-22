from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Self, TypeAlias

from unrealsdk import find_enum, logging
from unrealsdk.hooks import Block

from .native.keybinds import set_gameplay_keybind_callback

if TYPE_CHECKING:
    from .native.keybinds import _EInputEvent  # pyright: ignore[reportPrivateUsage]

    EInputEvent = _EInputEvent
else:
    EInputEvent = find_enum("EInputEvent")

__all__: tuple[str, ...] = ("Keybind",)

KeybindBlockSignal: TypeAlias = None | Block | type[Block]
KeybindCallback = Callable[[], KeybindBlockSignal] | Callable[[EInputEvent], KeybindBlockSignal]


@dataclass
class Keybind:
    """
    Represents a single keybind.

    Attributes:
        name: The name to use in the keybinds menu
        key: The bound key, or None if unbound. Updated on rebind.
        is_rebindable: If the key may be rebound.
        is_hidden: If the key displays in the keybinds menu.
        callback: The callback to run when the key is pressed.
        default_key: What the key was originally when registered. Does not change on rebind.
    """

    name: str
    key: str | None = None
    is_rebindable: bool = True
    is_hidden: bool = False

    callback: KeybindCallback | None = None

    default_key: str | None = field(default=key, init=False)

    def __post_init__(self) -> None:
        self.default_key = self.key

    def __call__(self, callback: KeybindCallback) -> Self:
        """
        Sets this keybind's callback.

        This allows this class to be constructed using decorator syntax, though note it is *not* a
        decorator, it returns itself so must be the outermost level.

        Args:
            callback: The callback to set.
        Returns:
            This keybind instance.
        """
        if self.callback is not None:
            logging.dev_warning(
                "Keybind.__call__ was called on a bind which already has an assigned callback",
            )

        self.callback = callback
        return self


def run_callback(callback: KeybindCallback, event: EInputEvent) -> KeybindBlockSignal:
    """
    Runs a keybind callback for the given event, if applicable.

    If the keybind callback has no args, only runs it on pressed events, and returns None otherwise.
    If it takes args, always calls it, passing the event.

    Args:
        callback: The callback to run.
        event: The event to run the callback for.
    Returns:
        The callback's result.
    """
    argless_callback: Callable[[], KeybindBlockSignal]
    if len(inspect.signature(callback).parameters) == 0:
        if event != EInputEvent.IE_Pressed:
            return None

        argless_callback = callback  # type: ignore  # noqa: PGH003
    else:
        argless_callback = functools.partial(callback, event)

    return argless_callback()


# Must import after defining keybind to avoid circular import
from .mod import mod_list  # noqa: E402


def gameplay_keybind_callback(key: str, event: EInputEvent) -> KeybindBlockSignal:
    """Gameplay keybind handler."""

    ret: KeybindBlockSignal = None
    for mod in mod_list:
        for bind in mod.keybinds:
            if bind.callback is None:
                continue
            if bind.key != key:
                continue

            # Need to put ret on the RHS to avoid short circuits
            ret = run_callback(bind.callback, event) or ret
    return ret


set_gameplay_keybind_callback(gameplay_keybind_callback)
