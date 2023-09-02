from __future__ import annotations

import inspect
import sys
from collections.abc import Callable, Iterator, MutableSequence
from dataclasses import dataclass, field
from enum import Enum, Flag, auto
from functools import cache
from pathlib import Path
from typing import Literal

from unrealsdk import logging

from .hook import HookProtocol
from .keybinds import Keybind
from .options import BaseOption, BoolOption, ButtonOption, TitleOption


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

    Attributes - Info:
        name: The mod's name.
        author: The mod's author(s).
        description: A short description of the mod.
        version: A string holding the mod's version. This is purely a display value, the module
                 level attributes should be used for version checking.
        mod_type: What type of mod this is. This influences ordering in the mod list.
        supported_games: The games this mod supports. When loaded in an unsupported game, a warning
                         will be displayed and the mod will be blocked from enabling.

    Attributes - Functionality:
        keybinds: The mod's keybinds. If not given, searches for them in instance variables.
        options: The mod's options. If not given, searches for them in instance variables.
        hooks: The mod's hooks. If not given, searches for them in instance variables.

    Attributes - Runtime:
        is_enabled: True if the mod is currently considered enabled.
        on_enable: A no-arg callback to run on mod enable. Useful when constructing via dataclass.
        on_disable: A no-arg callback to run on mod disable. Useful when constructing via dataclass.
    """

    name: str
    author: str = "Unknown Author"
    description: str = ""
    version: str = "Unknown Version"
    mod_type: ModType = ModType.Standard
    supported_games: Game = Game.BL3 | Game.WL

    # Set the default to None so we can detect when these aren't provided
    # Don't type them as possibly None though, since we're going to fix it immediately in the
    # constructor, and it'd force you to do None checks whenever you're accessing them
    keybinds: MutableSequence[Keybind] = field(default=None)  # type: ignore
    options: MutableSequence[BaseOption] = field(default=None)  # type: ignore
    hooks: MutableSequence[HookProtocol] = field(default=None)  # type: ignore

    is_enabled: bool = field(default=False, init=False)
    on_enable: Callable[[], None] | None = None
    on_disable: Callable[[], None] | None = None

    def __post_init__(self) -> None:
        need_to_search_instance_vars = False

        if find_keybinds := self.keybinds is None:  # type: ignore
            self.keybinds = []
            need_to_search_instance_vars = True

        if find_options := self.options is None:  # type: ignore
            self.options = []
            need_to_search_instance_vars = True

        if find_hooks := self.hooks is None:  # type: ignore
            self.hooks = []
            need_to_search_instance_vars = True

        if not need_to_search_instance_vars:
            return

        for _, value in inspect.getmembers(self):
            match value:
                case Keybind() if find_keybinds:
                    self.keybinds += (value,)
                case BaseOption() if find_options:
                    self.options += (value,)
                case HookProtocol() if find_hooks:
                    self.hooks += (value.bind(self),)
                case _:
                    pass

    def enable(self) -> None:
        """Called to enable the mod."""
        if Game.get_current() not in self.supported_games:
            return

        self.is_enabled = True

        for hook in self.hooks:
            hook.enable()

        if self.on_enable is not None:
            self.on_enable()

    def disable(self) -> None:
        """Called to disable the mod."""
        self.is_enabled = False

        for hook in self.hooks:
            hook.disable()

        if self.on_disable is not None:
            self.on_disable()

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
            yield TitleOption("Options")
            yield from self.options


@dataclass
class Library(Mod):
    """Helper subclass for libraries, which are always enabled."""

    mod_type: Literal[ModType.Library] = ModType.Library

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
            if not seen_enabled and option.name == "Enabled" and isinstance(option, BoolOption):
                seen_enabled = True
                continue
            yield option
