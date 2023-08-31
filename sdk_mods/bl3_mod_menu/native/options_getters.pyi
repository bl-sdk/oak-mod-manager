from typing import TypeAlias

from unrealsdk.unreal import UObject

_GbxGFxListItemComboBox: TypeAlias = UObject
_GbxGFxListItemNumber: TypeAlias = UObject
_GbxGFxListItemSpinner: TypeAlias = UObject

__all__: tuple[str, ...] = (
    "get_combo_box_selected_idx",
    "get_number_value",
    "get_spinner_selected_idx",
)

def get_combo_box_selected_idx(self: _GbxGFxListItemComboBox) -> int:
    """
    Gets the selected index of a GbxGFxListItemComboBox.

    Args:
        self: The combo box item to get the selected index of.
    """

def get_number_value(self: _GbxGFxListItemNumber) -> float:
    """
    Gets the value of a GbxGFxListItemNumber.

    Args:
        self: The number item to get the value of.
    """

def get_spinner_selected_idx(self: _GbxGFxListItemSpinner) -> int:
    """
    Gets the selected index of a GbxGFxListItemSpinner.

    Args:
        self: The spinner item to get the selected index of.
    """
