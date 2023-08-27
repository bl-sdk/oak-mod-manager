from collections.abc import Callable
from typing import TypeAlias

from unrealsdk.unreal import UObject

_GFxMainAndPauseBaseMenu: TypeAlias = UObject
_GFxOptionBase: TypeAlias = UObject

__all__: tuple[str, ...] = ("open_custom_options",)

def open_custom_options(
    self: _GFxMainAndPauseBaseMenu,
    name: str,
    callback: Callable[[_GFxOptionBase], None],
) -> None:
    """
    Opens a custom options menu.

    Uses a callback to specify the menu's entries. This callback takes a single
    positional arg, the option menu to add entires to. It's return value is ignored.

    Args:
        self: The current menu object to open under.
        name: The name of the options menu to open.
        callback: The setup callback to use.
    """

def refresh_options(self: _GFxOptionBase, callback: Callable[[_GFxOptionBase], None]) -> None:
    """
    Refreshes the current custom options menu, allowing changing it's entries.

    Uses a callback to specify the menu's entries. This callback takes a single
    positional arg, the option menu to add entires to. It's return value is ignored.

    Args:
        self: The current menu object to open under.
        callback: The setup callback to use.
    """
