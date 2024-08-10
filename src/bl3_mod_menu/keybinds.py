from enum import StrEnum

import unrealsdk
from keybinds import raw_keybinds
from mods_base import BoolOption, DropdownOption, EInputEvent, KeybindOption, get_pc
from unrealsdk.unreal import UObject

from .dialog_box import DialogBox
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
    description=(
        "What type of icon to display in mod options when a keybind is bound to a controller key."
        " Does not affect icons elsewhere in the game."
    ),
)
switch_swap_option = BoolOption(
    "Swap Switch Icons",
    True,
    description="When using switch style controller icons, should A / B and X / Y be swapped.",
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

SWITCH_BUTTON_SWAPS: dict[str, str] = {
    "Gamepad_FaceButton_Left": "Gamepad_FaceButton_Top",
    "Gamepad_FaceButton_Top": "Gamepad_FaceButton_Left",
    "Gamepad_FaceButton_Right": "Gamepad_FaceButton_Bottom",
    "Gamepad_FaceButton_Bottom": "Gamepad_FaceButton_Right",
}


LOCK_ICON = (
    '<img src="img://Game/UI/InteractionPrompt/InteractionPrompt_IDB.InteractionPrompt_IDB"'
    ' width="39" height="39"/>'
)


def add_keybind_option(options_menu: UObject, option: KeybindOption) -> None:
    """
    Adds a keybind option to the options menu.

    Args:
        options_menu: The menu to add to.
        option: The option to add.
    """
    display_key: str = ""
    if option.value is not None:
        display_key = option.value
        pressed_key = option.value

        icon_style = ControllerIconStyle(controller_style_option.value)

        if (
            icon_style == ControllerIconStyle.SWITCH
            and switch_swap_option.value
            and display_key in SWITCH_BUTTON_SWAPS
        ):
            pressed_key = SWITCH_BUTTON_SWAPS[pressed_key]

        if option.value in KEY_GLYPH_MAPPING:
            controller_style_mapping = KEY_GLYPH_MAPPING[pressed_key]

            if icon_style not in controller_style_mapping:
                icon_style = ControllerIconStyle.GENERIC

            if icon_style in controller_style_mapping:
                display_key = controller_style_mapping[icon_style]

    if not option.is_rebindable:
        display_key += LOCK_ICON

    add_binding(
        options_menu,
        option.display_name,
        display_key,
        option.description_title,
        option.description,
    )


# Avoid circular import
from .options_setup import refresh_current_options_menu  # noqa: E402


def handle_keybind_press(options_menu: UObject, option: KeybindOption) -> None:
    """
    Handles a press on a keybind option in the menu.

    Args:
        options_menu: The current menu the bind was pressed in.
        option: The option which was pressed.
    """
    if not option.is_rebindable:
        return

    raw_keybinds.push()

    @raw_keybinds.add(None, EInputEvent.IE_Pressed)
    def key_handler(key: str) -> None:  # pyright: ignore[reportUnusedFunction]
        if key not in ("Escape", "Gamepad_Special_Left"):
            option.value = None if key == option.value else key

        # If you bound to the close key, the dialog will auto close and we'll already be back to the
        # options menu
        menu_stack = get_pc().MenuStack
        if menu_stack.GetTopMenu() != options_menu:
            get_pc().MenuStack.Pop()
        raw_keybinds.pop()

        refresh_current_options_menu(options_menu)

    DialogBox(
        f'Rebind "{option.display_name}"',
        [],
        (
            f'Rebinding "{option.display_name}"\n'
            f"Press new input to bind.\n"
            f"\n"
            f"{{OakPC_PauseGame}}  Cancel"
        ),
        may_cancel=False,
    )
