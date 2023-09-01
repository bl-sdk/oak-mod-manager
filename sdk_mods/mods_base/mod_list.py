from functools import cmp_to_key

from .mod import Mod, ModType

mod_list: list[Mod] = []


def register_mod(mod: Mod) -> None:
    """
    Registers a mod instance.

    Args:
        mod: The mod to register.
    Returns:
        The mod which was registered.
    """
    mod_list.append(mod)


def deregister_mod(mod: Mod) -> None:
    """
    Removes a mod from the mod list.

    Args:
        mod: The mod to remove.
    """
    if mod.is_enabled:
        mod.disable()

    mod_list.remove(mod)


def get_ordered_mod_list() -> list[Mod]:
    """
    Gets the list of mods, in display order.

    Returns:
        The ordered mod list.
    """

    def cmp(a: Mod, b: Mod) -> int:
        if a.mod_type is not ModType.Library and b.mod_type is ModType.Library:
            return 1
        if a.mod_type is ModType.Library and b.mod_type is not ModType.Library:
            return -1

        if a.name < b.name:
            return -1
        if a.name > b.name:
            return 1
        return 0

    return sorted(mod_list, key=cmp_to_key(cmp))
