import unrealsdk
from unrealsdk.unreal import UObject

# Define up here to avoid a circular import in mod_list
__version_info__: tuple[int, int] = (1, 0)
__version__: str = f"{__version_info__[0]}.{__version_info__[1]}"

from . import raw_keybinds
from .command import (
    AbstractCommand,
    ArgParseCommand,
    capture_next_console_line,
    command,
    remove_next_console_line_capture,
)
from .hook import hook
from .keybinds import EInputEvent, KeybindType, keybind
from .mod import Game, Library, Mod, ModType
from .mod_factory import build_mod
from .mod_list import deregister_mod, get_ordered_mod_list, html_to_plain_text, register_mod
from .options import (
    JSON,
    BaseOption,
    BoolOption,
    ButtonOption,
    DropdownOption,
    GroupedOption,
    HiddenOption,
    KeybindOption,
    NestedOption,
    SliderOption,
    SpinnerOption,
    ValueOption,
)

__all__: tuple[str, ...] = (
    "__version__",
    "__version_info__",
    "AbstractCommand",
    "ArgParseCommand",
    "BaseOption",
    "BoolOption",
    "build_mod",
    "ButtonOption",
    "capture_next_console_line",
    "command",
    "deregister_mod",
    "DropdownOption",
    "EInputEvent",
    "ENGINE",
    "Game",
    "get_ordered_mod_list",
    "get_pc",
    "GroupedOption",
    "HiddenOption",
    "hook",
    "html_to_plain_text",
    "JSON",
    "keybind",
    "KeybindOption",
    "KeybindType",
    "Library",
    "raw_keybinds",
    "Mod",
    "ModType",
    "NestedOption",
    "register_mod",
    "remove_next_console_line_capture",
    "SliderOption",
    "SpinnerOption",
    "ValueOption",
)

ENGINE = unrealsdk.find_object("OakGameEngine", "/Engine/Transient.OakGameEngine_0")


_GAME_INSTANCE_PROP = ENGINE.Class._find_prop("GameInstance")
_LOCAL_PLAYERS_PROP = _GAME_INSTANCE_PROP.PropertyClass._find_prop("LocalPlayers")
_PLAYER_CONTROLLER_PROP = _LOCAL_PLAYERS_PROP.Inner.PropertyClass._find_prop("PlayerController")


def get_pc() -> UObject:
    """
    Gets the main (local) player controller object.

    Returns:
        The player controller.
    """
    return (
        ENGINE._get_field(_GAME_INSTANCE_PROP)
        ._get_field(_LOCAL_PLAYERS_PROP)[0]
        ._get_field(_PLAYER_CONTROLLER_PROP)
    )
