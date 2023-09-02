import inspect
from collections.abc import Callable, Sequence
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
    on_enable: Callable[[], None] | None,
    on_disable: Callable[[], None] | None,
) -> tuple[
    Sequence[Keybind],
    Sequence[BaseOption],
    Callable[[], None] | None,
    Callable[[], None] | None,
]:
    """
    Searches through a module for any mod fields which aren't already specified.

    Args:
        module: The module to search through.
        keybinds: The set of specified keybinds, or None if to search for them.
        options: The set of specified options, or None if to search for them.
        on_enable: The specified enable callback, or None if to search for one.
        on_disable: The specified disable callback, or None if to search for one.
    Returns:
        A tuple of all the passed fields, with their final values.
    """
    need_to_search_module = False

    if need_to_find_keybinds := keybinds is None:
        keybinds = []
        need_to_search_module = True

    if need_to_find_options := options is None:
        options = []
        need_to_search_module = True

    if on_enable is None:
        need_to_search_module = True
    if on_disable is None:
        need_to_search_module = True

    if need_to_search_module:
        for field, value in module.__dict__.items():
            match field, value:
                case _, Keybind() if need_to_find_keybinds:
                    cast(list[Keybind], keybinds).append(value)

                case _, BaseOption() if need_to_find_options:
                    cast(list[BaseOption], options).append(value)

                case "on_enable", Callable() if on_enable is None:
                    on_enable = cast(Callable[[], None], value)

                case "on_disable", Callable() if on_disable is None:
                    on_disable = cast(Callable[[], None], value)

                case _:
                    pass

    return keybinds, options, on_enable, on_disable


def build_mod(
    *,
    cls: type[Mod] = Mod,
    name: str | None = None,
    author: str | None = None,
    description: str = "",
    version: str | None = None,
    mod_type: ModType = ModType.Standard,
    supported_games: Game = Game.BL3 | Game.WL,
    keybinds: Sequence[Keybind] | None = None,
    options: Sequence[BaseOption] | None = None,
    on_enable: Callable[[], None] | None = None,
    on_disable: Callable[[], None] | None = None,
) -> Mod:
    """
    Factory function to create and register a mod.

    Unspecified fields are gathered from the contents of the calling module.

    Args:
        cls: The mod class to construct using. Can be used to select a subclass.
        name: The mod's name. Defaults to module.__name__ if None.
        author: The mod's author(s). Defaults to module.__author__ if None.
        description: A short description of the mod.
        version: A string holding the mod's version. Defaults to module.__version__ if None.
        mod_type: What type of mod this is.
        supported_games: The games this mod supports.
        keybinds: The mod's keybinds. Defaults to searching for Keybind instances in the module's
                  namespace if None.
        options: The mod's options. Defaults to searching for OptionBase instances in the module's
                 namespace if None.
        on_enable: A no-arg callback to run on mod enable. Defaults to searching for a callable
                   named `on_enable` in the module's namespace if None.
        on_disable: A no-arg callback to run on mod disable. Defaults to searching for a callable
                    named `on_disable` in the module's namespace if None.
    Returns:
        The created mod object.
    """

    module = inspect.getmodule(inspect.stack()[1].frame)
    if module is None:
        raise ValueError("Unable to find calling module when using build_mod factory!")

    keybinds, options, on_enable, on_disable = search_module_if_needed(
        module,
        keybinds,
        options,
        on_enable,
        on_disable,
    )

    mod = cls(
        name=name or module.__name__,
        author=author or getattr(module, "__author__", "Unknown Author"),
        description=description,
        version=version or getattr(module, "__version__", "Unknown Version"),
        mod_type=mod_type,
        supported_games=supported_games,
        keybinds=keybinds,
        options=options,
        on_enable=on_enable,
        on_disable=on_disable,
    )

    register_mod(mod)
    return mod
