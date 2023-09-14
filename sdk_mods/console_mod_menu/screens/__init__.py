from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from console_mod_menu.menu_loop import has_multiple_screens_open, pop_screen, quit_interactive_menu
from console_mod_menu.write import write


@dataclass
class AbstractScreen(ABC):
    unsaved_changes: bool = field(default=False, init=False)

    @abstractmethod
    def draw(self) -> None:
        """Draws this screen."""
        raise NotImplementedError

    @abstractmethod
    def handle_input(self, line: str) -> bool:
        """
        Handles a user input.

        Args:
            line: The line the user submitted, with whitespace stripped.
        Returns:
            True if able to parse the line, false otherwise.
        """
        raise NotImplementedError


def draw_standard_commands() -> None:
    """Draws the standard commands which apply across all screens."""
    write("[Q] Quit")

    if has_multiple_screens_open():
        write("[B] Back")

    write("[?] Re-draw this screen")


def handle_standard_command_input(line: str) -> bool:
    """
    Checks if a user input matched a standard command, and processes it.

    Args:
        line: The line the user submitted, with whitespace stripped.
    Returns:
        True if able to parse the line, false otherwise.
    """
    match lower_line := line.lower():
        case "q" | "quit" | "exit" | "mods":
            quit_interactive_menu(restart=lower_line == "mods")
            return True

        case ("b" | "back") if has_multiple_screens_open():
            pop_screen()
            return True

        case "?" | "help":
            return True

        case _:
            return False
