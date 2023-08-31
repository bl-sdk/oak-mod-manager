import unrealsdk

from . import menu_keybinds
from .keybinds import Keybind
from .mod import Game, Mod, ModType
from .mod_list import deregister_mod, register_mod

__version_info__: tuple[int, int] = (1, 0)
__version__: str = f"{__version_info__[0]}.{__version_info__[1]}"

__all__: tuple[str, ...] = (
    "__version__",
    "__version_info__",
    "deregister_mod",
    "engine",
    "Game",
    "Keybind",
    "menu_keybinds",
    "Mod",
    "ModType",
    "register_mod",
)

engine = unrealsdk.find_object("OakGameEngine", "/Engine/Transient.OakGameEngine_0")
assert engine is not None
