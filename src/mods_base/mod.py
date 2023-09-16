from __future__ import annotations

import inspect
import sys
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, field
from enum import Enum, Flag, auto
from functools import cache
from pathlib import Path
from typing import Literal

from unrealsdk import logging

from .command import AbstractCommand
from .hook import HookProtocol
from .keybinds import KeybindType
from .options import (
    BaseOption,
    BoolOption,
    ButtonOption,
    GroupedOption,
    KeybindOption,
    NestedOption,
)
from .settings import default_load_mod_settings, default_save_mod_settings


class Game(Flag):
    BL3 = auto()
    WL = auto()

    # While we don't expect to run under them, define the willow games too
    # This may prevent an attribute error letting the mod load, and allowing us to display the
    # incompatibility warning
    BL2 = auto()
    TPS = auto()
    AoDK = auto()

    @staticmethod
    @cache
    def get_current() -> Game:
        """Gets the current game."""
        lower_exe_names: dict[str, Game] = {
            "borderlands3.exe": Game.BL3,
            "wonderlands.exe": Game.WL,
        }

        exe = Path(sys.executable).name
        exe_lower = exe.lower()

        if exe_lower not in lower_exe_names:
            # We've occasionally seen the executable corrupt in the old willow sdk
            # Instead of throwing, we'll still try return something sane, to keep stuff working
            # Assuming you're not playing Wonderlands sounds pretty sane :)
            logging.error(f"Unknown executable name '{exe}'! Assuming BL3.")
            return Game.BL3

        return lower_exe_names[exe_lower]


class ModType(Enum):
    Standard = auto()
    Library = auto()


@dataclass
class Mod:
    """
    A mod instance to display in the mods menu.

    The various display strings may contain HTML tags + entities. All mod menus are expected to
    handle them, parsing or striping as appropriate. Other forms of markup are allowed, but may be
    handled incorrectly by some mod menus.

    Attributes - Metadata:
        name: The mod's name.
        author: The mod's author(s).
        description: A short description of the mod.
        version: A string holding the mod's version. This is purely a display value, the module
                 level attributes should be used for version checking.
        mod_type: What type of mod this is. This influences ordering in the mod list.
        supported_games: The games this mod supports. When loaded in an unsupported game, a warning
                         will be displayed and the mod will be blocked from enabling.
        settings_file: The file to save settings to. If None (the default), won't save settings.

    Attributes - Functionality:
        keybinds: The mod's keybinds. If not given, searches for them in instance variables.
        options: The mod's options. If not given, searches for them in instance variables.
        hooks: The mod's hooks. If not given, searches for them in instance variables.
        commands: The mod's commands. If not given, searches for them in instance variables.

    Attributes - Runtime:
        is_enabled: True if the mod is currently considered enabled. Not available in constructor.
        auto_enable: True if to enable the mod on launch if it was also enabled last time.
        on_enable: A no-arg callback to run on mod enable. Useful when constructing via dataclass.
        on_disable: A no-arg callback to run on mod disable. Useful when constructing via dataclass.
    """

    name: str
    author: str = "Unknown Author"
    description: str = ""
    version: str = "Unknown Version"
    mod_type: ModType = ModType.Standard
    supported_games: Game = Game.BL3 | Game.WL
    settings_file: Path | None = None

    # Set the default to None so we can detect when these aren't provided
    # Don't type them as possibly None though, since we're going to fix it immediately in the
    # constructor, and it'd force you to do None checks whenever you're accessing them
    keybinds: Sequence[KeybindType] = field(default=None)  # type: ignore
    options: Sequence[BaseOption] = field(default=None)  # type: ignore
    hooks: Sequence[HookProtocol] = field(default=None)  # type: ignore
    commands: Sequence[AbstractCommand] = field(default=None)  # type: ignore

    is_enabled: bool = field(default=False, init=False)
    auto_enable: bool = True
    on_enable: Callable[[], None] | None = None
    on_disable: Callable[[], None] | None = None

    def __post_init__(self) -> None:
        need_to_search_instance_vars = False

        new_keybinds: list[KeybindType] = []
        if find_keybinds := self.keybinds is None:  # type: ignore
            self.keybinds = new_keybinds
            need_to_search_instance_vars = True

        new_options: list[BaseOption] = []
        if find_options := self.options is None:  # type: ignore
            self.options = new_options
            need_to_search_instance_vars = True

        new_hooks: list[HookProtocol] = []
        if find_hooks := self.hooks is None:  # type: ignore
            self.hooks = new_hooks
            need_to_search_instance_vars = True

        new_commands: list[AbstractCommand] = []
        if find_commands := self.commands is None:  # type: ignore
            self.commands = new_commands
            need_to_search_instance_vars = True

        if not need_to_search_instance_vars:
            return

        for _, value in inspect.getmembers(self):
            match value:
                case KeybindType() if find_keybinds:
                    new_keybinds.append(value)
                case GroupedOption() | NestedOption() if find_options:
                    logging.dev_warning(
                        f"{self.name}: {type(value).__name__} instances must be explicitly"
                        f" specified in the options list!",
                    )
                case BaseOption() if find_options:
                    new_options.append(value)
                case HookProtocol() if find_hooks:
                    new_hooks.append(value.bind(self))
                case AbstractCommand() if find_commands:
                    new_commands.append(value)
                case _:
                    pass

    def enable(self) -> None:
        """Called to enable the mod."""
        if self.is_enabled:
            return
        if Game.get_current() not in self.supported_games:
            return

        self.is_enabled = True

        for hook in self.hooks:
            hook.enable()
        for command in self.commands:
            command.enable()

        if self.on_enable is not None:
            self.on_enable()

        if self.auto_enable:
            self.save_settings()

    def disable(self) -> None:
        """Called to disable the mod."""
        if not self.is_enabled:
            return

        self.is_enabled = False

        for hook in self.hooks:
            hook.disable()
        for command in self.commands:
            command.disable()

        if self.on_disable is not None:
            self.on_disable()

        if self.auto_enable:
            self.save_settings()

    def load_settings(self) -> None:
        """
        Loads data for this mod from it's settings file - including auto enabling if needed.

        This is called during `register_mod`, you generally won't need to call it yourself.
        """
        default_load_mod_settings(self)

    def save_settings(self) -> None:
        """Saves the current state of the mod to it's settings file."""
        default_save_mod_settings(self)

    def iter_display_options(self) -> Iterator[BaseOption]:
        """
        Iterates through the options to display in the options menu.

        This may yield options not in the options list, to customize how the menu is displayed.

        Yields:
            Options, in the order they should be displayed.
        """
        compatible_game = Game.get_current() in self.supported_games

        if not compatible_game:
            yield ButtonOption(
                "Incompatible Game!",
                description=f"This mod is incompatible with {Game.get_current().name}!",
            )

        yield ButtonOption(
            "Description",
            description=self.description,
            description_title=f"By {self.author}  -  {self.version}",
        )
        if compatible_game:
            yield BoolOption(
                "Enabled",
                self.is_enabled,
                on_change=lambda _, now_enabled: self.enable() if now_enabled else self.disable(),
            )

        if len(self.options) > 0:
            yield GroupedOption("Options", self.options)

        if len(self.keybinds) > 0:
            yield GroupedOption(
                "Keybinds",
                [KeybindOption.from_keybind(bind) for bind in self.keybinds],
            )


@dataclass
class Library(Mod):
    """Helper subclass for libraries, which are always enabled."""

    mod_type: Literal[ModType.Library] = ModType.Library
    auto_enable: Literal[False] = False  # Don't auto enable, since we're always enabled

    def __post_init__(self) -> None:
        super().__post_init__()

        if Game.get_current() in self.supported_games:
            self.enable()

    def disable(self) -> None:
        """No-op to prevent the library from being disabled."""

    def iter_display_options(self) -> Iterator[BaseOption]:
        """Custom display options, which remove the enabled switch."""
        seen_enabled = False
        for option in super().iter_display_options():
            if (
                not seen_enabled
                and option.identifier == "Enabled"
                and isinstance(option, BoolOption)
            ):
                seen_enabled = True
                continue
            yield option
