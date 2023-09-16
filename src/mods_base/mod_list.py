import os
from functools import cmp_to_key
from html.parser import HTMLParser
from pathlib import Path
from typing import cast

import pyunrealsdk
import unrealsdk

from . import __version__
from .mod import Library, Mod, ModType
from .options import BaseOption, ButtonOption

mod_list: list[Mod] = [
    Library(
        name="unrealsdk",
        author="bl-sdk",
        description="Base library for interacting with unreal objects.",
        version=unrealsdk.__version__,
        keybinds=[],
        options=[],
        hooks=[],
        commands=[],
    ),
    Library(
        name="pyunrealsdk",
        author="bl-sdk",
        description="Python bindings for unrealsdk.",
        version=pyunrealsdk.__version__,
        keybinds=[],
        options=[],
        hooks=[],
        commands=[],
    ),
    base_mod := Library(
        name="Python SDK Base",
        author="bl-sdk",
        description="Basic utilities used across all mods.",
        version=__version__,
        keybinds=[],
        options=cast(
            list[BaseOption],
            [
                ButtonOption(
                    "Open Mods Folder",
                    on_press=lambda _: os.startfile(Path(__file__).parent.parent),  # type: ignore
                ),
            ],
        ),
        hooks=[],
        commands=[],
    ),
]


def register_mod(mod: Mod) -> None:
    """
    Registers a mod instance.

    Args:
        mod: The mod to register.
    Returns:
        The mod which was registered.
    """
    mod_list.append(mod)
    mod.load_settings()


def deregister_mod(mod: Mod) -> None:
    """
    Removes a mod from the mod list.

    Args:
        mod: The mod to remove.
    """
    if mod.is_enabled:
        mod.disable()

    mod_list.remove(mod)


def html_to_plain_text(html: str) -> str:
    """
    Extracts plain text from HTML-containing text. This is *NOT* input sanitisation.

    Removes tags, and decodes entities - `<b>&amp;</b>` becomes `&`.

    Intended for use when accessing a mod name/description/option/etc., which may contain HTML tags,
    but in a situation where such tags would be inappropriate.

    Args:
        html: The HTML-containing text.
    Returns:
        The extracted plain text.
    """
    extracted_data: list[str] = []

    parser = HTMLParser()
    parser.handle_data = lambda data: extracted_data.append(data)
    parser.feed(html)

    return "".join(extracted_data)


def get_ordered_mod_list() -> list[Mod]:
    """
    Gets the list of mods, in display order.

    Returns:
        The ordered mod list.
    """

    def cmp(a: Mod, b: Mod) -> int:
        # The base mod should always appear at the start
        if a == base_mod and b != base_mod:
            return -1
        if a != base_mod and b == base_mod:
            return 1

        # Sort libraries after all other mod types
        if a.mod_type is not ModType.Library and b.mod_type is ModType.Library:
            return -1
        if a.mod_type is ModType.Library and b.mod_type is not ModType.Library:
            return 1

        # Finally, sort by name
        # Strip html tags, whitespace, and compare case insensitively
        a_plain = html_to_plain_text(a.name.strip()).lower()
        b_plain = html_to_plain_text(b.name.strip()).lower()
        if a_plain < b_plain:
            return -1
        if a_plain > b_plain:
            return 1
        return 0

    return sorted(mod_list, key=cmp_to_key(cmp))
