from __future__ import annotations

from mods_base import capture_next_console_line

from .write import write

screen_stack: list[AbstractScreen] = []


def push_screen(new_screen: AbstractScreen) -> None:
    """
    Switches to a new screen.

    Args:
        new_screen: The new screen to switch to.
    """
    screen_stack.append(new_screen)


def pop_screen() -> bool:
    """
    Closes the current screen.

    If the screen has unsaved changes, instead switches to a confirm screen (which will close the
    current screen if accepted).

    Returns:
        True it the screen was closed, False if it had unsaved changes.
    """
    if screen_stack[-1].unsaved_changes:
        push_screen(
            ConfirmScreen(
                "You have unsaved changes. Do you want to discard them?",
                on_confirm=screen_stack.pop,
            ),
        )
        return False

    screen_stack.pop()
    return True


def has_multiple_screens_open() -> bool:
    """
    Checks if more than one screen is in the stack.

    Returns:
        True if multiple screens are open.
    """
    return len(screen_stack) > 1


test = 1


def _handle_interactive_input(line: str) -> None:
    """Main input loop."""
    stripped = line.strip()

    if not screen_stack[-1].handle_input(stripped):
        write(f"Unrecognised input '{stripped}'. Please try again.\n")

    if len(screen_stack) > 0:
        screen_stack[-1].draw()
        capture_next_console_line(_handle_interactive_input)


def start_interactive_menu() -> None:
    """Starts the interactive mods menu."""
    screen_stack[:] = [home := HomeScreen()]
    home.draw()

    capture_next_console_line(_handle_interactive_input)


def quit_interactive_menu(restart: bool = False) -> None:
    """
    Tries to quits out of the interactive mods menu.

    May not quit if there are unsaved changes and the user does not discard.

    Args:
        restart: If true, immediately re-opens the menu on the home screen after closing.
    """

    def perform_quit() -> None:
        screen_stack.clear()
        if restart:
            start_interactive_menu()

    if any(screen.unsaved_changes for screen in screen_stack):
        push_screen(
            ConfirmScreen(
                "You have unsaved changes. Do you want to discard them?",
                on_confirm=perform_quit,
            ),
        )
    else:
        perform_quit()


# Avoid circular imports
from .screens import AbstractScreen  # noqa: E402
from .screens.confirm import ConfirmScreen  # noqa: E402
from .screens.home import HomeScreen  # noqa: E402
