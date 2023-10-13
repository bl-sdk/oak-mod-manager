from mods_base import EInputEvent, Game
from mods_base.mod_list import base_mod, mod_list
from mods_base.raw_keybinds import raw_keybind_callback_stack
from unrealsdk.hooks import Block
from unrealsdk.unreal import UObject

from .keybinds import set_keybind_callback

__all__: tuple[str, ...] = (
    "__author__",
    "__version__",
    "__version_info__",
)

__version_info__: tuple[int, int] = (1, 0)
__version__: str = f"{__version_info__[0]}.{__version_info__[1]}"
__author__: str = "bl-sdk"


def handle_raw_keybind(pc: UObject, key: str, event: EInputEvent) -> bool:
    """
    Handler which calls raw keybind callbacks.

    Args:
        pc: The OakPlayerController which caused the event.
        key: The key which was pressed.
        event: Which type of input happened.
    Returns:
        True if the key event should be blocked.
    """
    _ = pc

    should_block = False
    if len(raw_keybind_callback_stack) > 0:
        for callback in raw_keybind_callback_stack[-1]:
            ret = callback(key, event)

            if ret == Block or isinstance(ret, Block):
                should_block = True

    return should_block


def handle_gameplay_keybind(pc: UObject, key: str, event: EInputEvent) -> bool:
    """
    Handler which calls gameplay keybind callbacks.

    Args:
        pc: The OakPlayerController which caused the event.
        key: The key which was pressed.
        event: Which type of input happened.
    Returns:
        True if the key event should be blocked.
    """
    # Early exit if in a menu
    if Game.get_current() == Game.WL:
        # pc.IsInMenu() doesn't work in WL, since it uses a different menu system
        # Haven't found the correct replacement, but just checking cursor seems to work well enough,
        # even works on controller when no cursor is actually drawn
        if pc.bShowMouseCursor:
            return False
    else:
        if pc.IsInMenu():
            return False

    should_block = False
    for mod in mod_list:
        if not mod.is_enabled:
            continue

        for bind in mod.keybinds:
            if bind.callback is None:
                continue
            if bind.key != key:
                continue

            ret = bind.callback(event)
            if ret == Block or isinstance(ret, Block):
                should_block = True

    return should_block


@set_keybind_callback
def keybind_handler(pc: UObject, key: str, event: EInputEvent) -> None | Block | type[Block]:
    """General keybind handler."""
    if handle_raw_keybind(pc, key, event):
        return Block
    if handle_gameplay_keybind(pc, key, event):
        return Block

    return None


base_mod.components.append(base_mod.ComponentInfo("Keybinds", __version__))
