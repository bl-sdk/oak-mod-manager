from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from dataclasses import KW_ONLY, dataclass, field
from typing import Generic, Literal, Self, TypeVar

from .settings import JSON

_T = TypeVar("_T", bound=JSON)


@dataclass
class BaseOption(ABC):
    """
    Abstract base class for all options.

    Args:
        name: The option's name.
    Keyword Args:
        description: A short description about the option.
        description_title: The title to use for the description. If None, copies the name.
        is_hidden: If true, the option will not be shown in the options menu.
    """

    name: str
    _: KW_ONLY
    description: str = ""
    description_title: str | None = None
    is_hidden: bool = False

    @abstractmethod
    def __init__(self) -> None:
        raise NotImplementedError


@dataclass
class ValueOption(BaseOption, Generic[_T]):
    """
    Abstract base class for all options storing a value.

    Args:
        name: The option's name.
        value: The option's value.
    Keyword Args:
        description: A short description about the option.
        description_title: The title to use for the description. If None, copies the name.
        is_hidden: If true, the option will not be shown in the options menu.
        on_change: If not None, a callback to run before updating the value. Passed a reference to
                   the option object and the new value.
    Extra Attributes:
        default_value: What the value was originally when registered. Does not update on change.
    """

    value: _T
    default_value: _T = field(init=False)
    _: KW_ONLY
    on_change: Callable[[Self, _T], None] | None = None

    @abstractmethod
    def __init__(self) -> None:
        raise NotImplementedError

    def __post_init__(self) -> None:
        self.default_value = self.value


@dataclass
class HiddenOption(ValueOption[_T]):
    """
    A generic option which is always hidden. Use this to persist arbitrary (JSON-encodeable) data.

    Args:
        name: The option's name.
    Keyword Args:
        description: A short description about the option.
        description_title: The title to use for the description. If None, copies the name.
    Extra Attributes:
        is_hidden: Always true.
    """

    is_hidden: Literal[True] = field(default=True, init=False)


@dataclass
class TitleOption(BaseOption):
    """
    An entry in the options menu which simply acts as a title for a group of following options.

    Args:
        name: The option's name.
    Keyword Args:
        description: A short description about the option.
        description_title: The title to use for the description. If None, copies the name.
        is_hidden: If true, the option will not be shown in the options menu.
    """


@dataclass
class SliderOption(ValueOption[float]):
    """
    An option selecting a number within a range. Typically implemented as a slider.

    Args:
        name: The option's name.
        value: The option's value.
        min_value: The minimum value.
        max_value: The maximum value.
        step: How much the value should move each step of the slider.
        is_integer: If True, the value is treated as an integer.
    Keyword Args:
        description: A short description about the option.
        description_title: The title to use for the description. If None, copies the name.
        is_hidden: If true, the option will not be shown in the options menu.
        on_change: If not None, a callback to run before updating the value. Passed a reference to
                   the option object and the new value.
    Extra Attributes:
        default_value: What the value was originally when registered. Does not update on change.
    """

    min_value: float
    max_value: float
    step: float = 1
    is_integer: bool = True


@dataclass
class SpinnerOption(ValueOption[str]):
    """
    An option selecting one of a set of strings. Typically implemented as a spinner.

    Also see DropDownOption, which may be more suitable for larger numbers of choices.

    Args:
        name: The option's name.
        value: The option's value.
        choices: A list of choices for the value.
        wrap_enabled: If True, allows moving from the last choice back to the first, or vice versa.
    Keyword Args:
        description: A short description about the option.
        description_title: The title to use for the description. If None, copies the name.
        is_hidden: If true, the option will not be shown in the options menu.
        on_change: If not None, a callback to run before updating the value. Passed a reference to
                   the option object and the new value.
    Extra Attributes:
        default_value: What the value was originally when registered. Does not update on change.
    """

    choices: Sequence[str]
    wrap_enabled: bool = False


@dataclass
class BoolOption(ValueOption[bool]):
    """
    An option toggling a boolean value. Typically implemented as an "on/off" spinner.

    Args:
        name: The option's name.
        value: The option's value.
        true_text: If not None, overwrites the default text used for the True option.
        false_text: If not None, overwrites the default text used for the False option.
    Keyword Args:
        description: A short description about the option.
        description_title: The title to use for the description. If None, copies the name.
        is_hidden: If true, the option will not be shown in the options menu.
        on_change: If not None, a callback to run before updating the value. Passed a reference to
                   the option object and the new value.
    Extra Attributes:
        default_value: What the value was originally when registered. Does not update on change.
    """

    true_text: str | None = None
    false_text: str | None = None


@dataclass
class DropdownOption(ValueOption[str]):
    """
    An option selecting one of a set of strings. Typically implemented as a dropdown menu.

    Also see SpinnerOption, which may be more suitable for smaller numbers of choices.

    Args:
        name: The option's name.
        value: The option's value.
        choices: A list of choices for the value.
    Keyword Args:
        description: A short description about the option.
        description_title: The title to use for the description. If None, copies the name.
        is_hidden: If true, the option will not be shown in the options menu.
        on_change: If not None, a callback to run before updating the value. Passed a reference to
                   the option object and the new value.
    Extra Attributes:
        default_value: What the value was originally when registered. Does not update on change.
    """

    choices: Sequence[str]


@dataclass
class ButtonOption(BaseOption):
    """
    An entry in the options list which may be pressed to trigger a callback.

    May also be used without a callback, as a way to just inject plain entries, e.g. for extra
    descriptions.

    Args:
        name: The option's name.
        on_press: If not None, the callback to run when the button is pressed. Passed a reference to
                  the option object.
    Keyword Args:
        description: A short description about the option.
        description_title: The title to use for the description. If None, copies the name.
        is_hidden: If true, the option will not be shown in the options menu.
    """

    on_press: Callable[[Self], None] | None = None
