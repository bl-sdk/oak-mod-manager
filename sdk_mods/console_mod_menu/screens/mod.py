from collections.abc import Sequence
from dataclasses import dataclass, field

from mods_base import (
    JSON,
    BaseOption,
    BoolOption,
    ButtonOption,
    DropdownOption,
    GroupedOption,
    KeybindOption,
    Mod,
    NestedOption,
    SliderOption,
    SpinnerOption,
    ValueOption,
)
from unrealsdk import logging

from console_mod_menu.draw import draw
from console_mod_menu.menu_loop import get_stack_header, push_screen
from console_mod_menu.option_formatting import get_option_value_str

from . import AbstractScreen, draw_standard_commands, handle_standard_command_input
from .option import BoolOptionScreen, ButtonOptionScreen, ChoiceOptionScreen, SliderOptionScreen


@dataclass
class ModScreen(AbstractScreen):
    name: str = field(default="", init=False)
    mod: Mod

    drawn_options: list[BaseOption] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self.name = self.mod.name

    def draw_options_list(
        self,
        options: Sequence[BaseOption],
        stack: list[GroupedOption | NestedOption],
    ) -> None:
        """
        Recursively draws a set of options.

        Args:
            options: A list of the options to draw.
            stack: The stack of `GroupedOption` or `NestedOption`s which led to the current list.
        """
        indent = len(stack)

        for option in options:
            if option.is_hidden:
                continue

            if not isinstance(option, GroupedOption | NestedOption):
                self.drawn_options.append(option)

            drawn_idx = len(self.drawn_options)

            match option:
                case GroupedOption() | NestedOption() if option in stack:
                    logging.dev_warning(f"Found recursive options group, not drawing: {option}")
                case GroupedOption() | NestedOption():
                    draw(f"{option.display_name}:", indent=indent)

                    stack.append(option)
                    self.draw_options_list(option.children, stack)
                    stack.pop()

                case ValueOption():
                    j_option: ValueOption[JSON] = option

                    draw(
                        f"[{drawn_idx}] {option.display_name} ({get_option_value_str(j_option)})",
                        indent=indent,
                    )

                case ButtonOption():
                    draw(f"[{drawn_idx}] {option.display_name}", indent=indent)

                case _:
                    logging.dev_warning(f"Encountered unknown option type {type(option)}")

    def draw(self) -> None:  # noqa: D102
        draw(get_stack_header())

        self.drawn_options = []
        self.draw_options_list(tuple(self.mod.iter_display_options()), [])

        draw_standard_commands()

    def handle_input(self, line: str) -> bool:  # noqa: D102
        if handle_standard_command_input(line):
            return True

        option: BaseOption
        try:
            option = self.drawn_options[int(line)]
        except (ValueError, IndexError):
            return False

        match option:
            case BoolOption():
                push_screen(BoolOptionScreen(self, option))
            case ButtonOption():
                push_screen(ButtonOptionScreen(self, option))
            case DropdownOption() | SpinnerOption():
                push_screen(ChoiceOptionScreen(self, option))
            case SliderOption():
                push_screen(SliderOptionScreen(self, option))
            case _:
                logging.dev_warning(f"Encountered unknown option type {type(option)}")
        return False
