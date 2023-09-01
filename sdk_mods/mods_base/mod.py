from __future__ import annotations

import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum, Flag, auto
from functools import cache
from pathlib import Path

from unrealsdk import logging

from .keybinds import Keybind
from .options import BaseOption


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

    Attributes - Runtime:
        is_enabled: True if the mod is currently considered enabled.
    """

    name: str
    author: str
    description: str
    version: str
    mod_type: ModType
    supported_games: Game

    keybinds: Sequence[Keybind] = field(default_factory=list)
    options: Sequence[BaseOption] = field(default_factory=list)

    is_enabled: bool = field(init=False, default=False)

    def __repr__(self) -> str:
        return f"<{self.name}: " + ("Enabled" if self.is_enabled else "Disabled") + ">"

    def enable(self) -> None:
        """Called to enable the mod."""
        self.is_enabled = True

    def disable(self) -> None:
        """Called to disable the mod."""
        self.is_enabled = False
