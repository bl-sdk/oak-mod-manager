from typing import TypeAlias

from unrealsdk.unreal import UObject

_GFxOptionBase: TypeAlias = UObject

def add_title(self: _GFxOptionBase, name: str) -> None:
    """
    Adds a title to the options list.

    Args:
        self: The current options menu object to add to.
        name: The name of the title.
    """

def add_slider(
    self: _GFxOptionBase,
    name: str,
    value: float,
    slider_min: float,
    slider_max: float,
    slider_step: float = 1.0,
    slider_is_integer: bool = False,
    description_title: str | None = None,
    description: str = "",
) -> None:
    """
    Adds a slider to the options list.

    Args:
        self: The current options menu object to add to.
        name: The name of the slider.
        value: The current value of the slider.
        slider_min: The minimum value of the slider.
        slider_max: The maximum value of the slider.
        slider_step: How far the slider moves each step.
        slider_is_integer: True if the slider should only use integer values.
        description_title: The title of the slider's description. Defaults to
                           copying the name.
        description: The slider's description.
    """

def add_spinner(
    self: _GFxOptionBase,
    name: str,
    idx: int,
    options: list[str],
    wrap_enabled: bool = False,
    description_title: str | None = None,
    description: str = "",
) -> None:
    """
    Adds a spinner to the options list.

    Args:
        self: The current options menu object to add to.
        name: The name of the spinner.
        idx: The index of the current option to select.
        options: The list of options the spinner switches between.
        wrap_enabled: True if to allow wrapping from the last option back to the
                      first.
        description_title: The title of the spinner's description. Defaults to
                           copying the name.
        description: The spinner's description.
    """

def add_bool_spinner(
    self: _GFxOptionBase,
    name: str,
    value: bool,
    true_text: str | None = None,
    false_text: str | None = None,
    description_title: str | None = None,
    description: str = "",
) -> None:
    """
    Adds a boolean spinner to the options list.

    Args:
        self: The current options menu object to add to.
        name: The name of the spinner.
        value: The current value of the spinner.
        true_text: If set, overwrites the default text for the true option.
        false_text: If set, overwrites the default text for the false option.
        description_title: The title of the spinner's description. Defaults to
                           copying the name.
        description: The spinner's description.
    """

def add_dropdown(
    self: _GFxOptionBase,
    name: str,
    idx: int,
    options: list[str],
    description_title: str | None = None,
    description: str = "",
) -> None:
    """
    Adds a dropdown to the options list.

    Args:
        self: The current options menu object to add to.
        name: The name of the dropdown.
        idx: The index of the current option to select.
        options: The list of options to display.
        description_title: The title of the dropdown's description. Defaults to
                           copying the name.
        description: The dropdown's description.
    """

def add_button(
    self: _GFxOptionBase,
    name: str,
    description_title: str | None = None,
    description: str = "",
) -> None:
    """
    Adds a button to the options list.

    Args:
        self: The current options menu object to add to.
        name: The name of the button.
        description_title: The title of the button's description. Defaults to
                           copying the name.
        description: The button's description.
    """

def add_binding(
    self: _GFxOptionBase,
    name: str,
    display: str,
    description_title: str | None = None,
    description: str = "",
) -> None:
    """
    Adds a binding to the options list.

    Args:
        self: The current options menu object to add to.
        name: The name of the binding.
        display: The binding's display value. This is generally an image.
        description_title: The title of the binding's description. Defaults to
                           copying the name.
        description: The binding's description.
    """
