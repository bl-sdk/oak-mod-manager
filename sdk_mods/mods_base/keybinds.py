from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from dataclasses import KW_ONLY, dataclass, field
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

    Args:
        name: The name to use in the keybinds menu
        key: The bound key, or None if unbound. Updated on rebind.
        callback: The callback to run when the key is pressed.

    Keyword Args:
        description: A short description about the bind, to be used in the options menu.
        description_title: The title to use for the description. If None, copies the name.
        is_hidden: If true, the keybind will not be shown in the options menu.
        is_rebindable: If the key may be rebound.

    Extra Attributes:
        default_key: What the key was originally when registered. Does not update on rebind.
    """

    name: str
    key: str | None = None

    callback: KeybindCallback | None = None

    _: KW_ONLY
    description: str = ""
    description_title: str | None = None
    is_hidden: bool = False
    is_rebindable: bool = True

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


# Must import after defining keybind to avoid circular import
from .mod_list import mod_list  # noqa: E402


def gameplay_keybind_callback(key: str, event: EInputEvent) -> KeybindBlockSignal:
    """Gameplay keybind handler."""

    ret: KeybindBlockSignal = None
    for mod in mod_list:
        for bind in mod.keybinds:
            if bind.callback is None:
                continue
            if bind.key != key:
                continue

            argless_callback: Callable[[], KeybindBlockSignal]
            if len(inspect.signature(bind.callback).parameters) == 0:
                if event != EInputEvent.IE_Pressed:
                    continue

                argless_callback = bind.callback  # type: ignore
            else:
                argless_callback = functools.partial(bind.callback, event)

            # Need to put ret on the RHS to avoid short circuits
            ret = argless_callback() or ret

    return ret


set_gameplay_keybind_callback(gameplay_keybind_callback)
