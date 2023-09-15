from dataclasses import dataclass, field
from typing import Literal

from mods_base import Mod, get_ordered_mod_list

from console_mod_menu.draw import draw

from . import (
    AbstractScreen,
    draw_stack_header,
    draw_standard_commands,
    handle_standard_command_input,
    push_screen,
)
from .mod import ModScreen


@dataclass
class HomeScreen(AbstractScreen):
    name: Literal["Mods"] = "Mods"

    drawn_mod_list: list[Mod] = field(default_factory=list, init=False)

    def draw(self) -> None:  # noqa: D102
        draw_stack_header()

        self.drawn_mod_list = get_ordered_mod_list()
        for idx, mod in enumerate(self.drawn_mod_list):
            draw(f"[{idx + 1}] {mod.name}")

        draw_standard_commands()

    def handle_input(self, line: str) -> bool:  # noqa: D102
        if handle_standard_command_input(line):
            return True

        mod: Mod
        try:
            mod = self.drawn_mod_list[int(line) - 1]
        except (ValueError, IndexError):
            return False

        push_screen(ModScreen(mod))
        return True
