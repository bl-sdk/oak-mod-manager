import unrealsdk
from unrealsdk.unreal import UObject

from . import menu_keybinds
from .keybinds import Keybind
from .mod import Mod, deregister_mod, register_mod

__all__: tuple[str, ...] = (
    "deregister_mod",
    "engine",
    "Keybind",
    "menu_keybinds",
    "Mod",
    "register_mod",
)

engine: UObject = unrealsdk.find_object("OakGameEngine", "/Engine/Transient.OakGameEngine_0")
assert engine is not None

from . import menu  # noqa: E402, F401  # pyright: ignore[reportUnusedImport]
