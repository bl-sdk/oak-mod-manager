from typing import TypeVar, overload

from mods_base import JSON, BaseOption, BoolOption, KeybindOption, ValueOption

J = TypeVar("J", bound=JSON)


@overload
def get_option_value_str(option: ValueOption[J]) -> str:
    ...


@overload
def get_option_value_str(option: BaseOption) -> str | None:
    ...


def get_option_value_str(option: BaseOption) -> str | None:
    """
    Gets the string to use for the option's value.

    Args:
        option: The option to get the value string of.
    Returns:
        The option's value string, or None if it doesn't have a value.
    """
    match option:
        case BoolOption():
            return (option.false_text or "Off", option.true_text or "On")[option.value]
        case KeybindOption() if option.value is None:
            return "..."
        case ValueOption():
            # The generics mean the type of value is technically unknown here
            return str(option.value)  # type: ignore
        case _:
            return None
