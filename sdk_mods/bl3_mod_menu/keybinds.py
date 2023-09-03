from enum import StrEnum

import unrealsdk
from mods_base import BindingOption, DropdownOption
from unrealsdk.unreal import UObject

from .native.options_setup import add_binding


class ControllerIconStyle(StrEnum):
    GENERIC = "Generic"
    PS4 = "PS4"
    STADIA = "Stadia"
    SWITCH = "Switch"
    XBONE = "Xbox One"


controller_style_option = DropdownOption(
    "Controller Icon Style",
    ControllerIconStyle.GENERIC,
    list(ControllerIconStyle),
    description="When a keybind is bound to a controller key, what type of icon to display.",
)


def _texture_to_img(tex: UObject) -> str:
    path_without_class = "'".join(str(tex).split("'")[1:-1])
    return f'<img src="img:/{path_without_class}"/>'


KEY_GLYPH_MAPPING: dict[str, dict[ControllerIconStyle, str]] = {
    entry.Key.KeyName: (
        {ControllerIconStyle.GENERIC: _texture_to_img(kb_obj)}
        if (kb_obj := entry.KeyboardMouseGlyphBrush.ResourceObject) is not None
        else {
            style: _texture_to_img(obj)
            for style, field in (
                (ControllerIconStyle.GENERIC, "GenericGamepadGlyphBrush"),
                (ControllerIconStyle.PS4, "PS4GlyphBrush"),
                (ControllerIconStyle.STADIA, "StadiaGlyphBrush"),
                (ControllerIconStyle.SWITCH, "SwitchProGlyphBrush"),
                (ControllerIconStyle.XBONE, "XboxOneGlyphBrush"),
            )
            if (obj := getattr(entry, field).ResourceObject) is not None
        }
    )
    for entry in unrealsdk.find_object(
        "GbxInputToGlyphMap",
        "/Game/UI/_Shared/_Design/OakInputToGlyphMap.OakInputToGlyphMap",
    ).InputMap
}


LOCK_ICON = (
    '<img src="img://Game/UI/InteractionPrompt/InteractionPrompt_IDB.InteractionPrompt_IDB"'
    ' width="39" height="39"/>'
)


def add_keybind_option(options_menu: UObject, option: BindingOption) -> None:
    """
    Adds a keybind option to the options menu.

    Args:
        options_menu: The menu to add to.
        option: The option to add.
    """
    display_key: str = ""
    if option.value is not None:
        display_key = option.value

        if option.value in KEY_GLYPH_MAPPING:
            controller_style_mapping = KEY_GLYPH_MAPPING[option.value]

            icon_style = ControllerIconStyle(controller_style_option.value)
            if icon_style not in controller_style_mapping:
                icon_style = ControllerIconStyle.GENERIC

            if icon_style in controller_style_mapping:
                display_key = controller_style_mapping[icon_style]

    if not option.is_rebindable:
        display_key += LOCK_ICON

    add_binding(
        options_menu,
        option.name,
        display_key,
        option.description_title,
        option.description,
    )


def handle_keybind_press(option: BindingOption) -> None:
    """
    Handles a press on a keybind option in the menu.

    Args:
        option: The option which was pressed.
    """
    _ = option  # TODO
