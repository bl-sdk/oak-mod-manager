import inspect
from collections.abc import Callable, Sequence
from pathlib import Path
from types import ModuleType
from typing import Any, cast

from unrealsdk import logging

from .command import AbstractCommand
from .hook import HookProtocol
from .keybinds import KeybindType
from .mod import Game, Mod, ModType
from .mod_list import deregister_mod, mod_list, register_mod
from .options import BaseOption, GroupedOption, NestedOption
from .settings import SETTINGS_DIR


def search_module_if_needed(
    module: ModuleType,
    keybinds: Sequence[KeybindType] | None,
    options: Sequence[BaseOption] | None,
    hooks: Sequence[HookProtocol] | None,
    commands: Sequence[AbstractCommand] | None,
    on_enable: Callable[[], None] | None,
    on_disable: Callable[[], None] | None,
) -> tuple[
    Sequence[KeybindType],
    Sequence[BaseOption],
    Sequence[HookProtocol],
    Sequence[AbstractCommand],
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
        commands: The set of specified commands, or None if to search for them.
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

    new_commands: list[AbstractCommand] = []
    if find_commands := commands is None:
        commands = new_commands
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
                        f"{module.__name__}: {type(value).__name__} instances must be explicitly"
                        f" specified in the options list!",
                    )
                case _, BaseOption() if find_options:
                    new_options.append(value)

                case _, HookProtocol() if find_hooks:
                    new_hooks.append(value)

                case _, AbstractCommand() if find_commands:
                    new_commands.append(value)

                case "on_enable", Callable() if on_enable is None:
                    on_enable = cast(Callable[[], None], value)

                case "on_disable", Callable() if on_disable is None:
                    on_disable = cast(Callable[[], None], value)

                case _:
                    pass

    return keybinds, options, hooks, commands, on_enable, on_disable


def deregister_using_settings_file(settings_file: Path) -> None:
    """
    Deregisters all mods using the given settings file.

    Args:
        settings_file: The settings file path to deregister mods using.
    """
    mods_to_remove = [mod for mod in mod_list if mod.settings_file == settings_file]
    for mod in mods_to_remove:
        deregister_mod(mod)


def build_mod(
    *,
    cls: type[Mod] = Mod,
    name: str | None = None,
    author: str | None = None,
    description: str | None = None,
    version: str | None = None,
    mod_type: ModType | None = None,
    supported_games: Game | None = None,
    settings_file: Path | None = None,
    keybinds: Sequence[KeybindType] | None = None,
    options: Sequence[BaseOption] | None = None,
    hooks: Sequence[HookProtocol] | None = None,
    commands: Sequence[AbstractCommand] | None = None,
    auto_enable: bool | None = None,
    on_enable: Callable[[], None] | None = None,
    on_disable: Callable[[], None] | None = None,
    deregister_same_settings: bool = True,
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
        settings_file: The file to save settings to. Defaults to `<module.__name__>.json` in the
                       settings dir.
        keybinds: The mod's keybinds. Defaults to searching for Keybind instances in the module's
                  namespace if missing. Note the order is not necessarily stable.
        options: The mod's options. Defaults to searching for OptionBase instances in the module's
                 namespace if missing. Note the order is not necessarily stable.
        hooks: The mod's hooks. Defaults to searching for hook functions in the module's namespace
               if missing.
        commands: The mod's commands. Defaults to searching for AbstractCommand instances in the
                  module's namespace if missing.
        auto_enable: True if to enable the mod on launch if it was also enabled last time.
        on_enable: A no-arg callback to run on mod enable. Defaults to searching for a callable
                   named `on_enable` in the module's namespace if missing.
        on_disable: A no-arg callback to run on mod disable. Defaults to searching for a callable
                    named `on_disable` in the module's namespace if missing.
        deregister_same_settings: If true, deregisters any existing mods that use the same settings
                                  file. Useful so that reloading the module does not create multiple
                                  entries in the mods menu.
    Returns:
        The created mod object.
    """

    module = inspect.getmodule(inspect.stack()[1].frame)
    if module is None:
        raise ValueError("Unable to find calling module when using build_mod factory!")

    keybinds, options, hooks, commands, on_enable, on_disable = search_module_if_needed(
        module,
        keybinds,
        options,
        hooks,
        commands,
        on_enable,
        on_disable,
    )

    kwargs: dict[str, Any] = {
        "name": name or module.__name__,
        "keybinds": keybinds,
        "options": options,
        "hooks": hooks,
        "commands": commands,
    }

    if (author := (author or getattr(module, "__author__", None))) is not None:
        kwargs["author"] = author
    if (version := (version or getattr(module, "__version__", None))) is not None:
        kwargs["version"] = version

    if settings_file is None:
        settings_file = SETTINGS_DIR / (module.__name__ + ".json")
    kwargs["settings_file"] = settings_file
    if deregister_same_settings:
        deregister_using_settings_file(settings_file)

    for arg, arg_name in (
        (description, "description"),
        (mod_type, "mod_type"),
        (supported_games, "supported_games"),
        (auto_enable, "auto_enable"),
        (on_enable, "on_enable"),
        (on_disable, "on_disable"),
    ):
        if arg is not None:
            kwargs[arg_name] = arg

    mod = cls(**kwargs)
    register_mod(mod)
    return mod
