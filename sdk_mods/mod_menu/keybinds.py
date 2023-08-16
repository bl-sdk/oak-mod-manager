from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Self, TypeAlias

from unrealsdk import find_enum, logging
from unrealsdk.hooks import Block

from .native_keybinds import set_gameplay_keybind_callback

if TYPE_CHECKING:
    from .native_keybinds import _EInputEvent  # pyright: ignore[reportPrivateUsage]

    EInputEvent = _EInputEvent
else:
    EInputEvent = find_enum("EInputEvent")

KeybindBlockSignal: TypeAlias = None | Block | type[Block]
KeybindCallback = Callable[[], KeybindBlockSignal] | Callable[[EInputEvent], KeybindBlockSignal]

__all__: tuple[str, ...] = (
    "Keybind",
    "all_gameplay_keybinds",
)


@dataclass
class Keybind:
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


# TEMPORARY: will need to rework based on mod list
all_gameplay_keybinds: list[Keybind] = []


def gameplay_keybind_callback(key: str, event: EInputEvent) -> None | Block | type[Block]:
    """Gameplay keybind handler."""

    ret: KeybindBlockSignal = None
    for bind in all_gameplay_keybinds:
        if bind.callback is None:
            continue
        if bind.key != key:
            continue

        callback: Callable[[], KeybindBlockSignal]
        if len(inspect.signature(bind.callback).parameters) == 0:
            if event != EInputEvent.IE_Pressed:
                continue

            callback = bind.callback  # type: ignore  # noqa: PGH003
        else:
            callback = functools.partial(bind.callback, event)

        # Need to put ret on the RHS to avoid short circuits
        ret = callback() or ret
    return ret


set_gameplay_keybind_callback(gameplay_keybind_callback)
