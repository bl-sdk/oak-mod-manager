from collections.abc import Callable

from unrealsdk.unreal import UObject, WrappedStruct

def show_dialog_box(self: UObject, callback: Callable[[WrappedStruct], None]) -> None:
    """
    Displays a dialog box.

    Uses a callback to configure the dialog. This callback takes a single positional
    arg, a `GbxGFxDialogBoxInfo` struct to edit. It's return value is ignored.

    Args:
        self: The current menu object to open under.
        callback: The setup callback to use.
    """
