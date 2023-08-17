import inspect
from typing import overload

from .keybinds import Keybind

__all__: tuple[str, ...] = (
    "Mod",
    "register_mod",
    "deregister_mod",
)


class Mod:
    """
    A mod instance to display in the mods menu.

    Attributes - Info:
        name: The mod's name.

    Attributes - Functionality:
        keybinds: A list of the mod's keybinds.

    Attributes - Runtime:
        is_enabled: True if the mod is currently considered enabled.
    """

    name: str

    keybinds: list[Keybind]

    is_enabled: bool

    def __init__(self) -> None:
        self.name = "Unknown Mod"
        self.keybinds = []
        self.is_enabled = False

    def __repr__(self) -> str:
        return f"<{self.name}: " + ("Enabled" if self.is_enabled else "Disabled") + ">"

    def enable(self) -> None:
        """Called to enable the mod."""
        self.is_enabled = True

    def disable(self) -> None:
        """Called to disable the mod."""
        self.is_enabled = False


mod_list: list[Mod] = []


@overload
def register_mod(mod: Mod) -> Mod:  # noqa: D418
    """
    Registers a mod instance.

    Args:
        mod: The mod to register.
    Returns:
        The mod which was registered.
    """


@overload
def register_mod(  # noqa: D418
    *,
    name: str | None = None,
    keybinds: list[Keybind] | None = None,
) -> Mod:
    """
    Factory function to create and register a new mod based on the contents of the calling module.

    Args:
        name: The name of the mod. If not given, uses the module's __name__
        keybinds: The mod's keybinds. If not given, finds all Keybind instances in the module's
                  global namespace.
    Returns:
        The mod which was registered.
    """


def register_mod(  # noqa: D103
    mod: Mod | None = None,
    *,
    name: str | None = None,
    keybinds: list[Keybind] | None = None,
) -> Mod:
    if mod is not None:
        mod_list.append(mod)
        return mod

    module = inspect.getmodule(inspect.stack()[1].frame)
    if module is None:
        raise ValueError("Unable to find calling module when using register_mod factory!")

    mod = Mod()
    mod.name = name or module.__name__
    mod.keybinds = keybinds or []

    for field in dir(module):
        value = getattr(module, field)

        if keybinds is None and isinstance(value, Keybind):
            mod.keybinds.append(value)

    mod_list.append(mod)
    return mod


def deregister_mod(mod: Mod) -> None:
    """
    Removes a mod from the mod list.

    Args:
        mod: The mod to remove.
    """
    if mod.is_enabled:
        mod.disable()

    mod_list.remove(mod)
