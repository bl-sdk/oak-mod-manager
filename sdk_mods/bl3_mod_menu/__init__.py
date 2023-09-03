from mods_base import Game, Library, build_mod

__all__: list[str] = [
    "__version__",
    "__version_info__",
]

__version_info__: tuple[int, int] = (1, 0)
__version__: str = f"{__version_info__[0]}.{__version_info__[1]}"

# Importing any native modules will fail if we're running in WL, so we need to guard this
if Game.get_current() is Game.BL3:
    from .dialog_box import DialogBox, DialogBoxChoice

    __all__ += [
        "DialogBox",
        "DialogBoxChoice",
    ]

    # Import these modules for their side effects, which setup the actual menu
    from . import options_setup, outer_menu  # noqa: F401  # pyright: ignore[reportUnusedImport]

build_mod(
    cls=Library,
    name="BL3 Mod Menu",
    author="bl-sdk",
    description="Adds an in game mod menu to BL3.",
    supported_games=Game.BL3,
    keybinds=[],
    options=[],
    hooks=[],
)
