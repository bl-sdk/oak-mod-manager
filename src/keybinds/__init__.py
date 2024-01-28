from functools import wraps
from typing import cast

from mods_base import KeybindType
from mods_base.keybinds import KeybindCallback_Event, KeybindCallback_NoArgs
from mods_base.mod_list import base_mod
from mods_base.raw_keybinds import (
    RawKeybind,
    RawKeybindCallback_EventOnly,
    RawKeybindCallback_KeyAndEvent,
    RawKeybindCallback_KeyOnly,
    RawKeybindCallback_NoArgs,
)

from .keybinds import deregister_keybind, register_keybind

__all__: tuple[str, ...] = (
    "__author__",
    "__version__",
    "__version_info__",
)

__version_info__: tuple[int, int] = (2, 0)
__version__: str = f"{__version_info__[0]}.{__version_info__[1]}"
__author__: str = "bl-sdk"


@wraps(KeybindType.enable)
def enable_keybind(self: KeybindType) -> None:
    if self.key is None or self.callback is None:
        return

    # While this is redundant, it keeps the type checking happy
    if self.event_filter is None:
        handle = register_keybind(
            self.key,
            self.event_filter,
            True,
            cast(KeybindCallback_Event, self.callback),
        )
    else:
        handle = register_keybind(
            self.key,
            self.event_filter,
            True,
            cast(KeybindCallback_NoArgs, self.callback),
        )

    self._kb_handle = handle  # type: ignore


KeybindType.enable = enable_keybind


@wraps(KeybindType.disable)
def disable_keybind(self: KeybindType) -> None:
    handle = getattr(self, "_kb_handle", None)
    if handle is None:
        return

    deregister_keybind(handle)
    self._kb_handle = None  # type: ignore


KeybindType.disable = disable_keybind


@wraps(RawKeybind.enable)
def enable_raw_keybind(self: RawKeybind) -> None:
    # Even more redundancy for type checking
    # Can't use a match statement since an earlier `case None:` doesn't remove None from later cases
    if self.key is None:
        if self.event is None:
            handle = register_keybind(
                self.key,
                self.event,
                False,
                cast(RawKeybindCallback_KeyAndEvent, self.callback),
            )
        else:
            handle = register_keybind(
                self.key,
                self.event,
                False,
                cast(RawKeybindCallback_KeyOnly, self.callback),
            )
    elif self.event is None:
        handle = register_keybind(
            self.key,
            self.event,
            False,
            cast(RawKeybindCallback_EventOnly, self.callback),
        )
    else:
        handle = register_keybind(
            self.key,
            self.event,
            False,
            cast(RawKeybindCallback_NoArgs, self.callback),
        )

    self._kb_handle = handle  # type: ignore


RawKeybind.enable = enable_raw_keybind


@wraps(RawKeybind.disable)
def disable_raw_keybind(self: RawKeybind) -> None:
    handle = getattr(self, "_kb_handle", None)
    if handle is None:
        return

    deregister_keybind(handle)
    self._kb_handle = None  # type: ignore


RawKeybind.disable = disable_raw_keybind


base_mod.components.append(base_mod.ComponentInfo("Keybinds", __version__))
