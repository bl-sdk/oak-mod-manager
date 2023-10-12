from __future__ import annotations

import json
from collections.abc import Mapping, MutableMapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias, TypedDict, cast

from unrealsdk import logging

from .options import (
    BaseOption,
    BoolOption,
    DropdownOption,
    GroupedOption,
    HiddenOption,
    KeybindOption,
    NestedOption,
    SliderOption,
    SpinnerOption,
    ValueOption,
)

if TYPE_CHECKING:
    from .mod import Mod

JSON: TypeAlias = Mapping[str, "JSON"] | Sequence["JSON"] | str | int | float | bool | None

SETTINGS_DIR = Path(__file__).parent.parent / "settings"
SETTINGS_DIR.mkdir(parents=True, exist_ok=True)


class BasicModSettings(TypedDict, total=False):
    enabled: bool
    options: dict[str, JSON]
    keybinds: dict[str, str | None]


def load_options_dict(options: Sequence[BaseOption], settings: MutableMapping[str, JSON]) -> None:
    """
    Recursively loads options from their settings dict.

    Args:
        options: The list of options to load.
        settings: The settings dict.
    """
    for option in options:
        if option.identifier not in settings:
            continue

        value = settings[option.identifier]

        match option:
            case HiddenOption():
                option.value = value

            # For all other option types, try validate the type before setting it, we don't want
            # a "malicious" settings file to corrupt the types at runtime

            case BoolOption():
                # Special case a false string
                if isinstance(value, str) and value.strip().lower() == "false":
                    value = False

                option.value = bool(value)
            case SliderOption():
                try:
                    # Some of the JSON types won't support float conversion suppress the type
                    # error and catch the exception instead
                    option.value = float(value)  # type: ignore
                    if option.is_integer:
                        option.value = round(option.value)
                except ValueError:
                    logging.error(
                        f"'{value}' is not a valid value for option '{option.identifier}', sticking"
                        f" with the default",
                    )
            case DropdownOption() | SpinnerOption():
                value = str(value)
                if value in option.choices:
                    option.value = value
                else:
                    logging.error(
                        f"'{value}' is not a valid value for option '{option.identifier}', sticking"
                        f" with the default",
                    )
            case GroupedOption() | NestedOption():
                if isinstance(value, MutableMapping):
                    load_options_dict(option.children, value)
                else:
                    logging.error(
                        f"'{value}' is not a valid value for option '{option.identifier}', sticking"
                        f" with the default",
                    )
            case KeybindOption():
                logging.dev_warning(
                    f"Found a keybind option '{option.identifier}' in the options list. You should"
                    f" define a standard keybind instead, and only convert it into an option in"
                    f" `iter_display_options` (which is the default behaviour).",
                )

                if value is None:
                    option.value = None
                else:
                    option.value = str(value)

            case _:
                logging.error(
                    f"Couldn't load settings for unknown option type {type(option).__name__}",
                )


def default_load_mod_settings(self: Mod) -> None:
    """Default implementation for Mod.load_settings."""
    if self.settings_file is None:
        return

    settings: BasicModSettings
    try:
        with self.settings_file.open() as file:
            settings = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return

    # No sense doing this if not defined
    if "options" in settings:
        load_options_dict(self.options, settings["options"])

    if "keybinds" in settings:
        saved_keybinds = settings["keybinds"]
        for keybind in self.keybinds:
            if keybind.identifier in saved_keybinds:
                key = saved_keybinds[keybind.identifier]
                if key is None:
                    keybind.key = None
                else:
                    keybind.key = str(key)

    if self.auto_enable and settings.get("enabled", False):
        self.enable()


def create_options_dict(options: Sequence[BaseOption]) -> dict[str, JSON]:
    """
    Creates an options dict from a list of options.

    Args:
        options: The list of options to save.
    Returns:
        The options' values in dict form.
    """
    settings: dict[str, JSON] = {}
    for option in options:
        match option:
            case ValueOption():
                if isinstance(option, KeybindOption):
                    logging.dev_warning(
                        f"Found a keybind option '{option.identifier}' in the options list. You"
                        f" should define a standard keybind instead, and only convert it into an"
                        f" option in `iter_display_options` (which is the default behaviour).",
                    )

                # The generics mean the type of value is technically unknown here
                value = cast(JSON, option.value)  # type: ignore
                settings[option.identifier] = value
            case GroupedOption() | NestedOption():
                settings[option.identifier] = create_options_dict(option.children)
            case _:
                logging.error(
                    f"Couldn't save settings for unknown option type {type(option).__name__}",
                )

    return settings


def default_save_mod_settings(self: Mod) -> None:
    """Default implementation for Mod.save_settings."""
    if self.settings_file is None:
        return

    settings: BasicModSettings = {}

    if len(self.options) > 0:
        option_settings = create_options_dict(self.options)
        if len(option_settings) > 0:
            settings["options"] = option_settings

    if len(self.keybinds) > 0:
        keybind_settings = {}
        for keybind in self.keybinds:
            if not keybind.is_rebindable:
                continue
            keybind_settings[keybind.identifier] = keybind.key

        if len(keybind_settings) > 0:
            settings["keybinds"] = keybind_settings

    if self.auto_enable:
        settings["enabled"] = self.is_enabled

    if len(settings) == 0:
        self.settings_file.unlink(missing_ok=True)
        return

    with self.settings_file.open("w") as file:
        json.dump(settings, file, indent=4)
