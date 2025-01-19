from functools import wraps
from typing import cast

from mods_base import KeybindType
from mods_base.keybinds import KeybindCallback_Event, KeybindCallback_NoArgs
from mods_base.mod_list import base_mod

from .keybinds import deregister_keybind, register_keybind

__all__: tuple[str, ...] = (
    "__author__",
    "__version__",
    "__version_info__",
)

__version_info__: tuple[int, int] = (2, 5)
__version__: str = f"{__version_info__[0]}.{__version_info__[1]}"
__author__: str = "bl-sdk"


@wraps(KeybindType._enable)  # pyright: ignore[reportPrivateUsage]
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


KeybindType._enable = enable_keybind  # pyright: ignore[reportPrivateUsage]


@wraps(KeybindType._disable)  # pyright: ignore[reportPrivateUsage]
def disable_keybind(self: KeybindType) -> None:
    self.is_enabled = False

    handle = getattr(self, "_kb_handle", None)
    if handle is None:
        return

    deregister_keybind(handle)
    self._kb_handle = None  # type: ignore


KeybindType._disable = disable_keybind  # pyright: ignore[reportPrivateUsage]


@wraps(KeybindType._rebind)  # pyright: ignore[reportPrivateUsage]
def rebind_keybind(self: KeybindType, new_key: str | None) -> None:
    handle = getattr(self, "_kb_handle", None)
    if handle is not None:
        deregister_keybind(handle)

    if self.is_enabled:
        self.key = new_key
        enable_keybind(self)


KeybindType._rebind = rebind_keybind  # pyright: ignore[reportPrivateUsage]


base_mod.components.append(base_mod.ComponentInfo("Keybinds", __version__))
