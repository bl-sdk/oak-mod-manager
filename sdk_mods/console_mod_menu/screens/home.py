from dataclasses import dataclass

from mods_base import get_ordered_mod_list

from console_mod_menu.write import write

from . import AbstractScreen, draw_standard_commands, handle_standard_command_input


@dataclass
class HomeScreen(AbstractScreen):
    def draw(self) -> None:  # noqa: D102
        write("Available Mods:")
        for idx, mod in enumerate(get_ordered_mod_list()):
            write(f"[{idx}] {mod.name}")
        draw_standard_commands()

    def handle_input(self, line: str) -> bool:  # noqa: D102
        if handle_standard_command_input(line):
            return True
        print("INPUT2: ", line)
        return False
