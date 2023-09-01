import inspect
from collections.abc import Sequence
from types import ModuleType
from typing import cast

from .keybinds import Keybind
from .mod import Game, Mod, ModType
from .mod_list import register_mod
from .options import BaseOption


def search_module_if_needed(
    module: ModuleType,
    keybinds: Sequence[Keybind] | None,
    options: Sequence[BaseOption] | None,
) -> tuple[Sequence[Keybind], Sequence[BaseOption]]:
    """
    Searches through a module for any mod fields which aren't already specified.

    Args:
        module: The module to search through.
        keybinds: The set of specified keybinds, or None if to search for them.
        options: The set of specified options, or None if to search for them.
    Returns:
        A tuple of all the passed fields, with their final values.
    """
    needs_to_find_keybinds = keybinds is None
    if needs_to_find_keybinds:
        keybinds = []

    needs_to_find_options = options is None
    if needs_to_find_options:
        options = []

    if needs_to_find_keybinds or needs_to_find_options:
        for field in dir(module):
            match (value := getattr(module, field)):
                case Keybind() if needs_to_find_keybinds:
                    cast(list[Keybind], keybinds).append(value)
                case BaseOption() if needs_to_find_options:
                    cast(list[BaseOption], options).append(value)
                case _:
                    pass

    return keybinds, options


def build_mod(
    *,
    name: str | None = None,
    author: str | None = None,
    description: str = "",
    version: str | None = None,
    mod_type: ModType = ModType.Standard,
    supported_games: Game = Game.BL3 | Game.WL,
    keybinds: Sequence[Keybind] | None = None,
    options: Sequence[BaseOption] | None = None,
) -> Mod:
    """
    Factory function to create and register a mod.

    Unspecified fields are gathered from the contents of the calling module.

    Args:
        name: The mod's name. Defaults to module.__name__ if None.
        author: The mod's author(s). Defaults to module.__author__ if None.
        description: A short description of the mod.
        version: A string holding the mod's version. Defaults to module.__version__ if None.
        mod_type: What type of mod this is.
        supported_games: The games this mod supports.
        keybinds: The mod's keybinds. Defaults to searching for Keybind instances in the module's
                  namespace if None. Note that order may be unstable when doing this.
        options: The mod's options. Defaults to searching for OptionBase instances in the module's
                 namespace if None. Note that order may be unstable when doing this.
    Returns:
        The created mod object.
    """

    module = inspect.getmodule(inspect.stack()[1].frame)
    if module is None:
        raise ValueError("Unable to find calling module when using build_mod factory!")

    keybinds, options = search_module_if_needed(module, keybinds, options)

    mod = Mod(
        name=name or module.__name__,
        author=author or getattr(module, "__author__", "Unknown Author"),
        description=description,
        version=version or getattr(module, "__version__", "Unknown Version"),
        mod_type=mod_type,
        supported_games=supported_games,
        keybinds=keybinds,
        options=options,
    )

    register_mod(mod)
    return mod
