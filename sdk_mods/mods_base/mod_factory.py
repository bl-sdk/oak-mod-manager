import inspect
from collections.abc import Callable, Sequence
from dataclasses import MISSING
from types import ModuleType
from typing import Literal, cast

from .keybinds import Keybind
from .mod import Game, Mod, ModType
from .mod_list import register_mod
from .options import BaseOption


def search_module_if_needed(
    module: ModuleType,
    keybinds: Sequence[Keybind] | Literal[MISSING],
    options: Sequence[BaseOption] | Literal[MISSING],
    on_enable: Callable[[], None] | Literal[MISSING],
    on_disable: Callable[[], None] | Literal[MISSING],
) -> tuple[
    Sequence[Keybind],
    Sequence[BaseOption],
    Callable[[], None] | Literal[MISSING],
    Callable[[], None] | Literal[MISSING],
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

    if need_to_find_keybinds := keybinds is MISSING:
        keybinds = []
        need_to_search_module = True

    if need_to_find_options := options is MISSING:
        options = []
        need_to_search_module = True

    if on_enable is MISSING:
        need_to_search_module = True
    if on_disable is MISSING:
        need_to_search_module = True

    if need_to_search_module:
        for field, value in module.__dict__.items():
            match field, value:
                case _, Keybind() if need_to_find_keybinds:
                    cast(list[Keybind], keybinds).append(value)

                case _, BaseOption() if need_to_find_options:
                    cast(list[BaseOption], options).append(value)

                case "on_enable", Callable() if on_enable is MISSING:
                    on_enable = cast(Callable[[], None], value)

                case "on_disable", Callable() if on_disable is MISSING:
                    on_disable = cast(Callable[[], None], value)

                case _:
                    pass

    return keybinds, options, on_enable, on_disable


def build_mod(
    *,
    cls: type[Mod] = Mod,
    # Reuse the dataclass missing sentinel, so that we can forward it directly to the constructor
    # for any args we don't do anything special to, and it can handle it all
    name: str | Literal[MISSING] = MISSING,
    author: str | Literal[MISSING] = MISSING,
    description: str | Literal[MISSING] = MISSING,
    version: str | Literal[MISSING] = MISSING,
    mod_type: ModType | Literal[MISSING] = MISSING,
    supported_games: Game | Literal[MISSING] = MISSING,
    keybinds: Sequence[Keybind] | Literal[MISSING] = MISSING,
    options: Sequence[BaseOption] | Literal[MISSING] = MISSING,
    on_enable: Callable[[], None] | Literal[MISSING] = MISSING,
    on_disable: Callable[[], None] | Literal[MISSING] = MISSING,
) -> Mod:
    """
    Factory function to create and register a mod.

    Unspecified fields are gathered from the contents of the calling module.

    Args:
        cls: The mod class to construct using. Can be used to select a subclass.
        name: The mod's name. Defaults to module.__name__ if missing.
        author: The mod's author(s). Defaults to module.__author__ if missing.
        description: A short description of the mod.
        version: A string holding the mod's version. Defaults to module.__version__ if missing.
        mod_type: What type of mod this is.
        supported_games: The games this mod supports.
        keybinds: The mod's keybinds. Defaults to searching for Keybind instances in the module's
                  namespace if missing.
        options: The mod's options. Defaults to searching for OptionBase instances in the module's
                 namespace if missing.
        on_enable: A no-arg callback to run on mod enable. Defaults to searching for a callable
                   named `on_enable` in the module's namespace if missing.
        on_disable: A no-arg callback to run on mod disable. Defaults to searching for a callable
                    named `on_disable` in the module's namespace if missing.
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
        name=module.__name__ if name is MISSING else name,
        author=getattr(module, "__author__", "Unknown Author") if author is MISSING else author,
        description=description,  # type: ignore
        version=(
            getattr(module, "__version__", "Unknown Version") if version is MISSING else version
        ),
        mod_type=mod_type,  # type: ignore
        supported_games=supported_games,  # type: ignore
        keybinds=keybinds,
        options=options,
        on_enable=on_enable,  # type: ignore
        on_disable=on_disable,  # type: ignore
    )

    register_mod(mod)
    return mod
