from mods_base import BaseOption, Game, Library, build_mod

__all__: list[str] = [
    "__version__",
    "__version_info__",
]

__version_info__: tuple[int, int] = (1, 0)
__version__: str = f"{__version_info__[0]}.{__version_info__[1]}"

_options: list[BaseOption] = []

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
        outer_menu,  # noqa: F401  # pyright: ignore[reportUnusedImport]
    )

    _options.append(keybinds.controller_style_option)

build_mod(
    cls=Library,
    name="BL3 Mod Menu",
    author="bl-sdk",
    description="Adds an in game mod menu to BL3.",
    supported_games=Game.BL3,
    keybinds=[],
    options=_options,
    hooks=[],
)
