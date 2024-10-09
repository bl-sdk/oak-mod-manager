import functools
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import Any

import unrealsdk
from unrealsdk import logging
from unrealsdk.hooks import Type
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

from mods_base import (
    BaseOption,
    BoolOption,
    ButtonOption,
    CoopSupport,
    DropdownOption,
    Game,
    GroupedOption,
    KeybindOption,
    Mod,
    NestedOption,
    SliderOption,
    SpinnerOption,
    get_pc,
    hook,
)

from .keybinds import add_keybind_option
from .native.options_setup import (
    add_bool_spinner,
    add_button,
    add_dropdown,
    add_slider,
    add_spinner,
    add_title,
)
from .native.options_transition import open_custom_options, refresh_options

OPTIONS_MENU_CLS = unrealsdk.find_class("GFxOptionsMenu")


@dataclass
class OptionStackInfo:
    # What caused this level to be drawn
    cause: Mod | NestedOption
    # The list of options which were drawn, used to retrieve option by their index on modify
    drawn_options: list[BaseOption]
    # The menu object this is drawn within, or None if yet to draw
    options_menu: UObject | None = None


option_stack: list[OptionStackInfo] = []


def is_options_menu_open() -> bool:
    """
    Checks if a custom options menu is open.

    Returns:
        True if the options menu is open.
    """
    return len(option_stack) > 0


def get_displayed_option_at_idx(idx: int) -> BaseOption:
    """
    Gets the currently displayed option at the given index.

    Args:
        idx: The index to get.
    Returns:
        THe option which was displayed at that index.
    """
    return option_stack[-1].drawn_options[idx]


def any_option_visible(options: Sequence[BaseOption]) -> bool:
    """
    Recursively checks if any option in a sequence is visible.

    Recurses into grouped options, but not nested ones. A grouped option which is not explicitly
    hidden, but contains no visible children, does not count as visible.

    Args:
        options: The sequence of options to check.
    """
    return any(
        (
            isinstance(option, GroupedOption)
            and not option.is_hidden
            and any_option_visible(option.children)
        )
        or (not option.is_hidden)
        for option in options
    )


def draw_grouped_option(
    self: UObject,
    options: Sequence[BaseOption],
    group_stack: list[GroupedOption],
    option: GroupedOption,
    options_idx: int,
) -> None:
    """
    Draws a grouped option and it's children.

    Args:
        self: The options menu being drawn.
        options: The full options list this group is part of.
        group_stack: The stack of currently open grouped options.
        option: The specific grouped option to add.
        options_idx: The index of the specific grouped option being added.
    """
    if not any_option_visible(option.children):
        return

    group_stack.append(option)

    # If the first entry of the group is another group, don't draw a title, let the nested call do
    # it, so the first title is the most nested
    # If we're empty, or a different type, draw our own header
    if len(option.children) == 0 or not isinstance(option.children[0], GroupedOption):
        add_title(self, " - ".join(g.display_name for g in group_stack))
        option_stack[-1].drawn_options.append(option)

    draw_options(self, option.children, group_stack)

    group_stack.pop()

    # If we didn't just close the outermost group, the group above us still has extra visible
    # options, and the next one of those options is not another group, re-draw the outer group's
    # header
    if (
        group_stack
        and options_idx != len(options) - 1
        and any_option_visible(options[options_idx + 1 :])
        and not isinstance(options[options_idx + 1], GroupedOption)
    ):
        # This will print an empty string if we're on the last stack - which is about
        # the best we can do, we still want a gap
        add_title(self, " - ".join(g.display_name for g in group_stack))
        option_stack[-1].drawn_options.append(option)


def draw_options(  # noqa: C901 - imo the match is rated too highly
    self: UObject,
    options: Sequence[BaseOption],
    group_stack: list[GroupedOption],
) -> None:
    """
    Recursively draws a set of options.

    Args:
        self: The options menu being drawn.
        options: A list of the options to draw.
        group_stack: The stack of `GroupedOption`s which led to this list being drawn.
    """
    option_stack[-1].options_menu = self

    for idx, option in enumerate(options):
        if option.is_hidden:
            continue

        # Grouped options are a little more complex, it handles this manually
        if not isinstance(option, GroupedOption):
            option_stack[-1].drawn_options.append(option)

        match option:
            case ButtonOption() | NestedOption():
                add_button(self, option.display_name, option.description_title, option.description)

            case BoolOption():
                add_bool_spinner(
                    self,
                    option.display_name,
                    option.value,
                    option.true_text,
                    option.false_text,
                    option.description_title,
                    option.description,
                )

            case DropdownOption():
                add_dropdown(
                    self,
                    option.display_name,
                    option.choices.index(option.value),
                    option.choices,
                    option.description_title,
                    option.description,
                )

            case SliderOption():
                add_slider(
                    self,
                    option.display_name,
                    option.value,
                    option.min_value,
                    option.max_value,
                    option.step,
                    option.is_integer,
                    option.description_title,
                    option.description,
                )

            case SpinnerOption():
                add_spinner(
                    self,
                    option.display_name,
                    option.choices.index(option.value),
                    option.choices,
                    option.wrap_enabled,
                    option.description_title,
                    option.description,
                )

            case KeybindOption():
                add_keybind_option(self, option)

            case GroupedOption() if option in group_stack:
                logging.dev_warning(f"Found recursive options group, not drawing: {option}")
            case GroupedOption():
                draw_grouped_option(self, options, group_stack, option, idx)

            case _:
                logging.dev_warning(f"Encountered unknown option type {type(option)}")


def get_option_header() -> str:
    """
    Gets the header to display at the top of the options menu, based on the current option stack.

    Returns:
        The option header
    """
    return " - ".join(
        info.cause.name if isinstance(info.cause, Mod) else info.cause.display_name
        for info in option_stack
    )


def create_description_title(mod: Mod) -> str:
    """
    Creates the description title to use for a mod's description option.

    Args:
        mod: The mod to create the title for.
    Returns:
        The description title.
    """
    description_title = ""
    if mod.author:
        description_title += f"By {mod.author}"
    if mod.author and mod.version:
        description_title += "  -  "
    if mod.version:
        description_title += mod.version
    return description_title or "Description"


def create_description_text(mod: Mod) -> str:
    """
    Creates the text to use for a mod's description option.

    Args:
        mod: The mod to create the title for.
    Returns:
        The description text.
    """
    blocks: list[str] = []

    if Game.get_current() not in mod.supported_games:
        supported = [g.name for g in Game if g in mod.supported_games and g.name is not None]
        blocks.append(
            "<font color='#ffff00'>Incompatible Game!</font>\n"
            "This mod supports: " + ", ".join(supported),
        )

    if mod.description:
        blocks.append(mod.description)

    match mod.coop_support:
        case CoopSupport.Unknown:
            blocks.append("<font color='#e0e0e0'>Coop Support: Unknown</font>")
        case CoopSupport.Incompatible:
            blocks.append(
                "<font color='#e0e0e0'>Coop Support:</font>"
                " <font color='#ffff00'>Incompatible</font>",
            )
        case CoopSupport.RequiresAllPlayers:
            blocks.append(
                "<font color='#e0e0e0'>Coop Support: Requires All Players</font>",
            )
        case CoopSupport.ClientSide:
            blocks.append("<font color='#e0e0e0'>Coop Support: Client Side</font>")

    return "\n\n".join(blocks)


def get_mod_options(mod: Mod) -> tuple[BaseOption, ...]:
    """
    Gets the full list of mod options to display, including our custom header.

    Args:
        mod: The mod to get the options list of.
    Returns:
        A tuple of the options to display.
    """

    def inner() -> Iterator[BaseOption]:
        # Display the author and version in the title, if they're not the empty string

        yield ButtonOption(
            "Description",
            description=create_description_text(mod),
            description_title=create_description_title(mod),
        )

        if not mod.enabling_locked:
            yield BoolOption(
                "Enabled",
                mod.is_enabled,
                on_change=lambda _, now_enabled: mod.enable() if now_enabled else mod.disable(),
            )

        yield from mod.iter_display_options()

    return tuple(inner())


def open_options_menu(main_menu: UObject, mod: Mod) -> None:
    """
    Opens the options menu for a particular mod.

    Args:
        main_menu: The main menu to open under.
        mod: The mod to open the options for.
    """
    option_stack.append(OptionStackInfo(mod, []))
    open_custom_options(
        main_menu,
        get_option_header(),
        functools.partial(draw_options, options=get_mod_options(mod), group_stack=[]),
    )


def refresh_current_options_menu(options_menu: UObject, preserve_scroll: bool = True) -> None:
    """
    Refreshes the currently open options menu.

    Args:
        options_menu: The current options menu.
        preserve_scroll: If true, preserves the current scroll position.
    """
    option_info = option_stack[-1]

    option_info.drawn_options.clear()

    refresh_options(
        options_menu,
        functools.partial(
            draw_options,
            options=(
                get_mod_options(option_info.cause)
                if isinstance(option_info.cause, Mod)
                else option_info.cause.children
            ),
            group_stack=[],
        ),
        preserve_scroll,
    )


# Avoid circular import
from .outer_menu import MAIN_PAUSE_MENU_CLS  # noqa: E402


def open_nested_options_menu(nested: NestedOption) -> None:
    """
    Opens a nested options menu.

    Args:
        options_menu: The current options menu.
        nested: The nested options to draw
    """
    if (
        main_menu := next(
            (
                # Look for the uppermost main menu object in the menu stack
                entry.MenuObject
                for entry in reversed(get_pc().MenuStack.MenuStack)
                if (menu_obj := entry.MenuObject) is not None
                and menu_obj.Class._inherits(MAIN_PAUSE_MENU_CLS)
            ),
            None,
        )
    ) is None:
        raise RuntimeError("Unable to find main menu movie when drawing nested option")

    option_stack.append(OptionStackInfo(nested, []))

    open_custom_options(
        main_menu,
        get_option_header(),
        functools.partial(draw_options, options=nested.children, group_stack=[]),
    )


@hook("/Script/OakGame.GFxFrontendMenu:OnMenuStackChanged", Type.POST, immediately_enable=True)
def frontend_menu_change_hook(
    _1: UObject,
    args: WrappedStruct,
    _3: Any,
    _4: BoundFunction,
) -> None:
    """Hook to detect closing nested menus."""
    active_menu: UObject = args.ActiveMenu

    # If we transferred back to the main menu, regardless of how, save settings and clear the stack
    if active_menu.Class._inherits(MAIN_PAUSE_MENU_CLS):
        # This should always be the mod, but double check
        if len(option_stack) > 0 and isinstance(option_stack[0].cause, Mod):
            option_stack[0].cause.save_settings()

        option_stack.clear()
        return

    # If we changed to the menu one below the current, i.e. we closed the current menu, pop it
    if (
        active_menu.Class._inherits(OPTIONS_MENU_CLS)
        and len(option_stack) > 1
        and option_stack[-2].options_menu == active_menu.CurrentMenu
    ):
        option_stack.pop()
