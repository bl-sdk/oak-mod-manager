import os
from functools import cmp_to_key
from pathlib import Path
from typing import cast

import unrealsdk

import pyunrealsdk

from . import __version__
from .mod import Library, Mod, ModType
from .options import BaseOption, ButtonOption

mod_list: list[Mod] = [
    Library(
        name="unrealsdk",
        author="bl-sdk",
        description="Base library for interacting with unreal objects.",
        version=unrealsdk.__version__,
        search_instance_fields=False,
    ),
    Library(
        name="pyunrealsdk",
        author="bl-sdk",
        description="Python bindings for unrealsdk.",
        version=pyunrealsdk.__version__,
        search_instance_fields=False,
    ),
    Library(
        name="Mods Base",
        author="bl-sdk",
        description="Basic utilities used across all mods.",
        version=__version__,
        options=cast(
            list[BaseOption],
            [
                ButtonOption(
                    "Open Mods Folder",
                    lambda _: os.startfile(Path(__file__).parent.parent),  # type: ignore
                ),
            ],
        ),
        search_instance_fields=False,
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


def deregister_mod(mod: Mod) -> None:
    """
    Removes a mod from the mod list.

    Args:
        mod: The mod to remove.
    """
    if mod.is_enabled:
        mod.disable()

    mod_list.remove(mod)


def get_ordered_mod_list() -> list[Mod]:
    """
    Gets the list of mods, in display order.

    Returns:
        The ordered mod list.
    """

    def cmp(a: Mod, b: Mod) -> int:
        if a.mod_type is not ModType.Library and b.mod_type is ModType.Library:
            return 1
        if a.mod_type is ModType.Library and b.mod_type is not ModType.Library:
            return -1

        if a.name < b.name:
            return -1
        if a.name > b.name:
            return 1
        return 0

    return sorted(mod_list, key=cmp_to_key(cmp))
