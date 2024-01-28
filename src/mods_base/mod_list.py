import os
from dataclasses import dataclass, field
from functools import cmp_to_key
from html.parser import HTMLParser
from pathlib import Path

import pyunrealsdk
import unrealsdk

from . import MODS_DIR, __version__
from .command import AbstractCommand
from .hook import HookProtocol
from .keybinds import KeybindType
from .mod import Game, Library, Mod, ModType
from .options import BaseOption, ButtonOption
from .settings import SETTINGS_DIR

MOD_DB_URL: str
match Game.get_tree():
    case Game.Willow2:
        MOD_DB_URL = "https://bl-sdk.github.io/"  # pyright: ignore[reportConstantRedefinition]
    case Game.Oak:
        MOD_DB_URL = (  # pyright: ignore[reportConstantRedefinition]
            "https://bl-sdk.github.io/oak-mod-db/"
        )


@dataclass
class BaseMod(Library):
    name: str = "Python SDK"
    author: str = "bl-sdk"
    version: str = ""
    settings_file: Path | None = SETTINGS_DIR / "python-sdk.json"

    keybinds: list[KeybindType] = field(default_factory=list)  # type: ignore
    options: list[BaseOption] = field(default_factory=list)  # type: ignore
    hooks: list[HookProtocol] = field(default_factory=list)  # type: ignore
    commands: list[AbstractCommand] = field(default_factory=list)  # type: ignore

    @dataclass
    class ComponentInfo:
        name: str
        version: str

    # As an internal interface, the other submodules which the sdk ships with by default should add
    # themselves to this list on the `base_mod` object, rather than registering as their own mod.
    # This helps avoid cluttering the default mod list.
    components: list[ComponentInfo] = field(default_factory=list)

    @property
    def description(self) -> str:
        """Custom description getter, which builds it from the list of components."""

        # We want to show components in alphabetical order
        # Rather than use sorted, and throw away the result, might as well just do a proper sort
        # Once already sorted, re-sorting should be relatively quick
        self.components.sort(key=lambda c: c.name.lower())

        description = "Components:\n"
        for comp in self.components:
            description += f"- {comp.name}: {comp.version}\n"

        return description

    @description.setter
    def description(  # pyright: ignore[reportIncompatibleVariableOverride]
        self,
        _: str,
    ) -> None:
        """No-op description setter."""


mod_list: list[Mod] = [
    base_mod := BaseMod(
        options=[
            ButtonOption(
                "Open Mod Database",
                on_press=lambda _: os.startfile(MOD_DB_URL),  # type: ignore  # noqa: S606
            ),
            ButtonOption(
                "Open Installed Mods Folder",
                on_press=lambda _: os.startfile(MODS_DIR),  # type: ignore  # noqa: S606
            ),
        ],
        components=[
            BaseMod.ComponentInfo("Base", __version__),
            # Both of these start their version strings with their module name, strip it out
            BaseMod.ComponentInfo("unrealsdk", unrealsdk.__version__.partition(" ")[2]),
            BaseMod.ComponentInfo("pyunrealsdk", pyunrealsdk.__version__.partition(" ")[2]),
        ],
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
        mod.disable(dont_update_setting=True)

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
