from __future__ import annotations

import inspect
import sys
from collections.abc import Callable, Iterator, MutableSequence
from dataclasses import InitVar, dataclass, field
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
        keybinds: A sequence of the mod's keybinds.
        options: A sequence of the mod's options.
        hooks: A sequence of the mod's hooks.

    Attributes - Runtime:
        is_enabled: True if the mod is currently considered enabled.
        on_enable: A no-arg callback to run on mod enable. Useful when constructing via dataclass.
        on_disable: A no-arg callback to run on mod disable. Useful when constructing via dataclass.

    Init Vars:
        search_instance_fields: If True, will append to the keybind, option, and hook lists with
                                values found by searching through instance variables duing
                                initalization. Note the order is not necesarily stable.
    """

    name: str
    author: str = "Unknown Author"
    description: str = ""
    version: str = "Unknown Version"
    mod_type: ModType = ModType.Standard
    supported_games: Game = Game.BL3 | Game.WL

    keybinds: MutableSequence[Keybind] = field(default_factory=list)
    options: MutableSequence[BaseOption] = field(default_factory=list)
    hooks: MutableSequence[HookProtocol] = field(default_factory=list)

    is_enabled: bool = field(default=False, init=False)
    on_enable: Callable[[], None] | None = None
    on_disable: Callable[[], None] | None = None

    search_instance_fields: InitVar[bool] = True

    def __post_init__(self, search_instance_fields: bool) -> None:
        if not search_instance_fields:
            return

        for _, value in inspect.getmembers(self):
            match value:
                case Keybind() if value not in self.keybinds:
                    self.keybinds += (value,)
                case BaseOption() if value not in self.options:
                    self.options += (value,)
                case HookProtocol() if value not in self.hooks:
                    self.hooks += (value.bind(self),)
                case _:
                    pass

    def enable(self) -> None:
        """Called to enable the mod."""
        self.is_enabled = True

        for hook in self.hooks:
            hook.enable()

        if self.on_enable is not None:
            self.on_enable()

    def disable(self) -> None:
        """Called to disable the mod."""
        self.is_enabled = False

        if self.on_disable is not None:
            self.on_disable()

    def iter_display_options(self) -> Iterator[BaseOption]:
        """
        Iterates through the options to display in the options menu.

        This may yield options not in the options list, to customize how the menu is displayed.
        """
        yield ButtonOption(
            "Description",
            description=f"By {self.author}.\n{self.version}\n\n" + self.description,
        )
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

    def __post_init__(self, search_instance_fields: bool) -> None:
        super().__post_init__(search_instance_fields)

        if Game.get_current() in self.supported_games:
            self.enable()

    def disable(self) -> None:
        """No-op to prevent the library from being disabled."""
