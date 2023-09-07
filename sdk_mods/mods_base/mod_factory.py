import inspect
from collections.abc import Callable, Sequence
from types import ModuleType
from typing import Any, cast

from unrealsdk import logging

from .hook import HookProtocol
from .keybinds import KeybindType
from .mod import Game, Mod, ModType
from .mod_list import register_mod
from .options import BaseOption, GroupedOption, NestedOption


def search_module_if_needed(
    module: ModuleType,
    keybinds: Sequence[KeybindType] | None,
    options: Sequence[BaseOption] | None,
    hooks: Sequence[HookProtocol] | None,
    on_enable: Callable[[], None] | None,
    on_disable: Callable[[], None] | None,
) -> tuple[
    Sequence[KeybindType],
    Sequence[BaseOption],
    Sequence[HookProtocol],
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

    new_keybinds: list[KeybindType] = []
    if find_keybinds := keybinds is None:
        keybinds = new_keybinds
        need_to_search_module = True

    new_options: list[BaseOption] = []
    if find_options := options is None:
        options = new_options
        need_to_search_module = True

    new_hooks: list[HookProtocol] = []
    if find_hooks := hooks is None:
        hooks = new_hooks
        need_to_search_module = True

    if on_enable is None:
        need_to_search_module = True
    if on_disable is None:
        need_to_search_module = True

    if need_to_search_module:
        for field, value in inspect.getmembers(module):
            match field, value:
                case _, KeybindType() if find_keybinds:
                    new_keybinds.append(value)

                case _, (GroupedOption() | NestedOption()) if find_options:
                    logging.dev_warning(
                        f"{module.__name__}: {type(value).__name__} instances must be explictly"
                        f" specified in the options list!",
                    )
                case _, BaseOption() if find_options:
                    new_options.append(value)

                case _, HookProtocol() if find_hooks:
                    new_hooks.append(value)

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
    keybinds: Sequence[KeybindType] | None = None,
    options: Sequence[BaseOption] | None = None,
    hooks: Sequence[HookProtocol] | None = None,
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
