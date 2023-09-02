import unrealsdk

from . import menu_keybinds
from .keybinds import Keybind
from .mod import Game, Library, Mod, ModType
from .mod_factory import build_mod
from .mod_list import deregister_mod, register_mod
from .options import (
    BaseOption,
    BoolOption,
    ButtonOption,
    DropdownOption,
    HiddenOption,
    SliderOption,
    SpinnerOption,
    TitleOption,
    ValueOption,
)

__version_info__: tuple[int, int] = (1, 0)
__version__: str = f"{__version_info__[0]}.{__version_info__[1]}"

__all__: tuple[str, ...] = (
    "__version__",
    "__version_info__",
    "BaseOption",
    "BoolOption",
    "build_mod",
    "ButtonOption",
    "deregister_mod",
    "DropdownOption",
    "engine",
    "Game",
    "HiddenOption",
    "Keybind",
    "Library",
    "menu_keybinds",
    "Mod",
    "ModType",
    "register_mod",
    "SliderOption",
    "SpinnerOption",
    "TitleOption",
    "ValueOption",
)

engine = unrealsdk.find_object("OakGameEngine", "/Engine/Transient.OakGameEngine_0")
assert engine is not None
