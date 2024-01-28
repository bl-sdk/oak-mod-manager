from collections.abc import Callable

from unrealsdk.unreal import UObject

type _GFxMainAndPauseBaseMenu = UObject
type _GFxOptionBase = UObject

__all__: tuple[str, ...] = ("open_custom_options",)

def open_custom_options(
    self: _GFxMainAndPauseBaseMenu,
    name: str,
    callback: Callable[[_GFxOptionBase], None],
) -> None:
    """
    Opens a custom options menu.

    Uses a callback to specify the menu's entries. This callback takes a single
    positional arg, the option menu to add entries to. It's return value is ignored.

    Args:
        self: The current menu object to open under.
        name: The name of the options menu to open.
        callback: The setup callback to use.
    """

def refresh_options(
    self: _GFxOptionBase,
    callback: Callable[[_GFxOptionBase], None],
    preserve_scroll: bool = True,
) -> None:
    """
    Refreshes the current custom options menu, allowing changing it's entries.

    Uses a callback to specify the menu's entries. This callback takes a single
    positional arg, the option menu to add entries to. It's return value is ignored.

    Args:
        self: The current menu object to open under.
        callback: The setup callback to use.
        preserve_scroll: If true, preserves the current scroll position.
    """
