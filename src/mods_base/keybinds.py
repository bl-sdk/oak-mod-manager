from __future__ import annotations

from dataclasses import KW_ONLY, dataclass, field
from typing import TYPE_CHECKING, Any, overload

from unrealsdk import logging

if TYPE_CHECKING:
    from collections.abc import Callable
    from enum import auto

    from unrealsdk.hooks import Block
    from unrealsdk.unreal._uenum import UnrealEnum  # pyright: ignore[reportMissingModuleSource]

    class EInputEvent(UnrealEnum):
        IE_Pressed = auto()
        IE_Released = auto()
        IE_Repeat = auto()
        IE_DoubleClick = auto()
        IE_Axis = auto()
        IE_MAX = auto()

else:
    from unrealsdk import find_enum

    EInputEvent = find_enum("EInputEvent")

type KeybindBlockSignal = None | Block | type[Block]
type KeybindCallback_Event = Callable[[EInputEvent], KeybindBlockSignal]
type KeybindCallback_NoArgs = Callable[[], KeybindBlockSignal]


@dataclass
class KeybindType:
    """
    Represents a single keybind.

    The input callback takes no args, and may return the Block sentinel to prevent passing the input
    back into the game. Standard blocking logic applies when multiple keybinds use the same key.

    Args:
        identifier: The keybind's identifier.
        key: The bound key, or None if unbound. Updated on rebind.
        callback: The callback to run when the key is pressed.

    Keyword Args:
        display_name: The keybind name to use for display. Defaults to copying the identifier.
        description: A short description about the bind.
        description_title: The title of the description. Defaults to copying the display name.
        is_hidden: If true, the keybind will not be shown in the options menu.
        is_rebindable: If the key may be rebound.
        event_filter: If not None, only runs the callback when the given event fires.

    Extra Attributes:
        default_key: What the key was originally when registered. Does not update on rebind.
    """

    identifier: str
    key: str | None

    # If `event_filter` is None, `callback` should be `KeybindCallback_Event | None`
    # If `event_filter` is not None, `callback` should be `KeybindCallback_NoArgs | None`
    # The decorator uses overloads to enforce this
    callback: KeybindCallback_Event | KeybindCallback_NoArgs | None = None

    _: KW_ONLY
    display_name: str = None  # type: ignore
    description: str = ""
    description_title: str = None  # type: ignore
    is_hidden: bool = False
    is_rebindable: bool = True
    event_filter: EInputEvent | None = EInputEvent.IE_Released

    default_key: str | None = field(init=False)

    def __post_init__(self) -> None:
        if self.display_name is None:  # type: ignore
            self.display_name = self.identifier
        if self.description_title is None:  # type: ignore
            self.description_title = self.display_name

        self.default_key = self.key

    # These two functions should get replaced by the keybind implementation
    # The initialization script should make sure to load it before any mods, to make sure they don't
    # end up with references to these functions
    def enable(self) -> None:
        """Enables this keybind."""
        logging.error("No keybind implementation loaded, unable to enable binds")

    def disable(self) -> None:
        """Disables this keybind."""
        logging.error("No keybind implementation loaded, unable to disable binds")


@overload
def keybind(
    identifier: str,
    key: str | None,
    callback: KeybindCallback_NoArgs,
    *,
    display_name: str | None = None,
    description: str = "",
    description_title: str | None = None,
    is_hidden: bool = False,
    is_rebindable: bool = True,
    event_filter: EInputEvent = EInputEvent.IE_Pressed,
) -> KeybindType:
    ...


@overload
def keybind(
    identifier: str,
    key: str | None = None,
    callback: None = None,
    *,
    display_name: str | None = None,
    description: str = "",
    description_title: str | None = None,
    is_hidden: bool = False,
    is_rebindable: bool = True,
    event_filter: EInputEvent = EInputEvent.IE_Pressed,
) -> Callable[[KeybindCallback_NoArgs], KeybindType]:
    ...


@overload
def keybind(
    identifier: str,
    key: str | None,
    callback: KeybindCallback_Event,
    *,
    display_name: str | None = None,
    description: str = "",
    description_title: str | None = None,
    is_hidden: bool = False,
    is_rebindable: bool = True,
    event_filter: None = None,
) -> KeybindType:
    ...


@overload
def keybind(
    identifier: str,
    key: str | None = None,
    callback: None = None,
    *,
    display_name: str | None = None,
    description: str = "",
    description_title: str | None = None,
    is_hidden: bool = False,
    is_rebindable: bool = True,
    event_filter: None = None,
) -> Callable[[KeybindCallback_Event], KeybindType]:
    ...


def keybind(
    identifier: str,
    key: str | None = None,
    callback: KeybindCallback_NoArgs | KeybindCallback_Event | None = None,
    *,
    display_name: str | None = None,
    description: str = "",
    description_title: str | None = None,
    is_hidden: bool = False,
    is_rebindable: bool = True,
    event_filter: EInputEvent | None = EInputEvent.IE_Pressed,
) -> (
    Callable[[KeybindCallback_NoArgs], KeybindType]
    | Callable[[KeybindCallback_Event], KeybindType]
    | KeybindType
):
    """
    Decorator factory to construct a keybind.

    The input callback usually takes no args, and may return the Block sentinel to prevent passing
    the input back into the game. Standard blocking logic applies when multiple keybinds use the
    same key. If the event filter is set to None, such that the callback is fired for all events, it
    is instead passed a single positional arg, the event which occurred.

    Args:
        identifier: The keybind's identifier.
        key: The bound key, or None if unbound.
        callback: The callback to run when the key is pressed.
    Keyword Args:
        display_name: The keybind name to use for display. Defaults to copying the identifier.
        description: A short description about the bind.
        description_title: The title of the description. Defaults to copying the display name.
        is_hidden: If true, the keybind will not be shown in the options menu.
        is_rebindable: If the key may be rebound.
        event_filter: If not None, only runs the callback when the given event fires.
    """

    def decorator(func: KeybindCallback_NoArgs | KeybindCallback_Event) -> KeybindType:
        kwargs: dict[str, Any] = {
            "description": description,
            "is_hidden": is_hidden,
            "is_rebindable": is_rebindable,
            "event_filter": event_filter,
        }
        if display_name is not None:
            kwargs["display_name"] = display_name
        if description_title is not None:
            kwargs["description_title"] = description_title

        return KeybindType(identifier, key, func, **kwargs)

    if callback is None:
        return decorator
    return decorator(callback)
