import contextlib
import warnings
from typing import Literal, overload

import unrealsdk
from unrealsdk.unreal import UObject

from mods_base import Game, get_pc

__all__: tuple[str, ...] = (
    "KNOWN_BL3_IMAGE_NAMES",
    "show_modal_tutorial_message",
)

type KNOWN_BL3_IMAGE_NAMES = Literal[
    "ActionSkillTutorial",
    "Alisma",
    "Dandelion",
    "EridianAnalyzer",
    "Geranium",
    "Hibiscus",
    "HiJackTutorial",
    "Ixora1",
    "Ixora2",
    "TrueVaultHunter",
]


@overload
def show_modal_tutorial_message(title: str, msg: str) -> None: ...


@overload
def show_modal_tutorial_message(
    title: str,
    msg: str,
    *,
    image_name: KNOWN_BL3_IMAGE_NAMES | str,
) -> None: ...


@overload
def show_modal_tutorial_message(title: str, msg: str, *, image_texture: UObject) -> None: ...


@overload
def show_modal_tutorial_message(
    title: str,
    msg: str,
    *,
    image_name: KNOWN_BL3_IMAGE_NAMES | str,
    image_texture: UObject,
) -> None: ...


def show_modal_tutorial_message(
    title: str,
    msg: str,
    *,
    image_name: KNOWN_BL3_IMAGE_NAMES | str | None = None,
    image_texture: UObject | None = None,
) -> None:
    """
    Displays a large blocking tutorial message in the middle of the screen.

    Silently dropped if called during a loading screen. In WL, also silently dropped on the main
    menu, and delayed until you close any menus if you're in game.

    Tutorial messages contain an image across the top of the message box. In BL3, this is pulled
    from a texture atlas, you can specify which entry using 'image_name'. Not all names are
    currently known, those which are are in the type hints. In WL, the image instead is taken from
    an arbitrary Texture2D, which you can pass in 'image_texture'.

    Setting just one image source will cause a warning when used in the wrong game - though the
    tutorial will still be displayed. Setting both or neither source is allowed.

    Args:
        title: The title of the message box.
        msg: The message to display.
        image_name: BL3 only. The name of the image to use on the top of the message box.
        image_texture: WL only. A Texture2D to use as the image on top of the message box.
    """
    match image_name, image_texture:
        case None, None:
            pass
        case _, None if Game.get_current() != Game.BL3:
            warnings.warn(
                "'image_name' is only supported in BL3. Either remove it, or also pass an"
                " 'image_texture'.",
                stacklevel=2,
            )
        case None, _ if Game.get_current() == Game.BL3:
            warnings.warn(
                "'image_texture' is not supported in BL3. Either remove it, or also pass an"
                " 'image_name'.",
                stacklevel=2,
            )
        case _, _:
            pass

    pc = get_pc(possibly_loading=True)
    if pc is None:
        return

    data = unrealsdk.construct_object("GFxModalTutorialDataAsset", outer=None)
    data.Header = title
    data.Body = msg
    if image_name is not None:
        data.ImageFrameName = image_name

    # This property might not exist
    with contextlib.suppress(AttributeError):
        data.BackgroundTexture = image_texture

    data.bShowEvenIfTutorialsAreDisabled = True

    pc.ClientAddModalTutorialMessage(data)
