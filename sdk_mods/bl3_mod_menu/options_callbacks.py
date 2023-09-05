# ruff: noqa: D103

from typing import Any

from mods_base import (
    BaseOption,
    BoolOption,
    ButtonOption,
    DropdownOption,
    KeybindOption,
    SliderOption,
    SpinnerOption,
    TitleOption,
    ValueOption,
    hook,
)
from mods_base.options import J
from unrealsdk.hooks import Block, Type
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

from .keybinds import handle_keybind_press
from .native.options_getters import (
    get_combo_box_selected_idx,
    get_number_value,
    get_spinner_selected_idx,
)
from .options_setup import is_options_menu_open, last_drawn_options


def update_option_value(option: ValueOption[J], value: J) -> None:
    """
    Updates an option's value, running the callback if needed.

    Args:
        option: The option to update.
        value: The option's new value.
    """
    if option.on_change is not None:
        option.on_change(option, value)
    option.value = value


@hook("/Script/OakGame.GFxOptionBase:OnUnimplementedOptionClicked", Type.PRE, auto_enable=True)
def unimplemented_option_clicked(
    obj: UObject,
    args: WrappedStruct,
    _3: Any,
    _4: BoundFunction,
) -> None | type[Block]:
    if not is_options_menu_open():
        return None

    option: BaseOption
    button = args.PressedButton
    for idx, entry in enumerate(obj.ContentPanel.AllCells):
        if entry.Cell == button:
            option = last_drawn_options[idx]
            break
    else:
        raise ValueError("Couldn't find option which was pressed!")

    match option:
        case ButtonOption():
            if option.on_press is not None:
                option.on_press(option)
        case BoolOption():
            assert button.Class.Name == "GbxGFxListItemSpinner"
            update_option_value(option, get_spinner_selected_idx(button) == 1)
        case DropdownOption():
            assert button.Class.Name == "GbxGFxListItemComboBox"
            update_option_value(option, option.choices[get_combo_box_selected_idx(button)])
        case SliderOption():
            assert button.Class.Name == "GbxGFxListItemNumber"
            update_option_value(option, get_number_value(button))
        case SpinnerOption():
            assert button.Class.Name == "GbxGFxListItemComboBox"
            update_option_value(option, option.choices[get_spinner_selected_idx(button)])
        case TitleOption():
            pass
        case KeybindOption():
            handle_keybind_press(obj, option)
        case _:
            raise ValueError(f"Pressed option of unknown type {type(option)}")

    return Block
