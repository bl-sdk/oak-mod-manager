from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from console_mod_menu.draw import draw
from console_mod_menu.menu_loop import pop_screen

from . import AbstractScreen


@dataclass
class ConfirmScreen(AbstractScreen):
    unsaved_changes: Literal[False] = field(default=False, init=False)

    msg: str
    # Return values are ignored
    on_confirm: Callable[[], Any]
    on_cancel: Callable[[], Any] = field(default=lambda: None)

    def draw(self) -> None:  # noqa: D102
        draw(self.msg)
        draw("[Y] Yes")
        draw("[N] No")

    def handle_input(self, line: str) -> bool:  # noqa: D102
        # Just make extra sure we can actually pop this screen
        self.unsaved_changes = False
        pop_screen()

        if line[0] in ("Y", "y"):
            self.on_confirm()
        else:
            self.on_cancel()

        return True
