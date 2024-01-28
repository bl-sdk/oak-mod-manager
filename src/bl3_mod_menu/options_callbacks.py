from typing import Any

from mods_base import (
    JSON,
    BaseOption,
    BoolOption,
    ButtonOption,
    DropdownOption,
    KeybindOption,
    NestedOption,
    SliderOption,
    SpinnerOption,
    ValueOption,
    hook,
)
from unrealsdk.hooks import Block, Type
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

from .keybinds import handle_keybind_press
from .native.options_getters import (
    get_combo_box_selected_idx,
    get_number_value,
    get_spinner_selected_idx,
)
from .options_setup import (
    get_displayed_option_at_idx,
    is_options_menu_open,
    open_nested_options_menu,
)


def update_option_value[J: JSON](option: ValueOption[J], value: J) -> None:
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
    """Option interaction hook."""
    if not is_options_menu_open():
        return None

    option: BaseOption
    button = args.PressedButton
    for idx, entry in enumerate(obj.ContentPanel.AllCells):
        if entry.Cell == button:
            option = get_displayed_option_at_idx(idx)
            break
    else:
        raise ValueError("Couldn't find option which was pressed!")

    match option:
        case NestedOption():
            open_nested_options_menu(option)
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
            value = get_number_value(button)
            if option.is_integer:
                value = round(value)
            update_option_value(option, value)
        case SpinnerOption():
            assert button.Class.Name == "GbxGFxListItemComboBox"
            update_option_value(option, option.choices[get_spinner_selected_idx(button)])
        case KeybindOption():
            handle_keybind_press(obj, option)
        case _:
            raise ValueError(f"Pressed option of unknown type {type(option)}")

    return Block
