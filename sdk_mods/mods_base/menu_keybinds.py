from collections.abc import Callable
from typing import TypeAlias, cast, overload

from unrealsdk.hooks import Block

from .keybinds import EInputEvent, KeybindBlockSignal
from .native.keybinds import set_menu_keybind_callback

__all__: tuple[str, ...] = (
    "add",
    "pop",
    "push",
)

"""
Menu keybinds, unsurprisingly, fire in menus. They have no mod association, and thus don't appear in
any keybinds menu and cannot be rebound.

Menu keybinds work off of a stack. The top of the stack represents the currently focused menu - only
keybinds added within it are processed. On opening a new menu, with different binds, you should push
a new frame, and register binds within it. On closing a menu, you should pop it's frame.

Menu keybinds may block their inputs from being passed onto the game. This follows the same logic as
blocking execution in hooks, if any keybind returns the block sentinel, the input will be blocked.
"""


MenuKeybindCallback_KeyAndEvent: TypeAlias = Callable[[str, EInputEvent], KeybindBlockSignal]
MenuKeybindCallback_KeyOnly: TypeAlias = Callable[[str], KeybindBlockSignal]
MenuKeybindCallback_EventOnly: TypeAlias = Callable[[EInputEvent], KeybindBlockSignal]
MenuKeybindCallback_NoArgs: TypeAlias = Callable[[], KeybindBlockSignal]

MenuKeybindCallback_Any: TypeAlias = (
    MenuKeybindCallback_KeyAndEvent
    | MenuKeybindCallback_KeyOnly
    | MenuKeybindCallback_EventOnly
    | MenuKeybindCallback_NoArgs
)
MenuKeybindDecorator_Any: TypeAlias = (
    Callable[[MenuKeybindCallback_KeyAndEvent], None]
    | Callable[[MenuKeybindCallback_KeyOnly], None]
    | Callable[[MenuKeybindCallback_EventOnly], None]
    | Callable[[MenuKeybindCallback_NoArgs], None]
)

menu_callback_stack: list[list[MenuKeybindCallback_KeyAndEvent]] = []


def push() -> None:
    """Pushes a new set of menu keybinds."""
    menu_callback_stack.append([])


def pop() -> None:
    """Pops the current set of menu keybinds."""
    menu_callback_stack.pop()


@overload
def add(
    key: str,
    event: EInputEvent,
    callback: MenuKeybindCallback_NoArgs,
) -> None:
    ...


@overload
def add(
    key: str,
    event: None,
    callback: MenuKeybindCallback_EventOnly,
) -> None:
    ...


@overload
def add(
    key: None,
    event: EInputEvent,
    callback: MenuKeybindCallback_KeyOnly,
) -> None:
    ...


@overload
def add(
    key: None,
    event: None,
    callback: MenuKeybindCallback_KeyAndEvent,
) -> None:
    ...


@overload
def add(
    key: str,
    event: EInputEvent = EInputEvent.IE_Pressed,
    callback: None = None,
) -> Callable[[MenuKeybindCallback_NoArgs], None]:
    ...


@overload
def add(
    key: str,
    event: None = None,
    callback: None = None,
) -> Callable[[MenuKeybindCallback_EventOnly], None]:
    ...


@overload
def add(
    key: None,
    event: EInputEvent = EInputEvent.IE_Pressed,
    callback: None = None,
) -> Callable[[MenuKeybindCallback_KeyOnly], None]:
    ...


@overload
def add(
    key: None,
    event: None = None,
    callback: None = None,
) -> Callable[[MenuKeybindCallback_KeyAndEvent], None]:
    ...


def add(
    key: str | None,
    event: EInputEvent | None = EInputEvent.IE_Pressed,
    callback: MenuKeybindCallback_Any | None = None,
) -> MenuKeybindDecorator_Any | None:
    """
    Adds a new menu keybind callback.

    Args:
        key: The key to filter to, or None to be passed all keys.
        event: The event to filter to, or None to be passed all events.
        callback: The callback to run. If None, this function acts as a decorator factory,
    Returns:
        If the callback was not explictly provided, a decorator to register it.
    """

    def decorator(callback: MenuKeybindCallback_Any) -> None:
        nonlocal key, event

        full_callback: MenuKeybindCallback_KeyAndEvent
        match key, event:
            case None, None:
                full_callback = cast(MenuKeybindCallback_KeyAndEvent, callback)

            case None, event:
                cast_callback = cast(MenuKeybindCallback_KeyOnly, callback)

                def event_filter(cb_key: str, cb_event: EInputEvent) -> KeybindBlockSignal:
                    if cb_event != event:
                        return None
                    return cast_callback(cb_key)

                full_callback = event_filter

            case key, None:
                cast_callback = cast(MenuKeybindCallback_EventOnly, callback)

                def key_filter(cb_key: str, cb_event: EInputEvent) -> KeybindBlockSignal:
                    if cb_key != key:
                        return None
                    return cast_callback(cb_event)

                full_callback = key_filter
            case key, event:
                cast_callback = cast(MenuKeybindCallback_NoArgs, callback)

                def key_and_event_filter(cb_key: str, cb_event: EInputEvent) -> KeybindBlockSignal:
                    if cb_key != key or cb_event != event:
                        return None
                    return cast_callback()

                full_callback = key_and_event_filter

        menu_callback_stack[-1].append(full_callback)

    if callback is None:
        return decorator
    return decorator(callback)


@set_menu_keybind_callback
def menu_keybind_callback(key: str, event: EInputEvent) -> KeybindBlockSignal:
    """Menu keybind handler."""

    if len(menu_callback_stack) == 0:
        return None

    should_block = False
    for callback in menu_callback_stack[-1]:
        ret = callback(key, event)

        if ret == Block or isinstance(ret, Block):
            should_block = True

    return Block if should_block else None
