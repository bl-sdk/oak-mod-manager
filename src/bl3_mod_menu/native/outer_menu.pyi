from collections.abc import Callable

from unrealsdk.unreal import UObject

__all__: tuple[str, ...] = (
    "add_menu_item",
    "set_add_menu_item_callback",
    "begin_configure_menu_items",
    "set_menu_state",
    "get_menu_state",
)

type _AddMenuItemCallback = Callable[[UObject, str, str, bool, int], int]
type _GFxMainAndPauseBaseMenu = UObject

def add_menu_item(
    self: _GFxMainAndPauseBaseMenu,
    text: str,
    callback_name: str,
    big: bool,
    always_minus_one: int,
) -> int:
    r"""
    Calls GFxMainAndPauseBaseMenu::AddMenuItem. This does not trigger a callback.

    Args:
        self: The object to call on.
        text: The text to display in the menu.
        callback_name: The name of the unreal callback to use.
        big: True if the menu item should be big.
        always_minus_one: Always -1. ¯\_(ツ)_/¯
    Returns:
        The index of the inserted menu item.
    """

def set_add_menu_item_callback(callback: _AddMenuItemCallback) -> None:
    """
    Sets the callback to use when GFxMainAndPauseBaseMenu::AddMenuItem is called.

    This callback will be passed all 5 args positionally, and must return the return
    value to use - i.e. a no-op callback is `lambda *args: add_menu_item(*args)`.

    Args:
        callback: The callback to use.
    """

def begin_configure_menu_items(self: _GFxMainAndPauseBaseMenu) -> None:
    """
    Calls GFxMainAndPauseBaseMenu::AddMenuItem.

    Args:
        self: The object to call on.
    """

def set_menu_state(self: _GFxMainAndPauseBaseMenu, state: int) -> None:
    """
    Calls GFxMainAndPauseBaseMenu::SetMenuState.

    Args:
        self: The object to call on.
        state: The state to set the menu to.
    """

def get_menu_state(self: _GFxMainAndPauseBaseMenu) -> int:
    """
    Gets the menu state, which was previously set by a call to set menu state.

    Args:
        self: The object to get the state of.
    Returns:
        The object's menu state.
    """
