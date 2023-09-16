from collections.abc import Callable
from typing import TYPE_CHECKING, TypeAlias, cast, overload

from unrealsdk.hooks import Block
from unrealsdk.unreal import UObject

from .native.keybinds import set_keybind_callback

if TYPE_CHECKING:
    from .native.keybinds import _EInputEvent  # pyright: ignore[reportPrivateUsage]

    EInputEvent: TypeAlias = _EInputEvent
else:
    from unrealsdk import find_enum

    EInputEvent = find_enum("EInputEvent")

KeybindBlockSignal: TypeAlias = None | Block | type[Block]

# Must import after defining the keybind types to avoid circular import
# mod_list -> mod -> keybinds -> raw_keybinds
from .mod import Game  # noqa: E402
from .mod_list import mod_list  # noqa: E402

__all__: tuple[str, ...] = (
    "add",
    "pop",
    "push",
)

"""
This module allows for raw access to all key events. It is intended for short term use, to
temporarily add some extra callbacks, primarily to help enhance menus.

Raw keybinds work off of a stack. The top of the stack represents the currently focused menu, only
callbacks within it are processed. On opening a new menu, with different focus, you should push a
new frame, and register callbacks within it. On closing a menu, you should pop it's frame.

Raw keybinds follow the standard blocking logic when multiple callbacks receive the same event. Raw
keybinds are processed *before* gameplay keybinds, so a raw keybind specifying to block the input
will prevent any matching gameplay keybinds from being run.
"""


RawKeybindCallback_KeyAndEvent: TypeAlias = Callable[[str, EInputEvent], KeybindBlockSignal]
RawKeybindCallback_KeyOnly: TypeAlias = Callable[[str], KeybindBlockSignal]
RawKeybindCallback_EventOnly: TypeAlias = Callable[[EInputEvent], KeybindBlockSignal]
RawKeybindCallback_NoArgs: TypeAlias = Callable[[], KeybindBlockSignal]

RawKeybindCallback_Any: TypeAlias = (
    RawKeybindCallback_KeyAndEvent
    | RawKeybindCallback_KeyOnly
    | RawKeybindCallback_EventOnly
    | RawKeybindCallback_NoArgs
)
RawKeybindDecorator_Any: TypeAlias = (
    Callable[[RawKeybindCallback_KeyAndEvent], None]
    | Callable[[RawKeybindCallback_KeyOnly], None]
    | Callable[[RawKeybindCallback_EventOnly], None]
    | Callable[[RawKeybindCallback_NoArgs], None]
)

raw_keybind_callback_stack: list[list[RawKeybindCallback_KeyAndEvent]] = []


def push() -> None:
    """Pushes a new raw keybind frame."""
    raw_keybind_callback_stack.append([])


def pop() -> None:
    """Pops the current raw keybind frame."""
    raw_keybind_callback_stack.pop()


@overload
def add(
    key: str,
    event: EInputEvent,
    callback: RawKeybindCallback_NoArgs,
) -> None:
    ...


@overload
def add(
    key: str,
    event: None,
    callback: RawKeybindCallback_EventOnly,
) -> None:
    ...


@overload
def add(
    key: None,
    event: EInputEvent,
    callback: RawKeybindCallback_KeyOnly,
) -> None:
    ...


@overload
def add(
    key: None,
    event: None,
    callback: RawKeybindCallback_KeyAndEvent,
) -> None:
    ...


@overload
def add(
    key: str,
    event: EInputEvent = EInputEvent.IE_Pressed,
    callback: None = None,
) -> Callable[[RawKeybindCallback_NoArgs], None]:
    ...


@overload
def add(
    key: str,
    event: None = None,
    callback: None = None,
) -> Callable[[RawKeybindCallback_EventOnly], None]:
    ...


@overload
def add(
    key: None,
    event: EInputEvent = EInputEvent.IE_Pressed,
    callback: None = None,
) -> Callable[[RawKeybindCallback_KeyOnly], None]:
    ...


@overload
def add(
    key: None,
    event: None = None,
    callback: None = None,
) -> Callable[[RawKeybindCallback_KeyAndEvent], None]:
    ...


def add(
    key: str | None,
    event: EInputEvent | None = EInputEvent.IE_Pressed,
    callback: RawKeybindCallback_Any | None = None,
) -> RawKeybindDecorator_Any | None:
    """
    Adds a new raw keybind callback in the current frame.

    Args:
        key: The key to filter to, or None to be passed all keys.
        event: The event to filter to, or None to be passed all events.
        callback: The callback to run. If None, this function acts as a decorator factory,
    Returns:
        If the callback was not explictly provided, a decorator to register it.
    """

    def decorator(callback: RawKeybindCallback_Any) -> None:
        nonlocal key, event

        full_callback: RawKeybindCallback_KeyAndEvent
        match key, event:
            case None, None:
                full_callback = cast(RawKeybindCallback_KeyAndEvent, callback)

            case None, event:
                cast_callback = cast(RawKeybindCallback_KeyOnly, callback)

                def event_filter(cb_key: str, cb_event: EInputEvent) -> KeybindBlockSignal:
                    if cb_event != event:
                        return None
                    return cast_callback(cb_key)

                full_callback = event_filter

            case key, None:
                cast_callback = cast(RawKeybindCallback_EventOnly, callback)

                def key_filter(cb_key: str, cb_event: EInputEvent) -> KeybindBlockSignal:
                    if cb_key != key:
                        return None
                    return cast_callback(cb_event)

                full_callback = key_filter
            case key, event:
                cast_callback = cast(RawKeybindCallback_NoArgs, callback)

                def key_and_event_filter(cb_key: str, cb_event: EInputEvent) -> KeybindBlockSignal:
                    if cb_key != key or cb_event != event:
                        return None
                    return cast_callback()

                full_callback = key_and_event_filter

        raw_keybind_callback_stack[-1].append(full_callback)

    if callback is None:
        return decorator
    return decorator(callback)


# ==================================== Callback implementations ====================================


def handle_raw_keybind(pc: UObject, key: str, event: EInputEvent) -> bool:
    """
    Handler which calls raw keybind callbacks.

    Args:
        pc: The OakPlayerController which caused the event.
        key: The key which was pressed.
        event: Which type of input happened.
    Returns:
        True if the key event should be blocked.
    """
    _ = pc

    should_block = False
    if len(raw_keybind_callback_stack) > 0:
        for callback in raw_keybind_callback_stack[-1]:
            ret = callback(key, event)

            if ret == Block or isinstance(ret, Block):
                should_block = True

    return should_block


def handle_gameplay_keybind(pc: UObject, key: str, event: EInputEvent) -> bool:
    """
    Handler which calls gameplay keybind callbacks.

    Args:
        pc: The OakPlayerController which caused the event.
        key: The key which was pressed.
        event: Which type of input happened.
    Returns:
        True if the key event should be blocked.
    """
    # Early exit if in a menu
    if Game.get_current() == Game.WL:
        # pc.IsInMenu() doesn't work in WL, since it uses a different menu system
        # Haven't found the correct replacement, but just checking cursor seems to work well enough,
        # even works on controller when no cursor is actually drawn
        if pc.bShowMouseCursor:
            return False
    else:
        if pc.IsInMenu():
            return False

    should_block = False
    for mod in mod_list:
        if not mod.is_enabled:
            continue

        for bind in mod.keybinds:
            if bind.callback is None:
                continue
            if bind.key != key:
                continue

            ret = bind.callback(event)
            if ret == Block or isinstance(ret, Block):
                should_block = True

    return should_block


@set_keybind_callback
def keybind_handler(pc: UObject, key: str, event: EInputEvent) -> KeybindBlockSignal:
    """General keybind handler."""
    if handle_raw_keybind(pc, key, event):
        return Block
    if handle_gameplay_keybind(pc, key, event):
        return Block

    return None
