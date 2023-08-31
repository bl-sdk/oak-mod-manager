from typing import Final

from .keybinds import EInputEvent, KeybindBlockSignal, KeybindCallback, run_callback
from .native.keybinds import set_menu_keybind_callback

__all__: tuple[str, ...] = (
    "push",
    "pop",
    "register",
    "unregister",
    "ANY_KEY",
)

"""
Menu keybinds, unsurprisingly, fire in menus. They have no mod association, cannot be rebound and
thus not appear in the keybinds menu, and cannot have duplicates.

Menu keybinds work off of a stack. The top of the stack represents the currently focused menu, only
keybinds registered within it are processed. On opening a new menu, with different binds, you should
push a new frame, and register binds within it.

The sentinel `ANY_KEY` can be registered to accept all key presses, with the highest priority.
"""

ANY_KEY: Final[str] = ""

menu_callback_stack: list[dict[str, KeybindCallback]] = []


def push() -> None:
    """Pushes a new set of menu keybinds."""
    menu_callback_stack.append({})


def pop() -> None:
    """Pops the current set of menu keybinds."""
    menu_callback_stack.pop()


def register(key: str, callback: KeybindCallback) -> None:
    """
    Registers a menu keybind.

    Args:
        key: The key to register under.
        callback: The callback to run when the key is pressed.
    """
    menu_callback_stack[-1][key] = callback


def unregister(key: str) -> None:
    """
    Unregisters a menu keybind.

    Args:
        key: The key to remove.
    """
    del menu_callback_stack[-1][key]


def menu_keybind_callback(key: str, event: EInputEvent) -> KeybindBlockSignal:
    """Menu keybind handler."""

    if len(menu_callback_stack) == 0:
        return None

    frame = menu_callback_stack[-1]

    callback: KeybindCallback
    if ANY_KEY in frame:
        callback = frame[ANY_KEY]
    elif key in frame:
        callback = frame[key]
    else:
        return None

    return run_callback(callback, event)


set_menu_keybind_callback(menu_keybind_callback)
