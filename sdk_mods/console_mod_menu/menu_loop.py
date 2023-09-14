from __future__ import annotations

from mods_base import capture_next_console_line

from .draw import draw

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
                "Discard Changes?",
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


def get_stack_header() -> str:
    """
    Gets a header combining all the items in the stack.

    Returns:
        The stack header
    """
    return " / ".join(x.name for x in screen_stack)


_should_restart_interactive_menu: bool = False


def _handle_interactive_input(line: str) -> None:
    """Main input loop."""
    global _should_restart_interactive_menu
    stripped = line.strip()

    parsed_input = screen_stack[-1].handle_input(stripped)

    if len(screen_stack) > 0:
        screen_stack[-1].draw()
        capture_next_console_line(_handle_interactive_input)

    if not parsed_input:
        draw(f"\nUnrecognised input '{stripped}'.")

    if _should_restart_interactive_menu:
        start_interactive_menu()
    _should_restart_interactive_menu = False


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
        global _should_restart_interactive_menu
        screen_stack.clear()
        if restart:
            _should_restart_interactive_menu = True

    if any(screen.unsaved_changes for screen in screen_stack):
        push_screen(
            ConfirmScreen(
                "Discard Changes?",
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
