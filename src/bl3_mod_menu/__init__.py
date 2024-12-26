from mods_base import Game, GroupedOption
from mods_base.mod_list import base_mod

__all__: list[str] = [
    "__author__",
    "__version__",
    "__version_info__",
]

__version_info__: tuple[int, int] = (1, 5)
__version__: str = f"{__version_info__[0]}.{__version_info__[1]}"
__author__: str = "bl-sdk"


# Importing any native modules will fail if we're running in WL, so we need to guard this
if Game.get_current() is Game.BL3:
    from .dialog_box import DialogBox, DialogBoxChoice

    __all__ += [
        "DialogBox",
        "DialogBoxChoice",
    ]

    # Import these modules for their side effects, which setup the actual menu
    from . import (
        keybinds,
        options_callbacks,  # noqa: F401  # pyright: ignore[reportUnusedImport]
        options_setup,  # noqa: F401  # pyright: ignore[reportUnusedImport]
        outer_menu,
    )

    base_mod.options.append(
        GroupedOption(
            "BL3 Mod Menu",
            (
                keybinds.controller_style_option,
                keybinds.switch_swap_option,
                outer_menu.hide_behind_the_scenes,
                outer_menu.hide_store,
                outer_menu.hide_achievements,
                outer_menu.hide_photo_mode,
            ),
        ),
    )

base_mod.components.append(base_mod.ComponentInfo("BL3 Mod Menu", __version__))
