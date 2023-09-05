import inspect
from collections.abc import Callable, MutableSequence
from types import ModuleType
from typing import Any, cast

from .hook import HookProtocol
from .keybinds import KeybindType
from .mod import Game, Mod, ModType
from .mod_list import register_mod
from .options import BaseOption


def search_module_if_needed(
    module: ModuleType,
    keybinds: MutableSequence[KeybindType] | None,
    options: MutableSequence[BaseOption] | None,
    hooks: MutableSequence[HookProtocol] | None,
    on_enable: Callable[[], None] | None,
    on_disable: Callable[[], None] | None,
) -> tuple[
    MutableSequence[KeybindType],
    MutableSequence[BaseOption],
    MutableSequence[HookProtocol],
    Callable[[], None] | None,
    Callable[[], None] | None,
]:
    """
    Searches through a module for any mod fields which aren't already specified.

    Args:
        module: The module to search through.
        keybinds: The set of specified keybinds, or None if to search for them.
        options: The set of specified options, or None if to search for them.
        hooks: The set of specified hooks, or None if to search for them.
        on_enable: The specified enable callback, or None if to search for one.
        on_disable: The specified disable callback, or None if to search for one.
    Returns:
        A tuple of all the passed fields, with their final values.
    """
    need_to_search_module = False

    if find_keybinds := keybinds is None:
        keybinds = []
        need_to_search_module = True

    if find_options := options is None:
        options = []
        need_to_search_module = True

    if find_hooks := hooks is None:
        hooks = []
        need_to_search_module = True

    if on_enable is None:
        need_to_search_module = True
    if on_disable is None:
        need_to_search_module = True

    if need_to_search_module:
        for field, value in inspect.getmembers(module):
            match field, value:
                case _, KeybindType() if find_keybinds:
                    keybinds += (value,)

                case _, BaseOption() if find_options:
                    options += (value,)

                case _, HookProtocol() if find_hooks:
                    hooks += (value,)

                case "on_enable", Callable() if on_enable is None:
                    on_enable = cast(Callable[[], None], value)

                case "on_disable", Callable() if on_disable is None:
                    on_disable = cast(Callable[[], None], value)

                case _:
                    pass

    return keybinds, options, hooks, on_enable, on_disable


def build_mod(
    *,
    cls: type[Mod] = Mod,
    name: str | None = None,
    author: str | None = None,
    description: str | None = None,
    version: str | None = None,
    mod_type: ModType | None = None,
    supported_games: Game | None = None,
    keybinds: MutableSequence[KeybindType] | None = None,
    options: MutableSequence[BaseOption] | None = None,
    hooks: MutableSequence[HookProtocol] | None = None,
    on_enable: Callable[[], None] | None = None,
    on_disable: Callable[[], None] | None = None,
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
                  namespace if missing. Note the order is not necesarily stable.
        options: The mod's options. Defaults to searching for OptionBase instances in the module's
                 namespace if missing. Note the order is not necesarily stable.
        hooks: The mod's hooks. Defaults to searching for hook functions in the module's namespace
               if missing.
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

    keybinds, options, hooks, on_enable, on_disable = search_module_if_needed(
        module,
        keybinds,
        options,
        hooks,
        on_enable,
        on_disable,
    )

    kwargs: dict[str, Any] = {
        "name": name or module.__name__,
        "keybinds": keybinds,
        "options": options,
        "hooks": hooks,
    }

    if (author := (author or getattr(module, "__author__", None))) is not None:
        kwargs["author"] = author
    if description is not None:
        kwargs["description"] = description
    if (version := (version or getattr(module, "__version__", None))) is not None:
        kwargs["version"] = version
    if mod_type is not None:
        kwargs["mod_type"] = mod_type
    if supported_games is not None:
        kwargs["supported_games"] = supported_games
    if on_enable is not None:
        kwargs["on_enable"] = on_enable
    if on_disable is not None:
        kwargs["on_disable"] = on_disable

    mod = cls(**kwargs)
    register_mod(mod)
    return mod
