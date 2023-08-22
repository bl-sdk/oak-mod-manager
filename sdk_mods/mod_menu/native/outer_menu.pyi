from collections.abc import Callable
from typing import TypeAlias

from unrealsdk.unreal import UObject

_AddMenuItemCallback: TypeAlias = Callable[[UObject, str, str, bool, int], int]

def add_menu_item(
    self: UObject,
    text: str,
    callback_name: str,
    big: bool,
    always_minus_one: int,
) -> int: ...
def set_add_menu_item_callback(callback: _AddMenuItemCallback) -> None: ...
def begin_configure_menu_items(self: UObject) -> None: ...
def set_menu_state(self: UObject, value: int) -> None: ...
def get_menu_state(self: UObject) -> int: ...
